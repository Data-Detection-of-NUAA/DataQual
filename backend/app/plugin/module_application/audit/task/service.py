
"""Audit task service layer."""

import os
from typing import List, Tuple, Optional

from fastapi import UploadFile
from sqlalchemy import delete

from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.exceptions import CustomException
from app.common.request import PaginationService
from .crud import AuditTaskCRUD, AuditErrorCRUD
from .schema import AuditTaskCreate, AuditTaskUpdate, AuditTaskQueryParam
from .model import AuditError
from ..rule.crud import AuditRuleCRUD
from ..engine.file_parser import FileParser
from ..engine.ai_matcher import AIMatcher
from ..engine.audit_engine import AuditEngine
from ..engine.report_generator import ReportGenerator
from ..engine.content_extractor import ContentExtractor  # 新增：智能抽取器
from ..engine.content_detector import ContentDetector, GDPRDetectionReport  # 新增：GDPR检测器
from ..file import save_upload_file
from ..regulation.service import AuditRegulationService


class AuditTaskService:
    """Business service for audit tasks."""

    @staticmethod
    async def create_service(
        obj_in: AuditTaskCreate,
        auth: AuthSchema
    ):
        """Create an audit task and return a minimal payload."""
        task = await AuditTaskCRUD(auth).create(data=obj_in)
        return {
            "id": task.id,
            "task_name": task.task_name,
            "task_status": task.task_status,
            "description": task.description,
        }

    @staticmethod
    async def list_service(
        params: AuditTaskQueryParam,
        auth: AuthSchema
    ) -> Tuple[List[dict], int]:
        """Return task list data and total count."""
        search_conditions = {}
        if params.task_name is not None:
            search_conditions["task_name"] = params.task_name
        if params.task_status is not None:
            search_conditions["task_status"] = params.task_status

        tasks = await AuditTaskCRUD(auth).list(
            search=search_conditions,
            order_by=[{"created_time": "desc"}]
        )

        total = len(tasks)

        return [
            {
                "id": task.id,
                "task_name": task.task_name,
                "task_status": task.task_status,
                "regulation_file_name": task.regulation_file_name,
                "regulation_id": task.regulation_id,
                "dataset_file_name": task.dataset_file_name,
                "total_records": task.total_records,
                "error_records": task.error_records,
                "created_at": str(task.created_time) if task.created_time else None,
                "updated_at": str(task.updated_time) if task.updated_time else None,
            }
            for task in tasks
        ], total

    @staticmethod
    async def delete_service(ids: List[int], auth: AuthSchema) -> None:
        """Delete tasks and their error logs."""
        if not ids:
            return
        await AuditTaskCRUD(auth).delete(ids=ids)
        await auth.db.execute(delete(AuditError).where(AuditError.task_id.in_(ids)))
        await auth.db.flush()

    @staticmethod
    async def detail_service(id: int, auth: AuthSchema):
        """Return detail info for the given task id."""
        task = await AuditTaskCRUD(auth).get(id=id)
        if not task:
            raise CustomException(msg="Task not found", code=404)

        matched_rule_ids = AuditTaskService._extract_rule_ids(task.matched_rules)
        selected_rule_ids = AuditTaskService._extract_rule_ids(task.selected_rules)

        return {
            "id": task.id,
            "task_name": task.task_name,
            "task_status": task.task_status,
            "description": task.description,
            "regulation_file_type": task.regulation_file_type,
            "regulation_file_path": task.regulation_file_path,
            "regulation_file_name": task.regulation_file_name,
            "regulation_id": task.regulation_id,
            "matched_rules": matched_rule_ids,
            "matched_rule_ids": matched_rule_ids,
            "selected_rules": selected_rule_ids,
            "selected_rule_ids": selected_rule_ids,
            "dataset_file_type": task.dataset_file_type,
            "dataset_file_path": task.dataset_file_path,
            "dataset_file_name": task.dataset_file_name,
            "total_records": task.total_records,
            "error_records": task.error_records,
            "audit_report_path": task.audit_report_path,
            "created_at": str(task.created_time) if task.created_time else None,
            "updated_at": str(task.updated_time) if task.updated_time else None,
        }

    @staticmethod
    async def upload_regulation_service(
        task_id: int,
        file_type: str,
        file: UploadFile,
        auth: AuthSchema
    ) -> dict:
        """Save a regulation file to the library and bind it to the task."""
        task = await AuditTaskCRUD(auth).get(id=task_id)
        if not task:
            raise CustomException(msg="Task not found", code=404)

        saved_meta = await save_upload_file(file, file_type, "regulation")
        regulation = await AuditRegulationService.create_from_file_meta(
            saved_meta=saved_meta,
            file_type=file_type,
            regulation_name=os.path.splitext(
                saved_meta.original_name or saved_meta.stored_name
            )[0],
            description=None,
            auth=auth,
        )

        await AuditTaskCRUD(auth).update(
            id=task_id,
            data=AuditTaskUpdate(
                task_status="regulation_uploaded",
                regulation_file_type=regulation.file_type,
                regulation_file_path=regulation.file_path,
                regulation_file_name=regulation.file_name,
                regulation_id=regulation.id,
            ),
        )

        return {
            "file_path": regulation.file_path,
            "file_name": regulation.file_name,
            "file_type": regulation.file_type,
            "regulation_id": regulation.id,
        }

    @staticmethod
    async def use_existing_regulation_service(
        task_id: int,
        regulation_id: int,
        auth: AuthSchema
    ) -> dict:
        """Bind an existing regulation record to the task."""
        task = await AuditTaskCRUD(auth).get(id=task_id)
        if not task:
            raise CustomException(msg="Task not found", code=404)

        detail = await AuditRegulationService.detail_service(regulation_id, auth)
        file_path = detail["file_path"]
        file_type = detail["file_type"]
        file_name = detail["file_name"]

        await AuditTaskCRUD(auth).update(
            id=task_id,
            data=AuditTaskUpdate(
                task_status="regulation_uploaded",
                regulation_file_type=file_type,
                regulation_file_path=file_path,
                regulation_file_name=file_name,
                regulation_id=regulation_id,
            ),
        )

        return {
            "file_path": file_path,
            "file_name": file_name,
            "file_type": file_type,
            "regulation_id": regulation_id,
        }

    @staticmethod
    async def match_rules_service(
        task_id: int,
        auth: AuthSchema
    ) -> dict:
        """Use AI matcher to suggest rules for the task."""
        task = await AuditTaskCRUD(auth).get(id=task_id)
        if not task or not task.regulation_file_path:
            raise CustomException(msg="Please upload a regulation file first", code=400)

        # 使用新的智能抽取器（支持30+种格式）
        try:
            extracted_content = ContentExtractor.extract(
                task.regulation_file_path,
                task.regulation_file_type
            )

            # 获取文本内容用于AI匹配
            regulation_content = extracted_content.text or ""

            # 如果抽取失败，降级到旧的解析器
            if not regulation_content and extracted_content.status != "success":
                print(f"智能抽取失败，降级到旧解析器: {extracted_content.errors}")
                regulation_content = FileParser.parse_file(
                    task.regulation_file_path,
                    task.regulation_file_type,
                )
        except Exception as e:
            # 降级策略：使用旧的解析器
            print(f"智能抽取异常，降级到旧解析器: {str(e)}")
            regulation_content = FileParser.parse_file(
                task.regulation_file_path,
                task.regulation_file_type,
            )

        all_rules = await AuditRuleCRUD(auth).list(search={"is_active": 1})
        match_result = await AIMatcher.match_rules(regulation_content, all_rules)

        # 兼容新旧格式
        matched_rule_ids = match_result.get("rule_ids", match_result) if isinstance(match_result, dict) else match_result
        match_details = match_result.get("matches", []) if isinstance(match_result, dict) else []

        # 创建匹配详情映射
        match_details_map = {m["rule_id"]: m for m in match_details}

        await AuditTaskCRUD(auth).update(
            id=task_id,
            data=AuditTaskUpdate(
                task_status="rules_matched",
                matched_rules={"rule_ids": matched_rule_ids, "matches": match_details},
            ),
        )

        matched_rules = [rule for rule in all_rules if rule.id in matched_rule_ids]

        return {
            "matched_rule_ids": matched_rule_ids,
            "matched_rules": [
                {
                    "id": rule.id,
                    "rule_code": rule.rule_code,
                    "rule_name": rule.rule_name,
                    "rule_type": rule.rule_type,
                    "rule_description": rule.rule_description,
                    "severity": rule.severity,
                    "ai_matched": True,
                    # 添加匹配详情
                    "match_reason": match_details_map.get(rule.id, {}).get("reason", ""),
                    "regulation_ref": match_details_map.get(rule.id, {}).get("regulation_ref", ""),
                }
                for rule in matched_rules
            ],
        }

    @staticmethod
    async def confirm_rules_service(
        task_id: int,
        selected_rules: List[int],
        auth: AuthSchema
    ) -> dict:
        """Persist which rules the analyst selected."""
        task = await AuditTaskCRUD(auth).get(id=task_id)
        if not task:
            raise CustomException(msg="Task not found", code=404)
        if not selected_rules:
            raise CustomException(msg="At least one rule is required", code=400)

        await AuditTaskCRUD(auth).update(
            id=task_id,
            data=AuditTaskUpdate(
                task_status="rules_confirmed",
                selected_rules={"rule_ids": selected_rules},
            ),
        )

        return {"selected_rules": selected_rules}

    @staticmethod
    async def upload_dataset_service(
        task_id: int,
        file_type: str,
        file: UploadFile,
        auth: AuthSchema
    ) -> dict:
        """Upload the dataset that will be audited."""
        task = await AuditTaskCRUD(auth).get(id=task_id)
        selected_rule_ids = AuditTaskService._extract_rule_ids(
            task.selected_rules if task else None
        )
        if not task or not selected_rule_ids:
            raise CustomException(msg="Please confirm rules before uploading data", code=400)

        file_path, file_name = await AuditTaskService._save_file(file, file_type, "dataset")

        await AuditTaskCRUD(auth).update(
            id=task_id,
            data=AuditTaskUpdate(
                task_status="dataset_uploaded",
                dataset_file_type=file_type,
                dataset_file_path=file_path,
                dataset_file_name=file_name,
            ),
        )

        return {
            "file_path": file_path,
            "file_name": file_name,
            "file_type": file_type,
        }

    @staticmethod
    async def execute_audit_service(
        task_id: int,
        auth: AuthSchema
    ) -> dict:
        """Run the audit workflow on the uploaded dataset."""
        task = await AuditTaskCRUD(auth).get(id=task_id)
        if not task or not task.dataset_file_path:
            raise CustomException(msg="Please upload a dataset first", code=400)

        await AuditTaskCRUD(auth).update(
            id=task_id,
            data=AuditTaskUpdate(task_status="processing"),
        )

        try:
            selected_rule_ids = AuditTaskService._extract_rule_ids(task.selected_rules)
            if not selected_rule_ids:
                raise CustomException(msg="Please confirm rules before execution", code=400)

            selected_rules = []
            for rule_id in selected_rule_ids:
                rule = await AuditRuleCRUD(auth).get(id=rule_id)
                if rule:
                    selected_rules.append(rule)

            # ==================== 阶段1: 智能文件抽取 ====================
            print(f"[审计] 开始智能抽取数据集: {task.dataset_file_path}")
            extracted_content = ContentExtractor.extract(
                task.dataset_file_path,
                task.dataset_file_type
            )

            # 检查抽取状态
            if extracted_content.status == "failed":
                raise CustomException(
                    msg=f"文件抽取失败: {', '.join(extracted_content.errors or ['未知错误'])}",
                    code=400
                )

            # 打印抽取信息
            print(f"[审计] 抽取完成 - 状态: {extracted_content.status}")
            if extracted_content.text:
                print(f"[审计] - 文本内容: {len(extracted_content.text)} 字符")
            if extracted_content.structured:
                print(f"[审计] - 结构化字段: {len(extracted_content.structured)} 个")
            if extracted_content.warnings:
                print(f"[审计] - 警告: {len(extracted_content.warnings)} 条")

            # ==================== 阶段2: 规则验证（保留原有逻辑） ====================
            # 尝试获取结构化数据用于规则验证
            dataset_records = None
            if extracted_content.structured and isinstance(extracted_content.structured, dict):
                # 如果是CSV/Excel等结构化数据，转换为记录列表
                try:
                    # 尝试使用旧的解析器获取记录格式
                    dataset_records = FileParser.parse_file(
                        task.dataset_file_path,
                        task.dataset_file_type,
                    )
                except Exception as e:
                    print(f"[审计] 旧解析器失败，跳过规则验证: {str(e)}")
                    dataset_records = []

            # 执行规则验证（如果有数据）
            audit_result = {"total_records": 0, "error_records": 0, "errors": [], "rule_statistics": []}
            if dataset_records:
                print(f"[审计] 开始规则验证: {len(dataset_records)} 条记录")
                audit_result = AuditEngine.audit_dataset(dataset_records, selected_rules)
                print(f"[审计] 规则验证完成 - 发现 {len(audit_result['errors'])} 个错误")

            # ==================== 阶段3: GDPR智能检测（新增） ====================
            print(f"[审计] 开始GDPR智能检测...")
            gdpr_detection_results = ContentDetector.detect(extracted_content.to_dict())
            print(f"[审计] GDPR检测完成 - 发现 {len(gdpr_detection_results)} 项")

            # 生成GDPR报告
            gdpr_report = GDPRDetectionReport.generate_report(
                gdpr_detection_results,
                extracted_content.to_dict()
            )
            print(f"[审计] 合规分数: {gdpr_report['compliance_score']:.1f}/100")

            # ==================== 阶段4: 合并结果并保存 ====================
            # 将GDPR检测结果转换为错误记录格式
            for detection in gdpr_detection_results:
                error_dict = {
                    "task_id": task_id,
                    "error_type": "gdpr",  # 新类型：GDPR检测
                    "row_number": None,  # GDPR检测可能没有行号
                    "column_name": detection.location,  # 使用location作为列名
                    "field_name": detection.detection_type.value,
                    "original_value": detection.matched_value[:200] if detection.matched_value else None,  # 限制长度
                    "error_message": f"[{detection.risk_level.value}] {detection.detection_type.value}: {detection.recommendation}",
                    "rule_id": None,  # GDPR检测不关联规则
                    "severity": detection.risk_level.value,
                    "start_position": None,
                    "end_position": None,
                }
                auth.db.add(AuditError(**error_dict))

            # 保存原有规则验证的错误
            for error in audit_result["errors"]:
                error_dict = {
                    "task_id": task_id,
                    "error_type": error["error_type"],
                    "row_number": error.get("row_number"),
                    "column_name": error.get("column_name"),
                    "field_name": error.get("field_name"),
                    "original_value": error.get("original_value"),
                    "error_message": error.get("error_message"),
                    "rule_id": error.get("rule_id"),
                    "severity": error.get("severity"),
                    "start_position": error.get("start_position"),
                    "end_position": error.get("end_position"),
                }
                auth.db.add(AuditError(**error_dict))

            # 生成报告
            report_path = await ReportGenerator.generate_report(
                task_id,
                audit_result,
                selected_rules,
                gdpr_detection_results,
                gdpr_report,
            )

            # 计算总错误数（规则验证 + GDPR检测）
            total_errors = len(audit_result["errors"]) + len(gdpr_detection_results)

            # 计算总记录数（优先使用规则验证结果，否则从抽取内容推断）
            total_records = audit_result.get("total_records", 0)
            if total_records == 0 and extracted_content.structured:
                # 对于结构化数据（如CSV），统计唯一行数
                row_keys = set()
                for key in extracted_content.structured.keys():
                    if '.' in key:
                        # 格式: "row.0.field_name" -> 提取行号
                        parts = key.split('.')
                        if len(parts) >= 2 and parts[0] == 'row':
                            row_keys.add(parts[1])
                total_records = len(row_keys) if row_keys else 1
            elif total_records == 0 and extracted_content.text:
                # 对于非结构化数据（如HTML、TXT），视为1个文档
                total_records = 1

            # 计算错误记录数（规则验证错误 + GDPR检测）
            # 注意：GDPR检测的每一项都算作一个错误
            error_records = audit_result.get("error_records", 0)
            if error_records == 0 and len(gdpr_detection_results) > 0:
                # 如果规则验证没有运行，使用GDPR检测数量
                error_records = len(gdpr_detection_results)

            await AuditTaskCRUD(auth).update(
                id=task_id,
                data=AuditTaskUpdate(
                    task_status="completed",
                    total_records=total_records,
                    error_records=error_records,
                    audit_report_path=report_path,
                ),
            )

            await auth.db.commit()

            return {
                "status": "completed",
                "total_records": total_records,
                "error_records": error_records,
                "rule_statistics": audit_result.get("rule_statistics", []),
                # 新增：GDPR检测结果摘要
                "gdpr_summary": {
                    "total_detections": len(gdpr_detection_results),
                    "compliance_score": gdpr_report["compliance_score"],
                    "risk_breakdown": gdpr_report["summary"]["detection_by_risk"],
                    "recommendations": gdpr_report["recommendations"][:3],  # 前3条建议
                },
                "extraction_warnings": extracted_content.warnings or [],
            }

        except Exception as exc:  # pylint: disable=broad-except
            await AuditTaskCRUD(auth).update(
                id=task_id,
                data=AuditTaskUpdate(task_status="failed"),
            )
            await auth.db.commit()
            raise CustomException(msg=f"Audit execution failed: {exc}", code=500) from exc

    @staticmethod
    async def get_audit_result_service(
        task_id: int,
        auth: AuthSchema
    ) -> dict:
        """Return the audit result payload for UI display."""
        task = await AuditTaskCRUD(auth).get(id=task_id)
        if not task:
            raise CustomException(msg="Task not found", code=404)

        data_errors = await AuditErrorCRUD(auth).list(
            search={"task_id": task_id, "error_type": "data"}
        )
        label_errors = await AuditErrorCRUD(auth).list(
            search={"task_id": task_id, "error_type": "label"}
        )

        return {
            "task_id": task.id,
            "task_name": task.task_name,
            "task_status": task.task_status,
            "total_records": task.total_records,
            "error_records": task.error_records,
            "data_errors": [
                {
                    "row_number": err.row_number,
                    "column_name": err.column_name,
                    "original_value": err.original_value,
                    "error_message": err.error_message,
                    "severity": err.severity,
                    "start_position": err.start_position,
                    "end_position": err.end_position,
                }
                for err in data_errors
            ],
            "label_errors": [
                {
                    "row_number": err.row_number,
                    "field_name": err.field_name,
                    "original_value": err.original_value,
                    "error_message": err.error_message,
                    "severity": err.severity,
                    "start_position": err.start_position,
                    "end_position": err.end_position,
                }
                for err in label_errors
            ],
            "audit_report_path": task.audit_report_path,
        }

    @staticmethod
    async def get_errors_service(
        task_id: int,
        error_type: Optional[str],
        page_no: int,
        page_size: int,
        auth: AuthSchema
    ) -> dict:
        """Return paginated audit error rows."""
        search_conditions = {"task_id": task_id}
        if error_type:
            search_conditions["error_type"] = error_type

        errors = await AuditErrorCRUD(auth).list(search=search_conditions)

        normalized = [
            {
                "id": err.id,
                "error_type": err.error_type,
                "row_number": err.row_number,
                "column_name": err.column_name,
                "field_name": err.field_name,
                "original_value": err.original_value,
                "error_message": err.error_message,
                "severity": err.severity,
                "start_position": err.start_position,
                "end_position": err.end_position,
            }
            for err in errors
        ]

        return await PaginationService.paginate(
            data_list=normalized,
            page_no=page_no,
            page_size=page_size,
        )

    @staticmethod
    async def download_report_service(
        task_id: int,
        auth: AuthSchema
    ) -> str:
        """Return filesystem path of the generated report."""
        task = await AuditTaskCRUD(auth).get(id=task_id)
        if not task or not task.audit_report_path:
            raise CustomException(msg="Audit report not found", code=404)

        if not os.path.exists(task.audit_report_path):
            raise CustomException(msg="Report file does not exist", code=404)

        return task.audit_report_path

    @staticmethod
    def _extract_rule_ids(rule_payload) -> List[int]:
        """Normalize stored rule payload (dict or list) into IDs."""
        if not rule_payload:
            return []
        if isinstance(rule_payload, dict):
            value = rule_payload.get("rule_ids") or []
            if isinstance(value, list):
                return [int(rule_id) for rule_id in value]
            return []
        if isinstance(rule_payload, list):
            return [int(rule_id) for rule_id in rule_payload]
        return []

    @staticmethod
    async def _save_file(file: UploadFile, file_type: str, category: str) -> Tuple[str, str]:
        """Save upload and return canonical (path, display_name)."""
        saved_meta = await save_upload_file(file, file_type, category)
        display_name = saved_meta.original_name or saved_meta.stored_name
        return saved_meta.file_path, display_name

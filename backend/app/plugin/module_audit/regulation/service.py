"""
审计法规 Service
"""
from __future__ import annotations

import os
from typing import List, Tuple, Optional

from fastapi import UploadFile

from app.api.v1.module_system.auth.schema import AuthSchema
from app.common.request import PaginationService
from app.core.exceptions import CustomException

from ..file import SavedFileMeta, save_upload_file
from ..task.crud import AuditTaskCRUD
from .crud import AuditRegulationCRUD
from .model import AuditRegulation
from .schema import (
    AuditRegulationCreate,
    AuditRegulationQueryParam,
)


class AuditRegulationService:
    """审计法规相关业务"""

    @staticmethod
    async def list_service(
        params: AuditRegulationQueryParam,
        page_no: int,
        page_size: int,
        auth: AuthSchema,
    ) -> dict:
        """获取法规分页列表"""
        search_conditions = {}
        if getattr(params, "regulation_name", None):
            search_conditions["regulation_name"] = params.regulation_name
        if getattr(params, "file_name", None):
            search_conditions["file_name"] = params.file_name

        records = await AuditRegulationCRUD(auth).list(
            search=search_conditions,
            order_by=[{"created_time": "desc"}],
        )

        normalized = [
            AuditRegulationService._model_to_dict(item)
            for item in records
        ]
        return await PaginationService.paginate(
            data_list=normalized,
            page_no=page_no,
            page_size=page_size,
        )

    @staticmethod
    async def detail_service(regulation_id: int, auth: AuthSchema) -> dict:
        """获取单条法规详情"""
        regulation = await AuditRegulationService._get_model(regulation_id, auth)
        return AuditRegulationService._model_to_dict(regulation, include_path=True)

    @staticmethod
    async def upload_service(
        regulation_name: Optional[str],
        description: Optional[str],
        file_type: str,
        file: UploadFile,
        auth: AuthSchema,
    ) -> dict:
        """上传法规文件并入库"""
        saved_meta = await save_upload_file(file, file_type, "regulation")
        regulation = await AuditRegulationService.create_from_file_meta(
            saved_meta=saved_meta,
            file_type=file_type,
            regulation_name=regulation_name,
            description=description,
            auth=auth,
        )
        return AuditRegulationService._model_to_dict(regulation, include_path=True)

    @staticmethod
    async def delete_service(ids: List[int], auth: AuthSchema) -> None:
        """批量删除法规"""
        if not ids:
            return

        # 检查是否被任务引用
        in_use_tasks = await AuditTaskCRUD(auth).list(
            search={"regulation_id": ("in", ids)}
        )
        if in_use_tasks:
            task_names = ", ".join(task.task_name for task in in_use_tasks[:3])
            raise CustomException(
                msg=f"存在任务正在使用这些法规，无法删除（例如：{task_names}）"
            )

        await AuditRegulationCRUD(auth).delete(ids=ids)

    @staticmethod
    async def options_service(auth: AuthSchema) -> List[dict]:
        """获取法规选项"""
        records = await AuditRegulationCRUD(auth).list(
            order_by=[{"created_time": "desc"}]
        )
        return [
            {
                "id": item.id,
                "regulation_name": item.regulation_name,
                "file_name": item.file_name,
                "file_type": item.file_type,
                "file_size": item.file_size,
                "updated_time": str(item.updated_time) if item.updated_time else None,
            }
            for item in records
        ]

    @staticmethod
    async def create_from_file_meta(
        saved_meta: SavedFileMeta,
        file_type: str,
        regulation_name: Optional[str],
        description: Optional[str],
        auth: AuthSchema,
    ) -> AuditRegulation:
        """根据已保存的文件信息创建法规记录"""
        display_name = regulation_name or _derive_display_name(saved_meta.original_name or saved_meta.stored_name)
        create_in = AuditRegulationCreate(
            regulation_name=display_name,
            file_name=saved_meta.original_name or saved_meta.stored_name,
            file_type=file_type,
            file_path=saved_meta.file_path,
            file_size=saved_meta.file_size,
            description=description,
        )
        regulation = await AuditRegulationCRUD(auth).create(create_in)
        return regulation

    @staticmethod
    async def _get_model(regulation_id: int, auth: AuthSchema) -> AuditRegulation:
        regulation = await AuditRegulationCRUD(auth).get(id=regulation_id)
        if not regulation:
            raise CustomException(msg="法规不存在", code=404)
        return regulation

    @staticmethod
    def _model_to_dict(regulation: AuditRegulation, include_path: bool = False) -> dict:
        data = {
            "id": regulation.id,
            "regulation_name": regulation.regulation_name,
            "file_name": regulation.file_name,
            "file_type": regulation.file_type,
            "file_size": regulation.file_size,
            "status": regulation.status,
            "description": regulation.description,
            "created_time": str(regulation.created_time) if regulation.created_time else None,
            "updated_time": str(regulation.updated_time) if regulation.updated_time else None,
        }
        if include_path:
            data["file_path"] = regulation.file_path
        return data


def _derive_display_name(original_name: str) -> str:
    """默认使用文件名（去掉扩展名）作为法规名称"""
    base, _ = os.path.splitext(original_name or "")
    return base or original_name or "未命名法规"

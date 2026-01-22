# -*- coding: utf-8 -*-

import json
from typing import Any
from collections.abc import Sequence

from app.core.exceptions import CustomException
from app.core.logger import log
from app.api.v1.module_system.auth.schema import AuthSchema

from .schema import (
    ModelConfigCreateSchema,
    ModelConfigUpdateSchema,
    ModelConfigOutSchema,
    ModelConfigQueryParam,
    ModelCardSchema,
    ModelDetailSchema,
    ModelRecommendationRequest,
    ModelRecommendationResponse,
    ModelRecommendationItem,
    DatasetInfoForTrain
)
from .crud import ModelConfigCRUD
from .model import ModelConfigModel


class ModelCapabilityScoreService:
    """模型能力评分服务"""

    @staticmethod
    def calculate_model_capability_score(
        model: ModelConfigModel,
        dataset_modality: str,
        dataset_task_type: str | None = None,
        dataset_sample_count: int | None = None,
        dataset_class_count: int | None = None
    ) -> dict[str, Any]:
        """
        计算模型能力评分

        评分维度：
        1. 模态匹配度 (0-25分)
        2. 任务适配度 (0-30分)
        3. 模型性能指标 (0-20分)
        4. 数据集规模适配度 (0-15分)
        5. 模型优先级权重 (0-10分)

        参数:
        - model (ModelConfigModel): 模型配置
        - dataset_modality (str): 数据集模态
        - dataset_task_type (str | None): 数据集任务类型
        - dataset_sample_count (int | None): 样本数量
        - dataset_class_count (int | None): 类别数量

        返回:
        - dict: 包含总分、各维度得分和推荐理由
        """
        scores = {
            "modality_score": 0.0,      # 模态匹配度
            "task_score": 0.0,           # 任务适配度
            "performance_score": 0.0,    # 性能指标
            "scale_score": 0.0,          # 数据集规模适配度
            "priority_score": 0.0,       # 优先级权重
            "total_score": 0.0           # 总分
        }
        reasons = []

        # 1. 模态匹配度 (0-25分)
        supported_modalities = model.supported_modalities.split(',')
        supported_modalities = [m.strip() for m in supported_modalities]

        if dataset_modality in supported_modalities:
            scores["modality_score"] = 25.0
            reasons.append(f"支持{dataset_modality}模态")
        elif "multimodal" in supported_modalities:
            scores["modality_score"] = 15.0
            reasons.append("支持多模态数据")
        else:
            scores["modality_score"] = 0.0
            reasons.append("模态不完全匹配")

        # 2. 任务适配度 (0-30分)
        if dataset_task_type:
            supported_tasks = model.supported_task_types.split(',')
            supported_tasks = [t.strip() for t in supported_tasks]

            if dataset_task_type in supported_tasks:
                scores["task_score"] = 30.0
                reasons.append(f"专门针对{dataset_task_type}任务优化")
            else:
                # 模糊匹配（例如：image_classification 可以匹配 classification）
                task_matched = False
                for task in supported_tasks:
                    if dataset_task_type in task or task in dataset_task_type:
                        scores["task_score"] = 20.0
                        reasons.append(f"支持相关任务类型")
                        task_matched = True
                        break
                if not task_matched:
                    scores["task_score"] = 5.0
                    reasons.append("任务类型不完全匹配")
        else:
            scores["task_score"] = 15.0  # 未指定任务类型时给中等分数

        # 3. 模型性能指标 (0-20分)
        try:
            performance_metrics = json.loads(model.performance_metrics) if isinstance(model.performance_metrics, str) else model.performance_metrics

            if performance_metrics:
                # 提取关键性能指标
                accuracy = performance_metrics.get('accuracy', 0)
                precision = performance_metrics.get('precision', 0)
                recall = performance_metrics.get('recall', 0)
                f1_score = performance_metrics.get('f1_score', 0)

                # 计算平均性能
                metrics_list = [m for m in [accuracy, precision, recall, f1_score] if m > 0]
                if metrics_list:
                    avg_performance = sum(metrics_list) / len(metrics_list)
                    scores["performance_score"] = avg_performance * 20  # 归一化到0-20分

                    if avg_performance >= 0.9:
                        reasons.append("性能表现优异")
                    elif avg_performance >= 0.8:
                        reasons.append("性能表现良好")
                    else:
                        reasons.append("性能表现一般")
                else:
                    scores["performance_score"] = 10.0  # 无性能数据时给中等分数
            else:
                scores["performance_score"] = 10.0
        except:
            scores["performance_score"] = 10.0

        # 4. 数据集规模适配度 (0-15分)
        try:
            hardware_requirements = json.loads(model.hardware_requirements) if isinstance(model.hardware_requirements, str) else model.hardware_requirements

            if hardware_requirements and dataset_sample_count:
                min_samples = hardware_requirements.get('min_samples', 0)
                max_samples = hardware_requirements.get('max_samples', float('inf'))
                recommended_samples = hardware_requirements.get('recommended_samples', 10000)

                if min_samples <= dataset_sample_count <= max_samples:
                    # 检查是否接近推荐样本数
                    ratio = dataset_sample_count / recommended_samples if recommended_samples > 0 else 1.0
                    if 0.5 <= ratio <= 2.0:
                        scores["scale_score"] = 15.0
                        reasons.append("数据集规模非常适合该模型")
                    else:
                        scores["scale_score"] = 10.0
                        reasons.append("数据集规模适合该模型")
                else:
                    scores["scale_score"] = 5.0
                    if dataset_sample_count < min_samples:
                        reasons.append("数据集规模偏小，建议增加样本")
                    else:
                        reasons.append("数据集规模偏大，训练时间可能较长")
            else:
                scores["scale_score"] = 10.0  # 无规模信息时给中等分数
        except:
            scores["scale_score"] = 10.0

        # 5. 模型优先级权重 (0-10分)
        # 将优先级归一化到0-10分（假设优先级范围是0-100）
        max_priority = 100
        scores["priority_score"] = min(10.0, (model.priority / max_priority) * 10)

        # 计算总分
        scores["total_score"] = sum([
            scores["modality_score"],
            scores["task_score"],
            scores["performance_score"],
            scores["scale_score"],
            scores["priority_score"]
        ])

        # 归一化到0-1范围（总分是100分）
        normalized_score = scores["total_score"] / 100.0

        return {
            "match_score": round(normalized_score, 3),
            "scores": scores,
            "recommendation_reason": "；".join(reasons)
        }


class ModelRecommendationService:
    """模型推荐服务"""

    @classmethod
    async def recommend_models_service(
        cls,
        auth: AuthSchema,
        request: ModelRecommendationRequest
    ) -> ModelRecommendationResponse:
        """
        推荐模型服务

        参数:
        - auth (AuthSchema): 认证信息
        - request (ModelRecommendationRequest): 推荐请求

        返回:
        - ModelRecommendationResponse: 推荐响应
        """
        try:
            # 1. 获取数据集信息
            dataset_info = await cls._get_dataset_info(auth, request.dataset_id)

            # 使用请求中的模态和任务类型，如果没有则使用数据集的
            modality = request.modality or dataset_info.get("modality", "unknown")
            task_type = request.task_type or dataset_info.get("task_type")

            if modality == "unknown":
                raise CustomException(msg="无法确定数据集模态类型，请先分析数据集或手动指定")

            # 2. 从数据库查询候选模型
            crud = ModelConfigCRUD(auth)
            candidate_models = await crud.recommend_models(
                modality=modality,
                task_type=task_type,
                top_k=request.top_k * 2,  # 查询更多候选，后续按评分筛选
                only_active=request.only_active
            )

            if not candidate_models:
                raise CustomException(msg=f"未找到适合 {modality} 模态的模型")

            # 3. 计算每个模型的能力评分
            recommendations = []
            for model in candidate_models:
                score_result = ModelCapabilityScoreService.calculate_model_capability_score(
                    model=model,
                    dataset_modality=modality,
                    dataset_task_type=task_type,
                    dataset_sample_count=dataset_info.get("sample_count"),
                    dataset_class_count=dataset_info.get("class_count")
                )

                # 提取关键指标用于快速预览
                key_metrics = cls._extract_key_metrics(model)
                hardware_summary = cls._extract_hardware_summary(model)
                default_config_preview = cls._extract_default_config_preview(model)

                # 解析标签
                tags = model.tags.split(',') if model.tags else []
                tags = [tag.strip() for tag in tags]

                recommendation_item = ModelRecommendationItem(
                    model_id=model.id,
                    model_name=model.model_name,
                    display_name=model.display_name,
                    model_version=model.model_version,
                    description=model.description,
                    framework=model.framework,
                    tags=tags,
                    priority=model.priority,
                    match_score=score_result["match_score"],
                    recommendation_reason=score_result["recommendation_reason"],
                    key_metrics=key_metrics,
                    hardware_summary=hardware_summary,
                    default_config_preview=default_config_preview
                )
                recommendations.append(recommendation_item)

            # 4. 按匹配度评分排序并截取前 top_k 个
            recommendations.sort(key=lambda x: x.match_score, reverse=True)
            recommendations = recommendations[:request.top_k]

            # 5. 构建响应
            dataset_info_obj = DatasetInfoForTrain(
                dataset_id=dataset_info["dataset_id"],
                name=dataset_info["name"],
                modality=modality,
                task_type=task_type,
                sample_count=dataset_info.get("sample_count"),
                class_count=dataset_info.get("class_count"),
                file_size=dataset_info["file_size"],
                storage_path=dataset_info["storage_path"],
                dataset_metadata=dataset_info.get("dataset_metadata")
            )

            response = ModelRecommendationResponse(
                dataset_info=dataset_info_obj,
                total_recommended=len(recommendations),
                recommendations=recommendations,
                recommendation_metadata={
                    "algorithm_version": "1.0",
                    "scoring_method": "capability_based",
                    "timestamp": str(dataset_info.get("created_time", ""))
                }
            )

            log.info(f"推荐模型成功: 数据集ID={request.dataset_id}, 推荐数量={len(recommendations)}")
            return response

        except CustomException:
            raise
        except Exception as e:
            log.error(f"推荐模型失败: {str(e)}")
            raise CustomException(msg=f"推荐模型失败: {str(e)}")

    @classmethod
    async def _get_dataset_info(cls, auth: AuthSchema, dataset_id: int) -> dict:
        """
        获取数据集信息（从数据集模块）

        参数:
        - auth (AuthSchema): 认证信息
        - dataset_id (int): 数据集ID

        返回:
        - dict: 数据集信息
        """
        try:
            # 导入数据集模块的 CRUD
            from app.plugin.module_application.dataset.crud import DatasetCRUD

            dataset = await DatasetCRUD(auth).get_by_id_crud(id=dataset_id)
            if not dataset:
                raise CustomException(msg="数据集不存在")

            # 解析 JSON 字段
            dataset_metadata = None
            if dataset.dataset_metadata:
                try:
                    dataset_metadata = json.loads(dataset.dataset_metadata) if isinstance(dataset.dataset_metadata, str) else dataset.dataset_metadata
                except:
                    pass

            return {
                "dataset_id": dataset.id,
                "name": dataset.name,
                "modality": dataset.modality,
                "task_type": dataset.task_type,
                "sample_count": dataset.sample_count,
                "class_count": dataset.class_count,
                "file_size": dataset.file_size,
                "storage_path": dataset.storage_path,
                "dataset_metadata": dataset_metadata,
                "created_time": dataset.created_time
            }
        except CustomException:
            raise
        except Exception as e:
            log.error(f"获取数据集信息失败: {str(e)}")
            raise CustomException(msg=f"获取数据集信息失败: {str(e)}")

    @staticmethod
    def _extract_key_metrics(model: ModelConfigModel) -> dict | None:
        """提取关键性能指标"""
        try:
            performance_metrics = json.loads(model.performance_metrics) if isinstance(model.performance_metrics, str) else model.performance_metrics
            if not performance_metrics:
                return None

            # 只返回最关键的指标
            key_metrics = {}
            for key in ['accuracy', 'precision', 'recall', 'f1_score', 'inference_time', 'params_count']:
                if key in performance_metrics:
                    key_metrics[key] = performance_metrics[key]

            return key_metrics if key_metrics else None
        except:
            return None

    @staticmethod
    def _extract_hardware_summary(model: ModelConfigModel) -> str | None:
        """提取硬件要求简述"""
        try:
            hardware_requirements = json.loads(model.hardware_requirements) if isinstance(model.hardware_requirements, str) else model.hardware_requirements
            if not hardware_requirements:
                return None

            gpu_memory = hardware_requirements.get('min_gpu_memory', 'N/A')
            cpu_cores = hardware_requirements.get('min_cpu_cores', 'N/A')

            return f"GPU: {gpu_memory}, CPU: {cpu_cores} cores"
        except:
            return None

    @staticmethod
    def _extract_default_config_preview(model: ModelConfigModel) -> dict | None:
        """提取默认配置预览（简化版）"""
        try:
            default_config = json.loads(model.default_train_config) if isinstance(model.default_train_config, str) else model.default_train_config
            if not default_config:
                return None

            # 只返回最关键的配置
            preview = {}
            for key in ['learning_rate', 'batch_size', 'epochs', 'optimizer']:
                if key in default_config:
                    preview[key] = default_config[key]

            return preview if preview else None
        except:
            return None


class ModelConfigService:
    """模型配置服务"""

    @classmethod
    async def detail_service(cls, auth: AuthSchema, id: int) -> dict:
        """
        获取模型配置详情

        参数:
        - auth (AuthSchema): 认证信息
        - id (int): 模型配置ID

        返回:
        - dict: 模型配置详情
        """
        model = await ModelConfigCRUD(auth).get_by_id_crud(id=id)
        if not model:
            raise CustomException(msg="模型配置不存在")
        return ModelDetailSchema.model_validate(model).model_dump()

    @classmethod
    async def list_service(
        cls,
        auth: AuthSchema,
        search: ModelConfigQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None
    ) -> list[dict]:
        """
        模型配置列表查询

        参数:
        - auth (AuthSchema): 认证信息
        - search (ModelConfigQueryParam | None): 查询参数
        - order_by (list[dict[str, str]] | None): 排序参数

        返回:
        - list[dict]: 模型配置列表
        """
        search_dict = search.__dict__ if search else None
        model_list = await ModelConfigCRUD(auth).list_crud(search=search_dict, order_by=order_by)
        return [ModelCardSchema.model_validate(model).model_dump() for model in model_list]

    @classmethod
    async def page_service(
        cls,
        auth: AuthSchema,
        page_no: int,
        page_size: int,
        search: ModelConfigQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None
    ) -> dict:
        """
        模型配置分页查询

        参数:
        - auth (AuthSchema): 认证信息
        - page_no (int): 页码
        - page_size (int): 每页数量
        - search (ModelConfigQueryParam | None): 查询参数
        - order_by (list[dict[str, str]] | None): 排序参数

        返回:
        - dict: 分页数据
        """
        search_dict = search.__dict__ if search else {}
        order_by_list = order_by or [{'priority': 'desc'}, {'created_time': 'desc'}]
        offset = (page_no - 1) * page_size

        result = await ModelConfigCRUD(auth).page_crud(
            offset=offset,
            limit=page_size,
            order_by=order_by_list,
            search=search_dict
        )
        return result

    @classmethod
    async def create_service(cls, auth: AuthSchema, data: ModelConfigCreateSchema) -> dict:
        """
        创建模型配置

        参数:
        - auth (AuthSchema): 认证信息
        - data (ModelConfigCreateSchema): 创建数据

        返回:
        - dict: 创建的模型配置
        """
        model = await ModelConfigCRUD(auth).create_crud(data=data)
        log.info(f"创建模型配置成功: {data.model_name}")
        return ModelConfigOutSchema.model_validate(model).model_dump()

    @classmethod
    async def update_service(cls, auth: AuthSchema, id: int, data: ModelConfigUpdateSchema) -> dict:
        """
        更新模型配置

        参数:
        - auth (AuthSchema): 认证信息
        - id (int): 模型配置ID
        - data (ModelConfigUpdateSchema): 更新数据

        返回:
        - dict: 更新后的模型配置
        """
        model = await ModelConfigCRUD(auth).get_by_id_crud(id=id)
        if not model:
            raise CustomException(msg="模型配置不存在")

        updated_model = await ModelConfigCRUD(auth).update_crud(id=id, data=data)
        log.info(f"更新模型配置成功: ID={id}")
        return ModelConfigOutSchema.model_validate(updated_model).model_dump()

    @classmethod
    async def delete_service(cls, auth: AuthSchema, ids: list[int]) -> None:
        """
        删除模型配置

        参数:
        - auth (AuthSchema): 认证信息
        - ids (list[int]): 模型配置ID列表
        """
        if len(ids) < 1:
            raise CustomException(msg="删除对象不能为空")

        for id in ids:
            model = await ModelConfigCRUD(auth).get_by_id_crud(id=id)
            if not model:
                raise CustomException(msg=f"模型配置不存在: ID={id}")

        await ModelConfigCRUD(auth).delete_crud(ids=ids)
        log.info(f"删除模型配置成功: IDs={ids}")

    @classmethod
    async def statistics_service(cls, auth: AuthSchema) -> dict:
        """
        获取模型配置统计信息

        参数:
        - auth (AuthSchema): 认证信息

        返回:
        - dict: 统计信息
        """
        stats = await ModelConfigCRUD(auth).get_statistics()
        return stats

    @classmethod
    async def get_popular_models_service(
        cls,
        auth: AuthSchema,
        top_k: int = 10
    ) -> list[dict]:
        """
        获取热门模型

        参数:
        - auth (AuthSchema): 认证信息
        - top_k (int): 返回数量

        返回:
        - list[dict]: 热门模型列表
        """
        models = await ModelConfigCRUD(auth).get_popular_models(top_k=top_k, only_active=True)
        return [ModelCardSchema.model_validate(model).model_dump() for model in models]

    @classmethod
    async def increment_usage_service(cls, auth: AuthSchema, model_id: int) -> None:
        """
        增加模型使用次数

        参数:
        - auth (AuthSchema): 认证信息
        - model_id (int): 模型配置ID
        """
        await ModelConfigCRUD(auth).increment_usage_count(model_id=model_id)
        log.info(f"模型使用次数+1: ID={model_id}")

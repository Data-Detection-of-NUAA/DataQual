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
    DatasetInfoForTrain,
    TrainTaskCreateRequest,
    TrainTaskResponse,
    TrainTaskListResponse,
    TrainConfigSchema,
    TrainProgressResponse,
    TrainProgressCurveResponse,
    TrainProgressRecordRequest
)
from .crud import ModelConfigCRUD, TrainTaskCRUD, TrainProgressCRUD
from .model import ModelConfigModel, TrainTaskModel

# 尝试导入新的模型池管理器架构
try:
    from .engine_modalities import ModelPoolManager
    USE_NEW_MODEL_POOL = True
    log.info("新模型池架构已加载")
except ImportError as e:
    USE_NEW_MODEL_POOL = False
    log.warning(f"新模型池架构未加载，使用传统数据库查询: {e}")


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

            # 2. 从数据库查询候选模型（优先使用新架构）
            crud = ModelConfigCRUD(auth)

            # 尝试使用新的模型池管理器
            if USE_NEW_MODEL_POOL:
                try:
                    log.info(f"使用新模型池架构查询模型: modality={modality}")
                    # 获取新架构中的模型列表
                    available_models = ModelPoolManager.list_models(modality)
                    log.info(f"新架构返回 {len(available_models)} 个模型")

                    # 如果新架构返回了模型，从数据库中查询这些模型的详细信息
                    if available_models:
                        # available_models 已经是模型名称列表（字符串列表）
                        # 从数据库查询这些模型的配置
                        candidate_models = []
                        for model_name in available_models:
                            model = await crud.get_by_model_name(model_name)
                            if model and (not request.only_active or model.status == 'active'):
                                candidate_models.append(model)

                        log.info(f"从数据库匹配到 {len(candidate_models)} 个模型配置")
                    else:
                        # 新架构没有返回模型，使用传统查询
                        log.info("新架构未返回模型，回退到传统数据库查询")
                        candidate_models = await crud.recommend_models(
                            modality=modality,
                            task_type=task_type,
                            top_k=request.top_k * 2,
                            only_active=request.only_active
                        )
                except Exception as e:
                    # 新架构失败，回退到传统查询
                    log.warning(f"新模型池架构查询失败，回退到传统查询: {e}")
                    candidate_models = await crud.recommend_models(
                        modality=modality,
                        task_type=task_type,
                        top_k=request.top_k * 2,
                        only_active=request.only_active
                    )
            else:
                # 使用传统数据库查询
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


class TrainConfigRecommendationService:
    """训练参数推荐服务（对应使用手册第三步：第61-156行）"""

    @staticmethod
    def recommend_train_config(
        dataset_info: dict,
        model_config: dict
    ) -> TrainConfigSchema:
        """
        推荐训练超参数配置

        根据使用手册第61-156行的推荐算法逻辑

        参数:
        - dataset_info: 数据集信息
        - model_config: 模型配置

        返回:
        - TrainConfigSchema: 推荐的训练配置
        """
        sample_count = dataset_info.get("sample_count", 10000)
        class_count = dataset_info.get("class_count", 10)
        modality = dataset_info.get("modality", "image")

        # 从模型配置中提取信息
        default_config = model_config.get("default_train_config", {})
        if isinstance(default_config, str):
            try:
                default_config = json.loads(default_config)
            except:
                default_config = {}

        # 1. 推荐批次大小（第98-106行）
        if sample_count < 1000:
            batch_size = 16
        elif sample_count < 10000:
            batch_size = 32
        elif sample_count < 100000:
            batch_size = 64
        else:
            batch_size = 128

        # 2. 推荐优化器（第138-156行）
        optimizer = "adam"  # 默认推荐Adam（最稳定）

        if sample_count > 100000:
            optimizer = "sgd"  # 大数据集用SGD可能获得更好泛化

        if modality == "text" and sample_count > 50000:
            optimizer = "adamw"  # 文本任务常用AdamW

        # 简单任务的优化器
        if sample_count < 1000 and class_count < 5:
            optimizer = "sgd"  # 简单任务用SGD足够

        # 3. 推荐学习率（第72-97行）
        base_learning_rate = 0.001  # 默认基准

        # 根据优化器调整
        if optimizer == "sgd":
            learning_rate = base_learning_rate * 10  # SGD需要更大学习率
        elif optimizer == "adam":
            learning_rate = base_learning_rate  # Adam用默认值
        elif optimizer == "rmsprop":
            learning_rate = base_learning_rate * 2  # RMSprop中等
        else:
            learning_rate = base_learning_rate

        # 根据批次大小调整
        if batch_size > 128:
            learning_rate = learning_rate * 2  # 大批次可增大学习率
        elif batch_size < 32:
            learning_rate = learning_rate / 2  # 小批次减小学习率

        # 限制在合理范围 [0.0001, 0.01]
        learning_rate = max(min(learning_rate, 0.01), 0.0001)

        # 4. 推荐训练轮数（第108-136行）
        if sample_count < 5000:
            base_epochs = 100  # 小数据集易过拟合，需更多轮次
        elif sample_count < 20000:
            base_epochs = 80
        elif sample_count < 100000:
            base_epochs = 50
        elif sample_count < 500000:
            base_epochs = 30
        else:
            base_epochs = 20

        # 根据任务复杂度调整（类别数反映复杂度）
        if class_count > 20:
            epochs = int(base_epochs * 1.5)  # 多分类任务需要更多训练
        elif class_count < 3:
            epochs = int(base_epochs * 0.8)  # 二分类任务可减少轮数
        else:
            epochs = base_epochs

        # 限制范围 [10, 200]
        epochs = max(min(epochs, 200), 10)

        # 5. 其他默认配置
        return TrainConfigSchema(
            learning_rate=learning_rate,
            batch_size=batch_size,
            epochs=epochs,
            optimizer=optimizer,
            loss_function=default_config.get("loss_function", "cross_entropy"),
            weight_decay=default_config.get("weight_decay", 0.0001),
            momentum=default_config.get("momentum", 0.9) if optimizer == "sgd" else None,
            lr_scheduler=default_config.get("lr_scheduler", "step"),
            early_stopping=True,
            early_stopping_patience=10,
            data_augmentation=True if sample_count < 50000 else False,
            validation_split=0.2,
            seed=42,
            num_workers=4,
            pin_memory=True
        )


class TrainTaskService:
    """训练任务服务（对应使用手册第四步：第162-255行）"""

    @classmethod
    async def create_task_service(
        cls,
        auth: AuthSchema,
        request: TrainTaskCreateRequest
    ) -> dict:
        """
        创建训练任务

        对应使用手册第164-193行

        参数:
        - auth: 认证信息
        - request: 训练任务创建请求

        返回:
        - dict: 创建的训练任务信息
        """
        try:
            # 1. 获取数据集信息（快照）
            dataset_info = await cls._get_dataset_info(auth, request.dataset_id)

            # 2. 获取模型配置信息（快照）
            model_config = await cls._get_model_config_info(auth, request.model_config_id)

            # 3. 创建训练任务
            task_crud = TrainTaskCRUD(auth)
            task = await task_crud.create_task_crud(
                data=request,
                dataset_info=dataset_info,
                model_config=model_config
            )

            # 4. 增加模型使用次数
            await ModelConfigCRUD(auth).increment_usage_count(model_id=request.model_config_id)

            # 5. 转换为响应Schema
            response = TrainTaskResponse.model_validate(task)

            # 6. 启动训练引擎（异步执行）
            await cls._start_training_engine(task, dataset_info, model_config, request.train_config.model_dump(), auth)

            log.info(f"创建训练任务成功: task_id={task.task_id}, user_id={auth.user.id}")
            return response.model_dump()

        except CustomException:
            raise
        except Exception as e:
            log.error(f"创建训练任务失败: {str(e)}")
            raise CustomException(msg=f"创建训练任务失败: {str(e)}")

    @classmethod
    async def get_task_detail_service(
        cls,
        auth: AuthSchema,
        task_id: str
    ) -> dict:
        """
        获取训练任务详情

        参数:
        - auth: 认证信息
        - task_id: 任务ID

        返回:
        - dict: 任务详情
        """
        try:
            task = await TrainTaskCRUD(auth).get_by_task_id(task_id)
            if not task:
                raise CustomException(msg=f"任务 '{task_id}' 不存在")

            response = TrainTaskResponse.model_validate(task)
            return response.model_dump()

        except CustomException:
            raise
        except Exception as e:
            log.error(f"获取任务详情失败: {str(e)}")
            raise CustomException(msg=f"获取任务详情失败: {str(e)}")

    @classmethod
    async def get_task_list_service(
        cls,
        auth: AuthSchema,
        status: str | None = None,
        dataset_id: int | None = None,
        model_config_id: int | None = None,
        page: int = 1,
        page_size: int = 10
    ) -> dict:
        """
        获取训练任务列表（分页）

        参数:
        - auth: 认证信息
        - status: 状态过滤
        - dataset_id: 数据集ID过滤
        - model_config_id: 模型配置ID过滤
        - page: 页码
        - page_size: 每页数量

        返回:
        - dict: 分页数据
        """
        try:
            tasks, total = await TrainTaskCRUD(auth).page_crud(
                page=page,
                page_size=page_size,
                status=status,
                dataset_id=dataset_id,
                model_config_id=model_config_id,
                user_id=auth.user.id  # 只返回当前用户的任务
            )

            # 转换为列表响应Schema
            task_list = [TrainTaskListResponse.model_validate(task).model_dump() for task in tasks]

            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": task_list
            }

        except Exception as e:
            log.error(f"获取任务列表失败: {str(e)}")
            raise CustomException(msg=f"获取任务列表失败: {str(e)}")

    @classmethod
    async def update_task_status_service(
        cls,
        auth: AuthSchema | None,
        task_id: str,
        status: str,
        error_message: str | None = None
    ) -> dict:
        """
        更新训练任务状态

        参数:
        - auth: 认证信息（内部调用时可为None）
        - task_id: 任务ID
        - status: 新状态
        - error_message: 错误信息

        返回:
        - dict: 更新后的任务信息
        """
        # 如果auth为None，创建临时数据库会话
        db_session = None
        temp_auth = auth

        try:
            if auth is None:
                from app.core.database import async_db_session
                db_session = async_db_session()
                temp_auth = AuthSchema(
                    user=None,
                    check_data_scope=False,
                    db=db_session
                )

            task = await TrainTaskCRUD(temp_auth).update_task_status(
                task_id=task_id,
                status=status,
                error_message=error_message
            )

            response = TrainTaskResponse.model_validate(task)
            log.info(f"更新任务状态成功: task_id={task_id}, status={status}")

            # WebSocket广播状态变更
            try:
                from .ws import broadcast_status_change
                old_status = response.status  # 实际上这里应该是更新前的状态，但简化处理
                await broadcast_status_change(task_id, old_status, status)
            except Exception as e:
                log.warning(f"WebSocket广播状态变更失败: {e}")

            # 如果任务进入终止状态，停止日志流
            terminal_statuses = ['completed', 'failed', 'cancelled']
            if status in terminal_statuses:
                try:
                    await LogStreamer.stop_streaming(task_id)
                    log.info(f"日志流已停止: task_id={task_id}")
                except Exception as stream_error:
                    log.warning(f"停止日志流失败: {stream_error}")

            return response.model_dump()

        except CustomException:
            # 如果有临时会话，回滚事务
            if db_session is not None:
                await db_session.rollback()
            raise
        except Exception as e:
            # 如果有临时会话，回滚事务
            if db_session is not None:
                await db_session.rollback()
            log.error(f"更新任务状态失败: {str(e)}")
            raise CustomException(msg=f"更新任务状态失败: {str(e)}")
        finally:
            # 提交并关闭临时数据库会话
            if db_session is not None:
                try:
                    await db_session.commit()
                except Exception as e:
                    log.error(f"提交数据库事务失败: {str(e)}")
                    await db_session.rollback()
                finally:
                    await db_session.close()

    @classmethod
    async def delete_task_service(
        cls,
        auth: AuthSchema,
        task_id: str
    ) -> None:
        """
        删除训练任务

        参数:
        - auth: 认证信息
        - task_id: 任务ID
        """
        try:
            await TrainTaskCRUD(auth).delete_task_crud(task_id)
            log.info(f"删除训练任务成功: task_id={task_id}")

        except CustomException:
            raise
        except Exception as e:
            log.error(f"删除训练任务失败: {str(e)}")
            raise CustomException(msg=f"删除训练任务失败: {str(e)}")

    @classmethod
    async def get_latest_progress_service(
        cls,
        auth: AuthSchema,
        task_id: str
    ) -> dict | None:
        """
        获取训练任务的最新进度

        参数:
        - auth: 认证信息
        - task_id: 任务ID

        返回:
        - dict | None: 最新进度
        """
        try:
            progress = await TrainProgressCRUD(auth).get_latest_progress(task_id)
            if not progress:
                return None

            response = TrainProgressResponse.model_validate(progress)
            result = response.model_dump()

            return result

        except Exception as e:
            log.error(f"获取最新进度失败: {str(e)}")
            raise CustomException(msg=f"获取最新进度失败: {str(e)}")

    @classmethod
    async def get_progress_curve_service(
        cls,
        auth: AuthSchema,
        task_id: str,
        metrics: list[str] | None = None
    ) -> dict:
        """
        获取训练曲线数据

        参数:
        - auth: 认证信息
        - task_id: 任务ID
        - metrics: 需要的指标列表

        返回:
        - dict: 训练曲线数据
        """
        try:
            # 验证任务存在
            task = await TrainTaskCRUD(auth).get_by_task_id(task_id)
            if not task:
                raise CustomException(msg=f"任务 '{task_id}' 不存在")

            # 获取曲线数据
            curve_data = await TrainProgressCRUD(auth).get_progress_curve_data(
                task_id=task_id,
                metrics=metrics
            )

            response = TrainProgressCurveResponse(
                task_id=task_id,
                total_epochs=task.total_epochs,
                current_epoch=task.current_epoch,
                data_points=curve_data
            )

            return response.model_dump()

        except CustomException:
            raise
        except Exception as e:
            log.error(f"获取训练曲线失败: {str(e)}")
            raise CustomException(msg=f"获取训练曲线失败: {str(e)}")

    @classmethod
    async def update_task_result_service(
        cls,
        auth: AuthSchema | None,
        task_id: str,
        final_metrics: dict,
        model_save_path: str | None = None,
        result_file_path: str | None = None
    ) -> dict:
        """
        更新训练任务结果（训练完成时调用）

        对应使用手册第252-255行

        参数:
        - auth: 认证信息（内部调用时可为None）
        - task_id: 任务ID
        - final_metrics: 最终评估指标
        - model_save_path: 模型保存路径
        - result_file_path: 结果文件路径

        返回:
        - dict: 更新后的任务信息
        """
        # 如果auth为None，创建临时数据库会话
        db_session = None
        temp_auth = auth

        try:
            if auth is None:
                from app.core.database import async_db_session
                db_session = async_db_session()
                temp_auth = AuthSchema(
                    user=None,
                    check_data_scope=False,
                    db=db_session
                )

            task = await TrainTaskCRUD(temp_auth).update_task_result(
                task_id=task_id,
                final_metrics=final_metrics,
                model_save_path=model_save_path,
                result_file_path=result_file_path
            )

            response = TrainTaskResponse.model_validate(task)
            log.info(f"更新任务结果成功: task_id={task_id}")
            return response.model_dump()

        except CustomException:
            # 如果有临时会话，回滚事务
            if db_session is not None:
                await db_session.rollback()
            raise
        except Exception as e:
            # 如果有临时会话，回滚事务
            if db_session is not None:
                await db_session.rollback()
            log.error(f"更新任务结果失败: {str(e)}")
            raise CustomException(msg=f"更新任务结果失败: {str(e)}")
        finally:
            # 提交并关闭临时数据库会话
            if db_session is not None:
                try:
                    await db_session.commit()
                except Exception as e:
                    log.error(f"提交数据库事务失败: {str(e)}")
                    await db_session.rollback()
                finally:
                    await db_session.close()

    @classmethod
    async def get_train_config_recommendation_service(
        cls,
        auth: AuthSchema,
        dataset_id: int,
        model_config_id: int
    ) -> dict:
        """
        获取训练参数推荐

        对应使用手册第三步（第61-156行）

        参数:
        - auth: 认证信息
        - dataset_id: 数据集ID
        - model_config_id: 模型配置ID

        返回:
        - dict: 推荐的训练配置
        """
        try:
            # 1. 获取数据集信息
            dataset_info = await cls._get_dataset_info(auth, dataset_id)

            # 2. 获取模型配置信息
            model_config_dict = await cls._get_model_config_info(auth, model_config_id)

            # 3. 调用推荐算法
            recommended_config = TrainConfigRecommendationService.recommend_train_config(
                dataset_info=dataset_info,
                model_config=model_config_dict
            )

            log.info(f"生成训练参数推荐: dataset_id={dataset_id}, model_config_id={model_config_id}")
            return recommended_config.model_dump()

        except CustomException:
            raise
        except Exception as e:
            log.error(f"获取训练参数推荐失败: {str(e)}")
            raise CustomException(msg=f"获取训练参数推荐失败: {str(e)}")

    @classmethod
    async def _get_dataset_info(cls, auth: AuthSchema, dataset_id: int) -> dict:
        """
        获取数据集信息（用于快照）

        参数:
        - auth: 认证信息
        - dataset_id: 数据集ID

        返回:
        - dict: 数据集信息
        """
        try:
            from app.plugin.module_application.dataset.crud import DatasetCRUD

            dataset = await DatasetCRUD(auth).get_by_id_crud(id=dataset_id)
            if not dataset:
                raise CustomException(msg="数据集不存在")

            # 解析 dataset_metadata
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
                "dataset_metadata": dataset_metadata
            }
        except CustomException:
            raise
        except Exception as e:
            log.error(f"获取数据集信息失败: {str(e)}")
            raise CustomException(msg=f"获取数据集信息失败: {str(e)}")

    @classmethod
    def _get_device(cls, train_config: dict) -> str:
        """
        获取训练设备（自动检测CUDA是否可用）

        参数:
        - train_config: 训练配置

        返回:
        - str: 设备名称 ("cuda" 或 "cpu")
        """
        try:
            import torch

            # 从配置中获取设备偏好
            device_config = train_config.get("device", "auto")

            # 如果明确指定了cpu，直接返回
            if device_config == "cpu":
                log.info("使用CPU设备进行训练")
                return "cpu"

            # 检查CUDA是否可用
            if torch.cuda.is_available():
                log.info(f"检测到CUDA可用，使用GPU设备进行训练")
                return "cuda"
            else:
                log.warning("CUDA不可用，自动切换到CPU设备")
                return "cpu"

        except Exception as e:
            log.warning(f"检测设备时出错: {e}，使用CPU设备")
            return "cpu"

    @classmethod
    def _build_optimizer_params(cls, train_config: dict) -> dict:
        """
        构建优化器参数（根据优化器类型动态构建）

        参数:
        - train_config: 训练配置

        返回:
        - dict: 优化器参数
        """
        optimizer_type = train_config.get("optimizer", "adam")
        params = {
            "weight_decay": train_config.get("weight_decay", 0.0001)
        }

        # 只有SGD优化器才添加momentum参数
        if optimizer_type == "sgd":
            params["momentum"] = train_config.get("momentum", 0.9)

        return params

    @classmethod
    async def _start_training_engine(
        cls,
        task: Any,
        dataset_info: dict,
        model_config: dict,
        train_config: dict,
        auth: AuthSchema
    ):
        """
        启动训练执行引擎

        参数:
        - task: 训练任务对象
        - dataset_info: 数据集信息
        - model_config: 模型配置信息
        - train_config: 训练配置
        - auth: 认证信息
        """
        import subprocess
        import sys
        from pathlib import Path
        import zipfile
        import os

        try:
            # 1. 检查并解压数据集（如果是ZIP文件）
            dataset_path = dataset_info["storage_path"]
            if dataset_path.endswith('.zip'):
                # 生成解压目录路径
                extract_dir = dataset_path.replace('.zip', '_extracted')

                # 如果解压目录不存在，则解压
                if not os.path.exists(extract_dir):
                    log.info(f"开始解压数据集: {dataset_path} -> {extract_dir}")
                    try:
                        with zipfile.ZipFile(dataset_path, 'r') as zip_ref:
                            zip_ref.extractall(extract_dir)
                        log.info(f"数据集解压成功: {extract_dir}")
                    except Exception as e:
                        log.error(f"数据集解压失败: {str(e)}")
                        raise CustomException(msg=f"数据集解压失败: {str(e)}")
                else:
                    log.info(f"数据集已解压，使用现有目录: {extract_dir}")

                # 更新数据集路径为解压后的目录
                dataset_path = extract_dir

                # 检查是否有单个根目录（常见的ZIP结构）
                items = os.listdir(dataset_path)
                if len(items) == 1 and os.path.isdir(os.path.join(dataset_path, items[0])):
                    # 如果只有一个子目录，使用该子目录作为数据集路径
                    dataset_path = os.path.join(dataset_path, items[0])
                    log.info(f"检测到单根目录结构，使用子目录: {dataset_path}")

            # 2. 自动检测类别数（如果数据集信息中没有）
            num_classes = dataset_info.get("class_count")
            if not num_classes and os.path.exists(dataset_path):
                try:
                    # 统计数据集目录下的子目录数量（每个子目录代表一个类别）
                    class_dirs = [d for d in os.listdir(dataset_path)
                                 if os.path.isdir(os.path.join(dataset_path, d))]
                    num_classes = len(class_dirs)
                    log.info(f"自动检测到类别数: {num_classes}")
                except Exception as e:
                    log.warning(f"无法自动检测类别数: {e}，使用默认值10")
                    num_classes = 10
            else:
                num_classes = num_classes or 10

            # 3. 计算输出目录（使用绝对路径）
            from pathlib import Path as PathLib
            backend_root = PathLib(__file__).parent.parent.parent.parent.parent  # backend 目录
            task_output_dir = backend_root / "static" / "train" / "tasks" / task.task_id

            # 4. 准备训练配置
            engine_config = {
                # 任务标识
                "task_id": task.task_id,

                # 数据集信息
                "dataset_id": dataset_info["dataset_id"],
                "dataset_path": dataset_path,
                "dataset_modality": dataset_info["modality"],
                "num_classes": num_classes,
                "sample_count": dataset_info.get("sample_count") or 1000,

                # 模型配置
                "model_config_id": model_config["model_config_id"],
                "model_name": model_config["model_name"],
                "model_architecture": model_config.get("architecture", {}),
                "pretrained": model_config.get("pretrained", True),

                # 训练超参数（从用户选择的 train_config 获取）
                "num_epochs": train_config.get("epochs", 50),
                "batch_size": train_config.get("batch_size", 32),
                "learning_rate": train_config.get("learning_rate", 0.001),

                # 优化器配置
                "optimizer": train_config.get("optimizer", "adam"),
                "optimizer_params": cls._build_optimizer_params(train_config),

                # 学习率调度器
                "scheduler": train_config.get("lr_scheduler") or train_config.get("scheduler") or "step",
                "scheduler_params": {
                    "step_size": train_config.get("scheduler_step_size", 30),
                    "gamma": train_config.get("scheduler_gamma", 0.1)
                },

                # 训练策略
                "early_stopping_patience": train_config.get("early_stopping_patience", 10),
                "checkpoint_freq": train_config.get("checkpoint_freq", 5),

                # 数据增强
                "use_augmentation": train_config.get("data_augmentation", True),
                "augmentation_config": train_config.get("augmentation_config", {}),

                # 验证集配置
                "val_split": train_config.get("validation_split", 0.2),

                # 硬件配置
                "device": cls._get_device(train_config),
                "use_amp": train_config.get("use_amp", True),
                "num_workers": train_config.get("num_workers", 4),

                # 输出配置
                "output_dir": str(task_output_dir),

                # 其他配置
                "seed": train_config.get("seed", 42),

                # API 回调地址
                "api_base_url": "http://localhost:8001",
                "api_token": ""  # TODO: 如果需要认证，传递 token
            }

            # 5. 创建输出目录
            output_dir = Path(engine_config["output_dir"])
            output_dir.mkdir(parents=True, exist_ok=True)

            # 6. 保存配置文件
            config_file = output_dir / "training_config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(engine_config, f, indent=2, ensure_ascii=False)

            log.info(f"训练配置文件已生成: {config_file}")

            # 7. 启动训练引擎（异步子进程）
            # 使用当前文件的路径来定位 engine.py
            current_file = Path(__file__)  # service.py 的路径
            engine_script = current_file.parent / "engine.py"  # 同目录下的 engine.py

            # 使用 PowerShell 启动 Python 子进程
            cmd = [
                sys.executable,  # Python 解释器路径
                str(engine_script.absolute()),
                "--config", str(config_file.absolute())
            ]

            log.info(f"启动训练引擎: {' '.join(cmd)}")

            # 创建日志文件
            log_file = output_dir / "engine.log"

            # 异步启动子进程（不等待完成），将输出重定向到日志文件
            with open(log_file, 'w', encoding='utf-8') as f:
                subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,  # 将stderr合并到stdout
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
                )

            log.info(f"训练引擎已启动 (后台运行): task_id={task.task_id}, 日志文件: {log_file}")

            # 8. 启动日志流（监控engine.log并通过WebSocket广播）
            try:
                await LogStreamer.start_streaming(task.task_id, str(log_file))
                log.info(f"日志流已启动: task_id={task.task_id}")
            except Exception as stream_error:
                log.warning(f"启动日志流失败: {stream_error}")
                # 不影响主流程，继续执行

        except Exception as e:
            log.error(f"启动训练引擎失败: {str(e)}")
            # 不抛出异常，避免影响任务创建流程
            # 可以在这里更新任务状态为 failed
            try:
                await TrainTaskCRUD(auth).update_task_status(
                    task_id=task.task_id,
                    status="failed",
                    error_message=f"启动训练引擎失败: {str(e)}"
                )
            except:
                pass

    @classmethod
    async def _get_model_config_info(cls, auth: AuthSchema, model_config_id: int) -> dict:
        """
        获取模型配置信息（用于快照）

        参数:
        - auth: 认证信息
        - model_config_id: 模型配置ID

        返回:
        - dict: 模型配置信息
        """
        try:
            model = await ModelConfigCRUD(auth).get_by_id_crud(id=model_config_id)
            if not model:
                raise CustomException(msg="模型配置不存在")

            # 解析 JSON 字段
            default_train_config = None
            if model.default_train_config:
                try:
                    default_train_config = json.loads(model.default_train_config) if isinstance(model.default_train_config, str) else model.default_train_config
                except:
                    pass

            performance_metrics = None
            if model.performance_metrics:
                try:
                    performance_metrics = json.loads(model.performance_metrics) if isinstance(model.performance_metrics, str) else model.performance_metrics
                except:
                    pass

            hardware_requirements = None
            if model.hardware_requirements:
                try:
                    hardware_requirements = json.loads(model.hardware_requirements) if isinstance(model.hardware_requirements, str) else model.hardware_requirements
                except:
                    pass

            return {
                "model_config_id": model.id,
                "model_name": model.model_name,
                "display_name": model.display_name,
                "model_version": model.model_version,
                "framework": model.framework,
                "supported_modalities": model.supported_modalities,
                "supported_task_types": model.supported_task_types,
                "default_train_config": default_train_config,
                "performance_metrics": performance_metrics,
                "hardware_requirements": hardware_requirements
            }
        except CustomException:
            raise
        except Exception as e:
            log.error(f"获取模型配置信息失败: {str(e)}")
            raise CustomException(msg=f"获取模型配置信息失败: {str(e)}")

    @classmethod
    async def report_progress_service(
        cls,
        auth: AuthSchema | None,
        task_id: str,
        progress_data: dict
    ) -> dict:
        """
        上报训练进度

        参数:
        - auth: 认证信息（内部调用时可为None）
        - task_id: 任务ID
        - progress_data: 进度数据

        返回:
        - dict: 操作结果
        """
        # 如果auth为None，创建临时数据库会话
        db_session = None
        temp_auth = auth

        try:
            if auth is None:
                from app.core.database import async_db_session
                db_session = async_db_session()
                temp_auth = AuthSchema(
                    user=None,
                    check_data_scope=False,
                    db=db_session
                )

            # 验证任务存在（内部调用时不需要权限检查）
            task = await TrainTaskCRUD(temp_auth).get_by_task_id(task_id)
            if not task:
                raise CustomException(msg=f"任务 '{task_id}' 不存在")

            # 解析进度数据
            current_epoch = progress_data.get("current_epoch", task.current_epoch)
            total_epochs = progress_data.get("total_epochs", task.total_epochs)
            current_step = progress_data.get("current_step")
            total_steps = progress_data.get("total_steps")
            train_loss = progress_data.get("train_loss")
            train_accuracy = progress_data.get("train_accuracy")
            val_loss = progress_data.get("val_loss")
            val_accuracy = progress_data.get("val_accuracy")
            learning_rate = progress_data.get("learning_rate")
            epoch_time = progress_data.get("epoch_time")

            # 计算进度百分比
            progress_percentage = (current_epoch / total_epochs) * 100 if total_epochs > 0 else 0

            # 更新任务进度
            await TrainTaskCRUD(temp_auth).update_task_progress(
                task_id=task_id,
                current_epoch=current_epoch,
                progress_percentage=progress_percentage
            )

            # 创建进度记录
            progress_record = TrainProgressRecordRequest(
                task_id=task_id,
                epoch=current_epoch,
                batch=current_step,
                total_batches=total_steps,
                train_loss=train_loss,
                train_accuracy=train_accuracy,
                val_loss=val_loss,
                val_accuracy=val_accuracy,
                learning_rate=learning_rate,
                epoch_progress=(current_step / total_steps) if total_steps and current_step else None,
                overall_progress=progress_percentage / 100.0,
                additional_metrics={
                    "epoch_time": epoch_time
                } if epoch_time else None
            )

            await TrainProgressCRUD(temp_auth).create_progress_record(progress_record)



            # WebSocket广播进度更新
            try:
                from .ws import broadcast_progress_update
                await broadcast_progress_update(task_id, {
                    "epoch": current_epoch,
                    "current_epoch": current_epoch,
                    "total_epochs": total_epochs,
                    "train_loss": train_loss,
                    "train_accuracy": train_accuracy,
                    "val_loss": val_loss,
                    "val_accuracy": val_accuracy,
                    "learning_rate": learning_rate,
                    "overall_progress": progress_percentage / 100.0,
                    "progress_percentage": progress_percentage
                })
            except Exception as e:
                log.warning(f"WebSocket广播进度失败: {e}")

            return {
                "task_id": task_id,
                "current_epoch": current_epoch,
                "progress_percentage": progress_percentage
            }

        except CustomException:
            # 如果有临时会话，回滚事务
            if db_session is not None:
                await db_session.rollback()
            raise
        except Exception as e:
            # 如果有临时会话，回滚事务
            if db_session is not None:
                await db_session.rollback()
            log.error(f"上报进度失败: {str(e)}")
            raise CustomException(msg=f"上报进度失败: {str(e)}")
        finally:
            # 提交并关闭临时数据库会话
            if db_session is not None:
                try:
                    await db_session.commit()
                except Exception as e:
                    log.error(f"提交数据库事务失败: {str(e)}")
                    await db_session.rollback()
                finally:
                    await db_session.close()

    @classmethod
    async def get_task_result_service(
        cls,
        auth: AuthSchema,
        task_id: str
    ) -> dict:
        """
        获取训练任务结果

        参数:
        - auth: 认证信息
        - task_id: 任务ID

        返回:
        - dict: 结果数据
        """
        try:
            import json
            from pathlib import Path

            # 验证任务存在
            task = await TrainTaskCRUD(auth).get_by_task_id(task_id)
            if not task:
                raise CustomException(msg=f"任务 '{task_id}' 不存在")

            # 检查任务是否完成
            if task.status != "completed":
                raise CustomException(msg="任务尚未完成")

            # 读取result.json文件
            result_path = task.result_file_path
            if not result_path:
                raise CustomException(msg="结果文件路径不存在")

            result_file = Path(result_path)
            if not result_file.exists():
                raise CustomException(msg="结果文件不存在")

            with open(result_file, 'r', encoding='utf-8') as f:
                result_data = json.load(f)

            return result_data

        except CustomException:
            raise
        except Exception as e:
            log.error(f"获取任务结果失败: {str(e)}")
            raise CustomException(msg=f"获取任务结果失败: {str(e)}")

    @classmethod
    async def get_artifact_path_service(
        cls,
        auth: AuthSchema,
        task_id: str,
        relative_path: str
    ) -> str:
        """
        获取产物文件路径

        参数:
        - auth: 认证信息
        - task_id: 任务ID
        - relative_path: 相对路径

        返回:
        - str: 绝对路径
        """
        try:
            from pathlib import Path

            # 验证任务存在
            task = await TrainTaskCRUD(auth).get_by_task_id(task_id)
            if not task:
                raise CustomException(msg=f"任务 '{task_id}' 不存在")

            # 构建任务目录
            task_dir = Path("static/train/tasks") / task_id

            # 构建文件路径
            file_path = task_dir / relative_path

            # 安全检查：确保文件在任务目录内
            file_path = file_path.resolve()
            task_dir = task_dir.resolve()

            if not str(file_path).startswith(str(task_dir)):
                raise CustomException(msg="无效的文件路径")

            return str(file_path)

        except CustomException:
            raise
        except Exception as e:
            log.error(f"获取产物路径失败: {str(e)}")
            raise CustomException(msg=f"获取产物路径失败: {str(e)}")

    @classmethod
    async def get_task_report_service(
        cls,
        auth: AuthSchema,
        task_id: str
    ) -> dict:
        """
        获取训练任务报告

        参数:
        - auth: 认证信息
        - task_id: 任务ID

        返回:
        - dict: 报告数据
        """
        try:
            import json
            from pathlib import Path

            # 验证任务存在
            task = await TrainTaskCRUD(auth).get_by_task_id(task_id)
            if not task:
                raise CustomException(msg=f"任务 '{task_id}' 不存在")

            # 查找reports目录下的json文件
            task_dir = Path("static/train/tasks") / task_id
            reports_dir = task_dir / "reports"

            if not reports_dir.exists():
                raise CustomException(msg="报告目录不存在")

            # 查找json文件（假设有一个主要的报告文件）
            report_files = list(reports_dir.glob("*.json"))
            if not report_files:
                raise CustomException(msg="报告文件不存在")

            # 读取第一个json文件
            report_file = report_files[0]
            with open(report_file, 'r', encoding='utf-8') as f:
                report_data = json.load(f)

            return report_data

        except CustomException:
            raise
        except Exception as e:
            log.error(f"获取任务报告失败: {str(e)}")
            raise CustomException(msg=f"获取任务报告失败: {str(e)}")

    @classmethod
    async def get_task_logs_service(
        cls,
        auth: AuthSchema,
        task_id: str,
        lines: int = 100
    ) -> dict:
        """
        获取训练任务日志

        参数:
        - auth: 认证信息
        - task_id: 任务ID
        - lines: 返回最后N行日志

        返回:
        - dict: 日志数据
        """
        try:
            from pathlib import Path

            # 验证任务存在
            task = await TrainTaskCRUD(auth).get_by_task_id(task_id)
            if not task:
                raise CustomException(msg=f"任务 '{task_id}' 不存在")

            # 查找engine.log文件
            task_dir = Path("static/train/tasks") / task_id
            log_file = task_dir / "engine.log"

            if not log_file.exists():
                return {
                    "task_id": task_id,
                    "logs": [],
                    "total_lines": 0,
                    "message": "日志文件不存在"
                }

            # 读取最后N行日志
            log_lines = []
            try:
                # 尝试多种编码方式读取文件
                encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
                file_content = None
                used_encoding = None

                for encoding in encodings:
                    try:
                        with open(log_file, 'r', encoding=encoding) as f:
                            file_content = f.readlines()
                            used_encoding = encoding
                            break
                    except (UnicodeDecodeError, LookupError):
                        continue

                if file_content is None:
                    # 如果所有编码都失败，使用二进制模式读取并忽略错误
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        file_content = f.readlines()
                        used_encoding = 'utf-8 (with errors ignored)'

                all_lines = file_content
                total_lines = len(all_lines)

                # 获取最后N行
                start_index = max(0, total_lines - lines)
                log_lines = all_lines[start_index:]

                # 解析日志行
                parsed_logs = []
                for line in log_lines:
                    line = line.strip()
                    if line:
                        # 尝试解析日志格式: 时间戳 | 级别 | 消息
                        parts = line.split(' | ', 2)
                        if len(parts) >= 3:
                            parsed_logs.append({
                                "time": parts[0].strip(),
                                "level": parts[1].strip(),
                                "message": parts[2].strip()
                            })
                        else:
                            # 如果格式不匹配，直接使用原始行
                            parsed_logs.append({
                                "time": "",
                                "level": "INFO",
                                "message": line
                            })

                return {
                    "task_id": task_id,
                    "logs": parsed_logs,
                    "total_lines": total_lines,
                    "returned_lines": len(parsed_logs),
                    "encoding": used_encoding
                }

            except Exception as e:
                log.error(f"读取日志文件失败: {str(e)}")
                raise CustomException(msg=f"读取日志文件失败: {str(e)}")

        except CustomException:
            raise
        except Exception as e:
            log.error(f"获取任务日志失败: {str(e)}")
            raise CustomException(msg=f"获取任务日志失败: {str(e)}")


# 日志流管理器
import asyncio
from pathlib import Path as PathLib
from typing import Dict, Optional


class LogStreamer:
    """日志流管理器 - 监控engine.log并通过WebSocket广播"""

    _active_streamers: Dict[str, 'LogStreamer'] = {}

    def __init__(self, task_id: str, log_file_path: str):
        """
        初始化日志流

        参数:
        - task_id: 任务ID
        - log_file_path: 日志文件路径
        """
        self.task_id = task_id
        self.log_file_path = PathLib(log_file_path)
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._last_position = 0

    async def start(self):
        """启动日志流"""
        if self.is_running:
            log.warning(f"日志流已在运行: {self.task_id}")
            return

        self.is_running = True
        self._task = asyncio.create_task(self._stream_logs())
        LogStreamer._active_streamers[self.task_id] = self
        log.info(f"日志流已启动: {self.task_id}")

    async def stop(self):
        """停止日志流"""
        if not self.is_running:
            return

        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        if self.task_id in LogStreamer._active_streamers:
            del LogStreamer._active_streamers[self.task_id]

        log.info(f"日志流已停止: {self.task_id}")

    async def _stream_logs(self):
        """流式读取日志文件并广播"""
        from .ws import broadcast_log_message

        try:
            # 等待日志文件创建
            retry_count = 0
            while not self.log_file_path.exists() and retry_count < 30:
                await asyncio.sleep(1)
                retry_count += 1

            if not self.log_file_path.exists():
                log.warning(f"日志文件不存在: {self.log_file_path}")
                return

            log.info(f"开始监控日志文件: {self.log_file_path}")

            # 打开文件并持续读取
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # 移动到文件末尾（如果有初始位置）
                if self._last_position > 0:
                    f.seek(self._last_position)

                while self.is_running:
                    # 读取新行
                    line = f.readline()

                    if line:
                        # 有新内容，广播
                        line = line.rstrip('\n\r')
                        if line:  # 忽略空行
                            # 解析日志级别
                            level = "INFO"
                            if " - ERROR - " in line:
                                level = "ERROR"
                            elif " - WARNING - " in line:
                                level = "WARNING"
                            elif " - DEBUG - " in line:
                                level = "DEBUG"

                            # 广播日志消息
                            await broadcast_log_message(self.task_id, level, line)

                        # 更新位置
                        self._last_position = f.tell()
                    else:
                        # 没有新内容，等待一会儿
                        await asyncio.sleep(0.5)

        except asyncio.CancelledError:
            log.info(f"日志流被取消: {self.task_id}")
        except Exception as e:
            log.error(f"日志流异常: {self.task_id}, 错误: {e}")

    @classmethod
    async def start_streaming(cls, task_id: str, log_file_path: str):
        """
        启动日志流（类方法）

        参数:
        - task_id: 任务ID
        - log_file_path: 日志文件路径
        """
        # 如果已存在，先停止
        if task_id in cls._active_streamers:
            await cls._active_streamers[task_id].stop()

        # 创建并启动新的流
        streamer = cls(task_id, log_file_path)
        await streamer.start()

    @classmethod
    async def stop_streaming(cls, task_id: str):
        """
        停止日志流（类方法）

        参数:
        - task_id: 任务ID
        """
        if task_id in cls._active_streamers:
            await cls._active_streamers[task_id].stop()

    @classmethod
    def get_active_streamers(cls) -> list[str]:
        """获取所有活跃的日志流任务ID"""
        return list(cls._active_streamers.keys())

# -*- coding: utf-8 -*-

from fastapi import APIRouter, Body, Depends, Path, Query
from fastapi.responses import JSONResponse
from fastapi_limiter.depends import RateLimiter

from app.common.response import SuccessResponse
from app.core.router_class import OperationLogRoute
from app.core.base_params import PaginationQueryParam
from app.core.dependencies import AuthPermission
from app.core.logger import log
from app.api.v1.module_system.auth.schema import AuthSchema

from .service import (
    ModelConfigService,
    ModelRecommendationService,
    TrainConfigRecommendationService,
    TrainTaskService
)
from .schema import (
    ModelConfigCreateSchema,
    ModelConfigUpdateSchema,
    ModelConfigQueryParam,
    ModelRecommendationRequest,
    ModelRecommendationResponse,
    TrainTaskCreateRequest,
    TrainTaskStatusUpdateRequest,
    TrainTaskQueryParam
)


# ==================== 路由定义 ====================

# 注意：module_application会自动添加/application前缀，但我们需要保持/train路径兼容
# 所以手动设置prefix="/train"来覆盖默认的/application前缀
ModelTrainRouter = APIRouter(route_class=OperationLogRoute, prefix="/train", tags=["模型训练管理"])


# ==================== 模型推荐 API ====================

@ModelTrainRouter.post(
    "/recommend",
    summary="模型推荐",
    description="根据数据集信息智能推荐适合的训练模型",
    response_model=ModelRecommendationResponse,
    dependencies=[Depends(RateLimiter(times=30, seconds=60))]
)
async def recommend_models_controller(
    data: ModelRecommendationRequest,
    auth: AuthSchema = Depends(AuthPermission(["module_train:model:recommend"]))
) -> JSONResponse:
    """
    模型推荐

    功能：
    - 根据数据集的模态和任务类型推荐合适的模型
    - 计算模型能力评分（模态匹配度、任务适配度、性能指标等）
    - 返回排序后的推荐列表

    参数:
    - data (ModelRecommendationRequest): 推荐请求
      - dataset_id: 数据集ID（必填）
      - modality: 数据模态类型（可选，为空则从数据集获取）
      - task_type: 任务类型（可选，为空则从数据集获取）
      - top_k: 返回推荐数量（默认5，最多20）
      - only_active: 是否仅返回激活状态的模型（默认True）
    - auth (AuthSchema): 认证信息

    返回:
    - ModelRecommendationResponse: 推荐响应
      - dataset_info: 数据集信息
      - total_recommended: 推荐模型总数
      - recommendations: 推荐模型列表（包含匹配度评分和推荐理由）
      - recommendation_metadata: 推荐元数据

    示例:
    ```json
    {
        "dataset_id": 123,
        "top_k": 5,
        "only_active": true
    }
    ```
    """
    result = await ModelRecommendationService.recommend_models_service(auth=auth, request=data)

    log.info(f"模型推荐成功: dataset_id={data.dataset_id}, 推荐数量={result.total_recommended}")
    return SuccessResponse(
        data=result.model_dump(),
        msg=f"成功推荐 {result.total_recommended} 个模型"
    )


# ==================== 模型配置管理 API ====================

@ModelTrainRouter.get(
    "/model/detail/{id}",
    summary="获取模型配置详情",
    description="根据ID获取模型配置的详细信息",
    dependencies=[Depends(RateLimiter(times=30, seconds=10))]
)
async def get_model_detail_controller(
    id: int = Path(..., description="模型配置ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_train:model:detail"]))
) -> JSONResponse:
    """
    获取模型配置详情

    参数:
    - id (int): 模型配置ID
    - auth (AuthSchema): 认证信息

    返回:
    - JSONResponse: 模型配置详情
      - 包含完整的模型信息、性能指标、硬件要求、训练配置等
    """
    result = await ModelConfigService.detail_service(auth=auth, id=id)
    log.info(f"获取模型配置详情成功: id={id}")
    return SuccessResponse(data=result, msg="获取模型配置详情成功")


@ModelTrainRouter.get(
    "/model/list",
    summary="查询模型配置列表",
    description="分页查询模型配置列表，支持多种筛选条件",
    dependencies=[Depends(RateLimiter(times=30, seconds=10))]
)
async def get_model_list_controller(
    page: PaginationQueryParam = Depends(),
    search: ModelConfigQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(["module_train:model:query"]))
) -> JSONResponse:
    """
    查询模型配置列表（分页）

    参数:
    - page (PaginationQueryParam): 分页参数
      - page_no: 页码
      - page_size: 每页数量
      - order_by: 排序字段
    - search (ModelConfigQueryParam): 查询参数
      - model_name: 模型名称（模糊查询）
      - display_name: 显示名称（模糊查询）
      - framework: 深度学习框架
      - status: 模型状态（active/inactive/deprecated）
      - modality: 适用模态（模糊匹配）
      - task_type: 适用任务类型（模糊匹配）
      - tag: 标签（模糊匹配）
      - priority_min: 最小优先级
      - priority_max: 最大优先级
      - created_time: 创建时间范围
    - auth (AuthSchema): 认证信息

    返回:
    - JSONResponse: 分页数据
      - 包含模型卡片列表（轻量级信息）
    """
    result = await ModelConfigService.page_service(
        auth=auth,
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by
    )
    log.info("查询模型配置列表成功")
    return SuccessResponse(data=result, msg="查询模型配置列表成功")


@ModelTrainRouter.post(
    "/model/create",
    summary="创建模型配置",
    description="创建新的模型配置（需管理员权限）",
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
)
async def create_model_controller(
    data: ModelConfigCreateSchema,
    auth: AuthSchema = Depends(AuthPermission(["module_train:model:create"]))
) -> JSONResponse:
    """
    创建模型配置

    参数:
    - data (ModelConfigCreateSchema): 模型配置创建数据
      - model_name: 模型名称（唯一标识）
      - display_name: 显示名称
      - model_version: 模型版本号
      - supported_modalities: 适用模态列表
      - supported_task_types: 适用任务类型列表
      - description: 模型简介
      - default_train_config: 默认训练配置（必须包含learning_rate, batch_size, epochs）
      - pretrained_weights: 预训练权重信息（可选）
      - performance_metrics: 性能指标（可选）
      - hardware_requirements: 硬件要求（可选）
      - framework: 深度学习框架（默认PyTorch）
      - priority: 推荐优先级（默认0）
      - status: 模型状态（默认active）
      - tags: 标签列表（可选）
    - auth (AuthSchema): 认证信息

    返回:
    - JSONResponse: 创建的模型配置

    示例:
    ```json
    {
        "model_name": "ResNet50",
        "display_name": "ResNet-50",
        "supported_modalities": ["image"],
        "supported_task_types": ["image_classification", "object_detection"],
        "description": "经典的深度残差网络，50层结构",
        "default_train_config": {
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 100,
            "optimizer": "Adam"
        },
        "priority": 80
    }
    ```
    """
    result = await ModelConfigService.create_service(auth=auth, data=data)
    log.info(f"创建模型配置成功: {data.model_name}")
    return SuccessResponse(data=result, msg="创建模型配置成功")


@ModelTrainRouter.put(
    "/model/update/{id}",
    summary="更新模型配置",
    description="更新模型配置信息（需管理员权限）",
    dependencies=[Depends(RateLimiter(times=20, seconds=60))]
)
async def update_model_controller(
    data: ModelConfigUpdateSchema,
    id: int = Path(..., description="模型配置ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_train:model:update"]))
) -> JSONResponse:
    """
    更新模型配置

    参数:
    - data (ModelConfigUpdateSchema): 更新数据（所有字段可选）
    - id (int): 模型配置ID
    - auth (AuthSchema): 认证信息

    返回:
    - JSONResponse: 更新后的模型配置
    """
    result = await ModelConfigService.update_service(auth=auth, id=id, data=data)
    log.info(f"更新模型配置成功: id={id}")
    return SuccessResponse(data=result, msg="更新模型配置成功")


@ModelTrainRouter.delete(
    "/model/delete",
    summary="删除模型配置",
    description="批量删除模型配置（需管理员权限）",
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
)
async def delete_model_controller(
    ids: list[int] = Body(..., description="模型配置ID列表"),
    auth: AuthSchema = Depends(AuthPermission(["module_train:model:delete"]))
) -> JSONResponse:
    """
    删除模型配置

    参数:
    - ids (list[int]): 模型配置ID列表
    - auth (AuthSchema): 认证信息

    返回:
    - JSONResponse: 删除结果
    """
    await ModelConfigService.delete_service(auth=auth, ids=ids)
    log.info(f"删除模型配置成功: ids={ids}")
    return SuccessResponse(msg="删除模型配置成功")


@ModelTrainRouter.get(
    "/model/statistics",
    summary="模型配置统计",
    description="获取模型配置统计信息",
    dependencies=[Depends(RateLimiter(times=30, seconds=10))]
)
async def get_model_statistics_controller(
    auth: AuthSchema = Depends(AuthPermission(["module_train:model:statistics"]))
) -> JSONResponse:
    """
    获取模型配置统计信息

    参数:
    - auth (AuthSchema): 认证信息

    返回:
    - JSONResponse: 统计信息
      - total_count: 总模型数量
      - active_count: 激活模型数量
      - inactive_count: 停用模型数量
      - deprecated_count: 已弃用模型数量
      - total_usage: 总使用次数
      - framework_stats: 按框架分类统计
    """
    result = await ModelConfigService.statistics_service(auth=auth)
    log.info("获取模型配置统计信息成功")
    return SuccessResponse(data=result, msg="获取统计信息成功")


@ModelTrainRouter.get(
    "/model/popular",
    summary="热门模型",
    description="获取热门模型列表（按使用次数排序）",
    dependencies=[Depends(RateLimiter(times=30, seconds=10))]
)
async def get_popular_models_controller(
    top_k: int = Query(10, ge=1, le=50, description="返回数量"),
    auth: AuthSchema = Depends(AuthPermission(["module_train:model:query"]))
) -> JSONResponse:
    """
    获取热门模型

    参数:
    - top_k (int): 返回数量（默认10，最多50）
    - auth (AuthSchema): 认证信息

    返回:
    - JSONResponse: 热门模型列表
    """
    result = await ModelConfigService.get_popular_models_service(auth=auth, top_k=top_k)
    log.info(f"获取热门模型成功: top_k={top_k}")
    return SuccessResponse(data=result, msg="获取热门模型成功")


@ModelTrainRouter.post(
    "/model/increment-usage/{id}",
    summary="增加模型使用次数",
    description="增加模型使用次数统计（训练任务创建时调用）",
    dependencies=[Depends(RateLimiter(times=100, seconds=60))]
)
async def increment_model_usage_controller(
    id: int = Path(..., description="模型配置ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_train:model:use"]))
) -> JSONResponse:
    """
    增加模型使用次数

    当用户选择某个模型创建训练任务时，调用此接口增加使用次数统计

    参数:
    - id (int): 模型配置ID
    - auth (AuthSchema): 认证信息

    返回:
    - JSONResponse: 操作结果
    """
    await ModelConfigService.increment_usage_service(auth=auth, model_id=id)
    log.info(f"模型使用次数+1: id={id}")
    return SuccessResponse(msg="使用次数已更新")


# ==================== 模型状态管理 API ====================

@ModelTrainRouter.put(
    "/model/status/{id}",
    summary="更新模型状态",
    description="更新模型状态（active/inactive/deprecated）",
    dependencies=[Depends(RateLimiter(times=20, seconds=60))]
)
async def update_model_status_controller(
    id: int = Path(..., description="模型配置ID"),
    status: str = Body(..., description="模型状态（active/inactive/deprecated）"),
    auth: AuthSchema = Depends(AuthPermission(["module_train:model:update"]))
) -> JSONResponse:
    """
    更新模型状态

    参数:
    - id (int): 模型配置ID
    - status (str): 模型状态
      - active: 激活可用
      - inactive: 停用
      - deprecated: 已弃用
    - auth (AuthSchema): 认证信息

    返回:
    - JSONResponse: 操作结果
    """
    from .crud import ModelConfigCRUD

    result = await ModelConfigCRUD(auth).update_model_status(model_id=id, status=status)
    log.info(f"更新模型状态成功: id={id}, status={status}")
    return SuccessResponse(data={"id": result.id, "status": result.status}, msg="更新状态成功")


@ModelTrainRouter.put(
    "/model/batch-status",
    summary="批量更新模型状态",
    description="批量更新模型状态（需管理员权限）",
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
)
async def batch_update_model_status_controller(
    ids: list[int] = Body(..., description="模型配置ID列表"),
    status: str = Body(..., description="模型状态"),
    auth: AuthSchema = Depends(AuthPermission(["module_train:model:update"]))
) -> JSONResponse:
    """
    批量更新模型状态

    参数:
    - ids (list[int]): 模型配置ID列表
    - status (str): 模型状态（active/inactive/deprecated）
    - auth (AuthSchema): 认证信息

    返回:
    - JSONResponse: 操作结果
    """
    from .crud import ModelConfigCRUD

    crud = ModelConfigCRUD(auth)
    for model_id in ids:
        await crud.update_model_status(model_id=model_id, status=status)

    await auth.db.commit()

    log.info(f"批量更新模型状态成功: ids={ids}, status={status}")
    return SuccessResponse(msg=f"成功更新 {len(ids)} 个模型状态")


# ==================== 模型查询辅助 API ====================

@ModelTrainRouter.get(
    "/model/by-modality",
    summary="按模态查询模型",
    description="根据数据模态类型查询支持的模型列表",
    dependencies=[Depends(RateLimiter(times=30, seconds=10))]
)
async def get_models_by_modality_controller(
    modality: str = Query(..., description="数据模态类型（image/audio/video/text/sensor/multimodal）"),
    only_active: bool = Query(True, description="是否仅返回激活状态的模型"),
    auth: AuthSchema = Depends(AuthPermission(["module_train:model:query"]))
) -> JSONResponse:
    """
    按模态查询模型

    参数:
    - modality (str): 数据模态类型
    - only_active (bool): 是否仅返回激活状态的模型
    - auth (AuthSchema): 认证信息

    返回:
    - JSONResponse: 模型列表
    """
    from .crud import ModelConfigCRUD
    from .schema import ModelCardSchema

    models = await ModelConfigCRUD(auth).get_models_by_modality(
        modality=modality,
        only_active=only_active
    )

    result = [ModelCardSchema.model_validate(model).model_dump() for model in models]

    log.info(f"按模态查询模型成功: modality={modality}, count={len(result)}")
    return SuccessResponse(data=result, msg=f"找到 {len(result)} 个模型")


@ModelTrainRouter.get(
    "/model/by-task",
    summary="按任务类型查询模型",
    description="根据任务类型查询支持的模型列表",
    dependencies=[Depends(RateLimiter(times=30, seconds=10))]
)
async def get_models_by_task_controller(
    task_type: str = Query(..., description="任务类型"),
    only_active: bool = Query(True, description="是否仅返回激活状态的模型"),
    auth: AuthSchema = Depends(AuthPermission(["module_train:model:query"]))
) -> JSONResponse:
    """
    按任务类型查询模型

    参数:
    - task_type (str): 任务类型
    - only_active (bool): 是否仅返回激活状态的模型
    - auth (AuthSchema): 认证信息

    返回:
    - JSONResponse: 模型列表
    """
    from .crud import ModelConfigCRUD
    from .schema import ModelCardSchema

    models = await ModelConfigCRUD(auth).get_models_by_task_type(
        task_type=task_type,
        only_active=only_active
    )

    result = [ModelCardSchema.model_validate(model).model_dump() for model in models]

    log.info(f"按任务类型查询模型成功: task_type={task_type}, count={len(result)}")
    return SuccessResponse(data=result, msg=f"找到 {len(result)} 个模型")


@ModelTrainRouter.get(
    "/model/by-framework",
    summary="按框架查询模型",
    description="根据深度学习框架查询模型列表",
    dependencies=[Depends(RateLimiter(times=30, seconds=10))]
)
async def get_models_by_framework_controller(
    framework: str = Query(..., description="深度学习框架（PyTorch/TensorFlow/PaddlePaddle等）"),
    only_active: bool = Query(True, description="是否仅返回激活状态的模型"),
    auth: AuthSchema = Depends(AuthPermission(["module_train:model:query"]))
) -> JSONResponse:
    """
    按框架查询模型

    参数:
    - framework (str): 深度学习框架
    - only_active (bool): 是否仅返回激活状态的模型
    - auth (AuthSchema): 认证信息

    返回:
    - JSONResponse: 模型列表
    """
    from .crud import ModelConfigCRUD
    from .schema import ModelCardSchema

    models = await ModelConfigCRUD(auth).get_models_by_framework(
        framework=framework,
        only_active=only_active
    )

    result = [ModelCardSchema.model_validate(model).model_dump() for model in models]

    log.info(f"按框架查询模型成功: framework={framework}, count={len(result)}")
    return SuccessResponse(data=result, msg=f"找到 {len(result)} 个模型")


@ModelTrainRouter.get(
    "/model/search-by-tag",
    summary="按标签搜索模型",
    description="根据标签关键词搜索模型",
    dependencies=[Depends(RateLimiter(times=30, seconds=10))]
)
async def search_models_by_tag_controller(
    tag: str = Query(..., description="标签关键词"),
    only_active: bool = Query(True, description="是否仅返回激活状态的模型"),
    auth: AuthSchema = Depends(AuthPermission(["module_train:model:query"]))
) -> JSONResponse:
    """
    按标签搜索模型

    参数:
    - tag (str): 标签关键词
    - only_active (bool): 是否仅返回激活状态的模型
    - auth (AuthSchema): 认证信息

    返回:
    - JSONResponse: 模型列表
    """
    from .crud import ModelConfigCRUD
    from .schema import ModelCardSchema

    models = await ModelConfigCRUD(auth).search_models_by_tag(
        tag=tag,
        only_active=only_active
    )

    result = [ModelCardSchema.model_validate(model).model_dump() for model in models]

    log.info(f"按标签搜索模型成功: tag={tag}, count={len(result)}")
    return SuccessResponse(data=result, msg=f"找到 {len(result)} 个模型")


# ==================== 训练参数推荐 API ====================

@ModelTrainRouter.post(
    "/config/recommend",
    summary="训练参数推荐",
    description="根据数据集和模型配置智能推荐训练超参数",
    dependencies=[Depends(RateLimiter(times=30, seconds=60))]
)
async def recommend_train_config_controller(
    dataset_id: int = Body(..., description="数据集ID"),
    model_config_id: int = Body(..., description="模型配置ID"),
    auth: AuthSchema = Depends(AuthPermission([" module_train:config:recommend"]))
) -> JSONResponse:
    """
    训练参数推荐

    对应使用手册第52-156行（设置训练参数）

    功能：
    - 根据数据集特征（样本数、类别数、模态）智能推荐训练超参数
    - 推荐学习率、批次大小、训练轮数、优化器等参数
    - 完全对应使用手册的推荐算法逻辑

    参数:
    - dataset_id: 数据集ID
    - model_config_id: 模型配置ID

    返回:
    - 推荐的训练配置（TrainConfigSchema格式）

    示例请求:
    ```json
    {
        "dataset_id": 1,
        "model_config_id": 2
    }
    ```

    示例响应:
    ```json
    {
        "learning_rate": 0.001,
        "batch_size": 64,
        "epochs": 50,
        "optimizer": "adam",
        "data_augmentation": true,
        "validation_split": 0.2
    }
    ```
    """
    result = await TrainTaskService.get_train_config_recommendation_service(
        auth=auth,
        dataset_id=dataset_id,
        model_config_id=model_config_id
    )

    log.info(f"训练参数推荐成功: dataset_id={dataset_id}, model_config_id={model_config_id}")
    return SuccessResponse(
        data=result,
        msg="训练参数推荐成功"
    )


# ==================== 训练任务管理 API ====================

@ModelTrainRouter.post(
    "/tasks",
    summary="创建训练任务",
    description="创建新的训练任务（对应使用手册第164-193行）",
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
)
async def create_train_task_controller(
    data: TrainTaskCreateRequest,
    auth: AuthSchema = Depends(AuthPermission(["module_train:task:create"]))
) -> JSONResponse:
    """
    创建训练任务

    对应使用手册第164-193行（开始训练）

    功能：
    - 生成唯一任务ID（格式：TRAIN_timestamp_userid）
    - 保存数据集和模型配置快照
    - 创建训练任务记录
    - 初始化任务状态为 created

    参数:
    - data: 训练任务创建请求
      - dataset_id: 数据集ID
      - model_config_id: 模型配置ID
      - train_config: 训练配置（可使用推荐接口获取）
      - remarks: 备注（可选）

    返回:
    - 创建的训练任务详情（包含task_id）

    示例请求:
    ```json
    {
        "dataset_id": 1,
        "model_config_id": 2,
        "train_config": {
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 50,
            "optimizer": "adam",
            "data_augmentation": true,
            "validation_split": 0.2
        },
        "remarks": "CIFAR-10训练任务"
    }
    ```
    """
    result = await TrainTaskService.create_task_service(auth=auth, request=data)

    log.info(f"创建训练任务成功: task_id={result['task_id']}")
    return SuccessResponse(
        data=result,
        msg=f"训练任务创建成功，任务ID: {result['task_id']}"
    )


@ModelTrainRouter.get(
    "/tasks/{task_id}",
    summary="获取训练任务详情",
    description="根据任务ID获取训练任务详细信息",
    dependencies=[Depends(RateLimiter(times=30, seconds=10))]
)
async def get_train_task_detail_controller(
    task_id: str = Path(..., description="训练任务ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_train:task:query"]))
) -> JSONResponse:
    """
    获取训练任务详情

    参数:
    - task_id: 训练任务ID（例如：TRAIN_1710835200_1001）

    返回:
    - 训练任务详细信息
      - task_id: 任务ID
      - status: 任务状态
      - dataset_info: 数据集信息快照
      - model_config: 模型配置快照
      - train_config: 训练配置
      - current_epoch: 当前轮次
      - total_epochs: 总轮次
      - progress_percentage: 进度百分比
      - timestamps: 时间戳信息
    """
    result = await TrainTaskService.get_task_detail_service(auth=auth, task_id=task_id)

    log.info(f"获取训练任务详情成功: task_id={task_id}")
    return SuccessResponse(data=result, msg="获取训练任务详情成功")


@ModelTrainRouter.get(
    "/tasks",
    summary="查询训练任务列表",
    description="分页查询训练任务列表，支持多种筛选条件",
    dependencies=[Depends(RateLimiter(times=30, seconds=10))]
)
async def get_train_task_list_controller(
    page: PaginationQueryParam = Depends(),
    status: str | None = Query(None, description="任务状态过滤"),
    dataset_id: int | None = Query(None, description="数据集ID过滤"),
    model_config_id: int | None = Query(None, description="模型配置ID过滤"),
    auth: AuthSchema = Depends(AuthPermission(["module_train:task:query"]))
) -> JSONResponse:
    """
    查询训练任务列表（分页）

    参数:
    - page_no: 页码（默认1）
    - page_size: 每页数量（默认10）
    - status: 任务状态过滤（可选）
      - created: 已创建
      - pending: 等待中
      - running: 运行中
      - paused: 已暂停
      - completed: 已完成
      - failed: 失败
      - cancelled: 已取消
    - dataset_id: 数据集ID过滤（可选）
    - model_config_id: 模型配置ID过滤（可选）

    返回:
    - 分页数据
      - total: 总数
      - page: 当前页码
      - page_size: 每页数量
      - items: 任务列表
    """
    result = await TrainTaskService.get_task_list_service(
        auth=auth,
        status=status,
        dataset_id=dataset_id,
        model_config_id=model_config_id,
        page=page.page_no,
        page_size=page.page_size
    )

    log.info(f"查询训练任务列表成功: total={result['total']}")
    return SuccessResponse(data=result, msg="查询训练任务列表成功")


@ModelTrainRouter.put(
    "/tasks/{task_id}/status",
    summary="更新训练任务状态",
    description="更新训练任务状态（对应使用手册第200-201行）",
    dependencies=[Depends(RateLimiter(times=30, seconds=60))]
)
async def update_train_task_status_controller(
    task_id: str = Path(..., description="训练任务ID"),
    status: str = Body(..., description="新状态"),
    error_message: str | None = Body(None, description="错误信息（状态为failed时使用）")
) -> JSONResponse:
    """
    更新训练任务状态（内部接口，训练引擎调用）

    对应使用手册第200-201行（训练执行引擎状态变更）

    功能：
    - 更新任务状态
    - 自动设置时间戳
      - running → 设置 actual_start_time
      - completed → 设置 actual_completion_time 和 progress=100%
      - failed → 设置 actual_completion_time 和 error_message

    参数:
    - task_id: 训练任务ID
    - status: 新状态（created/pending/running/paused/completed/failed/cancelled）
    - error_message: 错误信息（可选，状态为failed时使用）

    示例请求:
    ```json
    {
        "status": "running"
    }
    ```

    或者（训练失败时）:
    ```json
    {
        "status": "failed",
        "error_message": "CUDA out of memory"
    }
    ```
    """
    result = await TrainTaskService.update_task_status_service(
        auth=None,
        task_id=task_id,
        status=status,
        error_message=error_message
    )

    log.info(f"更新训练任务状态成功: task_id={task_id}, status={status}")
    return SuccessResponse(
        data=result,
        msg=f"任务状态已更新为: {status}"
    )


@ModelTrainRouter.delete(
    "/tasks/{task_id}",
    summary="删除训练任务",
    description="删除训练任务（不能删除正在运行的任务）",
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
)
async def delete_train_task_controller(
    task_id: str = Path(..., description="训练任务ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_train:task:delete"]))
) -> JSONResponse:
    """
    删除训练任务

    注意：不能删除正在运行（status=running）的任务

    参数:
    - task_id: 训练任务ID

    返回:
    - 删除结果
    """
    await TrainTaskService.delete_task_service(auth=auth, task_id=task_id)

    log.info(f"删除训练任务成功: task_id={task_id}")
    return SuccessResponse(msg="训练任务已删除")


# ==================== 训练进度查询 API ====================

@ModelTrainRouter.get(
    "/tasks/{task_id}/progress",
    summary="获取训练任务的最新进度",
    description="获取训练任务的最新进度信息（对应使用手册第206-229行）",
    dependencies=[Depends(RateLimiter(times=60, seconds=10))]
)
async def get_train_progress_controller(
    task_id: str = Path(..., description="训练任务ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_train:task:query"]))
) -> JSONResponse:
    """
    获取训练任务的最新进度

    对应使用手册第206-229行（WebSocket实时数据）

    返回:
    - 最新进度信息
      - epoch: 当前轮次
      - batch: 当前批次
      - total_batches: 总批次数
      - train_loss: 训练损失
      - train_accuracy: 训练准确率
      - val_loss: 验证损失
      - val_accuracy: 验证准确率
      - learning_rate: 当前学习率
      - epoch_progress: 当前轮次进度
      - overall_progress: 总体进度
    """
    result = await TrainTaskService.get_latest_progress_service(auth=auth, task_id=task_id)

    if result is None:
        return SuccessResponse(data=None, msg="暂无进度数据")

    log.info(f"获取训练进度成功: task_id={task_id}, epoch={result.get('epoch')}")
    return SuccessResponse(data=result, msg="获取训练进度成功")


@ModelTrainRouter.get(
    "/tasks/{task_id}/progress/curve",
    summary="获取训练曲线数据",
    description="获取训练曲线数据（每个epoch的最终指标）",
    dependencies=[Depends(RateLimiter(times=30, seconds=10))]
)
async def get_train_curve_controller(
    task_id: str = Path(..., description="训练任务ID"),
    metrics: str | None = Query(None, description="指标列表（逗号分隔，如：train_loss,train_accuracy）"),
    auth: AuthSchema = Depends(AuthPermission(["module_train:task:query"]))
) -> JSONResponse:
    """
    获取训练曲线数据

    用于前端绘制训练曲线图

    参数:
    - task_id: 训练任务ID
    - metrics: 需要的指标列表（可选）
      - 可选值：train_loss, train_accuracy, val_loss, val_accuracy, learning_rate
      - 多个指标用逗号分隔，例如：train_loss,val_loss

    返回:
    - 训练曲线数据
      - task_id: 任务ID
      - total_epochs: 总轮次
      - current_epoch: 当前轮次
      - data_points: 数据点列表（每个epoch的最终指标）

    示例响应:
    ```json
    {
        "task_id": "TRAIN_1710835200_1001",
        "total_epochs": 50,
        "current_epoch": 12,
        "data_points": [
            {
                "epoch": 1,
                "train_loss": 0.8,
                "train_accuracy": 0.7,
                "val_loss": 0.85,
                "val_accuracy": 0.68
            },
            ...
        ]
    }
    ```
    """
    metrics_list = metrics.split(',') if metrics else None

    result = await TrainTaskService.get_progress_curve_service(
        auth=auth,
        task_id=task_id,
        metrics=metrics_list
    )

    log.info(f"获取训练曲线成功: task_id={task_id}, epochs={len(result.get('data_points', []))}")
    return SuccessResponse(data=result, msg="获取训练曲线成功")


# ==================== 训练结果管理 API ====================

@ModelTrainRouter.post(
    "/tasks/{task_id}/result",
    summary="更新训练任务结果",
    description="更新训练任务的最终结果（对应使用手册第252-255行）",
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
)
async def update_train_result_controller(
    task_id: str = Path(..., description="训练任务ID"),
    final_metrics: dict = Body(..., description="最终评估指标"),
    model_save_path: str | None = Body(None, description="模型保存路径"),
    result_file_path: str | None = Body(None, description="结果文件路径")
) -> JSONResponse:
    """
    更新训练任务结果（内部接口，训练引擎调用）

    对应使用手册第252-255行（训练完成后保存结果）

    功能：
    - 保存最终评估指标（test_loss, test_accuracy, f1_score等）
    - 保存模型文件路径
    - 保存结果报告路径

    参数:
    - task_id: 训练任务ID
    - final_metrics: 最终评估指标（dict）
    - model_save_path: 模型保存路径（可选）
    - result_file_path: 结果文件路径（可选）

    示例请求:
    ```json
    {
        "final_metrics": {
            "test_loss": 0.3245,
            "test_accuracy": 0.9156,
            "f1_score": 0.9012,
            "precision": 0.9234,
            "recall": 0.8956
        },
        "model_save_path": "/data/models/TRAIN_1710835200_1001/best_model.pth",
        "result_file_path": "/data/results/TRAIN_1710835200_1001/report.json"
    }
    ```
    """
    result = await TrainTaskService.update_task_result_service(
        auth=None,
        task_id=task_id,
        final_metrics=final_metrics,
        model_save_path=model_save_path,
        result_file_path=result_file_path
    )

    log.info(f"更新训练结果成功: task_id={task_id}")
    return SuccessResponse(
        data=result,
        msg="训练结果已保存"
    )


# ==================== 训练进度上报 API ====================

@ModelTrainRouter.post(
    "/tasks/{task_id}/progress/report",
    summary="训练进度上报",
    description="训练引擎上报进度信息（内部接口）",
    dependencies=[Depends(RateLimiter(times=100, seconds=10))]
)
async def report_train_progress_controller(
    task_id: str = Path(..., description="训练任务ID"),
    data: dict = Body(..., description="进度数据")
) -> JSONResponse:
    """
    训练进度上报

    由训练引擎调用，用于上报训练进度信息

    参数:
    - task_id: 训练任务ID
    - data: 进度数据
      - current_epoch: 当前轮次
      - total_epochs: 总轮次
      - current_step: 当前步数
      - total_steps: 总步数
      - train_loss: 训练损失
      - train_accuracy: 训练准确率
      - val_loss: 验证损失
      - val_accuracy: 验证准确率
      - learning_rate: 学习率
      - epoch_time: 轮次耗时

    返回:
    - JSONResponse: 操作结果
    """
    result = await TrainTaskService.report_progress_service(auth=None, task_id=task_id, progress_data=data)

    log.info(f"训练进度上报成功: task_id={task_id}, epoch={data.get('current_epoch')}")
    return SuccessResponse(data=result, msg="进度上报成功")


# ==================== 任务结果查询 API ====================

@ModelTrainRouter.get(
    "/tasks/{task_id}/result",
    summary="获取训练任务结果",
    description="读取训练任务的result.json文件",
    dependencies=[Depends(RateLimiter(times=30, seconds=10))]
)
async def get_train_task_result_controller(
    task_id: str = Path(..., description="训练任务ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_train:task:query"]))
) -> JSONResponse:
    """
    获取训练任务结果

    读取任务目录下的result.json文件

    参数:
    - task_id: 训练任务ID

    返回:
    - JSONResponse: 训练结果数据
    """
    result = await TrainTaskService.get_task_result_service(auth=auth, task_id=task_id)

    log.info(f"获取训练结果成功: task_id={task_id}")
    return SuccessResponse(data=result, msg="获取训练结果成功")


# ==================== 任务产物下载 API ====================

@ModelTrainRouter.get(
    "/tasks/{task_id}/artifact",
    summary="下载训练任务产物",
    description="下载训练任务的产物文件（如模型权重、报告等）",
    dependencies=[Depends(RateLimiter(times=20, seconds=60))]
)
async def download_train_artifact_controller(
    task_id: str = Path(..., description="训练任务ID"),
    path: str = Query(..., description="相对路径（如model.pth, report.pdf）"),
    auth: AuthSchema = Depends(AuthPermission(["module_train:task:query"]))
):
    """
    下载训练任务产物

    参数:
    - task_id: 训练任务ID
    - path: 相对路径

    返回:
    - FileResponse: 文件下载
    """
    from fastapi.responses import FileResponse
    import os

    file_path = await TrainTaskService.get_artifact_path_service(auth=auth, task_id=task_id, relative_path=path)

    if not os.path.exists(file_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="文件不存在")

    log.info(f"下载任务产物: task_id={task_id}, path={path}")
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type='application/octet-stream'
    )


# ==================== 任务报告查询 API ====================

@ModelTrainRouter.get(
    "/tasks/{task_id}/report",
    summary="获取训练任务报告",
    description="获取训练任务的报告数据（用于网页展示）",
    dependencies=[Depends(RateLimiter(times=30, seconds=10))]
)
async def get_train_task_report_controller(
    task_id: str = Path(..., description="训练任务ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_train:task:query"]))
) -> JSONResponse:
    """
    获取训练任务报告

    读取任务目录下的reports/*.json文件，用于前端报告页面展示

    参数:
    - task_id: 训练任务ID

    返回:
    - JSONResponse: 报告数据
    """
    result = await TrainTaskService.get_task_report_service(auth=auth, task_id=task_id)

    log.info(f"获取训练报告成功: task_id={task_id}")
    return SuccessResponse(data=result, msg="获取训练报告成功")


@ModelTrainRouter.get(
    "/tasks/{task_id}/logs",
    summary="获取训练日志",
    description="获取训练任务的实时日志内容",
    dependencies=[Depends(RateLimiter(times=60, seconds=10))]
)
async def get_train_task_logs_controller(
    task_id: str = Path(..., description="训练任务ID"),
    lines: int = Query(100, ge=1, le=1000, description="返回最后N行日志"),
    auth: AuthSchema = Depends(AuthPermission(["module_train:task:query"]))
) -> JSONResponse:
    """
    获取训练任务日志

    读取任务目录下的engine.log文件内容

    参数:
    - task_id: 训练任务ID
    - lines: 返回最后N行日志（默认100行，最多1000行）

    返回:
    - JSONResponse: 日志内容
    """
    result = await TrainTaskService.get_task_logs_service(auth=auth, task_id=task_id, lines=lines)

    log.info(f"获取训练日志成功: task_id={task_id}, lines={lines}")
    return SuccessResponse(data=result, msg="获取训练日志成功")

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
    ModelRecommendationService
)
from .schema import (
    ModelConfigCreateSchema,
    ModelConfigUpdateSchema,
    ModelConfigQueryParam,
    ModelRecommendationRequest,
    ModelRecommendationResponse
)


# ==================== 路由定义 ====================

# 注意：不要设置 prefix，因为动态路由发现会自动添加 /train 前缀（基于 module_train 目录名）
ModelTrainRouter = APIRouter(route_class=OperationLogRoute, tags=["模型训练管理"])


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

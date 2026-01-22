# -*- coding: utf-8 -*-

from fastapi import APIRouter, Body, Depends, Path
from fastapi.responses import JSONResponse, StreamingResponse

from app.common.response import SuccessResponse, StreamResponse
from app.common.request import PaginationService
from app.core.router_class import OperationLogRoute
from app.utils.common_util import bytes2file_response
from app.core.base_params import PaginationQueryParam
from app.core.dependencies import AuthPermission
from app.core.logger import log

OptimizerRouter = APIRouter(route_class=OperationLogRoute, prefix="/optimizer", tags=["优化器"])

from app.api.v1.module_system.auth.schema import AuthSchema
from .service import OptimizerTaskService, OptimizerResultService, OptimizerExecutionLogService
from .schema import (
    OptimizerTaskCreateSchema,
    OptimizerTaskUpdateSchema,
    OptimizerTaskQueryParam,
    OptimizerResultCreateSchema,
    OptimizerResultUpdateSchema,
    OptimizerResultQueryParam,
    OptimizerExecutionLogQueryParam,
    OptimizerTaskRunSchema,
    OptimizerResultApplySchema
)


# ==================== 优化器任务管理接口 ====================

@OptimizerRouter.get("/task/detail/{id}", summary="获取优化器任务详情", description="获取优化器任务详情")
async def get_task_detail_controller(
    id: int = Path(..., description="优化器任务ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_application:optimizer:detail"]))
) -> JSONResponse:
    """
    获取优化器任务详情

    参数:
    - id (int): 优化器任务ID
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含优化器任务详情的JSON响应
    """
    result_dict = await OptimizerTaskService.get_task_detail_service(id=id, auth=auth)
    log.info(f"获取优化器任务详情成功 {id}")
    return SuccessResponse(data=result_dict, msg="获取优化器任务详情成功")


@OptimizerRouter.get("/task/list", summary="查询优化器任务", description="查询优化器任务")
async def get_task_list_controller(
    page: PaginationQueryParam = Depends(),
    search: OptimizerTaskQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(["module_application:optimizer:query"]))
) -> JSONResponse:
    """
    查询优化器任务

    参数:
    - page (PaginationQueryParam): 分页查询参数模型
    - search (OptimizerTaskQueryParam): 查询参数模型
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含分页后的优化器任务列表的JSON响应
    """
    result_dict_list = await OptimizerTaskService.get_task_list_service(auth=auth, search=search, order_by=page.order_by)
    result_dict = await PaginationService.paginate(data_list=result_dict_list, page_no=page.page_no, page_size=page.page_size)
    log.info("查询优化器任务列表成功")
    return SuccessResponse(data=result_dict, msg="查询优化器任务列表成功")


@OptimizerRouter.post("/task/create", summary="创建优化器任务", description="创建优化器任务")
async def create_task_controller(
    data: OptimizerTaskCreateSchema,
    auth: AuthSchema = Depends(AuthPermission(["module_application:optimizer:create"]))
) -> JSONResponse:
    """
    创建优化器任务

    参数:
    - data (OptimizerTaskCreateSchema): 创建参数模型
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含创建优化器任务结果的JSON响应
    """
    result_dict = await OptimizerTaskService.create_task_service(auth=auth, data=data)
    log.info(f"创建优化器任务成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="创建优化器任务成功")


@OptimizerRouter.put("/task/update/{id}", summary="修改优化器任务", description="修改优化器任务")
async def update_task_controller(
    data: OptimizerTaskUpdateSchema,
    id: int = Path(..., description="优化器任务ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_application:optimizer:update"]))
) -> JSONResponse:
    """
    修改优化器任务

    参数:
    - data (OptimizerTaskUpdateSchema): 更新参数模型
    - id (int): 优化器任务ID
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含修改优化器任务结果的JSON响应
    """
    result_dict = await OptimizerTaskService.update_task_service(auth=auth, id=id, data=data)
    log.info(f"修改优化器任务成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="修改优化器任务成功")


@OptimizerRouter.delete("/task/delete", summary="删除优化器任务", description="删除优化器任务")
async def delete_task_controller(
    ids: list[int] = Body(..., description="ID列表"),
    auth: AuthSchema = Depends(AuthPermission(["module_application:optimizer:delete"]))
) -> JSONResponse:
    """
    删除优化器任务

    参数:
    - ids (list[int]): ID列表
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含删除优化器任务结果的JSON响应
    """
    await OptimizerTaskService.delete_task_service(auth=auth, ids=ids)
    log.info(f"删除优化器任务成功: {ids}")
    return SuccessResponse(msg="删除优化器任务成功")


@OptimizerRouter.post("/task/export", summary="导出优化器任务", description="导出优化器任务")
async def export_task_list_controller(
    search: OptimizerTaskQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(["module_application:optimizer:export"]))
) -> StreamingResponse:
    """
    导出优化器任务

    参数:
    - search (OptimizerTaskQueryParam): 查询参数模型
    - auth (AuthSchema): 认证信息模型

    返回:
    - StreamingResponse: 包含导出优化器任务结果的流式响应
    """
    result_dict_list = await OptimizerTaskService.get_task_list_service(search=search, auth=auth)
    export_result = await OptimizerTaskService.export_task_service(data_list=result_dict_list)
    log.info("导出优化器任务成功")

    return StreamResponse(
        data=bytes2file_response(export_result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={
            'Content-Disposition': 'attachment; filename=optimizer_task.xlsx'
        }
    )


@OptimizerRouter.delete("/task/clear", summary="清空优化器任务", description="清空优化器任务")
async def clear_task_controller(
    auth: AuthSchema = Depends(AuthPermission(["module_application:optimizer:delete"]))
) -> JSONResponse:
    """
    清空优化器任务

    参数:
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含清空优化器任务结果的JSON响应
    """
    await OptimizerTaskService.clear_task_service(auth=auth)
    log.info("清空优化器任务成功")
    return SuccessResponse(msg="清空优化器任务成功")


@OptimizerRouter.post("/task/run/{id}", summary="执行优化器任务", description="执行优化器任务")
async def run_task_controller(
    id: int = Path(..., description="优化器任务ID"),
    data: OptimizerTaskRunSchema = Body(default=OptimizerTaskRunSchema()),
    auth: AuthSchema = Depends(AuthPermission(["module_application:optimizer:run"]))
) -> JSONResponse:
    """
    执行优化器任务

    参数:
    - id (int): 优化器任务ID
    - data (OptimizerTaskRunSchema): 执行参数模型
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含执行优化器任务结果的JSON响应
    """
    result_dict = await OptimizerTaskService.run_task_service(auth=auth, id=id, override_config=data.override_config)
    log.info(f"执行优化器任务成功: {id}")
    return SuccessResponse(data=result_dict, msg="执行优化器任务成功")


@OptimizerRouter.put("/task/cancel/{id}", summary="取消优化器任务", description="取消优化器任务")
async def cancel_task_controller(
    id: int = Path(..., description="优化器任务ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_application:optimizer:update"]))
) -> JSONResponse:
    """
    取消优化器任务

    参数:
    - id (int): 优化器任务ID
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含取消优化器任务结果的JSON响应
    """
    await OptimizerTaskService.cancel_task_service(auth=auth, id=id)
    log.info(f"取消优化器任务成功: {id}")
    return SuccessResponse(msg="取消优化器任务成功")


# ==================== 优化器结果管理接口 ====================

@OptimizerRouter.get("/result/detail/{id}", summary="获取优化器结果详情", description="获取优化器结果详情")
async def get_result_detail_controller(
    id: int = Path(..., description="优化器结果ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_application:optimizer:detail"]))
) -> JSONResponse:
    """
    获取优化器结果详情

    参数:
    - id (int): 优化器结果ID
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含优化器结果详情的JSON响应
    """
    result_dict = await OptimizerResultService.get_result_detail_service(id=id, auth=auth)
    log.info(f"获取优化器结果详情成功 {id}")
    return SuccessResponse(data=result_dict, msg="获取优化器结果详情成功")


@OptimizerRouter.get("/result/list", summary="查询优化器结果", description="查询优化器结果")
async def get_result_list_controller(
    page: PaginationQueryParam = Depends(),
    search: OptimizerResultQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(["module_application:optimizer:query"]))
) -> JSONResponse:
    """
    查询优化器结果

    参数:
    - page (PaginationQueryParam): 分页查询参数模型
    - search (OptimizerResultQueryParam): 查询参数模型
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含分页后的优化器结果列表的JSON响应
    """
    result_dict_list = await OptimizerResultService.get_result_list_service(auth=auth, search=search, order_by=page.order_by)
    result_dict = await PaginationService.paginate(data_list=result_dict_list, page_no=page.page_no, page_size=page.page_size)
    log.info("查询优化器结果列表成功")
    return SuccessResponse(data=result_dict, msg="查询优化器结果列表成功")


@OptimizerRouter.post("/result/create", summary="创建优化器结果", description="创建优化器结果")
async def create_result_controller(
    data: OptimizerResultCreateSchema,
    auth: AuthSchema = Depends(AuthPermission(["module_application:optimizer:create"]))
) -> JSONResponse:
    """
    创建优化器结果

    参数:
    - data (OptimizerResultCreateSchema): 创建参数模型
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含创建优化器结果结果的JSON响应
    """
    result_dict = await OptimizerResultService.create_result_service(auth=auth, data=data)
    log.info(f"创建优化器结果成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="创建优化器结果成功")


@OptimizerRouter.put("/result/update/{id}", summary="修改优化器结果", description="修改优化器结果")
async def update_result_controller(
    data: OptimizerResultUpdateSchema,
    id: int = Path(..., description="优化器结果ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_application:optimizer:update"]))
) -> JSONResponse:
    """
    修改优化器结果

    参数:
    - data (OptimizerResultUpdateSchema): 更新参数模型
    - id (int): 优化器结果ID
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含修改优化器结果结果的JSON响应
    """
    result_dict = await OptimizerResultService.update_result_service(auth=auth, id=id, data=data)
    log.info(f"修改优化器结果成功: {result_dict}")
    return SuccessResponse(data=result_dict, msg="修改优化器结果成功")


@OptimizerRouter.delete("/result/delete", summary="删除优化器结果", description="删除优化器结果")
async def delete_result_controller(
    ids: list[int] = Body(..., description="ID列表"),
    auth: AuthSchema = Depends(AuthPermission(["module_application:optimizer:delete"]))
) -> JSONResponse:
    """
    删除优化器结果

    参数:
    - ids (list[int]): ID列表
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含删除优化器结果结果的JSON响应
    """
    await OptimizerResultService.delete_result_service(auth=auth, ids=ids)
    log.info(f"删除优化器结果成功: {ids}")
    return SuccessResponse(msg="删除优化器结果成功")


@OptimizerRouter.post("/result/export", summary="导出优化器结果", description="导出优化器结果")
async def export_result_list_controller(
    search: OptimizerResultQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(["module_application:optimizer:export"]))
) -> StreamingResponse:
    """
    导出优化器结果

    参数:
    - search (OptimizerResultQueryParam): 查询参数模型
    - auth (AuthSchema): 认证信息模型

    返回:
    - StreamingResponse: 包含导出优化器结果结果的流式响应
    """
    result_dict_list = await OptimizerResultService.get_result_list_service(search=search, auth=auth)
    export_result = await OptimizerResultService.export_result_service(data_list=result_dict_list)
    log.info("导出优化器结果成功")

    return StreamResponse(
        data=bytes2file_response(export_result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={
            'Content-Disposition': 'attachment; filename=optimizer_result.xlsx'
        }
    )


@OptimizerRouter.delete("/result/clear", summary="清空优化器结果", description="清空优化器结果")
async def clear_result_controller(
    auth: AuthSchema = Depends(AuthPermission(["module_application:optimizer:delete"]))
) -> JSONResponse:
    """
    清空优化器结果

    参数:
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含清空优化器结果结果的JSON响应
    """
    await OptimizerResultService.clear_result_service(auth=auth)
    log.info("清空优化器结果成功")
    return SuccessResponse(msg="清空优化器结果成功")


@OptimizerRouter.post("/result/apply/{id}", summary="应用优化器结果", description="应用优化器结果")
async def apply_result_controller(
    id: int = Path(..., description="优化器结果ID"),
    data: OptimizerResultApplySchema = Body(default=OptimizerResultApplySchema()),
    auth: AuthSchema = Depends(AuthPermission(["module_application:optimizer:update"]))
) -> JSONResponse:
    """
    应用优化器结果

    参数:
    - id (int): 优化器结果ID
    - data (OptimizerResultApplySchema): 应用参数模型
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含应用优化器结果结果的JSON响应
    """
    result_dict = await OptimizerResultService.apply_result_service(
        auth=auth,
        id=id,
        apply_mode=data.apply_mode,
        confirm=data.confirm
    )
    log.info(f"应用优化器结果成功: {id}")
    return SuccessResponse(data=result_dict, msg="应用优化器结果成功")


# ==================== 优化器执行日志管理接口 ====================

@OptimizerRouter.get("/log/detail/{id}", summary="获取优化器执行日志详情", description="获取优化器执行日志详情")
async def get_log_detail_controller(
    id: int = Path(..., description="优化器执行日志ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_application:optimizer:query"]))
) -> JSONResponse:
    """
    获取优化器执行日志详情

    参数:
    - id (int): 优化器执行日志ID
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含优化器执行日志详情的JSON响应
    """
    result_dict = await OptimizerExecutionLogService.get_log_detail_service(id=id, auth=auth)
    log.info(f"获取优化器执行日志详情成功 {id}")
    return SuccessResponse(data=result_dict, msg="获取优化器执行日志详情成功")


@OptimizerRouter.get("/log/list", summary="查询优化器执行日志", description="查询优化器执行日志")
async def get_log_list_controller(
    page: PaginationQueryParam = Depends(),
    search: OptimizerExecutionLogQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(["module_application:optimizer:query"]))
) -> JSONResponse:
    """
    查询优化器执行日志

    参数:
    - page (PaginationQueryParam): 分页查询参数模型
    - search (OptimizerExecutionLogQueryParam): 查询参数模型
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含分页后的优化器执行日志列表的JSON响应
    """
    result_dict_list = await OptimizerExecutionLogService.get_log_list_service(auth=auth, search=search, order_by=page.order_by)
    result_dict = await PaginationService.paginate(data_list=result_dict_list, page_no=page.page_no, page_size=page.page_size)
    log.info("查询优化器执行日志列表成功")
    return SuccessResponse(data=result_dict, msg="查询优化器执行日志列表成功")


@OptimizerRouter.delete("/log/delete", summary="删除优化器执行日志", description="删除优化器执行日志")
async def delete_log_controller(
    ids: list[int] = Body(..., description="ID列表"),
    auth: AuthSchema = Depends(AuthPermission(["module_application:optimizer:delete"]))
) -> JSONResponse:
    """
    删除优化器执行日志

    参数:
    - ids (list[int]): ID列表
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含删除优化器执行日志结果的JSON响应
    """
    await OptimizerExecutionLogService.delete_log_service(auth=auth, ids=ids)
    log.info(f"删除优化器执行日志成功: {ids}")
    return SuccessResponse(msg="删除优化器执行日志成功")


@OptimizerRouter.post("/log/export", summary="导出优化器执行日志", description="导出优化器执行日志")
async def export_log_list_controller(
    search: OptimizerExecutionLogQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(["module_application:optimizer:export"]))
) -> StreamingResponse:
    """
    导出优化器执行日志

    参数:
    - search (OptimizerExecutionLogQueryParam): 查询参数模型
    - auth (AuthSchema): 认证信息模型

    返回:
    - StreamingResponse: 包含导出优化器执行日志结果的流式响应
    """
    result_dict_list = await OptimizerExecutionLogService.get_log_list_service(search=search, auth=auth)
    export_result = await OptimizerExecutionLogService.export_log_service(data_list=result_dict_list)
    log.info("导出优化器执行日志成功")

    return StreamResponse(
        data=bytes2file_response(export_result),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={
            'Content-Disposition': 'attachment; filename=optimizer_log.xlsx'
        }
    )


@OptimizerRouter.delete("/log/clear", summary="清空优化器执行日志", description="清空优化器执行日志")
async def clear_log_controller(
    auth: AuthSchema = Depends(AuthPermission(["module_application:optimizer:delete"]))
) -> JSONResponse:
    """
    清空优化器执行日志

    参数:
    - auth (AuthSchema): 认证信息模型

    返回:
    - JSONResponse: 包含清空优化器执行日志结果的JSON响应
    """
    await OptimizerExecutionLogService.clear_log_service(auth=auth)
    log.info("清空优化器执行日志成功")
    return SuccessResponse(msg="清空优化器执行日志成功")

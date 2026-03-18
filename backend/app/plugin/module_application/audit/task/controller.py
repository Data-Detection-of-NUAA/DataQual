"""
审计任务Controller
"""
from fastapi import APIRouter, Depends, Path, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.common.response import SuccessResponse
from app.common.request import PaginationService
from app.core.router_class import OperationLogRoute
from app.core.dependencies import AuthPermission
from app.core.database import async_db_session
from app.core.base_params import PaginationQueryParam
from app.api.v1.module_system.auth.schema import AuthSchema
from .service import AuditTaskService
from .schema import (
    AuditTaskCreate, AuditTaskUpdate, AuditTaskQueryParam,
    RuleConfirm, AuditErrorQueryParam, AuditTaskBatchDelete
)


TaskRouter = APIRouter(
    route_class=OperationLogRoute,
    prefix="/audit/task",
    tags=["审计任务管理"]
)


@TaskRouter.post("/create", summary="创建审计任务")
async def create_task(
    task_name: str = Form(..., description='任务名称', max_length=200),
    description: Optional[str] = Form(None, description='备注'),
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:task:create"]))
) -> JSONResponse:
    """创建新的审计任务"""
    task_in = AuditTaskCreate(task_name=task_name, description=description)
    task = await AuditTaskService.create_service(obj_in=task_in, auth=auth)
    return SuccessResponse(data=task, msg="任务创建成功")


@TaskRouter.get("/list", summary="获取任务列表")
async def get_task_list(
    page: PaginationQueryParam = Depends(),
    params: AuditTaskQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:task:list"]))
) -> JSONResponse:
    """获取任务列表（分页）"""
    tasks, total = await AuditTaskService.list_service(params=params, auth=auth)
    result = await PaginationService.paginate(data_list=tasks, page_no=page.page_no, page_size=page.page_size)
    return SuccessResponse(data=result)


@TaskRouter.get("/detail/{id}", summary="获取任务详情")
async def get_task_detail(
    id: int = Path(..., description="任务ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:task:detail"]))
) -> JSONResponse:
    """获取任务详情"""
    task = await AuditTaskService.detail_service(id=id, auth=auth)
    return SuccessResponse(data=task)


@TaskRouter.delete("/delete", summary="删除审计任务")
async def delete_task(
    batch_in: AuditTaskBatchDelete,
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:task:delete"]))
) -> JSONResponse:
    """删除审计任务"""
    await AuditTaskService.delete_service(ids=batch_in.ids, auth=auth)
    return SuccessResponse(msg="删除成功")


@TaskRouter.post("/{id}/upload-regulation", summary="上传法规文件")
async def upload_regulation(
    id: int = Path(..., description="任务ID"),
    file_type: str = Form(..., description="文件类型"),
    file: UploadFile = File(...),
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:task:upload"]))
) -> JSONResponse:
    "Step 1: Upload regulation attachments for the task."
    result = await AuditTaskService.upload_regulation_service(
        task_id=id, file_type=file_type, file=file, auth=auth
    )
    return SuccessResponse(data=result, msg="法规上传成功")


@TaskRouter.post("/{id}/use-regulation/{regulation_id}", summary="选择已有法规")
async def use_regulation(
    id: int = Path(..., description="任务ID"),
    regulation_id: int = Path(..., description="法规ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:task:upload"]))
) -> JSONResponse:
    "Step 1: Bind an existing regulation file to the task."
    result = await AuditTaskService.use_existing_regulation_service(
        task_id=id,
        regulation_id=regulation_id,
        auth=auth,
    )
    return SuccessResponse(data=result, msg="已选择法规")


@TaskRouter.post("/{id}/match-rules", summary="AI匹配规则")
async def match_rules(
    id: int = Path(..., description="任务ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:task:match"]))
) -> JSONResponse:
    "Step 2: Match rules through the AI matcher."
    result = await AuditTaskService.match_rules_service(task_id=id, auth=auth)
    return SuccessResponse(data=result, msg="规则匹配完成")


@TaskRouter.post("/{id}/confirm-rules", summary="确认所选规则")
async def confirm_rules(
    id: int = Path(..., description="任务ID"),
    rule_confirm: Optional[RuleConfirm] = None,
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:task:confirm"]))
) -> JSONResponse:
    "Step 2: Confirm which rules will be executed for the task."
    selected_rules = rule_confirm.selected_rules if rule_confirm else []
    result = await AuditTaskService.confirm_rules_service(
        task_id=id,
        selected_rules=selected_rules,
        auth=auth,
    )
    return SuccessResponse(data=result, msg="规则确认成功")


@TaskRouter.post("/{id}/upload-dataset", summary="上传审计数据集")
async def upload_dataset(
    id: int = Path(..., description="任务ID"),
    file_type: str = Form(..., description="文件类型"),
    file: UploadFile = File(...),
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:task:upload"]))
) -> JSONResponse:
    "Step 3: Upload task dataset for auditing."
    result = await AuditTaskService.upload_dataset_service(
        task_id=id, file_type=file_type, file=file, auth=auth
    )
    return SuccessResponse(data=result, msg="数据集上传成功")


@TaskRouter.post("/{id}/execute", summary="执行审计")
async def execute_audit(
    id: int = Path(..., description="任务ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:task:execute"]))
) -> JSONResponse:
    """步骤4: 执行审计"""
    result = await AuditTaskService.execute_audit_service(task_id=id, auth=auth)
    return SuccessResponse(data=result, msg="审计执行完成")


@TaskRouter.get("/{id}/result", summary="获取审计结果")
async def get_audit_result(
    id: int = Path(..., description="任务ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:task:result"]))
) -> JSONResponse:
    """获取审计结果"""
    result = await AuditTaskService.get_audit_result_service(task_id=id, auth=auth)
    return SuccessResponse(data=result)


@TaskRouter.get("/{id}/errors", summary="获取错误详情列表")
async def get_errors(
    id: int = Path(..., description="任务ID"),
    page: PaginationQueryParam = Depends(),
    error_type: str = Query(None, description="错误类型：data/label"),
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:task:errors"]))
) -> JSONResponse:
    """获取错误详情列表（分页）"""
    errors = await AuditTaskService.get_errors_service(
        task_id=id,
        error_type=error_type,
        page_no=page.page_no,
        page_size=page.page_size,
        auth=auth
    )
    return SuccessResponse(data=errors)


@TaskRouter.get("/{id}/download-report", summary="下载审计报告")
async def download_report(
    id: int = Path(..., description="任务ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:task:download"]))
):
    """下载审计报告"""
    file_path = await AuditTaskService.download_report_service(task_id=id, auth=auth)
    return FileResponse(
        path=file_path,
        filename=f"audit_report_{id}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

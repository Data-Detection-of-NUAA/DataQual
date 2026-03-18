"""
审计法规管理 Controller
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, Path

from app.common.response import SuccessResponse
from app.core.router_class import OperationLogRoute
from app.core.dependencies import AuthPermission
from app.core.base_params import PaginationQueryParam
from app.api.v1.module_system.auth.schema import AuthSchema

from .schema import (
    AuditRegulationQueryParam,
    AuditRegulationBatchDelete,
)
from .service import AuditRegulationService

RegulationRouter = APIRouter(
    route_class=OperationLogRoute,
    prefix="/audit/regulation",
    tags=["审计法规库管理"],
)


@RegulationRouter.get("/list", summary="获取法规列表")
async def list_regulations(
    page: PaginationQueryParam = Depends(),
    params: AuditRegulationQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:regulation:query"])),
):
    """分页获取法规列表"""
    data = await AuditRegulationService.list_service(
        params=params,
        page_no=page.page_no,
        page_size=page.page_size,
        auth=auth,
    )
    return SuccessResponse(data=data)


@RegulationRouter.get("/detail/{id}", summary="获取法规详情")
async def detail_regulation(
    id: int = Path(..., description="法规ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:regulation:detail"])),
):
    result = await AuditRegulationService.detail_service(id, auth)
    return SuccessResponse(data=result)


@RegulationRouter.post("/upload", summary="上传法规文件")
async def upload_regulation(
    regulation_name: str | None = Form(None, description="法规名称"),
    description: str | None = Form(None, description="法规描述"),
    file_type: str = Form(..., description="文件类型"),
    file: UploadFile = File(...),
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:regulation:upload"])),
):
    result = await AuditRegulationService.upload_service(
        regulation_name=regulation_name,
        description=description,
        file_type=file_type,
        file=file,
        auth=auth,
    )
    return SuccessResponse(data=result, msg="法规上传成功")


@RegulationRouter.delete("/delete", summary="批量删除法规")
async def delete_regulations(
    batch_in: AuditRegulationBatchDelete,
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:regulation:delete"])),
):
    await AuditRegulationService.delete_service(batch_in.ids, auth)
    return SuccessResponse(msg="删除成功")


@RegulationRouter.get("/options", summary="获取法规选项")
async def regulation_options(
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:regulation:query"])),
):
    options = await AuditRegulationService.options_service(auth)
    return SuccessResponse(data=options)

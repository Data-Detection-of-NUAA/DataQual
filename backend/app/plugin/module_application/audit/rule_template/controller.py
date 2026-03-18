"""
审计规则模板Controller
"""
from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse

from app.common.response import SuccessResponse
from app.common.request import PaginationService
from app.core.router_class import OperationLogRoute
from app.core.dependencies import AuthPermission
from app.core.base_params import PaginationQueryParam
from app.api.v1.module_system.auth.schema import AuthSchema
from .service import AuditRuleTemplateService
from .schema import (
    AuditRuleTemplateCreate,
    AuditRuleTemplateUpdate,
    AuditRuleTemplateQueryParam,
    AuditRuleTemplateBatchDelete
)


RuleTemplateRouter = APIRouter(
    route_class=OperationLogRoute,
    prefix="/audit/rule-template",
    tags=["审计规则模板管理"]
)


@RuleTemplateRouter.get("/list", summary="获取规则模板列表")
async def get_template_list(
    page: PaginationQueryParam = Depends(),
    params: AuditRuleTemplateQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:rule_template:list"]))
) -> JSONResponse:
    """获取规则模板列表（分页）"""
    templates, total = await AuditRuleTemplateService.list_service(params=params, auth=auth)
    result = await PaginationService.paginate(
        data_list=templates,
        page_no=page.page_no,
        page_size=page.page_size
    )
    return SuccessResponse(data=result)


@RuleTemplateRouter.get("/all", summary="获取所有启用的模板")
async def get_all_active_templates(
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:rule_template:list"]))
) -> JSONResponse:
    """获取所有启用的规则模板"""
    templates = await AuditRuleTemplateService.all_active_service(auth=auth)
    return SuccessResponse(data=templates)


@RuleTemplateRouter.get("/options", summary="获取模板选项")
async def get_template_options(
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:rule_template:list"]))
) -> JSONResponse:
    """获取规则模板下拉框选项"""
    options = await AuditRuleTemplateService.options_service(auth=auth)
    return SuccessResponse(data=options)


@RuleTemplateRouter.get("/detail/{id}", summary="获取模板详情")
async def get_template_detail(
    id: int = Path(..., description="模板ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:rule_template:detail"]))
) -> JSONResponse:
    """获取规则模板详情"""
    template = await AuditRuleTemplateService.detail_service(id=id, auth=auth)
    return SuccessResponse(data=template)


@RuleTemplateRouter.post("/create", summary="创建规则模板")
async def create_template(
    template_in: AuditRuleTemplateCreate,
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:rule_template:create"]))
) -> JSONResponse:
    """创建规则模板"""
    template = await AuditRuleTemplateService.create_service(obj_in=template_in, auth=auth)
    return SuccessResponse(data=template, msg="创建成功")


@RuleTemplateRouter.put("/update/{id}", summary="更新规则模板")
async def update_template(
    id: int = Path(..., description="模板ID"),
    template_in: AuditRuleTemplateUpdate = None,
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:rule_template:update"]))
) -> JSONResponse:
    """更新规则模板"""
    template = await AuditRuleTemplateService.update_service(
        id=id,
        obj_in=template_in,
        auth=auth
    )
    return SuccessResponse(data=template, msg="更新成功")


@RuleTemplateRouter.delete("/delete", summary="删除规则模板")
async def delete_templates(
    batch_in: AuditRuleTemplateBatchDelete,
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:rule_template:delete"]))
) -> JSONResponse:
    """批量删除规则模板"""
    await AuditRuleTemplateService.delete_service(ids=batch_in.ids, auth=auth)
    return SuccessResponse(msg="删除成功")

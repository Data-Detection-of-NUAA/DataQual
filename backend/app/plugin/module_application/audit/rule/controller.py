"""
审计规则Controller
"""
from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse

from app.common.response import SuccessResponse
from app.common.request import PaginationService
from app.core.router_class import OperationLogRoute
from app.core.dependencies import AuthPermission
from app.core.base_params import PaginationQueryParam
from app.api.v1.module_system.auth.schema import AuthSchema
from .service import AuditRuleService
from .schema import (
    AuditRuleCreate,
    AuditRuleUpdate,
    AuditRuleQueryParam,
    AuditRuleBatchDelete,
    AuditRuleBatchStatus,
)


RuleRouter = APIRouter(
    route_class=OperationLogRoute,
    prefix="/audit/rule",
    tags=["审计规则管理"]
)


@RuleRouter.get("/list", summary="获取规则列表")
async def get_rule_list(
    page: PaginationQueryParam = Depends(),
    params: AuditRuleQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:rule:list"]))
) -> JSONResponse:
    """获取规则列表（分页）"""
    rules_list = await AuditRuleService.list_service(params=params, auth=auth)
    result_dict = await PaginationService.paginate(data_list=rules_list, page_no=page.page_no, page_size=page.page_size)
    return SuccessResponse(data=result_dict)


@RuleRouter.get("/all", summary="获取所有规则")
async def get_all_rules(
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:rule:list"]))
) -> JSONResponse:
    """获取所有启用的规则（不分页，用于规则选择）"""
    rules = await AuditRuleService.get_all_active_rules(auth=auth)
    return SuccessResponse(data=rules)


@RuleRouter.get("/options", summary="获取规则选项")
async def get_rule_options(
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:rule:list"]))
) -> JSONResponse:
    """获取所有启用的规则选项（用于下拉框）"""
    rules = await AuditRuleService.get_all_active_rules(auth=auth)
    return SuccessResponse(data=rules)


@RuleRouter.get("/detail/{id}", summary="获取规则详情")
async def get_rule_detail(
    id: int = Path(..., description="规则ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:rule:detail"]))
) -> JSONResponse:
    """获取规则详情"""
    rule = await AuditRuleService.detail_service(id=id, auth=auth)
    return SuccessResponse(data=rule)


@RuleRouter.post("/create", summary="创建规则")
async def create_rule(
    rule_in: AuditRuleCreate,
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:rule:create"]))
) -> JSONResponse:
    """创建新规则"""
    rule = await AuditRuleService.create_service(obj_in=rule_in, auth=auth)
    return SuccessResponse(data=rule, msg="创建成功")


@RuleRouter.put("/update", summary="更新规则")
async def update_rule(
    id: int = Query(..., description="规则ID"),
    rule_in: AuditRuleUpdate = None,
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:rule:update"]))
) -> JSONResponse:
    """更新规则"""
    rule = await AuditRuleService.update_service(id=id, obj_in=rule_in, auth=auth)
    return SuccessResponse(data=rule, msg="更新成功")


@RuleRouter.delete("/delete/{id}", summary="删除规则")
async def delete_rule(
    id: int = Path(..., description="规则ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:rule:delete"]))
) -> JSONResponse:
    """删除规则"""
    await AuditRuleService.delete_service(id=id, auth=auth)
    return SuccessResponse(msg="删除成功")


@RuleRouter.delete("/delete", summary="批量删除规则")
async def delete_rules(
    batch_in: AuditRuleBatchDelete,
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:rule:delete"]))
) -> JSONResponse:
    """批量删除规则"""
    await AuditRuleService.delete_batch_service(ids=batch_in.ids, auth=auth)
    return SuccessResponse(msg="批量删除成功")


@RuleRouter.patch("/batch", summary="批量设置规则状态")
async def batch_update_rule_status(
    batch_in: AuditRuleBatchStatus,
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:rule:patch"]))
) -> JSONResponse:
    """批量启用/禁用规则"""
    await AuditRuleService.batch_update_service(
        ids=batch_in.ids,
        is_active=batch_in.is_active,
        auth=auth
    )
    return SuccessResponse(msg="状态更新成功")

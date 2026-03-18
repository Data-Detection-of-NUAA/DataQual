"""
审计规则模板服务层
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.plugin.module_application.audit.rule_template import crud
from app.plugin.module_application.audit.rule_template.schema import (
    AuditRuleTemplateCreate,
    AuditRuleTemplateUpdate,
    AuditRuleTemplateQueryParam
)
from app.core.crud import DaveCRUD


async def list_service(
    db: AsyncSession,
    query_params: AuditRuleTemplateQueryParam,
    page: int,
    limit: int
) -> Any:
    """获取模板列表（分页）"""
    query_dict = {}
    if query_params.template_code:
        query_dict['template_code'] = query_params.template_code
    if query_params.template_name:
        query_dict['template_name'] = query_params.template_name
    if query_params.template_category:
        query_dict['template_category'] = query_params.template_category
    if query_params.is_active is not None:
        query_dict['is_active'] = query_params.is_active

    from app.plugin.module_application.audit.rule_template.model import AuditRuleTemplate
    return await DaveCRUD(AuditRuleTemplate).select_page_core(
        db=db,
        where_dict=query_dict,
        page=page,
        limit=limit,
        order_by=['template_category', 'template_code']
    )


async def detail_service(
    db: AsyncSession,
    template_id: int
) -> Any:
    """获取模板详情"""
    return await crud.get_template_by_id(db, template_id)


async def all_active_service(
    db: AsyncSession
) -> list[Any]:
    """获取所有启用的模板"""
    return await crud.get_all_active_templates(db)


async def options_service(
    db: AsyncSession
) -> list[dict]:
    """获取模板选项（用于下拉框）"""
    templates = await crud.get_all_active_templates(db)
    return [
        {
            "value": template.id,
            "label": template.template_name,
            "code": template.template_code,
            "category": template.template_category
        }
        for template in templates
    ]


async def create_service(
    db: AsyncSession,
    create_data: AuditRuleTemplateCreate
) -> Any:
    """创建模板"""
    # 检查编码是否已存在
    existing = await crud.get_template_by_code(db, create_data.template_code)
    if existing:
        raise ValueError(f"模板编码 {create_data.template_code} 已存在")

    return await crud.create_template(db, create_data.model_dump())


async def update_service(
    db: AsyncSession,
    template_id: int,
    update_data: AuditRuleTemplateUpdate
) -> Any:
    """更新模板"""
    template = await crud.get_template_by_id(db, template_id)
    if not template:
        raise ValueError(f"模板ID {template_id} 不存在")

    # 如果更新编码，检查是否重复
    if update_data.template_code and update_data.template_code != template.template_code:
        existing = await crud.get_template_by_code(db, update_data.template_code)
        if existing:
            raise ValueError(f"模板编码 {update_data.template_code} 已存在")

    return await crud.update_template(db, template_id, update_data.model_dump(exclude_unset=True))


async def delete_service(
    db: AsyncSession,
    template_ids: list[int]
) -> int:
    """删除模板（支持批量）"""
    # TODO: 检查模板是否被规则使用
    # 如果模板被使用，可以选择：
    # 1. 禁止删除
    # 2. 只是标记为不可用
    # 3. 级联处理相关规则

    if len(template_ids) == 1:
        success = await crud.delete_template(db, template_ids[0])
        return 1 if success else 0
    else:
        return await crud.batch_delete_templates(db, template_ids)

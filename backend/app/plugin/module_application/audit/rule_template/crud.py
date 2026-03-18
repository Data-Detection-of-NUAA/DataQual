"""
审计规则模板CRUD操作
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.plugin.module_application.audit.rule_template.model import AuditRuleTemplate


async def create_template(
    db: AsyncSession,
    template_data: dict
) -> AuditRuleTemplate:
    """创建规则模板"""
    template = AuditRuleTemplate(**template_data)
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


async def get_template_by_id(
    db: AsyncSession,
    template_id: int
) -> AuditRuleTemplate | None:
    """根据ID获取模板"""
    from sqlalchemy import select
    result = await db.execute(
        select(AuditRuleTemplate).where(AuditRuleTemplate.id == template_id)
    )
    return result.scalar_one_or_none()


async def get_template_by_code(
    db: AsyncSession,
    template_code: str
) -> AuditRuleTemplate | None:
    """根据编码获取模板"""
    from sqlalchemy import select
    result = await db.execute(
        select(AuditRuleTemplate).where(AuditRuleTemplate.template_code == template_code)
    )
    return result.scalar_one_or_none()


async def get_all_active_templates(
    db: AsyncSession
) -> list[AuditRuleTemplate]:
    """获取所有启用的模板"""
    from sqlalchemy import select
    result = await db.execute(
        select(AuditRuleTemplate)
        .where(AuditRuleTemplate.is_active == 1)
        .order_by(AuditRuleTemplate.template_category, AuditRuleTemplate.template_code)
    )
    return list(result.scalars().all())


async def update_template(
    db: AsyncSession,
    template_id: int,
    update_data: dict
) -> AuditRuleTemplate | None:
    """更新模板"""
    template = await get_template_by_id(db, template_id)
    if not template:
        return None

    for key, value in update_data.items():
        if value is not None and hasattr(template, key):
            setattr(template, key, value)

    await db.commit()
    await db.refresh(template)
    return template


async def delete_template(
    db: AsyncSession,
    template_id: int
) -> bool:
    """删除模板"""
    template = await get_template_by_id(db, template_id)
    if not template:
        return False

    await db.delete(template)
    await db.commit()
    return True


async def batch_delete_templates(
    db: AsyncSession,
    template_ids: list[int]
) -> int:
    """批量删除模板"""
    from sqlalchemy import delete
    result = await db.execute(
        delete(AuditRuleTemplate).where(AuditRuleTemplate.id.in_(template_ids))
    )
    await db.commit()
    return result.rowcount

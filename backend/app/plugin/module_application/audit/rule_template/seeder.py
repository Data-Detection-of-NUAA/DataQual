"""
规则模板数据初始化
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.plugin.module_application.audit.rule_template.model import AuditRuleTemplate
from app.plugin.module_application.audit.rule_template.default_templates import DEFAULT_RULE_TEMPLATES


async def seed_default_templates(db: AsyncSession) -> None:
    """
    初始化默认规则模板
    """
    from sqlalchemy import select

    for template_data in DEFAULT_RULE_TEMPLATES:
        # 检查模板是否已存在
        result = await db.execute(
            select(AuditRuleTemplate).where(
                AuditRuleTemplate.template_code == template_data['template_code']
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"模板 {template_data['template_code']} 已存在，跳过")
            continue

        # 创建新模板
        template = AuditRuleTemplate(**template_data)
        db.add(template)
        print(f"创建模板: {template_data['template_code']} - {template_data['template_name']}")

    await db.commit()
    print(f"默认规则模板初始化完成，共 {len(DEFAULT_RULE_TEMPLATES)} 个模板")


async def reset_templates(db: AsyncSession) -> None:
    """
    重置规则模板（删除所有模板并重新创建）
    慎用！会删除所有模板数据
    """
    from sqlalchemy import delete

    # 删除所有模板
    await db.execute(delete(AuditRuleTemplate))
    await db.commit()
    print("已删除所有规则模板")

    # 重新创建默认模板
    await seed_default_templates(db)

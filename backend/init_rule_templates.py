"""
初始化规则模板系统
执行数据库迁移并初始化10个默认规则模板
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config.setting import settings
from app.plugin.module_application.audit.rule_template.seeder import seed_default_templates


async def init_templates():
    """初始化规则模板"""
    print("=" * 60)
    print("规则模板系统初始化")
    print("=" * 60)

    # 创建数据库连接
    print("\n1. 连接数据库...")
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    try:
        async with async_session() as session:
            print("✓ 数据库连接成功")

            # 初始化规则模板
            print("\n2. 初始化规则模板...")
            await seed_default_templates(session)
            print("✓ 规则模板初始化完成")

            # 统计模板数量
            from sqlalchemy import select, func
            from app.plugin.module_application.audit.rule_template.model import AuditRuleTemplate

            result = await session.execute(
                select(func.count(AuditRuleTemplate.id))
            )
            total_count = result.scalar()

            result = await session.execute(
                select(func.count(AuditRuleTemplate.id))
                .where(AuditRuleTemplate.is_active == 1)
            )
            active_count = result.scalar()

            print(f"\n✓ 总模板数: {total_count}")
            print(f"✓ 已启用模板: {active_count}")

            # 显示所有模板
            print("\n3. 已安装的规则模板:")
            print("-" * 60)

            result = await session.execute(
                select(AuditRuleTemplate)
                .order_by(AuditRuleTemplate.template_category, AuditRuleTemplate.template_code)
            )
            templates = result.scalars().all()

            current_category = None
            for template in templates:
                if template.template_category != current_category:
                    current_category = template.template_category
                    print(f"\n【{current_category}】")

                status = "✓ 启用" if template.is_active else "✗ 禁用"
                print(f"  {status} {template.template_code:<30} {template.template_name}")

            print("\n" + "=" * 60)
            print("初始化完成！")
            print("=" * 60)
            print("\n下一步操作:")
            print("1. 查看规则模板: GET /audit/rule-template/list")
            print("2. 参考快速开始指南: backend/app/plugin/module_application/audit/QUICKSTART.md")
            print("3. 开始解析法规并生成规则！")

    except Exception as e:
        print(f"\n✗ 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await engine.dispose()

    return True


if __name__ == "__main__":
    print("\n" + "🚀 " * 20)
    result = asyncio.run(init_templates())
    print("🚀 " * 20 + "\n")

    sys.exit(0 if result else 1)

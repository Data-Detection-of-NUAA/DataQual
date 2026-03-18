"""
更新审计模块菜单路径的脚本
将 module_audit 更新为 module_application/audit
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import AsyncSession, async_engine
from sqlalchemy import text


async def update_menu_paths():
    """更新菜单路径"""

    sql_commands = [
        # 更新权限字符串
        """
        UPDATE sys_menu
        SET permission = REPLACE(permission, 'module_audit:', 'module_application:audit:')
        WHERE permission LIKE 'module_audit:%'
        """,

        # 更新组件路径
        """
        UPDATE sys_menu
        SET component_path = REPLACE(component_path, 'module_audit/', 'module_application/audit/')
        WHERE component_path LIKE 'module_audit/%'
        """,

        # 更新路由路径
        """
        UPDATE sys_menu
        SET route_path = REPLACE(route_path, '/audit/', '/application/audit/')
        WHERE route_path LIKE '/audit/%'
        """
    ]

    async with AsyncSession(async_engine) as session:
        try:
            print("开始更新菜单路径...")

            for i, sql in enumerate(sql_commands, 1):
                result = await session.execute(text(sql))
                print(f"✓ 执行第 {i} 条 SQL，影响 {result.rowcount} 行")

            await session.commit()
            print("\n✅ 菜单路径更新成功！")

            # 查询更新后的结果
            query = text("""
                SELECT id, menu_name, route_path, component_path, permission
                FROM sys_menu
                WHERE permission LIKE '%audit%'
                   OR component_path LIKE '%audit%'
                   OR route_path LIKE '%audit%'
                ORDER BY id
            """)
            result = await session.execute(query)
            rows = result.fetchall()

            print(f"\n更新后的审计相关菜单（共 {len(rows)} 条）：")
            for row in rows[:5]:  # 只显示前5条
                print(f"  - {row.menu_name}: {row.route_path}")

            if len(rows) > 5:
                print(f"  ... 还有 {len(rows) - 5} 条")

        except Exception as e:
            await session.rollback()
            print(f"❌ 更新失败: {str(e)}")
            raise


if __name__ == "__main__":
    asyncio.run(update_menu_paths())

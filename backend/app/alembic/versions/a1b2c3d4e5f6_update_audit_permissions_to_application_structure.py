"""update_audit_permissions_to_application_structure

Revision ID: a1b2c3d4e5f6
Revises: 9d8b1d2c3a4e
Create Date: 2026-01-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '9d8b1d2c3a4e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 更新权限字符串
    op.execute("""
        UPDATE sys_menu
        SET permission = REPLACE(permission, 'module_audit:', 'module_application:audit:')
        WHERE permission LIKE 'module_audit:%'
    """)

    # 更新组件路径
    op.execute("""
        UPDATE sys_menu
        SET component_path = REPLACE(component_path, 'module_audit/', 'module_application/audit/')
        WHERE component_path LIKE 'module_audit/%'
    """)

    # 更新路由路径
    op.execute("""
        UPDATE sys_menu
        SET route_path = REPLACE(route_path, '/audit/', '/application/audit/')
        WHERE route_path LIKE '/audit/%'
    """)


def downgrade() -> None:
    # 回滚权限字符串
    op.execute("""
        UPDATE sys_menu
        SET permission = REPLACE(permission, 'module_application:audit:', 'module_audit:')
        WHERE permission LIKE 'module_application:audit:%'
    """)

    # 回滚组件路径
    op.execute("""
        UPDATE sys_menu
        SET component_path = REPLACE(component_path, 'module_application/audit/', 'module_audit/')
        WHERE component_path LIKE 'module_application/audit/%'
    """)

    # 回滚路由路径
    op.execute("""
        UPDATE sys_menu
        SET route_path = REPLACE(route_path, '/application/audit/', '/audit/')
        WHERE route_path LIKE '/application/audit/%'
    """)

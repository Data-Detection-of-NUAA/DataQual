"""add audit regulation table and relation

Revision ID: 9d8b1d2c3a4e
Revises: 7a49feadbc1f
Create Date: 2026-01-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9d8b1d2c3a4e"
down_revision: Union[str, None] = "7a49feadbc1f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    table_names = set(inspector.get_table_names())
    if "audit_regulation" not in table_names:
        op.create_table(
            "audit_regulation",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, comment="主键ID"),
            sa.Column("uuid", sa.String(length=64), nullable=False, unique=True, comment="UUID全局唯一标识"),
            sa.Column("status", sa.String(length=10), nullable=False, server_default="0", comment="是否启用(0:启用 1:停用)"),
            sa.Column("description", sa.Text(), nullable=True, comment="备注/描述"),
            sa.Column("created_time", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="创建时间"),
            sa.Column("updated_time", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="更新时间"),
            sa.Column("regulation_name", sa.String(length=200), nullable=False, comment="法规名称"),
            sa.Column("file_name", sa.String(length=255), nullable=False, comment="上传原始文件名"),
            sa.Column("file_type", sa.String(length=50), nullable=False, comment="文件类型/扩展名"),
            sa.Column("file_path", sa.String(length=500), nullable=False, comment="法规文件存储路径"),
            sa.Column("file_size", sa.Integer(), nullable=True, comment="文件大小(字节)"),
            mysql_charset="utf8mb4",
            comment="审计法规资料表",
        )
        op.create_index("ix_audit_regulation_uuid", "audit_regulation", ["uuid"], unique=True)
        op.create_index("ix_audit_regulation_status", "audit_regulation", ["status"])
        op.create_index("ix_audit_regulation_created_time", "audit_regulation", ["created_time"])
        op.create_index("ix_audit_regulation_updated_time", "audit_regulation", ["updated_time"])
        op.create_index("ix_audit_regulation_name", "audit_regulation", ["regulation_name"])

    audit_task_columns = {col["name"] for col in inspector.get_columns("audit_task")}
    if "regulation_id" not in audit_task_columns:
        op.add_column(
            "audit_task",
            sa.Column("regulation_id", sa.Integer(), nullable=True, comment="引用的法规ID"),
        )
        op.create_index("ix_audit_task_regulation_id", "audit_task", ["regulation_id"])
        op.create_foreign_key(
            "fk_audit_task_regulation",
            source_table="audit_task",
            referent_table="audit_regulation",
            local_cols=["regulation_id"],
            remote_cols=["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    audit_task_columns = {col["name"] for col in inspector.get_columns("audit_task")}
    fk_names = {fk["name"] for fk in inspector.get_foreign_keys("audit_task")}

    if "regulation_id" in audit_task_columns:
        if "fk_audit_task_regulation" in fk_names:
            op.drop_constraint("fk_audit_task_regulation", "audit_task", type_="foreignkey")
        op.drop_index("ix_audit_task_regulation_id", table_name="audit_task")
        op.drop_column("audit_task", "regulation_id")

    table_names = set(inspector.get_table_names())
    if "audit_regulation" in table_names:
        op.drop_index("ix_audit_regulation_name", table_name="audit_regulation")
        op.drop_index("ix_audit_regulation_updated_time", table_name="audit_regulation")
        op.drop_index("ix_audit_regulation_created_time", table_name="audit_regulation")
        op.drop_index("ix_audit_regulation_status", table_name="audit_regulation")
        op.drop_index("ix_audit_regulation_uuid", table_name="audit_regulation")
        op.drop_table("audit_regulation")

"""add remark column to audit_rule

Revision ID: 7a49feadbc1f
Revises: 968312f7e3ca
Create Date: 2026-01-26 20:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "7a49feadbc1f"
down_revision: Union[str, None] = "968312f7e3ca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("audit_rule")}
    if "remark" not in columns:
        op.add_column(
            "audit_rule",
            sa.Column("remark", sa.Text(), nullable=True, comment="备注"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("audit_rule")}
    if "remark" in columns:
        op.drop_column("audit_rule", "remark")

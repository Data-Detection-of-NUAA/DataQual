"""add uuid and description to dataset_info

Revision ID: add_uuid_description
Revises: 465f7bf557e7
Create Date: 2026-01-19 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_uuid_description'
down_revision: Union[str, None] = '465f7bf557e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 检查并添加 uuid 列（如果不存在）
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('dataset_info')]

    if 'uuid' not in columns:
        op.add_column('dataset_info', sa.Column('uuid', sa.String(length=64), nullable=True, comment='UUID全局唯一标识'))

        # 为现有记录生成 uuid
        op.execute("""
            UPDATE dataset_info
            SET uuid = CONCAT('dataset-', LPAD(id, 10, '0'), '-', SUBSTRING(MD5(CONCAT(id, name, created_time)), 1, 12))
            WHERE uuid IS NULL
        """)

        # 设置 uuid 为非空并添加唯一索引 - MySQL 需要完整的列定义
        op.execute("ALTER TABLE dataset_info MODIFY COLUMN uuid VARCHAR(64) NOT NULL COMMENT 'UUID全局唯一标识'")
        op.create_unique_constraint('uq_dataset_uuid', 'dataset_info', ['uuid'])
        op.create_index('idx_dataset_uuid', 'dataset_info', ['uuid'])

    # 检查并添加 description 列（如果不存在）
    if 'description' not in columns:
        op.add_column('dataset_info', sa.Column('description', sa.Text(), nullable=True, comment='备注/描述'))

        # 迁移 remark 数据到 description（如果 remark 存在）
        if 'remark' in columns:
            op.execute("UPDATE dataset_info SET description = remark WHERE remark IS NOT NULL")
            op.drop_column('dataset_info', 'remark')


def downgrade() -> None:
    # 恢复 remark 列
    op.add_column('dataset_info', sa.Column('remark', sa.String(length=500), nullable=True, comment='备注'))
    op.execute("UPDATE dataset_info SET remark = description WHERE description IS NOT NULL")
    op.drop_column('dataset_info', 'description')

    # 删除 uuid 相关
    op.drop_index('idx_dataset_uuid', table_name='dataset_info')
    op.drop_constraint('uq_dataset_uuid', 'dataset_info', type_='unique')
    op.drop_column('dataset_info', 'uuid')

"""add dataset tables

Revision ID: 465f7bf557e7
Revises: 
Create Date: 2026-01-18 16:11:31.233048

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '465f7bf557e7'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建数据集信息表
    op.create_table(
        'dataset_info',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('created_time', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_time', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.Column('created_id', sa.Integer(), nullable=True, comment='创建者ID'),
        sa.Column('updated_id', sa.Integer(), nullable=True, comment='更新者ID'),
        sa.Column('status', sa.String(length=1), nullable=True, server_default='0', comment='状态(0:正常 1:停用)'),
        sa.Column('remark', sa.String(length=500), nullable=True, comment='备注'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='数据集名称'),
        sa.Column('original_filename', sa.String(length=255), nullable=False, comment='原始文件名'),
        sa.Column('file_size', sa.BIGINT(), nullable=False, comment='文件大小(字节)'),
        sa.Column('storage_path', sa.String(length=512), nullable=False, comment='存储路径'),
        sa.Column('file_hash', sa.String(length=64), nullable=False, comment='文件哈希值(MD5/SHA256)'),
        sa.Column('upload_id', sa.String(length=64), nullable=True, comment='上传会话ID'),
        sa.Column('upload_status', sa.String(length=20), nullable=False, server_default='uploading', comment='上传状态'),
        sa.Column('modality', sa.String(length=20), nullable=False, server_default='unknown', comment='数据模态类型'),
        sa.Column('sample_count', sa.Integer(), nullable=True, comment='样本数量'),
        sa.Column('class_count', sa.Integer(), nullable=True, comment='类别数量'),
        sa.Column('dataset_metadata', sa.Text(), nullable=True, comment='元数据(JSON格式)'),
        sa.Column('analysis_result', sa.Text(), nullable=True, comment='分析结果(JSON格式)'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_hash'),
        sa.UniqueConstraint('upload_id'),
        comment='数据集信息表'
    )

    # 创建索引
    op.create_index('idx_dataset_hash', 'dataset_info', ['file_hash'])
    op.create_index('idx_dataset_upload_status', 'dataset_info', ['upload_status'])

    # 创建数据集分片表
    op.create_table(
        'dataset_chunk',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('created_time', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_time', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.Column('dataset_id', sa.Integer(), nullable=False, comment='数据集ID'),
        sa.Column('upload_id', sa.String(length=64), nullable=False, comment='上传会话ID'),
        sa.Column('chunk_index', sa.Integer(), nullable=False, comment='分片索引'),
        sa.Column('chunk_hash', sa.String(length=64), nullable=False, comment='分片哈希值'),
        sa.Column('chunk_size', sa.Integer(), nullable=False, comment='分片大小(字节)'),
        sa.Column('chunk_storage_path', sa.String(length=512), nullable=False, comment='分片存储路径'),
        sa.Column('is_uploaded', sa.Integer(), nullable=False, server_default='0', comment='是否已上传'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['dataset_id'], ['dataset_info.id'], ondelete='CASCADE', onupdate='CASCADE'),
        comment='数据集分片表'
    )

    # 创建索引
    op.create_index('idx_chunk_dataset_id', 'dataset_chunk', ['dataset_id'])
    op.create_index('idx_chunk_upload_id', 'dataset_chunk', ['upload_id'])
    op.create_index('idx_chunk_index', 'dataset_chunk', ['dataset_id', 'chunk_index'])


def downgrade() -> None:
    # 删除数据集分片表
    op.drop_index('idx_chunk_index', table_name='dataset_chunk')
    op.drop_index('idx_chunk_upload_id', table_name='dataset_chunk')
    op.drop_index('idx_chunk_dataset_id', table_name='dataset_chunk')
    op.drop_table('dataset_chunk')

    # 删除数据集信息表
    op.drop_index('idx_dataset_upload_status', table_name='dataset_info')
    op.drop_index('idx_dataset_hash', table_name='dataset_info')
    op.drop_table('dataset_info')

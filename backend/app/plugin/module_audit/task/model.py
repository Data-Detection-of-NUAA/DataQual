"""
审计任务模型
"""
from sqlalchemy import String, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, MappedBase


class AuditTask(ModelMixin, MappedBase):
    """审计任务表"""
    __tablename__ = 'audit_task'
    __table_args__ = {'comment': '审计任务表'}

    task_name: Mapped[str] = mapped_column(String(200), nullable=False, comment='任务名称')
    task_status: Mapped[str] = mapped_column(String(20), default='pending',
                                             comment='任务状态：pending/processing/completed/failed')

    # 步骤1: 法规文件
    regulation_file_type: Mapped[str | None] = mapped_column(String(50), comment='法规文件类型：txt/xml/docx/pdf')
    regulation_file_path: Mapped[str | None] = mapped_column(String(500), comment='法规文件路径')
    regulation_file_name: Mapped[str | None] = mapped_column(String(200), comment='法规文件名')

    # 步骤2: AI匹配的规则
    matched_rules: Mapped[dict | None] = mapped_column(JSON, comment='AI匹配的规则ID列表')
    selected_rules: Mapped[dict | None] = mapped_column(JSON, comment='用户最终选择的规则ID列表')

    # 步骤3: 数据集文件
    dataset_file_type: Mapped[str | None] = mapped_column(String(50), comment='数据集文件类型')
    dataset_file_path: Mapped[str | None] = mapped_column(String(500), comment='数据集文件路径')
    dataset_file_name: Mapped[str | None] = mapped_column(String(200), comment='数据集文件名')

    # 审计结果
    total_records: Mapped[int] = mapped_column(Integer, default=0, comment='总记录数')
    error_records: Mapped[int] = mapped_column(Integer, default=0, comment='错误记录数')
    data_errors: Mapped[dict | None] = mapped_column(JSON, comment='数据错误详情')
    label_errors: Mapped[dict | None] = mapped_column(JSON, comment='标签错误详情')
    audit_report_path: Mapped[str | None] = mapped_column(String(500), comment='审计报告路径')


class AuditError(ModelMixin, MappedBase):
    """审计错误详情表"""
    __tablename__ = 'audit_error'
    __table_args__ = {'comment': '审计错误详情表'}

    task_id: Mapped[int] = mapped_column(Integer, nullable=False, comment='任务ID', index=True)
    error_type: Mapped[str] = mapped_column(String(20), nullable=False, comment='错误类型：data/label', index=True)

    # 错误位置
    row_number: Mapped[int | None] = mapped_column(Integer, comment='行号')
    column_name: Mapped[str | None] = mapped_column(String(100), comment='列名')
    field_name: Mapped[str | None] = mapped_column(String(100), comment='字段名')

    # 错误内容
    original_value: Mapped[str | None] = mapped_column(Text, comment='原始值')
    error_message: Mapped[str | None] = mapped_column(Text, comment='错误描述')
    rule_id: Mapped[int | None] = mapped_column(Integer, comment='违反的规则ID')
    severity: Mapped[str | None] = mapped_column(String(20), comment='严重级别')

    # 错误标记位置（用于前端波浪线标记）
    start_position: Mapped[int | None] = mapped_column(Integer, comment='错误开始位置')
    end_position: Mapped[int | None] = mapped_column(Integer, comment='错误结束位置')

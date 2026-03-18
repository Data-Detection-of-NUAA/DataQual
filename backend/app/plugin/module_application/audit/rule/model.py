"""
审计规则模型
"""
from sqlalchemy import String, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, MappedBase


class AuditRule(ModelMixin, MappedBase):
    """审计规则表"""
    __tablename__ = 'audit_rule'
    __table_args__ = {'comment': '审计规则表'}

    rule_code: Mapped[str] = mapped_column(String(100), nullable=False, comment='规则编码', index=True)
    rule_name: Mapped[str] = mapped_column(String(200), nullable=False, comment='规则名称')
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False, comment='规则类型：email/phone/idcard/custom等')
    rule_description: Mapped[str | None] = mapped_column(Text, comment='规则描述')
    rule_expression: Mapped[str | None] = mapped_column(Text, comment='规则表达式(正则/JSON)')
    severity: Mapped[str] = mapped_column(String(20), default='warning', comment='严重级别：error/warning/info')
    is_active: Mapped[int] = mapped_column(Integer, default=1, comment='是否启用：1-启用，0-禁用')
    remark: Mapped[str | None] = mapped_column(Text, default=None, comment='备注')

    # 规则模板实例化相关字段
    template_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('audit_rule_template.id', ondelete='SET NULL'),
        comment='关联的规则模板ID（如果是从模板实例化而来）'
    )
    instance_parameters: Mapped[dict | None] = mapped_column(
        JSON,
        comment='实例化参数（如果是从模板实例化，存储具体的参数值）'
    )
    regulation_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('audit_regulation.id', ondelete='SET NULL'),
        comment='关联的法规ID（如果是从法规解析生成）'
    )
    auto_generated: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment='是否自动生成：1-AI自动生成，0-手动创建'
    )

"""
审计规则模型
"""
from sqlalchemy import String, Text, Integer
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

"""
审计规则模板模型
规则模板是通用的、可参数化的规则，可以实例化为具体的规则
"""
from sqlalchemy import String, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, MappedBase


class AuditRuleTemplate(ModelMixin, MappedBase):
    """审计规则模板表"""
    __tablename__ = 'audit_rule_template'
    __table_args__ = {'comment': '审计规则模板表 - 用于规则实例化'}

    template_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment='模板编码（唯一）',
        index=True
    )
    template_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment='模板名称'
    )
    template_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment='模板分类：field_validation/format_check/business_rule/data_quality等'
    )
    template_description: Mapped[str | None] = mapped_column(
        Text,
        comment='模板描述（详细说明该模板的用途）'
    )

    # 参数定义 - JSON Schema格式
    parameters_schema: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment='参数定义（JSON Schema格式），定义实例化时需要哪些参数'
    )

    # 验证逻辑模板
    validation_template: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment='验证逻辑模板配置'
    )

    # 默认配置
    default_severity: Mapped[str] = mapped_column(
        String(20),
        default='warning',
        comment='默认严重级别：error/warning/info'
    )

    # 标签和元信息
    tags: Mapped[dict | None] = mapped_column(
        JSON,
        comment='模板标签（用于分类和搜索）'
    )

    is_active: Mapped[int] = mapped_column(
        Integer,
        default=1,
        comment='是否启用：1-启用，0-禁用'
    )

    remark: Mapped[str | None] = mapped_column(
        Text,
        default=None,
        comment='备注'
    )

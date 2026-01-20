"""
审计规则Schema
"""
from pydantic import Field
from typing import Optional

from app.core.base_schema import BaseSchema, QueryBaseParam


class AuditRuleBase(BaseSchema):
    """规则基础Schema"""
    rule_code: str = Field(..., description='规则编码', max_length=100)
    rule_name: str = Field(..., description='规则名称', max_length=200)
    rule_type: str = Field(..., description='规则类型', max_length=50)
    rule_description: Optional[str] = Field(None, description='规则描述')
    rule_expression: Optional[str] = Field(None, description='规则表达式')
    severity: str = Field(default='warning', description='严重级别')
    is_active: int = Field(default=1, description='是否启用')
    remark: Optional[str] = Field(None, description='备注')


class AuditRuleCreate(AuditRuleBase):
    """创建规则Schema"""
    pass


class AuditRuleUpdate(BaseSchema):
    """更新规则Schema"""
    rule_code: Optional[str] = Field(None, description='规则编码', max_length=100)
    rule_name: Optional[str] = Field(None, description='规则名称', max_length=200)
    rule_type: Optional[str] = Field(None, description='规则类型', max_length=50)
    rule_description: Optional[str] = Field(None, description='规则描述')
    rule_expression: Optional[str] = Field(None, description='规则表达式')
    severity: Optional[str] = Field(None, description='严重级别')
    is_active: Optional[int] = Field(None, description='是否启用')
    remark: Optional[str] = Field(None, description='备注')


class AuditRuleQueryParam(QueryBaseParam):
    """规则查询参数"""
    rule_code: Optional[str] = Field(None, description='规则编码')
    rule_name: Optional[str] = Field(None, description='规则名称')
    rule_type: Optional[str] = Field(None, description='规则类型')
    is_active: Optional[int] = Field(None, description='是否启用')

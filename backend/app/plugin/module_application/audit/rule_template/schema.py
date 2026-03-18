"""
审计规则模板Schema
"""
from pydantic import Field
from typing import Optional, List, Dict, Any
from fastapi import Query

from app.core.base_schema import BaseSchema


class AuditRuleTemplateBase(BaseSchema):
    """规则模板基础Schema"""
    template_code: str = Field(..., description='模板编码', max_length=100)
    template_name: str = Field(..., description='模板名称', max_length=200)
    template_category: str = Field(..., description='模板分类', max_length=50)
    template_description: Optional[str] = Field(None, description='模板描述')
    parameters_schema: Dict[str, Any] = Field(..., description='参数定义（JSON Schema）')
    validation_template: Dict[str, Any] = Field(..., description='验证逻辑模板配置')
    default_severity: str = Field(default='warning', description='默认严重级别')
    tags: Optional[Dict[str, Any]] = Field(None, description='模板标签')
    is_active: int = Field(default=1, description='是否启用')
    remark: Optional[str] = Field(None, description='备注')


class AuditRuleTemplateCreate(AuditRuleTemplateBase):
    """创建规则模板Schema"""
    pass


class AuditRuleTemplateUpdate(BaseSchema):
    """更新规则模板Schema"""
    template_code: Optional[str] = Field(None, description='模板编码', max_length=100)
    template_name: Optional[str] = Field(None, description='模板名称', max_length=200)
    template_category: Optional[str] = Field(None, description='模板分类', max_length=50)
    template_description: Optional[str] = Field(None, description='模板描述')
    parameters_schema: Optional[Dict[str, Any]] = Field(None, description='参数定义')
    validation_template: Optional[Dict[str, Any]] = Field(None, description='验证逻辑模板配置')
    default_severity: Optional[str] = Field(None, description='默认严重级别')
    tags: Optional[Dict[str, Any]] = Field(None, description='模板标签')
    is_active: Optional[int] = Field(None, description='是否启用')
    remark: Optional[str] = Field(None, description='备注')


class AuditRuleTemplateQueryParam:
    """规则模板查询参数"""
    def __init__(
        self,
        template_code: Optional[str] = Query(None, description='模板编码'),
        template_name: Optional[str] = Query(None, description='模板名称'),
        template_category: Optional[str] = Query(None, description='模板分类'),
        is_active: Optional[int] = Query(None, description='是否启用')
    ):
        self.template_code = ("like", template_code) if template_code else None
        self.template_name = ("like", template_name) if template_name else None
        self.template_category = ("eq", template_category) if template_category else None
        self.is_active = ("eq", is_active) if is_active is not None else None


class AuditRuleTemplateBatchDelete(BaseSchema):
    """批量删除规则模板"""
    ids: List[int] = Field(..., description='模板ID列表')


class RuleInstantiationRequest(BaseSchema):
    """规则实例化请求"""
    template_id: int = Field(..., description='模板ID')
    instance_parameters: Dict[str, Any] = Field(..., description='实例化参数')
    rule_code: str = Field(..., description='规则编码')
    rule_name: str = Field(..., description='规则名称')
    rule_description: Optional[str] = Field(None, description='规则描述')
    severity: str = Field(default='warning', description='严重等级')
    regulation_id: Optional[int] = Field(None, description='关联的法规ID')


class RegulationParseRequest(BaseSchema):
    """法规解析请求"""
    regulation_id: int = Field(..., description='法规ID')
    parse_mode: str = Field(default='auto', description='解析模式：auto-自动解析, manual-手动结构化输入')
    structured_input: Optional[Dict[str, Any]] = Field(None, description='结构化输入（parse_mode=manual时使用）')


class RegulationParseResult(BaseSchema):
    """法规解析结果"""
    success: bool = Field(..., description='是否成功')
    requirements_count: int = Field(..., description='提取的要求数量')
    requirements: List[Dict[str, Any]] = Field(..., description='解析的要求列表')
    error_message: Optional[str] = Field(None, description='错误消息')


class RuleBatchGenerateRequest(BaseSchema):
    """批量生成规则请求"""
    regulation_id: int = Field(..., description='法规ID')
    parsed_requirements: List[Dict[str, Any]] = Field(..., description='解析的要求列表')
    auto_activate: bool = Field(default=True, description='是否自动启用生成的规则')


class RuleBatchGenerateResult(BaseSchema):
    """批量生成规则结果"""
    success: bool = Field(..., description='是否成功')
    generated_count: int = Field(..., description='成功生成的规则数量')
    failed_count: int = Field(..., description='失败的数量')
    rule_ids: List[int] = Field(..., description='生成的规则ID列表')
    errors: List[str] = Field(default_factory=list, description='错误列表')

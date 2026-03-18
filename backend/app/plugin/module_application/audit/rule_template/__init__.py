"""
审计规则模板模块
"""
from app.plugin.module_application.audit.rule_template.model import AuditRuleTemplate
from app.plugin.module_application.audit.rule_template.controller import RuleTemplateRouter

__all__ = ['AuditRuleTemplate', 'RuleTemplateRouter']

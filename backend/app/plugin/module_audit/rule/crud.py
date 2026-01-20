"""
审计规则CRUD
"""
from app.core.base_crud import CRUDBase
from .model import AuditRule
from .schema import AuditRuleCreate, AuditRuleUpdate


class AuditRuleCRUD(CRUDBase[AuditRule, AuditRuleCreate, AuditRuleUpdate]):
    """审计规则CRUD类"""
    pass


audit_rule_crud = AuditRuleCRUD(AuditRule)

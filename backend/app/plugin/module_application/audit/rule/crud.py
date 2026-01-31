"""
审计规则CRUD
"""
from app.core.base_crud import CRUDBase
from app.api.v1.module_system.auth.schema import AuthSchema
from .model import AuditRule
from .schema import AuditRuleCreate, AuditRuleUpdate


class AuditRuleCRUD(CRUDBase[AuditRule, AuditRuleCreate, AuditRuleUpdate]):
    """审计规则CRUD类"""

    def __init__(self, auth: AuthSchema) -> None:
        """
        初始化审计规则CRUD

        参数:
        - auth (AuthSchema): 认证信息模型
        """
        self.auth = auth
        super().__init__(model=AuditRule, auth=auth)

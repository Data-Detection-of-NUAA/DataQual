"""
审计规则CRUD
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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


async def get_rule_by_code(db: AsyncSession, rule_code: str) -> AuditRule | None:
    """根据规则编码获取规则"""
    result = await db.execute(
        select(AuditRule).where(AuditRule.rule_code == rule_code)
    )
    return result.scalar_one_or_none()

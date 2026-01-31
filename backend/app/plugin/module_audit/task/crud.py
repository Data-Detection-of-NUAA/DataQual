"""
审计任务CRUD
"""
from app.core.base_crud import CRUDBase
from app.api.v1.module_system.auth.schema import AuthSchema
from .model import AuditTask, AuditError
from .schema import AuditTaskCreate, AuditTaskUpdate


class AuditTaskCRUD(CRUDBase[AuditTask, AuditTaskCreate, AuditTaskUpdate]):
    """审计任务CRUD类"""

    def __init__(self, auth: AuthSchema) -> None:
        """
        初始化审计任务CRUD

        参数:
        - auth (AuthSchema): 认证信息模型
        """
        self.auth = auth
        super().__init__(model=AuditTask, auth=auth)


class AuditErrorCRUD(CRUDBase[AuditError, None, None]):
    """审计错误CRUD类"""

    def __init__(self, auth: AuthSchema) -> None:
        """
        初始化审计错误CRUD

        参数:
        - auth (AuthSchema): 认证信息模型
        """
        self.auth = auth
        super().__init__(model=AuditError, auth=auth)

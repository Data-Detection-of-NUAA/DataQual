"""
审计任务CRUD
"""
from app.core.base_crud import CRUDBase
from .model import AuditTask, AuditError
from .schema import AuditTaskCreate, AuditTaskUpdate


class AuditTaskCRUD(CRUDBase[AuditTask, AuditTaskCreate, AuditTaskUpdate]):
    """审计任务CRUD类"""
    pass


class AuditErrorCRUD(CRUDBase[AuditError, None, None]):
    """审计错误CRUD类"""
    pass


audit_task_crud = AuditTaskCRUD(AuditTask)
audit_error_crud = AuditErrorCRUD(AuditError)

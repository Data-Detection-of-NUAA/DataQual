"""
审计法规 CRUD
"""
from app.core.base_crud import CRUDBase
from app.api.v1.module_system.auth.schema import AuthSchema
from .model import AuditRegulation
from .schema import AuditRegulationCreate, AuditRegulationUpdate


class AuditRegulationCRUD(CRUDBase[AuditRegulation, AuditRegulationCreate, AuditRegulationUpdate]):
    """审计法规 CRUD"""

    def __init__(self, auth: AuthSchema) -> None:
        super().__init__(model=AuditRegulation, auth=auth)

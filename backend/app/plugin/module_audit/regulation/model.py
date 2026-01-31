"""
审计法规资料模型
"""
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, MappedBase


class AuditRegulation(ModelMixin, MappedBase):
    """审计法规资料表"""

    __tablename__ = "audit_regulation"
    __table_args__ = {"comment": "审计法规资料表"}

    regulation_name: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True, comment="法规名称"
    )
    file_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="上传时的原始文件名"
    )
    file_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="文件类型/扩展名"
    )
    file_path: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="法规文件存储路径"
    )
    file_size: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="文件大小(字节)"
    )

"""
审计法规 Schema 定义
"""
from typing import Optional, List
from fastapi import Query
from pydantic import Field

from app.core.base_schema import BaseSchema


class AuditRegulationBase(BaseSchema):
    """法规基础字段"""

    regulation_name: str = Field(..., max_length=200, description="法规名称")
    file_name: str = Field(..., max_length=255, description="原始文件名")
    file_type: str = Field(..., max_length=50, description="文件类型/扩展名")
    file_path: str = Field(..., max_length=500, description="存储路径")
    file_size: Optional[int] = Field(None, ge=0, description="文件大小(字节)")
    description: Optional[str] = Field(None, description="法规描述/备注")


class AuditRegulationCreate(AuditRegulationBase):
    """创建法规"""

    pass


class AuditRegulationUpdate(BaseSchema):
    """更新法规"""

    regulation_name: Optional[str] = Field(None, max_length=200, description="法规名称")
    description: Optional[str] = Field(None, description="法规描述")


class AuditRegulationQueryParam:
    """法规查询参数"""

    def __init__(
        self,
        keyword: Optional[str] = Query(None, description="关键字（名称/文件名模糊匹配）"),
    ):
        self.regulation_name = ("like", keyword) if keyword else None
        self.file_name = ("like", keyword) if keyword else None


class AuditRegulationBatchDelete(BaseSchema):
    """批量删除法规"""

    ids: List[int] = Field(..., description="法规ID列表")

"""
审计任务Schema
"""
from pydantic import Field
from typing import Optional, List, Dict, Any

from app.core.base_schema import BaseSchema, QueryBaseParam


class AuditTaskCreate(BaseSchema):
    """创建审计任务Schema"""
    task_name: str = Field(..., description='任务名称', max_length=200)
    remark: Optional[str] = Field(None, description='备注')


class AuditTaskUpdate(BaseSchema):
    """更新审计任务Schema"""
    task_name: Optional[str] = Field(None, description='任务名称')
    task_status: Optional[str] = Field(None, description='任务状态')
    remark: Optional[str] = Field(None, description='备注')


class RegulationFileUpload(BaseSchema):
    """法规文件上传Schema"""
    file_type: str = Field(..., description='文件类型', max_length=50)
    file_path: str = Field(..., description='文件路径', max_length=500)
    file_name: str = Field(..., description='文件名', max_length=200)


class RuleConfirm(BaseSchema):
    """规则确认Schema"""
    selected_rules: List[int] = Field(..., description='选中的规则ID列表')


class DatasetFileUpload(BaseSchema):
    """数据集文件上传Schema"""
    file_type: str = Field(..., description='文件类型', max_length=50)
    file_path: str = Field(..., description='文件路径', max_length=500)
    file_name: str = Field(..., description='文件名', max_length=200)


class AuditTaskQueryParam(QueryBaseParam):
    """任务查询参数"""
    task_name: Optional[str] = Field(None, description='任务名称')
    task_status: Optional[str] = Field(None, description='任务状态')


class AuditErrorQueryParam(QueryBaseParam):
    """错误查询参数"""
    task_id: int = Field(..., description='任务ID')
    error_type: Optional[str] = Field(None, description='错误类型')


class AuditResultResponse(BaseSchema):
    """审计结果响应Schema"""
    task_id: int = Field(..., description='任务ID')
    task_name: str = Field(..., description='任务名称')
    task_status: str = Field(..., description='任务状态')
    total_records: int = Field(..., description='总记录数')
    error_records: int = Field(..., description='错误记录数')
    data_errors: List[Dict[str, Any]] = Field(default_factory=list, description='数据错误列表')
    label_errors: List[Dict[str, Any]] = Field(default_factory=list, description='标签错误列表')
    audit_report_path: Optional[str] = Field(None, description='审计报告路径')

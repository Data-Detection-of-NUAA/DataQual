
"""Schemas used by the audit task module."""

from typing import Optional, List, Dict, Any

from fastapi import Query
from pydantic import Field

from app.core.base_schema import BaseSchema


class AuditTaskCreate(BaseSchema):
    """Input payload when creating an audit task."""

    task_name: str = Field(..., description="Task name", max_length=200)
    description: Optional[str] = Field(None, description="Task description")


class AuditTaskUpdate(BaseSchema):
    """Fields that can be updated on an audit task."""

    task_name: Optional[str] = Field(None, description="Task name")
    task_status: Optional[str] = Field(None, description="Task status code")
    description: Optional[str] = Field(None, description="Task description")
    regulation_file_type: Optional[str] = Field(None, description="Regulation file type")
    regulation_file_path: Optional[str] = Field(None, description="Regulation file path")
    regulation_file_name: Optional[str] = Field(None, description="Regulation file name")
    regulation_id: Optional[int] = Field(None, description="Bound regulation ID")
    matched_rules: Optional[Dict[str, Any]] = Field(None, description="Matched rules payload")
    selected_rules: Optional[Dict[str, Any]] = Field(None, description="Confirmed rules payload")
    dataset_file_type: Optional[str] = Field(None, description="Dataset file type")
    dataset_file_path: Optional[str] = Field(None, description="Dataset file path")
    dataset_file_name: Optional[str] = Field(None, description="Dataset file name")
    total_records: Optional[int] = Field(None, description="Total dataset rows")
    error_records: Optional[int] = Field(None, description="Failed dataset rows")
    audit_report_path: Optional[str] = Field(None, description="Generated report path")


class RegulationFileUpload(BaseSchema):
    """Response payload describing an uploaded regulation file."""

    file_type: str = Field(..., description="File type", max_length=50)
    file_path: str = Field(..., description="File storage path", max_length=500)
    file_name: str = Field(..., description="Original or display name", max_length=200)


class RuleConfirm(BaseSchema):
    """User-confirmed rule list."""

    selected_rules: List[int] = Field(..., description="Rule IDs selected for execution")


class DatasetFileUpload(BaseSchema):
    """Response payload describing an uploaded dataset file."""

    file_type: str = Field(..., description="File type", max_length=50)
    file_path: str = Field(..., description="File storage path", max_length=500)
    file_name: str = Field(..., description="Original or display name", max_length=200)


class AuditTaskQueryParam:
    """Query helper for listing tasks."""

    def __init__(
        self,
        task_name: Optional[str] = Query(None, description="Fuzzy match on task name"),
        task_status: Optional[str] = Query(None, description="Exact match on task status"),
    ):
        self.task_name = ("like", task_name) if task_name else None
        self.task_status = ("eq", task_status) if task_status else None


class AuditErrorQueryParam:
    """Query helper for fetching audit errors."""

    def __init__(
        self,
        task_id: int = Query(..., description="Task ID"),
        error_type: Optional[str] = Query(None, description="Filter by error type (data/label)"),
        keyword: Optional[str] = Query(None, description="Keyword search on stored payload"),
    ):
        self.task_id = ("eq", task_id)
        self.error_type = ("eq", error_type) if error_type else None
        self.keyword = ("like", keyword) if keyword else None


class AuditResultResponse(BaseSchema):
    """Standard response for returning audit results."""

    task_id: int = Field(..., description="Task ID")
    task_name: str = Field(..., description="Task name")
    task_status: str = Field(..., description="Current task status")
    total_records: int = Field(..., description="Total dataset rows")
    error_records: int = Field(..., description="Rows that failed compliance")
    data_errors: List[Dict[str, Any]] = Field(default_factory=list, description="Structured data errors")
    label_errors: List[Dict[str, Any]] = Field(default_factory=list, description="Label errors")
    audit_report_path: Optional[str] = Field(None, description="Path to generated report")


class AuditTaskBatchDelete(BaseSchema):
    """Payload for deleting multiple tasks."""

    ids: List[int] = Field(..., description="Task ID list")

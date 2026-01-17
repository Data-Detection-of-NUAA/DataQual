# -*- coding: utf-8 -*-

"""
dqscan API 的 Pydantic 模型（请求/响应契约）。

读代码时你可以把它当作“前后端的数据协议说明书”：
- 哪些字段是必填/可选
- 默认算法名是什么
- status 的枚举范围是什么
"""

from __future__ import annotations

from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class SuccessResponseOut(BaseModel, Generic[T]):
    code: int
    msg: str
    data: T | None = None
    status_code: int
    success: bool


class DQScanUploadOut(BaseModel):
    file_id: str = Field(..., description="服务端文件标识（相对 backend 根目录路径）")
    filename: str = Field(..., description="原始文件名")
    file_size: int = Field(..., description="文件大小（字节）")


class DQScanAlgorithmOut(BaseModel):
    name: str
    label: str
    description: str
    params_schema: dict[str, Any]


class DQScanCreateTaskIn(BaseModel):
    file_id: str
    algorithm: str = Field(default="tabular_quality_engine_v3")
    params: dict[str, Any] | None = None


TaskStatus = Literal["PENDING", "RUNNING", "SUCCESS", "FAILED"]


class DQScanCreateTaskOut(BaseModel):
    task_id: str


class DQScanTaskOut(BaseModel):
    task_id: str
    status: TaskStatus
    progress: int = Field(ge=0, le=100)
    started_at: float | None = None
    ended_at: float | None = None
    error: str | None = None
    result_file_id: str | None = None


class DQScanResultOut(BaseModel):
    summary: dict[str, Any] = Field(default_factory=dict)
    modules: dict[str, Any] | None = None
    reports: dict[str, Any] | None = None

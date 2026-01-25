# -*- coding: utf-8 -*-

from pydantic import BaseModel, ConfigDict, Field, field_validator
from fastapi import Query

from app.core.validator import DateTimeStr
from app.core.base_schema import BaseSchema, UserBySchema


class OptimizerTaskCreateSchema(BaseModel):
    """优化器任务创建模型"""
    name: str = Field(..., max_length=100, description='任务名称')
    description: str | None = Field(None, max_length=500, description='任务描述')
    task_type: str = Field(..., max_length=50, description='任务类型')
    config: dict = Field(..., description='任务配置JSON')
    priority: int = Field(default=0, ge=0, le=10, description='优先级(0-10)')
    status: str = Field("0", description="状态(0:待执行 1:执行中 2:已完成 3:失败 4:已取消)")

    @field_validator('task_type')
    @classmethod
    def _validate_task_type(cls, v: str) -> str:
        allowed = {'query_optimization', 'index_suggestion', 'schema_optimization',
                   'performance_analysis', 'cost_optimization', 'data_quality_check'}
        v = v.strip()
        if v not in allowed:
            raise ValueError(f'任务类型必须为: {", ".join(allowed)}')
        return v


class OptimizerTaskUpdateSchema(BaseModel):
    """优化器任务更新模型"""
    name: str | None = Field(None, max_length=100, description='任务名称')
    description: str | None = Field(None, max_length=500, description='任务描述')
    task_type: str | None = Field(None, max_length=50, description='任务类型')
    config: dict | None = Field(None, description='任务配置JSON')
    priority: int | None = Field(None, ge=0, le=10, description='优先级(0-10)')
    status: str | None = Field(None, description="状态")


class OptimizerTaskOutSchema(BaseSchema, UserBySchema):
    """优化器任务响应模型"""
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str | None
    task_type: str
    config: dict
    priority: int
    status: str


class OptimizerResultCreateSchema(BaseModel):
    """优化器结果创建模型"""
    task_id: int = Field(..., description='任务ID')
    result_type: str = Field(..., max_length=50, description='结果类型')
    result_data: dict = Field(..., description='结果数据JSON')
    score: float | None = Field(None, ge=0, le=100, description='优化评分(0-100)')
    improvement: float | None = Field(None, description='改进百分比')
    status: str = Field("0", description="状态(0:待应用 1:已应用 2:已拒绝)")


class OptimizerResultUpdateSchema(BaseModel):
    """优化器结果更新模型"""
    result_type: str | None = Field(None, max_length=50, description='结果类型')
    result_data: dict | None = Field(None, description='结果数据JSON')
    score: float | None = Field(None, ge=0, le=100, description='优化评分(0-100)')
    improvement: float | None = Field(None, description='改进百分比')
    status: str | None = Field(None, description="状态")


class OptimizerResultOutSchema(BaseSchema, UserBySchema):
    """优化器结果响应模型"""
    model_config = ConfigDict(from_attributes=True)

    task_id: int
    result_type: str
    result_data: dict
    score: float | None
    improvement: float | None
    status: str


class OptimizerExecutionLogCreateSchema(BaseModel):
    """优化器执行日志创建模型"""
    task_id: int = Field(..., description='任务ID')
    execution_time: float = Field(..., description='执行时间(秒)')
    status: str = Field(..., description='执行状态')
    error_message: str | None = Field(None, description='错误信息')
    log_data: dict | None = Field(None, description='日志数据JSON')


class OptimizerExecutionLogOutSchema(BaseSchema):
    """优化器执行日志响应模型"""
    model_config = ConfigDict(from_attributes=True)

    task_id: int
    execution_time: float
    status: str
    error_message: str | None
    log_data: dict | None


class OptimizerTaskQueryParam:
    """优化器任务查询参数"""

    def __init__(
        self,
        name: str | None = Query(None, description="任务名称"),
        task_type: str | None = Query(None, description="任务类型"),
        status: str | None = Query(None, description="状态"),
        priority: int | None = Query(None, description="优先级"),
        created_time: list[DateTimeStr] | None = Query(None, description="创建时间范围", examples=["2025-01-01 00:00:00", "2025-12-31 23:59:59"]),
        updated_time: list[DateTimeStr] | None = Query(None, description="更新时间范围", examples=["2025-01-01 00:00:00", "2025-12-31 23:59:59"]),
        created_id: int | None = Query(None, description="创建人"),
        updated_id: int | None = Query(None, description="更新人"),
    ) -> None:
        # 模糊查询字段
        self.name = ("like", name) if name else None

        # 精确查询字段
        self.task_type = task_type
        self.status = status
        self.priority = priority
        self.created_id = created_id
        self.updated_id = updated_id

        # 时间范围查询
        if created_time and len(created_time) == 2:
            self.created_time = ("between", (created_time[0], created_time[1]))
        if updated_time and len(updated_time) == 2:
            self.updated_time = ("between", (updated_time[0], updated_time[1]))


class OptimizerResultQueryParam:
    """优化器结果查询参数"""

    def __init__(
        self,
        task_id: int | None = Query(None, description="任务ID"),
        result_type: str | None = Query(None, description="结果类型"),
        status: str | None = Query(None, description="状态"),
        min_score: float | None = Query(None, description="最小评分"),
        created_time: list[DateTimeStr] | None = Query(None, description="创建时间范围", examples=["2025-01-01 00:00:00", "2025-12-31 23:59:59"]),
        updated_time: list[DateTimeStr] | None = Query(None, description="更新时间范围", examples=["2025-01-01 00:00:00", "2025-12-31 23:59:59"]),
        created_id: int | None = Query(None, description="创建人"),
        updated_id: int | None = Query(None, description="更新人"),
    ) -> None:
        # 精确查询字段
        self.task_id = task_id
        self.result_type = result_type
        self.status = status
        self.created_id = created_id
        self.updated_id = updated_id

        # 范围查询
        if min_score is not None:
            self.score = (">=", min_score)

        # 时间范围查询
        if created_time and len(created_time) == 2:
            self.created_time = ("between", (created_time[0], created_time[1]))
        if updated_time and len(updated_time) == 2:
            self.updated_time = ("between", (updated_time[0], updated_time[1]))


class OptimizerExecutionLogQueryParam:
    """优化器执行日志查询参数"""

    def __init__(
        self,
        task_id: int | None = Query(None, description="任务ID"),
        status: str | None = Query(None, description="执行状态"),
        created_time: list[DateTimeStr] | None = Query(None, description="创建时间范围", examples=["2025-01-01 00:00:00", "2025-12-31 23:59:59"]),
    ) -> None:
        # 精确查询字段
        self.task_id = task_id
        self.status = status

        # 时间范围查询
        if created_time and len(created_time) == 2:
            self.created_time = ("between", (created_time[0], created_time[1]))


class OptimizerTaskRunSchema(BaseModel):
    """优化器任务执行参数"""
    override_config: dict | None = Field(None, description='覆盖配置')


class OptimizerResultApplySchema(BaseModel):
    """优化器结果应用参数"""
    apply_mode: str = Field("auto", description='应用模式(auto:自动 manual:手动 preview:预览)')
    confirm: bool = Field(False, description='是否确认应用')

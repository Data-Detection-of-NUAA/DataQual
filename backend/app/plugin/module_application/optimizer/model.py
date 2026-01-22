# -*- coding: utf-8 -*-

from sqlalchemy import String, Integer, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import ModelMixin, UserMixin


class OptimizerTaskModel(ModelMixin, UserMixin):
    """
    优化器任务表
    - 0: 待执行
    - 1: 执行中
    - 2: 已完成
    - 3: 失败
    - 4: 已取消
    """
    __tablename__: str = 'app_optimizer_task'
    __table_args__: dict[str, str] = ({'comment': '优化器任务表'})
    __loader_options__: list[str] = ["results", "execution_logs", "created_by", "updated_by"]

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment='任务名称')
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment='任务描述')
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, comment='任务类型')
    config: Mapped[dict] = mapped_column(JSON, nullable=False, comment='任务配置JSON')
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment='优先级(0-10)')

    # 关联关系
    results: Mapped[list['OptimizerResultModel'] | None] = relationship(
        back_populates="task",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    execution_logs: Mapped[list['OptimizerExecutionLogModel'] | None] = relationship(
        back_populates="task",
        lazy="selectin",
        cascade="all, delete-orphan"
    )


class OptimizerResultModel(ModelMixin, UserMixin):
    """
    优化器结果表
    - 0: 待应用
    - 1: 已应用
    - 2: 已拒绝
    """
    __tablename__: str = 'app_optimizer_result'
    __table_args__: dict[str, str] = ({'comment': '优化器结果表'})
    __loader_options__: list[str] = ["task", "created_by", "updated_by"]

    result_type: Mapped[str] = mapped_column(String(50), nullable=False, comment='结果类型')
    result_data: Mapped[dict] = mapped_column(JSON, nullable=False, comment='结果数据JSON')
    score: Mapped[float | None] = mapped_column(Float, nullable=True, comment='优化评分(0-100)')
    improvement: Mapped[float | None] = mapped_column(Float, nullable=True, comment='改进百分比')

    # 任务关联
    task_id: Mapped[int] = mapped_column(
        ForeignKey('app_optimizer_task.id', ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment='任务ID'
    )

    task: Mapped["OptimizerTaskModel"] = relationship(
        back_populates="results",
        lazy="selectin"
    )


class OptimizerExecutionLogModel(ModelMixin):
    """
    优化器执行日志表
    """
    __tablename__: str = 'app_optimizer_execution_log'
    __table_args__: dict[str, str] = ({'comment': '优化器执行日志表'})
    __loader_options__: list[str] = ["task"]

    execution_time: Mapped[float] = mapped_column(Float, nullable=False, comment='执行时间(秒)')
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment='错误信息')
    log_data: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment='日志数据JSON')

    # 任务关联
    task_id: Mapped[int] = mapped_column(
        ForeignKey('app_optimizer_task.id', ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment='任务ID'
    )

    task: Mapped["OptimizerTaskModel"] = relationship(
        back_populates="execution_logs",
        lazy="selectin"
    )

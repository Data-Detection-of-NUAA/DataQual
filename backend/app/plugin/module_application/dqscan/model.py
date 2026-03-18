# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, UserMixin


class DQScanTaskModel(ModelMixin, UserMixin):
    """
    dqscan 扫描任务表（最小可用版：任务元数据持久化）。

    说明：
    - ModelMixin.status 字段语义是“是否启用”，与任务运行状态无关；任务状态使用 task_status。
    - task_id 作为对外稳定标识（API path 参数），与 static/tasks/{task_id} 目录一致。
    """

    __tablename__: str = "app_dqscan_task"
    __table_args__: dict[str, str] = ({"comment": "dqscan 扫描任务表"})
    __loader_options__: list[str] = ["created_by", "updated_by"]

    task_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True, comment="任务ID")
    task_status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING", index=True, comment="任务状态")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="任务进度(0-100)")

    algorithm: Mapped[str] = mapped_column(String(64), nullable=False, comment="算法名")
    file_id: Mapped[str] = mapped_column(String(512), nullable=False, comment="输入文件file_id（相对backend根路径）")
    baseline_file_id: Mapped[str | None] = mapped_column(
        String(512), nullable=True, default=None, comment="基线文件file_id（可选）"
    )

    params_json: Mapped[str | None] = mapped_column(Text, nullable=True, default=None, comment="任务参数(JSON字符串)")
    result_file_id: Mapped[str | None] = mapped_column(
        String(512), nullable=True, default=None, comment="result.json 的 file_id（任务成功后填充）"
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True, default=None, comment="错误信息（任务失败时填充）")

    started_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None, comment="开始时间")
    ended_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None, comment="结束时间")


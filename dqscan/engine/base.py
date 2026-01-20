"""
dqscan 引擎层的“算法接口定义”。

这里不依赖 FastAPI，也不依赖后端工程，目标是让算法可以被：
- 列出（供 UI 展示）: 读取 `AlgorithmSpec`
- 执行（供任务系统调用）: 调用 `Algorithm.run(...)`

Algorithm.run 的约定输入输出：
- input_path: 输入文件路径（当前主要是 CSV/TXT）
- output_dir: 输出目录（算法在里面写 result.json / reports/*）
- params: 算法参数（dict），由前端透传
- emit: 回调函数，用于上报运行事件（log/progress/done/error）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol


EmitEvent = Callable[[dict[str, Any]], None]


@dataclass(frozen=True)
class AlgorithmSpec:
    name: str
    label: str
    description: str
    params_schema: dict[str, Any]


class Algorithm(Protocol):
    spec: AlgorithmSpec

    def run(
        self,
        *,
        input_path: str,
        output_dir: str,
        params: dict[str, Any] | None = None,
        emit: EmitEvent | None = None,
    ) -> dict[str, Any]: ...

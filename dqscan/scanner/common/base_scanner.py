# -*- coding: utf-8 -*-

"""
扫描器基类（Scanner Base）。

扫描器（scanner）的职责：
- 接收某种“数据形态”（这里主要是 pandas.DataFrame / numpy.ndarray）
- 执行检测逻辑并返回统一结构的 dict

统一结构的目的：
- 前端展示更稳定（has_issues/total_issues/issue_percentage 等字段一致）
- 报告生成器可以抽象处理（不需要理解每个模块的细节）
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseScanner(ABC):
    """所有 scanner 的基类。"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def scan(self, data: Any, **kwargs) -> dict[str, Any]:
        raise NotImplementedError

    def _error_result(self, message: str) -> dict[str, Any]:
        """标准化错误返回（用于依赖缺失/输入不合法等情况）。"""
        return {"error": message, "has_issues": False, "total_issues": 0, "issue_percentage": 0.0}

    def validate_data(self, data: Any, expected_type: type) -> None:
        """输入类型校验（失败直接抛 TypeError）。"""
        if not isinstance(data, expected_type):
            raise TypeError(f"期望数据类型为 {expected_type}，实际为 {type(data)}")

    def check_empty(self, data: Any) -> bool:
        """尽量兼容地判断数据是否为空（DataFrame/list/numpy 等）。"""
        try:
            import pandas as pd  # type: ignore

            if isinstance(data, pd.DataFrame):
                return data.empty
        except Exception:
            pass
        try:
            import numpy as np  # type: ignore

            if isinstance(data, (list, tuple, np.ndarray)):
                return len(data) == 0
        except Exception:
            if isinstance(data, (list, tuple)):
                return len(data) == 0
        return data is None

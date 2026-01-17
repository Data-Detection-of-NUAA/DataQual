# -*- coding: utf-8 -*-

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseScanner(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def scan(self, data: Any, **kwargs) -> dict[str, Any]:
        raise NotImplementedError

    def _error_result(self, message: str) -> dict[str, Any]:
        return {"error": message, "has_issues": False, "total_issues": 0, "issue_percentage": 0.0}

    def validate_data(self, data: Any, expected_type: type) -> None:
        if not isinstance(data, expected_type):
            raise TypeError(f"期望数据类型为 {expected_type}，实际为 {type(data)}")

    def check_empty(self, data: Any) -> bool:
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


# -*- coding: utf-8 -*-

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseScorer(ABC):
    @abstractmethod
    def calculate_score(self, results: dict[str, Any]) -> float:
        raise NotImplementedError

    @abstractmethod
    def calculate_total_score(self, all_results: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_scoring_explanation(self) -> dict[str, Any]:
        raise NotImplementedError

    def get_grade(self, score: float) -> str:
        if score >= 90:
            return "S"
        if score >= 80:
            return "A"
        if score >= 70:
            return "B"
        if score >= 60:
            return "C"
        return "D"


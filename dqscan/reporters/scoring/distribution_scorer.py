# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any

from .base_scorer import BaseScorer


class DistributionScorer(BaseScorer):
    P_VALUE_THRESHOLDS = [
        (0.05, 100.0, "不显著"),
        (0.01, 80.0, "弱显著"),
        (0.001, 60.0, "显著"),
        (0.0, 40.0, "高度显著"),
    ]

    def calculate_score(self, results: dict[str, Any]) -> float:
        p_value = self._extract_p_value(results)
        return self._p_value_to_score(p_value)

    def calculate_total_score(self, all_results: dict[str, Any]) -> dict[str, Any]:
        data_type_scores: dict[str, Any] = {}
        total = 0.0
        count = 0
        for dt, dt_results in all_results.items():
            if not isinstance(dt_results, dict):
                continue
            p_value = self._extract_p_value(dt_results)
            score = self._p_value_to_score(p_value)
            significance = self._get_significance(p_value)
            data_type_scores[dt] = {
                "score": score,
                "p_value": p_value,
                "significance": significance,
                "drift_detected": bool(dt_results.get("drift_detected", False)),
            }
            total += score
            count += 1
        final_score = total / count if count > 0 else 100.0
        return {
            "total_score": round(final_score, 1),
            "grade": self.get_grade(final_score),
            "scoring_method": "p值统计显著性",
            "data_type_scores": data_type_scores,
        }

    def get_scoring_explanation(self) -> dict[str, Any]:
        return {"method": "p值统计显著性", "description": "基于统计检验p值评估分布漂移程度"}

    def _extract_p_value(self, results: dict[str, Any]) -> float:
        p_value = results.get("p_value")
        if p_value is None and isinstance(results.get("mmd_result"), dict):
            p_value = results["mmd_result"].get("p_value")
        return float(p_value) if p_value is not None else 1.0

    def _p_value_to_score(self, p_value: float) -> float:
        for threshold, score, _ in self.P_VALUE_THRESHOLDS:
            if p_value >= threshold:
                return float(score)
        return 40.0

    def _get_significance(self, p_value: float) -> str:
        for threshold, _, level in self.P_VALUE_THRESHOLDS:
            if p_value >= threshold:
                return level
        return "高度显著"


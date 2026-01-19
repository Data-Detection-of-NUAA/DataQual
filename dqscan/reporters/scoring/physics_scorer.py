# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any

from .base_scorer import BaseScorer


class PhysicsScorer(BaseScorer):
    VIOLATION_RATE_THRESHOLDS = [
        (0.01, 100.0, "高保真"),
        (0.05, 80.0, "中等保真"),
        (0.15, 60.0, "低保真"),
        (1.0, 40.0, "极低保真"),
    ]

    def calculate_score(self, results: dict[str, Any]) -> float:
        violation_rate = float(results.get("violation_rate", 0) or 0)
        return self._violation_rate_to_score(violation_rate)

    def calculate_total_score(self, all_results: dict[str, Any]) -> dict[str, Any]:
        data_type_scores: dict[str, Any] = {}
        total = 0.0
        count = 0
        for dt, dt_results in all_results.items():
            if not isinstance(dt_results, dict):
                continue
            violation_rate = float(dt_results.get("violation_rate", 0) or 0)
            causality_score = float(dt_results.get("causality_score", 1.0) or 0)
            score = self._violation_rate_to_score(violation_rate)
            fidelity_level = self._get_fidelity_level(violation_rate)
            data_type_scores[dt] = {
                "score": score,
                "violation_rate": round(violation_rate, 4),
                "causality_score": round(causality_score, 4),
                "fidelity_level": fidelity_level,
                "total_issues": int(dt_results.get("total_issues", 0) or 0),
                "algorithm": dt_results.get("algorithm", "Unknown"),
            }
            total += score
            count += 1
        final_score = total / count if count > 0 else 100.0
        return {
            "total_score": round(final_score, 1),
            "grade": self.get_grade(final_score),
            "scoring_method": "约束违规率评估",
            "data_type_scores": data_type_scores,
        }

    def get_scoring_explanation(self) -> dict[str, Any]:
        return {"method": "约束违规率评估", "description": "基于物理约束违规率评估数据保真度"}

    def _violation_rate_to_score(self, violation_rate: float) -> float:
        for threshold, score, _ in self.VIOLATION_RATE_THRESHOLDS:
            if violation_rate <= threshold:
                return float(score)
        return 40.0

    def _get_fidelity_level(self, violation_rate: float) -> str:
        for threshold, _, level in self.VIOLATION_RATE_THRESHOLDS:
            if violation_rate <= threshold:
                return level
        return "极低保真"


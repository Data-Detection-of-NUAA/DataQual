# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any

from .base_scorer import BaseScorer


class AdversarialScorer(BaseScorer):
    ATTACK_RATE_THRESHOLDS = [
        (0.10, 100.0, "高鲁棒"),
        (0.30, 80.0, "中等鲁棒"),
        (0.50, 60.0, "低鲁棒"),
        (1.0, 40.0, "极低鲁棒"),
    ]

    def calculate_score(self, results: dict[str, Any]) -> float:
        attack_success_rate = float(results.get("attack_success_rate", 0) or 0)
        return self._attack_rate_to_score(attack_success_rate)

    def calculate_total_score(self, all_results: dict[str, Any]) -> dict[str, Any]:
        data_type_scores: dict[str, Any] = {}
        total = 0.0
        count = 0
        for dt, dt_results in all_results.items():
            if not isinstance(dt_results, dict):
                continue
            attack_success_rate = float(dt_results.get("attack_success_rate", 0) or 0)
            robustness_score = float(dt_results.get("robustness_score", 1 - attack_success_rate) or 0)
            score = self._attack_rate_to_score(attack_success_rate)
            robustness_level = self._get_robustness_level(attack_success_rate)
            data_type_scores[dt] = {
                "score": score,
                "attack_success_rate": round(attack_success_rate, 4),
                "robustness_score": round(robustness_score, 4),
                "robustness_level": robustness_level,
                "total_issues": int(dt_results.get("total_issues", 0) or 0),
                "algorithm": dt_results.get("algorithm", "Unknown"),
            }
            total += score
            count += 1
        final_score = total / count if count > 0 else 100.0
        return {
            "total_score": round(final_score, 1),
            "grade": self.get_grade(final_score),
            "scoring_method": "攻击成功率评估",
            "data_type_scores": data_type_scores,
        }

    def get_scoring_explanation(self) -> dict[str, Any]:
        return {"method": "攻击成功率评估", "description": "基于对抗攻击成功率评估鲁棒性"}

    def _attack_rate_to_score(self, attack_success_rate: float) -> float:
        for threshold, score, _ in self.ATTACK_RATE_THRESHOLDS:
            if attack_success_rate <= threshold:
                return float(score)
        return 40.0

    def _get_robustness_level(self, attack_success_rate: float) -> str:
        for threshold, _, level in self.ATTACK_RATE_THRESHOLDS:
            if attack_success_rate <= threshold:
                return level
        return "极低鲁棒"


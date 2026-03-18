# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any

from .base_scorer import BaseScorer


class DirtyDataScorer(BaseScorer):
    DEDUCTION_RULES = {
        "anomaly": [(0.20, 60), (0.10, 40), (0.05, 20), (0.0, 0)],
        "missing": [(0.15, 40), (0.05, 25), (0.01, 10), (0.0, 0)],
        "duplicate": [(0.30, 30), (0.15, 20), (0.05, 10), (0.0, 0)],
        # 疑似错标（Label Mismatch）属于“标注质量”问题：对训练/评估影响更大，因此扣分略重
        "label_mismatch": [(0.10, 70), (0.05, 40), (0.02, 20), (0.0, 0)],
    }

    def calculate_score(self, results: dict[str, Any]) -> float:
        anomaly_rate = float(results.get("anomaly_rate", 0) or 0)
        missing_rate = float(results.get("missing_rate", 0) or 0)
        duplicate_rate = float(results.get("duplicate_rate", 0) or 0)
        label_mismatch_rate = float(results.get("label_mismatch_rate", 0) or 0)
        deductions = self._calculate_deductions(anomaly_rate, missing_rate, duplicate_rate, label_mismatch_rate)
        return max(0.0, 100.0 - sum(deductions.values()))

    def calculate_total_score(self, all_results: dict[str, Any]) -> dict[str, Any]:
        data_type_scores: dict[str, Any] = {}
        total = 0.0
        count = 0

        for dt, dt_results in all_results.items():
            if not isinstance(dt_results, dict):
                continue
            anomaly_rate = float(dt_results.get("anomaly_rate", 0) or 0)
            missing_rate = float(dt_results.get("missing_rate", 0) or 0)
            duplicate_rate = float(dt_results.get("duplicate_rate", 0) or 0)
            label_mismatch_rate = float(dt_results.get("label_mismatch_rate", 0) or 0)
            deductions = self._calculate_deductions(anomaly_rate, missing_rate, duplicate_rate, label_mismatch_rate)
            score = max(0.0, 100.0 - sum(deductions.values()))
            data_type_scores[dt] = {
                "score": score,
                "anomaly_rate": round(anomaly_rate, 4),
                "missing_rate": round(missing_rate, 4),
                "duplicate_rate": round(duplicate_rate, 4),
                "label_mismatch_rate": round(label_mismatch_rate, 4),
                "deductions": deductions,
            }
            total += score
            count += 1

        final_score = total / count if count > 0 else 100.0
        return {
            "total_score": round(final_score, 1),
            "grade": self.get_grade(final_score),
            "scoring_method": "扣分制(满分100)",
            "data_type_scores": data_type_scores,
        }

    def get_scoring_explanation(self) -> dict[str, Any]:
        return {
            "method": "扣分制(满分100)",
            "description": "根据异常率、缺失率、重复率、疑似错标率分段扣分",
        }

    def _calculate_deductions(
        self,
        anomaly_rate: float,
        missing_rate: float,
        duplicate_rate: float,
        label_mismatch_rate: float,
    ) -> dict[str, int]:
        return {
            "anomaly": self._get_deduction("anomaly", anomaly_rate),
            "missing": self._get_deduction("missing", missing_rate),
            "duplicate": self._get_deduction("duplicate", duplicate_rate),
            "label_mismatch": self._get_deduction("label_mismatch", label_mismatch_rate),
        }

    def _get_deduction(self, rate_type: str, rate: float) -> int:
        rules = self.DEDUCTION_RULES.get(rate_type, [])
        for threshold, deduction in rules:
            if rate > threshold:
                return int(deduction)
        return 0

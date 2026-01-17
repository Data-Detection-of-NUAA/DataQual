# -*- coding: utf-8 -*-

from __future__ import annotations

import os
from typing import Any

from .base_reporter import BaseReporter
from .scoring import AdversarialScorer, DirtyDataScorer, DistributionScorer, PhysicsScorer


class DetectionReportGenerator(BaseReporter):
    SCORERS = {
        "distribution": DistributionScorer,
        "dirty_data": DirtyDataScorer,
        "adversarial": AdversarialScorer,
        "physics": PhysicsScorer,
    }

    def _get_scorer(self, module_type: str):
        scorer_class = self.SCORERS.get(module_type)
        return scorer_class() if scorer_class else None

    def _calculate_score(self, results: dict[str, Any], module_type: str) -> dict[str, Any]:
        scorer = self._get_scorer(module_type)
        if scorer:
            return scorer.calculate_total_score(results)
        return {"total_score": 0, "grade": "N/A", "data_type_scores": {}}

    def generate_json_report(self, results: dict[str, Any], report_name: str) -> str:
        module_type = self.extract_module_type(report_name)
        scoring = self._calculate_score(results, module_type)

        report = {
            "metadata": {"generated_at": self.now_iso(), "report_version": "v4.0", "module_type": module_type},
            "scoring": scoring,
            "results": self.convert_numpy_types(self._compact_results(results)),
        }
        report_path = os.path.join(self.report_dir, f"{report_name}.json")
        self.save_json(report, report_path)
        return report_path

    def generate_summary_report(self, results: dict[str, Any], report_name: str) -> str:
        module_type = self.extract_module_type(report_name)
        scoring = self._calculate_score(results, module_type)

        summary = {
            "metadata": {"generated_at": self.now_iso(), "module_type": module_type},
            "score": scoring.get("total_score", 0),
            "grade": scoring.get("grade", "N/A"),
            "data_types": {},
        }

        for dt, dt_results in results.items():
            if not isinstance(dt_results, dict):
                continue
            dt_summary: dict[str, Any] = {
                "algorithm": dt_results.get("algorithm", "Unknown"),
                "has_issues": bool(dt_results.get("has_issues", False)),
                "total_issues": int(dt_results.get("total_issues", 0) or 0),
                "issue_percentage": round(float(dt_results.get("issue_percentage", 0) or 0), 4),
            }
            if module_type == "distribution":
                dt_summary["p_value"] = float(dt_results.get("p_value", 1.0) or 1.0)
                dt_summary["drift_detected"] = bool(dt_results.get("drift_detected", False))
            elif module_type == "dirty_data":
                dt_summary["anomaly_rate"] = round(float(dt_results.get("anomaly_rate", 0) or 0), 4)
                dt_summary["missing_rate"] = round(float(dt_results.get("missing_rate", 0) or 0), 4)
                dt_summary["duplicate_rate"] = round(float(dt_results.get("duplicate_rate", 0) or 0), 4)
            elif module_type == "adversarial":
                dt_summary["attack_success_rate"] = round(float(dt_results.get("attack_success_rate", 0) or 0), 4)
                dt_summary["robustness_score"] = round(float(dt_results.get("robustness_score", 1.0) or 0), 4)
            elif module_type == "physics":
                dt_summary["violation_rate"] = round(float(dt_results.get("violation_rate", 0) or 0), 4)
                dt_summary["causality_score"] = round(float(dt_results.get("causality_score", 1.0) or 0), 4)

            dt_score = scoring.get("data_type_scores", {}).get(dt)
            if isinstance(dt_score, dict) and "score" in dt_score:
                dt_summary["score"] = dt_score["score"]

            summary["data_types"][dt] = dt_summary

        summary_path = os.path.join(self.report_dir, f"{report_name}_summary.json")
        self.save_json(summary, summary_path)
        return summary_path

    def generate_full_report(self, results: dict[str, Any], report_name: str, generate_docx: bool = True) -> dict[str, str]:
        json_path = self.generate_json_report(results, report_name)
        summary_path = self.generate_summary_report(results, report_name)
        paths = {"json_report": json_path, "summary_report": summary_path}

        if generate_docx:
            try:
                from .docx_report_generator import DocxReportGenerator

                module_type = self.extract_module_type(report_name)
                gen = DocxReportGenerator(output_dir=self.output_dir)
                docx_path = gen.generate_report(results, report_name=report_name, module_type=module_type)
                paths["docx_report"] = docx_path
            except Exception as e:
                paths["docx_report_error"] = str(e)

        return paths

    def _compact_results(self, results: dict[str, Any], max_items: int = 20) -> dict[str, Any]:
        compact: dict[str, Any] = {}
        for dt, dt_results in results.items():
            if not isinstance(dt_results, dict):
                compact[dt] = dt_results
                continue
            compact[dt] = self._compact_dict(dt_results, max_items)
        return compact

    def _compact_dict(self, d: dict[str, Any], max_items: int) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k, v in d.items():
            if isinstance(v, list):
                out[k] = v[:max_items]
                if len(v) > max_items:
                    out[f"{k}_total"] = len(v)
            elif isinstance(v, dict):
                out[k] = self._compact_dict(v, max_items)
            else:
                out[k] = v
        return out


# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Optional

from ..common.base_scanner import BaseScanner

try:
    import numpy as np  # type: ignore
    import pandas as pd  # type: ignore

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from pyod.models.ecod import ECOD  # type: ignore

    PYOD_AVAILABLE = True
except ImportError:
    PYOD_AVAILABLE = False


class TabularDirtyScanner(BaseScanner):
    def __init__(self, contamination: float = 0.1):
        super().__init__(name="TabularDirtyScanner")
        self.contamination = contamination

    def scan(
        self,
        data: Any,
        numerical_columns: Optional[list[str]] = None,
        categorical_columns: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        if not PANDAS_AVAILABLE:
            return self._error_result("pandas未安装，请先安装 pandas/numpy 依赖")

        assert PANDAS_AVAILABLE
        self.validate_data(data, pd.DataFrame)

        if self.check_empty(data):
            return {"error": "数据为空", "total_samples": 0, "has_issues": False, "total_issues": 0}

        if numerical_columns is None:
            numerical_columns = data.select_dtypes(include=[np.number]).columns.tolist()
        if categorical_columns is None:
            categorical_columns = data.select_dtypes(exclude=[np.number]).columns.tolist()

        results: dict[str, Any] = {
            "algorithm": "ECOD + 3σ Rule" if PYOD_AVAILABLE else "3σ Rule (Fallback - pyod未安装)",
            "total_samples": len(data),
            "total_features": len(data.columns),
            "numerical_features": len(numerical_columns),
            "categorical_features": len(categorical_columns),
        }

        anomaly_results = self._detect_anomalies(data, numerical_columns)
        results["anomaly_detection"] = anomaly_results

        missing_results = self._detect_missing(data)
        results["missing_values"] = missing_results

        duplicate_results = self._detect_duplicates(data)
        results["duplicates"] = duplicate_results

        range_results = self._detect_range_violations(data, numerical_columns)
        results["range_violations"] = range_results

        results["anomaly_rate"] = float(anomaly_results.get("anomaly_rate", 0.0) or 0.0)
        results["missing_rate"] = float(missing_results.get("missing_rate", 0.0) or 0.0)
        results["duplicate_rate"] = float(duplicate_results.get("duplicate_rate", 0.0) or 0.0)

        results["has_issues"] = bool(
            results["anomaly_rate"] > 0 or results["missing_rate"] > 0 or results["duplicate_rate"] > 0
        )

        detailed_issues: list[dict[str, Any]] = []
        total_issues = 0

        anomaly_indices = anomaly_results.get("anomaly_indices") or []
        total_issues += len(anomaly_indices)
        for idx in anomaly_indices[:50]:
            detailed_issues.append(
                {
                    "data_id": f"row_{idx}",
                    "issue_type": "异常值",
                    "severity": "moderate" if results["anomaly_rate"] > 0.1 else "light",
                    "details": {"affected_fields": numerical_columns},
                }
            )

        missing_by_column = (missing_results.get("missing_by_column") or {}) if isinstance(missing_results, dict) else {}
        for col_name, col_info in list(missing_by_column.items())[:20]:
            count = int(col_info.get("count", 0) or 0)
            rate = float(col_info.get("rate", 0.0) or 0.0)
            total_issues += count
            detailed_issues.append(
                {
                    "data_id": f"column_{col_name}",
                    "issue_type": "缺失值",
                    "severity": "severe" if rate > 0.15 else "light",
                    "details": {"missing_count": count},
                }
            )

        dup_indices = duplicate_results.get("duplicate_indices") or []
        total_issues += len(dup_indices)
        for idx in dup_indices[:30]:
            detailed_issues.append(
                {"data_id": f"row_{idx}", "issue_type": "重复数据", "severity": "light", "details": {}}
            )

        results["total_issues"] = int(total_issues)
        results["issue_percentage"] = float(total_issues / len(data)) if len(data) > 0 else 0.0
        results["detailed_issues"] = detailed_issues
        return results

    def _detect_anomalies(self, data: "pd.DataFrame", numerical_columns: list[str]) -> dict[str, Any]:
        if len(numerical_columns) == 0:
            return {"method": "ECOD", "anomaly_count": 0, "anomaly_rate": 0.0}

        X = data[numerical_columns].copy()
        X_clean = X.fillna(X.mean(numeric_only=True))

        if (X_clean.std(numeric_only=True) == 0).all():
            return {"method": "ECOD", "anomaly_count": 0, "anomaly_rate": 0.0}

        if PYOD_AVAILABLE:
            try:
                detector = ECOD(contamination=self.contamination)
                detector.fit(X_clean)
                predictions = detector.predict(X_clean)
                anomaly_indices = np.where(predictions == 1)[0].tolist()
                return {
                    "method": "ECOD",
                    "anomaly_count": int(np.sum(predictions)),
                    "anomaly_rate": float(np.mean(predictions)),
                    "anomaly_indices": anomaly_indices[:100],
                    "threshold": float(getattr(detector, "threshold_", 0.0)),
                }
            except Exception as e:
                return {"method": "ECOD", "error": str(e), "anomaly_count": 0, "anomaly_rate": 0.0}

        # fallback: z-score 3σ
        try:
            z = (X_clean - X_clean.mean()) / X_clean.std().replace(0, np.nan)
            mask = (np.abs(z) > 3).any(axis=1)
            anomaly_indices = np.where(mask.fillna(False).values)[0].tolist()
            anomaly_rate = len(anomaly_indices) / len(X_clean) if len(X_clean) else 0.0
            return {
                "method": "3σ Rule",
                "anomaly_count": int(len(anomaly_indices)),
                "anomaly_rate": float(anomaly_rate),
                "anomaly_indices": anomaly_indices[:100],
            }
        except Exception as e:
            return {"method": "3σ Rule", "error": str(e), "anomaly_count": 0, "anomaly_rate": 0.0}

    def _detect_missing(self, data: "pd.DataFrame") -> dict[str, Any]:
        missing_counts = data.isnull().sum()
        total_missing = int(missing_counts.sum())
        missing_by_column: dict[str, dict[str, Any]] = {}
        for col, count in missing_counts.items():
            if int(count) > 0:
                missing_by_column[str(col)] = {"count": int(count), "rate": float(count / len(data))}
        return {
            "total_missing": total_missing,
            "missing_rate": float(total_missing / (len(data) * max(len(data.columns), 1))),
            "columns_with_missing": len(missing_by_column),
            "missing_by_column": missing_by_column,
        }

    def _detect_duplicates(self, data: "pd.DataFrame") -> dict[str, Any]:
        exact_duplicates = data.duplicated(keep=False)
        duplicate_count = int(exact_duplicates.sum())
        duplicate_indices = np.where(exact_duplicates)[0].tolist()
        return {
            "duplicate_count": duplicate_count,
            "duplicate_rate": float(duplicate_count / len(data)) if len(data) else 0.0,
            "duplicate_indices": duplicate_indices[:100],
        }

    def _detect_range_violations(self, data: "pd.DataFrame", numerical_columns: list[str]) -> dict[str, Any]:
        violations: dict[str, Any] = {}
        total_violations = 0
        for col in numerical_columns:
            values = data[col].dropna()
            if len(values) == 0:
                continue
            mean, std = values.mean(), values.std()
            if std == 0:
                continue
            lower_bound = mean - 3 * std
            upper_bound = mean + 3 * std
            violating = data[(data[col] < lower_bound) | (data[col] > upper_bound)].index.tolist()
            if len(violating) > 0:
                violations[str(col)] = {"count": len(violating), "bounds": [float(lower_bound), float(upper_bound)]}
                total_violations += len(violating)
        return {"total_violations": int(total_violations), "violations_by_column": violations}


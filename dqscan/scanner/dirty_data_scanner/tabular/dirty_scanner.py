# -*- coding: utf-8 -*-

"""
脏数据扫描（Tabular）。

目标：快速给出“这份表格数据是否存在明显质量问题”的可解释信号。

当前实现包含四类检测：
1) 异常值：优先 pyod.ECOD；否则用 3σ 规则降级
2) 缺失值：统计每列缺失量
3) 重复行：完全重复的行
4) 范围违规：按每列均值±3σ 的简单启发式找可疑点

输出结构遵循 BaseScanner 的统一约定，便于前端展示与报告生成。
"""

from __future__ import annotations

from typing import Any, Optional

from ...common.base_scanner import BaseScanner

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
    """表格脏数据扫描器（支持依赖缺失时降级）。"""

    def __init__(self, contamination: float = 0.1):
        super().__init__(name="TabularDirtyScanner")
        self.contamination = contamination

    def scan(
        self,
        data: Any,
        numerical_columns: Optional[list[str]] = None,
        categorical_columns: Optional[list[str]] = None,
        *,
        enabled_checks: Optional[list[str]] = None,
        missing_threshold: Optional[float] = None,
        duplicate_threshold: Optional[float] = None,
        duplicate_key_columns: Optional[list[str]] = None,
        range_method: str = "sigma",
        range_sigma: float = 3.0,
        range_iqr_factor: float = 1.5,
        range_only_columns: Optional[list[str]] = None,
        max_examples: int = 50,
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

        max_examples = int(max(10, min(int(max_examples or 50), 500)))
        enabled_checks = [str(x) for x in enabled_checks] if enabled_checks else []
        enable_all = not enabled_checks
        check_anomaly = enable_all or "anomaly" in enabled_checks
        check_missing = enable_all or "missing" in enabled_checks
        check_duplicate = enable_all or "duplicate" in enabled_checks
        check_range = enable_all or "range" in enabled_checks

        results: dict[str, Any] = {
            "algorithm": "ECOD + 3σ规则" if PYOD_AVAILABLE else "3σ规则（降级：未安装 pyod）",
            "total_samples": len(data),
            "total_features": len(data.columns),
            "numerical_features": len(numerical_columns),
            "categorical_features": len(categorical_columns),
        }

        # 1) 异常值（outliers）
        anomaly_results = self._detect_anomalies(data, numerical_columns) if check_anomaly else {"anomaly_rate": 0.0}
        results["anomaly_detection"] = anomaly_results

        # 2) 缺失值（missing values）
        missing_results = (
            self._detect_missing(data, threshold=missing_threshold) if check_missing else {"missing_rate": 0.0}
        )
        results["missing_values"] = missing_results

        # 3) 重复数据（duplicate rows）
        duplicate_results = (
            self._detect_duplicates(data, key_columns=duplicate_key_columns)
            if check_duplicate
            else {"duplicate_rate": 0.0}
        )
        results["duplicates"] = duplicate_results

        # 4) 简单范围违规（每列均值±3σ）
        range_results = (
            self._detect_range_violations(
                data,
                numerical_columns,
                method=range_method,
                sigma=range_sigma,
                iqr_factor=range_iqr_factor,
                only_columns=range_only_columns,
            )
            if check_range
            else {"total_violations": 0, "violations_by_column": {}}
        )
        results["range_violations"] = range_results

        results["anomaly_rate"] = float(anomaly_results.get("anomaly_rate", 0.0) or 0.0)
        results["missing_rate"] = float(missing_results.get("missing_rate", 0.0) or 0.0)
        results["duplicate_rate"] = float(duplicate_results.get("duplicate_rate", 0.0) or 0.0)

        missing_flag = bool(missing_results.get("has_issues", results["missing_rate"] > 0))
        if duplicate_threshold is not None:
            try:
                dup_thresh = float(duplicate_threshold)
            except Exception:
                dup_thresh = None
        else:
            dup_thresh = None
        duplicate_flag = bool(duplicate_results.get("has_issues", results["duplicate_rate"] > 0))
        if dup_thresh is not None:
            duplicate_flag = results["duplicate_rate"] >= dup_thresh

        has_issues = bool(
            results["anomaly_rate"] > 0
            or missing_flag
            or duplicate_flag
            or int(range_results.get("total_violations", 0) or 0) > 0
        )
        results["has_issues"] = has_issues

        detailed_issues: list[dict[str, Any]] = []
        remaining_examples = max_examples
        total_issues = 0

        if check_anomaly and remaining_examples > 0:
            anomaly_indices = anomaly_results.get("anomaly_indices") or []
            total_issues += int(anomaly_results.get("anomaly_count", len(anomaly_indices)) or 0)
            take = min(len(anomaly_indices), remaining_examples)
            for idx in anomaly_indices[:take]:
                row_preview = self._row_preview(data, int(idx))
                try:
                    row_index = data.index[int(idx)]
                except Exception:
                    row_index = int(idx)
                detailed_issues.append(
                    {
                        "data_id": f"row_{idx}",
                        "issue_type": "异常值",
                        "severity": "moderate" if results["anomaly_rate"] > 0.1 else "light",
                        "details": {"affected_fields": numerical_columns, "row_index": row_index, "row_preview": row_preview},
                    }
                )
            remaining_examples -= take

        if check_missing and remaining_examples > 0:
            missing_by_column = (
                (missing_results.get("missing_by_column") or {}) if isinstance(missing_results, dict) else {}
            )
            for col_name, col_info in list(missing_by_column.items())[:remaining_examples]:
                count = int(col_info.get("count", 0) or 0)
                rate = float(col_info.get("rate", 0.0) or 0.0)
                total_issues += count
                try:
                    sample_missing_row_ids = data.index[data[str(col_name)].isna()].tolist()[:5]
                except Exception:
                    sample_missing_row_ids = []
                detailed_issues.append(
                    {
                        "data_id": f"column_{col_name}",
                        "issue_type": "缺失值",
                        "severity": "severe" if rate > 0.15 else "light",
                        "details": {
                            "missing_count": count,
                            "missing_rate": round(rate, 6),
                            "row_preview": {"column": str(col_name), "sample_missing_row_ids": sample_missing_row_ids},
                        },
                    }
                )
                remaining_examples -= 1
                if remaining_examples <= 0:
                    break

        if check_duplicate and remaining_examples > 0:
            dup_indices = duplicate_results.get("duplicate_indices") or []
            total_issues += len(dup_indices)
            for idx in dup_indices[:remaining_examples]:
                row_preview = self._row_preview(data, int(idx))
                try:
                    row_index = data.index[int(idx)]
                except Exception:
                    row_index = int(idx)
                detailed_issues.append(
                    {
                        "data_id": f"row_{idx}",
                        "issue_type": "重复数据",
                        "severity": "light",
                        "details": {
                            "row_index": row_index,
                            "key_columns": duplicate_results.get("key_columns") or [],
                            "row_preview": row_preview,
                        },
                    }
                )
                remaining_examples -= 1
                if remaining_examples <= 0:
                    break

        results["total_issues"] = int(total_issues)
        results["issue_percentage"] = float(total_issues / len(data)) if len(data) > 0 else 0.0
        results["detailed_issues"] = detailed_issues
        return results

    def _row_preview(self, data: "pd.DataFrame", i: int, *, max_fields: int = 30) -> dict[str, Any]:
        if not PANDAS_AVAILABLE:
            return {}
        try:
            row = data.iloc[int(i)]
        except Exception:
            return {}

        cols = list(data.columns)[: int(max_fields)]
        preview: dict[str, Any] = {}
        for c in cols:
            try:
                v = row.get(c)
            except Exception:
                v = None
            try:
                if pd.isna(v):
                    v = None
            except Exception:
                pass
            if isinstance(v, str) and len(v) > 200:
                v = v[:200] + "…"
            preview[str(c)] = v
        return preview

    def _detect_anomalies(self, data: "pd.DataFrame", numerical_columns: list[str]) -> dict[str, Any]:
        """
        异常值检测。

        - 有 pyod 时：ECOD（无监督异常检测）
        - 无 pyod 时：对每行计算 z-score，任一列 |z|>3 认为该行异常（粗粒度但可用）
        """
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

    def _detect_missing(self, data: "pd.DataFrame", *, threshold: Optional[float] = None) -> dict[str, Any]:
        missing_counts = data.isnull().sum()
        total_missing = int(missing_counts.sum())
        missing_by_column: dict[str, dict[str, Any]] = {}
        over_threshold: list[str] = []
        for col, count in missing_counts.items():
            if int(count) > 0:
                rate = float(count / len(data))
                missing_by_column[str(col)] = {"count": int(count), "rate": rate}
                if threshold is not None and rate >= float(threshold):
                    over_threshold.append(str(col))
        return {
            "total_missing": total_missing,
            "missing_rate": float(total_missing / (len(data) * max(len(data.columns), 1))),
            "columns_with_missing": len(missing_by_column),
            "missing_by_column": missing_by_column,
            "missing_threshold": float(threshold) if threshold is not None else None,
            "columns_over_threshold": over_threshold,
            "has_issues": bool(over_threshold) if threshold is not None else total_missing > 0,
        }

    def _detect_duplicates(self, data: "pd.DataFrame", *, key_columns: Optional[list[str]] = None) -> dict[str, Any]:
        subset = None
        if key_columns:
            available = [c for c in key_columns if c in data.columns]
            if available:
                subset = available
        exact_duplicates = data.duplicated(subset=subset, keep=False)
        duplicate_count = int(exact_duplicates.sum())
        duplicate_indices = np.where(exact_duplicates)[0].tolist()
        return {
            "duplicate_count": duplicate_count,
            "duplicate_rate": float(duplicate_count / len(data)) if len(data) else 0.0,
            "duplicate_indices": duplicate_indices[:100],
            "key_columns": subset or [],
            "has_issues": duplicate_count > 0,
        }

    def _detect_range_violations(
        self,
        data: "pd.DataFrame",
        numerical_columns: list[str],
        *,
        method: str = "sigma",
        sigma: float = 3.0,
        iqr_factor: float = 1.5,
        only_columns: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        violations: dict[str, Any] = {}
        total_violations = 0
        target_columns = numerical_columns
        if only_columns:
            only_set = {c for c in only_columns if c in data.columns}
            target_columns = [c for c in numerical_columns if c in only_set]
        for col in target_columns:
            values = data[col].dropna()
            if len(values) == 0:
                continue
            method_lower = method.lower().strip() if method else "sigma"
            if method_lower == "iqr":
                q1 = values.quantile(0.25)
                q3 = values.quantile(0.75)
                iqr = q3 - q1
                if iqr == 0:
                    continue
                lower_bound = q1 - float(iqr_factor) * iqr
                upper_bound = q3 + float(iqr_factor) * iqr
            else:
                mean, std = values.mean(), values.std()
                if std == 0:
                    continue
                k = float(sigma or 3.0)
                lower_bound = mean - k * std
                upper_bound = mean + k * std
            violating = data[(data[col] < lower_bound) | (data[col] > upper_bound)].index.tolist()
            if len(violating) > 0:
                violations[str(col)] = {
                    "count": len(violating),
                    "bounds": [float(lower_bound), float(upper_bound)],
                }
                total_violations += len(violating)
        return {
            "total_violations": int(total_violations),
            "violations_by_column": violations,
            "method": method_lower,
            "sigma": float(sigma),
            "iqr_factor": float(iqr_factor),
        }

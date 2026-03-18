# -*- coding: utf-8 -*-

"""
数据驱动的物理保真度检测（Tabular）。

通过统计/机器学习方法自动发现"单列合法但组合异常"的数据问题，
无需用户显式配置规则。

三个互补的检测方法：
- regression_residual：回归残差法——高相关列对上用鲁棒回归检测异常残差
- isolation_forest：隔离森林——多维特征空间中的离群点检测
- correlation_consistency：相关性一致性——高相关列对间逐行偏离度检测

所有方法均为可选：依赖缺失时降级跳过，不影响其余方法执行。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from ..common.base_scanner import BaseScanner

try:
    import numpy as np  # type: ignore
    import pandas as pd  # type: ignore

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from sklearn.linear_model import HuberRegressor  # type: ignore
    from sklearn.ensemble import IsolationForest  # type: ignore

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)

_DEFAULT_METHODS = ["regression_residual", "isolation_forest", "correlation_consistency"]
_MAX_DETAILED_ISSUES = 50


class TabularPhysicsDataDrivenScanner(BaseScanner):
    """
    数据驱动的物理保真度检测（无需显式规则）。

    通过统计/机器学习方法自动发现"单列合法但组合异常"的数据问题。
    所有方法都是可选的：依赖缺失时降级跳过。
    """

    def __init__(
        self,
        *,
        methods: Optional[list[str]] = None,
        contamination: float = 0.05,
        max_features: int = 20,
        correlation_threshold: float = 0.7,
        max_samples: int = 10000,
        seed: int = 42,
    ):
        super().__init__(name="TabularPhysicsDataDrivenScanner")
        self.methods = methods if methods is not None else list(_DEFAULT_METHODS)
        self.contamination = contamination
        self.max_features = max_features
        self.correlation_threshold = correlation_threshold
        self.max_samples = max_samples
        self.seed = seed

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def scan(self, data: Any, numerical_columns: Optional[list[str]] = None) -> dict[str, Any]:
        """
        执行数据驱动检测。

        返回结构包含 algorithm / total_samples / methods_used / has_issues 等统一字段。
        """
        if not PANDAS_AVAILABLE:
            return self._error_result("pandas未安装，请先安装 pandas/numpy 依赖")

        if data is None or len(data) == 0:
            return self._error_result("数据为空")

        self.validate_data(data, pd.DataFrame)

        if numerical_columns is None:
            numerical_columns = data.select_dtypes(include=[np.number]).columns.tolist()

        if len(numerical_columns) == 0:
            return self._error_result("没有数值列可供检测")

        results: dict[str, Any] = {
            "algorithm": "Data-Driven Physics Validation",
            "total_samples": int(len(data)),
            "total_features": int(len(numerical_columns)),
        }

        methods_used: list[str] = []
        methods_skipped: dict[str, str] = {}
        method_results: dict[str, Any] = {}
        all_issues: list[dict[str, Any]] = []

        # 按用户配置的顺序依次执行各方法
        dispatch = {
            "regression_residual": self._regression_residual_check,
            "isolation_forest": self._isolation_forest_check,
            "correlation_consistency": self._correlation_consistency_check,
        }

        for method_name in self.methods:
            fn = dispatch.get(method_name)
            if fn is None:
                methods_skipped[method_name] = f"未知方法: {method_name}"
                continue

            # sklearn 依赖检查
            if method_name in {"regression_residual", "isolation_forest"} and not SKLEARN_AVAILABLE:
                methods_skipped[method_name] = "sklearn未安装，请先安装: pip install scikit-learn"
                continue

            try:
                mr = fn(data, numerical_columns)
                method_results[method_name] = mr
                methods_used.append(method_name)
                all_issues.extend(mr.get("issues", []))
            except Exception as e:
                logger.exception("数据驱动检测方法 %s 执行异常", method_name)
                methods_skipped[method_name] = f"执行异常: {e}"

        # 按 data_id 去重（同一行可能被多个方法检出）
        seen_ids: set[Any] = set()
        unique_issues: list[dict[str, Any]] = []
        for issue in all_issues:
            did = issue.get("data_id")
            if did not in seen_ids:
                seen_ids.add(did)
                unique_issues.append(issue)

        total_anomaly = len(seen_ids)
        total_samples = len(data)
        anomaly_rate = total_anomaly / max(total_samples, 1)

        results["methods_used"] = methods_used
        results["methods_skipped"] = methods_skipped
        results["has_issues"] = total_anomaly > 0
        results["total_issues"] = total_anomaly
        results["issue_percentage"] = float(anomaly_rate)
        results["anomaly_count"] = total_anomaly
        results["anomaly_rate"] = float(anomaly_rate)
        results["detailed_issues"] = unique_issues[:_MAX_DETAILED_ISSUES]
        results["method_results"] = method_results

        return results

    # ------------------------------------------------------------------
    # 方法 1: 回归残差法
    # ------------------------------------------------------------------

    def _regression_residual_check(self, data: "pd.DataFrame", numerical_columns: list[str]) -> dict[str, Any]:
        """高相关列对上用 HuberRegressor 拟合，通过残差 z-score 检测异常。"""
        result: dict[str, Any] = {
            "pairs_checked": 0,
            "high_correlation_pairs": [],
            "anomaly_count": 0,
            "anomaly_rate": 0.0,
            "issues": [],
        }

        if len(numerical_columns) < 2:
            return result

        # 计算相关矩阵
        corr_matrix = data[numerical_columns].corr()
        high_pairs: list[tuple[str, str, float]] = []

        for i, col_a in enumerate(numerical_columns):
            for col_b in numerical_columns[i + 1 :]:
                corr_val = corr_matrix.loc[col_a, col_b]
                if pd.notna(corr_val) and abs(corr_val) > self.correlation_threshold:
                    high_pairs.append((col_a, col_b, float(corr_val)))

        result["pairs_checked"] = len(numerical_columns) * (len(numerical_columns) - 1) // 2
        result["high_correlation_pairs"] = [
            (p[0], p[1], round(p[2], 4)) for p in high_pairs
        ]

        if not high_pairs:
            return result

        anomaly_rows: dict[int, dict[str, Any]] = {}  # row_index -> 第一次检出的详情

        for target, predictor, corr_val in high_pairs:
            try:
                pair_data = data[[target, predictor]].dropna()
                if len(pair_data) < 10:
                    continue

                X = pair_data[[predictor]].values
                y = pair_data[target].values

                reg = HuberRegressor()
                reg.fit(X, y)
                predicted = reg.predict(X)
                residuals = y - predicted

                # MAD 鲁棒标准差估计
                median_res = np.median(residuals)
                mad = np.median(np.abs(residuals - median_res))
                robust_std = mad * 1.4826  # MAD -> std 转换系数

                if robust_std < 1e-10:
                    continue

                z_scores = (residuals - median_res) / robust_std

                for local_idx, (abs_idx, row) in enumerate(pair_data.iterrows()):
                    z = z_scores[local_idx]
                    if abs(z) > 3:
                        row_idx = int(abs_idx)
                        if row_idx not in anomaly_rows:
                            anomaly_rows[row_idx] = {
                                "data_id": row_idx,
                                "issue_type": "跨字段关系异常",
                                "severity": "warning",
                                "details": {
                                    "method": "regression_residual",
                                    "target_column": target,
                                    "predictor_columns": [predictor],
                                    "actual_value": _to_native(row[target]),
                                    "predicted_value": _to_native(predicted[local_idx]),
                                    "residual": _to_native(residuals[local_idx]),
                                    "residual_zscore": _to_native(z),
                                    "reason": f"{target} 偏离 {predictor} 的预测值 {abs(z):.1f} 个标准差",
                                },
                            }
            except Exception:
                logger.debug("regression_residual: 列对 (%s, %s) 处理异常", target, predictor, exc_info=True)
                continue

        issues = list(anomaly_rows.values())
        result["anomaly_count"] = len(issues)
        result["anomaly_rate"] = float(len(issues) / max(len(data), 1))
        result["issues"] = issues

        return result

    # ------------------------------------------------------------------
    # 方法 2: 隔离森林
    # ------------------------------------------------------------------

    def _isolation_forest_check(self, data: "pd.DataFrame", numerical_columns: list[str]) -> dict[str, Any]:
        """使用 IsolationForest 在多维特征空间中检测离群点。"""
        result: dict[str, Any] = {
            "features_used": 0,
            "samples_used": 0,
            "anomaly_count": 0,
            "anomaly_rate": 0.0,
            "issues": [],
        }

        # 选择数值列（最多 max_features 列）
        cols = numerical_columns[: self.max_features]
        subset = data[cols].copy()

        # 中位数填充缺失值
        for c in cols:
            median_val = subset[c].median()
            subset[c] = subset[c].fillna(median_val if pd.notna(median_val) else 0.0)

        result["features_used"] = len(cols)

        # 若数据量 > max_samples，采样
        if len(subset) > self.max_samples:
            rng = np.random.RandomState(self.seed)
            sample_indices = rng.choice(len(subset), size=self.max_samples, replace=False)
            sample_indices.sort()
            subset = subset.iloc[sample_indices]

        result["samples_used"] = len(subset)

        if len(subset) < 2:
            return result

        clf = IsolationForest(
            contamination=self.contamination,
            random_state=self.seed,
            n_jobs=-1,
        )
        labels = clf.fit_predict(subset.values)
        scores = clf.decision_function(subset.values)

        issues: list[dict[str, Any]] = []
        for local_idx, (abs_idx, _) in enumerate(subset.iterrows()):
            if labels[local_idx] == -1:
                issues.append({
                    "data_id": int(abs_idx),
                    "issue_type": "多变量组合异常",
                    "severity": "warning",
                    "details": {
                        "method": "isolation_forest",
                        "anomaly_score": _to_native(scores[local_idx]),
                        "reason": f"该记录在多维特征空间中表现为异常（隔离森林得分 {scores[local_idx]:.2f}）",
                    },
                })

        result["anomaly_count"] = len(issues)
        result["anomaly_rate"] = float(len(issues) / max(len(subset), 1))
        result["issues"] = issues

        return result

    # ------------------------------------------------------------------
    # 方法 3: 相关性一致性
    # ------------------------------------------------------------------

    def _correlation_consistency_check(self, data: "pd.DataFrame", numerical_columns: list[str]) -> dict[str, Any]:
        """检测高相关列对间逐行偏离度异常。"""
        result: dict[str, Any] = {
            "high_corr_pairs": [],
            "anomaly_count": 0,
            "anomaly_rate": 0.0,
            "issues": [],
        }

        if len(numerical_columns) < 2:
            return result

        corr_matrix = data[numerical_columns].corr()
        high_pairs: list[tuple[str, str, float]] = []

        for i, col_a in enumerate(numerical_columns):
            for col_b in numerical_columns[i + 1 :]:
                corr_val = corr_matrix.loc[col_a, col_b]
                if pd.notna(corr_val) and abs(corr_val) > 0.8:
                    high_pairs.append((col_a, col_b, float(corr_val)))

        result["high_corr_pairs"] = [
            (p[0], p[1], round(p[2], 4)) for p in high_pairs
        ]

        if not high_pairs:
            return result

        anomaly_rows: dict[int, dict[str, Any]] = {}

        for col_a, col_b, corr_val in high_pairs:
            try:
                pair_data = data[[col_a, col_b]].dropna()
                if len(pair_data) < 10:
                    continue

                # 标准化（z-score）
                mean_a, std_a = pair_data[col_a].mean(), pair_data[col_a].std()
                mean_b, std_b = pair_data[col_b].mean(), pair_data[col_b].std()

                if std_a < 1e-10 or std_b < 1e-10:
                    continue

                z_a = (pair_data[col_a] - mean_a) / std_a
                z_b = (pair_data[col_b] - mean_b) / std_b

                # 标准化差值
                diff = (z_a - z_b).abs()

                for abs_idx, d in diff.items():
                    if d > 3:
                        row_idx = int(abs_idx)
                        if row_idx not in anomaly_rows:
                            anomaly_rows[row_idx] = {
                                "data_id": row_idx,
                                "issue_type": "相关性违规",
                                "severity": "warning",
                                "details": {
                                    "method": "correlation_consistency",
                                    "column_a": col_a,
                                    "column_b": col_b,
                                    "correlation": _to_native(corr_val),
                                    "deviation": _to_native(d),
                                    "value_a": _to_native(pair_data.loc[abs_idx, col_a]),
                                    "value_b": _to_native(pair_data.loc[abs_idx, col_b]),
                                    "reason": f"{col_a} 与 {col_b} 的标准化偏离度为 {d:.1f}，超过阈值 3",
                                },
                            }
            except Exception:
                logger.debug("correlation_consistency: 列对 (%s, %s) 处理异常", col_a, col_b, exc_info=True)
                continue

        issues = list(anomaly_rows.values())
        result["anomaly_count"] = len(issues)
        result["anomaly_rate"] = float(len(issues) / max(len(data), 1))
        result["issues"] = issues

        return result


# ------------------------------------------------------------------
# 工具函数
# ------------------------------------------------------------------


def _to_native(value: Any) -> int | float | str | None:
    """将 numpy/pandas 标量转为 Python 原生类型，确保 JSON 可序列化。"""
    if value is None:
        return None
    try:
        if isinstance(value, (np.integer,)):
            return int(value)
        if isinstance(value, (np.floating,)):
            return float(value)
        if isinstance(value, (np.bool_,)):
            return bool(value)
        if isinstance(value, (np.ndarray,)):
            return value.tolist()
    except Exception:
        pass
    if isinstance(value, float):
        return float(value)
    if isinstance(value, int):
        return int(value)
    return value

# -*- coding: utf-8 -*-

"""
物理保真度/约束一致性检测（Tabular）。

你可以把它理解为“数据是否违反明显的物理/业务规则”：
- 例如年龄必须在 [0,120]，金额不能为负，比例必须在 [0,1] 等

实现上分两档：
- 有 pandera：用 DataFrameSchema + Check(ge/le) 进行校验并提取 failure_cases
- 无 pandera：降级用简单的 pandas 过滤逻辑
"""

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
    import pandera as pa  # type: ignore
    from pandera import Check, Column, DataFrameSchema  # type: ignore

    PANDERA_AVAILABLE = True
except ImportError:
    PANDERA_AVAILABLE = False


class TabularPhysicsScanner(BaseScanner):
    def __init__(self, constraints: Optional[dict[str, dict[str, Any]]] = None, check_conservation: bool = False):
        super().__init__(name="TabularPhysicsScanner")
        self.constraints = constraints or {}
        self.check_conservation = check_conservation

    def scan(self, data: Any, numerical_columns: Optional[list[str]] = None) -> dict[str, Any]:
        if not PANDAS_AVAILABLE:
            return self._error_result("pandas未安装，请先安装 pandas/numpy 依赖")

        assert PANDAS_AVAILABLE
        if data is None or len(data) == 0:
            return self._error_result("数据为空")

        self.validate_data(data, pd.DataFrame)

        if numerical_columns is None:
            numerical_columns = data.select_dtypes(include=[np.number]).columns.tolist()

        if len(numerical_columns) == 0:
            return self._error_result("没有数值列可供检测")

        results: dict[str, Any] = {
            "algorithm": "Pandera Schema Validation" if PANDERA_AVAILABLE else "Basic Constraint Validation (Fallback - pandera未安装)",
            "total_samples": len(data),
            "total_features": len(numerical_columns),
        }

        if not PANDERA_AVAILABLE:
            return self._fallback_scan(data, numerical_columns)

        violations: list[dict[str, Any]] = []
        total_violations = 0

        for col in numerical_columns:
            if col not in data.columns:
                continue
            col_violations = self._validate_column(data, col)
            if col_violations:
                violations.extend(col_violations)
                total_violations += len(col_violations)

        cross_col_violations = self._check_cross_column_constraints(data)
        if cross_col_violations:
            violations.extend(cross_col_violations)
            total_violations += len(cross_col_violations)

        total_checks = len(data) * len(numerical_columns)
        violation_rate = total_violations / max(total_checks, 1)

        results["has_issues"] = violation_rate > 0.01
        results["constraint_violations"] = int(total_violations)
        results["violation_rate"] = float(violation_rate)
        results["causality_score"] = float(1.0 - min(violation_rate * 10, 1.0))
        results["total_issues"] = int(total_violations)
        results["issue_percentage"] = float(violation_rate)
        results["constraints_checked"] = list(self.constraints.keys())

        detailed_issues: list[dict[str, Any]] = []
        for v in violations[:50]:
            detailed_issues.append(
                {
                    "data_id": v.get("row_index", "N/A"),
                    "issue_type": v.get("constraint_type", "约束违规"),
                    "severity": self._get_severity(violation_rate),
                    "details": {
                        "constraint_name": v.get("column"),
                        "expected": v.get("expected"),
                        "actual": v.get("actual_value"),
                    },
                }
            )
        results["detailed_issues"] = detailed_issues
        return results

    def _validate_column(self, data: "pd.DataFrame", column: str) -> list[dict[str, Any]]:
        violations: list[dict[str, Any]] = []
        constraint = self.constraints.get(column, {})
        min_val = constraint.get("min")
        max_val = constraint.get("max")

        checks: list[Any] = []
        if min_val is not None:
            checks.append(Check.ge(min_val))
        if max_val is not None:
            checks.append(Check.le(max_val))
        if not checks:
            return violations

        try:
            schema = DataFrameSchema({column: Column(checks=checks, nullable=True)})
            schema.validate(data[[column]], lazy=True)
        except pa.errors.SchemaErrors as e:
            for failure in e.failure_cases.itertuples():
                violations.append(
                    {
                        "column": column,
                        "row_index": int(getattr(failure, "index", 0)),
                        "constraint_type": "值域约束违规",
                        "constraint": f"min={min_val}, max={max_val}",
                        "actual_value": float(getattr(failure, "failure_case", 0.0)),
                        "expected": f"[{min_val}, {max_val}]",
                    }
                )
        except Exception:
            pass
        return violations

    def _check_cross_column_constraints(self, data: "pd.DataFrame") -> list[dict[str, Any]]:
        violations: list[dict[str, Any]] = []
        if not self.check_conservation:
            return violations

        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for i, col1 in enumerate(numeric_cols):
            for col2 in numeric_cols[i + 1 :]:
                if "in" in col1.lower() and "out" in col2.lower():
                    diff = data[col1] - data[col2]
                    extreme_diff = np.abs(diff) > 3 * diff.std()
                    extreme_indices = data[extreme_diff].index.tolist()
                    for idx in extreme_indices[:10]:
                        violations.append(
                            {
                                "column": f"{col1} vs {col2}",
                                "row_index": int(idx),
                                "constraint_type": "守恒约束违规",
                                "constraint": "输入输出平衡",
                                "actual_value": float(diff.loc[idx]),
                                "expected": "接近0",
                            }
                        )
        return violations

    def _fallback_scan(self, data: "pd.DataFrame", numerical_columns: list[str]) -> dict[str, Any]:
        results: dict[str, Any] = {
            "algorithm": "Basic Constraint Validation (Fallback - pandera未安装)",
            "total_samples": len(data),
            "total_features": len(numerical_columns),
            "warning": "pandera未安装，使用基本验证。建议安装: pip install pandera",
        }

        violations: list[dict[str, Any]] = []
        total_violations = 0
        for col in numerical_columns:
            if col not in data.columns:
                continue
            constraint = self.constraints.get(col, {})
            min_val = constraint.get("min")
            max_val = constraint.get("max")
            if min_val is not None:
                mask = data[col] < min_val
                for idx in data[mask].index[:10]:
                    violations.append(
                        {
                            "column": col,
                            "row_index": int(idx),
                            "constraint_type": "最小值约束违规",
                            "actual_value": float(data.loc[idx, col]),
                            "expected": f">= {min_val}",
                        }
                    )
                total_violations += int(mask.sum())
            if max_val is not None:
                mask = data[col] > max_val
                for idx in data[mask].index[:10]:
                    violations.append(
                        {
                            "column": col,
                            "row_index": int(idx),
                            "constraint_type": "最大值约束违规",
                            "actual_value": float(data.loc[idx, col]),
                            "expected": f"<= {max_val}",
                        }
                    )
                total_violations += int(mask.sum())

        total_checks = len(data) * len(numerical_columns)
        violation_rate = total_violations / max(total_checks, 1)
        results["has_issues"] = violation_rate > 0.01
        results["constraint_violations"] = int(total_violations)
        results["violation_rate"] = float(violation_rate)
        results["causality_score"] = float(1.0 - min(violation_rate * 10, 1.0))
        results["total_issues"] = int(total_violations)
        results["issue_percentage"] = float(violation_rate)
        results["detailed_issues"] = violations[:50]
        return results

    def _get_severity(self, violation_rate: float) -> str:
        if violation_rate > 0.15:
            return "severe"
        if violation_rate > 0.05:
            return "moderate"
        return "light"

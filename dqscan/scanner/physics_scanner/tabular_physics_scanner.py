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

import re
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
    def __init__(
        self,
        constraints: Optional[dict[str, dict[str, Any]]] = None,
        *,
        rules: Optional[list[dict[str, Any]]] = None,
        check_conservation: bool = False,
    ):
        super().__init__(name="TabularPhysicsScanner")
        self.constraints = constraints or {}
        self.rules = rules or []
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
        violation_types: dict[str, int] = {}

        for col in numerical_columns:
            if col not in data.columns:
                continue
            col_violations = self._validate_column(data, col)
            if col_violations:
                violations.extend(col_violations)
                total_violations += len(col_violations)
                violation_types[str(col)] = violation_types.get(str(col), 0) + len(col_violations)

        cross_col_violations = self._check_cross_column_constraints(data)
        if cross_col_violations:
            violations.extend(cross_col_violations)
            total_violations += len(cross_col_violations)
            for v in cross_col_violations:
                key = str(v.get("column", "cross"))
                violation_types[key] = violation_types.get(key, 0) + 1

        custom_rule_violations, custom_rule_counts = self._check_custom_rules(data)
        rule_ids = self._configured_rule_ids()
        if custom_rule_violations:
            violations.extend(custom_rule_violations)
        if custom_rule_counts:
            for k, v in custom_rule_counts.items():
                violation_types[k] = violation_types.get(k, 0) + int(v)
                total_violations += int(v)

        # violation_rate 分母优化：如果配置了具体规则/约束，用实际检查数作为分母
        constraints_checked = list(self.constraints.keys())
        checks_count = max(len(constraints_checked) + len(rule_ids), len(numerical_columns))
        total_checks = len(data) * checks_count
        violation_rate = total_violations / max(total_checks, 1)

        results["has_issues"] = violation_rate > 0.01
        results["constraint_violations"] = int(total_violations)
        results["violation_rate"] = float(violation_rate)
        results["causality_score"] = float(1.0 - min(violation_rate * 10, 1.0))
        results["total_issues"] = int(total_violations)
        results["issue_percentage"] = float(violation_rate)
        results["constraints_checked"] = constraints_checked + rule_ids
        results["violation_types"] = violation_types
        results["rules_checked"] = rule_ids

        global_severity = self._get_severity(violation_rate)
        detailed_issues: list[dict[str, Any]] = []
        for v in violations[:50]:
            # 规则级 severity 优先，否则使用全局推算
            severity = v.get("severity") or global_severity
            detailed_issues.append(
                {
                    "data_id": v.get("row_index", "N/A"),
                    "issue_type": v.get("constraint_type", "约束违规"),
                    "severity": severity,
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
        violation_types: dict[str, int] = {}
        for col in numerical_columns:
            if col not in data.columns:
                continue
            constraint = self.constraints.get(col, {})
            min_val = constraint.get("min")
            max_val = constraint.get("max")
            col_violations = 0
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
                col_violations += int(mask.sum())
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
                col_violations += int(mask.sum())
            if col_violations:
                violation_types[str(col)] = violation_types.get(str(col), 0) + col_violations

        cross_col_violations = self._check_cross_column_constraints(data)
        if cross_col_violations:
            violations.extend(cross_col_violations)
            total_violations += len(cross_col_violations)
            for v in cross_col_violations:
                key = str(v.get("column", "cross"))
                violation_types[key] = violation_types.get(key, 0) + 1

        custom_rule_violations, custom_rule_counts = self._check_custom_rules(data)
        rule_ids = self._configured_rule_ids()
        if custom_rule_violations:
            violations.extend(custom_rule_violations)
        if custom_rule_counts:
            for k, v in custom_rule_counts.items():
                violation_types[k] = violation_types.get(k, 0) + int(v)
                total_violations += int(v)

        # violation_rate 分母优化：如果配置了具体规则/约束，用实际检查数作为分母
        constraints_checked = list(self.constraints.keys())
        checks_count = max(len(constraints_checked) + len(rule_ids), len(numerical_columns))
        total_checks = len(data) * checks_count
        violation_rate = total_violations / max(total_checks, 1)
        results["has_issues"] = violation_rate > 0.01
        results["constraint_violations"] = int(total_violations)
        results["violation_rate"] = float(violation_rate)
        results["causality_score"] = float(1.0 - min(violation_rate * 10, 1.0))
        results["total_issues"] = int(total_violations)
        results["issue_percentage"] = float(violation_rate)
        results["constraints_checked"] = constraints_checked + rule_ids
        results["violation_types"] = violation_types
        results["rules_checked"] = rule_ids
        results["detailed_issues"] = violations[:50]
        return results

    def _get_severity(self, violation_rate: float) -> str:
        if violation_rate > 0.15:
            return "severe"
        if violation_rate > 0.05:
            return "moderate"
        return "light"

    def _check_custom_rules(self, data: "pd.DataFrame") -> tuple[list[dict[str, Any]], dict[str, int]]:
        """
        结构化规则（DSL）校验：避免 eval，支持少量可扩展的 rule types。

        返回：
        - violations_examples：违规样例（最多每条规则取前 10 行）
        - violation_counts：rule_id -> 违规总数（用于统计与 violation_rate 计算）
        """
        rules = self.rules if isinstance(self.rules, list) else []
        if not rules:
            return [], {}

        violations: list[dict[str, Any]] = []
        counts: dict[str, int] = {}

        for idx, rule in enumerate(rules):
            if not isinstance(rule, dict):
                continue
            rule_id = str(rule.get("id") or rule.get("name") or f"rule_{idx+1}")
            rtype = str(rule.get("type") or "").strip().lower()
            try:
                if rtype == "relation":
                    vmask, expected, actual = self._eval_relation_rule(data, rule)
                elif rtype == "sum":
                    vmask, expected, actual = self._eval_sum_rule(data, rule)
                elif rtype == "ratio_range":
                    vmask, expected, actual = self._eval_ratio_range_rule(data, rule)
                elif rtype == "not_null":
                    vmask, expected, actual = self._eval_not_null_rule(data, rule)
                elif rtype == "in_set":
                    vmask, expected, actual = self._eval_in_set_rule(data, rule)
                elif rtype == "if_then":
                    vmask, expected, actual = self._eval_if_then_rule(data, rule)
                elif rtype == "unique":
                    vmask, expected, actual = self._eval_unique_rule(data, rule)
                elif rtype == "regex":
                    vmask, expected, actual = self._eval_regex_rule(data, rule)
                elif rtype == "monotonic":
                    vmask, expected, actual = self._eval_monotonic_rule(data, rule)
                else:
                    continue
            except Exception as e:
                # 规则本身配置不合法：记为 0 次违规，但把 error 暴露在样例里，便于排查
                violations.append(
                    {
                        "column": rule_id,
                        "row_index": 0,
                        "constraint_type": "规则解析失败",
                        "constraint": rtype,
                        "actual_value": str(e),
                        "expected": "valid_rule_config",
                    }
                )
                continue

            cnt = int(vmask.sum()) if hasattr(vmask, "sum") else 0
            if cnt <= 0:
                continue
            counts[rule_id] = counts.get(rule_id, 0) + cnt

            # 规则级 severity：若规则配置了 severity，附加到 violation 记录中
            rule_severity = rule.get("severity") if isinstance(rule, dict) else None

            example_idx = data.index[vmask].tolist()[:10]
            for ridx in example_idx:
                v_entry: dict[str, Any] = {
                    "column": rule_id,
                    "row_index": int(ridx) if str(ridx).isdigit() else ridx,
                    "constraint_type": "跨字段约束违规",
                    "constraint": rtype,
                    "actual_value": actual(data, ridx),
                    "expected": expected,
                }
                if rule_severity:
                    v_entry["severity"] = rule_severity
                violations.append(v_entry)

        return violations[:200], counts

    def _configured_rule_ids(self) -> list[str]:
        rules = self.rules if isinstance(self.rules, list) else []
        ids: list[str] = []
        for idx, rule in enumerate(rules):
            if not isinstance(rule, dict):
                continue
            rid = str(rule.get("id") or rule.get("name") or f"rule_{idx+1}")
            if rid and rid not in ids:
                ids.append(rid)
        return ids[:200]

    def _operand_series(self, data: "pd.DataFrame", operand: Any) -> "pd.Series":
        if isinstance(operand, dict):
            if "col" in operand:
                col = operand.get("col")
                if isinstance(col, str) and col in data.columns:
                    return data[col]
                return pd.Series([np.nan] * len(data), index=data.index)
            if "value" in operand:
                return pd.Series([operand.get("value")] * len(data), index=data.index)
        if isinstance(operand, str) and operand in data.columns:
            return data[operand]
        return pd.Series([operand] * len(data), index=data.index)

    def _eval_relation_rule(self, data: "pd.DataFrame", rule: dict[str, Any]):
        op = str(rule.get("op") or "").strip()
        left = self._operand_series(data, rule.get("left"))
        right = self._operand_series(data, rule.get("right"))

        abs_tol = float(rule.get("abs_tol", 0.0) or 0.0)
        rel_tol = float(rule.get("rel_tol", 0.0) or 0.0)

        if op in {"==", "!="}:
            lnum = pd.to_numeric(left, errors="coerce")
            rnum = pd.to_numeric(right, errors="coerce")
            valid = lnum.notna() & rnum.notna()
            diff = (lnum - rnum).abs()
            tol = abs_tol + rel_tol * rnum.abs()
            ok = diff <= tol
            if op == "!=":
                ok = ~ok
            vmask = valid & (~ok)
        else:
            valid = left.notna() & right.notna()
            if op == "<=":
                vmask = valid & ~(left <= right)
            elif op == "<":
                vmask = valid & ~(left < right)
            elif op == ">=":
                vmask = valid & ~(left >= right)
            elif op == ">":
                vmask = valid & ~(left > right)
            else:
                raise ValueError(f"unsupported op: {op}")

        expected = f"relation({op}, abs_tol={abs_tol}, rel_tol={rel_tol})"

        def _actual(df: "pd.DataFrame", idx):
            try:
                return {"left": df.loc[idx, left.name] if getattr(left, "name", None) else None, "right": df.loc[idx, right.name] if getattr(right, "name", None) else None}
            except Exception:
                return {}

        return vmask, expected, _actual

    def _eval_sum_rule(self, data: "pd.DataFrame", rule: dict[str, Any]):
        terms = rule.get("terms")
        if not isinstance(terms, list) or not terms:
            raise ValueError("sum rule missing terms")
        op = str(rule.get("op") or "==").strip()
        if op not in {"==", "<=", ">="}:
            raise ValueError(f"unsupported sum op: {op}")
        right = rule.get("right")
        abs_tol = float(rule.get("abs_tol", 0.0) or 0.0)
        rel_tol = float(rule.get("rel_tol", 0.0) or 0.0)

        acc = pd.Series([0.0] * len(data), index=data.index, dtype="float64")
        valid = pd.Series([True] * len(data), index=data.index)
        for t in terms:
            if not isinstance(t, dict) or "col" not in t:
                continue
            col = t.get("col")
            if not isinstance(col, str) or col not in data.columns:
                continue
            coef = float(t.get("coef", 1.0) or 1.0)
            s = pd.to_numeric(data[col], errors="coerce")
            valid &= s.notna()
            acc = acc + coef * s.fillna(0.0)

        rser = self._operand_series(data, right)
        rnum = pd.to_numeric(rser, errors="coerce")
        valid &= rnum.notna()

        diff = (acc - rnum).abs()
        tol = abs_tol + rel_tol * rnum.abs()

        if op == "==":
            ok = diff <= tol
        elif op == "<=":
            ok = acc <= rnum + tol
        else:  # >=
            ok = acc + tol >= rnum

        vmask = valid & (~ok)
        expected = f"sum({op}, abs_tol={abs_tol}, rel_tol={rel_tol})"

        def _actual(df: "pd.DataFrame", idx):
            try:
                return {"sum": float(acc.loc[idx]), "right": float(rnum.loc[idx]), "diff": float(diff.loc[idx])}
            except Exception:
                return {}

        return vmask, expected, _actual

    def _eval_ratio_range_rule(self, data: "pd.DataFrame", rule: dict[str, Any]):
        num = pd.to_numeric(self._operand_series(data, rule.get("numerator")), errors="coerce")
        den = pd.to_numeric(self._operand_series(data, rule.get("denominator")), errors="coerce")
        vmin = float(rule.get("min", 0.0) or 0.0)
        vmax = float(rule.get("max", 1.0) or 0.0)
        abs_tol = float(rule.get("abs_tol", 0.0) or 0.0)

        valid = num.notna() & den.notna() & (den != 0)
        ratio = pd.Series([np.nan] * len(data), index=data.index, dtype="float64")
        ratio.loc[valid] = (num.loc[valid] / den.loc[valid]).astype("float64")

        ok = (ratio >= vmin - abs_tol) & (ratio <= vmax + abs_tol)
        vmask = valid & (~ok)
        expected = f"ratio_range([{vmin}, {vmax}], abs_tol={abs_tol})"

        def _actual(df: "pd.DataFrame", idx):
            try:
                return {"ratio": float(ratio.loc[idx]), "numerator": float(num.loc[idx]), "denominator": float(den.loc[idx])}
            except Exception:
                return {}

        return vmask, expected, _actual

    def _eval_not_null_rule(self, data: "pd.DataFrame", rule: dict[str, Any]):
        ser = self._operand_series(data, rule.get("col") or rule.get("operand"))
        vmask = ser.isna()
        expected = "not_null"

        def _actual(df: "pd.DataFrame", idx):
            try:
                return {"value": df.loc[idx, ser.name]} if getattr(ser, "name", None) else {}
            except Exception:
                return {}

        return vmask, expected, _actual

    # ---- 新增规则类型 ----

    def _compare_series(self, series: "pd.Series", op: str, value: Any) -> "pd.Series":
        """通用比较操作：支持 ==, !=, >, <, >=, <=, in, not_in"""
        if op == "==":
            return series == value
        elif op == "!=":
            return series != value
        elif op == ">":
            return series > value
        elif op == "<":
            return series < value
        elif op == ">=":
            return series >= value
        elif op == "<=":
            return series <= value
        elif op == "in":
            if not isinstance(value, list):
                raise ValueError("in 操作需要 list 类型的 value")
            return series.isin(value)
        elif op == "not_in":
            if not isinstance(value, list):
                raise ValueError("not_in 操作需要 list 类型的 value")
            return ~series.isin(value)
        else:
            raise ValueError(f"不支持的操作符: {op}")

    def _eval_if_then_rule(self, data: "pd.DataFrame", rule: dict[str, Any]):
        """条件规则：满足 condition 的行必须同时满足 then 条件"""
        condition = rule.get("condition")
        then = rule.get("then")
        if not isinstance(condition, dict) or not isinstance(then, dict):
            raise ValueError("if_then rule 缺少 condition 或 then")

        cond_col = condition.get("col")
        cond_op = str(condition.get("op", "==")).strip()
        cond_val = condition.get("value")
        if not isinstance(cond_col, str) or cond_col not in data.columns:
            raise ValueError(f"if_then condition 列 '{cond_col}' 不存在")

        then_col = then.get("col")
        then_op = str(then.get("op", "==")).strip()
        then_val = then.get("value")
        if not isinstance(then_col, str) or then_col not in data.columns:
            raise ValueError(f"if_then then 列 '{then_col}' 不存在")

        # 筛选满足 condition 的行
        cond_mask = self._compare_series(data[cond_col], cond_op, cond_val)
        # 在这些行中检查 then 条件
        then_mask = self._compare_series(data[then_col], then_op, then_val)
        # 满足 condition 但不满足 then 的行为违规
        vmask = cond_mask & (~then_mask)

        expected = f"if({cond_col} {cond_op} {cond_val}) then({then_col} {then_op} {then_val})"

        def _actual(df: "pd.DataFrame", idx):
            try:
                return {cond_col: df.loc[idx, cond_col], then_col: df.loc[idx, then_col]}
            except Exception:
                return {}

        return vmask, expected, _actual

    def _eval_unique_rule(self, data: "pd.DataFrame", rule: dict[str, Any]):
        """联合唯一约束：指定列组合不允许有重复行"""
        columns = rule.get("columns")
        if not isinstance(columns, list) or not columns:
            raise ValueError("unique rule 缺少 columns")
        missing = [c for c in columns if c not in data.columns]
        if missing:
            raise ValueError(f"unique rule 列不存在: {missing}")

        vmask = data.duplicated(subset=columns, keep=False)
        expected = f"unique({columns})"

        def _actual(df: "pd.DataFrame", idx):
            try:
                return {c: df.loc[idx, c] for c in columns}
            except Exception:
                return {}

        return vmask, expected, _actual

    def _eval_regex_rule(self, data: "pd.DataFrame", rule: dict[str, Any]):
        """正则约束：指定列必须匹配给定正则表达式"""
        col = rule.get("col")
        pattern = rule.get("pattern")
        if not isinstance(col, str) or col not in data.columns:
            raise ValueError(f"regex rule 列 '{col}' 不存在")
        if not isinstance(pattern, str) or not pattern:
            raise ValueError("regex rule 缺少 pattern")

        # 编译验证正则合法性
        re.compile(pattern)

        ser = data[col].astype(str)
        # 非空且不匹配的行标记为违规（原始值为 NaN 的行不算违规）
        not_null = data[col].notna()
        matched = ser.str.match(pattern, na=False)
        vmask = not_null & (~matched)

        expected = f"regex({pattern})"

        def _actual(df: "pd.DataFrame", idx):
            try:
                return {"value": df.loc[idx, col]}
            except Exception:
                return {}

        return vmask, expected, _actual

    def _eval_monotonic_rule(self, data: "pd.DataFrame", rule: dict[str, Any]):
        """单调性约束：指定列必须单调递增或递减"""
        col = rule.get("col")
        direction = str(rule.get("direction", "asc")).strip().lower()
        order_by = rule.get("order_by")

        if not isinstance(col, str) or col not in data.columns:
            raise ValueError(f"monotonic rule 列 '{col}' 不存在")
        if direction not in {"asc", "desc"}:
            raise ValueError(f"monotonic direction 必须为 asc 或 desc，实际: {direction}")

        # 若指定 order_by，先按 order_by 列排序
        if order_by and isinstance(order_by, str) and order_by in data.columns:
            sorted_data = data.sort_values(by=order_by).reset_index(drop=True)
        else:
            sorted_data = data.reset_index(drop=True)

        series = pd.to_numeric(sorted_data[col], errors="coerce")
        diff = series.diff()

        if direction == "asc":
            # 单调递增：diff < 0 为违规（第一行 diff=NaN 不算违规）
            violation_mask = diff < 0
        else:
            # 单调递减：diff > 0 为违规
            violation_mask = diff > 0

        # 将第一行标记为不违规
        violation_mask.iloc[0] = False
        # NaN diff（如值本身为 NaN）不算违规
        violation_mask = violation_mask.fillna(False)

        # 映射回原始 DataFrame 的 index
        original_indices = data.index
        if order_by and isinstance(order_by, str) and order_by in data.columns:
            sorted_original_idx = data.sort_values(by=order_by).index
        else:
            sorted_original_idx = data.index

        # 构建基于原始 index 的 vmask
        vmask = pd.Series(False, index=data.index)
        violating_positions = violation_mask[violation_mask].index.tolist()
        for pos in violating_positions:
            if pos < len(sorted_original_idx):
                vmask.loc[sorted_original_idx[pos]] = True

        expected = f"monotonic({direction})"

        def _actual(df: "pd.DataFrame", idx):
            try:
                return {"value": df.loc[idx, col]}
            except Exception:
                return {}

        return vmask, expected, _actual

    def _eval_in_set_rule(self, data: "pd.DataFrame", rule: dict[str, Any]):
        allowed = rule.get("allowed")
        if not isinstance(allowed, list) or not allowed:
            raise ValueError("in_set rule missing allowed")
        ser = self._operand_series(data, rule.get("col") or rule.get("operand"))
        valid = ~ser.isna()
        ok = ser.isin(allowed)
        vmask = valid & (~ok)
        expected = f"in_set({allowed[:10]}{'...' if len(allowed) > 10 else ''})"

        def _actual(df: "pd.DataFrame", idx):
            try:
                return {"value": df.loc[idx, ser.name]} if getattr(ser, "name", None) else {}
            except Exception:
                return {}

        return vmask, expected, _actual

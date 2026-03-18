# -*- coding: utf-8 -*-

"""
物理保真度检测编排层（Tabular）。

将规则驱动（TabularPhysicsScanner）与数据驱动（TabularPhysicsDataDrivenScanner）
两个子 Scanner 的结果合并为统一的 physics 模块输出。

data_driven 默认关闭，需显式启用（向后兼容）。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from .tabular_physics_scanner import TabularPhysicsScanner
from .tabular_physics_data_driven import TabularPhysicsDataDrivenScanner

logger = logging.getLogger(__name__)


class TabularPhysicsOrchestrator:
    """
    编排规则驱动 + 数据驱动两个物理保真度检测子系统。

    参数
    ----
    constraints : dict
        传给 TabularPhysicsScanner 的单列约束。
    rules : list
        传给 TabularPhysicsScanner 的 DSL 规则。
    check_conservation : bool
        是否启用守恒约束检测。
    data_driven : dict | None
        数据驱动检测配置。为 None 或 {"enabled": False} 时不执行。
        示例: {"enabled": True, "methods": ["regression_residual", "isolation_forest"], "contamination": 0.05}
    """

    def __init__(
        self,
        constraints: Optional[dict[str, dict[str, Any]]] = None,
        *,
        rules: Optional[list[dict[str, Any]]] = None,
        check_conservation: bool = False,
        data_driven: Optional[dict[str, Any]] = None,
    ):
        self.constraints = constraints or {}
        self.rules = rules or []
        self.check_conservation = check_conservation
        self.data_driven_cfg = data_driven or {}

    def scan(self, data: Any, numerical_columns: Optional[list[str]] = None) -> dict[str, Any]:
        """
        执行完整的物理保真度检测（规则 + 数据驱动）。

        返回结构与 TabularPhysicsScanner.scan() 兼容，额外增加 data_driven 子结果。
        """
        # 1. 规则驱动检测（始终执行）
        rule_scanner = TabularPhysicsScanner(
            constraints=self.constraints,
            rules=self.rules,
            check_conservation=self.check_conservation,
        )
        rule_result = rule_scanner.scan(data, numerical_columns)

        # 2. 数据驱动检测（仅在 enabled=True 时执行）
        dd_cfg = self.data_driven_cfg
        dd_enabled = bool(dd_cfg.get("enabled", False))
        dd_result: Optional[dict[str, Any]] = None

        if dd_enabled:
            try:
                dd_scanner = TabularPhysicsDataDrivenScanner(
                    methods=dd_cfg.get("methods"),
                    contamination=float(dd_cfg.get("contamination", 0.05)),
                    max_features=int(dd_cfg.get("max_features", 20)),
                    correlation_threshold=float(dd_cfg.get("correlation_threshold", 0.7)),
                    max_samples=int(dd_cfg.get("max_samples", 10000)),
                    seed=int(dd_cfg.get("seed", 42)),
                )
                dd_result = dd_scanner.scan(data, numerical_columns)
            except Exception as e:
                logger.exception("数据驱动物理保真度检测异常")
                dd_result = {"error": str(e), "has_issues": False, "total_issues": 0}

        # 3. 合并结果
        merged = self._merge_results(rule_result, dd_result)
        return merged

    def _merge_results(
        self,
        rule_result: dict[str, Any],
        dd_result: Optional[dict[str, Any]],
    ) -> dict[str, Any]:
        """合并规则驱动与数据驱动的结果。"""
        # 以规则驱动结果为基础
        merged = dict(rule_result)

        if dd_result is None:
            merged["data_driven"] = {"enabled": False}
            return merged

        # 注入数据驱动子结果
        merged["data_driven"] = dd_result

        # 合并 issues 统计
        rule_issues = int(rule_result.get("total_issues", 0))
        dd_issues = int(dd_result.get("total_issues", 0))
        merged["total_issues"] = rule_issues + dd_issues

        # 合并 has_issues
        merged["has_issues"] = bool(rule_result.get("has_issues")) or bool(dd_result.get("has_issues"))

        # 合并 detailed_issues（规则优先，数据驱动追加，总数限制 100）
        rule_di = list(rule_result.get("detailed_issues", []))
        dd_di = list(dd_result.get("detailed_issues", []))
        merged["detailed_issues"] = (rule_di + dd_di)[:100]

        # 更新 algorithm 描述
        dd_methods = dd_result.get("methods_used", [])
        if dd_methods:
            rule_algo = rule_result.get("algorithm", "Rule-Based")
            merged["algorithm"] = f"{rule_algo} + Data-Driven({', '.join(dd_methods)})"

        return merged

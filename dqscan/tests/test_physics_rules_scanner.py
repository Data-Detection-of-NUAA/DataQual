# -*- coding: utf-8 -*-

from __future__ import annotations


def test_physics_rules_dsl_sum_and_relation():
    import pandas as pd

    from dqscan.scanner.physics_scanner.tabular_physics_scanner import TabularPhysicsScanner

    df = pd.DataFrame(
        {
            "a": [1.0, 2.0, 3.0, 4.0],
            "b": [1.0, 1.0, 3.0, 1.0],
            "total": [2.0, 3.0, 6.0, 999.0],  # last row violates sum(a+b)==total
        }
    )

    rules = [
        {
            "id": "sum_total",
            "type": "sum",
            "terms": [{"col": "a"}, {"col": "b"}],
            "op": "==",
            "right": {"col": "total"},
            "abs_tol": 1e-6,
        },
        {
            "id": "a_le_b",
            "type": "relation",
            "left": {"col": "a"},
            "op": "<=",
            "right": {"col": "b"},
        },
    ]

    scanner = TabularPhysicsScanner(constraints={}, rules=rules, check_conservation=False)
    res = scanner.scan(df)
    assert "error" not in res
    vt = res.get("violation_types") or {}
    # sum_total 只有最后一行违规（1次）
    assert int(vt.get("sum_total", 0) or 0) >= 1
    # a_le_b 至少有一行违规（a>b）
    assert int(vt.get("a_le_b", 0) or 0) >= 1


def test_if_then_rule():
    """status=paid 但 amount<=0 应被检测为违规"""
    import pandas as pd

    from dqscan.scanner.physics_scanner.tabular_physics_scanner import TabularPhysicsScanner

    df = pd.DataFrame(
        {
            "status": ["paid", "paid", "unpaid", "paid"],
            "paid_amount": [100, -5, 0, 0],  # 第 1、3 行 status=paid 但 amount<=0
            "dummy_num": [1, 2, 3, 4],  # 保证有数值列
        }
    )

    rules = [
        {
            "id": "paid_amount_check",
            "type": "if_then",
            "condition": {"col": "status", "op": "==", "value": "paid"},
            "then": {"col": "paid_amount", "op": ">", "value": 0},
        }
    ]

    scanner = TabularPhysicsScanner(constraints={}, rules=rules)
    res = scanner.scan(df)
    assert "error" not in res
    vt = res.get("violation_types") or {}
    # status=paid 且 paid_amount<=0 的有行 1 和行 3
    assert int(vt.get("paid_amount_check", 0)) == 2


def test_unique_rule():
    """联合键重复检测"""
    import pandas as pd

    from dqscan.scanner.physics_scanner.tabular_physics_scanner import TabularPhysicsScanner

    df = pd.DataFrame(
        {
            "order_id": ["A", "A", "B", "A"],
            "line_item": [1, 1, 1, 2],  # 前两行 (A,1) 重复
            "amount": [10.0, 20.0, 30.0, 40.0],
        }
    )

    rules = [
        {
            "id": "order_unique",
            "type": "unique",
            "columns": ["order_id", "line_item"],
        }
    ]

    scanner = TabularPhysicsScanner(constraints={}, rules=rules)
    res = scanner.scan(df)
    assert "error" not in res
    vt = res.get("violation_types") or {}
    # (A,1) 出现了两次，duplicated(keep=False) 会标记这两行
    assert int(vt.get("order_unique", 0)) == 2


def test_regex_rule():
    """email 格式检测"""
    import pandas as pd

    from dqscan.scanner.physics_scanner.tabular_physics_scanner import TabularPhysicsScanner

    df = pd.DataFrame(
        {
            "email": ["a@b.com", "invalid", "x@y.org", None],
            "score": [1.0, 2.0, 3.0, 4.0],
        }
    )

    rules = [
        {
            "id": "email_format",
            "type": "regex",
            "col": "email",
            "pattern": r"^[^@]+@[^@]+\.[^@]+$",
        }
    ]

    scanner = TabularPhysicsScanner(constraints={}, rules=rules)
    res = scanner.scan(df)
    assert "error" not in res
    vt = res.get("violation_types") or {}
    # "invalid" 不匹配正则，None 不算违规
    assert int(vt.get("email_format", 0)) == 1


def test_monotonic_rule():
    """单调递增违反检测"""
    import pandas as pd

    from dqscan.scanner.physics_scanner.tabular_physics_scanner import TabularPhysicsScanner

    df = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            "cumulative_count": [10, 20, 15, 25],  # 第 3 行 15 < 20 违反单调递增
        }
    )

    rules = [
        {
            "id": "cumulative_monotone",
            "type": "monotonic",
            "col": "cumulative_count",
            "direction": "asc",
            "order_by": "date",
        }
    ]

    scanner = TabularPhysicsScanner(constraints={}, rules=rules)
    res = scanner.scan(df)
    assert "error" not in res
    vt = res.get("violation_types") or {}
    # 15 < 20 这一行违反单调递增
    assert int(vt.get("cumulative_monotone", 0)) == 1


def test_rule_severity():
    """规则级 severity 配置应覆盖全局推算"""
    import pandas as pd

    from dqscan.scanner.physics_scanner.tabular_physics_scanner import TabularPhysicsScanner

    df = pd.DataFrame(
        {
            "status": ["paid", "paid"],
            "paid_amount": [-1, -2],
            "dummy_num": [1, 2],
        }
    )

    rules = [
        {
            "id": "paid_check_severe",
            "type": "if_then",
            "condition": {"col": "status", "op": "==", "value": "paid"},
            "then": {"col": "paid_amount", "op": ">", "value": 0},
            "severity": "severe",
        }
    ]

    scanner = TabularPhysicsScanner(constraints={}, rules=rules)
    res = scanner.scan(df)
    assert "error" not in res

    # 检查 detailed_issues 中使用了规则级 severity
    detailed = res.get("detailed_issues") or []
    assert len(detailed) > 0
    for issue in detailed:
        if issue.get("details", {}).get("constraint_name") == "paid_check_severe":
            assert issue["severity"] == "severe"


# ---- P1 数据驱动测试 ----

def test_data_driven_correlation_consistency():
    """相关性一致性检测应能发现高相关列间的异常偏离"""
    import numpy as np
    import pandas as pd
    from dqscan.scanner.physics_scanner.tabular_physics_data_driven import TabularPhysicsDataDrivenScanner

    rng = np.random.RandomState(42)
    n = 500
    x = rng.normal(0, 1, n)
    y = x * 2 + rng.normal(0, 0.05, n)  # 高相关（corr > 0.99）
    # 注入 5 个温和的异常：偏离但不会大幅破坏整体相关结构
    y[-5:] = y[-5:] + 8

    df = pd.DataFrame({"x": x, "y": y})
    scanner = TabularPhysicsDataDrivenScanner(methods=["correlation_consistency"])
    res = scanner.scan(df)

    assert "error" not in res
    assert res["has_issues"] is True
    assert res["anomaly_count"] >= 3


def test_data_driven_sklearn_degradation():
    """sklearn 不可用时应降级跳过依赖 sklearn 的方法"""
    import numpy as np
    import pandas as pd
    from dqscan.scanner.physics_scanner import tabular_physics_data_driven as mod

    original = mod.SKLEARN_AVAILABLE
    mod.SKLEARN_AVAILABLE = False
    try:
        df = pd.DataFrame({"a": np.arange(50, dtype=float), "b": np.arange(50, dtype=float)})
        scanner = mod.TabularPhysicsDataDrivenScanner(
            methods=["regression_residual", "isolation_forest", "correlation_consistency"]
        )
        res = scanner.scan(df)
        assert "error" not in res
        assert "regression_residual" in res.get("methods_skipped", {})
        assert "isolation_forest" in res.get("methods_skipped", {})
        assert "correlation_consistency" in res.get("methods_used", [])
    finally:
        mod.SKLEARN_AVAILABLE = original


# ---- 编排层测试 ----

def test_orchestrator_rule_only():
    """编排层 data_driven 关闭时等价于纯规则驱动"""
    import pandas as pd
    from dqscan.scanner.physics_scanner.tabular_physics_orchestrator import TabularPhysicsOrchestrator

    df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [1.0, 1.0, 3.0]})
    orch = TabularPhysicsOrchestrator(constraints={"a": {"min": 0, "max": 10}}, data_driven=None)
    res = orch.scan(df)
    assert "error" not in res
    assert res["data_driven"]["enabled"] is False


def test_orchestrator_with_data_driven():
    """编排层 data_driven 启用时应合并两个子系统结果"""
    import numpy as np
    import pandas as pd
    from dqscan.scanner.physics_scanner.tabular_physics_orchestrator import TabularPhysicsOrchestrator

    rng = np.random.RandomState(42)
    n = 100
    x = rng.normal(0, 1, n)
    y = x * 3 + rng.normal(0, 0.1, n)
    y[-3:] += 30

    df = pd.DataFrame({"x": x, "y": y})
    orch = TabularPhysicsOrchestrator(
        constraints={},
        data_driven={"enabled": True, "methods": ["correlation_consistency"]},
    )
    res = orch.scan(df)
    assert "error" not in res
    assert "data_driven" in res
    assert isinstance(res["data_driven"], dict)


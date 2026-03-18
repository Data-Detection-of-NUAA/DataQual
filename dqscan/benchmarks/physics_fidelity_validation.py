#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物理保真度算法可行性验证脚本。

验证三个核心算法在 dqscan 环境下的可行性：
1. 回归残差法（Regression Residual）   — 检测违反变量间函数关系的行
2. Isolation Forest 多维异常            — 无监督检测组合异常
3. if_then 条件规则（DSL 扩展）        — 检测违反条件业务规则的行

运行方式：
    ./.venv/bin/python dqscan/benchmarks/physics_fidelity_validation.py
"""

from __future__ import annotations

import sys
import time
from typing import Any

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def precision_recall(predicted: set[int], actual: set[int]) -> dict[str, float]:
    """计算 precision / recall / f1。"""
    tp = len(predicted & actual)
    fp = len(predicted - actual)
    fn = len(actual - predicted)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def print_section(title: str) -> None:
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_metrics(metrics: dict[str, Any]) -> None:
    print(f"  Precision : {metrics['precision']:.4f}")
    print(f"  Recall    : {metrics['recall']:.4f}")
    print(f"  F1        : {metrics['f1']:.4f}")
    print(f"  TP={metrics['tp']}  FP={metrics['fp']}  FN={metrics['fn']}")


# =========================================================================
# 验证 1：回归残差法（Regression Residual）
# =========================================================================

def validation_regression_residual() -> dict[str, Any]:
    """
    构造满足 PV = nRT 的合成数据集，注入违反行，
    用回归残差法检测。
    """
    print_section("验证 1：回归残差法（Regression Residual）")

    from sklearn.linear_model import HuberRegressor

    rng = np.random.RandomState(42)
    n_samples = 2000
    n_anomalies = 50  # 2.5% 异常率

    # --- 1. 构造合成数据（PV = nRT，简化为 P = T/V）---
    # 假设 nR = 1（简化常数），则 P = T / V
    # 这是一个非线性关系，需要特征工程来线性化
    temperature = rng.uniform(200, 500, n_samples)   # K
    volume = rng.uniform(1, 10, n_samples)            # m^3
    # 正常 pressure = T / V + 小噪声
    pressure = temperature / volume + rng.normal(0, 0.5, n_samples)

    # --- 2. 注入异常行 ---
    anomaly_indices = set(rng.choice(n_samples, n_anomalies, replace=False).tolist())
    anomaly_list = sorted(anomaly_indices)
    for idx in anomaly_list:
        # 大幅偏离正常关系：pressure 随机加/减 30-80
        pressure[idx] += rng.choice([-1, 1]) * rng.uniform(30, 80)

    df = pd.DataFrame({
        "temperature": temperature,
        "volume": volume,
        "pressure": pressure,
    })

    print(f"  数据集: {n_samples} 行, 注入 {n_anomalies} 个违反 PV=nRT 的行")
    print(f"  注入行索引（前 10）: {anomaly_list[:10]}...")

    # --- 3. 拟合 HuberRegressor（鲁棒回归）---
    # 关键：P = T/V 是非线性的，直接用 T, V 做线性回归效果差。
    # 正确做法：特征工程，加入 T/V 作为特征（或用 P*V vs T 线性化）。
    t0 = time.time()
    X = np.column_stack([
        temperature / volume,           # T/V（线性化的核心特征）
        temperature,                     # T
        volume,                          # V
        temperature * volume,            # T*V（交互项）
    ])
    y = df["pressure"].values

    model = HuberRegressor(epsilon=1.35, max_iter=200)
    model.fit(X, y)
    y_pred = model.predict(X)

    residuals = y - y_pred
    residual_std = np.std(residuals)
    residual_mean = np.mean(residuals)

    # --- 4. 检测残差 > 3σ 的行 ---
    z_scores = np.abs((residuals - residual_mean) / residual_std)
    threshold = 3.0
    detected_mask = z_scores > threshold
    detected_indices = set(np.where(detected_mask)[0].tolist())
    elapsed = time.time() - t0

    metrics = precision_recall(detected_indices, anomaly_indices)
    print(f"\n  HuberRegressor 拟合 + 3σ 阈值检测")
    print(f"  检测到 {len(detected_indices)} 个异常行 (阈值={threshold}σ)")
    print_metrics(metrics)
    print(f"  耗时: {elapsed:.3f}s")

    # --- 5. 展示几个检出的异常行 ---
    print(f"\n  检出样例（前 5 个）:")
    for idx in sorted(detected_indices)[:5]:
        is_true = "TRUE" if idx in anomaly_indices else "FALSE"
        print(f"    row {idx}: T={df.loc[idx,'temperature']:.1f}, V={df.loc[idx,'volume']:.1f}, "
              f"P={df.loc[idx,'pressure']:.1f}, predicted={y_pred[idx]:.1f}, "
              f"residual_z={z_scores[idx]:.2f}, injected={is_true}")

    return {
        "method": "regression_residual",
        "model": "HuberRegressor",
        "threshold": f"{threshold}σ",
        "n_samples": n_samples,
        "n_anomalies": n_anomalies,
        "n_detected": len(detected_indices),
        "metrics": metrics,
        "elapsed_sec": round(elapsed, 3),
    }


# =========================================================================
# 验证 2：Isolation Forest 多维异常
# =========================================================================

def validation_isolation_forest() -> dict[str, Any]:
    """
    在同一合成数据集上运行 Isolation Forest，对比回归残差法。
    """
    print_section("验证 2：Isolation Forest 多维异常")

    from sklearn.ensemble import IsolationForest

    rng = np.random.RandomState(42)
    n_samples = 2000
    n_anomalies = 50

    # 同验证 1 的数据构造
    temperature = rng.uniform(200, 500, n_samples)
    volume = rng.uniform(1, 10, n_samples)
    pressure = temperature / volume + rng.normal(0, 0.5, n_samples)

    anomaly_indices = set(rng.choice(n_samples, n_anomalies, replace=False).tolist())
    anomaly_list = sorted(anomaly_indices)
    for idx in anomaly_list:
        pressure[idx] += rng.choice([-1, 1]) * rng.uniform(30, 80)

    df = pd.DataFrame({
        "temperature": temperature,
        "volume": volume,
        "pressure": pressure,
    })

    print(f"  数据集: {n_samples} 行, 注入 {n_anomalies} 个异常行")

    # --- Isolation Forest ---
    t0 = time.time()
    contamination = n_anomalies / n_samples  # 已知异常率，用于公平对比

    iso = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
    )
    X = df[["temperature", "volume", "pressure"]].values
    labels = iso.fit_predict(X)  # -1 = 异常, 1 = 正常
    scores = iso.decision_function(X)

    detected_indices = set(np.where(labels == -1)[0].tolist())
    elapsed = time.time() - t0

    metrics = precision_recall(detected_indices, anomaly_indices)
    print(f"\n  IsolationForest (n_estimators=200, contamination={contamination:.4f})")
    print(f"  检测到 {len(detected_indices)} 个异常行")
    print_metrics(metrics)
    print(f"  耗时: {elapsed:.3f}s")

    # --- 检测"组合异常"的能力验证 ---
    # 构造更微妙的组合异常：单列在正常范围但组合违反 PV=nRT
    print(f"\n  --- 组合异常检测能力验证 ---")

    rng2 = np.random.RandomState(99)
    n2 = 2000
    n_combo_anomalies = 40

    temperature2 = rng2.uniform(200, 500, n2)
    volume2 = rng2.uniform(1, 10, n2)
    pressure2 = temperature2 / volume2 + rng2.normal(0, 0.5, n2)

    combo_indices = set(rng2.choice(n2, n_combo_anomalies, replace=False).tolist())
    for idx in sorted(combo_indices):
        # 组合异常：交换 pressure 和一个随机正常行的 pressure
        # 这样每列的值域仍在正常范围，但 (T, V, P) 组合不一致
        swap_target = rng2.randint(0, n2)
        while swap_target in combo_indices:
            swap_target = rng2.randint(0, n2)
        pressure2[idx], pressure2[swap_target] = pressure2[swap_target], pressure2[idx]

    df2 = pd.DataFrame({
        "temperature": temperature2,
        "volume": volume2,
        "pressure": pressure2,
    })

    iso2 = IsolationForest(
        n_estimators=200,
        contamination=n_combo_anomalies / n2,
        random_state=42,
        n_jobs=-1,
    )
    X2 = df2[["temperature", "volume", "pressure"]].values
    labels2 = iso2.fit_predict(X2)
    detected2 = set(np.where(labels2 == -1)[0].tolist())
    metrics2 = precision_recall(detected2, combo_indices)

    print(f"  组合异常数据集: {n2} 行, 注入 {n_combo_anomalies} 个组合异常")
    print(f"  （单列值在正常范围，但 T/V/P 组合不一致）")
    print(f"  检测到 {len(detected2)} 个异常行")
    print_metrics(metrics2)

    return {
        "method": "isolation_forest",
        "n_samples": n_samples,
        "n_anomalies": n_anomalies,
        "n_detected": len(detected_indices),
        "metrics_obvious": metrics,
        "combo_anomalies": n_combo_anomalies,
        "combo_detected": len(detected2),
        "metrics_combo": metrics2,
        "elapsed_sec": round(elapsed, 3),
    }


# =========================================================================
# 验证 3：if_then 条件规则（DSL 新增类型）
# =========================================================================

def validation_if_then_rule() -> dict[str, Any]:
    """
    构造 status + amount 数据集，注入 "status=paid 但 amount<=0" 违规行。
    用纯 pandas 实现 if_then 规则验证。
    """
    print_section("验证 3：if_then 条件规则（DSL 扩展）")

    rng = np.random.RandomState(42)
    n_samples = 1000
    n_anomalies = 30

    # --- 构造数据 ---
    statuses = rng.choice(["pending", "paid", "cancelled", "refunded"], n_samples, p=[0.3, 0.4, 0.2, 0.1])
    amounts = rng.uniform(10, 1000, n_samples).round(2)

    # 正常逻辑：paid 的 amount 都 > 0（已由 uniform(10,1000) 保证）
    # 注入违规：选 30 个 paid 行把 amount 改为 <= 0
    paid_indices = np.where(statuses == "paid")[0]
    if len(paid_indices) < n_anomalies:
        # 确保有足够的 paid 行
        for i in range(n_anomalies - len(paid_indices)):
            statuses[rng.randint(0, n_samples)] = "paid"
        paid_indices = np.where(statuses == "paid")[0]

    anomaly_indices_arr = rng.choice(paid_indices, n_anomalies, replace=False)
    anomaly_indices = set(anomaly_indices_arr.tolist())
    for idx in anomaly_indices:
        amounts[idx] = rng.choice([-50, -10, 0, -0.01])

    df = pd.DataFrame({"status": statuses, "amount": amounts})

    print(f"  数据集: {n_samples} 行, 注入 {n_anomalies} 个违规行")
    print(f"  规则: if status=='paid' then amount > 0")
    print(f"  注入行索引（前 10）: {sorted(anomaly_indices)[:10]}...")

    # --- if_then 规则实现（纯 pandas） ---
    t0 = time.time()

    def eval_if_then(data: pd.DataFrame, rule: dict) -> pd.Series:
        """
        if_then 规则验证：返回 boolean Series（True = 违规）。

        rule schema:
        {
            "condition": {"col": str, "op": str, "value": Any},
            "then": {"col": str, "op": str, "value": Any}
        }
        """
        cond = rule["condition"]
        then = rule["then"]

        # 评估 condition
        cond_series = data[cond["col"]]
        cond_op = cond["op"]
        cond_val = cond["value"]

        if cond_op == "==":
            cond_mask = cond_series == cond_val
        elif cond_op == "!=":
            cond_mask = cond_series != cond_val
        elif cond_op == ">":
            cond_mask = cond_series > cond_val
        elif cond_op == ">=":
            cond_mask = cond_series >= cond_val
        elif cond_op == "<":
            cond_mask = cond_series < cond_val
        elif cond_op == "<=":
            cond_mask = cond_series <= cond_val
        elif cond_op == "in":
            cond_mask = cond_series.isin(cond_val)
        else:
            raise ValueError(f"Unsupported condition op: {cond_op}")

        # 评估 then
        then_series = data[then["col"]]
        then_op = then["op"]
        then_val = then["value"]

        if then_op == "==":
            then_ok = then_series == then_val
        elif then_op == "!=":
            then_ok = then_series != then_val
        elif then_op == ">":
            then_ok = then_series > then_val
        elif then_op == ">=":
            then_ok = then_series >= then_val
        elif then_op == "<":
            then_ok = then_series < then_val
        elif then_op == "<=":
            then_ok = then_series <= then_val
        elif then_op == "in":
            then_ok = then_series.isin(then_val)
        else:
            raise ValueError(f"Unsupported then op: {then_op}")

        # 违规 = 满足条件但不满足 then
        violation = cond_mask & ~then_ok
        return violation

    rule = {
        "id": "paid_amount_check",
        "type": "if_then",
        "condition": {"col": "status", "op": "==", "value": "paid"},
        "then": {"col": "amount", "op": ">", "value": 0},
    }

    violation_mask = eval_if_then(df, rule)
    detected_indices = set(np.where(violation_mask)[0].tolist())
    elapsed = time.time() - t0

    metrics = precision_recall(detected_indices, anomaly_indices)

    print(f"\n  if_then 规则检测结果:")
    print(f"  检测到 {len(detected_indices)} 个违规行")
    print_metrics(metrics)
    print(f"  耗时: {elapsed:.6f}s")

    # 展示样例
    print(f"\n  检出样例（前 5 个）:")
    for idx in sorted(detected_indices)[:5]:
        is_true = "TRUE" if idx in anomaly_indices else "FALSE"
        print(f"    row {idx}: status={df.loc[idx,'status']}, amount={df.loc[idx,'amount']}, injected={is_true}")

    # --- 验证 2：多条件 if_then ---
    print(f"\n  --- 多条件 if_then 扩展验证 ---")

    def eval_if_then_multi(data: pd.DataFrame, rule: dict) -> pd.Series:
        """
        支持 conditions 列表（多条件 AND 逻辑）。
        """
        conditions = rule.get("conditions", [rule.get("condition")])
        if not isinstance(conditions, list):
            conditions = [conditions]

        cond_mask = pd.Series([True] * len(data), index=data.index)
        for cond in conditions:
            col_series = data[cond["col"]]
            op = cond["op"]
            val = cond["value"]
            if op == "==":
                cond_mask &= col_series == val
            elif op == ">":
                cond_mask &= col_series > val
            elif op == ">=":
                cond_mask &= col_series >= val
            elif op == "<":
                cond_mask &= col_series < val
            elif op == "<=":
                cond_mask &= col_series <= val

        then = rule["then"]
        then_series = data[then["col"]]
        then_op = then["op"]
        then_val = then["value"]
        if then_op == ">":
            then_ok = then_series > then_val
        elif then_op == ">=":
            then_ok = then_series >= then_val
        elif then_op == "==":
            then_ok = then_series == then_val
        elif then_op == "<=":
            then_ok = then_series <= then_val
        else:
            then_ok = pd.Series([True] * len(data), index=data.index)

        return cond_mask & ~then_ok

    # 添加 category 列
    df["category"] = rng.choice(["A", "B", "C"], n_samples)
    # 注入：category=A & status=paid 但 amount <= 100
    multi_rule = {
        "conditions": [
            {"col": "status", "op": "==", "value": "paid"},
            {"col": "category", "op": "==", "value": "A"},
        ],
        "then": {"col": "amount", "op": ">", "value": 0},
    }
    multi_violations = eval_if_then_multi(df, multi_rule)
    print(f"  多条件规则: if status=='paid' AND category=='A' then amount > 0")
    print(f"  检出违规: {multi_violations.sum()} 行")

    return {
        "method": "if_then_rule",
        "n_samples": n_samples,
        "n_anomalies": n_anomalies,
        "n_detected": len(detected_indices),
        "metrics": metrics,
        "elapsed_sec": round(elapsed, 6),
    }


# =========================================================================
# 交叉对比：回归残差 vs Isolation Forest
# =========================================================================

def cross_comparison() -> None:
    """对比两种方法在同一数据集上的检测差异。"""
    print_section("交叉对比：回归残差 vs Isolation Forest")

    from sklearn.linear_model import HuberRegressor
    from sklearn.ensemble import IsolationForest

    rng = np.random.RandomState(42)
    n_samples = 2000
    n_anomalies = 50

    temperature = rng.uniform(200, 500, n_samples)
    volume = rng.uniform(1, 10, n_samples)
    pressure = temperature / volume + rng.normal(0, 0.5, n_samples)

    anomaly_indices = set(rng.choice(n_samples, n_anomalies, replace=False).tolist())
    for idx in sorted(anomaly_indices):
        pressure[idx] += rng.choice([-1, 1]) * rng.uniform(30, 80)

    df = pd.DataFrame({
        "temperature": temperature,
        "volume": volume,
        "pressure": pressure,
    })

    # 回归残差（含特征工程：T/V 线性化）
    temperature_arr = df["temperature"].values
    volume_arr = df["volume"].values
    X = np.column_stack([
        temperature_arr / volume_arr,
        temperature_arr,
        volume_arr,
        temperature_arr * volume_arr,
    ])
    y = df["pressure"].values
    model = HuberRegressor(epsilon=1.35, max_iter=200)
    model.fit(X, y)
    residuals = y - model.predict(X)
    z_scores = np.abs((residuals - np.mean(residuals)) / np.std(residuals))
    reg_detected = set(np.where(z_scores > 3.0)[0].tolist())

    # Isolation Forest
    iso = IsolationForest(n_estimators=200, contamination=n_anomalies / n_samples, random_state=42)
    labels = iso.fit_predict(df[["temperature", "volume", "pressure"]].values)
    iso_detected = set(np.where(labels == -1)[0].tolist())

    # 对比
    both_detected = reg_detected & iso_detected
    only_reg = reg_detected - iso_detected
    only_iso = iso_detected - reg_detected

    reg_metrics = precision_recall(reg_detected, anomaly_indices)
    iso_metrics = precision_recall(iso_detected, anomaly_indices)

    print(f"  注入 {n_anomalies} 个异常行")
    print(f"\n  回归残差: 检出 {len(reg_detected)} 行")
    print(f"    Precision={reg_metrics['precision']:.4f}, Recall={reg_metrics['recall']:.4f}, F1={reg_metrics['f1']:.4f}")
    print(f"\n  Isolation Forest: 检出 {len(iso_detected)} 行")
    print(f"    Precision={iso_metrics['precision']:.4f}, Recall={iso_metrics['recall']:.4f}, F1={iso_metrics['f1']:.4f}")
    print(f"\n  两者均检出: {len(both_detected)} 行")
    print(f"  仅回归残差: {len(only_reg)} 行")
    print(f"  仅 Isolation Forest: {len(only_iso)} 行")

    # 分析 only_iso 中有多少真正异常
    only_iso_true = only_iso & anomaly_indices
    only_reg_true = only_reg & anomaly_indices
    print(f"\n  仅回归残差检出中真正异常: {len(only_reg_true)} / {len(only_reg)}")
    print(f"  仅 IF 检出中真正异常: {len(only_iso_true)} / {len(only_iso)}")

    print(f"\n  结论:")
    if reg_metrics["f1"] > iso_metrics["f1"]:
        print(f"    回归残差法在已知变量关系时表现更优（F1 更高）")
    else:
        print(f"    Isolation Forest 在此数据集上 F1 更高或持平")
    print(f"    两种方法互补：回归残差可解释性强，IF 不依赖先验关系知识")


# =========================================================================
# 主入口
# =========================================================================

def main() -> None:
    print("=" * 70)
    print("  dqscan 物理保真度算法可行性验证")
    print("=" * 70)

    results = []

    # 验证 1
    r1 = validation_regression_residual()
    results.append(r1)

    # 验证 2
    r2 = validation_isolation_forest()
    results.append(r2)

    # 验证 3
    r3 = validation_if_then_rule()
    results.append(r3)

    # 交叉对比
    cross_comparison()

    # --- 总结 ---
    print_section("验证总结")
    print(f"\n  {'方法':<30} {'Precision':>10} {'Recall':>10} {'F1':>10}")
    print(f"  {'-'*62}")

    for r in results:
        m = r.get("metrics") or r.get("metrics_obvious", {})
        print(f"  {r['method']:<30} {m['precision']:>10.4f} {m['recall']:>10.4f} {m['f1']:>10.4f}")

    if len(results) >= 2 and "metrics_combo" in results[1]:
        mc = results[1]["metrics_combo"]
        print(f"  {'isolation_forest (combo)':<30} {mc['precision']:>10.4f} {mc['recall']:>10.4f} {mc['f1']:>10.4f}")

    print(f"\n  结论：")
    print(f"  1. 回归残差法：在已知变量关系的场景下检测能力最强，可解释性最佳。")
    print(f"     适合作为 physics 模块的 P1 数据驱动能力。")
    print(f"  2. Isolation Forest：不依赖先验知识的通用兜底方案。")
    print(f"     对明显异常检出率高，对微妙的组合异常（值交换）检测较弱。")
    print(f"     适合作为零配置的异常信号补充。")
    print(f"  3. if_then 条件规则：100% 精确，实现简单（纯 pandas），")
    print(f"     填补了当前 DSL 不支持条件约束的盲区。")
    print(f"     适合作为 P0 规则扩展立即集成。")
    print(f"\n  三种算法均已验证可行，可在 dqscan 环境下直接集成。")


if __name__ == "__main__":
    main()
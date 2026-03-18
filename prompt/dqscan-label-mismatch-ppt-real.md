# dqscan：分类标签错标检测（dirty_data.label_mismatch）阶段汇报

日期：2026-02-05  

---

## 1. 本轮交付
- 能力：在结构化表格分类任务中输出“疑似错标”候选集（Top-N，可解释）
- 算法：两档执行器可切换（`cv_consistency` / `confident_learning(lite)`）
- 工程：前端配置 → 后端任务 → 报告展示闭环（含样本行预览、按类型配色）
- 评估：开源数据集（真实）+ 合成错标注入（可复现）输出 P/R、Top-k、耗时

---

## 2. 案例（我们解决什么问题）
- 典型场景：人工标注误差 / 规则标签失效 / 标注标准不一致
- 输出定位：**人工复核候选集（ranking）**，不做自动改标签
- 复核成本：优先看 Top-20/Top-50，快速定位“哪条数据、为什么可疑”

---

## 3. 关键数据结构（输入/输出）
- 输入：缺陷级配置（必填 `label_column`）
```json
{
  "defects.selected.dirty_data.label_mismatch": {
    "executor_algorithm": "confident_learning",
    "params": { "label_column": "label", "n_splits": 5, "max_samples": 20000 }
  }
}
```
- 输出：issues（带解释字段 + 行预览）
```json
{
  "issue_type": "疑似错标",
  "details": {
    "given_label": "A",
    "suggested_label": "B",
    "prob_given": 0.02,
    "prob_suggested": 0.95,
    "reason": "confident_learning_confident_flip",
    "row_preview": { "field1": 123, "field2": "..." }
  }
}
```

---

## 4. 共同核心：out-of-fold 概率矩阵 P
- 原因：必须用样本外预测概率，避免训练集记忆导致漏检
- 方法：`StratifiedKFold` 交叉验证 → 拼接得到 `P(n×K)`

---

## 5. 执行器 A：cv_consistency（兜底/更严格）
- 判定（强信号）：`pred != given` 且 `P[given] <= 0.2` 且 `max(P) >= 0.6`
- 排序：`max(P) - P[given]` 越大越优先
- 特点：更少候选、更直观，偏精度

---

## 6. 执行器 B：confident_learning(lite)（主线/更高覆盖）
- 分数：label quality（默认 `self_confidence=P[given]`，越低越可疑）
- 剪枝：按类 quota（`filter_by=both`）+ 强信号（confident_flip）强制纳入
- 诊断：`per_class_issue_rate`（哪一类更脏）+ `confusion_pairs_top`（主要混淆方向）

---

## 7. 实测结果（真实数据集 + 可复现评估）
![](prompt/assets/label_mismatch/eval_table.png)

---

## 8. 案例展示（digits：真实数据 + 注入 10% 错标）
![](prompt/assets/label_mismatch/case_digits.png)

---

## 9. 风险与边界（必须说明）
- 候选集 ≠ 真错标证明：边界样本/类别重叠会带来不确定性
- 概率质量影响排序：特征弱时排序质量会下降
- 极小类样本不足无法做可靠 CV（会返回错误提示）

---

## 10. 下一步
- 引入可选 cleanlab（更完整的 confident joint/噪声矩阵估计）
- 叠加 KNN 一致性（ENN/NCL 风格）作为补充信号
- 与标注系统联动：导出候选集、回填复核结果、沉淀数据治理 KPI


# dqscan：分类标签错标检测（dirty_data.label_mismatch）阶段汇报 PPT（内容稿）

> 用法：本文件是“逐页内容稿”，可直接复制到 PPT。  
> 建议版式：每页不超过 6 行要点；表格/结果页可截图 `prompt/dqscan-label-mismatch-evaluation.md` 或用图表重绘。  

---

## 1. 标题页
- 项目：dqscan 脏数据检测
- 主题：分类标签错标检测（dirty_data.label_mismatch）
- 本轮交付：算法实现 + 端到端闭环 + 可复现评估
- 日期：2026-02-04

---

## 2. 背景与痛点
- 标签错标会直接拉低模型上限，且引入不可解释波动
- 常见原因：人工标注误差、规则标签失效、多人标准不一致
- 研发成本：把“数据问题”当“模型问题”反复调参

---

## 3. 本轮目标与交付
- 目标：在 dqscan 中落地“疑似错标检测”，输出可排序复核候选集
- 交付：
  - 两档算法（兜底 + 高级）可切换
  - 前端配置 → 后端任务 → 报告展示闭环
  - 开源数据集 + 合成错标注入评估（可复现）

---

## 4. 系统流程（端到端）
- UI：勾选缺陷 `dirty_data.label_mismatch`，选择 executor，配置 `label_column`
- 后端：创建任务，推送日志/进度，产出 result.json + reports
- 引擎：tabular_quality_engine → dirty_data → label_mismatch_scanner
- 报告：候选集 + 指标 + 行数据预览（按错误类型配色）

---

## 5. 输出标准（我们交付什么）
- 指标：`label_mismatch_rate / label_mismatch_count`
- 候选集：`detailed_issues`（Top-N，可排序）
- 单条解释字段：
  - given_label / suggested_label
  - prob_given / prob_suggested / margin
  - reason（触发原因）
  - row_preview（字段→值，报告页可直接表格展示）

---

## 6. 关键数据结构（输入/输出，便于对齐联调）
- 输入（缺陷级配置，核心字段）：
```json
{
  "defects.selected.dirty_data.label_mismatch": {
    "executor_algorithm": "confident_learning",
    "params": { "label_column": "label", "n_splits": 5, "max_samples": 5000 }
  }
}
```
- 输出（单条 issue 样例，核心字段）：
```json
{
  "issue_type": "疑似错标",
  "details": { "given_label": "A", "suggested_label": "B", "prob_given": 0.02, "prob_suggested": 0.95 }
}
```

---

## 7. 关键中间量：out-of-fold 概率矩阵 P
- 核心：必须使用样本外预测概率（out-of-fold），避免模型“记住错标”导致漏检
- 实现：StratifiedKFold，fold 内训练、fold 外预测，拼接得到 P（n×K）

---

## 8. 算法总览：两档执行器
- 兜底（更严格）：`cv_consistency`
  - 高置信冲突阈值法，候选更少，偏高精度
- 高级（主线）：`confident_learning (lite)`
  - label quality score + 按类剪枝 + 混淆方向统计，覆盖更高，偏召回

---

## 9. 算法 A：cv_consistency（阈值法）
- 判定（强信号）：
  - suggested != given
  - prob_given <= threshold_prob_true（默认 0.2）
  - prob_suggested >= threshold_prob_pred（默认 0.6~0.8）
- 排序：prob_suggested - prob_given 越大越可疑

---

## 10. 算法 B：confident_learning（lite）
- 分数（label quality score）：
  - 默认 self_confidence = P[given]（越低越可疑）
  - 可选 normalized_margin / confidence_weighted_entropy
- 剪枝（控制候选规模）：
  - prune_by_class / prune_by_noise_rate / both（默认）
  - 强信号（confident_flip）强制纳入
- 额外输出：per_class_issue_rate、confusion_pairs_top

---

## 11. 工程护栏与可解释性
- 性能：`max_samples` 分层抽样；`n_splits` 自适应到最小类样本数
- 防误报：高基数类别列自动剔除（max_categorical_cardinality），支持 exclude_columns
- 可解释：每条 issue 携带 row_preview，报告页直接“像看数据表”一样复核

---

## 12. 评估设计（可复现）
- 数据集：sklearn 内置（来源 UCI，许可 CC BY 4.0）
  - breast_cancer（二分类）
  - digits（10 类）
- 方法：合成错标注入（uniform / class-conditional），记录 flipped indices 作为 GT
- 指标：precision/recall + precision@k/recall@k + 耗时

---

## 13. 评估结果（摘要）
（建议放一页表格，来自 `prompt/dqscan-label-mismatch-evaluation.md`）
- 总体趋势：
  - confident_learning：多数场景 recall 更高（覆盖更多候选）
  - cv_consistency：更严格，候选更少，precision 往往更高
- Top-k 现象：Top-10/Top-20 命中率通常较高，适合“优先复核列表”

---

## 14. 案例展示（脱敏示例：强信号疑似错标）
（字段/数值为构造示例，用于解释输出含义）
```json
{
  "data_id": 1287,
  "issue_type": "疑似错标",
  "details": {
    "given_label": "通过",
    "suggested_label": "拒绝",
    "prob_given": 0.02,
    "prob_suggested": 0.95,
    "reason": "confident_learning_confident_flip",
    "row_preview": { "age": 19, "income": 12000, "debt_ratio": 0.92, "label": "通过" }
  }
}
```
- 价值：复核人员直接看到“哪条数据 + 为什么可疑 + 关键字段值”，优先处理 Top-N

---

## 15. 局限与风险（必须明确）
- 候选集 ≠ 真错标证明：边界样本/类别重叠会引入不确定性
- 概率质量影响排序：特征弱/模型弱时候选集质量会下降
- 小类样本不足无法做可靠 CV（会返回错误提示）

---

## 16. 使用建议与闭环
- 推荐默认：confident_learning + filter_by=both + fraction_noise 0.03~0.10
- 复核流程：先看 Top-20/50 → 回标/修规则 → 再跑 dqscan 看 label_mismatch_rate 是否下降

---

## 17. 下一步规划（可选增强）
- 可选接入 cleanlab（更完整的 confident joint/噪声矩阵估计）
- 增加 KNN 一致性（ENN/NCL 风格）作为补充信号
- 更强基模型与概率校准提升排序稳定性
- 与标注系统联动：导出候选集、回填复核结果、治理 KPI

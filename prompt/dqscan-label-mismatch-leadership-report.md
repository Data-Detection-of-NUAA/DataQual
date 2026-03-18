# dqscan 脏数据检测：分类标签错标检测（dirty_data.label_mismatch）算法说明（汇报版）

版本：2026-01-31  
范围：仅覆盖 **Tabular（结构化表格）分类任务** 的“疑似错标（Label Mismatch）检测”能力；不包含物理保真/分布漂移/对抗性检测。

---

## 0. 一句话结论（给管理侧）
我们在 dqscan 的“脏数据检测”模块中落地了 **分类标签错标检测**：通过“交叉验证的样本外预测概率（out-of-fold proba）”识别**特征与给定标签明显矛盾**的样本，输出**可排序的人工复核清单**（Top-N），并在报告页可直接看到被标记数据的字段预览与错误类型。

---

## 1. 背景与业务价值
### 1.1 为什么要做“错标检测”
在分类任务中，训练数据的标签质量直接决定模型上限。典型问题包括：
- 人工标注误差（看错/填错/复制粘贴错误）
- 规则标注失效（业务规则变化但历史标签未回补）
- 多人/多批次标注标准不一致（类边界漂移）

错标的直接影响：
- 模型训练被“错误监督信号”牵引，表现下降且难以解释
- 线上判别不稳定、客户投诉、业务策略失效
- 研发调参成本上升（把“数据问题”当“模型问题”来调）

### 1.2 dqscan 的定位：先发现、可解释、便于闭环
本能力的定位是 **Data Quality 的“发现与定位”**：
- 输出“疑似错标候选”，目标是让标注/业务/算法人员快速定位并复核
- 不做“自动纠错”（真实业务中“错标 vs 边界样本”天然难完全区分）
- 通过排序与解释字段，把复核成本压缩到“先看 Top 20/50/100”

---

## 2. 问题定义与输出标准
### 2.1 输入/输出
输入：
- `X`：表格特征（数值列 + 类别列）
- `y~`：给定标签列（分类，至少 2 类）

输出（面向产品/报告）：
- `label_mismatch_rate`：疑似错标比例（候选集规模/样本数）
- `label_mismatch_count`：疑似错标数量
- `detailed_issues`：Top-N 候选列表（按“可疑程度”排序），每条包含：
  - 给定标签 `given_label`
  - 建议标签 `suggested_label`（模型 argmax）
  - 置信度/分数 `prob_given / prob_suggested / score`
  - 触发原因 `reason`
  - 数据预览 `row_preview`（用于前端表格直接展示样本）

### 2.2 “疑似错标”的判定标准（可解释）
我们重点抓两类信号：
1) **高置信冲突（强信号）**：模型在样本外预测中“强烈认为是 B”，而给定标签是 A  
2) **低质量样本（弱信号）**：模型对给定标签不自信、且存在明确的替代标签趋势（但未必达到强信号阈值）

最终输出为“人工复核候选集”，支持：
- 复核优先级排序（先看最可疑的）
- 按类别统计“哪一类更脏”
- 统计主要混淆方向（A 常被标成 B，便于追溯标注规范/业务流程）

---

## 3. 总体技术路线（两档算法 + 同一套中间量）
> 核心思想：要检测错标，必须使用“样本外”预测概率，否则模型会记忆训练标签导致漏检。

### 3.1 关键中间量：out-of-fold 概率矩阵 P（n×K）
对每条样本 `i`，得到一个预测概率向量 `P_i[0..K-1]`（K=类别数）。  
实现方式：`StratifiedKFold` 交叉验证，fold 内训练、fold 外预测并拼接。

为什么必须用 out-of-fold：
- 如果用训练集内预测，模型可能“记住错标”，反而把错标样本预测成给定标签（漏检）

### 3.2 数据预处理（tabular pipeline）
为保证对混合类型表格可用：
- 数值列：缺失值用 median 填充
- 类别列：缺失值用 most_frequent 填充 + one-hot 编码（未知类别 `handle_unknown=ignore`）
- 自动剔除高基数类别列：`max_categorical_cardinality`（默认 50），避免 ID/时间戳类字段造成记忆与误报

### 3.3 基模型（用于生成 P）
当前默认基模型：Logistic Regression（`solver=saga`，可输出 `predict_proba`）  
原因：
- 速度快、稳定、工程依赖低
- 输出概率可解释，适合 ranking 与阈值判定

### 3.4 两档算法（同一套 P，不同的“取候选集”策略）
我们提供两个可切换的执行器（executor）：
- **兜底算法：`cv_consistency`**（阈值法：高置信冲突）
- **高级算法：`confident_learning`（lite）**（打分 + 按类剪枝 + 混淆统计）

工程默认建议：优先 `confident_learning`，必要时可切换到更严格的 `cv_consistency`。

---

## 4. 算法 A：cv_consistency（兜底/更严格）
### 4.1 规则
对样本 `i`：
- `given = y~_i`
- `suggested = argmax_k P_i[k]`
- `prob_given = P_i[given]`
- `prob_suggested = max_k P_i[k]`

判定“疑似错标（强信号）”：
- `suggested != given`
- `prob_given <= threshold_prob_true`（默认 0.2）
- `prob_suggested >= threshold_prob_pred`（默认 0.6~0.8）

### 4.2 输出与排序
对命中的样本按 `margin = prob_suggested - prob_given` 降序排序（越大越可疑），输出 Top-N。

### 4.3 适用场景
- 业务希望“少而准”的候选集（复核资源有限）
- 数据噪声不高、且希望先抓明显错标

---

## 5. 算法 B：confident_learning（lite）（主线/更高覆盖）
> 参考 confident learning / cleanlab 的工程思想：用预测概率估计每条样本的标签质量，并用剪枝策略控制候选集规模。

### 5.1 label quality score（用于排序/剪枝）
我们为每条样本计算“标签质量”分数（越低越可疑），可选 `score_method`：
- `self_confidence`：`P_i[given]`（默认，直观且鲁棒）
- `normalized_margin`：`(P_i[given] - max_{k!=given}P_i[k]) / (P_i[given] + max_{k!=given}P_i[k] + eps)`
- `confidence_weighted_entropy`：`P_i[given] * (1 - entropy(P_i))`（兼顾不确定性）

### 5.2 候选池限制（降低“边界样本”误报）
剪枝时默认只在 **`pred != given`** 的样本中做 bottom 选择：  
这能显著减少把“仅仅是不确定/边界”的样本批量当作错标。

### 5.3 剪枝策略（filter_by）
为把候选集规模控制在“可人工复核”的水平，引入 `filter_by`：
- `prune_by_class`：每个给定类取 bottom `ceil(fraction_noise * class_count)` 的低质量样本
- `prune_by_noise_rate`：用“强信号（高置信冲突）”比例估计类噪声率，按估计噪声率分配 quota 再取 bottom
- `both`（默认）：取上述两者并集，并且强制包含强信号样本
- `confident_learning`：只输出强信号样本（等价于“更严格的候选集”）

### 5.4 诊断信息（便于管理与复盘）
除候选列表外，额外输出：
- `per_class_issue_rate`：每个给定类别的可疑比例（定位“哪一类更脏”）
- `confusion_pairs_top`：主要混淆方向（given→suggested 的 Top 统计）

---

## 6. 工程化关键点（可靠性/性能/可解释）
### 6.1 大数据量护栏（性能）
参数 `max_samples`（默认 5000）：
- 当数据量过大时做**分层抽样**，尽量保留各类样本，避免全量 CV 带来不可接受的耗时

### 6.2 类别样本过少的处理（可靠性）
CV 折数会自动调整为：`n_splits = min(configured_n_splits, min_class_count)`  
若 `n_splits < 2`，直接报错（无法生成可靠的 out-of-fold 概率）。

### 6.3 高基数字段的风险控制
两道防线：
- 显式排除：`exclude_columns`（例如 id/uuid/时间戳/手机号等）
- 自动剔除：`max_categorical_cardinality`（默认 50），高基数类别列不参与建模

### 6.4 结果可解释（面向复核）
每条 issue 都包含：
- 给定/建议标签与对应概率
- score 与 reason（说明“为什么被选中”）
- 行数据预览 `row_preview`，前端可直接按列展示、按错误类型高亮

---

## 7. 评估与效果（可复现）
### 7.1 为什么用“合成错标注入”评估
公开数据集通常没有“真实错标”标注，难以计算 precision/recall。  
因此采用：随机把一部分样本标签翻转，并记录翻转位置作为 ground truth。

### 7.2 数据集（开源、可复现）
选用 scikit-learn 内置数据（来源指向 UCI，许可 CC BY 4.0）：
- `breast_cancer`（二分类，量小，验证快速）
- `digits`（10 类，量更大，难度更接近真实多类场景）

### 7.3 指标
同时看两类指标：
- 总体 `precision/recall`：候选集整体命中率与覆盖率
- `precision@k / recall@k`：Top-k 的质量（更贴近“人工复核先看前几十条”的产品用法）

### 7.4 本机一次运行结果摘要（示例）
> 更完整结果见：`prompt/dqscan-label-mismatch-evaluation.md`

（1）总体 precision/recall（节选）
| dataset | noise_fraction | algorithm | precision | recall |
|---|---:|---:|---:|---:|
| breast_cancer | 0.05 | cv_consistency | 0.682 | 0.536 |
| breast_cancer | 0.05 | confident_learning | 0.516 | 0.571 |
| digits | 0.05 | cv_consistency | 0.649 | 0.831 |
| digits | 0.05 | confident_learning | 0.609 | 0.944 |

（2）现象结论
- Top-k（Top-10/Top-20）命中率通常很高：适合作为“优先复核列表”
- `confident_learning` 通常 **召回更高**（覆盖更多潜在错标），`cv_consistency` 通常更严格（偏高精度/候选更少）

---

## 8. 使用建议（面向上线与交付）
### 8.1 推荐默认策略
- 默认执行器：`confident_learning`
- 默认阈值（强信号）：`threshold_prob_true=0.2`、`threshold_prob_pred=0.6~0.8`
- 默认候选规模控制：`filter_by=both`、`fraction_noise=0.03~0.10`（按业务噪声预期调）

### 8.2 典型调参指南
- 候选太多：降低 `fraction_noise`，或把 `filter_by` 改为 `confident_learning`（只抓强信号）
- 希望更“少而准”：提高 `threshold_prob_pred` + 降低 `threshold_prob_true`
- 误报明显（疑似被 ID 列带偏）：把疑似 ID/时间戳字段加入 `exclude_columns`，或降低 `max_categorical_cardinality`
- 数据量大导致慢：降低 `max_samples` 或 `n_splits`

### 8.3 建议的业务闭环流程
1) 在 dqscan 勾选“疑似错标检测”，配置 `label_column`
2) 先复核 Top-20/Top-50（强信号优先）
3) 修正标签/补充标注规范
4) 重新训练模型并复跑 dqscan，观察 `label_mismatch_rate` 是否下降（作为数据治理 KPI）

---

## 9. 局限与风险说明（汇报必须明确）
- **候选集不是“真错标”证明**：边界样本/特征不足会造成不确定性，仍需人工复核
- **概率质量影响排序**：若特征对标签解释力弱，模型给出的概率本身不可靠，排序质量会下降
- **极小类场景**：当某些类别样本过少时无法做可靠 CV，会直接返回错误提示

---

## 10. 当前落地位置（便于验收与追溯）
- 扫描器：`dqscan/scanner/dirty_data_scanner/tabular/label_mismatch_scanner.py`
- 引擎编排：`dqscan/engine/algorithms/tabular/quality_engine.py`
- 评估脚本：`dqscan/benchmarks/label_mismatch_eval.py`
- 效果记录：`prompt/dqscan-label-mismatch-evaluation.md`

---

## 11. 下一步可选增强（路线图）
> 这里列“能显著提升能力，但不阻塞当前交付”的增强项。

1) **可选接入 cleanlab**：复用其更完整的 confident joint / 噪声矩阵估计与更多过滤策略  
2) **KNN 一致性（ENN/NCL 风格）**：对“局部邻域一致性冲突”敏感，可补充模型概率信号  
3) **更强的基模型与概率校准**：如 GBDT + 校准，提高概率质量与排序稳定性  
4) **与标注系统联动**：一键导出候选集、回填复核结果，形成数据治理闭环指标


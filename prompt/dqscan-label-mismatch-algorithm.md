# dqscan 算法说明：分类错标检测（dirty_data.label_mismatch）

## 1. 这是什么（目标与定位）
`dirty_data.label_mismatch` 用于在**分类数据集（tabular）**中发现“**特征与给定标签不一致**”的样本，并输出一个**可排序的人工复核候选集**。

重要说明：
- 输出是“疑似错标候选”，不是“自动判定真错标”；边界样本/难样本可能被标为可疑。
- 核心依赖是 **out-of-fold / out-of-sample** 的预测概率，否则模型记忆会导致漏检。

本模块当前提供 **两档算法**：
- **兜底算法：`cv_consistency`**（高置信冲突阈值法）
- **高级算法：`confident_learning`（lite）**（label quality score + 按类剪枝 + 混淆方向）

## 2. 输入与前置条件

### 2.1 输入数据
- `X`：表格特征（数值列 + 类别列均可）
- `y~`：给定标签列（分类，至少 2 类）

### 2.2 依赖
- 必需：`pandas`、`numpy`、`scikit-learn`
- 当前实现不强制依赖 `cleanlab`（后续可选增强）

### 2.3 常见“误报来源”（需要在使用时规避）
- 高基数 ID 列（uuid、流水号、时间戳字符串）：容易让模型“记住样本”，导致异常结果。
- 类极不平衡：概率阈值在小类上更不稳定，需要更谨慎的 `n_splits` 与更小的候选集规模。

## 3. 通用流程（两种算法共享）

1) **特征预处理（tabular pipeline）**
- 数值列：缺失值用 median 填充
- 类别列：缺失值用 most_frequent 填充 + one-hot
- 自动剔除高基数类别列：`max_categorical_cardinality`（默认 50）

2) **生成 out-of-fold 概率矩阵 `P`（n×K）**
- 使用 `StratifiedKFold` 交叉验证
- 每个 fold 只在训练子集拟合，并对验证子集输出 `predict_proba`
- 汇总得到每行的 out-of-fold 概率 `P_i[k]`

3) **输出统一格式**
- `label_mismatch_count / label_mismatch_rate`
- `detailed_issues`：Top-N 可疑样本（可排序 + 可解释）

## 4. 兜底算法：`cv_consistency`（阈值法）

### 4.1 判定逻辑
对每个样本 `i`：
- `given = y~_i`
- `suggested = argmax_k P_i[k]`
- `prob_given = P_i[given]`
- `prob_suggested = max_k P_i[k]`

若满足：
- `suggested != given`
- `prob_given <= threshold_prob_true`（默认 0.2）
- `prob_suggested >= threshold_prob_pred`（默认 0.6）

则标为“疑似错标”（高置信冲突）。

### 4.2 特点
- 优点：直观、解释成本低、误报相对少（偏高精度）
- 缺点：只抓“高置信冲突”，召回可能偏低；无法给出系统性的混淆方向统计

## 5. 高级算法：`confident_learning`（lite）

该实现是 “cleanlab / confident learning 风格” 的**轻量落地**：基于 out-of-fold 概率对每条样本打分并按类剪枝（控制候选集规模）。

### 5.1 label quality score（可选）
对每个样本 `i`：
- `self_confidence = P_i[given]`（默认使用，越低越可疑）
- `normalized_margin = (P_i[given] - max_{k!=given} P_i[k]) / (P_i[given] + max_{k!=given} P_i[k] + eps)`
- `entropy = -Σ_k P_i[k] log P_i[k] / log(K)`（归一化熵，越高越不确定）
- `confidence_weighted_entropy = self_confidence * (1 - entropy)`（越低越可疑）

通过 `score_method` 选择实际用于排序/剪枝的 `quality`：
- `self_confidence`（默认）
- `normalized_margin`
- `confidence_weighted_entropy`

### 5.2 候选池限制（减少边界误报）
为了避免把“纯边界/不确定”样本大量标为错标，剪枝阶段默认只在：
- `pred != given`（模型预测类别与给定标签冲突）

的样本里做 per-class bottom 选择。

### 5.3 filter/pruning 策略（`filter_by`）
输出 Top-N 候选需要“剪枝”，否则会把大量难样本都丢进列表。

支持的 `filter_by`：
- `prune_by_class`：每个给定类别取 bottom `ceil(fraction_noise * count_in_class)` 的低质量样本
- `prune_by_noise_rate`：用“高置信冲突”样本的比例作为该类噪声率估计，再按估计噪声率分配 quota
- `both`（默认）：取 `prune_by_class ∪ prune_by_noise_rate`，再强制并入“高置信冲突”
- `confident_learning`：仅返回“高置信冲突”样本（等价于更严格的候选集）

当前实现中，“高置信冲突”定义为：
- `pred != given` 且 `prob_given <= threshold_prob_true` 且 `prob_suggested >= threshold_prob_pred`

### 5.4 输出增强（诊断信息）
除 `detailed_issues` 外，`confident_learning` 额外输出：
- `per_class_issue_rate`：按给定标签统计的可疑比例（方便定位“哪一类更脏”）
- `confusion_pairs_top`：Top 混淆方向（given→suggested 的计数）

## 6. 输出字段说明（result.json / report）

### 6.1 `modules.dirty_data.label_mismatch`（核心）
关键字段（简化）：
- `executor_algorithm`：`confident_learning` 或 `cv_consistency`
- `label_mismatch_count / label_mismatch_rate`
- `detailed_issues`：Top-N 可疑样本明细
- 可选：`per_class_issue_rate`、`confusion_pairs_top`

### 6.2 `detailed_issues`（每条）
每条 issue 的 `details` 会包含（随算法略有不同）：
- `given_label`：给定标签
- `suggested_label`：建议标签（模型 argmax）
- `prob_given / prob_suggested / margin`
- `score / score_method / entropy / normalized_margin`
- `reason`：触发原因（用于前端渲染解释）

## 7. 参数配置（推荐）

### 7.1 defects.selected 方式（推荐）
在创建 dqscan task 的 `params` 中：
```json
{
  "defects": {
    "selected": {
      "dirty_data.label_mismatch": {
        "enabled": true,
        "executor_algorithm": "confident_learning",
        "params": {
          "label_column": "label",
          "n_splits": 5,
          "max_samples": 5000,
          "max_examples": 50,
          "exclude_columns": ["id"],
          "max_categorical_cardinality": 50,
          "score_method": "self_confidence",
          "filter_by": "both",
          "fraction_noise": 0.05,
          "threshold_prob_true": 0.2,
          "threshold_prob_pred": 0.6
        }
      }
    }
  }
}
```

### 7.2 建议默认值与调参方向
- **先用高级算法**：`executor_algorithm="confident_learning"`
- 候选集过多：减小 `fraction_noise`（如 0.01~0.03）或用 `filter_by="confident_learning"`
- 想更“严格/高精度”：提高 `threshold_prob_pred`、降低 `threshold_prob_true`
- 表很大：降低 `max_samples`（先抽样做复核候选集）
- 高基数列误导：补充 `exclude_columns` 或降低 `max_categorical_cardinality`

## 8. 局限与注意事项（务必读）
- **错标 vs 边界样本不可完全区分**：候选集需要人工复核闭环。
- **概率质量影响排序**：如果模型/特征不足，`P` 会很差，候选集质量会下降。
- **极小类样本不足**：`n_splits` 会自适应到最小类样本数；过小会直接报错（无法做 CV）。

## 9. 代码位置
- 扫描器：`dqscan/scanner/dirty_data_scanner/tabular/label_mismatch_scanner.py`
- 引擎接入：`dqscan/engine/algorithms/tabular/quality_engine.py`
- 后端缺陷树（算法列表）：`backend/app/plugin/module_application/dqscan/service.py`


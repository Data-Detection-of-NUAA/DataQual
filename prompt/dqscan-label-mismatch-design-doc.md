# 设计文档：dqscan 分类标签错标检测（dirty_data.label_mismatch）

版本：v1.0  
日期：2026-02-04  
作者：dqscan（算法/工程）  
适用范围：**结构化表格（tabular）分类任务**  

---

## 1. 背景与目标

### 1.1 背景
在分类任务中，训练数据的标签质量决定模型性能上限。常见问题包括：
- 人工标注误差（看错/填错/复制粘贴错误）
- 弱规则标签失效（规则变更、特征口径变更）
- 多人/多批次标注标准不一致（类边界漂移）

这些问题会带来：
- 模型训练收敛异常、上线效果波动、难以解释
- 研发把数据问题当模型问题调参，迭代成本上升

### 1.2 目标（本轮迭代）
在 dqscan 的 `dirty_data` 模块内落地“**疑似错标检测**”，实现端到端闭环：
1) **可配置**：前端可选择缺陷与执行算法，配置关键参数（尤其 `label_column`）。  
2) **可执行**：后端任务可运行引擎，输出结构化结果（`metrics + issues`）。  
3) **可解释**：报告页能看到“哪条数据、为什么可疑”，并按错误类型配色。  
4) **可评估**：基于开源数据集 + 合成错标注入，提供可复现对比指标。  

### 1.3 非目标（明确边界）
- 不承诺“自动纠错/自动改标签”；输出定位为**人工复核候选集**（ranking）。  
- 不覆盖非表格模态（文本/图片 embedding 等）。  
- 不解决数据缺失/异常值等其它脏数据问题（那些由 dirty_data 其它子检测处理）。  

---

## 2. 产品与系统概览

### 2.1 用户使用流程（UI → 任务 → 报告）
1) 上传当前数据集（CSV）。  
2) 在缺陷树中勾选：`脏数据 → 疑似错标检测（dirty_data.label_mismatch）`。  
3) 选择执行器（executor）：`confident_learning` 或 `cv_consistency`。  
4) 在“脏数据 → 算法参数”中配置：
   - **label_column（必填）**
   - exclude_columns / max_samples / n_splits / 阈值 / 剪枝策略等
5) 发起任务，实时查看日志/进度。  
6) 在报告视图查看：指标、候选样本列表、样本字段预览。  

### 2.2 系统数据流（后端/引擎/扫描器）
前端 → 后端（创建任务）→ 引擎 `tabular_quality_engine` → `dirty_data` 模块 → `TabularLabelMismatchScanner` → 写入：
- `output_dir/result.json`（完整结果，供前端展示）
- `output_dir/reports/*`（模块报告 json/summary/docx，供下载/归档）

---

## 3. 关键数据结构与协议

### 3.1 输入配置（Task Params）—— 推荐口径
我们使用缺陷级配置（defects.selected）承载执行器与参数：

```json
{
  "modules": ["dirty_data"],
  "dirty_data": {
    "enabled_checks": ["label_mismatch"],
    "label_mismatch": { "label_column": "label" }
  },
  "defects": {
    "selected": {
      "dirty_data.label_mismatch": {
        "module": "dirty_data",
        "enabled": true,
        "status": "ready",
        "executor_algorithm": "confident_learning",
        "params": {
          "label_column": "label",
          "exclude_columns": ["id"],
          "max_samples": 5000,
          "max_examples": 50,
          "n_splits": 5,
          "threshold_prob_true": 0.2,
          "threshold_prob_pred": 0.6,
          "score_method": "self_confidence",
          "filter_by": "both",
          "fraction_noise": 0.05
        }
      }
    }
  }
}
```

说明：
- `label_column` 是 **强制必填**（启用错标检测即必须提供）。
- `dirty_data.enabled_checks` 用于声明本次 dirty_data 子检测项（只选错标时为 `["label_mismatch"]`）。

### 3.2 中间量（算法内部）
为了避免“训练集记忆导致漏检”，核心中间量是 **out-of-fold 概率矩阵**：
- `P ∈ R^{n×K}`：`P[i,k]=P(model predicts class=k | x_i)`，由交叉验证 fold 外预测得到。  

### 3.3 输出结构（result.json / 前端渲染）
在 `result.json` 的 `modules.dirty_data` 下，会包含：
- `label_mismatch_rate`：疑似错标率
- `label_mismatch_count`：疑似错标数
- `detailed_issues`：候选样本列表（含 issue_type=“疑似错标”）
- `label_mismatch`：错标模块子结果（包含 per-class 统计与混淆方向）

每条 issue 结构（关键字段）：
- `issue_type`: `"疑似错标"`
- `severity`: `"light|moderate|severe"`
- `details`：
  - `given_label / suggested_label`
  - `prob_given / prob_suggested / margin`
  - `score / score_method`（高级算法）
  - `reason`（触发原因）
  - `row_preview`（字段→值的截断预览，供报告页“数据表格”展示）

### 3.4 案例（脱敏示例：一条“强信号”疑似错标）
以下示例用于说明输出可解释性（字段/数值为脱敏构造）：

```json
{
  "issue_type": "疑似错标",
  "severity": "severe",
  "data_id": 1287,
  "details": {
    "label_column": "label",
    "given_label": "通过",
    "suggested_label": "拒绝",
    "prob_given": 0.02,
    "prob_suggested": 0.95,
    "margin": 0.93,
    "reason": "confident_learning_confident_flip",
    "row_preview": {
      "age": 19,
      "income": 12000,
      "debt_ratio": 0.92,
      "history_bad_debt": 3,
      "label": "通过"
    }
  }
}
```

解读方式：
- `prob_given` 很低 + `prob_suggested` 很高 + `reason=confident_flip`：属于强信号，建议优先复核。  
- `row_preview` 直接给出关键字段值，复核人员无需再去二次查库/翻原始表即可定位样本。  

---

## 4. 算法设计与选型

### 4.1 总体原则
我们把错标检测定位为“**候选集生成 + 解释**”，而不是二分类判定器：
- 输出需可排序（优先复核 Top-N）
- 输出需可解释（为什么怀疑）
- 可降级、依赖轻（适配现有 dqscan 工程形态）

### 4.2 两档执行器（executor）
本轮落地两种算法：

#### A) 兜底：cv_consistency（高置信冲突阈值法）
对样本 i：
- given = y~_i  
- suggested = argmax(P_i)  
- prob_given = P_i[given]  
- prob_suggested = max(P_i)  

判为疑似错标（强信号）：
- suggested != given
- prob_given <= threshold_prob_true（默认 0.2）
- prob_suggested >= threshold_prob_pred（默认 0.6~0.8）

排序：按 `prob_suggested - prob_given` 从大到小。

优点：直观、误报相对少（偏精度）。  
缺点：只抓强信号，召回可能偏低。  

#### B) 主线：confident_learning（lite）
参考 confident learning/cleanlab 思想：基于 OOF 概率对每条样本打“标签质量”分数，并用剪枝策略控制候选集规模。

1) label quality score（可选项，默认 self_confidence）：
- `self_confidence = P_i[given]`（越低越可疑）
- `normalized_margin`、`confidence_weighted_entropy`（可选）

2) 强信号（confident_flip）：
- pred != given 且 prob_given <= threshold_prob_true 且 prob_suggested >= threshold_prob_pred

3) 剪枝策略（filter_by）：
- `prune_by_class`：每类取 bottom `ceil(fraction_noise * class_count)`（仅在 pred!=given 子集中选，降低边界样本误报）
- `prune_by_noise_rate`：用强信号比例估计类噪声率再分配 quota
- `both`：并集 + 强信号强制纳入（默认）
- `confident_learning`：仅输出强信号（更严格）

额外输出：
- `per_class_issue_rate`（按给定标签统计可疑比例）
- `confusion_pairs_top`（given→suggested 混淆方向 Top）

优点：覆盖更高（偏召回），诊断信息更丰富。  
缺点：对概率质量有依赖；需要合理的剪枝策略控制候选集规模。  

---

## 5. 工程实现要点

### 5.1 依赖与降级
依赖：`pandas/numpy/scikit-learn`  
当依赖缺失会返回明确 error，不影响其它模块执行（符合 dqscan 可降级原则）。

### 5.2 性能护栏
- `max_samples`：数据量过大时分层抽样，避免全量 CV 导致耗时过高
- `n_splits` 自适应：`min(configured_n_splits, min_class_count)`，不足则报错
- `max_categorical_cardinality`：自动剔除高基数类别列（防止 ID 记忆）

### 5.3 可解释输出（面向报告页）
每条 issue 携带 `row_preview`（字段→值），前端可直接以表格方式展示，并按 `issue_type` 高亮颜色。

### 5.4 “只勾选错标”为何会看到异常值相关显示（已修复）
因为错标检测属于 dirty_data 模块子检测项，报告页曾固定展示异常率等列。  
本轮修复：
- 引擎侧：当仅启用 `label_mismatch` 时覆盖 dirty_data 的 algorithm/统计字段
- 报告视图：按 `enabled_checks` 动态隐藏未勾选检测项的列与图表 series

---

## 6. 评估设计与实测表现

### 6.1 评估动机
公开数据集通常没有“真实错标”真值，因此采用**合成错标注入**来构建可计算指标的 ground truth。

### 6.2 数据集
为保证可复现且不依赖外网下载，选用 scikit-learn 内置数据（来源指向 UCI，许可 CC BY 4.0）：
- `breast_cancer`（二分类）
- `digits`（10 类）

### 6.3 指标
设 S 为算法输出可疑集合，G 为注入翻转集合：
- precision = |S∩G|/|S|
- recall = |S∩G|/|G|
- precision@k / recall@k（Top-k 复核更贴近真实用法）

### 6.4 结果摘要（一次运行记录）
完整表格见：`prompt/dqscan-label-mismatch-evaluation.md`。  
总体趋势：
- `confident_learning(lite)` 多数场景 **recall 更高**（候选覆盖更大）
- `cv_consistency` 候选更少、更严格，precision 往往更高
- Top-k（Top-10/Top-20）命中率通常较高，适合作为“优先复核列表”

---

## 7. 风险与限制（汇报必须明确）
- 候选集不等于真错标：边界样本/类别重叠/特征不足会引入不确定性
- 概率质量影响排序：基模型/特征弱时，错标排序质量会下降
- 极小类样本不足时无法做可靠 CV：会返回错误提示，需要先治理类分布

---

## 8. 使用建议与闭环
推荐默认：
- executor：`confident_learning`
- `filter_by=both`，`fraction_noise=0.03~0.10`
- 强信号阈值：`threshold_prob_true=0.2`，`threshold_prob_pred=0.6~0.8`

闭环建议：
1) dqscan 输出 Top-N 候选 → 人工复核/回标  
2) 修订标注规范/规则或补标  
3) 再跑 dqscan 观察 `label_mismatch_rate` 是否下降（作为数据治理 KPI）  

---

## 9. 代码与产物位置
- 扫描器：`dqscan/scanner/dirty_data_scanner/tabular/label_mismatch_scanner.py`
- 引擎编排：`dqscan/engine/algorithms/tabular/quality_engine.py`
- 评估脚本：`dqscan/benchmarks/label_mismatch_eval.py`
- 效果记录：`prompt/dqscan-label-mismatch-evaluation.md`
- 领导汇报版：`prompt/dqscan-label-mismatch-leadership-report.md`

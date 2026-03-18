# dqscan 评估：分类错标检测（dirty_data.label_mismatch）

## 1. 评估目标
验证 `dirty_data.label_mismatch` 在“分类 tabular 数据”上的**疑似错标候选集**质量：
- `cv_consistency`（兜底阈值法） vs `confident_learning`（lite）
- 关注：precision / recall、precision@k / recall@k、运行耗时

> 说明：公开数据集通常没有“真实错标”标注，因此采用**合成错标注入**作为 ground truth。

## 2. 开源数据集（来源 / 许可 / 获取方式）
为避免外网依赖，数据集选用 scikit-learn 内置数据（来源指向 UCI）：

1) Breast Cancer Wisconsin (Diagnostic)
- 来源：UCI Machine Learning Repository（id=17）
- 许可：CC BY 4.0
- 获取方式：`sklearn.datasets.load_breast_cancer(as_frame=True)`

2) Optical Recognition of Handwritten Digits（8×8 版本 / 子集）
- 来源：UCI Machine Learning Repository（id=80）
- 许可：CC BY 4.0
- 获取方式：`sklearn.datasets.load_digits()`

## 3. 评估方法

### 3.1 合成错标注入（ground truth）
对每个数据集：
- `uniform`：随机选择 `noise_fraction` 的样本，把标签替换为“任意其它类别”
- `class_conditional`：随机选择 `noise_fraction` 的样本，把标签替换为“固定映射到下一类”（c→c+1 mod K）

记录被 flip 的样本 index 作为 `ground truth mislabeled indices`，用于计算指标。

### 3.2 被测算法配置（与工程默认一致）
- `n_splits=5`（StratifiedKFold，out-of-fold `predict_proba`）
- `threshold_prob_true=0.2`
- `threshold_prob_pred=0.8`
- `confident_learning`：`score_method=self_confidence`、`filter_by=both`、`fraction_noise` 默认跟随注入比例（可通过脚本参数覆盖）

### 3.3 指标定义
设：
- `S`：算法输出的（按 score 排序的）疑似错标样本集合
- `G`：注入时 flip 的样本集合（ground truth）

则：
- `precision = |S ∩ G| / |S|`
- `recall = |S ∩ G| / |G|`
- `precision@k / recall@k`：按输出排序取 Top-k 计算（k ∈ {10,20,50,100,|G|}）

## 4. 复现实验脚本
脚本位置：`dqscan/benchmarks/label_mismatch_eval.py`

推荐运行方式（使用本项目 `.venv`）：
```bash
./.venv/bin/python dqscan/benchmarks/label_mismatch_eval.py
```

可选参数（示例）：
```bash
./.venv/bin/python dqscan/benchmarks/label_mismatch_eval.py \
  --datasets breast_cancer,digits \
  --noise-modes uniform,class_conditional \
  --noise-fractions 0.05,0.10 \
  --executors cv_consistency,confident_learning
```

## 5. 结果（本机一次运行记录）
环境（仅用于复现参考）：numpy=2.2.6, pandas=2.2.2, sklearn=1.5.2, scipy=1.14.1

> 备注：breast_cancer 是二分类，因此 `uniform` 与 `class_conditional` 等价，结果一致。

### 5.1 总体 precision / recall（按输出集合 S 统计）
| dataset | noise_mode | noise_fraction | algorithm | detected | precision | recall | time |
|---|---:|---:|---:|---:|---:|---:|---:|
| breast_cancer | uniform | 0.05 | cv_consistency | 22 | 0.682 | 0.536 | 0.15s |
| breast_cancer | uniform | 0.05 | confident_learning | 31 | 0.516 | 0.571 | 0.15s |
| breast_cancer | uniform | 0.10 | cv_consistency | 22 | 0.818 | 0.321 | 0.15s |
| breast_cancer | uniform | 0.10 | confident_learning | 41 | 0.805 | 0.589 | 0.15s |
| digits | uniform | 0.05 | cv_consistency | 114 | 0.649 | 0.831 | 5.55s |
| digits | uniform | 0.05 | confident_learning | 138 | 0.609 | 0.944 | 5.40s |
| digits | uniform | 0.10 | cv_consistency | 127 | 0.882 | 0.626 | 5.98s |
| digits | uniform | 0.10 | confident_learning | 197 | 0.843 | 0.927 | 5.38s |
| digits | class_conditional | 0.05 | cv_consistency | 118 | 0.636 | 0.843 | 5.02s |
| digits | class_conditional | 0.05 | confident_learning | 140 | 0.571 | 0.899 | 4.73s |
| digits | class_conditional | 0.10 | cv_consistency | 165 | 0.727 | 0.670 | 5.65s |
| digits | class_conditional | 0.10 | confident_learning | 223 | 0.632 | 0.788 | 5.98s |

### 5.2 Top-k（代表性结论）
- `digits` 上 Top-10/Top-20 通常 precision 很高（多数组合达到 100%），说明 **ranking 的头部质量很好**，适合产品化做“优先复核列表”。
- `confident_learning` 相对 `cv_consistency` 在多数设置下 **recall 更高**（候选更多），但往往以 **precision 略下降**为代价。

## 6. 结论与建议（工程默认的合理性）
1) 默认 `executor_algorithm=confident_learning` 是合理的：更偏 recall，能覆盖更多潜在错标候选；并且仍保留 `cv_consistency` 作为更严格（偏精度）的兜底。
2) 如果用户更关注“少量高确信错标”：建议用 `cv_consistency` 或在 `confident_learning` 下设 `filter_by=confident_learning`（只保留高置信冲突）。
3) 如果表很大/时延敏感：降低 `n_splits` 或设置 `max_samples` 分层抽样；必要时可扩展更快的模型（如线性 SVM 概率校准、朴素贝叶斯等）作为替代基模型。

## 7. 局限
- 合成错标只覆盖“标签翻转”这一类噪声；真实业务中错标常伴随分布偏移、弱标注、边界样本等，评估结果仅作快速 sanity check。
- 当前基模型为 LogisticRegression（OOF），概率校准质量会影响排序；后续可考虑补充校准（Platt/Isotonic）或引入可选的 cleanlab 增强。


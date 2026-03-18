# 群内进展汇报（可直接复制粘贴）

各位好，汇报 dqscan 本轮“分类标签错标检测（dirty_data.label_mismatch）”进展（案例 / 算法实现 / 效果评估）：

1) 案例/使用场景  
- 面向结构化表格分类数据，识别“特征与给定标签明显不一致”的样本，输出 Top-N **人工复核候选集**（非自动纠错）。  
- 报告页可直接看到被标记样本的字段预览，并按问题类型配色高亮，便于复核定位。

2) 算法实现（两档可切换）  
- 兜底算法：`cv_consistency`（交叉验证 OOF 概率 + 高置信冲突阈值）  
- 高级算法：`confident_learning(lite)`（label quality score + 按类剪枝 + 混淆方向统计）  
- 关键点：使用 **out-of-fold 概率矩阵**避免训练集记忆导致漏检；支持大表 `max_samples` 护栏与高基数字段过滤。

3) 效果评估（可复现）  
- 数据集：sklearn 内置 `breast_cancer` / `digits`（来源 UCI，许可 CC BY 4.0）  
- 方法：合成错标注入（uniform / class-conditional）构造 ground truth  
- 指标：precision/recall + precision@k/recall@k + 耗时  
- 结论摘要：`confident_learning` 多数场景 recall 更高，`cv_consistency` 更严格偏精度；Top-k（Top-10/20）命中率通常较高，适合作为“优先复核列表”。

4) 端到端进展  
- 前端：缺陷树勾选 + 参数面板（强制 `label_column`）+ 报告视图 issues 表格/样本预览表展示（按类型配色）  
- 后端/引擎：任务执行、result.json/reports 产物、错标 issues 写入 row_preview 供前端展示  
- 体验修复：仅勾选错标时，报告页不会再误导展示“异常值检测”相关列/图表

文档与复现入口：  
- 设计文档：`prompt/dqscan-label-mismatch-design-doc.md`  
- 领导汇报版：`prompt/dqscan-label-mismatch-leadership-report.md`  
- 评估结果：`prompt/dqscan-label-mismatch-evaluation.md`（脚本：`dqscan/benchmarks/label_mismatch_eval.py`）  
- PPT 内容稿：`prompt/dqscan-label-mismatch-ppt.md`

如需我补一版“更贴近业务表格字段”的案例页/截图页，请直接 @ 我（需要一份脱敏样例或字段口径）。


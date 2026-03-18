# Label Mismatch 展示重设计 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 移除标签错误检测的 Top-N 优先级截断（上限提升至 500），并在前端新增专用的"原始标签 → 建议标签"展示表格。

**Architecture:** 后端将 `max_examples` 默认值从 50 升至 500，去除 `issues[:50]` 截断；前端将 label_mismatch issues 从通用表格中分离出来，单独渲染专用表格，列为：样本ID | 原始标签 | 建议标签 | 原始置信度 | 预测置信度 | 严重度。

**Tech Stack:** Python（FastAPI/dqscan）, Vue 3 + Element Plus

---

### Task 1: 后端 - 提升 label_mismatch_scanner 默认上限

**Files:**
- Modify: `dqscan/scanner/dirty_data_scanner/tabular/label_mismatch_scanner.py:83`

**Step 1: 修改 scan() 方法的 max_examples 默认值**

将 `scan()` 签名第 4 个参数从 50 改为 500：

```python
# 原来
def scan(
    self,
    data: Any,
    *,
    label_column: str,
    exclude_columns: Optional[list[str]] = None,
    max_examples: int = 50,
) -> dict[str, Any]:

# 改为
def scan(
    self,
    data: Any,
    *,
    label_column: str,
    exclude_columns: Optional[list[str]] = None,
    max_examples: int = 500,
) -> dict[str, Any]:
```

**Step 2: 验证内部保护逻辑已支持 500**

确认两个检测方法中的保护行（无需修改，确认即可）：
- `_detect_cv_consistency`：`max_examples = int(max(10, min(int(max_examples or 50), 500)))`
- `_detect_confident_learning`：同上

这两行已将上限固定在 500，改变默认值后不需要额外修改。

**Step 3: Commit**

```bash
git add dqscan/scanner/dirty_data_scanner/tabular/label_mismatch_scanner.py
git commit -m "feat: raise label_mismatch_scanner max_examples default to 500"
```

---

### Task 2: 后端 - 修复 quality_engine 中的截断逻辑

**Files:**
- Modify: `dqscan/engine/algorithms/tabular/quality_engine.py`

需要修改两处：

**Step 1: 修改 lm_max_examples 兜底值（约第 267-269 行）**

```python
# 原来
lm_max_examples = lm_params.get("max_examples") or lm_cfg.get("max_examples") or dirty_cfg.get(
    "max_examples", report_cfg.get("max_examples", 50)
)

# 改为
lm_max_examples = lm_params.get("max_examples") or lm_cfg.get("max_examples") or dirty_cfg.get(
    "max_examples", report_cfg.get("max_examples", 500)
)
```

**Step 2: 修改 defect_results 中 label_mismatch 的 issues 截断（约第 669 行）**

定位到 `elif defect_key == "dirty_data.label_mismatch":` 分支内的：

```python
# 原来
issues = lm.get("detailed_issues") if isinstance(lm.get("detailed_issues"), list) else []

# 该行本身没有截断，但紧接着 base.update 里有 issues[:50]
# 找到 base.update 部分（约第 713-719 行）：
base.update(
    {
        "status": "SUCCESS",
        "metrics": metrics,
        "issues": issues[:50],   # ← 这里
    }
)
```

将该通用的 `issues[:50]` 改为根据 defect_key 区分：

```python
# 改为（仅 label_mismatch 用 500，其余保持 50）
issue_limit = 500 if defect_key == "dirty_data.label_mismatch" else 50
base.update(
    {
        "status": "SUCCESS",
        "metrics": metrics,
        "issues": issues[:issue_limit],
    }
)
```

**Step 3: Commit**

```bash
git add dqscan/engine/algorithms/tabular/quality_engine.py
git commit -m "feat: raise label_mismatch issue limit to 500 in quality_engine"
```

---

### Task 3: 前端 - 修改 labelMismatchMaxExamples 默认值

**Files:**
- Modify: `frontend/src/views/module_application/dqscan/index.vue:3611`

**Step 1: 找到并修改初始化行**

```typescript
// 原来（约第 3611 行）
const labelMismatchMaxExamples = ref(50);

// 改为
const labelMismatchMaxExamples = ref(500);
```

同时找到重置逻辑（约第 3804 行）：
```typescript
// 原来
labelMismatchMaxExamples.value = 50;

// 改为
labelMismatchMaxExamples.value = 500;
```

**Step 2: Commit**

```bash
git add frontend/src/views/module_application/dqscan/index.vue
git commit -m "feat: raise labelMismatchMaxExamples default to 500"
```

---

### Task 4: 前端 - 在 reportDetailItems 中提取 labelMismatchIssues

**Files:**
- Modify: `frontend/src/views/module_application/dqscan/index.vue` (~line 4704-4768)

**Step 1: 修改 normalizedIssues 计算逻辑**

定位到约第 4704-4768 行的 `reportDetailItems` computed 中处理 issues 的部分，进行如下改造：

```typescript
// 原来（约第 4707-4733 行）
const issues = fullIssues || (Array.isArray(dtResult.detailed_issues) ? dtResult.detailed_issues : []);
const normalizedIssues = issues.slice(0, 50).map((it: any) => ({
  issue_type: String(it?.issue_type ?? "未知"),
  data_id: String(it?.data_id ?? "-"),
  severity: String(it?.severity ?? "-"),
  detailsText: issueDetailsText(it?.details),
  issue_kind: issueKindFromType(it?.issue_type),
  row_preview: (() => { ... })(),
  previewRows: (() => { ... })(),
}));

// 改为
const allRawIssues = fullIssues || (Array.isArray(dtResult.detailed_issues) ? dtResult.detailed_issues : []);
const lmRaw = allRawIssues.filter((it: any) => issueKindFromType(it?.issue_type) === "label_mismatch");
const otherRaw = allRawIssues.filter((it: any) => issueKindFromType(it?.issue_type) !== "label_mismatch");

const normalizedIssues = otherRaw.slice(0, 50).map((it: any) => ({
  issue_type: String(it?.issue_type ?? "未知"),
  data_id: String(it?.data_id ?? "-"),
  severity: String(it?.severity ?? "-"),
  detailsText: issueDetailsText(it?.details),
  issue_kind: issueKindFromType(it?.issue_type),
  row_preview: (() => {
    const rp = it?.details?.row_preview;
    if (!rp || typeof rp !== "object" || Array.isArray(rp)) return null;
    return rp as Record<string, any>;
  })(),
  previewRows: (() => {
    const rp = it?.details?.row_preview;
    if (!rp || typeof rp !== "object") return [];
    try {
      return Object.entries(rp)
        .slice(0, 30)
        .map(([k, v]) => ({
          field: String(k),
          value: typeof v === "object" ? JSON.stringify(v) : String(v),
        }));
    } catch {
      return [];
    }
  })(),
}));

// label_mismatch 专用列表
const labelMismatchIssues = lmRaw.slice(0, 500).map((it: any) => ({
  data_id: String(it?.data_id ?? "-"),
  given_label: String(it?.details?.given_label ?? "-"),
  suggested_label: String(it?.details?.suggested_label ?? "-"),
  prob_given: `${(Number(it?.details?.prob_given ?? 0) * 100).toFixed(1)}%`,
  prob_suggested: `${(Number(it?.details?.prob_suggested ?? 0) * 100).toFixed(1)}%`,
  severity: String(it?.severity ?? "-"),
  previewRows: (() => {
    const rp = it?.details?.row_preview;
    if (!rp || typeof rp !== "object") return [];
    try {
      return Object.entries(rp)
        .slice(0, 30)
        .map(([k, v]) => ({
          field: String(k),
          value: typeof v === "object" ? JSON.stringify(v) : String(v),
        }));
    } catch {
      return [];
    }
  })(),
}));
```

**Step 2: 修改 sampleRows 过滤，去掉 label_mismatch（因为它有专用表格了）**

```typescript
// 原来（约第 4735-4743 行）
const sampleRows = normalizedIssues
  .filter((x: any) => x?.row_preview && ["anomaly", "duplicate", "label_mismatch"].includes(x.issue_kind))
  .slice(0, 20)
  ...

// 改为（去掉 label_mismatch）
const sampleRows = normalizedIssues
  .filter((x: any) => x?.row_preview && ["anomaly", "duplicate"].includes(x.issue_kind))
  .slice(0, 20)
  ...
```

**Step 3: 在 return 对象中增加 labelMismatchIssues 字段**

```typescript
// 原来（约第 4754-4766 行）
return {
  dataTypeKey: dt,
  dataTypeLabel: dataTypeLabel(dt),
  algorithm: String(dtResult.algorithm || "N/A"),
  hasIssues: !!dtResult.has_issues,
  totalIssues: Number(dtResult.total_issues ?? 0),
  issuePercentage: `${(Number(dtResult.issue_percentage ?? 0) * 100).toFixed(2)}%`,
  score: Number.isFinite(score) ? Number(score.toFixed(0)) : 0,
  extraMetrics,
  sampleRows,
  sampleColumns,
  issues: normalizedIssues,
};

// 改为（新增 labelMismatchIssues）
return {
  dataTypeKey: dt,
  dataTypeLabel: dataTypeLabel(dt),
  algorithm: String(dtResult.algorithm || "N/A"),
  hasIssues: !!dtResult.has_issues,
  totalIssues: Number(dtResult.total_issues ?? 0),
  issuePercentage: `${(Number(dtResult.issue_percentage ?? 0) * 100).toFixed(2)}%`,
  score: Number.isFinite(score) ? Number(score.toFixed(0)) : 0,
  extraMetrics,
  sampleRows,
  sampleColumns,
  issues: normalizedIssues,
  labelMismatchIssues,
};
```

**Step 4: Commit**

```bash
git add frontend/src/views/module_application/dqscan/index.vue
git commit -m "feat: extract labelMismatchIssues for dedicated display"
```

---

### Task 5: 前端 - 在模板中添加专用标签错误表格

**Files:**
- Modify: `frontend/src/views/module_application/dqscan/index.vue` (~line 2088)

**Step 1: 定位插入位置**

找到约第 2088 行，`<el-table v-if="d.issues.length"` 的 issues 通用表格之前，紧接 `</el-descriptions>` 之后插入以下代码块：

```vue
<!-- 疑似错标专用展示区 -->
<template v-if="d.labelMismatchIssues?.length">
  <div class="flex items-center gap-2 mt-3 mb-2">
    <span class="font-bold">疑似错标清单</span>
    <el-tag type="warning" effect="plain" size="small">
      共 {{ d.labelMismatchIssues.length }} 条
    </el-tag>
  </div>
  <el-table
    :data="d.labelMismatchIssues"
    border
    size="small"
    class="dqscan-issue-table"
  >
    <el-table-column type="expand" width="42">
      <template #default="{ row }">
        <div class="p-2">
          <el-table v-if="row.previewRows?.length" :data="row.previewRows" border size="small">
            <el-table-column prop="field" label="字段" min-width="180" />
            <el-table-column prop="value" label="值" min-width="220" />
          </el-table>
          <el-empty v-else description="暂无样本预览" />
        </div>
      </template>
    </el-table-column>
    <el-table-column prop="data_id" label="样本 ID" width="130">
      <template #default="{ row }">
        <span class="font-mono text-xs">{{ row.data_id }}</span>
      </template>
    </el-table-column>
    <el-table-column label="原始标签" width="150">
      <template #default="{ row }">
        <el-tag size="small" type="danger" effect="plain">{{ row.given_label }}</el-tag>
      </template>
    </el-table-column>
    <el-table-column label="" width="36">
      <template #default>
        <span class="text-gray text-xs">→</span>
      </template>
    </el-table-column>
    <el-table-column label="建议标签" width="150">
      <template #default="{ row }">
        <el-tag size="small" type="success" effect="plain">{{ row.suggested_label }}</el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="prob_given" label="原始置信度" width="100" />
    <el-table-column prop="prob_suggested" label="预测置信度" width="100" />
    <el-table-column prop="severity" label="严重度" width="90">
      <template #default="{ row }">
        <el-tag size="small" effect="plain" :type="severityTagType(row.severity)">{{ row.severity }}</el-tag>
      </template>
    </el-table-column>
  </el-table>
</template>
```

**Step 2: Commit**

```bash
git add frontend/src/views/module_application/dqscan/index.vue
git commit -m "feat: add dedicated label_mismatch table with given→suggested label display"
```

---

### Task 6: 验证

**Step 1: 启动后端，运行一次标签检测**

确认 `result.json` 中 `label_mismatch.detailed_issues` 的条数达到 500（或全部检测到的数量）。

**Step 2: 打开前端，检查结果页面**

- "2. 检测详情" 区域内，疑似错标清单应独立展示，不在通用 issues 表格中
- 表格列：样本ID | 原始标签 | → | 建议标签 | 原始置信度 | 预测置信度 | 严重度
- 展开行可看到原始字段值

**Step 3: 最终 commit（如有遗漏）**

```bash
git add -p
git commit -m "feat: label_mismatch show all detected errors with dedicated table"
```

---

## 变更文件汇总

| 文件 | 改动类型 | 改动行数（估算） |
|------|----------|-----------------|
| `dqscan/scanner/dirty_data_scanner/tabular/label_mismatch_scanner.py` | 修改 | 1 行 |
| `dqscan/engine/algorithms/tabular/quality_engine.py` | 修改 | 3 行 |
| `frontend/src/views/module_application/dqscan/index.vue` | 修改 + 新增 | ~80 行 |

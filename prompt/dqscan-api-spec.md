# dqscan 后端接口草案（Defect Catalog + Task Runner）

本文档用于把 dqscan 的“缺陷体系树 + 缺陷配置”前端形态，落到可实现/可扩展的后端接口协议上，便于后续补齐能力与联调。

说明：
- 当前仓库已实现 dqscan 的任务闭环（上传→建任务→WS→结果→报告/下载），见 `prompt/dqscan-integration.md`。
- 本文档在不破坏现有接口的前提下，给出 **新增缺陷 catalog** 与 **defects 结构化入参** 的约定。

---

## 1. 关键概念

### 1.1 模态（modality）

- `tabular`：CSV/TXT 表格
- `text` / `image` / `timeseries`：后续扩展

### 1.2 模块（module_key）

固定枚举：
- `dirty_data`：脏数据
- `distribution`：分布偏差
- `adversarial`：对抗性
- `physics`：物理保真度

### 1.3 缺陷（defect_key）

建议命名规则：`{module_key}.{defect_name}`，例如：
- `dirty_data.missing`
- `dirty_data.label_mismatch`
- `distribution.numeric_drift`

---

## 2. 现有接口（已实现）

### 2.1 获取算法列表

- `GET /api/v1/application/dqscan/algorithms`

响应（示例）：
```json
{
  "code": 200,
  "msg": "success",
  "data": [
    {
      "name": "tabular_quality_engine",
      "label": "表格数据质量探测引擎",
      "description": "脏数据扫描 / 分布偏差 / 对抗性 / 物理保真度，生成 JSON 摘要与 Word 报告。",
      "params_schema": {}
    }
  ],
  "success": true
}
```

### 2.2 上传文件

- `POST /api/v1/application/dqscan/upload`（multipart/form-data）

响应：
```json
{
  "data": { "file_id": "uploads/xxx.csv", "filename": "xxx.csv", "file_size": 12345 }
}
```

### 2.3 创建任务

- `POST /api/v1/application/dqscan/tasks`

请求（当前已支持）：
```json
{
  "file_id": "uploads/current.csv",
  "baseline_file_id": "uploads/baseline.csv",
  "algorithm": "tabular_quality_engine",
  "params": {
    "modules": ["dirty_data", "distribution", "adversarial", "physics"],
    "train_test_split": 0.7,
    "p_val": 0.05,
    "exclude_columns": ["id"],
    "contamination": 0.1,
    "adversarial": { "epsilon": 0.05, "max_iter": 20 },
    "physics": { "check_conservation": false, "constraints": {} }
  }
}
```

响应：
```json
{ "data": { "task_id": "dqscan_20260101_xxx" } }
```

### 2.4 查询任务状态

- `GET /api/v1/application/dqscan/tasks/{task_id}`

### 2.5 获取结果

- `GET /api/v1/application/dqscan/tasks/{task_id}/result`

### 2.6 下载结果 JSON

- `GET /api/v1/application/dqscan/tasks/{task_id}/download`

### 2.7 下载任务产物（docx/json/summary）

- `GET /api/v1/application/dqscan/tasks/{task_id}/artifact?path=reports/...`

### 2.8 获取报告（JSON/summary）

- `GET /api/v1/application/dqscan/tasks/{task_id}/report?report_type=json|summary&module=dirty_data|distribution|adversarial|physics`

### 2.9 WebSocket（日志/进度）

- `WS /api/v1/application/dqscan/ws/{task_id}`

---

## 3. 新增接口：缺陷体系 Catalog（建议新增）

目的：前端渲染“缺陷树 + 参数表单 + 算法选择”所需的元数据，避免前端硬编码。

### 3.1 获取缺陷树

- `GET /api/v1/application/dqscan/defects?modality=tabular&engine=tabular_quality_engine`

响应建议：
```json
{
  "data": {
    "modality": "tabular",
    "engine": "tabular_quality_engine",
    "tree": [
      {
        "key": "dirty_data",
        "label": "脏数据体系",
        "desc": "完整性 / 一致性 / 异常与噪声 / 标注质量",
        "children": [
          {
            "key": "dirty_data.missing",
            "label": "缺失值异常",
            "status": "ready",
            "algorithms": [
              { "key": "missing_stats_threshold", "label": "缺失统计 + 阈值", "status": "ready" }
            ],
            "params_schema": { "type": "object", "properties": { "missing_threshold": { "type": "number" } } }
          }
        ]
      }
    ]
  }
}
```

字段约定：
- `status`: `ready | planned`（planned 用于展示但默认不可执行）
- `algorithms[]`: 每个缺陷可选择的算法清单（同样带 `status`）
- `params_schema`: JSON Schema，用于驱动前端动态表单（可选；短期可先由前端静态表单实现）

---

## 4. 创建任务入参扩展：模块级算法 + 缺陷绑定（建议新增，向后兼容）

### 4.1 模块级算法：params.module_algorithms（建议）

前端页面按“模块”选择算法，再把“缺陷 → 执行算法”做绑定编排。这样可以表达：
- 一个算法覆盖多个缺陷（例如一个脏数据扫描器可同时输出“缺失/重复/值域/异常”等信号）
- 多个缺陷复用同一个算法（避免重复计算）
- 同一模块可同时启用多个算法（例如“通用扫描器 + 专项检测”）

建议新增字段：
```json
{
  "module_algorithms": {
    "dirty_data": ["ecod_3sigma", "missing_stats_threshold", "exact_duplicate", "sigma_rule"],
    "distribution": ["mmd_ks_chi2"],
    "adversarial": ["zoo_or_random"],
    "physics": ["pandera_or_fallback", "cross_constraints"]
  },
  "module_algorithms_runtime": {
    "dirty_data": ["ecod_3sigma", "missing_stats_threshold", "exact_duplicate", "sigma_rule"],
    "distribution": ["mmd_ks_chi2"],
    "adversarial": ["zoo_or_random"],
    "physics": ["pandera_or_fallback", "cross_constraints"]
  },
  "module_algorithms_skipped": {
    "dirty_data": [],
    "distribution": [],
    "adversarial": [],
    "physics": []
  }
}
```

说明：
- `module_algorithms`：前端“选择了哪些算法”的原始配置（用于回放/审计/报告解释）。
- `module_algorithms_runtime`：后端实际执行的算法集合（过滤掉 `planned` 等不可执行能力）。
- `module_algorithms_skipped`：被跳过的算法集合（可选，用于解释）。

---

### 4.2 缺陷绑定：params.defects（建议）

`params.defects` 用于结构化描述“选了哪些缺陷、每个缺陷绑定哪个执行算法、参数是什么”：
```json
{
  "defects": {
    "preset": "balanced",
    "global": { "max_samples": 20000, "parallelism": 2, "seed": 42 },
    "report": { "docx": true, "summary": true, "max_examples": 50 },
    "algorithms_config": { "psi_bins": 10, "pgd_steps": 20 },
    "selected": {
      "dirty_data.missing": {
        "enabled": true,
        "status": "ready",
        "module": "dirty_data",
        "algorithms": ["missing_stats_threshold"],
        "algorithms_runtime": ["missing_stats_threshold"],
        "algorithms_skipped": [],
        "executor_algorithm": "missing_stats_threshold",
        "executor_runtime": "missing_stats_threshold",
        "params": { "missing_threshold": 0.1 }
      },
      "dirty_data.label_mismatch": {
        "enabled": true,
        "status": "planned",
        "module": "dirty_data",
        "algorithms": [],
        "algorithms_runtime": [],
        "algorithms_skipped": [],
        "executor_algorithm": null,
        "executor_runtime": null,
        "params": { "label_column": "label", "confidence": 0.8 }
      }
    }
  }
}
```

兼容策略（建议）：
- 后端先保持对旧字段（`modules/train_test_split/p_val/...`）的兼容；
- 若 `params.defects` 存在，则：
  - 用 `selected` 推导 `modules`（或与 `modules` 取交集）；
  - 对 `status=planned` 的缺陷：直接跳过执行，但可写入 result 的 `skipped` 列表，便于解释。

---

### 4.3 参数分层（建议：与前端交互一致）

为了配合前端“基础参数 vs 算法参数”的分层交互，建议后端把参数按层级拆开存储/解析：

- **模块基础参数**（与具体算法无关）：建议放到 `params.modules_config.{module_key}`
  - 例：`distribution.compare_mode / distribution.train_test_split / distribution.exclude_columns`
- **算法额外参数**（随算法变化）：建议放到 `params.algorithms_config.{algo_key}`
  - 例：`mmd_ks_chi2.p_val`、`ecod_3sigma.contamination`
- **缺陷级参数**（只对某个 defect 生效）：放到 `params.defects.selected.{defect_key}.params`
  - 例：`distribution.label_shift.label_column`

示例（片段）：
```json
{
  "params": {
    "modules_config": {
      "distribution": {
        "compare_mode": "baseline_file",
        "train_test_split": 0.7,
        "exclude_columns": ["id"]
      }
    },
    "algorithms_config": {
      "mmd_ks_chi2": { "p_val": 0.05 },
      "ecod_3sigma": { "contamination": 0.1 }
    },
    "defects": {
      "selected": {
        "distribution.label_shift": {
          "executor_algorithm": "mmd_ks_chi2",
          "params": { "label_column": "label" }
        }
      }
    }
  }
}
```

校验建议（可选）：
- 当 `distribution.compare_mode = baseline_file` 时要求 `baseline_file_id` 必填；
- 当启用 `distribution.label_shift` 时要求 `label_column` 必填。

---

## 5. 结果结构扩展（建议新增 defects 维度）

现有 `result.json` 已包含 `summary/modules/reports`。建议新增：

```json
{
  "summary": {},
  "modules": {},
  "defects": {
    "dirty_data.missing": { "status": "SUCCESS", "metrics": {}, "issues": [], "report_paths": {} },
    "dirty_data.label_mismatch": { "status": "SKIPPED", "reason": "planned" }
  },
  "reports": {}
}
```

好处：
- 前端可以按“缺陷”维度展示更细粒度的结果与追溯；
- 模块仍然可以保留聚合摘要，兼容旧报告视图。

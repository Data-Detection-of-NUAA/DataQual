# Audit模块重构计划

根据项目开发规范，对audit模块进行结构调整。

## 一、当前结构分析

### 1.1 后端模块结构（✅ 基本符合规范）

当前结构：
```
backend/app/plugin/module_application/audit/
├── task/           # 审计任务子模块
│   ├── controller.py  ✅
│   ├── schema.py      ✅
│   ├── service.py     ✅
│   ├── crud.py        ✅（按需增加）
│   └── model.py       ✅（按需增加）
├── rule/           # 审计规则子模块
│   ├── controller.py  ✅
│   ├── schema.py      ✅
│   ├── service.py     ✅
│   ├── crud.py        ✅
│   └── model.py       ✅
├── regulation/     # 法规管理子模块
│   ├── controller.py  ✅
│   ├── schema.py      ✅
│   ├── service.py     ✅
│   ├── crud.py        ✅
│   └── model.py       ✅
├── rule_template/  # 规则模板子模块
│   ├── schema.py      ✅
│   ├── service.py     ✅
│   ├── crud.py        ✅
│   ├── model.py       ✅
│   └── controller.py  ❌ 缺失（已禁用：controller.py.disabled）
├── file/           # 文件管理
│   └── storage.py     ✅
└── engine/         # 核心算法引擎
    ├── audit_engine.py
    ├── ai_matcher.py
    ├── file_parser.py
    ├── content_detector.py
    └── ...
```

**评估**：结构基本符合规范，主要问题：
- ✅ 每个子模块都有必备三件套（controller/schema/service）
- ✅ 按需添加了 crud.py 和 model.py
- ❌ rule_template 模块缺少 controller.py（已禁用）
- ⚠️ 存在多个子模块（task/rule/regulation/rule_template），但规范建议一个算法模块对应一个后端插件

### 1.2 当前接口设计（❌ 不符合统一任务型接口规范）

**规范要求的统一接口**：
```
POST   /upload                     # 上传文件
POST   /tasks                      # 创建任务
GET    /tasks/{task_id}            # 查询任务状态/进度
GET    /tasks/{task_id}/result     # 获取结果
GET    /tasks/{task_id}/artifact   # 下载产物
GET    /tasks/{task_id}/report     # 报告视图
WS     /ws/{task_id}               # 实时日志/进度
```

**当前audit模块的接口**（分散在各子模块）：
```
# task子模块
POST   /audit/task/create                  # ❌ 应改为 POST /audit/tasks
GET    /audit/task/list                    # ⚠️ 列表接口，可保留
GET    /audit/task/detail/{id}             # ❌ 应改为 GET /audit/tasks/{id}
POST   /audit/task/{id}/upload-regulation  # ⚠️ 特殊步骤
POST   /audit/task/{id}/match-rules        # ⚠️ 特殊步骤
POST   /audit/task/{id}/confirm-rules      # ⚠️ 特殊步骤
POST   /audit/task/{id}/upload-dataset     # ❌ 应改为 POST /audit/upload
POST   /audit/task/{id}/execute            # ⚠️ 合并到创建任务
GET    /audit/task/{id}/result             # ✅ 符合规范
GET    /audit/task/{id}/errors             # ⚠️ 额外接口，可保留
GET    /audit/task/{id}/download-report    # ❌ 应改为 GET /audit/tasks/{id}/artifact

# rule子模块
POST   /audit/rule/create
GET    /audit/rule/list
GET    /audit/rule/detail/{id}
PUT    /audit/rule/update/{id}
DELETE /audit/rule/delete

# regulation子模块
POST   /audit/regulation/create
GET    /audit/regulation/list
...
```

**问题分析**：
1. ❌ 任务创建接口路径不统一（/task/create vs /tasks）
2. ❌ 文件上传分散在多个接口（upload-regulation, upload-dataset）
3. ❌ 下载接口路径不统一（download-report vs artifact）
4. ⚠️ audit模块的4步向导流程特殊，需要额外接口支持

### 1.3 前端结构（✅ 符合规范）

```
frontend/src/
├── views/module_application/audit/
│   ├── task/
│   │   ├── index.vue                      ✅ 主页面
│   │   ├── workflow.vue                   ✅ 向导页面
│   │   └── components/                    ✅ 页面私有组件
│   │       ├── StepRegulation.vue
│   │       ├── StepRuleSelect.vue
│   │       ├── StepDataset.vue
│   │       └── StepResult.vue
│   ├── rule/
│   │   └── index.vue
│   └── regulation/
│       └── index.vue
└── api/module_application/audit/
    ├── task.ts                            ✅ API封装
    ├── rule.ts                            ✅
    └── regulation.ts                      ✅
```

**评估**：前端结构完全符合规范

### 1.4 文件落盘目录（❌ 不符合规范）

**规范要求**：
```
backend/static/<模块名>/
├── uploads/                  # 上传文件
└── tasks/{task_id}/          # 任务产物
    ├── result.json
    ├── log.txt
    └── reports/
```

**当前audit模块**（需要检查代码确认）：
- 可能分散在多个位置
- 需要统一到 `backend/static/audit/`

---

## 二、重构方案

### 方案A：完全遵循规范（推荐用于新模块）

**优点**：
- 符合团队标准，易于维护
- 接口统一，前端可复用组件

**缺点**：
- 需要大幅重构现有接口
- 前端需要同步修改
- audit模块的4步向导流程特殊，难以完全套用标准接口

**不适用原因**：
audit模块已经开发完成，有4步向导的特殊业务流程（法规上传 → AI匹配 → 规则确认 → 数据审计），强行套用标准接口会破坏现有逻辑。

---

### 方案B：渐进式重构（推荐）⭐

在保持现有业务逻辑的前提下，逐步向规范靠拢：

#### 阶段1：接口路径对齐（不破坏现有功能）

**调整内容**：
1. 添加规范路径的别名路由，保留原有路径（向后兼容）
2. 逐步迁移前端调用到新路径

**具体调整**：
```python
# 新增规范路由（别名）
POST   /audit/tasks                        → 调用原有 create_task
GET    /audit/tasks/{task_id}              → 调用原有 get_task_detail
GET    /audit/tasks/{task_id}/result       → 调用原有 get_audit_result
GET    /audit/tasks/{task_id}/artifact     → 调用原有 download_report

# 保留原有路由（向后兼容）
POST   /audit/task/create
GET    /audit/task/detail/{id}
...

# 保留audit特有的4步向导接口
POST   /audit/tasks/{task_id}/upload-regulation
POST   /audit/tasks/{task_id}/use-regulation/{regulation_id}
POST   /audit/tasks/{task_id}/match-rules
POST   /audit/tasks/{task_id}/confirm-rules
POST   /audit/tasks/{task_id}/upload-dataset
POST   /audit/tasks/{task_id}/execute
```

#### 阶段2：统一文件上传接口

**新增通用上传接口**：
```python
POST /audit/upload
Body:
{
  "file_type": "regulation|dataset",
  "file": <binary>,
  "task_id": 123  # 可选
}
Response:
{
  "file_path": "...",
  "file_name": "...",
  "file_size": 12345
}
```

**保留原有专用上传接口**（内部调用通用接口）

#### 阶段3：rule_template启用controller

当前 `controller.py.disabled` 需要启用，提供完整的CRUD接口

#### 阶段4：统一落盘目录

将所有文件统一存储到：
```
backend/static/audit/
├── uploads/
│   ├── regulations/
│   └── datasets/
└── tasks/{task_id}/
    ├── result.json
    ├── audit_report.xlsx
    └── logs/
```

---

### 方案C：最小改动（保持现状）

仅修复明显问题：
1. 启用 rule_template 的 controller
2. 统一落盘目录
3. 添加文档说明audit模块的特殊性

**优点**：改动最小，风险低
**缺点**：不符合规范，长期维护成本高

---

## 三、推荐执行计划（方案B）

### Step 1: 添加规范别名路由（不破坏现有功能）✅

**修改文件**：`backend/app/plugin/module_application/audit/task/controller.py`

**改动内容**：
```python
# 新增规范路径（复用现有service）
@TaskRouter.post("/audit/tasks", summary="创建审计任务（规范路径）")
async def create_task_standard(...)  # 调用 create_task 的逻辑

@TaskRouter.get("/audit/tasks/{task_id}", summary="获取任务详情（规范路径）")
async def get_task_standard(...)  # 调用 get_task_detail 的逻辑

@TaskRouter.get("/audit/tasks/{task_id}/result", summary="获取结果（规范路径）")
async def get_result_standard(...)  # 调用 get_audit_result 的逻辑

@TaskRouter.get("/audit/tasks/{task_id}/artifact", summary="下载产物（规范路径）")
async def download_artifact(...)  # 调用 download_report 的逻辑
```

**前端**：暂不修改，保持调用原有接口

### Step 2: 启用 rule_template controller

**修改文件**：
1. 重命名 `controller.py.disabled` → `controller.py`
2. 修复可能的导入问题
3. 在 `__init__.py` 中导出路由

### Step 3: 统一落盘目录

**修改文件**：
1. `backend/app/plugin/module_application/audit/file/storage.py`
2. 所有涉及文件路径的 service

**统一路径**：
```python
AUDIT_BASE_DIR = "backend/static/audit"
UPLOADS_DIR = f"{AUDIT_BASE_DIR}/uploads"
TASKS_DIR = f"{AUDIT_BASE_DIR}/tasks"
```

### Step 4: 添加通用上传接口（可选）

**新增接口**：
```python
@TaskRouter.post("/audit/upload", summary="通用文件上传")
async def upload_file(...)
```

### Step 5: 前端API迁移（可选）

逐步将前端API调用迁移到规范路径：
```typescript
// 旧：POST /audit/task/create
// 新：POST /audit/tasks
```

### Step 6: 测试

- 测试新增的规范路由
- 测试原有路由是否正常工作
- 测试文件上传下载
- 测试4步向导流程

---

## 四、注意事项

### 4.1 audit模块的特殊性

audit模块不是典型的"一次性任务提交"模式，而是4步交互式向导：

```
Step 1: 上传法规 → AI分析
Step 2: 显示推荐规则 → 用户选择
Step 3: 上传数据集
Step 4: 执行审计 → 生成报告
```

这种业务流程需要保留特殊的接口，不能完全套用规范的"POST /tasks一次性提交"模式。

### 4.2 向后兼容

重构过程中必须保证：
1. 原有接口继续可用
2. 前端无需立即修改
3. 数据库表结构不变

### 4.3 规范的适用性

开发规范适用于"标准任务型算法模块"，但audit模块有以下特点：
- 多子模块（task/rule/regulation/rule_template）
- 交互式向导流程
- 需要独立的规则管理、法规管理页面

**建议**：在规范基础上，允许audit模块保留特殊接口，但尽量向规范路径靠拢。

---

## 五、执行优先级

### 高优先级（必须做）
1. ✅ 启用 rule_template controller
2. ✅ 统一落盘目录到 `backend/static/audit/`
3. ✅ 添加规范别名路由（`/audit/tasks`等）

### 中优先级（建议做）
4. 添加通用上传接口 `/audit/upload`
5. 添加文档说明audit模块的接口设计

### 低优先级（可选）
6. 前端API逐步迁移到规范路径
7. 移除向后兼容的旧接口（需要确认前端已完全迁移）

---

## 六、风险评估

| 风险 | 等级 | 缓解措施 |
|------|------|---------|
| 接口路径变更导致前端报错 | 中 | 保留旧接口，添加别名路由 |
| 文件路径变更导致历史数据丢失 | 高 | 数据迁移脚本 + 兼容旧路径读取 |
| rule_template启用后权限问题 | 低 | 配置默认权限 |
| 测试不充分导致隐藏bug | 中 | 完整的回归测试 |

---

## 七、总结

**当前audit模块的规范符合度**：
- 后端结构：85% ✅
- 前端结构：95% ✅
- 接口设计：60% ⚠️
- 落盘目录：未知 ❓

**推荐方案**：方案B（渐进式重构）

**核心原则**：
1. 保持audit模块的特殊业务流程
2. 尽量向规范靠拢（添加别名路由）
3. 不破坏现有功能（向后兼容）
4. 逐步迁移，降低风险

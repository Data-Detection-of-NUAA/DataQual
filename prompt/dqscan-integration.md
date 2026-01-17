# dqscan 集成说明（FastapiAdmin）

本文档描述“数据集质量探测引擎（dqscan）”在本仓库中的前后端集成位置、模块职责与调用方式，便于后续迭代与容器化拆分。

## 目标

- 算法引擎独立放在仓库根目录 `dqscan/`，未来可直接抽离成独立服务。
- 当前系统（FastAPI 后端 + Vue3 前端）作为“适配层 + UI”，实现：
  - CSV/TXT 表格数据（tabular）闭环；
  - 四大检测模块：分布偏差、脏数据、对抗性、物理保真度；
  - 任务执行（进度 + 实时日志 WebSocket）；
  - 结果展示与报告下载（JSON + DOCX）。

## 目录与文件（后端）

### FastAPI 适配层（插件模块）

位置：`backend/app/plugin/module_application/dqscan/`

- `backend/app/plugin/module_application/dqscan/controller.py`
  - HTTP API：
    - `GET /api/v1/application/dqscan/algorithms`：算法列表
    - `POST /api/v1/application/dqscan/upload`：上传 CSV/TXT（最大 500MB）
    - `POST /api/v1/application/dqscan/tasks`：创建任务
    - `GET /api/v1/application/dqscan/tasks/{task_id}`：查询任务状态/进度
    - `GET /api/v1/application/dqscan/tasks/{task_id}/result`：获取 `result.json`
    - `GET /api/v1/application/dqscan/tasks/{task_id}/download`：下载 `result.json`
    - `GET /api/v1/application/dqscan/tasks/{task_id}/artifact?path=...`：下载任务产物（如 docx/json 报告）
- `backend/app/plugin/module_application/dqscan/service.py`
  - 任务管理与落盘
  - 从仓库根目录 `dqscan/` 引擎包加载算法并执行（线程池 `asyncio.to_thread`）
  - WebSocket 事件广播（log/progress/done/error）
- `backend/app/plugin/module_application/dqscan/schema.py`
  - 请求/响应 Pydantic 模型（默认算法：`tabular_quality_engine_v3`）
- `backend/app/plugin/module_application/dqscan/ws.py`
  - WebSocket 路由（避免动态路由全局 RateLimiter 影响 WS 握手）

### 手动注册 WebSocket 路由

位置：`backend/app/plugin/init_app.py`

- 手动 `include_router` dqscan 的 WS 路由（使用 `WebSocketRateLimiter`），避免动态路由的 HTTP `RateLimiter` 依赖导致握手失败。
- 兼容外部探活：`GET /health`

### 任务落盘目录（不入库）

默认落盘在：`backend/static/dqscan/`

- `backend/static/dqscan/uploads/`：上传文件
- `backend/static/dqscan/tasks/{task_id}/`：
  - `result.json`：总结果（含四模块摘要 + 报告相对路径）
  - `log.txt`：运行日志
  - `reports/`：每模块 `json/summary/docx` 报告

这些目录已在 `.gitignore` 里忽略。

## 目录与文件（算法引擎）

位置：仓库根目录 `dqscan/`

### 算法注册与发现

- `dqscan/engine/registry.py`
  - 注册并列出可用算法（当前仅注册 `tabular_quality_engine_v3`）

### 表格质量探测引擎（V3：四模块）

- `dqscan/engine/algorithms/tabular/quality_engine_v3.py`
  - 算法名：`tabular_quality_engine_v3`
  - 输入：CSV/TXT 文件路径
  - 输出：写入 `output_dir/result.json`（会进行 numpy 类型转换，保证 JSON 可序列化）
  - 每个模块会生成报告到 `output_dir/reports/` 并在 `result.json` 中记录相对路径（供后端 artifact 下载）

### V3 复刻（扫描器 + 报告器）

位置：`dqscan/v3/`

- `dqscan/v3/scanner/*`：四大模块的表格扫描器（Tabular 版本）
- `dqscan/v3/reporters/*`：报告生成（JSON / summary / docx）

说明：
- `distribution` 与 `adversarial` 等依赖 `scipy` / `scikit-learn` 等库；
- `docx` 报告依赖 `python-docx`；
- `pyod` / `pandera` 未安装时会降级执行并在结果中返回 `warning/error` 字段。

## 目录与文件（前端）

### 页面

- `frontend/src/views/module_application/dqscan/index.vue`
  - 参考你提供的 demo 流程重做为 5 步（箭头步骤条）：
    1) 选择数据模态
    2) 上传文件
    3) 选择算法（四大模块勾选）
    4) 检测运行（进度 + WebSocket 实时日志，轮询兜底）
    5) 查看结果（每模块摘要 + 报告下载）

### API 封装

- `frontend/src/api/module_application/dqscan.ts`
  - 对应后端 dqscan API，包含 `downloadArtifact` 用于下载 docx/json 报告

### 路由（修复侧边栏样式）

- `frontend/src/router/index.ts`
  - dqscan 作为顶级 `Layout` 路由：`/dqscan/index`，保证左侧菜单布局正常。

## 运行与依赖

### 后端

- 启动：`cd backend && python main.py run --env=dev`
- 建议安装（用于完整四模块 + Word 报告）：
  - `scipy`、`scikit-learn`、`pyod`、`python-docx`、`pandera`
  - 已写入：`backend/requirements.txt`

### 前端

- `cd frontend && pnpm dev`
- 若当前环境无法联网获取 pnpm，可直接用已安装依赖运行（示例）：
  - `cd frontend && node node_modules/vite/bin/vite.js`


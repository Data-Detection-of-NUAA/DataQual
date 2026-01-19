# FastapiAdmin 学习路线（先看项目布局，再学语法）

这份文档按你的诉求组织：**先看整个项目怎么分层、文件怎么摆放**，再讲**后端 FastAPI/Python 基础语法**与**前端 Vue3/TS 基础**，最后你就能自然读懂 dqscan 这类新功能是怎么接入的。

---

## 1) 整体项目布局（你先建立“地图”）

> 你可以把它当成：后端服务 + 前端管理后台 + 一个可独立的算法引擎 + 部署脚本。

```
FastapiAdmin/
  backend/                 # 后端：FastAPI + 插件化模块 + DB/Redis/限流等
    main.py                # 后端启动入口（Typer CLI）：create_app() + uvicorn.run(...)
    app/
      config/              # 配置：settings（包含 ROOT_PATH=/api/v1 等）
      plugin/              # 插件系统（module_*）+ init_app（注册路由/中间件/静态文件/文档）
      core/                # 核心工具：动态路由发现 discover.py 等
      api/v1/              # 系统/监控等内置模块（不是 dqscan）
      common/              # 通用响应封装、枚举等
      utils/               # 工具函数
    static/                # 静态目录（静态文件挂载、上传/任务产物等）

  frontend/                # 前端：Vue3 + Vite + TypeScript + Element Plus
    vite.config.ts         # Vite 配置（dev 代理 /api/v1 -> 后端地址）
    src/
      utils/request.ts     # Axios 封装（baseURL、拦截器、错误处理）
      api/                 # 每个业务模块一个 API 文件（dqscan.ts 等）
      views/               # 页面（dqscan/index.vue 等）
      router/              # 路由表
      store/               # Pinia 状态管理（用户信息、token 等）

  dqscan/                  # 算法引擎（独立于 FastAPI，可抽成单独服务）
    engine/                # 算法注册/发现/统一接口（AlgorithmSpec + registry）
    scanner/               # 四模块扫描器（对外稳定导出）
    reporters/             # 报告生成器（对外稳定导出）

  devops/                  # 部署/运维脚本、说明
  prompt/                  # 你要求的说明文档（集成说明、代码阅读指南等）
```

你需要记住的最重要一句话：

> **backend 负责“HTTP/WS + 任务管理 + 落盘”，dqscan 负责“算法计算”，frontend 负责“页面交互”。**

---

## 2) 后端是怎么启动/注册路由的（从入口到接口）

### 2.1 启动入口：`backend/main.py`

- `create_app()` 会创建 `FastAPI(...)` 实例，并调用一系列注册函数：
  - `register_exceptions(app)`：统一异常处理
  - `register_middlewares(app)`：中间件
  - `register_routers(app)`：注册路由（核心！）
  - `register_files(app)`：挂载静态目录 `/static`
  - `reset_api_docs(app)`：自定义 docs/redoc 页面

对应代码：`backend/main.py:17`

### 2.2 路由注册：`backend/app/plugin/init_app.py`

这里做两件事：

1) **手动注册少量路由**（尤其是 WebSocket）  
例如 dqscan 的 WS：`backend/app/plugin/init_app.py:135`

2) **注册动态路由**：`get_dynamic_router()`  
它会扫描 `app.plugin/module_*/**/controller.py`，找到里面的 `APIRouter` 并 include 到应用里。

对应代码：`backend/app/plugin/init_app.py:137`

### 2.3 动态路由发现：`backend/app/core/discover.py`

核心规则：

- 扫描：`app.plugin/module_*/**/controller.py`
- 约定：顶级目录名 `module_xxx` 映射为前缀 `/<xxx>`
  - `module_application` → `/application`
  - `module_generator` → `/generator`
- controller.py 里定义的 `APIRouter`（例如 `DQScanRouter`）会被 include 到这个容器前缀下

对应代码：`backend/app/core/discover.py:23`

### 2.4 最终 URL 是怎么拼出来的（重要！）

以 dqscan 为例：

- 目录前缀（来自动态发现）：
  - `backend/app/plugin/module_application/...` → `/application`
- Router 前缀（APIRouter 的 prefix）：
  - `DQScanRouter = APIRouter(prefix="/dqscan", ...)` → `/dqscan`
- 路由路径（装饰器里的 path）：
  - `@DQScanRouter.get("/algorithms")` → `/algorithms`

所以最终路径是：

> `/application` + `/dqscan` + `/algorithms` = `/application/dqscan/algorithms`

另外，本项目把 `ROOT_PATH` 配成了 `/api/v1`（用于对外统一前缀），所以前端通常访问：

> `/api/v1/application/dqscan/algorithms`

配置位置：`backend/app/config/setting.py:44`

---

## 3) FastAPI / Python 基础语法（用项目里的代码来学）

你先掌握下面这些，就能读懂 80% 的后端代码。

### 3.1 `APIRouter` + 装饰器（定义接口）

典型写法（你项目里就长这样）：

- `DQScanRouter = APIRouter(prefix="/dqscan", tags=[...])`
- `@DQScanRouter.get("/algorithms", response_model=...)`
- `async def list_algorithms_controller() -> JSONResponse: ...`

看这里：`backend/app/plugin/module_application/dqscan/controller.py:37`

你只要记住：

> 装饰器 `@router.get/post/...` 就是在“登记接口”；函数名随便取，路径和方法最重要。

### 3.2 参数从哪里来（FastAPI 的核心规则）

同一个函数里，参数类型不同，来源也不同：

- Path 参数：`/tasks/{task_id}` → `task_id: str`
- Query 参数：`?path=...` → `path: str = Query(...)`
- Body（JSON）：`body: DQScanCreateTaskIn`（Pydantic 模型）
- 文件上传：`file: UploadFile`（multipart/form-data）

看这里：`backend/app/plugin/module_application/dqscan/controller.py:51`

### 3.3 Pydantic 模型（请求/响应的数据契约）

你可以把 `schema.py` 当成“接口字段说明书”：

- `DQScanCreateTaskIn` 定义请求体字段、默认值
- `TaskStatus = Literal[...]` 限定枚举值
- `Field(..., description="...")` 生成文档注释

看这里：`backend/app/plugin/module_application/dqscan/schema.py:22`

### 3.4 `async/await`（异步函数）

FastAPI 常用 `async def`，你会看到大量 `await ...`：

- `await DQScanService.upload(...)`
- `await websocket.accept()`

什么时候必须 `await`？

> 只要你调用的是“协程函数（async def）”或返回 awaitable，就必须 await。

### 3.5 为什么要 `asyncio.to_thread(...)`（别卡住服务）

算法扫描属于“重 CPU/IO”，直接在 `async def` 里跑会阻塞事件循环，导致所有请求变慢。

本项目做法：

- `_run_task` 是后台协程
- 真正的 `alg.run(...)` 丢给线程池：`await asyncio.to_thread(alg.run, ...)`

看这里：`backend/app/plugin/module_application/dqscan/service.py:372`

### 3.6 WebSocket 基础（实时推送）

后端 WebSocket 路由：

- `@WS_DQSCAN.websocket("/ws/{task_id}")`
- `await websocket.accept()`
- 持续 `send_text(...)`

看这里：`backend/app/plugin/module_application/dqscan/ws.py:17`

---

## 4) 前端基础（Vue3 + TS + Axios + Element Plus）

你先把下面这些学会，就能读懂 dqscan 页面。

### 4.1 Vite 环境变量 + 代理（为什么前端能访问 /api/v1）

- 请求 baseURL：`import.meta.env.VITE_APP_BASE_API`  
  看这里：`frontend/src/utils/request.ts:16`
- Vite dev 代理：把 `/api/v1` 代理到后端地址  
  看这里：`frontend/vite.config.ts:41`

### 4.2 Axios 封装（统一处理 token / 错误 / code）

`frontend/src/utils/request.ts` 做了三件事：

- 请求拦截器：自动加 `Authorization: Bearer <token>`（如果有 token）
- 响应拦截器：检查 `data.code`，不成功就弹框并 reject
- 下载文件：`responseType === "blob"` 直接返回二进制

看这里：`frontend/src/utils/request.ts:26`

### 4.3 TypeScript 基础（interface / type）

你会经常看到：

- `export interface DQScanTaskOut { ... }`：描述对象结构
- `export type DQScanTaskStatus = "PENDING" | ...`：联合类型（枚举感）

看这里：`frontend/src/api/module_application/dqscan.ts:9`

### 4.4 Vue3 Composition API（`<script setup>`）

页面状态几乎都长这样：

- `const activeStep = ref(0)`：一个可变状态
- `const progressStatus = computed(() => ...)`：派生状态
- `onMounted(() => loadAlgorithms())`：页面加载时执行

看这里：`frontend/src/views/module_application/dqscan/index.vue:287`

### 4.5 模板语法（你写页面离不开）

常见指令：

- `v-show="activeStep === 1"`：显示/隐藏
- `v-for="m in modules"`：循环渲染
- `:type="statusTagType"`：绑定属性
- `@click="startScan"`：绑定事件
- `v-model="selectedModules"`：双向绑定

看这里：`frontend/src/views/module_application/dqscan/index.vue:52`

### 4.6 WebSocket（前端实时日志）

浏览器端：

- `ws = new WebSocket(url)`
- `ws.onmessage = (evt) => { const msg = JSON.parse(evt.data) ... }`

看这里：`frontend/src/views/module_application/dqscan/index.vue:474`

---

## 5) 你接下来怎么学（我给你安排的“最短路径”）

按下面顺序走，成本最低、收获最大：

1) **读入口**：`backend/main.py`（知道服务怎么启动）
2) **读路由注册**：`backend/app/plugin/init_app.py`（知道路由怎么挂上去）
3) **读动态发现**：`backend/app/core/discover.py`（知道为啥 controller.py 会自动生效）
4) **读一个最简单 controller + schema**：先只看“参数怎么来、返回长啥样”
5) **读 request.ts**：知道前端为啥要求后端返回 `{code,msg,data}`
6) **读一个页面 index.vue**：只看 `ref/computed/onMounted/await API` 这条链路

做完以上 6 步，再去看 dqscan 的 service/engine 才不会迷路。

---

如果你希望我“边讲边带你读”，我会按第 1~6 步逐个文件推进，每次只讲 1 个概念 + 1 个对应代码片段，直到你能自己复述它在干什么。

# FastapiAdmin 集大成学习指南（按项目需求定制）

> 面向：**前端小白 / 刚上手 Vue3 + TS**，目标是**最快学会本项目需要的前端能力**，同时能理解后端接口如何配合（不要求你先精通算法/后端）。
>
> 本文整合了仓库内的文档与代码结构（`README.md`、`prompt/*`、`frontend/*`、`backend/*`），并把你提供的两套学习网站内容“映射到本项目要用到的技能点”，做成一条最短闭环的学习路径。

---

## 目录（建议按顺序读）

1) 项目目标（学到什么算会）  
2) 项目地图（目录与分层）  
3) 先跑起来（env / proxy / base）  
4) 两个学习网站“该看哪里”（按项目需求筛选）  
5) 本项目前端必会清单（Vue/TS/Axios/Router/Pinia/UI/样式）  
6) 本项目“标准开发三件套”（API + 页面 + 路由）模板  
7) 最短学习路径（按天/按阶段）  
8) dqscan 作为实战教材（上传/任务/WS/下载/渲染）  
9) 常见卡点与排错清单  
10) 你今天就能做的 3 件事

---

## 0. 先建立目标（你学到什么程度算“会了”）

你在这个项目里，前端要能完成的事情，基本就是下面 6 类（能做到就算会）：

1) **能跑起来项目**：本地启动前端 + 能通过代理访问后端 API  
2) **能看懂一个页面**：知道 `<template>` 显示什么、`<script setup>` 管什么状态、`<style>` 管什么样式  
3) **能调用后端接口**：会在 `frontend/src/api/*` 写 API 方法、会在页面里 `await` 调用并渲染  
4) **能做页面交互**：表单/上传/按钮/表格/弹窗/消息提示（Element Plus）  
5) **能理解路由与菜单**：会加一个新页面路由，能让它出现在系统里  
6) **能调试与定位问题**：能用浏览器 DevTools 看请求、看报错、看 WS、定位是哪一层出问题

> dqscan 页面已经覆盖了：上传、建任务、轮询、WebSocket、下载、渲染结果。学会读懂它，你就具备在本项目里开发业务页面的核心能力。

---

## 1. 项目地图（先知道每个目录负责什么）

来自 `README.md` 的工程结构 + 本仓库实际内容：

```
FastapiAdmin/
  backend/                 # 后端：FastAPI（提供 /api/v1/... 的 API + WS）
    main.py                # 启动入口：create_app() + uvicorn.run(...)
    app/
      config/              # 配置：ROOT_PATH=/api/v1 等
      core/                # 核心机制：动态路由发现 discover.py 等
      plugin/              # 插件化业务模块（module_*）+ init_app（注册路由/静态/文档）
      api/v1/              # 系统内置模块（用户、权限、监控等）
    static/                # 静态目录：/static 挂载、上传文件、任务产物等

  frontend/                # 前端：Vue3 + Vite + TS + Element Plus + Pinia + UnoCSS
    vite.config.ts         # Vite 配置（dev 代理 /api/v1 -> 后端）
    .env.*.example         # 环境变量示例（VITE_APP_BASE_API、WS端点等）
    src/
      utils/request.ts     # Axios 封装（baseURL、token、统一返回码、Blob下载）
      api/                 # API 封装层（每个模块一个文件，例如 dqscan.ts）
      views/               # 页面（每个模块一个目录/页面，例如 dqscan/index.vue）
      router/              # 路由（页面入口与 Layout）
      store/               # Pinia 状态（用户、权限、配置等）
      types/               # 全局类型（ApiResponse 等）

  dqscan/                  # 算法引擎（可独立，不依赖前端/后端框架）
  prompt/                  # 本仓库的“学习/集成/读代码”文档（你要求的）
```

你只要抓住一句话：

> **frontend 只负责“页面 + 调接口 + 交互”，backend 负责“接口 + 权限 + 落盘”，dqscan 负责“算法计算”。**

---

## 2. 先跑起来（你后面所有学习都依赖这一步）

### 2.1 前端怎么知道后端地址？

关键点在两处：

1) **请求 baseURL**：`frontend/src/utils/request.ts`  
它用 `import.meta.env.VITE_APP_BASE_API` 作为 axios 的 `baseURL`。

2) **Vite 开发代理**：`frontend/vite.config.ts`  
它把 `VITE_APP_BASE_API`（默认 `/api/v1`）代理到 `VITE_API_BASE_URL`（默认 `http://127.0.0.1:8001`）。

你在开发时看到前端请求 `/api/v1/...` 能成功，就是因为代理在起作用。

对应文件：
- 环境变量示例：`frontend/.env.development.example`
- Vite 代理：`frontend/vite.config.ts`
- Axios baseURL：`frontend/src/utils/request.ts`

### 2.2 为什么访问地址是 `/web`？

本项目 Vite 配置了 `base: "/web"`（生产部署的子路径），所以本地启动后访问通常是：

- `http://localhost:5180/web`

对应：`frontend/vite.config.ts:26`

> 你在本地访问 5180 端口，如果打开的是空白页或资源 404，第一件事就是检查你访问的路径是否带 `/web`。

---

## 3. 这两个学习网站你该看哪些部分（按“本项目需求”筛选）

你给的两个网站很好，但“全看完会很慢”。下面我按本项目的真实代码，把“必须学”筛出来，并告诉你学完要能做什么。

### 3.1 Vue3 工程化站（vue3.chengpeiquan.com）

你截图里左侧目录的推荐顺序（只看这些就够你在本项目开干）：

**A. 前端工程化入门教程**
1) `了解前端工程化`  
   你要学会：npm/pnpm 是什么、项目目录是什么、为什么要构建  
   对照本项目：`frontend/package.json`、`frontend/vite.config.ts`
2) `工程化的前期准备`  
   你要学会：Node 版本、包管理器、依赖安装、dev/build 的区别  
   对照本项目：`README.md` 的前端启动部分
3) `快速上手 TypeScript`  
   你要学会：interface/type、可选字段、联合类型、泛型  
   对照本项目：`frontend/src/api/module_application/dqscan.ts`、`frontend/src/types/global.d.ts`

**B. Vue3 入门教程**
1) `脚手架的升级与配置`  
   你要学会：Vite 基础概念、env、proxy、构建 base 路径  
   对照本项目：`frontend/vite.config.ts`、`frontend/.env.development.example`
2) `单组件的编写`（非常重要）  
   你要学会：SFC 结构、`<script setup>`、ref/computed、生命周期  
   对照本项目：`frontend/src/views/module_application/dqscan/index.vue`
3) `组件之间的通信`  
   你要学会：props / emit / v-model / slot（你做页面拆分会用到）
4) `路由的使用`  
   你要学会：路由表、懒加载 import、meta、Layout  
   对照本项目：`frontend/src/router/index.ts`
5) `全局状态的管理`  
   你要学会：Pinia 的 state/getters/actions、组件外使用 store  
   对照本项目：`frontend/src/store/modules/user.store.ts`
6) `插件的开发和使用`（了解即可）  
   你要学会：项目怎么组织通用能力（比如 request 封装、下载封装）
7) `高效开发`（了解即可）  
   你要学会：你现在不用背各种优化技巧，先学会“按项目习惯写代码”

> 你可以把 Vue3 工程化站当成“体系化目录”，每看完一个章节，就回到本项目对应文件里找同类写法，这样学得最快。

### 3.2 千古前端图文（web.qianguyihao.com）

你截图里左侧目录的推荐顺序（只学本项目用得到的“最小集”）：

1) `00-前端工具`  
   目标：会用浏览器 DevTools（Console/Network/Application），这是你排错的命根子
2) `01-HTML`  
   目标：认识标签、表单、文件上传的 input（虽然 Vue 里不直接写原生 input，但概念要有）
3) `02-CSS基础` + `03-CSS进阶`  
   目标：盒模型、Flex、Grid、响应式；能看懂你页面的布局为什么这样写  
   对照本项目：`frontend/src/views/module_application/dqscan/index.vue` 的样式区 + UnoCSS class
4) `04-JavaScript基础`  
   目标：变量/函数/对象/数组/条件/循环，能读懂页面逻辑
5) `05-JavaScript基础：ES6语法`（非常重要）  
   目标：import/export、解构、模板字符串、箭头函数、map/filter/reduce  
   对照本项目：`frontend/src/utils/request.ts`、`frontend/src/views/module_application/dqscan/index.vue`
6) `06-JavaScript基础：异步编程`（非常重要）  
   目标：Promise、async/await、try/catch，能读懂“调接口”的主流程
7) `08-前端基本功：CSS和DOM练习`（选看）  
   Vue 项目很少手写 DOM，但你要知道事件、冒泡、DOM 是啥（看一遍即可）

不用现在学：
- `09-移动Web开发`（本项目 web 端优先）
- `10-MySQL数据库`（你学前端暂时不需要）

---

## 4. 本项目“前端必会知识”清单（抽取出来，不走弯路）

下面是你写本项目页面时最常碰到的知识点，我按“你改 dqscan 能用到”的顺序排：

### 4.1 Vue3：你需要掌握到什么程度？

你不用一上来学全生态，只要先掌握这些：

1) **SFC 结构**：`<template>` / `<script setup>` / `<style>`  
2) **响应式**：`ref()`、`computed()`、`watch()`（先会前两个就能做大多数事）  
3) **生命周期**：`onMounted`、`onBeforeUnmount`（页面初始化/清理定时器/关闭WS）  
4) **模板指令**：`v-if/v-show/v-for`、`:prop`、`@event`、`v-model`  
5) **组件拆分思路**：大页面先能读懂，再学 props/emit 拆成多个子组件

练习入口：`frontend/src/views/module_application/dqscan/index.vue`

你可以用 dqscan 页面做“对照学习”，它已经涵盖了很多常用模式：
- `ref/computed`：页面状态与派生状态
- `async function xxx()`：调接口
- `WebSocket + onmessage`：实时推送
- `setInterval`：轮询兜底
- `onBeforeUnmount`：释放资源

### 4.2 TypeScript：你需要掌握到什么程度？

你只要先会这 5 件事：

1) `interface`：描述对象结构（例如接口返回）  
2) `type` 联合类型：例如状态 `"PENDING" | "RUNNING"`  
3) 可选字段：`foo?: string`  
4) 泛型：`ApiResponse<T>`（让接口返回有类型提示）  
5) 断言与 any：项目里会看到 `as any`，你要知道这是“临时绕过类型检查”

练习入口：
- `frontend/src/api/module_application/dqscan.ts`
- 全局响应类型：`frontend/src/types/global.d.ts`

### 4.3 Axios 请求封装：这是“项目通信约定”

你必须读懂 `frontend/src/utils/request.ts`，因为它决定了：

- baseURL 从哪来（env）
- token 如何携带（request interceptor）
- 后端返回什么结构才算成功（response interceptor 里检查 `data.code`）
- 下载文件为什么要用 `responseType: "blob"`

对应文件：
- `frontend/src/utils/request.ts`
- 返回码枚举：`frontend/src/enums/api/result.enum.ts`

> 你写新接口时，如果后端返回结构不符合 `ApiResponse`，前端会直接当作失败。这个是“项目约定”，不是你的代码写错。

### 4.4 路由：你新增页面一定会遇到

你至少要知道：

- 路由表在哪里：`frontend/src/router/index.ts`
- 如何添加一个新页面路由（参考 dqscan 的路由写法）
- `Layout` 的意义：用于左侧菜单/整体布局
- `meta` 常见字段：`title/icon/keepAlive/hidden`

练习入口：`frontend/src/router/index.ts`

### 4.5 Pinia：你不用先精通，但要会“看”

你至少要知道：

- store 是全局状态容器（用户信息、菜单、权限等）
- `actions` 里通常会调 API
- 本项目的 token 存储在 `Auth` 工具类里（localStorage/sessionStorage）

练习入口：
- `frontend/src/store/modules/user.store.ts`
- `frontend/src/utils/auth.ts`
- `frontend/src/utils/storage.ts`

### 4.6 UI（Element Plus）+ 样式（UnoCSS）：你写页面离不开

Element Plus：你至少要熟悉这些组件/概念：

- `el-form` / `el-input` / `el-select`（表单）
- `el-upload`（上传）
- `el-button` / `el-tag` / `el-alert`（交互与提示）
- `ElMessage` / `ElNotification`（全局提示）
- `el-table`（你后面做列表页会大量用）

UnoCSS：你只要先知道它是什么、怎么用“工具类”就行：

- `flex items-center gap-2` 这类 class 是 UnoCSS（不是普通 CSS 文件里的 class）
- `i-svg:xxx` 是本地 svg 图标（由 UnoCSS icons preset 处理）

配置位置：`frontend/uno.config.ts`

---

## 5. 本项目的“标准开发三件套”（照这个写，最快不迷路）

本项目做一个业务页面，通常就是三件事：

1) 写 API：`frontend/src/api/.../*.ts`  
2) 写页面：`frontend/src/views/.../*.vue`  
3) 加路由：`frontend/src/router/index.ts`

你可以把它理解为：

> **API 文件负责“跟后端说话”，Vue 页面负责“跟用户说话”，路由负责“告诉系统这个页面在哪”。**

下面给你一套“可照抄的模板”，以后新增模块基本就按这个套路走。

### 5.1 API 文件模板（axios 封装的正确用法）

参考：`frontend/src/api/module_application/dqscan.ts`

你新增一个模块 API 时，结构建议长这样：

```ts
import request from "@/utils/request";

const API_PATH = "/application/yourmodule";

export interface YourThingOut {
  id: string;
  name: string;
}

const YourModuleAPI = {
  list() {
    return request<ApiResponse<YourThingOut[]>>({
      url: `${API_PATH}/list`,
      method: "get",
    });
  },

  create(body: { name: string }) {
    return request<ApiResponse<{ id: string }>>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },
};

export default YourModuleAPI;
```

你要理解的关键点：

- `request<...>(...)` 的泛型让你在页面里拿到正确的类型提示  
- 统一返回结构是 `ApiResponse<T>`（定义在 `frontend/src/types/global.d.ts`）  
- 后端如果不返回 `{code,msg,data,...}`，前端拦截器会认为失败（`frontend/src/utils/request.ts`）

### 5.2 页面模板（Vue3 `<script setup>` 最常用写法）

参考：`frontend/src/views/module_application/dqscan/index.vue`

你可以用这个“最小页面骨架”理解一个页面：

```vue
<template>
  <div class="app-container">
    <el-card shadow="hover">
      <template #header>
        <div class="flex-x-between">
          <div class="font-bold">你的页面标题</div>
          <el-button @click="reload">刷新</el-button>
        </div>
      </template>

      <el-empty v-if="loading" description="加载中..." />
      <div v-else>
        <pre>{{ JSON.stringify(list, null, 2) }}</pre>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import YourModuleAPI, { type YourThingOut } from "@/api/module_application/yourmodule";

const loading = ref(false);
const list = ref<YourThingOut[]>([]);

async function reload() {
  loading.value = true;
  try {
    const res = await YourModuleAPI.list();
    list.value = res.data.data || [];
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  reload();
});
</script>
```

你要理解的关键点：

- `ref(...)` 是状态容器；真正的值在 `.value` 上  
- `onMounted` 里做初始化请求  
- `try/finally` 用来保证 loading 关闭（这比 if/else 更不容易漏）

### 5.3 路由模板（如何让页面“能打开”）

参考：`frontend/src/router/index.ts`

在本项目里，dqscan 用的是“顶级 Layout 路由”，写法如下（你可以照着新增）：

```ts
{
  path: "/yourmodule",
  component: Layout,
  redirect: "/yourmodule/index",
  meta: { title: "你的模块", icon: "table", keepAlive: false },
  children: [
    {
      path: "index",
      name: "YourModule",
      meta: { title: "你的模块", icon: "table", keepAlive: false },
      component: () => import("@/views/module_application/yourmodule/index.vue"),
    },
  ],
}
```

你要理解的关键点：

- `component: Layout`：表示这个页面在系统主布局下显示（左侧菜单/顶部导航都正常）
- `component: () => import("...")`：懒加载（页面打开时才加载）
- `meta.title/icon`：影响菜单/标签页显示（具体表现跟项目的 Layout 实现有关）

---

## 6. 最短学习路径（我建议你这样学，最快能上手改项目）

> 不建议“先学完所有理论再动手”。最有效的方法：**每学一个点，就回到本项目改一小块**。

### 阶段 1：跑通 + 会看请求（1 天）

你要达成：
- 能打开 `http://localhost:5180/web`
- 能登录
- 能在 DevTools → Network 看到请求 `/api/v1/...` 成功返回

你要看的文件：
- `frontend/.env.development.example`
- `frontend/vite.config.ts`
- `frontend/src/utils/request.ts`

练习：
- 在 dqscan 页面 `loadAlgorithms()` 里加 `console.log(res.data)`，看返回结构（然后再删掉）

### 阶段 2：会写/会改一个 API 文件（1~2 天）

你要达成：
- 看得懂 `frontend/src/api/module_application/dqscan.ts`
- 能新增一个方法并在页面调用

练习（建议做这个）：
- 给 dqscan API 增加一个 `ping()`（随便调用一个 GET 接口，比如 `/health` 或某个现有接口），然后在页面 `onMounted` 打印结果

### 阶段 3：会改一个页面（2~4 天）

你要达成：
- 看得懂 `ref/computed/onMounted`
- 能把后端返回渲染到页面
- 能做一个简单交互（点击按钮→调用接口→显示结果）

练习：
- 在 dqscan 结果页增加一个“复制原始 JSON”按钮（调用 `navigator.clipboard.writeText(prettyResult)`）
- 或增加一个“只显示有问题的模块”开关（用 `computed` 过滤）

### 阶段 4：会加一个新页面路由（1~2 天）

你要达成：
- 能在 `frontend/src/router/index.ts` 新增一个路由
- 能在 Layout 下正常展示

练习：
- 新建一个极简页面：`frontend/src/views/module_application/dqscan/help.vue`
- 新增路由 `/dqscan/help` 指向这个页面

> 做完阶段 1~4，你就具备“在本项目持续开发前端页面”的能力了。

---

## 7. 用 dqscan 当“实战教材”（最后你自然就能读懂你加的功能）

你不用一开始就钻算法。dqscan 对前端来说就是“一个典型业务模块”，它完整覆盖了你最常见的开发场景：

### 6.1 dqscan 的前端三件套

1) API 封装：`frontend/src/api/module_application/dqscan.ts`
2) 页面：`frontend/src/views/module_application/dqscan/index.vue`
3) 路由：`frontend/src/router/index.ts`（`/dqscan/index`）

### 6.2 dqscan 的端到端请求链路（你要能复述）

1) 上传文件：`uploadFile(file)` → 后端返回 `file_id`
2) 创建任务：`createTask({file_id,...})` → 返回 `task_id`
3) 实时状态：
   - WebSocket：接收 `snapshot/log/progress/done/error`
   - 轮询兜底：`getTask(task_id)` 每 2 秒查一次
4) 结果展示：`getResult(task_id)` → 渲染 summary/modules/reports
5) 下载：`downloadResult` / `downloadArtifact`（Blob + file-saver）

你可以用这条链路，把 Vue/TS/Axios/WS/上传下载全部串起来。

更深入的 dqscan 细节（算法/输出结构）可以看：
- 集成说明：`prompt/dqscan-integration.md`
- 代码阅读指南：`prompt/dqscan-code-walkthrough.md`

---

## 8. 常见“新手卡点”与快速排错清单

### 7.1 页面空白/资源 404

- 检查你访问的地址是否包含 `/web`
- 检查 `frontend/vite.config.ts` 的 `base: "/web"`

### 7.2 前端请求都失败（Network Error / 404）

- 看 `frontend/.env.development.example`：`VITE_APP_BASE_API=/api/v1`
- 看 `frontend/vite.config.ts`：proxy 是否把 `/api/v1` 代理到后端 `8001`
- 看后端是否启动成功（默认 `8001`）

### 7.3 明明后端返回了数据，前端还报“请求错误”

大概率是返回结构不符合约定：

- 前端要求 `ApiResponse`：`frontend/src/types/global.d.ts`
- 前端拦截器检查 `data.code`：`frontend/src/utils/request.ts`

### 7.4 WebSocket 连不上

- 检查 `VITE_APP_WS_ENDPOINT` 是否配置（示例在 `frontend/.env.development.example`）
- 检查后端 WS 路由是否注册（dqscan 在后端是手动注册的）

### 7.5 上传/下载有问题

- 上传：必须用 `FormData` + `multipart/form-data`（dqscan 已示范）
- 下载：必须 `responseType: "blob"`（否则会把二进制当 JSON 解析）

---

## 9. 你下一步该怎么做（具体到“今天就能做的事”）

如果你现在完全没有头绪，我建议你今天只做三件事：

1) 打开并通读（不要求全懂）：`frontend/src/views/module_application/dqscan/index.vue`  
   目标：知道它分为“状态区 + 函数区 + 模板区”，并能找到 `startScan/connectWs/loadAlgorithms`
2) 打开并通读：`frontend/src/api/module_application/dqscan.ts` 和 `frontend/src/utils/request.ts`  
   目标：知道“API 文件怎么写”、“统一返回码在哪里校验”
3) 在浏览器 DevTools → Network 里观察 dqscan 的 3 个请求：  
   - `/api/v1/application/dqscan/algorithms`
   - `/api/v1/application/dqscan/upload`
   - `/api/v1/application/dqscan/tasks`

做完这三件事，你就不再是“完全小白”，后续学习会越来越快。

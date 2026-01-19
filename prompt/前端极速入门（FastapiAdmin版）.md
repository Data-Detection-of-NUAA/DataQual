# FastapiAdmin 前端极速入门（只讲项目用得到的）

目标：用最短时间让你能**看懂并改动**本项目的前端页面（例如 `frontend/src/views/module_application/dqscan/index.vue`），理解 HTML/CSS/JS/TS、AJAX/axios、Vue3 的最小必备知识，并搞清楚为什么目录结构这样组织。

> 这不是“从零到精通”的长教程，只覆盖本项目日常开发会反复用到的部分。

---

## 1. 这套前端在项目里扮演什么角色？

一句话：**前端负责页面交互与展示；后端负责鉴权/业务/任务执行/落盘；dqscan 引擎负责算法计算。**

在这个仓库里：
- 前端：`frontend/`（Vue3 + TypeScript + Vite + Element Plus + UnoCSS）
- 后端：`backend/`（FastAPI）
- 引擎：`dqscan/`（算法与报告生成）

前端最常见的一条链路是：

`页面 (views/*.vue)` → `API 封装 (src/api/*.ts)` → `axios 统一封装 (src/utils/request.ts)` → `后端接口`

你只要理解这条链路，就能做 80% 的功能。

---

## 2. 先看目录结构：为什么这样组织？（你问的“规范”核心）

### 2.1 这是一种“分层 + 按业务模块归类”的组织方式

本项目的 `frontend/src/` 既不是纯“按技术分层”(Layer-based) 也不是纯“按功能切片”(Feature-based)，而是：

- **基础设施层**：`utils/`、`router/`、`store/`、`plugins/`、`styles/`、`types/`
- **业务层**：`views/module_xxx/...` + `api/module_xxx/...`

它的优点是：
- 新人好找：页面在 `views`，接口在 `api`，请求封装在 `utils/request.ts`
- 与后端模块天然对应：`module_system` / `module_monitor` / `module_application`
- 适合后台系统：页面多、模块多、表格多、权限多、请求多

### 2.2 src 目录“地图”（你至少要认识这些）

（根据仓库实际结构摘取核心目录）

```
frontend/src/
  api/                  # “后端接口”的前端封装（一个业务模块一个文件夹）
    module_application/  # 业务模块：应用（dqscan、ai、workflow等）
    module_system/       # 业务模块：系统（用户、角色、菜单等）
    module_monitor/      # 业务模块：监控

  views/                 # 页面（路由入口组件，通常是业务页面）
    module_application/
    module_system/
    module_monitor/

  components/            # 可复用组件（跨页面复用）
  layouts/               # 框架布局（侧边栏、顶栏、标签页、主容器）
  router/                # 路由（Vue Router）
  store/                 # 全局状态（Pinia）
  utils/                 # 工具函数（含 axios 封装 request.ts）
  plugins/               # 插件（权限、图标、下载等“全局能力”）
  directives/            # 自定义指令（例如权限指令 v-permission）
  styles/                # 全局样式与主题（含 element-plus 样式覆盖）
  enums/                 # 枚举（例如结果码 ResultEnum）
  constants/             # 常量（storage keys 等）
  lang/                  # i18n
  types/                 # 类型声明（含 auto-import / components.d.ts）
```

> 你关心 dqscan：页面在 `frontend/src/views/module_application/dqscan/index.vue`，接口在 `frontend/src/api/module_application/dqscan.ts`。

---

## 3. HTML / CSS / JS / TS 在 Vue3 里分别在哪？

一个 `.vue` 文件 = 三段：

### 3.1 HTML（结构）
写在 `<template>`：你看到的 `<div>`、`<el-card>`、`<el-table>` 都在这里。

### 3.2 JS/TS（交互逻辑）
写在 `<script setup lang="ts">`：状态、事件、请求、计算属性都在这里。

### 3.3 CSS/SCSS（样式）
写在 `<style scoped lang="scss">`：只作用于当前组件（scoped）。

---

## 4. Vue3：你只需要掌握的最小心智模型

### 4.1 响应式：ref / computed
- `ref(x)`：一个“会驱动 UI 更新”的变量
- `computed(() => ...)`：基于 ref 派生出来的值（自动更新）

你读页面时可以把它当成：
- `ref`：页面状态（loading、表单值、结果数据…）
- `computed`：显示用的“加工值”（状态文字、按钮禁用、表格数据…）

### 4.2 模板指令：v-if / v-for / v-model
三件套够用了：
- `v-if="cond"`：条件显示
- `v-for="x in list"`：循环渲染
- `v-model="state"`：输入控件双向绑定（Input/Select/Slider 等）

### 4.3 生命周期：onMounted / onBeforeUnmount
最常用两个：
- `onMounted(() => {...})`：页面打开时初始化（拉算法列表、拉数据…）
- `onBeforeUnmount(() => {...})`：页面离开时清理（关 WebSocket、清 timer…）

---

## 5. AJAX / axios：在本项目里怎么发请求？

### 5.1 “AJAX”只是概念
AJAX = 不刷新页面发 HTTP 请求拿数据（本质是浏览器请求）。

### 5.2 axios 是工具库，本项目做了统一封装
核心文件：`frontend/src/utils/request.ts`

你需要知道的两点：
- **拦截器会自动带 token**（Authorization）
- **responseType=blob** 的响应会直接返回（用于文件下载）

### 5.3 API 封装的规范（本项目的约定）
以 dqscan 为例：`frontend/src/api/module_application/dqscan.ts`
- 每个函数对应一个后端路由（URL + method）
- 返回值用 TS 类型描述（接口返回结构清晰）

你新增接口时照抄这个模式就行。

---

## 6. TypeScript：只学这 6 个就能上手改项目

1) 基础类型：`string | number | boolean`
2) 对象类型：`interface` / `type`
3) 可选字段：`foo?: string`
4) 联合类型（常见于状态）：`type Status = "RUNNING" | "SUCCESS" | "FAILED"`
5) Record：`Record<string, any>`（当你暂时不想细化结构时）
6) 泛型（接口统一返回）：`ApiResponse<T>`

你看 `frontend/src/api/module_application/dqscan.ts` 基本就能把这些都见一遍。

---

## 7. 为什么 views / api / store 要分开？（“规范”的底层逻辑）

这是典型后台工程的“职责分离”：
- `views/`：页面与交互（UI 状态、按钮、表格、对话框）
- `api/`：请求参数与返回数据的契约（对后端接口的唯一入口）
- `utils/request.ts`：网络层公共能力（鉴权、错误处理、下载）
- `store/`：跨页面共享状态（用户信息、权限、配置）
- `components/`：可复用 UI 积木

好处：
- 你改 UI 不会把请求逻辑写散到处都是
- 你改后端接口，只要改 `api/`，页面调用点不乱
- 你能快速定位问题：网络问题看 request.ts / api；渲染问题看 views；全局状态问题看 store

---

## 8. 看懂一个页面的最快方法（以 dqscan 为例）

打开：`frontend/src/views/module_application/dqscan/index.vue`

按这个顺序读：
1) **模板 `<template>` 顶部**：页面有哪些区域（步骤条、上传、运行日志、结果）
2) **状态定义（ref）**：哪些变量决定页面显示（activeStep、taskId、result、loading…）
3) **动作函数（async function）**：按钮点击会调用什么（upload、createTask、connectWs、fetchResult…）
4) **computed**：哪些字段只是展示加工（statusText、resultModules、图表 options…）
5) **style**：只看和布局相关的（step-bar、card、metric）

你能按这 5 步把 dqscan 读通，就基本能读通本仓库大部分业务页面。

---

## 9. 你马上就能做的“最短练习”（建议顺序）

### 练习 A：加一个按钮
在 dqscan 页面 header 加个按钮，点击弹出提示：
- 模板里加：`<el-button @click="ElMessage.success('hello')">测试</el-button>`
- 你会学到：事件绑定、Element Plus 组件使用

### 练习 B：新增一个后端接口并调用
1) 在 `frontend/src/api/module_application/dqscan.ts` 新增函数
2) 在 `index.vue` 里写一个 `async function` 调它，并把结果 `ref` 存起来
3) 模板里 `{{ xxx }}` 显示出来

你会学到：axios 封装、TS 类型、ref 驱动渲染

### 练习 C：看网络请求
打开浏览器 DevTools → Network：
- 点“刷新结果”
- 观察请求 URL、状态码、返回 JSON
- 你会理解整条链路：页面 → api → request → 后端

---

## 10. 常见问题（你很快会遇到）

### Q1：为什么很多地方不用 import 也能用 ref？
因为项目使用了自动导入与组件自动注册，类型声明在：
- `frontend/src/types/auto-imports.d.ts`
- `frontend/src/types/components.d.ts`

### Q2：为什么 view 目录里有 module_system / module_monitor / module_application？
因为后端也是按模块划分插件（`backend/app/plugin/module_*`），前端按同样维度归类更好维护，并且菜单/路由也以模块为粒度。

### Q3：我应该把“可复用组件”放哪？
- 只在某个页面用：放 `views/xxx/components/`
- 多页面复用：放 `components/`

---

## 11. 本项目里你最该记住的 5 个文件

- `frontend/src/views/module_application/dqscan/index.vue`：完整业务页面样板（步骤、WS、结果、下载、报告视图）
- `frontend/src/api/module_application/dqscan.ts`：API 封装样板
- `frontend/src/utils/request.ts`：axios 拦截器与错误处理（全局生效）
- `frontend/src/router/index.ts`：路由入口（决定页面怎么挂载）
- `frontend/src/layouts/index.vue`：布局入口（侧边栏/顶栏/主内容）

---

如果你告诉我你**下一步最想改的点**（例如“新增一个参数 UI”“把报告视图再做得像 Word 一样”“新增一个模块卡片/图表”），我可以基于这个文档再给你一份“照着抄就能改”的最短操作清单，并直接定位到相关文件与函数。*** End Patch"}}

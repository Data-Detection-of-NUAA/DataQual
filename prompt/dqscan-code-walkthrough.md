# dqscan 代码阅读指南（从 0 到能改）

这份文档的目标是：把 dqscan 的“文件结构、输入输出、算法实现、关键语法”一次讲清楚，便于你从“只会用”过渡到“能读懂、能改、能扩展”。

> 你已经有一份更偏“集成位置/接口”的说明：`prompt/dqscan-integration.md`。本文更偏“读代码/学基础/理解算法”。

---

## 1) 目录树（数据扫描相关）

> 只列出 dqscan 相关的关键文件（省略 `__pycache__` 等）。

```
FastapiAdmin/
  dqscan/                               # 算法引擎（可独立抽成服务）
    engine/
      base.py                           # Algorithm 协议/规范（run 的签名、AlgorithmSpec）
      registry.py                       # 算法注册表：discover / list / get
      algorithms/
        tabular/
          quality_engine.py             # “四模块”表格质量引擎：读取CSV→跑扫描器→写result.json→生成报告
    scanner/
        common/base_scanner.py          # 扫描器基类（输入校验/空数据处理/标准错误输出）
        dirty_data_scanner/
          tabular_dirty_scanner.py      # 脏数据扫描：异常/缺失/重复/范围违规
        distribution_scanner/
          tabular_distribution_scanner.py # 分布偏差：MMD + KS + Chi-square（可选label shift）
        adversarial_scanner/
          tabular_adversarial_scanner.py  # 对抗性：优先ART(ZOO)，否则随机扰动降级
        physics_scanner/
          tabular_physics_scanner.py    # 物理保真度：Pandera约束（缺失则降级基本规则）
    reporters/
        base_reporter.py                # 报告基类（输出目录、JSON写入、numpy类型转JSON）
        detection_report_generator.py   # 统一报告生成：json/summary/docx（docx可选）
        docx_report_generator.py        # Word 报告生成（依赖 python-docx）
        scoring/
          base_scorer.py                # 评分器接口
          dirty_data_scorer.py          # 脏数据评分（扣分制）
          distribution_scorer.py        # 分布偏差评分（p值→分数）
          adversarial_scorer.py         # 对抗性评分（攻击成功率→分数）
          physics_scorer.py             # 物理保真度评分（违规率→分数）

  backend/                              # FastAPI 后端（dqscan 的“适配层”）
    app/plugin/module_application/dqscan/
      controller.py                     # HTTP API：上传/建任务/查状态/取结果/下载产物
      service.py                        # 任务管理：落盘、线程执行引擎、WebSocket事件广播
      schema.py                         # Pydantic 请求/响应模型（前后端约定）
      ws.py                             # WebSocket 路由：订阅任务日志/进度
    app/plugin/init_app.py              # 手动 include dqscan WebSocket 路由（避免限流依赖导致握手失败）
    static/dqscan/                      # 运行时产物目录（.gitignore）
      uploads/                          # 上传的原始文件
      tasks/{task_id}/                  # 每个任务一个目录：result.json、log.txt、reports/*

  frontend/                             # Vue3 前端（dqscan UI）
    src/api/module_application/dqscan.ts # dqscan API 封装
    src/views/module_application/dqscan/index.vue # dqscan 页面（上传→选择模块→运行→看结果）

  prompt/
    dqscan-integration.md               # dqscan 集成说明（偏“位置/接口”）
    dqscan-code-walkthrough.md          # 本文（偏“读代码/学基础/理解算法”）
```

---

## 2) 一次扫描是怎么跑起来的（端到端链路）

从“你在前端点开始检测”到“后端写出 result.json”，核心链路是：

1. **前端上传文件**  
   - 调用：`POST /api/v1/application/dqscan/upload`（multipart/form-data）
   - 返回：`file_id`（后端用“相对 backend 根目录的路径字符串”标识文件）

2. **前端创建任务**  
   - 调用：`POST /api/v1/application/dqscan/tasks`
   - 入参：`{ file_id, baseline_file_id?, algorithm, params }`
   - 返回：`task_id`

3. **后端异步执行任务**（不阻塞 HTTP）  
   - 入口：`DQScanService.create_task()`  
   - 它会 `asyncio.create_task(...)` 启一个后台协程 `_run_task(...)`
   - `_run_task(...)` 内部再用 `asyncio.to_thread(...)` 把“CPU/IO比较重的算法 run”丢到线程池，避免卡住 FastAPI 的事件循环

4. **算法引擎读取输入→跑四模块→写文件**  
   - `dqscan.engine.registry.get_algorithm(name)` 拿到算法对象
   - 调用 `alg.run(input_path=..., output_dir=..., params=..., emit=...)`
   - 算法在 `output_dir` 下写：
     - `result.json`（总结果）
     - `reports/*.json`、`reports/*_summary.json`、`reports/*.docx`（可选）

5. **前端查状态/看结果**  
   - `GET /tasks/{task_id}` 轮询兜底（progress/status/error）
   - WebSocket：`/api/v1/application/dqscan/ws/{task_id}` 实时接收 log/progress/done/error
   - `GET /tasks/{task_id}/result` 读取 `result.json`
   - `GET /tasks/{task_id}/artifact?path=...` 下载某个报告文件（比如 docx）

---

## 3) 输入输出（你需要先把“数据的形状”搞清楚）

### 3.1 HTTP API 的输入输出（后端适配层）

1) 上传

- 请求：`POST /api/v1/application/dqscan/upload`
  - Content-Type: `multipart/form-data`
  - 字段：`file`
- 响应：`DQScanUploadOut`
  - `file_id`: `backend/static/dqscan/uploads/...` 的相对路径
  - `filename`: 原文件名
  - `file_size`: 字节数

2) 创建任务

- 请求：`POST /api/v1/application/dqscan/tasks`
  - JSON：`DQScanCreateTaskIn`
  - `algorithm`: 当前默认 `tabular_quality_engine`
  - `params`: 算法参数（典型是选哪些模块、阈值、读CSV的sep/encoding等）
  - `baseline_file_id`（可选）：用于分布偏差检测的“基线文件”（推荐做法）；不传则会在同一文件内按 `train_test_split` 切分模拟对比
- 响应：`{ task_id }`

3) 查询任务

- 请求：`GET /api/v1/application/dqscan/tasks/{task_id}`
- 响应：`DQScanTaskOut`
  - `status`: `PENDING/RUNNING/SUCCESS/FAILED`
  - `progress`: 0~100
  - `result_file_id`: 任务成功后，`result.json` 的相对路径

4) 获取结果 JSON（给前端渲染）

- 请求：`GET /api/v1/application/dqscan/tasks/{task_id}/result`
- 响应：`DQScanResult`
  - `summary`: 总结（状态、数据类型、模块列表、耗时等）
  - `modules`: 每个模块的详细结果（dict）
  - `reports`: 每个模块的报告文件相对路径（供下载）

### 3.2 WebSocket 事件的输入输出

WebSocket 推送的事件都是 JSON 字符串，核心字段：

- `type`: `snapshot | log | progress | done | error`
- `task_id`: 任务ID
- `message`: 日志/结束/错误文案（log/done/error 常见）
- `value`: 进度值（progress 常见）

> 你读代码时只要抓住：**算法 run 里的 emit(event) → 后端写log/更新progress → 推送到WS**。

---

## 4) 引擎的“接口规范”（AlgorithmSpec + run）

引擎侧的核心思想是：**算法是一个对象**，它必须满足一个约定：

- 有 `spec`（描述算法的“元信息”）
- 有 `run(...)`（执行入口）

对应代码：

- `dqscan/engine/base.py`：定义了 `AlgorithmSpec` 和 `Algorithm(Protocol)`
- `dqscan/engine/registry.py`：负责注册、发现、list/get

为什么要这样做？

- 后端要“列出算法列表”给前端用 → 读 `spec`
- 后端要“按名字执行算法” → `get_algorithm(name)` 然后调用 `run`

---

## 5) 四模块引擎 TabularQualityEngine 的算法是怎么实现的

入口文件：`dqscan/engine/algorithms/tabular/quality_engine.py`

### 5.1 算法流程（伪代码）

```
读CSV为 DataFrame df
modules = params.modules (默认四个)
for module in modules:
    根据 module 选择 scanner
    res = scanner.scan(...)
    生成报告 json/summary/docx
把 modules 的 res 汇总写到 result.json
```

### 5.2 输入

- `input_path`: CSV/TXT 文件路径
- `params`: 字典（例如）
  - `modules`: 选择要跑的模块
  - `p_val`: 分布偏差显著性阈值
  - `exclude_columns`: 分布偏差检测可选：排除不参与对比的列（如 id/时间戳/唯一标识列，避免误报）
  - `contamination`: 异常检测污染率
  - `read_csv.sep/encoding`: 读CSV参数

补充（分布偏差模块的基线文件）：
- 创建任务时可额外传 `baseline_file_id`（可选）。后端会把基线文件解析为路径并注入到算法参数中（内部字段），用于“基线 vs 当前”的分布对比。

### 5.3 输出

写到 `output_dir/`（后端会把 `output_dir` 指向 `backend/static/dqscan/tasks/{task_id}`）：

- `result.json`: 总结果（summary + modules + reports）
- `reports/`: 每个模块的报告（json/summary/docx）

> 注意：为了让 JSON 可序列化，报告生成器会把 numpy 的类型（np.float32 等）转换为 Python 原生类型。

---

## 6) 四个模块分别在做什么（算法解释）

下面讲“实现思路”，不是严格论文级别，但足够你读懂代码并能改。

### 6.1 脏数据扫描（dirty_data）

入口：`dqscan/scanner/dirty_data_scanner/tabular_dirty_scanner.py`

做的事情：

- **异常值**：
  - 优先用 `pyod` 的 `ECOD`（如安装了 pyod）
  - 否则用 **3σ 规则**（z-score，绝对值大于 3 认为异常）
- **缺失值**：`data.isnull().sum()`
- **重复数据**：`data.duplicated(keep=False)`
- **范围违规**：对每个数值列，计算均值±3σ，超出视为可疑（简单规则）

输出关注点：

- `anomaly_rate / missing_rate / duplicate_rate`
- `has_issues`：是否有风险（当前逻辑：任一 rate > 0）
- `detailed_issues`：给前端展示的示例问题（截断到一定数量，避免爆炸）

### 6.2 分布偏差（distribution）

入口：`dqscan/scanner/distribution_scanner/tabular_distribution_scanner.py`

对比数据来源有两种模式（由引擎层决定）：

1) **基线文件 vs 当前文件（推荐）**  
   - 你上传两份文件：`baseline_file_id`（基线）和 `file_id`（当前）  
   - 引擎会读取两份 CSV，直接做分布对比（更符合真实生产监控）

2) **同一文件内切分（兼容旧逻辑）**  
   - 只上传一份文件（不传 `baseline_file_id`）  
   - 引擎会按 `train_test_split` 把同一份数据切成两段模拟“旧 vs 新”  
   - 前提：你的 CSV 行顺序最好是“先旧后新”，否则切分就不太有意义

核心做三类统计检验（你可以理解为“三把尺子”）：

1. **MMD（Maximum Mean Discrepancy）**：整体分布差异的度量  
   - 先把数值特征标准化（`StandardScaler`）
   - 用 RBF 核计算 MMD 值
   - 用置换检验（permutation test）近似得到 p-value
2. **K-S 检验（KS test）**：对每一列数值特征做两样本KS检验  
   - p-value < 阈值（`p_val`）认为该列发生漂移
3. **卡方检验（Chi-square）**：对每一列类别特征做卡方检验  
   - 比较 value_counts 后的列联表

可选：`label_shift`（如果你传了 `label_column`）

输出关注点：

- `drift_detected`: 是否检测到漂移（综合判定）
- `p_value`: 用 MMD 的 p-value 当作“总体漂移程度”的代表值（用于前端摘要）

### 6.3 对抗性（adversarial）

入口：`dqscan/scanner/adversarial_scanner/tabular_adversarial_scanner.py`

本仓库是“演示版对抗性检测”，大体逻辑：

- 你先要有一个分类模型 `model`（这里在 `quality_engine.py` 里用随机森林训练了一个演示模型）
- 在“原本预测正确”的样本上，生成对抗样本，观察是否能让模型预测翻车

攻击实现分两档：

1. 有 IBM ART（可选依赖）时，用 `ZooAttack` 做黑盒攻击
2. 没有 ART 时，用“随机扰动搜索”的降级攻击：
   - 随机挑若干特征加噪声
   - 如果预测被翻转 → 认为攻击成功

输出关注点：

- `attack_success_rate`: 攻击成功率
- `robustness_score = 1 - attack_success_rate`

### 6.4 物理保真度（physics）

入口：`dqscan/scanner/physics_scanner/tabular_physics_scanner.py`

你可以把它理解为：“数据是否违反一些明显的物理/业务约束”。

两种实现路径：

1. 安装了 `pandera`：用 DataFrameSchema + Check(ge/le) 来验证 min/max 约束，并能拿到 failure_cases
2. 没装 `pandera`：降级用简单的 mask 过滤来找违规样本

还支持一个可选的“守恒约束”（`check_conservation=True`）：

- 如果存在类似 `xxx_in` / `xxx_out` 的列名组合，检查二者差异是否异常大（简单启发式）

输出关注点：

- `violation_rate`: 违规率
- `constraints_checked`: 实际检查了哪些列约束

---

## 7) 读懂这些代码需要的 Python/工程语法（最小集合）

你读 dqscan 代码时，最常见的“看不懂点”主要是下面这些：

### 7.1 类型标注（type hints）

比如：

- `dict[str, Any]`：字典，key 是 str，value 是任意类型
- `float | None`：要么 float，要么 None（Python 3.10+ 的写法）
- `list[DQScanAlgorithmOut]`：列表里放某个类型

它们本质上是“给人和编辑器看的”，不影响运行（但能显著提升可读性）。

### 7.2 `from __future__ import annotations`

作用：让类型注解延迟求值（把注解当字符串处理），避免循环引用/导入顺序问题，也能减少运行期开销。

### 7.3 `async/await` 与 `asyncio.to_thread`

FastAPI 的请求处理通常是 `async def`，运行在事件循环里：

- **不能**在事件循环里直接跑很重的 CPU 计算/阻塞 IO（会卡住整个服务）
- 所以在 `DQScanService._run_task` 里用 `await asyncio.to_thread(alg.run, ...)`：
  - `alg.run` 在后台线程执行
  - FastAPI 的事件循环仍然可以处理其他请求

### 7.4 `dataclass`

`@dataclass` 是用来快速定义“只装数据的类”的语法糖。  
比如 `service.py` 里的 `_TaskState`：就是任务的状态容器。

### 7.5 `Protocol`

`Protocol` 用来表达“鸭子类型接口”：只要对象有这些属性/方法，就认为它符合接口。  
在 `dqscan/engine/base.py` 里，任何实现了 `spec` 和 `run()` 的对象都能作为算法被注册。

---

## 8) 你要怎么改/扩展（给你一个明确的改法）

### 8.1 新增一个算法（例如 tabular_quality_engine_custom）

1. 新建文件：`dqscan/engine/algorithms/tabular/quality_engine_custom.py`
2. 写一个类，满足：
   - `spec = AlgorithmSpec(...)`
   - `def run(...): ...`
3. 在 `dqscan/engine/registry.py::_discover()` 里 `register(TabularQualityEngineV4())`
4. 后端不用改：`/algorithms` 会自动多一个算法，前端可选择后调用 `/tasks`

### 8.2 改一个模块的判定逻辑

建议从最小的函数入口入手：

- 脏数据：`TabularDirtyScanner.scan()` → 看 anomaly/missing/duplicate 这三块如何组合成 has_issues
- 分布偏差：`TabularDistributionScanner._detect_mmd/_detect_ks/_detect_chi2` → 看你要替换哪把“尺子”
- 对抗性：`TabularAdversarialScanner.scan()` → 改攻击方式/改阈值
- 物理保真度：`TabularPhysicsScanner.constraints` → 约束来源可以从“启发式”升级为“用户配置/模型推断”

---

## 9) 一个推荐的“学习顺序”（从最容易到最核心）

如果你现在“只知其然不知其所以然”，按下面顺序读代码效率最高：

1. `backend/app/plugin/module_application/dqscan/controller.py`（看 API 是怎么设计的）
2. `backend/app/plugin/module_application/dqscan/service.py`（看任务/线程/WS 的工程实现）
3. `dqscan/engine/registry.py`（看算法如何注册/发现）
4. `dqscan/engine/algorithms/tabular/quality_engine.py`（看四模块如何串起来）
5. 四个 scanner（你真正关心的算法细节）
6. reporters/scoring（你要改报告/评分时再看）

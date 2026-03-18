# AGENTS.md（FastapiAdmin / dqscan）

本文件对本仓库 **全目录树** 生效（除非子目录存在更具体的 `AGENTS.md` 覆盖）。

## 规划与记录（强制）

本项目使用“文件化规划”工作流：`task_plan.md` / `findings.md` / `progress.md`。

**硬性要求：每完成一个计划步骤（Step/Phase/里程碑）必须同时更新以下三个文件：**
1) `task_plan.md`：勾选已完成项；必要时调整下一步与阶段状态（in_progress/complete/pending）。
2) `findings.md`：记录本步骤的关键发现/算法取舍/数据结构/边界条件（避免只留在对话上下文）。
3) `progress.md`：追加本步骤做了什么（含命令/测试/输出/错误与解决方式）。

> 解释：上下文是易失的；规划文件是唯一可信的“工作记忆”。


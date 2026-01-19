# -*- coding: utf-8 -*-

"""
dqscan 后端适配层：任务管理 + 运行引擎 + WebSocket 推送

这层代码的定位是“工程胶水”，把仓库根目录的 `dqscan/` 算法引擎接入 FastAPI：

- 上传文件落盘：`backend/static/dqscan/uploads/`
- 创建任务目录：`backend/static/dqscan/tasks/{task_id}/`
- 异步执行算法：`asyncio.to_thread(alg.run, ...)` 避免阻塞事件循环
- 事件推送：算法通过 `emit({...})` 上报 log/progress/done/error，本服务广播到 WebSocket 客户端

注意：
- 任务状态当前只保存在内存（`DQScanService._tasks`），服务重启后状态会丢失；
- 结果文件落盘在 static 目录，因此前端可通过 “result/artifact” 接口拉取。
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import UploadFile, WebSocket

from app.core.logger import log
from app.config.path_conf import BASE_DIR, STATIC_DIR


def _find_repo_root() -> Path:
    """
    定位仓库根目录。

    由于算法引擎 `dqscan/` 放在仓库根目录，而后端运行入口在 `backend/`，这里通过向上
    查找同时包含 `backend/` 和 `frontend/` 的目录来判断 repo root，便于把根目录塞进 sys.path。
    """
    here = Path(__file__).resolve()
    for p in here.parents:
        if (p / "backend").is_dir() and (p / "frontend").is_dir():
            return p
    return here.parents[5]


def _ensure_dqscan_importable() -> None:
    """确保 `import dqscan` 可用（将 repo root 注入 `sys.path`）。"""
    repo_root = _find_repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def _dqscan_root() -> Path:
    """dqscan 的静态根目录：`backend/static/dqscan/`。"""
    return STATIC_DIR / "dqscan"


def _uploads_root() -> Path:
    """上传目录：`backend/static/dqscan/uploads/`。"""
    return _dqscan_root() / "uploads"


def _tasks_root() -> Path:
    """任务目录：`backend/static/dqscan/tasks/`。"""
    return _dqscan_root() / "tasks"


def _safe_rel_file_id(abs_path: Path) -> str:
    """
    将绝对路径转换为“相对 backend 根目录”的 file_id（用于接口返回）。

    这是一个安全边界：只允许返回位于 `backend/` 目录下的路径，避免把任意系统路径暴露给前端。
    """
    abs_path = abs_path.resolve()
    base = BASE_DIR.resolve()
    if base not in abs_path.parents and abs_path != base:
        raise ValueError("path must be under backend base dir")
    return str(abs_path.relative_to(base)).replace("\\", "/")


def _resolve_file_id(file_id: str) -> Path:
    """
    将 file_id（相对 backend 根目录路径）解析成绝对路径，并做路径穿越防护。

    约束：
    - 只允许访问 `backend/static/dqscan/` 下的文件（上传文件、任务产物等）
    """
    file_id = file_id.lstrip("/").replace("\\", "/")
    abs_path = (BASE_DIR / file_id).resolve()
    dq_root = _dqscan_root().resolve()
    if dq_root not in abs_path.parents:
        raise ValueError("invalid file_id")
    return abs_path


@dataclass
class _TaskState:
    """任务在内存中的运行态状态（给 HTTP 查询与 WS snapshot 使用）。"""
    task_id: str
    status: str = "PENDING"
    progress: int = 0
    started_at: float | None = None
    ended_at: float | None = None
    error: str | None = None
    baseline_file_id: str | None = None
    result_file_id: str | None = None
    # 每个 websocket 连接对应一个 queue：生产者（算法线程）写入事件，消费者（ws_pump）读取并发送
    ws_clients: dict[WebSocket, asyncio.Queue[dict[str, Any]]] = field(default_factory=dict)


class DQScanService:
    """
    dqscan 服务层（不入库的轻量任务系统）。

    - `_tasks`：内存任务表（task_id -> state）
    - `_run_task`：后台协程，负责调用算法并写出 result.json
    - WebSocket：允许前端订阅实时日志与进度
    """

    _tasks: dict[str, _TaskState] = {}
    _lock = asyncio.Lock()

    @classmethod
    async def list_algorithms(cls) -> list[dict[str, Any]]:
        """返回算法引擎中已注册的算法列表（供前端下拉选择）。"""
        _ensure_dqscan_importable()
        from dqscan.engine import list_algorithms

        return list_algorithms()

    @classmethod
    async def upload(cls, file: UploadFile, *, max_bytes: int) -> dict[str, Any]:
        """
        上传文件落盘到 static 目录，并返回 file_id。

        - 以 1MB chunk 读取，避免把大文件一次性加载进内存；
        - 超过 max_bytes 直接报错；
        - 返回的 file_id 是“相对 backend 根目录”的路径字符串。
        """
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in {".csv", ".txt"}:
            raise ValueError("仅支持 .csv / .txt")

        _uploads_root().mkdir(parents=True, exist_ok=True)
        file_id = f"{uuid.uuid4().hex}_{Path(file.filename or 'upload').name}"
        target = (_uploads_root() / file_id).resolve()

        size = 0
        try:
            with open(target, "wb") as f:
                while True:
                    chunk = await file.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > max_bytes:
                        raise ValueError(f"文件超过大小限制：{max_bytes} bytes")
                    f.write(chunk)
        except Exception:
            try:
                target.unlink(missing_ok=True)
            except Exception:
                pass
            raise

        return {
            "file_id": _safe_rel_file_id(target),
            "filename": file.filename or target.name,
            "file_size": size,
        }

    @classmethod
    async def create_task(
        cls,
        *,
        file_id: str,
        baseline_file_id: str | None,
        algorithm: str,
        params: dict[str, Any] | None,
    ) -> str:
        """
        创建任务并异步执行。

        返回 task_id。任务执行不阻塞当前 HTTP 请求（后台运行）。
        """
        task_id = uuid.uuid4().hex
        task_dir = (_tasks_root() / task_id).resolve()
        task_dir.mkdir(parents=True, exist_ok=True)

        state = _TaskState(task_id=task_id, status="PENDING", progress=0, baseline_file_id=baseline_file_id)
        async with cls._lock:
            cls._tasks[task_id] = state

        asyncio.create_task(
            cls._run_task(
                state=state,
                file_id=file_id,
                baseline_file_id=baseline_file_id,
                algorithm=algorithm,
                params=params,
            )
        )
        return task_id

    @classmethod
    async def get_task(cls, task_id: str) -> dict[str, Any]:
        """查询任务状态（仅内存态，不保证服务重启后可查）。"""
        async with cls._lock:
            state = cls._tasks.get(task_id)
        if not state:
            raise KeyError("task not found")

        return {
            "task_id": state.task_id,
            "status": state.status,
            "progress": state.progress,
            "started_at": state.started_at,
            "ended_at": state.ended_at,
            "error": state.error,
            "baseline_file_id": state.baseline_file_id,
            "result_file_id": state.result_file_id,
        }

    @classmethod
    async def get_result_path(cls, task_id: str) -> Path:
        """获取 result.json 的绝对路径（任务成功后才存在）。"""
        async with cls._lock:
            state = cls._tasks.get(task_id)
        if not state or not state.result_file_id:
            raise KeyError("result not ready")
        return _resolve_file_id(state.result_file_id)

    @classmethod
    async def get_task_dir(cls, task_id: str) -> Path:
        """校验 task_id 并返回任务目录（用于 artifact 下载）。"""
        task_dir = (_tasks_root() / task_id).resolve()
        if not task_dir.exists():
            raise KeyError("task not found")
        root = _tasks_root().resolve()
        if root not in task_dir.parents and task_dir != root:
            raise ValueError("invalid task_id")
        return task_dir

    @classmethod
    async def resolve_task_artifact(cls, task_id: str, rel_path: str) -> Path:
        """
        解析并校验任务产物路径（防止 path traversal）。

        前端传入的 `path` 必须是任务目录下的相对路径，例如：`reports/dirty_data_report_tabular.docx`。
        """
        task_dir = await cls.get_task_dir(task_id)
        rel_path = (rel_path or "").lstrip("/").replace("\\", "/")
        abs_path = (task_dir / rel_path).resolve()
        if task_dir not in abs_path.parents and abs_path != task_dir:
            raise ValueError("invalid artifact path")
        if not abs_path.exists():
            raise FileNotFoundError("artifact not found")
        return abs_path

    @classmethod
    async def get_reports(
        cls,
        task_id: str,
        *,
        module: str | None = None,
        report_type: str = "json",
    ) -> dict[str, Any]:
        """
        读取并返回任务的报告 JSON（给前端页面展示用）。

        - report_type="json"：读取 `reports/*_report_*.json`（包含 scoring + compact results）
        - report_type="summary"：读取 `reports/*_summary.json`（更轻量）

        返回结构：
        - {"reports": {<module_key>: <report_json>, ...}}
        """
        if report_type not in {"json", "summary"}:
            raise ValueError("invalid report_type")

        task_dir = await cls.get_task_dir(task_id)
        result_path = (task_dir / "result.json").resolve()
        if not result_path.exists():
            raise FileNotFoundError("result.json not found")

        result_obj = json.loads(result_path.read_text("utf-8"))
        report_index = result_obj.get("reports") if isinstance(result_obj, dict) else None
        if not isinstance(report_index, dict):
            return {"reports": {}}

        def _pick_path(paths: dict[str, Any]) -> str | None:
            if report_type == "summary":
                v = paths.get("summary_report")
            else:
                v = paths.get("json_report")
            return str(v) if v else None

        modules = [module] if module else list(report_index.keys())
        out: dict[str, Any] = {}
        for m in modules:
            if not m:
                continue
            entry = report_index.get(m)
            if not isinstance(entry, dict):
                continue
            paths = entry.get("paths")
            if not isinstance(paths, dict):
                continue
            rel = _pick_path(paths)
            if not rel:
                continue
            rel = rel.lstrip("/").replace("\\", "/")
            abs_path = (task_dir / rel).resolve()
            if task_dir not in abs_path.parents and abs_path != task_dir:
                raise ValueError("invalid report path")
            if not abs_path.exists():
                continue
            try:
                out[m] = json.loads(abs_path.read_text("utf-8"))
            except Exception as e:
                out[m] = {"error": f"report parse failed: {e}"}

        if module and module not in out:
            raise KeyError("report not found")

        return {"reports": out}

    @classmethod
    async def ws_connect(cls, task_id: str, websocket: WebSocket) -> _TaskState:
        """
        建立 WebSocket 连接并发送 snapshot（当前状态快照）。

        snapshot 之后，客户端会持续收到 `log/progress/done/error` 事件。
        """
        async with cls._lock:
            state = cls._tasks.get(task_id)
        if not state:
            raise KeyError("task not found")

        await websocket.accept()
        state.ws_clients[websocket] = asyncio.Queue()

        await websocket.send_text(
            json.dumps(
                {
                    "type": "snapshot",
                    "task_id": state.task_id,
                    "status": state.status,
                    "progress": state.progress,
                    "error": state.error,
                    "baseline_file_id": state.baseline_file_id,
                    "result_file_id": state.result_file_id,
                },
                ensure_ascii=False,
            )
        )
        if state.status == "SUCCESS":
            await websocket.send_text(
                json.dumps(
                    {"type": "done", "task_id": state.task_id, "message": "扫描完成（已结束）"},
                    ensure_ascii=False,
                )
            )
        elif state.status == "FAILED":
            await websocket.send_text(
                json.dumps(
                    {"type": "error", "task_id": state.task_id, "message": state.error or "任务失败"},
                    ensure_ascii=False,
                )
            )
        return state

    @classmethod
    def ws_disconnect(cls, state: _TaskState, websocket: WebSocket) -> None:
        """断开连接时从 ws_clients 移除（避免队列泄漏）。"""
        try:
            state.ws_clients.pop(websocket, None)
        except Exception:
            pass

    @classmethod
    async def ws_pump(cls, state: _TaskState, websocket: WebSocket) -> None:
        """将队列中的事件持续推送给指定 websocket。"""
        queue = state.ws_clients.get(websocket)
        if queue is None:
            return
        while True:
            event = await queue.get()
            try:
                await websocket.send_text(json.dumps(event, ensure_ascii=False))
            except Exception:
                return

    @classmethod
    def _broadcast_nowait(cls, state: _TaskState, event: dict[str, Any]) -> None:
        """向所有已连接 websocket 广播事件（非阻塞 put_nowait）。"""
        for q in list(state.ws_clients.values()):
            try:
                q.put_nowait(event)
            except Exception:
                pass

    @classmethod
    async def _run_task(
        cls,
        *,
        state: _TaskState,
        file_id: str,
        baseline_file_id: str | None,
        algorithm: str,
        params: dict[str, Any] | None,
    ):
        """
        后台任务执行器。

        - 解析 file_id → 输入文件绝对路径
        - 调用引擎算法 `alg.run(...)`
        - 校验并记录 result.json 路径
        - 过程中通过 emit 写 log.txt、更新 progress、广播 WS
        """
        state.status = "RUNNING"
        state.started_at = time.time()
        state.progress = 0
        loop = asyncio.get_running_loop()

        task_dir = (_tasks_root() / state.task_id).resolve()
        log_file = (task_dir / "log.txt").resolve()

        def emit(event: dict[str, Any]) -> None:
            # emit 可能在 worker thread 内被调用，所以这里：
            # 1) 同步更新 state（简单字段，允许轻微竞态）
            # 2) 用 call_soon_threadsafe 把广播调度回事件循环线程
            event = dict(event)
            event.setdefault("task_id", state.task_id)

            if event.get("type") == "progress":
                try:
                    state.progress = int(event.get("value", state.progress))
                except Exception:
                    pass
            if event.get("type") == "log":
                try:
                    log_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(str(event.get("message", "")) + "\n")
                except Exception:
                    pass

            try:
                loop.call_soon_threadsafe(cls._broadcast_nowait, state, event)
            except Exception:
                return

        try:
            input_path = _resolve_file_id(file_id)

            _ensure_dqscan_importable()
            from dqscan.engine import get_algorithm

            alg = get_algorithm(algorithm)

            params_to_pass = dict(params or {})
            if baseline_file_id:
                baseline_path = _resolve_file_id(baseline_file_id)
                # 仅由后端注入基线路径，避免前端随意传系统路径造成风险
                params_to_pass["baseline_input_path"] = os.fspath(baseline_path)

            await asyncio.to_thread(
                alg.run,
                input_path=os.fspath(input_path),
                output_dir=os.fspath(task_dir),
                params=params_to_pass,
                emit=emit,
            )

            result_path = (task_dir / "result.json").resolve()
            if not result_path.exists():
                raise RuntimeError("result.json not generated")

            state.result_file_id = _safe_rel_file_id(result_path)
            state.status = "SUCCESS"
            state.progress = 100
            state.ended_at = time.time()
            cls._broadcast_nowait(state, {"type": "done", "task_id": state.task_id, "message": "扫描完成"})
        except Exception as e:
            state.status = "FAILED"
            state.error = str(e)
            state.ended_at = time.time()
            log.exception("dqscan task failed")
            cls._broadcast_nowait(state, {"type": "error", "task_id": state.task_id, "message": str(e)})

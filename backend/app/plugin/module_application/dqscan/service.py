# -*- coding: utf-8 -*-

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
    here = Path(__file__).resolve()
    for p in here.parents:
        if (p / "backend").is_dir() and (p / "frontend").is_dir():
            return p
    return here.parents[5]


def _ensure_dqscan_importable() -> None:
    repo_root = _find_repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def _dqscan_root() -> Path:
    return STATIC_DIR / "dqscan"


def _uploads_root() -> Path:
    return _dqscan_root() / "uploads"


def _tasks_root() -> Path:
    return _dqscan_root() / "tasks"


def _safe_rel_file_id(abs_path: Path) -> str:
    abs_path = abs_path.resolve()
    base = BASE_DIR.resolve()
    if base not in abs_path.parents and abs_path != base:
        raise ValueError("path must be under backend base dir")
    return str(abs_path.relative_to(base)).replace("\\", "/")


def _resolve_file_id(file_id: str) -> Path:
    file_id = file_id.lstrip("/").replace("\\", "/")
    abs_path = (BASE_DIR / file_id).resolve()
    dq_root = _dqscan_root().resolve()
    if dq_root not in abs_path.parents:
        raise ValueError("invalid file_id")
    return abs_path


@dataclass
class _TaskState:
    task_id: str
    status: str = "PENDING"
    progress: int = 0
    started_at: float | None = None
    ended_at: float | None = None
    error: str | None = None
    result_file_id: str | None = None
    ws_clients: dict[WebSocket, asyncio.Queue[dict[str, Any]]] = field(default_factory=dict)


class DQScanService:
    _tasks: dict[str, _TaskState] = {}
    _lock = asyncio.Lock()

    @classmethod
    async def list_algorithms(cls) -> list[dict[str, Any]]:
        _ensure_dqscan_importable()
        from dqscan.engine import list_algorithms

        return list_algorithms()

    @classmethod
    async def upload(cls, file: UploadFile, *, max_bytes: int) -> dict[str, Any]:
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
    async def create_task(cls, *, file_id: str, algorithm: str, params: dict[str, Any] | None) -> str:
        task_id = uuid.uuid4().hex
        task_dir = (_tasks_root() / task_id).resolve()
        task_dir.mkdir(parents=True, exist_ok=True)

        state = _TaskState(task_id=task_id, status="PENDING", progress=0)
        async with cls._lock:
            cls._tasks[task_id] = state

        asyncio.create_task(cls._run_task(state=state, file_id=file_id, algorithm=algorithm, params=params))
        return task_id

    @classmethod
    async def get_task(cls, task_id: str) -> dict[str, Any]:
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
            "result_file_id": state.result_file_id,
        }

    @classmethod
    async def get_result_path(cls, task_id: str) -> Path:
        async with cls._lock:
            state = cls._tasks.get(task_id)
        if not state or not state.result_file_id:
            raise KeyError("result not ready")
        return _resolve_file_id(state.result_file_id)

    @classmethod
    async def get_task_dir(cls, task_id: str) -> Path:
        task_dir = (_tasks_root() / task_id).resolve()
        if not task_dir.exists():
            raise KeyError("task not found")
        root = _tasks_root().resolve()
        if root not in task_dir.parents and task_dir != root:
            raise ValueError("invalid task_id")
        return task_dir

    @classmethod
    async def resolve_task_artifact(cls, task_id: str, rel_path: str) -> Path:
        task_dir = await cls.get_task_dir(task_id)
        rel_path = (rel_path or "").lstrip("/").replace("\\", "/")
        abs_path = (task_dir / rel_path).resolve()
        if task_dir not in abs_path.parents and abs_path != task_dir:
            raise ValueError("invalid artifact path")
        if not abs_path.exists():
            raise FileNotFoundError("artifact not found")
        return abs_path

    @classmethod
    async def ws_connect(cls, task_id: str, websocket: WebSocket) -> _TaskState:
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
        try:
            state.ws_clients.pop(websocket, None)
        except Exception:
            pass

    @classmethod
    async def ws_pump(cls, state: _TaskState, websocket: WebSocket) -> None:
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
        for q in list(state.ws_clients.values()):
            try:
                q.put_nowait(event)
            except Exception:
                pass

    @classmethod
    async def _run_task(cls, *, state: _TaskState, file_id: str, algorithm: str, params: dict[str, Any] | None):
        state.status = "RUNNING"
        state.started_at = time.time()
        state.progress = 0
        loop = asyncio.get_running_loop()

        task_dir = (_tasks_root() / state.task_id).resolve()
        log_file = (task_dir / "log.txt").resolve()

        def emit(event: dict[str, Any]) -> None:
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

            await asyncio.to_thread(
                alg.run,
                input_path=os.fspath(input_path),
                output_dir=os.fspath(task_dir),
                params=params or {},
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

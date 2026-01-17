# -*- coding: utf-8 -*-

"""
dqscan 的 HTTP API（FastAPI Router）。

这层只做“HTTP 协议适配”，核心业务在 `service.py`：
- upload：上传文件到 `backend/static/dqscan/uploads/`
- tasks：创建任务并异步执行（后台线程跑算法）
- result/artifact：读取任务目录下落盘的产物

前端对应调用：`frontend/src/api/module_application/dqscan.ts`
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, UploadFile, Query
from fastapi.responses import JSONResponse

from app.common.response import SuccessResponse, UploadFileResponse
from app.core.router_class import OperationLogRoute

from .schema import (
    DQScanAlgorithmOut,
    DQScanCreateTaskIn,
    DQScanCreateTaskOut,
    DQScanResultOut,
    DQScanTaskOut,
    DQScanUploadOut,
    SuccessResponseOut,
)
from .service import DQScanService


DQScanRouter = APIRouter(route_class=OperationLogRoute, prefix="/dqscan", tags=["数据集质量扫描（dqscan）"])


@DQScanRouter.get(
    "/algorithms",
    summary="获取算法列表",
    description="返回 dqscan 引擎已注册的算法（用于前端算法选择）。",
    response_model=SuccessResponseOut[list[DQScanAlgorithmOut]],
)
async def list_algorithms_controller() -> JSONResponse:
    data = await DQScanService.list_algorithms()
    return SuccessResponse(data=data, msg="获取成功")


@DQScanRouter.post(
    "/upload",
    summary="上传 CSV/TXT",
    description="上传表格文件（MVP：仅支持 .csv / .txt，最大 500MB）。",
    response_model=SuccessResponseOut[DQScanUploadOut],
)
async def upload_controller(file: UploadFile) -> JSONResponse:
    data = await DQScanService.upload(file, max_bytes=500 * 1024 * 1024)
    return SuccessResponse(data=data, msg="上传成功")


@DQScanRouter.post(
    "/tasks",
    summary="创建扫描任务",
    description="创建 dqscan 扫描任务并异步执行；通过 WebSocket 获取实时日志与进度。",
    response_model=SuccessResponseOut[DQScanCreateTaskOut],
)
async def create_task_controller(body: DQScanCreateTaskIn) -> JSONResponse:
    task_id = await DQScanService.create_task(
        file_id=body.file_id,
        algorithm=body.algorithm,
        params=body.params,
    )
    return SuccessResponse(data={"task_id": task_id}, msg="任务已创建")


@DQScanRouter.get(
    "/tasks/{task_id}",
    summary="查询任务状态",
    description="查询任务状态/进度/错误信息。",
    response_model=SuccessResponseOut[DQScanTaskOut],
)
async def get_task_controller(task_id: str) -> JSONResponse:
    data = await DQScanService.get_task(task_id)
    return SuccessResponse(data=data, msg="获取成功")


@DQScanRouter.get(
    "/tasks/{task_id}/result",
    summary="获取任务结果",
    description="读取任务目录下的 result.json（不同算法会有不同字段，但至少包含 summary）。",
    response_model=SuccessResponseOut[DQScanResultOut],
)
async def get_result_controller(task_id: str) -> JSONResponse:
    result_path = await DQScanService.get_result_path(task_id)
    data = json.loads(Path(result_path).read_text("utf-8"))
    return SuccessResponse(data=data, msg="获取成功")


@DQScanRouter.get("/tasks/{task_id}/download", summary="下载result.json", description="下载result.json")
async def download_result_controller(task_id: str) -> UploadFileResponse:
    result_path = await DQScanService.get_result_path(task_id)
    return UploadFileResponse(file_path=str(result_path), filename="result.json")


@DQScanRouter.get("/tasks/{task_id}/artifact", summary="下载任务产物", description="下载任务产物")
async def download_artifact_controller(task_id: str, path: str = Query(..., description="相对任务目录路径")) -> UploadFileResponse:
    artifact = await DQScanService.resolve_task_artifact(task_id, path)
    return UploadFileResponse(file_path=str(artifact), filename=artifact.name)

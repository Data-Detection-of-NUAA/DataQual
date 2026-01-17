# -*- coding: utf-8 -*-

from __future__ import annotations

from fastapi import APIRouter, WebSocket

from .service import DQScanService


WS_DQSCAN = APIRouter(
    prefix="/application/dqscan",
    tags=["数据集质量扫描（MVP）WebSocket"],
)


@WS_DQSCAN.websocket("/ws/{task_id}", name="DQScan WebSocket")
async def dqscan_ws_controller(websocket: WebSocket, task_id: str):
    state = await DQScanService.ws_connect(task_id, websocket)
    try:
        await DQScanService.ws_pump(state, websocket)
    finally:
        DQScanService.ws_disconnect(state, websocket)

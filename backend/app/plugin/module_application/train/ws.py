# -*- coding: utf-8 -*-

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.core.dependencies import AuthPermission
from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.logger import log
import json
from typing import Dict, Set
import asyncio

from .service import TrainTaskService
from .crud import TrainTaskCRUD

# WebSocket路由
TrainWebSocketRouter = APIRouter(prefix="/train", tags=["训练WebSocket"])


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, task_id: str, websocket: WebSocket):
        """建立连接"""
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)
        log.info(f"WebSocket连接建立: task_id={task_id}, 连接数={len(self.active_connections[task_id])}")

    def disconnect(self, task_id: str, websocket: WebSocket):
        """断开连接"""
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
            log.info(f"WebSocket连接断开: task_id={task_id}")

    async def broadcast_to_task(self, task_id: str, message: dict):
        """向任务的所有连接广播消息"""
        if task_id in self.active_connections:
            disconnected = set()
            for websocket in self.active_connections[task_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    log.warning(f"WebSocket发送消息失败: {e}")
                    disconnected.add(websocket)

            # 清理断开的连接
            for websocket in disconnected:
                self.disconnect(task_id, websocket)


# 全局连接管理器
manager = ConnectionManager()


@TrainWebSocketRouter.websocket("/ws/{task_id}")
async def train_websocket_endpoint(
    task_id: str,
    websocket: WebSocket
):
    """
    训练任务WebSocket连接

    提供实时训练日志和进度推送

    参数:
    - task_id: 训练任务ID

    消息格式:
    - 客户端发送: {"type": "subscribe"} 订阅任务更新
    - 服务端推送:
      - {"type": "progress", "data": {...}} 进度更新
      - {"type": "log", "data": {"level": "INFO", "message": "..."}} 日志消息
      - {"type": "status", "data": {"status": "running"}} 状态变更
    """
    # 创建临时认证对象用于数据库查询
    from app.core.database import async_db_session
    db_session = None

    try:
        # 创建临时数据库会话和认证对象
        db_session = async_db_session()
        temp_auth = AuthSchema(user=None, check_data_scope=False, db=db_session)

        # 验证任务存在
        task = await TrainTaskCRUD(temp_auth).get_by_task_id(task_id)
        if not task:
            await websocket.close(code=1008, reason="任务不存在")
            return

        # 建立连接
        await manager.connect(task_id, websocket)

        try:
            while True:
                # 接收客户端消息
                data = await websocket.receive_json()

                if data.get("type") == "subscribe":
                    # 客户端订阅，发送当前状态
                    current_progress = await TrainTaskService.get_latest_progress_service(temp_auth, task_id)
                    if current_progress:
                        await websocket.send_json({
                            "type": "progress",
                            "data": current_progress
                        })

                    # 发送任务状态
                    await websocket.send_json({
                        "type": "status",
                        "data": {
                            "status": task.status,
                            "current_epoch": task.current_epoch,
                            "total_epochs": task.total_epochs,
                            "progress_percentage": task.progress_percentage
                        }
                    })

                elif data.get("type") == "ping":
                    # 心跳包
                    await websocket.send_json({"type": "pong"})

        except WebSocketDisconnect:
            manager.disconnect(task_id, websocket)

    except Exception as e:
        log.error(f"WebSocket连接错误: {e}")
        try:
            await websocket.close(code=1011, reason="服务器错误")
        except:
            pass
    finally:
        # 关闭临时数据库会话
        if db_session is not None:
            await db_session.close()


# 广播进度更新的辅助函数
async def broadcast_progress_update(task_id: str, progress_data: dict):
    """广播进度更新"""
    await manager.broadcast_to_task(task_id, {
        "type": "progress",
        "data": progress_data
    })


async def broadcast_log_message(task_id: str, level: str, message: str):
    """广播日志消息"""
    await manager.broadcast_to_task(task_id, {
        "type": "log",
        "data": {
            "level": level,
            "message": message,
            "timestamp": str(asyncio.get_event_loop().time())
        }
    })


async def broadcast_status_change(task_id: str, old_status: str, new_status: str):
    """广播状态变更"""
    await manager.broadcast_to_task(task_id, {
        "type": "status",
        "data": {
            "old_status": old_status,
            "new_status": new_status,
            "timestamp": str(asyncio.get_event_loop().time())
        }
    })
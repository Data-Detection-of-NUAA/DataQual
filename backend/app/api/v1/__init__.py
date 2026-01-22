# -*- coding: utf-8 -*-

from fastapi import APIRouter

from app.api.v1.module_common import common_router
from app.api.v1.module_monitor import monitor_router
from app.api.v1.module_system import system_router

# 创建主路由
api_router = APIRouter(prefix="/api/v1")

# 注册各模块路由
api_router.include_router(common_router)
api_router.include_router(monitor_router)
api_router.include_router(system_router)

__all__ = ["api_router"]

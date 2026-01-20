# -*- coding: utf-8 -*-

from fastapi import APIRouter

from app.api.v1.module_common import common_router
from app.api.v1.module_monitor import monitor_router
from app.api.v1.module_system import system_router
# 导入 optimizer 模块路由
from optimizer.api.optimizer import diagnosis_router, strategy_router, review_router, execution_router

# 创建主路由
api_router = APIRouter(prefix="/api/v1")

# 注册各模块路由
api_router.include_router(common_router)
api_router.include_router(monitor_router)
api_router.include_router(system_router)
# 注册 optimizer 子路由
optimizer_router = APIRouter(prefix="/optimizer", tags=["数据优化器"])
optimizer_router.include_router(diagnosis_router)
optimizer_router.include_router(strategy_router)
optimizer_router.include_router(review_router)
optimizer_router.include_router(execution_router)
api_router.include_router(optimizer_router)

__all__ = ["api_router"]

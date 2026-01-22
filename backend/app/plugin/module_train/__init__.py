# -*- coding: utf-8 -*-

"""
模型训练模块

提供模型配置管理和智能推荐功能
"""

# 只导入模型，不导入 controller（避免循环导入）
# controller 会在动态路由发现时自动导入
from .train.model import (
    ModelConfigModel,
    ModelModalityEnum,
    ModelTaskTypeEnum,
    ModelStatusEnum
)

__all__ = [
    "ModelConfigModel",
    "ModelModalityEnum",
    "ModelTaskTypeEnum",
    "ModelStatusEnum",
]

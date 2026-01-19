"""
算法注册表（registry）。

为什么需要 registry？
- 后端需要提供“算法列表”给前端 → `list_algorithms()`
- 后端需要“按名字执行算法” → `get_algorithm(name)`

当前实现采用“懒发现”（lazy discover）：
- 第一次 list/get 时才 import 并 register 内置算法
- 好处：启动快、避免不必要依赖在 import 阶段就报错
"""

from __future__ import annotations

from typing import Any

from .base import Algorithm

_ALGORITHMS: dict[str, Algorithm] = {}
_DISCOVERED = False


def register(algorithm: Algorithm) -> None:
    """注册一个算法实例（通常在 `_discover()` 里调用）。"""
    name = algorithm.spec.name
    if not name:
        raise ValueError("algorithm.spec.name is required")
    if name in _ALGORITHMS:
        raise ValueError(f"algorithm already registered: {name}")
    _ALGORITHMS[name] = algorithm


def _discover() -> None:
    """发现并注册内置算法（只执行一次）。"""
    global _DISCOVERED
    if _DISCOVERED or _ALGORITHMS:
        return
    _DISCOVERED = True

    from .algorithms.tabular.quality_engine import TabularQualityEngine

    register(TabularQualityEngine())


def list_algorithms() -> list[dict[str, Any]]:
    """返回所有已注册算法的 spec 信息（用于 UI 展示）。"""
    _discover()
    return [
        {
            "name": alg.spec.name,
            "label": alg.spec.label,
            "description": alg.spec.description,
            "params_schema": alg.spec.params_schema,
        }
        for alg in _ALGORITHMS.values()
    ]


def get_algorithm(name: str) -> Algorithm:
    """按算法名获取算法实例（不存在则抛 KeyError）。"""
    _discover()
    if name in _ALGORITHMS:
        return _ALGORITHMS[name]

    # 兼容旧的“带版本号”算法名：例如 `xxx_v3` → `xxx`
    # 用户侧不再需要控制版本号，但历史任务/前端缓存可能仍会传旧值。
    if "_v" in name:
        base, suffix = name.rsplit("_v", 1)
        if suffix.isdigit() and base in _ALGORITHMS:
            return _ALGORITHMS[base]

    raise KeyError(f"unknown algorithm: {name}")

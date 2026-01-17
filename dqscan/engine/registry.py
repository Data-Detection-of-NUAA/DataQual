from __future__ import annotations

from typing import Any

from .base import Algorithm

_ALGORITHMS: dict[str, Algorithm] = {}
_DISCOVERED = False



def register(algorithm: Algorithm) -> None:
    name = algorithm.spec.name
    if not name:
        raise ValueError("algorithm.spec.name is required")
    if name in _ALGORITHMS:
        raise ValueError(f"algorithm already registered: {name}")
    _ALGORITHMS[name] = algorithm


def _discover() -> None:
    global _DISCOVERED
    if _DISCOVERED or _ALGORITHMS:
        return
    _DISCOVERED = True

    from .algorithms.tabular.quality_engine_v3 import TabularQualityEngineV3

    register(TabularQualityEngineV3())


def list_algorithms() -> list[dict[str, Any]]:
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
    _discover()
    try:
        return _ALGORITHMS[name]
    except KeyError as e:
        raise KeyError(f"unknown algorithm: {name}") from e

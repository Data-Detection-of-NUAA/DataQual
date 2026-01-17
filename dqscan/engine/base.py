from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol


EmitEvent = Callable[[dict[str, Any]], None]


@dataclass(frozen=True)
class AlgorithmSpec:
    name: str
    label: str
    description: str
    params_schema: dict[str, Any]


class Algorithm(Protocol):
    spec: AlgorithmSpec

    def run(
        self,
        *,
        input_path: str,
        output_dir: str,
        params: dict[str, Any] | None = None,
        emit: EmitEvent | None = None,
    ) -> dict[str, Any]: ...


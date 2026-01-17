# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import os
from abc import ABC
from datetime import datetime
from typing import Any


class BaseReporter(ABC):
    DATA_TYPE_LABELS = {
        "tabular": "表格数据",
        "timeseries": "时序数据",
        "image": "图像数据",
        "text": "文本数据",
        "graph": "图结构",
        "video": "视频",
        "audio": "语音",
        "pointcloud": "点云",
        "field": "场",
        "spectrum": "谱",
        "signal": "信号",
        "control": "控制指令",
        "mesh": "三维模型",
    }

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.report_dir = os.path.join(output_dir, "reports")
        os.makedirs(self.report_dir, exist_ok=True)

    def now_iso(self) -> str:
        return datetime.now().isoformat(timespec="seconds")

    def get_grade(self, score: float) -> str:
        if score >= 90:
            return "S"
        if score >= 80:
            return "A"
        if score >= 70:
            return "B"
        if score >= 60:
            return "C"
        return "D"

    def get_grade_full(self, score: float) -> str:
        if score >= 90:
            return "S (优秀)"
        if score >= 80:
            return "A (良好)"
        if score >= 70:
            return "B (中等)"
        if score >= 60:
            return "C (及格)"
        return "D (不及格)"

    def extract_module_type(self, report_name: str) -> str:
        if "_report_" in report_name:
            prefix = report_name.split("_report_")[0]
            if prefix in {"distribution", "dirty_data", "adversarial", "physics"}:
                return prefix
        return "all"

    def convert_numpy_types(self, obj: Any) -> Any:
        try:
            import numpy as np  # type: ignore

            if isinstance(obj, np.bool_):
                return bool(obj)
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, np.floating):
                if np.isnan(obj) or np.isinf(obj):
                    return None
                return float(obj)
            if isinstance(obj, np.ndarray):
                return [self.convert_numpy_types(x) for x in obj.tolist()]
        except Exception:
            pass

        if isinstance(obj, dict):
            return {k: self.convert_numpy_types(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self.convert_numpy_types(v) for v in obj]
        if isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        return str(obj)

    def save_json(self, data: dict[str, Any], filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.convert_numpy_types(data), f, indent=2, ensure_ascii=False)


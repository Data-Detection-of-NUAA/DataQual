"""
图片质量引擎（Image Quality Engine）。

与 TabularQualityEngine 平级的独立引擎，负责图片模态的质量检测。
当前支持的检测项：
- dirty_data.image_label_mismatch: 图片分类错标检测

接口契约：
- input_path: 解压后的图片目录路径（包含图片文件和 CSV 标签文件）
- params 必须包含:
  - label_csv_path: CSV 标签文件路径（相对于 input_path 或绝对路径）
  - image_column: CSV 中图片路径列名（默认 "image_path"）
  - label_column: CSV 中标签列名（默认 "label"）
  - defects.selected: 启用的缺陷检测项
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from dqscan.engine.base import AlgorithmSpec, EmitEvent

logger = logging.getLogger(__name__)


class ImageQualityEngine:
    """图片质量检测引擎。"""

    spec = AlgorithmSpec(
        name="image_quality_engine",
        label="图片质量引擎",
        description="面向图片分类数据集的质量检测引擎，支持图片错标检测等功能",
        params_schema={
            "label_csv_path": {
                "type": "string",
                "required": True,
                "description": "CSV 标签文件路径（相对于 input_path）",
            },
            "image_column": {
                "type": "string",
                "default": "image_path",
                "description": "CSV 中图片路径列名",
            },
            "label_column": {
                "type": "string",
                "default": "label",
                "description": "CSV 中标签列名",
            },
        },
    )

    def run(
        self,
        *,
        input_path: str,
        output_dir: str,
        params: dict[str, Any] | None = None,
        emit: EmitEvent | None = None,
    ) -> dict[str, Any]:
        """
        执行图片质量检测。

        Parameters
        ----------
        input_path : str
            解压后的图片目录路径
        output_dir : str
            输出目录（写 result.json）
        params : dict
            算法参数，必须包含 label_csv_path, image_column, label_column
        emit : callable, optional
            事件回调（log/progress/done/error）
        """
        params = params or {}
        os.makedirs(output_dir, exist_ok=True)
        start_time = time.time()

        def _emit(event: dict[str, Any]) -> None:
            if emit:
                emit(event)

        _emit({"type": "log", "message": "图片质量引擎启动..."})

        # --- 解析参数 ---
        label_csv_path = params.get("label_csv_path", "")
        image_column = params.get("image_column", "image_path")
        label_column = params.get("label_column", "label")

        defects_selected = params.get("defects", {}).get("selected", {})
        if not defects_selected:
            defects_selected = {"dirty_data.image_label_mismatch": params}

        # --- 解析 CSV 路径 ---
        if not os.path.isabs(label_csv_path):
            label_csv_path = os.path.join(input_path, label_csv_path)

        if not os.path.isfile(label_csv_path):
            msg = f"标签文件不存在: {label_csv_path}"
            _emit({"type": "error", "message": msg})
            return {"error": msg, "modules": {}}

        # --- 加载标签 CSV ---
        try:
            import pandas as pd
        except ImportError:
            msg = "缺少 pandas 依赖，无法读取标签文件"
            _emit({"type": "error", "message": msg})
            return {"error": msg, "modules": {}}

        _emit({"type": "log", "message": f"读取标签文件: {label_csv_path}"})
        try:
            label_df = pd.read_csv(label_csv_path)
        except Exception as exc:
            msg = f"标签文件读取失败: {exc}"
            _emit({"type": "error", "message": msg})
            return {"error": msg, "modules": {}}

        if image_column not in label_df.columns:
            msg = f"标签文件中缺少图片列 '{image_column}'，可用列: {list(label_df.columns)}"
            _emit({"type": "error", "message": msg})
            return {"error": msg, "modules": {}}

        if label_column not in label_df.columns:
            msg = f"标签文件中缺少标签列 '{label_column}'，可用列: {list(label_df.columns)}"
            _emit({"type": "error", "message": msg})
            return {"error": msg, "modules": {}}

        total_images = len(label_df)
        n_classes = label_df[label_column].nunique()
        _emit({
            "type": "log",
            "message": f"数据集: {total_images} 张图片, {n_classes} 个类别",
        })

        # --- 执行检测模块 ---
        modules_result: dict[str, Any] = {}

        # dirty_data.image_label_mismatch
        if "dirty_data.image_label_mismatch" in defects_selected:
            _emit({"type": "log", "message": "执行图片错标检测..."})
            _emit({"type": "progress", "value": 10})

            defect_params = defects_selected["dirty_data.image_label_mismatch"]
            if isinstance(defect_params, bool):
                defect_params = {}
            scanner_params = defect_params.get("params", defect_params)

            algorithm = scanner_params.get("algorithm", "simifeat_knn")

            try:
                from dqscan.scanner.image_scanner import ImageLabelMismatchScanner

                scanner = ImageLabelMismatchScanner(
                    algorithm=algorithm,
                    k=scanner_params.get("k", 10),
                    threshold=scanner_params.get("threshold", 0.5),
                    max_samples=scanner_params.get("max_samples", 5000),
                    max_examples=scanner_params.get("max_examples", 500),
                    batch_size=scanner_params.get("batch_size", 32),
                    device=scanner_params.get("device", "auto"),
                    model_name=scanner_params.get(
                        "model_name", "openai/clip-vit-base-patch32"
                    ),
                    hash_size=scanner_params.get("hash_size", 16),
                )

                scan_result = scanner.scan(
                    image_dir=input_path,
                    label_df=label_df,
                    image_column=image_column,
                    label_column=label_column,
                    output_dir=output_dir,
                    emit=_emit,
                )
                modules_result["dirty_data"] = {
                    "image_label_mismatch": scan_result,
                    "algorithm": scan_result.get("algorithm", algorithm),
                    "has_issues": scan_result.get("has_issues", False),
                    "total_issues": scan_result.get("total_issues", 0),
                    "issue_percentage": scan_result.get("issue_percentage", 0.0),
                }

            except Exception as exc:
                logger.exception("图片错标检测失败")
                modules_result["dirty_data"] = {
                    "image_label_mismatch": {
                        "error": str(exc),
                        "has_issues": False,
                        "total_issues": 0,
                        "issue_percentage": 0.0,
                    }
                }
                _emit({"type": "log", "message": f"图片错标检测失败: {exc}"})

        _emit({"type": "progress", "value": 90})

        # --- 汇总结果 ---
        elapsed = round(time.time() - start_time, 2)
        result = {
            "data_type": "image",
            "total_images": total_images,
            "n_classes": n_classes,
            "modules": modules_result,
            "elapsed_seconds": elapsed,
        }

        # 写 result.json
        result_path = os.path.join(output_dir, "result.json")
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)

        _emit({"type": "log", "message": f"图片质量检测完成，耗时 {elapsed}s"})
        _emit({"type": "progress", "value": 100})
        _emit({"type": "done", "result_file": result_path})

        return result

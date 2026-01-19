"""
表格数据质量探测引擎（四模块）。

这是 dqscan 的“编排层（orchestrator）”：
- 负责读取 CSV/TXT → pandas.DataFrame
- 依次调用四个 scanner（dirty_data / distribution / adversarial / physics）
- 统一生成报告（json/summary/docx）并写出 `result.json`
- 通过 `emit({...})` 回调把 log/progress/done 事件推给后端任务系统

真正的算法实现分别在 `dqscan` 内部的 scanner/reporters 模块中。
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from ...base import AlgorithmSpec, EmitEvent


class TabularQualityEngine:
    """
    引擎入口类（满足 `dqscan.engine.base.Algorithm` 协议）。

    - `spec`：提供给 UI/后端的元信息与参数 JSON Schema
    - `run`：执行入口（由后端线程池调用）
    """

    spec = AlgorithmSpec(
        name="tabular_quality_engine",
        label="表格数据质量探测引擎",
        description="脏数据扫描 / 分布偏差 / 对抗性 / 物理保真度，生成 JSON 摘要与 Word 报告。",
        params_schema={
            "type": "object",
            "properties": {
                "modules": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["dirty_data", "distribution", "adversarial", "physics"]},
                    "default": ["dirty_data", "distribution", "adversarial", "physics"],
                },
                "train_test_split": {"type": "number", "minimum": 0.1, "maximum": 0.9, "default": 0.7},
                "contamination": {"type": "number", "minimum": 0.0, "maximum": 0.5, "default": 0.1},
                "p_val": {"type": "number", "minimum": 0.0001, "maximum": 0.2, "default": 0.05},
                "exclude_columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "分布偏差检测可选：排除不参与对比的列（如 id/时间戳/高基数标识列）",
                },
                "adversarial": {
                    "type": "object",
                    "properties": {
                        "max_iter": {"type": "integer", "minimum": 1, "default": 20},
                        "epsilon": {"type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.05},
                    },
                    "default": {},
                },
                "physics": {
                    "type": "object",
                    "properties": {
                        "constraints": {"type": "object", "additionalProperties": True, "default": {}},
                        "check_conservation": {"type": "boolean", "default": False},
                    },
                    "default": {},
                },
                "read_csv": {
                    "type": "object",
                    "properties": {
                        "sep": {"type": ["string", "null"], "default": None},
                        "encoding": {"type": ["string", "null"], "default": None},
                    },
                    "default": {},
                },
            },
            "additionalProperties": True,
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
        执行扫描并在 output_dir 写入产物。

        参数:
        - input_path: CSV/TXT 路径（由后端 upload 得到）
        - output_dir: 输出目录（通常是 `backend/static/dqscan/tasks/{task_id}`）
        - params: 算法参数（见 `spec.params_schema`）
        - emit: 事件回调（log/progress/done/error）；若为 None 则静默运行

        返回:
        - result_jsonable: dict（已转换 numpy 类型，保证可 JSON 序列化）

        产物:
        - output_dir/result.json
        - output_dir/reports/*（每个模块的 json/summary/docx）
        """
        started = time.time()
        params = params or {}

        def _emit(e: dict[str, Any]) -> None:
            if emit is not None:
                emit(e)

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_dir = os.fspath(output_dir)
        input_path = os.fspath(input_path)

        # 模块选择：允许前端传 modules 子集；不合法的模块名会被过滤掉
        modules = params.get("modules") or ["dirty_data", "distribution", "adversarial", "physics"]
        modules = [m for m in modules if m in {"dirty_data", "distribution", "adversarial", "physics"}]
        if not modules:
            modules = ["dirty_data"]

        try:
            import numpy as np  # type: ignore
            import pandas as pd  # type: ignore
        except ImportError as e:
            raise RuntimeError(
                "运行四模块需要安装 pandas/numpy（完整能力还需要 scipy/sklearn/python-docx 等）"
            ) from e

        # 读 CSV 参数透传：sep/encoding（sep=None 时用 python engine 以兼容更多分隔符场景）
        read_csv_cfg = params.get("read_csv") or {}
        sep = read_csv_cfg.get("sep", None)
        encoding = read_csv_cfg.get("encoding", None)

        _emit({"type": "log", "message": f"读取文件：{os.path.basename(input_path)}"})
        df = pd.read_csv(input_path, sep=sep, engine="python" if sep is None else "c", encoding=encoding)
        _emit({"type": "log", "message": f"数据规模：{len(df)} 行, {len(df.columns)} 列"})

        from dqscan.scanner import (
            TabularAdversarialScanner,
            TabularDirtyScanner,
            TabularDistributionScanner,
            TabularPhysicsScanner,
        )
        from dqscan.reporters import DetectionReportGenerator

        task_reports: dict[str, Any] = {}
        module_results: dict[str, Any] = {}

        # 报告生成器会负责：写 reports/*.json & reports/*_summary.json & 可选 docx
        # 以及：把 numpy 类型转换成 JSON 兼容的 Python 类型
        report_generator = DetectionReportGenerator(output_dir=output_dir)

        for idx, module in enumerate(modules):
            # 进度是一个“粗粒度估算”：每跑完一个模块，进度推进一段
            base_progress = int((idx / max(len(modules), 1)) * 100)
            _emit({"type": "progress", "value": max(1, base_progress)})
            _emit({"type": "log", "message": f"开始模块：{module}"})

            if module == "dirty_data":
                # 脏数据：异常/缺失/重复/范围违规（pyod/pandas 依赖缺失时会降级）
                contamination = float(params.get("contamination", 0.1))
                scanner = TabularDirtyScanner(contamination=contamination)
                res = scanner.scan(df)

            elif module == "distribution":
                # 分布漂移（两种模式）：
                # 1) 传入基线文件（推荐）：baseline.csv vs current.csv
                # 2) 未传基线文件（兼容旧逻辑）：在同一份文件内按 train_test_split 切两段模拟对比
                p_val = float(params.get("p_val", 0.05))
                scanner = TabularDistributionScanner(p_val=p_val)

                # 排除列：用于避免把 id/时间戳/唯一标识 等“天然会变化”的列纳入漂移检测导致误报
                excluded: list[str] = []
                exclude_columns_raw = params.get("exclude_columns")
                if isinstance(exclude_columns_raw, list):
                    for x in exclude_columns_raw:
                        if isinstance(x, str) and x.strip():
                            excluded.append(x.strip())
                elif isinstance(exclude_columns_raw, str) and exclude_columns_raw.strip():
                    excluded.append(exclude_columns_raw.strip())
                excluded_set = set(excluded)
                if excluded:
                    preview = ", ".join(excluded[:10])
                    suffix = "" if len(excluded) <= 10 else f" 等{len(excluded)}列"
                    _emit({"type": "log", "message": f"分布检测排除列：{preview}{suffix}"})

                baseline_input_path = params.get("baseline_input_path")
                if isinstance(baseline_input_path, str) and baseline_input_path:
                    try:
                        _emit({"type": "log", "message": f"分布检测使用基线文件：{os.path.basename(baseline_input_path)}"})
                        baseline_df = pd.read_csv(
                            baseline_input_path,
                            sep=sep,
                            engine="python" if sep is None else "c",
                            encoding=encoding,
                        )
                    except Exception as e:
                        res = {
                            "algorithm": "MMD + K-S Test + Chi-Square",
                            "error": f"读取基线文件失败：{e}",
                            "has_issues": False,
                            "drift_detected": False,
                            "p_value": 1.0,
                            "total_issues": 0,
                            "issue_percentage": 0.0,
                            "comparison_mode": "baseline_file",
                        }
                    else:
                        # 对齐列：只检测两边都有的列（避免基线/新数据列不一致导致崩溃）
                        common_cols = [c for c in df.columns if c in baseline_df.columns]
                        if excluded_set:
                            common_cols = [c for c in common_cols if c not in excluded_set]
                        dropped_current = [c for c in df.columns if c not in common_cols]
                        dropped_baseline = [c for c in baseline_df.columns if c not in common_cols]
                        if not common_cols:
                            res = {
                                "algorithm": "MMD + K-S Test + Chi-Square",
                                "error": "基线文件与当前文件没有共同列，无法进行分布对比",
                                "has_issues": False,
                                "drift_detected": False,
                                "p_value": 1.0,
                                "total_issues": 0,
                                "issue_percentage": 0.0,
                                "comparison_mode": "baseline_file",
                            }
                        else:
                            if dropped_current or dropped_baseline:
                                _emit(
                                    {
                                        "type": "log",
                                        "message": f"列对齐：共同列 {len(common_cols)}；忽略当前文件列 {len(dropped_current)}；忽略基线文件列 {len(dropped_baseline)}",
                                    }
                                )
                            baseline_use = baseline_df[common_cols].copy()
                            current_use = df[common_cols].copy()
                            res = scanner.scan(baseline_use, current_use)
                            res["comparison_mode"] = "baseline_file"
                            res["baseline_filename"] = os.path.basename(baseline_input_path)
                            res["current_filename"] = os.path.basename(input_path)
                            res["excluded_columns"] = excluded
                else:
                    # 兼容旧逻辑：用 train/test 的切分来模拟“历史数据 vs 新数据”的漂移检测
                    split = float(params.get("train_test_split", 0.7))
                    df_use = df.drop(columns=excluded, errors="ignore") if excluded else df
                    if len(df_use.columns) == 0:
                        res = {
                            "algorithm": "MMD + K-S Test + Chi-Square",
                            "error": "分布检测：排除列后没有剩余列可检测",
                            "has_issues": False,
                            "drift_detected": False,
                            "p_value": 1.0,
                            "total_issues": 0,
                            "issue_percentage": 0.0,
                            "comparison_mode": "in_file_split",
                            "excluded_columns": excluded,
                        }
                    else:
                        split_idx = int(len(df_use) * split)
                        train_df = df_use.iloc[:split_idx].copy()
                        test_df = df_use.iloc[split_idx:].copy()
                        res = scanner.scan(train_df, test_df)
                        res["comparison_mode"] = "in_file_split"
                        res["excluded_columns"] = excluded

            elif module == "adversarial":
                # 对抗性：需要一个分类模型。本实现使用数值列训练“演示模型”，仅用于展示流程。
                try:
                    from sklearn.ensemble import RandomForestClassifier  # type: ignore
                except Exception as e:
                    res = {
                        "error": f"scikit-learn未安装，无法执行对抗性检测：{e}",
                        "has_issues": False,
                        "attack_success_rate": 0.0,
                        "robustness_score": 1.0,
                        "total_issues": 0,
                        "issue_percentage": 0.0,
                    }
                else:
                    numeric_df = df.select_dtypes(include=[np.number])
                    if numeric_df.empty:
                        res = {
                            "error": "未找到数值列",
                            "has_issues": False,
                            "attack_success_rate": 0.0,
                            "robustness_score": 1.0,
                            "total_issues": 0,
                            "issue_percentage": 0.0,
                        }
                    else:
                        # 构造一个演示任务：用第一列的中位数作为二分类标签。
                        # 真实业务中应替换为：你的业务标签/训练方式/模型。
                        X = numeric_df.values.astype(np.float32)
                        y = (X[:, 0] > np.median(X[:, 0])).astype(int)
                        _emit({"type": "log", "message": "训练演示模型：RandomForestClassifier"})
                        model = RandomForestClassifier(n_estimators=20, random_state=42)
                        model.fit(X, y)
                        adv_cfg = params.get("adversarial") or {}
                        scanner = TabularAdversarialScanner(
                            max_iter=int(adv_cfg.get("max_iter", 20)),
                            epsilon=float(adv_cfg.get("epsilon", 0.05)),
                        )
                        res = scanner.scan(model, X[:50], y[:50], model_type="sklearn", max_samples=50)

            elif module == "physics":
                # 物理保真度：从 params 读取用户约束，同时补充一些启发式默认约束（age/price/temp/rate 等）
                phy_cfg = params.get("physics") or {}
                constraints: dict[str, dict[str, Any]] = {}
                user_constraints = phy_cfg.get("constraints") or {}
                if isinstance(user_constraints, dict):
                    for k, v in user_constraints.items():
                        if isinstance(v, dict):
                            constraints[str(k)] = {**v}

                for col in df.select_dtypes(include=[np.number]).columns:
                    col_lower = str(col).lower()
                    if col in constraints:
                        continue
                    if "age" in col_lower:
                        constraints[str(col)] = {"min": 0, "max": 120}
                    elif "price" in col_lower or "amount" in col_lower:
                        constraints[str(col)] = {"min": 0}
                    elif "temperature" in col_lower or "temp" in col_lower:
                        constraints[str(col)] = {"min": -273.15, "max": 1000}
                    elif "rate" in col_lower or "ratio" in col_lower:
                        constraints[str(col)] = {"min": 0, "max": 1}

                scanner = TabularPhysicsScanner(
                    constraints=constraints,
                    check_conservation=bool(phy_cfg.get("check_conservation", False)),
                )
                res = scanner.scan(df)

            else:
                res = {"error": f"未知模块: {module}"}

            module_results[module] = res

            # 每个模块输出一个报告集合（json/summary/docx），并把路径写入 result.json，供后端下载
            report_name = f"{module}_report_tabular"
            report_paths_abs = report_generator.generate_full_report(
                {"tabular": res}, report_name=report_name, generate_docx=True
            )
            report_paths: dict[str, Any] = {}
            for k, v in report_paths_abs.items():
                if k.endswith("_error"):
                    report_paths[k] = v
                    continue
                try:
                    report_paths[k] = os.path.relpath(str(v), output_dir)
                except Exception:
                    report_paths[k] = str(v)

            task_reports[module] = {"report_name": report_name, "paths": report_paths}

            _emit({"type": "log", "message": f"完成模块：{module}"})

        result = {
            "summary": {
                "status": "SUCCESS",
                "data_type": "tabular",
                "modules": modules,
                "elapsed_seconds": round(time.time() - started, 3),
            },
            "modules": module_results,
            "reports": task_reports,
        }

        # 写 result.json 前统一做 numpy → Python 类型转换，保证 JSON dumps 不会失败
        result_jsonable = report_generator.convert_numpy_types(result)
        Path(output_dir, "result.json").write_text(
            json.dumps(result_jsonable, ensure_ascii=False, indent=2),
            "utf-8",
        )
        _emit({"type": "progress", "value": 100})
        _emit({"type": "done", "message": "扫描完成"})
        return result_jsonable

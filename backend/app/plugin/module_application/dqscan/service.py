# -*- coding: utf-8 -*-

"""
dqscan 后端适配层：任务管理 + 运行引擎 + WebSocket 推送

这层代码的定位是“工程胶水”，把仓库根目录的 `dqscan/` 算法引擎接入 FastAPI：

- 上传文件落盘：`backend/static/dqscan/uploads/`
- 创建任务目录：`backend/static/dqscan/tasks/{task_id}/`
- 异步执行算法：`asyncio.to_thread(alg.run, ...)` 避免阻塞事件循环
- 事件推送：算法通过 `emit({...})` 上报 log/progress/done/error，本服务广播到 WebSocket 客户端

注意：
- 任务运行态（ws_clients/queue）仍在内存；任务元数据会落库（服务重启后可查询已结束任务的状态与结果索引）；
- 结果文件落盘在 static 目录，因此前端可通过 “result/artifact” 接口拉取。
"""

from __future__ import annotations

import asyncio
import copy
import json
import os
import shutil
import sys
import time
import uuid
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import UploadFile, WebSocket
from sqlalchemy import select, update

from app.core.logger import log
from app.config.path_conf import BASE_DIR, STATIC_DIR
from app.core.database import async_db_session

from .model import DQScanTaskModel


def _find_repo_root() -> Path:
    """
    定位仓库根目录。

    由于算法引擎 `dqscan/` 放在仓库根目录，而后端运行入口在 `backend/`，这里通过向上
    查找同时包含 `backend/` 和 `frontend/` 的目录来判断 repo root，便于把根目录塞进 sys.path。
    """
    here = Path(__file__).resolve()
    for p in here.parents:
        if (p / "backend").is_dir() and (p / "frontend").is_dir():
            return p
    return here.parents[5]


def _ensure_dqscan_importable() -> None:
    """确保 `import dqscan` 可用（将 repo root 注入 `sys.path`）。"""
    repo_root = _find_repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def _dqscan_root() -> Path:
    """dqscan 的静态根目录：`backend/static/dqscan/`。"""
    return STATIC_DIR / "dqscan"


def _uploads_root() -> Path:
    """上传目录：`backend/static/dqscan/uploads/`。"""
    return _dqscan_root() / "uploads"


def _tasks_root() -> Path:
    """任务目录：`backend/static/dqscan/tasks/`。"""
    return _dqscan_root() / "tasks"


def _safe_rel_file_id(abs_path: Path) -> str:
    """
    将绝对路径转换为“相对 backend 根目录”的 file_id（用于接口返回）。

    这是一个安全边界：只允许返回位于 `backend/` 目录下的路径，避免把任意系统路径暴露给前端。
    """
    abs_path = abs_path.resolve()
    base = BASE_DIR.resolve()
    if base not in abs_path.parents and abs_path != base:
        raise ValueError("path must be under backend base dir")
    return str(abs_path.relative_to(base)).replace("\\", "/")


def _resolve_file_id(file_id: str) -> Path:
    """
    将 file_id（相对 backend 根目录路径）解析成绝对路径，并做路径穿越防护。

    约束：
    - 只允许访问 `backend/static/dqscan/` 下的文件（上传文件、任务产物等）
    """
    file_id = file_id.lstrip("/").replace("\\", "/")
    abs_path = (BASE_DIR / file_id).resolve()
    dq_root = _dqscan_root().resolve()
    if dq_root not in abs_path.parents:
        raise ValueError("invalid file_id")
    return abs_path


_BASE_DIRTY_ALGOS = [
    {
        "key": "ecod_3sigma",
        "label": "通用脏数据扫描器（ECOD + 3σ）",
        "desc": "一次扫描输出异常/缺失/重复/值域四类信号；有 pyod 则 ECOD，无依赖时降级为 3σ 规则。",
        "status": "ready",
    },
    {"key": "isolation_forest", "label": "IsolationForest", "desc": "对高维数值更稳定的异常检测。", "status": "planned"},
    {"key": "ruleset", "label": "可配置规则引擎", "desc": "按字段类型/业务规则进行检查。", "status": "planned"},
    {"key": "autoencoder", "label": "AutoEncoder 异常检测", "desc": "适合大规模/非线性异常。", "status": "planned"},
]

_DISTRIBUTION_ALGOS = [
    {
        "key": "mmd_ks_chi2",
        "label": "MMD + KS + 卡方（两样本）",
        "desc": "对数值列做 MMD/KS，对类别列做卡方检验，输出 drift_detected 与 p_value。",
        "status": "ready",
    },
    {"key": "psi", "label": "PSI（Population Stability Index）", "desc": "更适合离散/分箱场景，输出稳定性指数。", "status": "planned"},
    {"key": "wasserstein", "label": "Wasserstein 距离", "desc": "对连续分布的距离度量，可用于分布差异排序。", "status": "planned"},
    {"key": "embedding_mmd", "label": "Embedding 分布漂移（文本/图像）", "desc": "对非结构化数据先做 embedding，再做分布对比。", "status": "planned"},
]

_ADVERSARIAL_ALGOS = [
    {
        "key": "zoo_or_random",
        "label": "ZOO（ART）/ 随机扰动",
        "desc": "有 ART 则用 ZOO 黑盒攻击；无 ART 则使用随机扰动搜索降级。",
        "status": "ready",
    },
    {"key": "fgsm", "label": "FGSM（白盒）", "desc": "快速白盒攻击，需要梯度支持。", "status": "planned"},
    {"key": "pgd", "label": "PGD（白盒）", "desc": "更强的迭代攻击，需要梯度支持。", "status": "planned"},
    {"key": "cw", "label": "C&W（白盒）", "desc": "优化式攻击，需要梯度支持。", "status": "planned"},
]

_PHYSICS_ALGOS = [
    {
        "key": "pandera_or_fallback",
        "label": "Pandera Schema / 基础校验",
        "desc": "有 pandera 则 schema 校验，否则使用基本 min/max 规则验证。",
        "status": "ready",
    },
    {
        "key": "cross_constraints",
        "label": "跨字段约束（守恒/一致性）",
        "desc": "启用输入输出守恒等跨字段启发式规则（已接入）。",
        "status": "ready",
    },
    {"key": "causal_graph", "label": "因果图一致性", "desc": "基于因果图做一致性检查。", "status": "planned"},
    {"key": "temporal_rules", "label": "时序物理规律", "desc": "适用于时序数据的物理规律校验。", "status": "planned"},
]


_DIRTY_MISSING_ALGOS = _BASE_DIRTY_ALGOS + [
    {
        "key": "missing_stats_threshold",
        "label": "缺失统计 + 阈值",
        "desc": "统计每列缺失率，超过阈值则告警，并输出影响字段与缺失分布。",
        "status": "ready",
    },
    {
        "key": "missing_pattern_mcar",
        "label": "缺失模式分析（MCAR/MAR）",
        "desc": "分析缺失是否与其他字段相关，定位系统性缺失与采集偏差。",
        "status": "planned",
    },
    {
        "key": "auto_imputation_suggest",
        "label": "自动补全建议（KNN/Iterative）",
        "desc": "给出补全策略与风险提示，辅助数据修复。",
        "status": "planned",
    },
    {
        "key": "missing_correlation_heatmap",
        "label": "缺失相关性热力图",
        "desc": "以可视化方式呈现缺失相关结构，便于快速排查。",
        "status": "planned",
    },
]

_DIRTY_DUPLICATE_ALGOS = _BASE_DIRTY_ALGOS + [
    {
        "key": "exact_duplicate",
        "label": "完全重复检测",
        "desc": "按整行或关键字段判断重复，输出重复率与示例行。",
        "status": "ready",
    },
    {
        "key": "near_duplicate_similarity",
        "label": "近重复（相似度）",
        "desc": "支持“近重复/模糊重复”识别（例如文本字段轻微差异）。",
        "status": "planned",
    },
    {"key": "minhash_lsh", "label": "MinHash + LSH", "desc": "适合大规模去重的近似方法。", "status": "planned"},
    {
        "key": "record_linkage",
        "label": "Record Linkage（实体对齐）",
        "desc": "针对多字段拼接的“同一实体多条记录”识别。",
        "status": "planned",
    },
]

_DIRTY_RANGE_ALGOS = _BASE_DIRTY_ALGOS + [
    {"key": "sigma_rule", "label": "3σ 规则", "desc": "用均值±kσ 的启发式方式发现可疑极值。", "status": "ready"},
    {"key": "iqr_rule", "label": "IQR 规则", "desc": "对长尾分布更稳健的四分位距方法。", "status": "planned"},
    {"key": "domain_rules", "label": "业务规则（min/max/枚举）", "desc": "按字段业务约束检查取值范围。", "status": "planned"},
    {"key": "schema_constraints", "label": "Schema 约束联动", "desc": "与 Pandera/规则库联动，统一落地字段约束。", "status": "planned"},
]

_LABEL_MISMATCH_ALGOS = [
    {
        "key": "confident_learning",
        "label": "Confident Learning（错标候选集）",
        "desc": "基于 out-of-fold 概率的 label quality score + 按类剪枝，输出疑似错标候选集与混淆方向。",
        "status": "ready",
    },
    {
        "key": "cv_consistency",
        "label": "交叉验证一致性",
        "desc": "通过交叉验证训练并找出“模型强烈不认可的标签”样本。",
        "status": "ready",
    },
    {
        "key": "embedding_knn",
        "label": "Embedding + KNN 近邻一致性",
        "desc": "在特征/embedding 空间中检查近邻标签一致性，发现疑似错标。",
        "status": "planned",
    },
    {
        "key": "confidence_margin",
        "label": "置信度边界样本",
        "desc": "识别高不确定样本与置信度异常样本，辅助人工复核。",
        "status": "planned",
    },
]

_DEFECT_CATALOG = {
    "modality": "tabular",
    "engine": "tabular_quality_engine",
    "tree": [
        {
            "key": "dirty_data",
            "label": "脏数据体系",
            "desc": "完整性 / 一致性 / 异常与噪声 / 标注质量",
            "children": [
                {
                    "key": "dirty_data.group_integrity",
                    "label": "完整性（Completeness）",
                    "desc": "缺失、空值、字段缺失等",
                    "children": [
                        {
                            "key": "dirty_data.missing",
                            "label": "缺失值异常",
                            "desc": "统计缺失率与缺失模式，定位缺失严重字段。",
                            "badge": {"text": "推荐", "type": "success"},
                            "status": "ready",
                            "module": "dirty_data",
                            "algorithms": _DIRTY_MISSING_ALGOS,
                        }
                    ],
                },
                {
                    "key": "dirty_data.group_noise",
                    "label": "异常与噪声（Outliers）",
                    "desc": "异常点、极值、噪声样本",
                    "children": [
                        {
                            "key": "dirty_data.anomaly",
                            "label": "异常样本（Outlier）",
                            "desc": "无监督异常检测，定位疑似异常行与可疑字段。",
                            "badge": {"text": "推荐", "type": "success"},
                            "status": "ready",
                            "module": "dirty_data",
                            "algorithms": _BASE_DIRTY_ALGOS,
                        },
                        {
                            "key": "dirty_data.range",
                            "label": "值域违规",
                            "desc": "用统计规则或业务规则识别异常取值范围。",
                            "status": "ready",
                            "module": "dirty_data",
                            "algorithms": _DIRTY_RANGE_ALGOS,
                        },
                    ],
                },
                {
                    "key": "dirty_data.group_consistency",
                    "label": "一致性（Consistency）",
                    "desc": "重复、矛盾、规则不一致等",
                    "children": [
                        {
                            "key": "dirty_data.duplicate",
                            "label": "重复 / 近重复",
                            "desc": "识别完全重复与近重复记录，输出去重建议。",
                            "status": "ready",
                            "module": "dirty_data",
                            "algorithms": _DIRTY_DUPLICATE_ALGOS,
                        }
                    ],
                },
                {
                    "key": "dirty_data.group_label",
                    "label": "标注质量（Label）",
                    "desc": "错标、弱标注、标签噪声",
                    "children": [
                        {
                            "key": "dirty_data.label_mismatch",
                            "label": "疑似错标（Label Mismatch）",
                            "desc": "识别“标签与特征不一致”的样本（如猫被标成狗）。",
                            "badge": {"text": "可用", "type": "success"},
                            "status": "ready",
                            "module": "dirty_data",
                            "algorithms": _LABEL_MISMATCH_ALGOS,
                        }
                    ],
                },
            ],
        },
        {
            "key": "distribution",
            "label": "分布偏差体系",
            "desc": "训练/基线 vs 当前数据分布变化监控",
            "children": [
                {
                    "key": "distribution.group_feature",
                    "label": "特征漂移（Feature Drift）",
                    "desc": "数值/类别特征的分布变化",
                    "children": [
                        {
                            "key": "distribution.numeric_drift",
                            "label": "数值特征漂移",
                            "desc": "对连续特征分布做两样本检验，输出漂移结论与 p 值。",
                            "badge": {"text": "推荐", "type": "success"},
                            "status": "ready",
                            "module": "distribution",
                            "algorithms": _DISTRIBUTION_ALGOS,
                        },
                        {
                            "key": "distribution.categorical_drift",
                            "label": "类别特征漂移",
                            "desc": "对离散特征做卡方等检验，定位漂移字段。",
                            "status": "ready",
                            "module": "distribution",
                            "algorithms": _DISTRIBUTION_ALGOS,
                        },
                    ],
                },
                {
                    "key": "distribution.group_label",
                    "label": "标签漂移（Label Shift）",
                    "desc": "标签分布变化与类别占比变化",
                    "children": [
                        {
                            "key": "distribution.label_shift",
                            "label": "标签分布变化",
                            "desc": "对标签列做分布对比，监控类占比突变与先验变化。",
                            "status": "ready",
                            "module": "distribution",
                            "algorithms": _DISTRIBUTION_ALGOS,
                        }
                    ],
                },
                {
                    "key": "distribution.group_unstructured",
                    "label": "非结构化漂移",
                    "desc": "文本/图像 embedding 的漂移监控",
                    "children": [
                        {
                            "key": "distribution.embedding_drift",
                            "label": "Embedding 分布漂移（文本/图像）",
                            "desc": "对非结构化数据先做 embedding，再做分布对比。",
                            "badge": {"text": "即将上线", "type": "warning"},
                            "status": "planned",
                            "disabled": True,
                            "module": "distribution",
                            "algorithms": _DISTRIBUTION_ALGOS,
                        }
                    ],
                },
            ],
        },
        {
            "key": "adversarial",
            "label": "对抗性与鲁棒性体系",
            "desc": "黑盒/白盒攻击下模型脆弱性评估",
            "children": [
                {
                    "key": "adversarial.group_attack",
                    "label": "攻击评估（Attack）",
                    "desc": "攻击成功率、扰动预算与鲁棒性",
                    "children": [
                        {
                            "key": "adversarial.blackbox",
                            "label": "黑盒攻击（ZOO/随机）",
                            "desc": "在无梯度条件下进行黑盒攻击，评估模型易受攻击程度。",
                            "badge": {"text": "可用", "type": "success"},
                            "status": "ready",
                            "module": "adversarial",
                            "algorithms": _ADVERSARIAL_ALGOS,
                        },
                        {
                            "key": "adversarial.whitebox",
                            "label": "白盒攻击（FGSM/PGD）",
                            "desc": "基于梯度的白盒攻击评估（需要模型与梯度接口）。",
                            "badge": {"text": "即将上线", "type": "warning"},
                            "status": "planned",
                            "disabled": True,
                            "module": "adversarial",
                            "algorithms": _ADVERSARIAL_ALGOS,
                        },
                    ],
                },
                {
                    "key": "adversarial.group_monitor",
                    "label": "鲁棒性监控（Monitoring）",
                    "desc": "敏感特征、鲁棒性分解与风险提示",
                    "children": [
                        {
                            "key": "adversarial.sensitivity",
                            "label": "特征敏感性分析",
                            "desc": "识别对扰动最敏感的特征与子群体风险。",
                            "badge": {"text": "即将上线", "type": "warning"},
                            "status": "planned",
                            "disabled": True,
                            "module": "adversarial",
                            "algorithms": _ADVERSARIAL_ALGOS,
                        }
                    ],
                },
            ],
        },
        {
            "key": "physics",
            "label": "物理保真度与规则体系",
            "desc": "按列配置约束与业务规则，扫描数据质量",
            "children": [
                {
                    "key": "physics.rules",
                    "label": "规则扫描",
                    "desc": "对每列设置 min/max、非空、正则、允许值等约束，支持跨列关系/条件/求和/唯一性规则。",
                    "badge": {"text": "推荐", "type": "success"},
                    "status": "ready",
                    "module": "physics",
                    "algorithms": _PHYSICS_ALGOS,
                }
            ],
        },
    ],
}

_IMAGE_DEFECT_CATALOG = {
    "modality": "image",
    "engine": "image_quality_engine",
    "tree": [
        {
            "key": "dirty_data",
            "label": "脏数据体系",
            "children": [
                {
                    "key": "dirty_data.image_label_mismatch",
                    "label": "图片分类错标检测",
                    "desc": "检测图片数据集中标签可能标错的样本，基于视觉特征与标签一致性分析",
                    "group": "group_label",
                    "group_label": "标签质量",
                    "status": "ready",
                    "algorithms": [
                        {"key": "simifeat_knn", "label": "SimiFeat KNN (CLIP)", "status": "ready", "badge": "推荐"},
                        {"key": "phash_outlier", "label": "pHash 类内离群", "status": "ready", "badge": "轻量"},
                    ],
                    "params_schema": {
                        "label_column": {"type": "string", "required": True, "default": "label"},
                        "image_column": {"type": "string", "required": True, "default": "image_path"},
                        "k": {"type": "int", "default": 10, "min": 3, "max": 50},
                        "threshold": {"type": "float", "default": 0.5, "min": 0.1, "max": 0.9},
                    },
                }
            ],
        }
    ],
}


@dataclass
class _TaskState:
    """任务在内存中的运行态状态（给 HTTP 查询与 WS snapshot 使用）。"""
    task_id: str
    data_type: str = "tabular"  # tabular | image
    status: str = "PENDING"
    progress: int = 0
    started_at: float | None = None
    ended_at: float | None = None
    error: str | None = None
    baseline_file_id: str | None = None
    result_file_id: str | None = None
    # 每个 websocket 连接对应一个 queue：生产者（算法线程）写入事件，消费者（ws_pump）读取并发送
    ws_clients: dict[WebSocket, asyncio.Queue[dict[str, Any]]] = field(default_factory=dict)


class DQScanService:
    """
    dqscan 服务层（不入库的轻量任务系统）。

    - `_tasks`：内存任务表（task_id -> state）
    - `_run_task`：后台协程，负责调用算法并写出 result.json
    - WebSocket：允许前端订阅实时日志与进度
    """

    _tasks: dict[str, _TaskState] = {}
    _lock = asyncio.Lock()

    @classmethod
    async def _db_create_task(
        cls,
        *,
        task_id: str,
        file_id: str,
        baseline_file_id: str | None,
        algorithm: str,
        params: dict[str, Any] | None,
    ) -> None:
        """创建任务元数据（DB 持久化，失败则降级为仅内存态/落盘）。"""
        try:
            async with async_db_session() as session:
                async with session.begin():
                    obj = DQScanTaskModel(
                        task_id=task_id,
                        task_status="PENDING",
                        progress=0,
                        algorithm=algorithm,
                        file_id=file_id,
                        baseline_file_id=baseline_file_id,
                        params_json=json.dumps(params or {}, ensure_ascii=False),
                        result_file_id=None,
                        error=None,
                        started_time=None,
                        ended_time=None,
                    )
                    session.add(obj)
        except Exception as e:
            log.warning(f"⚠️ dqscan 任务入库失败（将仅保留落盘文件与内存态）: {e}")

    @classmethod
    async def _db_get_task(cls, task_id: str) -> DQScanTaskModel | None:
        """按 task_id 查询任务记录（DB）。"""
        try:
            async with async_db_session() as session:
                result = await session.execute(select(DQScanTaskModel).where(DQScanTaskModel.task_id == task_id))
                return result.scalars().first()
        except Exception as e:
            log.warning(f"⚠️ dqscan 查询任务失败: {e}")
            return None

    @classmethod
    async def _db_update_task(cls, task_id: str, values: dict[str, Any]) -> None:
        """按 task_id 更新任务记录（DB）。"""
        if not values:
            return
        try:
            async with async_db_session() as session:
                async with session.begin():
                    await session.execute(update(DQScanTaskModel).where(DQScanTaskModel.task_id == task_id).values(**values))
        except Exception as e:
            log.warning(f"⚠️ dqscan 更新任务失败: {e}")

    @classmethod
    async def list_algorithms(cls) -> list[dict[str, Any]]:
        """返回算法引擎中已注册的算法列表（供前端下拉选择）。"""
        _ensure_dqscan_importable()
        from dqscan.engine import list_algorithms

        return list_algorithms()

    @classmethod
    async def get_defects_catalog(cls, *, modality: str = "tabular", engine: str | None = None) -> dict[str, Any]:
        """返回缺陷树（用于前端渲染缺陷体系与算法选项）。"""
        _CATALOG_MAP: dict[str, dict[str, Any]] = {
            "tabular": _DEFECT_CATALOG,
            "image": _IMAGE_DEFECT_CATALOG,
        }
        catalog = _CATALOG_MAP.get(modality)
        if catalog is None:
            raise ValueError(f"不支持的模态: {modality}，当前支持: {', '.join(_CATALOG_MAP)}")
        if engine and engine != catalog["engine"]:
            raise ValueError(f"engine 不匹配（期望 {catalog['engine']}，收到 {engine}）")
        return copy.deepcopy(catalog)

    # ZIP 上传限制常量
    _ZIP_MAX_BYTES: int = 2 * 1024 * 1024 * 1024  # 2 GB
    _ZIP_MAX_FILES: int = 50_000
    _ZIP_ALLOWED_IMAGE_EXTS: set[str] = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

    @classmethod
    async def upload(cls, file: UploadFile, *, max_bytes: int) -> dict[str, Any]:
        """
        上传文件落盘到 static 目录，并返回 file_id。

        - 以 1MB chunk 读取，避免把大文件一次性加载进内存；
        - 超过 max_bytes 直接报错；
        - 返回的 file_id 是“相对 backend 根目录”的路径字符串。
        - 支持 .zip 文件上传（用于图片数据集），会解压提取图片与 CSV 文件。
        """
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in {".csv", ".txt", ".zip"}:
            raise ValueError("仅支持 .csv / .txt / .zip")

        _uploads_root().mkdir(parents=True, exist_ok=True)
        file_id = f"{uuid.uuid4().hex}_{Path(file.filename or 'upload').name}"
        target = (_uploads_root() / file_id).resolve()

        size = 0
        try:
            with open(target, "wb") as f:
                while True:
                    chunk = await file.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > max_bytes:
                        raise ValueError(f"文件超过大小限制：{max_bytes} bytes")
                    f.write(chunk)
        except Exception:
            try:
                target.unlink(missing_ok=True)
            except Exception:
                pass
            raise

        # 非 ZIP 文件：直接返回
        if suffix != ".zip":
            return {
                "file_id": _safe_rel_file_id(target),
                "filename": file.filename or target.name,
                "file_size": size,
            }

        # --- ZIP 文件处理 ---
        return await cls._handle_zip_upload(target, file.filename or target.name, size)

    @classmethod
    async def _handle_zip_upload(cls, zip_path: Path, original_filename: str, zip_size: int) -> dict[str, Any]:
        """
        解压 ZIP 文件，提取图片与 CSV，返回结构化信息。

        安全措施：
        - Zip Slip 防护：验证解压路径不越过目标目录
        - 总大小限制 2 GB
        - 文件数限制 50,000
        - 仅提取图片格式与 CSV
        """
        extract_dir_name = f"{uuid.uuid4().hex}_images"
        extract_dir = (_uploads_root() / extract_dir_name).resolve()

        try:
            extract_dir.mkdir(parents=True, exist_ok=True)

            image_count = 0
            csv_files: list[str] = []
            total_extracted_size = 0
            file_count = 0

            with zipfile.ZipFile(zip_path, "r") as zf:
                for info in zf.infolist():
                    # 跳过目录条目
                    if info.is_dir():
                        continue

                    entry_suffix = Path(info.filename).suffix.lower()
                    is_image = entry_suffix in cls._ZIP_ALLOWED_IMAGE_EXTS
                    is_csv = entry_suffix == ".csv"

                    # 仅提取图片和 CSV
                    if not is_image and not is_csv:
                        continue

                    # 文件数限制
                    file_count += 1
                    if file_count > cls._ZIP_MAX_FILES:
                        raise ValueError(f"ZIP 内文件数超过限制：{cls._ZIP_MAX_FILES}")

                    # 总大小限制
                    total_extracted_size += info.file_size
                    if total_extracted_size > cls._ZIP_MAX_BYTES:
                        raise ValueError(f"ZIP 解压总大小超过限制：{cls._ZIP_MAX_BYTES} bytes")

                    # Zip Slip 防护：确保解压路径不越过目标目录
                    target_path = (extract_dir / info.filename).resolve()
                    if extract_dir not in target_path.parents and target_path != extract_dir:
                        raise ValueError(f"Zip Slip 攻击检测：非法路径 {info.filename}")

                    # 创建父目录并解压
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(info) as src, open(target_path, "wb") as dst:
                        shutil.copyfileobj(src, dst)

                    if is_image:
                        image_count += 1
                    elif is_csv:
                        # 返回相对于 extract_dir 的路径
                        csv_files.append(str(target_path.relative_to(extract_dir)))

            return {
                "file_id": _safe_rel_file_id(extract_dir),
                "filename": original_filename,
                "file_size": zip_size,
                "image_count": image_count,
                "csv_files": csv_files,
            }
        except Exception:
            # 清理解压目录
            try:
                if extract_dir.exists():
                    shutil.rmtree(extract_dir)
            except Exception:
                pass
            # 清理原始 ZIP 文件
            try:
                zip_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise

    @classmethod
    async def create_task(
        cls,
        *,
        file_id: str,
        baseline_file_id: str | None,
        algorithm: str,
        params: dict[str, Any] | None,
        data_type: str = "tabular",
    ) -> str:
        """
        创建任务并异步执行。

        返回 task_id。任务执行不阻塞当前 HTTP 请求（后台运行）。

        参数:
            data_type: 数据模态，"tabular"（默认）或 "image"。
                       image 模态下 algorithm 默认为 "image_quality_engine"。
        """
        if data_type not in {"tabular", "image"}:
            raise ValueError(f"不支持的 data_type: {data_type}")

        # image 模态默认 algorithm
        if data_type == "image" and not algorithm:
            algorithm = "image_quality_engine"

        cls._validate_params(params, baseline_file_id, data_type=data_type)
        task_id = uuid.uuid4().hex
        task_dir = (_tasks_root() / task_id).resolve()
        task_dir.mkdir(parents=True, exist_ok=True)

        state = _TaskState(
            task_id=task_id, data_type=data_type, status="PENDING", progress=0, baseline_file_id=baseline_file_id
        )
        async with cls._lock:
            cls._tasks[task_id] = state

        await cls._db_create_task(
            task_id=task_id,
            file_id=file_id,
            baseline_file_id=baseline_file_id,
            algorithm=algorithm,
            params=params,
        )

        asyncio.create_task(
            cls._run_task(
                state=state,
                file_id=file_id,
                baseline_file_id=baseline_file_id,
                algorithm=algorithm,
                params=params,
            )
        )
        return task_id

    @classmethod
    def _validate_params(
        cls, params: dict[str, Any] | None, baseline_file_id: str | None, *, data_type: str = "tabular"
    ) -> None:
        """按 data_type 分派参数校验。"""
        if data_type == "image":
            cls._validate_params_image(params)
            return
        # --- tabular 校验（原有逻辑） ---
        cls._validate_params_tabular(params, baseline_file_id)

    @classmethod
    def _validate_params_tabular(cls, params: dict[str, Any] | None, baseline_file_id: str | None) -> None:
        """表格模态的参数校验（原有逻辑，保持不变）。"""
        if not params or not isinstance(params, dict):
            return

        modules_config = params.get("modules_config") if isinstance(params.get("modules_config"), dict) else {}
        defects_cfg = params.get("defects") if isinstance(params.get("defects"), dict) else {}
        defects_selected = defects_cfg.get("selected") if isinstance(defects_cfg.get("selected"), dict) else {}

        dist_cfg_raw = modules_config.get("distribution") if isinstance(modules_config, dict) else None
        dist_cfg = dist_cfg_raw if isinstance(dist_cfg_raw, dict) else {}
        compare_mode = params.get("distribution_compare_mode") or dist_cfg.get("compare_mode")
        modules = params.get("modules") if isinstance(params.get("modules"), list) else []
        if not modules and defects_selected:
            for defect_key, cfg in defects_selected.items():
                if not isinstance(cfg, dict):
                    continue
                mk = cfg.get("module") or (defect_key.split(".", 1)[0] if isinstance(defect_key, str) else None)
                if mk:
                    modules.append(str(mk))

        if compare_mode == "baseline_file" and "distribution" in modules and not baseline_file_id:
            raise ValueError("分布偏差选择了“基线文件对比”，但未提供 baseline_file_id")

        label_shift = defects_selected.get("distribution.label_shift") if isinstance(defects_selected, dict) else None
        if isinstance(label_shift, dict) and label_shift.get("enabled") is not False:
            executor = label_shift.get("executor_algorithm") or label_shift.get("executor_runtime")
            if executor:
                label_column = params.get("label_column")
                if not label_column:
                    label_column = dist_cfg.get("label_column")
                if not label_column:
                    params_block = label_shift.get("params") if isinstance(label_shift.get("params"), dict) else {}
                    label_column = params_block.get("label_column")
                if not label_column:
                    raise ValueError("已启用标签分布变化，但未提供 label_column")

        label_mismatch = defects_selected.get("dirty_data.label_mismatch") if isinstance(defects_selected, dict) else None
        if isinstance(label_mismatch, dict) and label_mismatch.get("enabled") is not False:
            # label_mismatch 有默认 executor（引擎侧会回退到 confident_learning），因此只要启用就必须提供 label_column
            dirty_cfg = params.get("dirty_data") if isinstance(params.get("dirty_data"), dict) else {}
            params_block = label_mismatch.get("params") if isinstance(label_mismatch.get("params"), dict) else {}
            label_column = params_block.get("label_column") or params.get("label_column") or dirty_cfg.get("label_column")
            if not label_column:
                raise ValueError("已启用疑似错标检测，但未提供 label_column")

    @classmethod
    def _validate_params_image(cls, params: dict[str, Any] | None) -> None:
        """图片模态的参数校验：校验 label_csv_path, image_column, label_column。"""
        if not params or not isinstance(params, dict):
            raise ValueError("图片模态必须提供 params")

        label_csv_path = params.get("label_csv_path")
        if not label_csv_path or not isinstance(label_csv_path, str):
            raise ValueError("图片模态必须提供 label_csv_path（标签 CSV 文件路径）")

        image_column = params.get("image_column")
        if not image_column or not isinstance(image_column, str):
            raise ValueError("图片模态必须提供 image_column（图片路径列名）")

        label_column = params.get("label_column")
        if not label_column or not isinstance(label_column, str):
            raise ValueError("图片模态必须提供 label_column（标签列名）")

    @classmethod
    async def get_task(cls, task_id: str) -> dict[str, Any]:
        """查询任务状态（优先内存态；服务重启后可降级从 DB 查询）。"""
        async with cls._lock:
            state = cls._tasks.get(task_id)
        if state:
            return {
                "task_id": state.task_id,
                "status": state.status,
                "progress": state.progress,
                "started_at": state.started_at,
                "ended_at": state.ended_at,
                "error": state.error,
                "baseline_file_id": state.baseline_file_id,
                "result_file_id": state.result_file_id,
            }

        obj = await cls._db_get_task(task_id)
        if not obj:
            raise KeyError("task not found")

        started_at = obj.started_time.timestamp() if obj.started_time else None
        ended_at = obj.ended_time.timestamp() if obj.ended_time else None
        return {
            "task_id": obj.task_id,
            "status": obj.task_status,
            "progress": int(obj.progress or 0),
            "started_at": started_at,
            "ended_at": ended_at,
            "error": obj.error,
            "baseline_file_id": obj.baseline_file_id,
            "result_file_id": obj.result_file_id,
        }

    @classmethod
    async def get_result_path(cls, task_id: str) -> Path:
        """获取 result.json 的绝对路径（任务成功后才存在）。"""
        async with cls._lock:
            state = cls._tasks.get(task_id)
        if state and state.result_file_id:
            return _resolve_file_id(state.result_file_id)

        obj = await cls._db_get_task(task_id)
        if not obj or not obj.result_file_id:
            raise KeyError("result not ready")
        return _resolve_file_id(obj.result_file_id)

    @classmethod
    async def get_task_dir(cls, task_id: str) -> Path:
        """校验 task_id 并返回任务目录（用于 artifact 下载）。"""
        task_dir = (_tasks_root() / task_id).resolve()
        if not task_dir.exists():
            raise KeyError("task not found")
        root = _tasks_root().resolve()
        if root not in task_dir.parents and task_dir != root:
            raise ValueError("invalid task_id")
        return task_dir

    @classmethod
    async def resolve_task_artifact(cls, task_id: str, rel_path: str) -> Path:
        """
        解析并校验任务产物路径（防止 path traversal）。

        前端传入的 `path` 必须是任务目录下的相对路径，例如：`reports/dirty_data_report_tabular.docx`。
        """
        task_dir = await cls.get_task_dir(task_id)
        rel_path = (rel_path or "").lstrip("/").replace("\\", "/")
        abs_path = (task_dir / rel_path).resolve()
        if task_dir not in abs_path.parents and abs_path != task_dir:
            raise ValueError("invalid artifact path")
        if not abs_path.exists():
            raise FileNotFoundError("artifact not found")
        return abs_path

    @classmethod
    async def get_reports(
        cls,
        task_id: str,
        *,
        module: str | None = None,
        report_type: str = "json",
    ) -> dict[str, Any]:
        """
        读取并返回任务的报告 JSON（给前端页面展示用）。

        - report_type="json"：读取 `reports/*_report_*.json`（包含 scoring + compact results）
        - report_type="summary"：读取 `reports/*_summary.json`（更轻量）

        返回结构：
        - {"reports": {<module_key>: <report_json>, ...}}
        """
        if report_type not in {"json", "summary"}:
            raise ValueError("invalid report_type")

        task_dir = await cls.get_task_dir(task_id)
        result_path = (task_dir / "result.json").resolve()
        if not result_path.exists():
            raise FileNotFoundError("result.json not found")

        result_obj = json.loads(result_path.read_text("utf-8"))
        report_index = result_obj.get("reports") if isinstance(result_obj, dict) else None
        if not isinstance(report_index, dict):
            return {"reports": {}}

        def _pick_path(paths: dict[str, Any]) -> str | None:
            if report_type == "summary":
                v = paths.get("summary_report")
            else:
                v = paths.get("json_report")
            return str(v) if v else None

        modules = [module] if module else list(report_index.keys())
        out: dict[str, Any] = {}
        for m in modules:
            if not m:
                continue
            entry = report_index.get(m)
            if not isinstance(entry, dict):
                continue
            paths = entry.get("paths")
            if not isinstance(paths, dict):
                continue
            rel = _pick_path(paths)
            if not rel:
                continue
            rel = rel.lstrip("/").replace("\\", "/")
            abs_path = (task_dir / rel).resolve()
            if task_dir not in abs_path.parents and abs_path != task_dir:
                raise ValueError("invalid report path")
            if not abs_path.exists():
                continue
            try:
                out[m] = json.loads(abs_path.read_text("utf-8"))
            except Exception as e:
                out[m] = {"error": f"report parse failed: {e}"}

        if module and module not in out:
            raise KeyError("report not found")

        return {"reports": out}

    @classmethod
    async def ws_connect(cls, task_id: str, websocket: WebSocket) -> _TaskState:
        """
        建立 WebSocket 连接并发送 snapshot（当前状态快照）。

        snapshot 之后，客户端会持续收到 `log/progress/done/error` 事件。
        """
        async with cls._lock:
            state = cls._tasks.get(task_id)
        if not state:
            raise KeyError("task not found")

        await websocket.accept()
        state.ws_clients[websocket] = asyncio.Queue()

        await websocket.send_text(
            json.dumps(
                {
                    "type": "snapshot",
                    "task_id": state.task_id,
                    "status": state.status,
                    "progress": state.progress,
                    "error": state.error,
                    "baseline_file_id": state.baseline_file_id,
                    "result_file_id": state.result_file_id,
                },
                ensure_ascii=False,
            )
        )
        if state.status == "SUCCESS":
            await websocket.send_text(
                json.dumps(
                    {"type": "done", "task_id": state.task_id, "message": "扫描完成（已结束）"},
                    ensure_ascii=False,
                )
            )
        elif state.status == "FAILED":
            await websocket.send_text(
                json.dumps(
                    {"type": "error", "task_id": state.task_id, "message": state.error or "任务失败"},
                    ensure_ascii=False,
                )
            )
        return state

    @classmethod
    def ws_disconnect(cls, state: _TaskState, websocket: WebSocket) -> None:
        """断开连接时从 ws_clients 移除（避免队列泄漏）。"""
        try:
            state.ws_clients.pop(websocket, None)
        except Exception:
            pass

    @classmethod
    async def ws_pump(cls, state: _TaskState, websocket: WebSocket) -> None:
        """将队列中的事件持续推送给指定 websocket。"""
        queue = state.ws_clients.get(websocket)
        if queue is None:
            return
        while True:
            event = await queue.get()
            try:
                await websocket.send_text(json.dumps(event, ensure_ascii=False))
            except Exception:
                return

    @classmethod
    def _broadcast_nowait(cls, state: _TaskState, event: dict[str, Any]) -> None:
        """向所有已连接 websocket 广播事件（非阻塞 put_nowait）。"""
        for q in list(state.ws_clients.values()):
            try:
                q.put_nowait(event)
            except Exception:
                pass

    @classmethod
    async def _run_task(
        cls,
        *,
        state: _TaskState,
        file_id: str,
        baseline_file_id: str | None,
        algorithm: str,
        params: dict[str, Any] | None,
    ):
        """
        后台任务执行器。

        - 解析 file_id → 输入文件绝对路径
        - 调用引擎算法 `alg.run(...)`
        - 校验并记录 result.json 路径
        - 过程中通过 emit 写 log.txt、更新 progress、广播 WS
        """
        state.status = "RUNNING"
        state.started_at = time.time()
        state.progress = 0
        await cls._db_update_task(
            state.task_id,
            {
                "task_status": "RUNNING",
                "progress": 0,
                "started_time": datetime.now(),
                "ended_time": None,
                "error": None,
            },
        )
        loop = asyncio.get_running_loop()

        task_dir = (_tasks_root() / state.task_id).resolve()
        log_file = (task_dir / "log.txt").resolve()

        def emit(event: dict[str, Any]) -> None:
            # emit 可能在 worker thread 内被调用，所以这里：
            # 1) 同步更新 state（简单字段，允许轻微竞态）
            # 2) 用 call_soon_threadsafe 把广播调度回事件循环线程
            event = dict(event)
            event.setdefault("task_id", state.task_id)

            if event.get("type") == "progress":
                try:
                    state.progress = int(event.get("value", state.progress))
                except Exception:
                    pass
                try:
                    loop.call_soon_threadsafe(
                        asyncio.create_task, cls._db_update_task(state.task_id, {"progress": int(state.progress)})
                    )
                except Exception:
                    pass
            if event.get("type") == "log":
                try:
                    log_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(str(event.get("message", "")) + "\n")
                except Exception:
                    pass

            try:
                loop.call_soon_threadsafe(cls._broadcast_nowait, state, event)
            except Exception:
                return

        try:
            input_path = _resolve_file_id(file_id)

            _ensure_dqscan_importable()
            from dqscan.engine import get_algorithm

            alg = get_algorithm(algorithm)

            params_to_pass = dict(params or {})
            if baseline_file_id:
                baseline_path = _resolve_file_id(baseline_file_id)
                # 仅由后端注入基线路径，避免前端随意传系统路径造成风险
                params_to_pass["baseline_input_path"] = os.fspath(baseline_path)

            await asyncio.to_thread(
                alg.run,
                input_path=os.fspath(input_path),
                output_dir=os.fspath(task_dir),
                params=params_to_pass,
                emit=emit,
            )

            result_path = (task_dir / "result.json").resolve()
            if not result_path.exists():
                raise RuntimeError("result.json not generated")

            state.result_file_id = _safe_rel_file_id(result_path)
            state.status = "SUCCESS"
            state.progress = 100
            state.ended_at = time.time()
            await cls._db_update_task(
                state.task_id,
                {
                    "task_status": "SUCCESS",
                    "progress": 100,
                    "ended_time": datetime.now(),
                    "result_file_id": state.result_file_id,
                    "error": None,
                },
            )
            cls._broadcast_nowait(state, {"type": "done", "task_id": state.task_id, "message": "扫描完成"})
        except Exception as e:
            state.status = "FAILED"
            state.error = str(e)
            state.ended_at = time.time()
            await cls._db_update_task(
                state.task_id,
                {
                    "task_status": "FAILED",
                    "ended_time": datetime.now(),
                    "error": state.error,
                    "progress": int(state.progress or 0),
                },
            )
            log.exception("dqscan task failed")
            cls._broadcast_nowait(state, {"type": "error", "task_id": state.task_id, "message": str(e)})

"""补数审核API路由"""
from fastapi import APIRouter, Query
from typing import List

from optimizer.schemas.schemas import CandidateData
from optimizer.core.optimizer_service import OptimizerService

router = APIRouter(prefix="/review", tags=["补数审核"])


@router.get("/candidates", response_model=dict)
async def get_candidates(
    source: str = Query("all", description="数据源筛选: all, augmentation, retrieval, genai"),
    category: str = Query("", description="类别筛选"),
    min_confidence: float = Query(0.0, description="最低置信度"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """
    获取候选数据列表

    支持筛选:
    - 按来源筛选
    - 按类别筛选
    - 按置信度筛选
    """
    # TODO: 实际应用中应从数据库或缓存读取
    all_candidates = await OptimizerService.generate_candidates({
        "augmentation": {},
        "retrieval": {"data_source": "OpenImages", "target_count": 100},
        "genai": {"model": "SDXL", "scenario": "雨天", "batch_size": 10}
    })

    # 应用筛选
    filtered_candidates = all_candidates
    if source != "all":
        filtered_candidates = [c for c in filtered_candidates if c.source == source]
    if category:
        filtered_candidates = [c for c in filtered_candidates if c.category == category]
    if min_confidence > 0:
        filtered_candidates = [c for c in filtered_candidates if c.confidence >= min_confidence]

    # 分页
    total = len(filtered_candidates)
    start = (page - 1) * page_size
    end = start + page_size
    page_candidates = filtered_candidates[start:end]

    return {
        "code": 0,
        "msg": "获取成功",
        "data": {
            "total": total,
            "items": page_candidates,
            "page": page,
            "page_size": page_size
        }
    }


@router.post("/batch-accept")
async def batch_accept(candidate_ids: List[str]):
    """
    批量采纳候选数据

    将选中的候选数据标记为采纳，将添加到训练集
    """
    # TODO: 实际应用中应将数据添加到训练集数据库
    return {
        "code": 0,
        "msg": f"成功采纳 {len(candidate_ids)} 条数据",
        "data": {
            "accepted_count": len(candidate_ids),
            "candidate_ids": candidate_ids
        }
    }


@router.post("/batch-reject")
async def batch_reject(candidate_ids: List[str]):
    """
    批量拒绝候选数据

    将选中的候选数据标记为拒绝
    """
    # TODO: 实际应用中应标记拒绝状态
    return {
        "code": 0,
        "msg": f"成功拒绝 {len(candidate_ids)} 条数据",
        "data": {
            "rejected_count": len(candidate_ids),
            "candidate_ids": candidate_ids
        }
    }


@router.post("/{candidate_id}/accept")
async def accept_candidate(candidate_id: str):
    """采纳单条候选数据"""
    return {
        "code": 0,
        "msg": "采纳成功",
        "data": {"candidate_id": candidate_id}
    }


@router.post("/{candidate_id}/reject")
async def reject_candidate(candidate_id: str):
    """拒绝单条候选数据"""
    return {
        "code": 0,
        "msg": "拒绝成功",
        "data": {"candidate_id": candidate_id}
    }

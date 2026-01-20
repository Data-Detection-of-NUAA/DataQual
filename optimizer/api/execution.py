"""执行确认API路由"""
from fastapi import APIRouter

from optimizer.core.optimizer_service import OptimizerService
from optimizer.schemas.schemas import StrategyConfig, ExecutionResult

router = APIRouter(prefix="/execution", tags=["执行确认"])


@router.post("/execute", response_model=ExecutionResult)
async def execute_optimization(config: StrategyConfig):
    """
    执行优化任务

    根据保存的策略配置，执行优化任务
    """
    result = await OptimizerService.execute_optimization(config.dict(), [])
    return result


@router.get("/progress")
async def get_execution_progress():
    """
    获取执行进度

    返回各阶段的进度状态
    """
    # TODO: 实际应用中应从任务队列获取实时进度
    return {
        "code": 0,
        "msg": "获取进度成功",
        "data": {
            "current_stage": "retrieval",
            "overall_progress": 45,
            "stages": [
                {"stage": "生成任务", "progress": 100, "status": "completed"},
                {"stage": "检索写回", "progress": 30, "status": "in_progress"},
                {"stage": "人工复核", "progress": 0, "status": "pending"}
            ]
        }
    }


@router.post("/export")
async def export_plan(config: StrategyConfig, format: str = "json"):
    """
    导出优化方案

    支持导出格式:
    - json: JSON格式
    - pdf: PDF格式报告
    """
    # TODO: 实际应用中应生成实际的优化方案文档
    return {
        "code": 0,
        "msg": "导出成功",
        "data": {
            "format": format,
            "download_url": "/downloads/optimization_plan.json"
        }
    }


@router.post("/download")
async def download_dataset(config: StrategyConfig):
    """
    下载新增样本包

    将采纳的候选数据打包下载
    """
    # TODO: 实际应用中应生成ZIP压缩包
    return {
        "code": 0,
        "msg": "准备下载",
        "data": {
            "download_url": "/downloads/optimized_dataset.zip",
            "file_size_gb": 5.0
        }
    }


@router.post("/trigger-training")
async def trigger_training(config: StrategyConfig):
    """
    触发训练任务

    将优化后的数据集推送到训练系统
    """
    # TODO: 实际应用中应调用训练系统的API
    return {
        "code": 0,
        "msg": "训练任务已触发",
        "data": {
            "training_id": "TRAIN_20250118_001",
            "dataset_id": "OPT_DATASET_001",
            "estimated_duration_hours": 2.0
        }
    }

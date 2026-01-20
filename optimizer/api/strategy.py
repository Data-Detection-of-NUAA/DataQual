"""策略配置API路由"""
from fastapi import APIRouter

from optimizer.core.optimizer_service import OptimizerService
from optimizer.schemas.schemas import StrategyConfig, CandidateListResponse

router = APIRouter(prefix="/strategy", tags=["策略配置"])


@router.post("/config")
async def save_strategy_config(config: StrategyConfig):
    """
    保存策略配置

    接收三种策略配置:
    - 增强策略 (Augmentation)
    - 检索策略 (Retrieval)
    - 生成策略 (GenAI)
    """
    # TODO: 实际应用中应将配置保存到数据库
    return {
        "code": 0,
        "msg": "策略配置保存成功",
        "data": config.dict()
    }


@router.get("/config")
async def get_strategy_config():
    """获取当前策略配置"""
    # TODO: 实际应用中应从数据库读取
    return StrategyConfig()


@router.post("/generate", response_model=CandidateListResponse)
async def generate_candidates(config: StrategyConfig):
    """
    生成候选数据集

    根据配置的策略，生成候选数据集
    """
    candidates = await OptimizerService.generate_candidates(config.dict())

    return CandidateListResponse(
        total=len(candidates),
        items=candidates,
        page=1,
        page_size=20
    )


@router.get("/estimate")
async def get_estimation(config: StrategyConfig):
    """
    获取优化估算

    返回:
    - 预计新增样本数量
    - 预估 mAP 提升
    - 资源需求预测
    """
    estimation = await OptimizerService.calculate_estimation(config.dict())

    return {
        "code": 0,
        "msg": "估算计算成功",
        "data": estimation
    }

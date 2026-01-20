"""诊断概览API路由"""
from fastapi import APIRouter

from optimizer.core.optimizer_service import OptimizerService
from optimizer.schemas.schemas import DiagnosisOverview

router = APIRouter(prefix="/diagnosis", tags=["诊断概览"])


@router.get("/overview", response_model=DiagnosisOverview)
async def get_diagnosis_overview():
    """
    获取诊断概览数据

    返回包括:
    - 质量探测问题统计
    - 鲁棒性评估结果
    - 合规审计问题
    - 模型评估指标
    """
    overview = await OptimizerService.get_diagnosis_overview()
    return overview


@router.get("/suggestions")
async def get_suggestions():
    """
    获取智能优化建议

    基于当前诊断结果，返回系统建议
    """
    # TODO: 实际应用中应根据诊断结果动态生成建议
    return {
        "suggestions": [
            {
                "type": "warning",
                "message": "检测到'行人'类别存在大量漏标，且对抗攻击防御力低",
                "recommended_action": "建议增加对抗训练样本并调整检测阈值"
            },
            {
                "type": "info",
                "message": "标注错误率较高，建议重新审查标注数据",
                "recommended_action": "组织标注团队进行数据清洗"
            }
        ]
    }

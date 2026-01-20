"""优化器数据模型"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ==================== 诊断相关模型 ====================

class QualityDetectionIssue(BaseModel):
    """质量探测问题"""
    type: str = Field(..., description="问题类型")
    count: int = Field(..., description="问题数量")
    severity: str = Field(default="medium", description="严重程度: low, medium, high")
    confidence: float = Field(default=0.0, description="置信度")


class RobustnessIssue(BaseModel):
    """鲁棒性问题"""
    attack_type: str = Field(..., description="攻击类型: FGSM, PGD, etc.")
    count: int = Field(..., description="问题数量")
    vulnerability_score: float = Field(default=0.0, description="脆弱性评分")


class ComplianceIssue(BaseModel):
    """合规问题"""
    issue_type: str = Field(..., description="问题类型: privacy, sensitive, etc.")
    count: int = Field(..., description="问题数量")
    severity: str = Field(default="warning", description="严重程度")


class ModelEvaluation(BaseModel):
    """模型评估结果"""
    metric_name: str = Field(..., description="指标名称")
    current_value: float = Field(..., description="当前值")
    low_ap_categories: list[str] = Field(default_factory=list, description="低AP类别列表")


class DiagnosisOverview(BaseModel):
    """诊断概览"""
    quality_issues: list[QualityDetectionIssue] = Field(default_factory=list)
    robustness_issues: list[RobustnessIssue] = Field(default_factory=list)
    compliance_issues: list[ComplianceIssue] = Field(default_factory=list)
    model_evaluation: Optional[ModelEvaluation] = None


# ==================== 策略相关模型 ====================

class AugmentationStrategy(BaseModel):
    """增强策略"""
    noise_level: int = Field(default=50, ge=0, le=100, description="噪声强度 0-100%")
    blur_radius: int = Field(default=0, ge=0, le=10, description="模糊程度")
    enable_adversarial: bool = Field(default=False, description="开启对抗样本生成")


class RetrievalStrategy(BaseModel):
    """检索策略"""
    data_source: str = Field(..., description="数据源名称")
    target_count: int = Field(..., ge=1, le=10000, description="目标补入数量")


class GenAIStrategy(BaseModel):
    """大模型生成策略"""
    model: str = Field(..., description="生成模型")
    scenario: str = Field(..., description="预设场景")
    batch_size: int = Field(default=10, ge=1, le=100, description="生成批次")


class StrategyConfig(BaseModel):
    """策略配置"""
    augmentation: AugmentationStrategy = Field(default_factory=AugmentationStrategy)
    retrieval: RetrievalStrategy = Field(default_factory=RetrievalStrategy)
    genai: GenAIStrategy = Field(default_factory=GenAIStrategy)

    class Config:
        schema_extra = {
            "example": {
                "augmentation": {
                    "noise_level": 50,
                    "blur_radius": 2,
                    "enable_adversarial": False
                },
                "retrieval": {
                    "data_source": "OpenImages",
                    "target_count": 1000
                },
                "genai": {
                    "model": "Stable Diffusion XL",
                    "scenario": "雨天场景",
                    "batch_size": 10
                }
            }
        }


# ==================== 候选数据相关模型 ====================

class CandidateData(BaseModel):
    """候选数据"""
    id: str = Field(..., description="数据ID")
    source: str = Field(..., description="来源: augmentation, retrieval, genai")
    category: str = Field(..., description="类别")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    thumbnail: str = Field(..., description="缩略图URL或base64")
    description: str = Field(..., description="详情描述")

    class Config:
        schema_extra = {
            "example": {
                "id": "CAND_001",
                "source": "retrieval",
                "category": "行人",
                "confidence": 0.92,
                "thumbnail": "/images/cand001_thumb.jpg",
                "description": "类别: 行人; 来源库: CCTV_04"
            }
        }


class CandidateListResponse(BaseModel):
    """候选数据列表响应"""
    total: int
    items: list[CandidateData]
    page: int = 1
    page_size: int = 20


# ==================== 执行相关模型 ====================

class ExecutionTaskSummary(BaseModel):
    """执行任务摘要"""
    retrieval_count: int = Field(default=0, description="检索补入数量")
    genai_count: int = Field(default=0, description="生成补入数量")
    augmentation_count: int = Field(default=0, description="增强处理数量")
    total_new_count: int = Field(default=0, description="总计新增数量")


class ResourceForecast(BaseModel):
    """资源预测"""
    gpu_time_hours: float = Field(..., description="GPU预计耗时(小时)")
    storage_gb: float = Field(..., description="存储空间增量(GB)")
    estimated_cost_usd: float = Field(..., description="费用估算(USD)")


class ProcessProgress(BaseModel):
    """流程进度"""
    task_name: str = Field(..., description="任务名称")
    progress: int = Field(..., ge=0, le=100, description="进度百分比")
    status: str = Field(default="pending", description="状态: pending, in_progress, completed")
    log_url: Optional[str] = Field(None, description="日志URL")


class ExecutionResult(BaseModel):
    """执行结果"""
    task_summary: ExecutionTaskSummary
    resource_forecast: ResourceForecast
    progress: list[ProcessProgress]
    predicted_map: float = Field(..., description="预测mAP")
    map_improvement: float = Field(..., description="mAP提升幅度")


# ==================== 通用响应模型 ====================

class OptimizerResponse(BaseModel):
    """优化器通用响应"""
    code: int = Field(default=0, description="状态码")
    msg: str = Field(default="success", description="消息")
    data: Optional[dict] = None

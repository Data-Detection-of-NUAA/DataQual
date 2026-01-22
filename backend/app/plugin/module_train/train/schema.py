# -*- coding: utf-8 -*-

import json
from pydantic import BaseModel, ConfigDict, Field, field_validator
from fastapi import Query

from app.core.base_schema import BaseSchema, UserBySchema
from app.core.validator import DateTimeStr


# ==================== 数据集信息相关 ====================

class DatasetInfoForTrain(BaseModel):
    """用于训练的数据集信息(从数据集模块获取)"""
    dataset_id: int = Field(..., description="数据集ID")
    name: str = Field(..., description="数据集名称")
    modality: str = Field(..., description="数据模态类型(image/audio/video/text/sensor/multimodal)")
    task_type: str | None = Field(default=None, description="任务类型")
    sample_count: int | None = Field(default=None, description="样本数量")
    class_count: int | None = Field(default=None, description="类别数量")
    file_size: int = Field(..., description="文件大小(字节)")
    storage_path: str = Field(..., description="存储路径")
    dataset_metadata: dict | None = Field(default=None, description="元数据")


class ModelRecommendationRequest(BaseModel):
    """模型推荐请求"""
    dataset_id: int = Field(..., gt=0, description="数据集ID")
    modality: str | None = Field(default=None, description="数据模态类型(如果为空则从数据集获取)")
    task_type: str | None = Field(default=None, description="任务类型(如果为空则从数据集获取)")
    top_k: int = Field(default=5, ge=1, le=20, description="返回推荐模型数量(默认5个,最多20个)")
    only_active: bool = Field(default=True, description="是否仅返回激活状态的模型")


# ==================== 模型配置相关 ====================

class ModelConfigCreateSchema(BaseModel):
    """创建模型配置请求"""
    model_name: str = Field(..., min_length=1, max_length=100, description="模型名称(唯一标识)")
    display_name: str = Field(..., min_length=1, max_length=100, description="显示名称")
    model_version: str = Field(default="1.0.0", max_length=50, description="模型版本号")
    supported_modalities: list[str] = Field(..., min_items=1, description="适用模态列表")
    supported_task_types: list[str] = Field(..., min_items=1, description="适用任务类型列表")
    description: str = Field(..., min_length=1, description="模型简介")
    architecture_summary: str | None = Field(default=None, max_length=500, description="架构简要说明")
    pretrained_weights: dict | None = Field(default=None, description="预训练权重信息")
    default_train_config: dict = Field(..., description="默认训练配置")
    performance_metrics: dict | None = Field(default=None, description="性能指标参考")
    hardware_requirements: dict | None = Field(default=None, description="硬件要求")
    framework: str = Field(default="PyTorch", max_length=50, description="深度学习框架")
    framework_version: str | None = Field(default=None, max_length=50, description="框架版本要求")
    model_code_path: str | None = Field(default=None, max_length=512, description="模型代码路径")
    config_template_path: str | None = Field(default=None, max_length=512, description="配置模板文件路径")
    priority: int = Field(default=0, description="推荐优先级(数值越大优先级越高)")
    status: str = Field(default="active", description="模型状态(active/inactive/deprecated)")
    tags: list[str] | None = Field(default=None, description="标签列表")
    reference_url: str | None = Field(default=None, max_length=512, description="参考文档或论文链接")
    remarks: str | None = Field(default=None, description="备注信息")

    @field_validator('supported_modalities')
    @classmethod
    def validate_modalities(cls, v: list[str]) -> list[str]:
        """验证模态类型"""
        allowed = {'image', 'audio', 'video', 'text', 'sensor', 'multimodal'}
        for modality in v:
            if modality not in allowed:
                raise ValueError(f'不支持的模态类型: {modality}, 仅支持: {", ".join(allowed)}')
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """验证状态值"""
        allowed = {'active', 'inactive', 'deprecated'}
        if v not in allowed:
            raise ValueError(f'不支持的状态值: {v}, 仅支持: {", ".join(allowed)}')
        return v

    @field_validator('default_train_config')
    @classmethod
    def validate_train_config(cls, v: dict) -> dict:
        """验证训练配置格式"""
        required_keys = ['learning_rate', 'batch_size', 'epochs']
        for key in required_keys:
            if key not in v:
                raise ValueError(f'训练配置缺少必需字段: {key}')
        return v


class ModelConfigUpdateSchema(BaseModel):
    """更新模型配置请求"""
    display_name: str | None = Field(default=None, min_length=1, max_length=100, description="显示名称")
    model_version: str | None = Field(default=None, max_length=50, description="模型版本号")
    supported_modalities: list[str] | None = Field(default=None, description="适用模态列表")
    supported_task_types: list[str] | None = Field(default=None, description="适用任务类型列表")
    description: str | None = Field(default=None, description="模型简介")
    architecture_summary: str | None = Field(default=None, max_length=500, description="架构简要说明")
    pretrained_weights: dict | None = Field(default=None, description="预训练权重信息")
    default_train_config: dict | None = Field(default=None, description="默认训练配置")
    performance_metrics: dict | None = Field(default=None, description="性能指标参考")
    hardware_requirements: dict | None = Field(default=None, description="硬件要求")
    framework: str | None = Field(default=None, max_length=50, description="深度学习框架")
    framework_version: str | None = Field(default=None, max_length=50, description="框架版本要求")
    model_code_path: str | None = Field(default=None, max_length=512, description="模型代码路径")
    config_template_path: str | None = Field(default=None, max_length=512, description="配置模板文件路径")
    priority: int | None = Field(default=None, description="推荐优先级")
    status: str | None = Field(default=None, description="模型状态(active/inactive/deprecated)")
    tags: list[str] | None = Field(default=None, description="标签列表")
    reference_url: str | None = Field(default=None, max_length=512, description="参考文档或论文链接")
    remarks: str | None = Field(default=None, description="备注信息")

    @field_validator('supported_modalities')
    @classmethod
    def validate_modalities(cls, v: list[str] | None) -> list[str] | None:
        """验证模态类型"""
        if v is None:
            return v
        allowed = {'image', 'audio', 'video', 'text', 'sensor', 'multimodal'}
        for modality in v:
            if modality not in allowed:
                raise ValueError(f'不支持的模态类型: {modality}')
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        """验证状态值"""
        if v is None:
            return v
        allowed = {'active', 'inactive', 'deprecated'}
        if v not in allowed:
            raise ValueError(f'不支持的状态值: {v}')
        return v


class ModelCardSchema(BaseModel):
    """单个模型卡片信息(用于列表展示)"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="模型配置ID")
    model_name: str = Field(..., description="模型名称")
    display_name: str = Field(..., description="显示名称")
    model_version: str = Field(..., description="模型版本号")
    description: str = Field(..., description="模型简介")
    supported_modalities: list[str] = Field(..., description="适用模态列表")
    supported_task_types: list[str] = Field(..., description="适用任务类型列表")
    framework: str = Field(..., description="深度学习框架")
    priority: int = Field(..., description="推荐优先级")
    status: str = Field(..., description="模型状态")
    tags: list[str] | None = Field(default=None, description="标签列表")
    usage_count: int = Field(default=0, description="使用次数")

    # 简化的性能指标(仅展示关键指标)
    key_metrics: dict | None = Field(default=None, description="关键性能指标")

    @field_validator('supported_modalities', 'supported_task_types', 'tags', mode='before')
    @classmethod
    def parse_string_to_list(cls, v):
        """将逗号分隔的字符串转换为列表"""
        if v is None:
            return None
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        return v

    @field_validator('key_metrics', mode='before')
    @classmethod
    def parse_json_field(cls, v):
        """将 JSON 字符串转换为 dict"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v


class ModelDetailSchema(ModelCardSchema):
    """模型详细信息(用于单个模型展示)"""
    architecture_summary: str | None = Field(default=None, description="架构简要说明")
    pretrained_weights: dict | None = Field(default=None, description="预训练权重信息")
    default_train_config: dict = Field(..., description="默认训练配置")
    performance_metrics: dict | None = Field(default=None, description="完整性能指标")
    hardware_requirements: dict | None = Field(default=None, description="硬件要求")
    framework_version: str | None = Field(default=None, description="框架版本要求")
    model_code_path: str | None = Field(default=None, description="模型代码路径")
    config_template_path: str | None = Field(default=None, description="配置模板文件路径")
    reference_url: str | None = Field(default=None, description="参考文档链接")
    remarks: str | None = Field(default=None, description="备注信息")
    created_time: str | None = Field(default=None, description="创建时间")
    updated_time: str | None = Field(default=None, description="更新时间")

    @field_validator('pretrained_weights', 'default_train_config', 'performance_metrics', 'hardware_requirements', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        """将 JSON 字符串转换为 dict"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v

    @field_validator('created_time', 'updated_time', mode='before')
    @classmethod
    def convert_datetime_to_str(cls, v):
        """将 datetime 对象转换为字符串"""
        if v is None:
            return None
        if hasattr(v, 'isoformat'):
            # datetime 对象，转换为 ISO 格式字符串
            return v.isoformat()
        return str(v)


class ModelConfigOutSchema(BaseSchema, UserBySchema):
    """模型配置完整输出(包含所有字段)"""
    model_config = ConfigDict(from_attributes=True)

    model_name: str = Field(..., description="模型名称")
    display_name: str = Field(..., description="显示名称")
    model_version: str = Field(..., description="模型版本号")
    supported_modalities: list[str] = Field(..., description="适用模态列表")
    supported_task_types: list[str] = Field(..., description="适用任务类型列表")
    description: str = Field(..., description="模型简介")
    architecture_summary: str | None = Field(default=None, description="架构简要说明")
    pretrained_weights: dict | None = Field(default=None, description="预训练权重信息")
    default_train_config: dict = Field(..., description="默认训练配置")
    performance_metrics: dict | None = Field(default=None, description="性能指标参考")
    hardware_requirements: dict | None = Field(default=None, description="硬件要求")
    framework: str = Field(..., description="深度学习框架")
    framework_version: str | None = Field(default=None, description="框架版本要求")
    model_code_path: str | None = Field(default=None, description="模型代码路径")
    config_template_path: str | None = Field(default=None, description="配置模板文件路径")
    priority: int = Field(..., description="推荐优先级")
    status: str = Field(..., description="模型状态")
    usage_count: int = Field(..., description="使用次数")
    tags: list[str] | None = Field(default=None, description="标签列表")
    reference_url: str | None = Field(default=None, description="参考文档链接")
    remarks: str | None = Field(default=None, description="备注信息")

    @field_validator('supported_modalities', 'supported_task_types', 'tags', mode='before')
    @classmethod
    def parse_string_to_list(cls, v):
        """将逗号分隔的字符串转换为列表"""
        if v is None:
            return None
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        return v

    @field_validator('pretrained_weights', 'default_train_config', 'performance_metrics', 'hardware_requirements', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        """将 JSON 字符串转换为 dict"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v


# ==================== 模型推荐响应 ====================

class ModelRecommendationItem(BaseModel):
    """单个推荐模型项"""
    model_id: int = Field(..., description="模型配置ID")
    model_name: str = Field(..., description="模型名称")
    display_name: str = Field(..., description="显示名称")
    model_version: str = Field(..., description="模型版本号")
    description: str = Field(..., description="模型简介")
    framework: str = Field(..., description="深度学习框架")
    tags: list[str] | None = Field(default=None, description="标签列表")
    priority: int = Field(..., description="推荐优先级")
    match_score: float = Field(..., ge=0, le=1, description="匹配度评分(0-1)")
    recommendation_reason: str = Field(..., description="推荐理由")

    # 快速预览的关键信息
    key_metrics: dict | None = Field(default=None, description="关键性能指标")
    hardware_summary: str | None = Field(default=None, description="硬件要求简述")
    default_config_preview: dict | None = Field(default=None, description="默认配置预览(简化版)")


class ModelRecommendationResponse(BaseModel):
    """模型推荐响应"""
    dataset_info: DatasetInfoForTrain = Field(..., description="数据集信息")
    total_recommended: int = Field(..., description="推荐模型总数")
    recommendations: list[ModelRecommendationItem] = Field(..., description="推荐模型列表")
    recommendation_metadata: dict | None = Field(default=None, description="推荐元数据(包含推荐算法版本、时间戳等)")


# ==================== 查询参数 ====================

class ModelConfigQueryParam:
    """模型配置查询参数"""
    def __init__(
        self,
        model_name: str | None = Query(None, description="模型名称(模糊查询)"),
        display_name: str | None = Query(None, description="显示名称(模糊查询)"),
        framework: str | None = Query(None, description="深度学习框架"),
        status: str | None = Query(None, description="模型状态(active/inactive/deprecated)"),
        modality: str | None = Query(None, description="适用模态(模糊匹配)"),
        task_type: str | None = Query(None, description="适用任务类型(模糊匹配)"),
        tag: str | None = Query(None, description="标签(模糊匹配)"),
        priority_min: int | None = Query(None, description="最小优先级"),
        priority_max: int | None = Query(None, description="最大优先级"),
        created_time: list[DateTimeStr] | None = Query(None, description="创建时间范围", examples=["2025-01-01 00:00:00", "2025-12-31 23:59:59"]),
        updated_time: list[DateTimeStr] | None = Query(None, description="更新时间范围", examples=["2025-01-01 00:00:00", "2025-12-31 23:59:59"]),
        created_id: int | None = Query(None, description="创建人ID"),
    ) -> None:
        # 模糊查询字段
        if model_name:
            self.model_name = ("like", model_name)
        if display_name:
            self.display_name = ("like", display_name)
        if modality:
            self.supported_modalities = ("like", modality)
        if task_type:
            self.supported_task_types = ("like", task_type)
        if tag:
            self.tags = ("like", tag)

        # 精确查询字段
        if framework:
            self.framework = ("eq", framework)
        if status:
            self.status = ("eq", status)
        if created_id:
            self.created_id = ("eq", created_id)

        # 优先级范围查询
        if priority_min is not None and priority_max is not None:
            self.priority = ("between", (priority_min, priority_max))
        elif priority_min is not None:
            self.priority = ("ge", priority_min)
        elif priority_max is not None:
            self.priority = ("le", priority_max)

        # 时间范围查询
        if created_time and len(created_time) == 2:
            self.created_time = ("between", (created_time[0], created_time[1]))
        if updated_time and len(updated_time) == 2:
            self.updated_time = ("between", (updated_time[0], updated_time[1]))


# ==================== 训练任务相关 ====================

class TrainTaskCreateSchema(BaseModel):
    """创建训练任务请求"""
    task_name: str = Field(..., min_length=1, max_length=255, description="训练任务名称")
    dataset_id: int = Field(..., gt=0, description="数据集ID")
    model_id: int = Field(..., gt=0, description="模型配置ID")
    train_config: dict = Field(..., description="训练配置(可基于模型默认配置修改)")
    description: str | None = Field(default=None, max_length=1000, description="任务描述")

    @field_validator('train_config')
    @classmethod
    def validate_train_config(cls, v: dict) -> dict:
        """验证训练配置"""
        required_keys = ['learning_rate', 'batch_size', 'epochs']
        for key in required_keys:
            if key not in v:
                raise ValueError(f'训练配置缺少必需字段: {key}')
        return v


# 注意：这是一个简单的常量类，不是 Pydantic BaseModel
# 如果需要在请求中使用，应该直接使用字符串字面量
# class TrainTaskStatusEnum:
#     """训练任务状态枚举（已移至 model.py，此处注释保留供参考）"""
#     PENDING = "pending"  # 等待中
#     RUNNING = "running"  # 运行中
#     COMPLETED = "completed"  # 已完成
#     FAILED = "failed"  # 失败
#     CANCELLED = "cancelled"  # 已取消


class TrainTaskOutSchema(BaseSchema, UserBySchema):
    """训练任务输出"""
    model_config = ConfigDict(from_attributes=True)

    task_name: str = Field(..., description="训练任务名称")
    dataset_id: int = Field(..., description="数据集ID")
    model_id: int = Field(..., description="模型配置ID")
    train_config: dict = Field(..., description="训练配置")
    status: str = Field(..., description="任务状态")
    progress: float = Field(default=0.0, ge=0, le=1, description="训练进度(0-1)")
    current_epoch: int = Field(default=0, description="当前训练轮次")
    total_epochs: int = Field(..., description="总训练轮次")
    metrics: dict | None = Field(default=None, description="训练指标")
    result_path: str | None = Field(default=None, description="训练结果路径")
    error_message: str | None = Field(default=None, description="错误信息")
    description: str | None = Field(default=None, description="任务描述")

    @field_validator('train_config', 'metrics', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        """将 JSON 字符串转换为 dict"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v

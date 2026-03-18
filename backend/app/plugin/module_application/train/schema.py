# -*- coding: utf-8 -*-

import json
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
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

class TrainConfigSchema(BaseModel):
    """训练配置"""
    # 基础超参数
    learning_rate: float = Field(..., gt=0, le=1, description="学习率")
    batch_size: int = Field(..., gt=0, le=1024, description="批次大小")
    epochs: int = Field(..., gt=0, le=1000, description="训练轮数")
    optimizer: str = Field(..., description="优化器(adam/sgd/adamw/rmsprop)")

    # 可选超参数
    loss_function: str | None = Field(default="cross_entropy", description="损失函数")
    weight_decay: float | None = Field(default=0.0001, ge=0, description="权重衰减")
    momentum: float | None = Field(default=0.9, ge=0, le=1, description="动量(仅SGD)")
    lr_scheduler: str | None = Field(default=None, description="学习率调度器")
    early_stopping: bool = Field(default=False, description="是否启用早停")
    early_stopping_patience: int | None = Field(default=10, gt=0, description="早停耐心值")

    # 数据增强
    data_augmentation: bool = Field(default=True, description="是否启用数据增强")
    validation_split: float = Field(default=0.2, ge=0, le=0.5, description="验证集比例")

    # 其他配置
    seed: int | None = Field(default=42, description="随机种子")
    num_workers: int = Field(default=4, ge=0, description="数据加载线程数")
    pin_memory: bool = Field(default=True, description="是否使用pin_memory")

    @field_validator('optimizer')
    @classmethod
    def validate_optimizer(cls, v: str) -> str:
        """验证优化器"""
        allowed = {'adam', 'sgd', 'adamw', 'rmsprop'}
        if v.lower() not in allowed:
            raise ValueError(f'不支持的优化器: {v}, 仅支持: {", ".join(allowed)}')
        return v.lower()


class TrainTaskCreateRequest(BaseModel):
    """创建训练任务请求（对应使用手册第四步）"""
    dataset_id: int = Field(..., gt=0, description="数据集ID")
    model_config_id: int = Field(..., gt=0, description="模型配置ID")
    train_config: TrainConfigSchema = Field(..., description="训练配置")
    remarks: str | None = Field(default=None, max_length=1000, description="备注信息")

    @field_validator('train_config', mode='before')
    @classmethod
    def parse_train_config(cls, v):
        """解析训练配置"""
        if isinstance(v, dict):
            return TrainConfigSchema(**v)
        return v


class TrainTaskStatusUpdateRequest(BaseModel):
    """更新训练任务状态请求"""
    status: str = Field(..., description="任务状态(created/pending/running/paused/completed/failed/cancelled)")
    error_message: str | None = Field(default=None, description="错误信息（status为failed时必填）")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """验证状态值"""
        allowed = {'created', 'pending', 'running', 'paused', 'completed', 'failed', 'cancelled'}
        if v not in allowed:
            raise ValueError(f'不支持的状态值: {v}, 仅支持: {", ".join(allowed)}')
        return v


class TrainTaskResponse(BaseSchema, UserBySchema):
    """训练任务详情响应（对应使用手册任务记录结构）"""
    model_config = ConfigDict(from_attributes=True)

    # 任务标识
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")

    # 关联信息
    dataset_id: int = Field(..., description="数据集ID")
    dataset_info: dict = Field(..., description="数据集信息快照")
    dataset_name: str | None = Field(default=None, description="数据集名称")
    model_config_id: int = Field(..., description="模型配置ID")
    model_configuration: dict = Field(..., validation_alias="model_config", description="模型配置快照")
    model_name: str | None = Field(default=None, description="模型名称")
    train_config: dict = Field(..., description="训练配置")

    # 时间信息
    estimated_start_time: str | None = Field(default=None, description="预计开始时间")
    actual_start_time: str | None = Field(default=None, description="实际开始时间")
    estimated_completion_time: str | None = Field(default=None, description="预计完成时间")
    actual_completion_time: str | None = Field(default=None, description="实际完成时间")

    # 进度信息
    current_epoch: int = Field(default=0, description="当前训练轮数")
    total_epochs: int = Field(..., description="总训练轮数")
    progress_percentage: float = Field(default=0.0, description="总体进度百分比(0-100)")

    # 结果信息
    model_save_path: str | None = Field(default=None, description="模型保存路径")
    log_file_path: str | None = Field(default=None, description="日志文件路径")
    result_file_path: str | None = Field(default=None, description="结果文件路径")
    final_metrics: dict | None = Field(default=None, description="最终评估指标")
    error_message: str | None = Field(default=None, description="错误信息")
    remarks: str | None = Field(default=None, description="备注信息")

    @field_validator('dataset_info', 'model_configuration', 'train_config', 'final_metrics', mode='before')
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

    @field_validator('estimated_start_time', 'actual_start_time',
                     'estimated_completion_time', 'actual_completion_time', mode='before')
    @classmethod
    def convert_datetime_to_str(cls, v):
        """将 datetime 对象转换为字符串"""
        if v is None:
            return None
        if hasattr(v, 'isoformat'):
            return v.isoformat()
        return str(v)

    @model_validator(mode='after')
    def extract_names(self):
        """从dataset_info和model_configuration中提取名称"""
        # 提取数据集名称
        if self.dataset_name is None and self.dataset_info:
            if isinstance(self.dataset_info, dict):
                self.dataset_name = self.dataset_info.get('name')

        # 提取模型名称
        if self.model_name is None and self.model_configuration:
            if isinstance(self.model_configuration, dict):
                self.model_name = self.model_configuration.get('model_name')

        return self


class TrainTaskListResponse(BaseModel):
    """训练任务列表响应"""
    model_config = ConfigDict(from_attributes=True)

    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    dataset_id: int = Field(..., description="数据集ID")
    model_config_id: int = Field(..., description="模型配置ID")
    current_epoch: int = Field(..., description="当前轮数")
    total_epochs: int = Field(..., description="总轮数")
    progress_percentage: float = Field(..., description="进度百分比")
    created_time: str = Field(..., description="创建时间")
    actual_start_time: str | None = Field(default=None, description="开始时间")

    # 简化的快照信息（从JSON中提取）
    dataset_name: str | None = Field(default=None, description="数据集名称")
    model_name: str | None = Field(default=None, description="模型名称")
    model_save_path: str | None = Field(default=None, description="模型保存路径（相对路径）")

    # 用于存储原始JSON数据的隐藏字段
    dataset_info: dict | None = Field(default=None, exclude=True)
    model_configuration: dict | None = Field(default=None, validation_alias="model_config", exclude=True)

    @field_validator('dataset_info', 'model_configuration', mode='before')
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

    @model_validator(mode='after')
    def extract_names(self):
        """从dataset_info和model_configuration中提取名称"""
        if self.dataset_name is None and self.dataset_info:
            if isinstance(self.dataset_info, dict):
                self.dataset_name = self.dataset_info.get('name')
        if self.model_name is None and self.model_configuration:
            if isinstance(self.model_configuration, dict):
                self.model_name = self.model_configuration.get('model_name') or self.model_configuration.get('display_name')
        return self

    @field_validator('created_time', 'actual_start_time', mode='before')
    @classmethod
    def convert_datetime_to_str(cls, v):
        """将 datetime 对象转换为字符串"""
        if v is None:
            return None
        if hasattr(v, 'isoformat'):
            return v.isoformat()
        return str(v)


# ==================== 训练进度相关 ====================

class TrainMetricsSchema(BaseModel):
    """训练指标（对应使用手册WebSocket实时数据）"""
    train_loss: float = Field(..., description="训练损失值")
    train_accuracy: float = Field(..., ge=0, le=1, description="训练准确率(0-1)")
    val_loss: float | None = Field(default=None, description="验证损失值")
    val_accuracy: float | None = Field(default=None, ge=0, le=1, description="验证准确率(0-1)")
    learning_rate: float = Field(..., description="当前学习率")


class ResourceMetricsSchema(BaseModel):
    """资源监控指标（对应使用手册资源监控数据）"""
    gpu: dict | None = Field(default=None, description="GPU指标")
    system: dict | None = Field(default=None, description="系统指标")


class TrainProgressRecordRequest(BaseModel):
    """训练进度记录请求"""
    task_id: str = Field(..., description="训练任务ID")
    epoch: int = Field(..., gt=0, description="当前训练轮数")
    batch: int | None = Field(default=None, ge=0, description="当前批次")
    total_batches: int | None = Field(default=None, gt=0, description="总批次数")

    # 训练指标
    train_loss: float | None = Field(default=None, description="训练损失值")
    train_accuracy: float | None = Field(default=None, ge=0, le=1, description="训练准确率")
    val_loss: float | None = Field(default=None, description="验证损失值")
    val_accuracy: float | None = Field(default=None, ge=0, le=1, description="验证准确率")
    learning_rate: float | None = Field(default=None, description="当前学习率")

    # 进度信息
    epoch_progress: float | None = Field(default=None, ge=0, le=1, description="当前epoch进度")
    overall_progress: float | None = Field(default=None, ge=0, le=1, description="整体进度")

    # 资源监控
    resource_metrics: dict | None = Field(default=None, description="资源使用指标")
    additional_metrics: dict | None = Field(default=None, description="额外指标")


class TrainProgressResponse(BaseModel):
    """训练进度响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="进度记录ID")
    task_id: str = Field(..., description="训练任务ID")
    epoch: int = Field(..., description="当前训练轮数")
    batch: int | None = Field(default=None, description="当前批次")
    total_batches: int | None = Field(default=None, description="总批次数")

    # 训练指标
    train_loss: float | None = Field(default=None, description="训练损失值")
    train_accuracy: float | None = Field(default=None, description="训练准确率")
    val_loss: float | None = Field(default=None, description="验证损失值")
    val_accuracy: float | None = Field(default=None, description="验证准确率")
    learning_rate: float | None = Field(default=None, description="当前学习率")

    # 进度信息
    epoch_progress: float | None = Field(default=None, description="当前epoch进度")
    overall_progress: float | None = Field(default=None, description="整体进度")

    # 资源监控
    resource_metrics: dict | None = Field(default=None, description="资源使用指标")
    additional_metrics: dict | None = Field(default=None, description="额外指标")

    # 时间戳
    timestamp: str = Field(..., description="记录时间戳")

    @field_validator('resource_metrics', 'additional_metrics', mode='before')
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

    @field_validator('timestamp', mode='before')
    @classmethod
    def convert_datetime_to_str(cls, v):
        """将 datetime 对象转换为字符串"""
        if v is None:
            return None
        if hasattr(v, 'isoformat'):
            return v.isoformat()
        return str(v)


class TrainProgressCurveResponse(BaseModel):
    """训练曲线数据响应（用于图表展示）"""
    task_id: str = Field(..., description="任务ID")
    total_epochs: int = Field(..., description="总训练轮数")
    current_epoch: int = Field(..., description="当前训练轮数")
    data_points: list[dict] = Field(..., description="数据点列表（每个epoch的指标）")


# ==================== WebSocket 实时推送数据 ====================

class WSTrainingMetricsData(BaseModel):
    """WebSocket训练指标数据（对应使用手册第206-229行）"""
    epoch: int = Field(..., description="当前轮数")
    batch: int = Field(..., description="当前批次")
    total_batches: int = Field(..., description="总批次数")

    metrics: TrainMetricsSchema = Field(..., description="训练指标")
    progress: dict = Field(..., description="进度信息")


class WSTrainingMetricsMessage(BaseModel):
    """WebSocket训练指标消息"""
    type: str = Field(default="training_metrics", description="消息类型")
    timestamp: str = Field(..., description="时间戳")
    data: WSTrainingMetricsData = Field(..., description="训练指标数据")


class WSResourceMetricsMessage(BaseModel):
    """WebSocket资源监控消息（对应使用手册第231-250行）"""
    type: str = Field(default="resource_metrics", description="消息类型")
    timestamp: str = Field(..., description="时间戳")
    data: ResourceMetricsSchema = Field(..., description="资源监控数据")


class WSTrainingLogMessage(BaseModel):
    """WebSocket训练日志消息"""
    type: str = Field(default="training_log", description="消息类型")
    timestamp: str = Field(..., description="时间戳")
    level: str = Field(..., description="日志级别(INFO/WARNING/ERROR)")
    message: str = Field(..., description="日志消息")


class WSTaskStatusMessage(BaseModel):
    """WebSocket任务状态变更消息"""
    type: str = Field(default="task_status", description="消息类型")
    timestamp: str = Field(..., description="时间戳")
    task_id: str = Field(..., description="任务ID")
    old_status: str = Field(..., description="旧状态")
    new_status: str = Field(..., description="新状态")
    message: str | None = Field(default=None, description="状态变更说明")


# ==================== 查询参数 ====================

class TrainTaskQueryParam:
    """训练任务查询参数"""
    def __init__(
        self,
        task_id: str | None = Query(None, description="任务ID"),
        status: str | None = Query(None, description="任务状态"),
        dataset_id: int | None = Query(None, description="数据集ID"),
        model_config_id: int | None = Query(None, description="模型配置ID"),
        created_time: list[DateTimeStr] | None = Query(None, description="创建时间范围"),
        created_id: int | None = Query(None, description="创建人ID"),
    ) -> None:
        # 精确查询
        if task_id:
            self.task_id = ("eq", task_id)
        if status:
            self.status = ("eq", status)
        if dataset_id:
            self.dataset_id = ("eq", dataset_id)
        if model_config_id:
            self.model_config_id = ("eq", model_config_id)
        if created_id:
            self.created_id = ("eq", created_id)

        # 时间范围查询
        if created_time and len(created_time) == 2:
            self.created_time = ("between", (created_time[0], created_time[1]))

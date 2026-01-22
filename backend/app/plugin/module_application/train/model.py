# -*- coding: utf-8 -*-

import enum
from sqlalchemy import String, Integer, Text, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from app.core.base_model import ModelMixin, UserMixin


class ModelModalityEnum(enum.Enum):
    """模型适用模态类型枚举"""
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    TEXT = "text"
    SENSOR = "sensor"
    MULTIMODAL = "multimodal"


class ModelTaskTypeEnum(enum.Enum):
    """模型适用任务类型枚举"""
    # 图像任务
    IMAGE_CLASSIFICATION = "image_classification"
    OBJECT_DETECTION = "object_detection"
    SEMANTIC_SEGMENTATION = "semantic_segmentation"
    INSTANCE_SEGMENTATION = "instance_segmentation"
    IMAGE_GENERATION = "image_generation"

    # 音频任务
    SPEECH_RECOGNITION = "speech_recognition"
    AUDIO_CLASSIFICATION = "audio_classification"
    SOUND_EVENT_DETECTION = "sound_event_detection"

    # 视频任务
    VIDEO_CLASSIFICATION = "video_classification"
    ACTION_RECOGNITION = "action_recognition"
    VIDEO_OBJECT_TRACKING = "video_object_tracking"

    # 文本任务
    TEXT_CLASSIFICATION = "text_classification"
    NAMED_ENTITY_RECOGNITION = "named_entity_recognition"
    TEXT_GENERATION = "text_generation"
    SENTIMENT_ANALYSIS = "sentiment_analysis"

    # 传感器任务
    TIME_SERIES_CLASSIFICATION = "time_series_classification"
    ANOMALY_DETECTION = "anomaly_detection"

    # 多模态任务
    VISUAL_QUESTION_ANSWERING = "visual_question_answering"
    IMAGE_CAPTIONING = "image_captioning"


class ModelStatusEnum(enum.Enum):
    """模型状态枚举"""
    ACTIVE = "active"  # 激活可用
    INACTIVE = "inactive"  # 停用
    DEPRECATED = "deprecated"  # 已弃用


class ModelConfigModel(ModelMixin, UserMixin):
    """
    模型配置表

    用于存储深度学习模型的配置信息
    支持根据数据集的模态和任务类型推荐合适的模型
    记录预训练权重、默认训练参数等配置
    """
    __tablename__: str = 'model_config'
    __table_args__ = (
        Index('idx_model_status', 'status'),
        Index('idx_model_name', 'model_name'),
        {'comment': '模型配置表'}
    )
    __loader_options__: list[str] = ["created_by", "updated_by"]

    # 基本信息
    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment='模型名称(唯一标识,如:ResNet50, YOLO-v8, BERT等)'
    )
    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment='显示名称(用于前端展示)'
    )
    model_version: Mapped[str] = mapped_column(
        String(50),
        default="1.0.0",
        nullable=False,
        comment='模型版本号'
    )

    # 适用范围
    supported_modalities: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment='适用模态列表(逗号分隔,如:image,video)'
    )
    supported_task_types: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment='适用任务类型列表(逗号分隔,如:image_classification,object_detection)'
    )

    # 模型描述
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='模型简介(包括模型特点、优势等)'
    )
    architecture_summary: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment='架构简要说明'
    )

    # 预训练权重信息
    pretrained_weights: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment='预训练权重信息(JSON格式,包含权重文件路径、下载URL、权重来源等)'
    )

    # 默认训练配置
    default_train_config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment='默认训练配置(JSON格式,包含学习率、批次大小、优化器、损失函数、训练轮数等)'
    )

    # 模型性能指标参考
    performance_metrics: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment='性能指标参考(JSON格式,如在某些标准数据集上的准确率、速度等)'
    )

    # 资源要求
    hardware_requirements: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment='硬件要求(JSON格式,包含最小/推荐GPU内存、CPU核心数等)'
    )

    # 模型框架信息
    framework: Mapped[str] = mapped_column(
        String(50),
        default="PyTorch",
        nullable=False,
        comment='深度学习框架(PyTorch, TensorFlow, PaddlePaddle等)'
    )
    framework_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment='框架版本要求'
    )

    # 模型文件信息
    model_code_path: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment='模型代码路径(相对路径或绝对路径)'
    )
    config_template_path: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment='配置模板文件路径'
    )

    # 推荐优先级和状态
    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment='推荐优先级(数值越大优先级越高,用于排序)'
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=ModelStatusEnum.ACTIVE.value,
        nullable=False,
        comment='模型状态(active:激活 inactive:停用 deprecated:已弃用)'
    )

    # 使用统计
    usage_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment='使用次数统计'
    )

    # 扩展信息
    tags: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment='标签(逗号分隔,如:轻量级,高精度,实时推理)'
    )
    reference_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment='参考文档或论文链接'
    )
    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='备注信息'
    )

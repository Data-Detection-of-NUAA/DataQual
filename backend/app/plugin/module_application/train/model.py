# -*- coding: utf-8 -*-

import enum
from datetime import datetime
from sqlalchemy import String, Integer, Text, JSON, Index, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
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


class TrainTaskStatusEnum(enum.Enum):
    """训练任务状态枚举"""
    CREATED = "created"  # 已创建
    PENDING = "pending"  # 等待中
    RUNNING = "running"  # 运行中
    PAUSED = "paused"  # 已暂停
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


class TrainTaskModel(ModelMixin, UserMixin):
    """
    训练任务表

    用于存储模型训练任务的基本信息
    记录任务状态、关联的数据集和模型配置、训练参数等
    对应使用手册第四步"开始训练"的任务记录结构
    """
    __tablename__: str = 'train_task'
    __table_args__ = (
        Index('idx_task_status', 'status'),
        Index('idx_task_user', 'created_id'),
        Index('idx_task_dataset', 'dataset_id'),
        Index('idx_task_model', 'model_config_id'),
        Index('idx_task_id', 'task_id'),
        {'comment': '训练任务表'}
    )
    __loader_options__: list[str] = ["created_by", "updated_by"]

    # 任务标识
    task_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment='任务ID(格式:TRAIN_timestamp_userid,如TRAIN_1710835200_1001)'
    )

    # 任务状态
    status: Mapped[str] = mapped_column(
        String(20),
        default=TrainTaskStatusEnum.CREATED.value,
        nullable=False,
        comment='任务状态(created/pending/running/paused/completed/failed/cancelled)'
    )

    # 关联数据集信息
    dataset_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment='数据集ID(关联dataset表)'
    )
    dataset_info: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment='数据集信息快照(JSON格式:filename,modality,sample_count,class_count等)'
    )

    # 关联模型配置
    model_config_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment='模型配置ID(关联model_config表)'
    )
    model_config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment='模型配置快照(JSON格式:name,parameters,hyperparameters等)'
    )

    # 训练参数配置
    train_config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment='训练超参数配置(JSON格式:learning_rate,batch_size,epochs,optimizer等)'
    )

    # 时间戳信息
    estimated_start_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment='预计开始时间'
    )
    actual_start_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment='实际开始时间'
    )
    estimated_completion_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment='预计完成时间'
    )
    actual_completion_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment='实际完成时间'
    )

    # 训练进度信息
    current_epoch: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment='当前训练轮数'
    )
    total_epochs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment='总训练轮数'
    )
    progress_percentage: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        comment='总体进度百分比(0-100)'
    )

    # 训练结果路径
    model_save_path: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment='训练好的模型保存路径(相对于static/train/tasks/)'
    )
    log_file_path: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment='训练日志文件路径'
    )
    result_file_path: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment='训练结果JSON文件路径(result.json)'
    )

    # 最终评估指标
    final_metrics: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment='最终评估指标(JSON格式:final_loss,final_accuracy,val_loss,val_accuracy等)'
    )

    # 错误信息
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='任务失败时的错误信息'
    )

    # 备注信息
    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment='备注信息'
    )


class TrainProgressModel(ModelMixin):
    """
    训练进度表

    用于存储训练过程中的实时指标数据
    记录每个epoch/batch的损失、准确率等指标
    支持WebSocket实时推送和前端图表展示
    对应使用手册第四步"模型训练与监控"的实时数据
    """
    __tablename__: str = 'train_progress'
    __table_args__ = (
        Index('idx_progress_task', 'task_id'),
        Index('idx_progress_epoch', 'task_id', 'epoch'),
        Index('idx_progress_time', 'timestamp'),
        {'comment': '训练进度表'}
    )

    # 关联任务
    task_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment='训练任务ID(关联train_task表的task_id)'
    )

    # 训练进度标识
    epoch: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment='当前训练轮数(epoch编号,从1开始)'
    )
    batch: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment='当前批次(batch编号,可选,用于更细粒度监控)'
    )
    total_batches: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment='总批次数(每个epoch的batch总数)'
    )

    # 训练指标
    train_loss: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment='训练损失值'
    )
    train_accuracy: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment='训练准确率(0-1之间)'
    )
    val_loss: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment='验证损失值'
    )
    val_accuracy: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment='验证准确率(0-1之间)'
    )
    learning_rate: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment='当前学习率'
    )

    # 进度信息
    epoch_progress: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment='当前epoch进度百分比(0-1之间)'
    )
    overall_progress: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment='整体训练进度百分比(0-1之间)'
    )

    # 资源监控数据(可选)
    resource_metrics: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment='资源使用指标(JSON格式:gpu_utilization,memory_used,cpu_usage等)'
    )

    # 时间戳
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
        comment='记录时间戳'
    )

    # 扩展指标
    additional_metrics: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment='额外的自定义指标(JSON格式,如precision,recall,f1_score等)'
    )


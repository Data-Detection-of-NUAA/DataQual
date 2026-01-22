# -*- coding: utf-8 -*-

import enum
from sqlalchemy import String, Integer, BIGINT, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from app.core.base_model import ModelMixin, UserMixin


class DatasetModalityEnum(enum.Enum):
    """数据集模态类型枚举"""
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    TEXT = "text"
    SENSOR = "sensor"
    MULTIMODAL = "multimodal"
    UNKNOWN = "unknown"


class UploadStatusEnum(enum.Enum):
    """上传状态枚举"""
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DatasetModel(ModelMixin, UserMixin):
    """
    数据集信息表

    用于存储数据集的基本信息、文件信息
    支持大文件上传（分片上传）、秒传检测
    记录上传状态和进度、分析结果
    """
    __tablename__: str = 'dataset_info'
    __table_args__ = (
        Index('idx_dataset_hash', 'file_hash'),
        Index('idx_dataset_upload_status', 'upload_status'),
        {'comment': '数据集信息表'}
    )
    __loader_options__: list[str] = ["created_by", "updated_by"]

    # 基本信息
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment='数据集名称')
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False, comment='原始文件名')

    # 文件信息
    file_size: Mapped[int] = mapped_column(BIGINT, nullable=False, comment='文件大小(字节)')
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False, comment='存储路径')
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, comment='文件哈希值(MD5/SHA256)')

    # 上传信息
    upload_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, comment='上传会话ID')
    upload_status: Mapped[str] = mapped_column(
        String(20),
        default=UploadStatusEnum.UPLOADING.value,
        nullable=False,
        comment='上传状态(uploading:上传中 completed:已完成 failed:失败 cancelled:已取消)'
    )

    # 数据集特征信息
    modality: Mapped[str] = mapped_column(
        String(20),
        default=DatasetModalityEnum.UNKNOWN.value,
        nullable=False,
        comment='数据模态类型(image/audio/video/text/sensor/multimodal/unknown)'
    )
    task_type: Mapped[str | None] = mapped_column(
        String(100),
        default="classification",
        nullable=True,
        comment='任务类型(classification/object_detection/speech_recognition等)'
    )
    sample_count: Mapped[int | None] = mapped_column(Integer, nullable=True, comment='样本数量')
    class_count: Mapped[int | None] = mapped_column(Integer, nullable=True, comment='类别数量')

    # 扩展信息
    dataset_metadata: Mapped[str | None] = mapped_column("metadata", Text, nullable=True, comment='元数据(JSON格式,包含特征统计、标签信息等)')
    analysis_result: Mapped[str | None] = mapped_column(Text, nullable=True, comment='分析结果(JSON格式)')

    # 关联关系
    chunks: Mapped[list["DatasetChunkModel"]] = relationship(
        "DatasetChunkModel",
        back_populates="dataset",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="DatasetChunkModel.chunk_index"
    )


class DatasetChunkModel(ModelMixin):
    """
    数据集分片信息表

    用于存储大文件的分片上传进度
    支持断点续传功能
    """
    __tablename__: str = 'dataset_chunk'
    __table_args__ = (
        Index('idx_chunk_dataset_id', 'dataset_id'),
        Index('idx_chunk_upload_id', 'upload_id'),
        Index('idx_chunk_index', 'dataset_id', 'chunk_index'),
        {'comment': '数据集分片表'}
    )

    # 关联数据集
    dataset_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('dataset_info.id', ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        comment='数据集ID'
    )

    # 上传会话ID (用于分片续传)
    upload_id: Mapped[str] = mapped_column(String(64), nullable=False, comment='上传会话ID')

    # 分片信息
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, comment='分片索引(从0开始)')
    chunk_hash: Mapped[str] = mapped_column(String(64), nullable=False, comment='分片哈希值(用于校验)')
    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False, comment='分片大小(字节)')
    chunk_storage_path: Mapped[str] = mapped_column(String(512), nullable=False, comment='分片存储路径')

    # 上传状态
    is_uploaded: Mapped[bool] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment='是否已上传(0:未上传 1:已上传)'
    )

    # 关联关系
    dataset: Mapped[Optional["DatasetModel"]] = relationship(
        "DatasetModel",
        back_populates="chunks",
        lazy="selectin"
    )

# -*- coding: utf-8 -*-

import json
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from fastapi import Query

from app.core.base_schema import BaseSchema, UserBySchema
from app.core.validator import DateTimeStr


# ==================== 上传初始化 ====================

class UploadInitRequest(BaseModel):
    """上传初始化请求模型"""
    filename: str = Field(..., min_length=1, max_length=255, description="原始文件名")
    file_size: int = Field(..., gt=0, description="文件大小(字节)")
    file_hash: str = Field(..., min_length=32, max_length=64, description="文件哈希值(MD5/SHA256)")
    chunk_size: int = Field(default=5 * 1024 * 1024, gt=0, le=100 * 1024 * 1024, description="分片大小(字节),默认5MB,最大100MB")
    name: str | None = Field(default=None, max_length=255, description="数据集名称,不传则使用文件名")
    task_type: str | None = Field(default="classification", max_length=100, description="任务类型")

    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """验证文件名格式"""
        v = v.strip()
        if not v:
            raise ValueError('文件名不能为空')
        # 检查文件扩展名
        allowed_extensions = ['.zip', '.tar', '.gz', '.rar', '.7z', '.tar.gz', '.tar.bz2']
        if not any(v.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError(f'不支持的文件格式,仅支持: {", ".join(allowed_extensions)}')
        return v

    @field_validator('file_hash')
    @classmethod
    def validate_file_hash(cls, v: str) -> str:
        """验证哈希值格式"""
        v = v.strip().lower()
        if len(v) not in [32, 64]:  # MD5(32) or SHA256(64)
            raise ValueError('哈希值长度必须为32(MD5)或64(SHA256)位')
        if not all(c in '0123456789abcdef' for c in v):
            raise ValueError('哈希值只能包含十六进制字符(0-9, a-f)')
        return v

    @model_validator(mode='after')
    def validate_file_size_limit(self):
        """验证文件大小限制"""
        max_size = 100 * 1024 * 1024 * 1024  # 100GB
        if self.file_size > max_size:
            raise ValueError(f'文件大小超过限制(最大100GB)')
        return self


class ChunkInfo(BaseModel):
    """分片信息"""
    chunk_index: int = Field(..., description="分片索引")
    chunk_size: int = Field(..., description="分片大小(字节)")
    is_uploaded: bool = Field(default=False, description="是否已上传")


class UploadInitResponse(BaseModel):
    """上传初始化响应模型"""
    upload_id: str = Field(..., description="上传会话ID")
    dataset_id: int | None = Field(default=None, description="数据集ID(如果文件已存在)")
    storage_path: str = Field(..., description="存储路径")
    total_chunks: int = Field(..., description="总分片数")
    chunk_size: int = Field(..., description="分片大小(字节)")
    chunks: list[ChunkInfo] = Field(default_factory=list, description="分片列表")
    file_exists: bool = Field(default=False, description="文件是否已存在")
    uploaded_chunks: list[int] = Field(default_factory=list, description="已上传的分片索引列表(用于断点续传)")


# ==================== 分片上传 ====================

class ChunkUploadRequest(BaseModel):
    """分片上传请求模型"""
    upload_id: str = Field(..., min_length=1, max_length=64, description="上传会话ID")
    chunk_index: int = Field(..., ge=0, description="分片索引(从0开始)")
    chunk_hash: str = Field(..., min_length=32, max_length=64, description="分片哈希值(MD5/SHA256)")
    # 注: chunk_data 通过 UploadFile 传递,不在此Schema中定义

    @field_validator('chunk_hash')
    @classmethod
    def validate_chunk_hash(cls, v: str) -> str:
        """验证分片哈希值格式"""
        v = v.strip().lower()
        if len(v) not in [32, 64]:
            raise ValueError('哈希值长度必须为32(MD5)或64(SHA256)位')
        if not all(c in '0123456789abcdef' for c in v):
            raise ValueError('哈希值只能包含十六进制字符(0-9, a-f)')
        return v


class ChunkUploadResponse(BaseModel):
    """分片上传响应模型"""
    upload_id: str = Field(..., description="上传会话ID")
    chunk_index: int = Field(..., description="分片索引")
    chunk_uploaded: bool = Field(..., description="分片是否上传成功")
    progress: float = Field(..., ge=0, le=1, description="上传进度(0-1)")
    uploaded_chunks: int = Field(..., description="已上传分片数")
    total_chunks: int = Field(..., description="总分片数")


# ==================== 上传完成 ====================

class UploadCompleteRequest(BaseModel):
    """上传完成请求模型"""
    upload_id: str = Field(..., min_length=1, max_length=64, description="上传会话ID")
    verify_hash: bool = Field(default=True, description="是否验证文件哈希值")


class UploadCompleteResponse(BaseModel):
    """上传完成响应模型"""
    dataset_id: int = Field(..., description="数据集ID")
    upload_id: str = Field(..., description="上传会话ID")
    storage_path: str = Field(..., description="最终存储路径")
    file_size: int = Field(..., description="文件大小(字节)")
    file_hash: str = Field(..., description="文件哈希值")
    hash_verified: bool = Field(default=False, description="哈希值是否验证通过")
    merge_success: bool = Field(..., description="分片合并是否成功")
    message: str = Field(default="上传完成", description="消息")


# ==================== 断点续传查询 ====================

class ResumeUploadRequest(BaseModel):
    """断点续传查询请求模型"""
    file_hash: str = Field(..., min_length=32, max_length=64, description="文件哈希值")

    @field_validator('file_hash')
    @classmethod
    def validate_file_hash(cls, v: str) -> str:
        """验证哈希值格式"""
        v = v.strip().lower()
        if len(v) not in [32, 64]:
            raise ValueError('哈希值长度必须为32(MD5)或64(SHA256)位')
        if not all(c in '0123456789abcdef' for c in v):
            raise ValueError('哈希值只能包含十六进制字符(0-9, a-f)')
        return v


class ResumeUploadResponse(BaseModel):
    """断点续传查询响应模型"""
    can_resume: bool = Field(..., description="是否可以断点续传")
    upload_id: str | None = Field(default=None, description="上传会话ID")
    uploaded_chunks: list[int] = Field(default_factory=list, description="已上传的分片索引列表")
    total_chunks: int | None = Field(default=None, description="总分片数")
    progress: float = Field(default=0.0, ge=0, le=1, description="上传进度(0-1)")
    file_exists: bool = Field(default=False, description="文件是否已完整存在")
    dataset_id: int | None = Field(default=None, description="数据集ID(如果文件已存在)")


# ==================== 数据集信息 ====================

class DatasetCreateSchema(BaseModel):
    """创建数据集请求模型(仅用于非上传方式创建)"""
    name: str = Field(..., min_length=1, max_length=255, description="数据集名称")
    original_filename: str = Field(..., max_length=255, description="原始文件名")
    file_size: int = Field(..., gt=0, description="文件大小(字节)")
    storage_path: str = Field(..., max_length=512, description="存储路径")
    file_hash: str = Field(..., min_length=32, max_length=64, description="文件哈希值")
    status: str = Field(default="0", description="是否启用(0:启用 1:禁用)")
    description: str | None = Field(default=None, max_length=1000, description="数据集描述")
    task_type: str | None = Field(default="classification", max_length=100, description="任务类型")


class DatasetUpdateSchema(BaseModel):
    """更新数据集请求模型"""
    name: str | None = Field(default=None, min_length=1, max_length=255, description="数据集名称")
    status: str | None = Field(default=None, description="是否启用(0:启用 1:禁用)")
    description: str | None = Field(default=None, max_length=1000, description="数据集描述")
    modality: str | None = Field(default=None, description="数据模态类型")
    task_type: str | None = Field(default=None, max_length=100, description="任务类型")
    sample_count: int | None = Field(default=None, ge=0, description="样本数量")
    class_count: int | None = Field(default=None, ge=0, description="类别数量")
    dataset_metadata: dict | None = Field(default=None, description="元数据(JSON格式)")
    analysis_result: dict | None = Field(default=None, description="分析结果(JSON格式)")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        """验证状态值"""
        if v is not None and v not in ["0", "1"]:
            raise ValueError('状态值必须为0或1')
        return v

    @field_validator('modality')
    @classmethod
    def validate_modality(cls, v: str | None) -> str | None:
        """验证模态类型"""
        if v is not None:
            allowed_modalities = ['image', 'audio', 'video', 'text', 'sensor', 'multimodal', 'unknown']
            if v not in allowed_modalities:
                raise ValueError(f'模态类型必须为: {", ".join(allowed_modalities)}')
        return v


class DatasetAnalysisInfo(BaseModel):
    """数据集分析信息"""
    modality: str | None = Field(default=None, description="数据模态类型")
    sample_count: int | None = Field(default=None, description="样本数量")
    class_count: int | None = Field(default=None, description="类别数量")
    feature_dimension: int | None = Field(default=None, description="特征维度")
    format_info: dict | None = Field(default=None, description="格式信息")
    preview_samples: list[str] | None = Field(default=None, description="前5个样本预览")


class DatasetOutSchema(BaseSchema, UserBySchema):
    """数据集响应模型"""
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="数据集名称")
    original_filename: str = Field(..., description="原始文件名")
    file_size: int = Field(..., description="文件大小(字节)")
    storage_path: str = Field(..., description="存储路径")
    file_hash: str = Field(..., description="文件哈希值")
    upload_id: str | None = Field(default=None, description="上传会话ID")
    upload_status: str = Field(..., description="上传状态")
    modality: str = Field(..., description="数据模态类型")
    task_type: str | None = Field(default="classification", description="任务类型")
    sample_count: int | None = Field(default=None, description="样本数量")
    class_count: int | None = Field(default=None, description="类别数量")
    dataset_metadata: dict | None = Field(default=None, description="元数据")
    analysis_result: dict | None = Field(default=None, description="分析结果")

    @field_validator('dataset_metadata', 'analysis_result', mode='before')
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


class DatasetDetailOutSchema(DatasetOutSchema):
    """数据集详细信息响应模型(包含分片信息)"""
    chunk_count: int | None = Field(default=None, description="分片数量")
    uploaded_chunk_count: int | None = Field(default=None, description="已上传分片数量")


# ==================== 查询参数 ====================

class DatasetQueryParam:
    """数据集查询参数"""
    def __init__(
        self,
        name: str | None = Query(None, description="数据集名称(模糊查询)"),
        original_filename: str | None = Query(None, description="原始文件名(模糊查询)"),
        upload_status: str | None = Query(None, description="上传状态"),
        modality: str | None = Query(None, description="数据模态类型"),
        status: str | None = Query(None, description="是否启用(0:启用 1:禁用)"),
        created_time: list[DateTimeStr] | None = Query(None, description="创建时间范围", examples=["2025-01-01 00:00:00", "2025-12-31 23:59:59"]),
        updated_time: list[DateTimeStr] | None = Query(None, description="更新时间范围", examples=["2025-01-01 00:00:00", "2025-12-31 23:59:59"]),
        created_id: int | None = Query(None, description="创建人ID"),
        file_size_min: int | None = Query(None, ge=0, description="最小文件大小(字节)"),
        file_size_max: int | None = Query(None, ge=0, description="最大文件大小(字节)"),
    ) -> None:
        # 模糊查询字段
        if name:
            self.name = ("like", name)
        if original_filename:
            self.original_filename = ("like", original_filename)

        # 精确查询字段
        if upload_status:
            self.upload_status = ("eq", upload_status)
        if modality:
            self.modality = ("eq", modality)
        if status:
            self.status = ("eq", status)
        if created_id:
            self.created_id = ("eq", created_id)

        # 时间范围查询
        if created_time and len(created_time) == 2:
            self.created_time = ("between", (created_time[0], created_time[1]))
        if updated_time and len(updated_time) == 2:
            self.updated_time = ("between", (updated_time[0], updated_time[1]))

        # 文件大小范围查询
        if file_size_min is not None and file_size_max is not None:
            self.file_size = ("between", (file_size_min, file_size_max))
        elif file_size_min is not None:
            self.file_size = ("ge", file_size_min)
        elif file_size_max is not None:
            self.file_size = ("le", file_size_max)


# ==================== 数据集删除 ====================

class DatasetDeleteRequest(BaseModel):
    """数据集删除请求模型"""
    delete_file: bool = Field(default=False, description="是否同时删除存储文件")


# ==================== 数据集分析 ====================

class DatasetAnalysisRequest(BaseModel):
    """数据集分析请求模型"""
    dataset_id: int = Field(..., description="数据集ID")
    analysis_options: dict | None = Field(default=None, description="分析选项配置")


class DatasetAnalysisResponse(BaseModel):
    """数据集分析响应模型"""
    task_id: str = Field(..., description="分析任务ID")
    dataset_id: int = Field(..., description="数据集ID")
    status: str = Field(..., description="分析状态(pending/running/completed/failed)")
    message: str = Field(default="分析任务已创建", description="消息")


class DatasetAnalysisStatusResponse(BaseModel):
    """数据集分析状态查询响应模型"""
    task_id: str = Field(..., description="分析任务ID")
    status: str = Field(..., description="分析状态")
    progress: float = Field(default=0.0, ge=0, le=1, description="分析进度(0-1)")
    result: DatasetAnalysisInfo | None = Field(default=None, description="分析结果")
    error: str | None = Field(default=None, description="错误信息")

# -*- coding: utf-8 -*-

from fastapi import APIRouter, Body, Depends, Path, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional
from fastapi_limiter.depends import RateLimiter

from app.common.response import SuccessResponse
from app.core.router_class import OperationLogRoute
from app.core.base_params import PaginationQueryParam
from app.core.dependencies import AuthPermission
from app.core.logger import log
from app.api.v1.module_system.auth.schema import AuthSchema

from .service import DatasetUploadService, DatasetService
from .schema import (
    UploadInitRequest,
    UploadInitResponse,
    ChunkUploadRequest,
    ChunkUploadResponse,
    UploadCompleteRequest,
    UploadCompleteResponse,
    ResumeUploadRequest,
    ResumeUploadResponse,
    DatasetUpdateSchema,
    DatasetQueryParam,
    DatasetDeleteRequest,
)


# ==================== 路由定义 ====================

# 注意：保持 /dataset/data 前缀以兼容现有前端API调用
# module_application会自动添加/application前缀，但我们显式设置完整路径来覆盖
DatasetRouter = APIRouter(route_class=OperationLogRoute, prefix="/dataset/data", tags=["数据集管理"])


# ==================== 上传管理 API ====================

@DatasetRouter.post(
    "/upload/init",
    summary="上传初始化",
    description="初始化文件上传，创建上传会话并返回分片信息",
    response_model=UploadInitResponse,
    dependencies=[Depends(RateLimiter(times=100, seconds=60))]  # 放宽限制：1分钟内100次
)
async def upload_init_controller(
    data: UploadInitRequest,
    auth: AuthSchema = Depends(AuthPermission(["module_dataset:upload:init"]))
) -> JSONResponse:
    """
    上传初始化

    功能：
    - 检查文件是否已存在（秒传）
    - 创建上传会话
    - 生成分片信息
    - 支持断点续传

    参数:
    - data (UploadInitRequest): 上传初始化请求数据
      - filename: 原始文件名
      - file_size: 文件大小(字节)
      - file_hash: 文件哈希值(MD5/SHA256)
      - chunk_size: 分片大小(默认5MB)
      - name: 数据集名称(可选)
    - auth (AuthSchema): 认证信息

    返回:
    - UploadInitResponse: 上传初始化响应
      - upload_id: 上传会话ID
      - dataset_id: 数据集ID
      - storage_path: 存储路径
      - total_chunks: 总分片数
      - chunk_size: 分片大小
      - chunks: 分片列表
      - file_exists: 文件是否已存在（秒传）
      - uploaded_chunks: 已上传的分片索引列表
    """
    result = await DatasetUploadService.upload_init_service(auth=auth, data=data)

    if result.file_exists:
        log.info(f"文件秒传成功: {data.filename}, dataset_id: {result.dataset_id}")
        return SuccessResponse(data=result.model_dump(), msg="文件已存在，秒传成功")

    log.info(f"上传初始化成功: {data.filename}, upload_id: {result.upload_id}")
    return SuccessResponse(data=result.model_dump(), msg="上传初始化成功")


@DatasetRouter.post(
    "/upload/chunk",
    summary="分片上传",
    description="上传单个文件分片",
    response_model=ChunkUploadResponse,
    dependencies=[Depends(RateLimiter(times=10000, seconds=60))]  # 极宽松限制：1分钟内10000次（支持100GB文件）
)
async def chunk_upload_controller(
    upload_id: str = Form(..., description="上传会话ID"),
    chunk_index: int = Form(..., description="分片索引"),
    chunk_hash: str = Form(..., description="分片哈希值"),
    file: UploadFile = File(..., description="分片文件"),
    auth: AuthSchema = Depends(AuthPermission(["module_dataset:upload:chunk"]))
) -> JSONResponse:
    """
    分片上传

    功能：
    - 上传单个文件分片
    - 验证分片哈希值
    - 记录上传进度
    - 支持断点续传（重复上传会被跳过）

    参数:
    - upload_id (str): 上传会话ID
    - chunk_index (int): 分片索引(从0开始)
    - chunk_hash (str): 分片哈希值(用于校验)
    - file (UploadFile): 分片文件数据
    - auth (AuthSchema): 认证信息

    返回:
    - ChunkUploadResponse: 分片上传响应
      - upload_id: 上传会话ID
      - chunk_index: 分片索引
      - chunk_uploaded: 是否上传成功
      - progress: 上传进度(0-1)
      - uploaded_chunks: 已上传分片数
      - total_chunks: 总分片数
    """
    # 构建请求数据
    request_data = ChunkUploadRequest(
        upload_id=upload_id,
        chunk_index=chunk_index,
        chunk_hash=chunk_hash
    )

    result = await DatasetUploadService.chunk_upload_service(
        auth=auth,
        data=request_data,
        file=file
    )

    log.info(f"分片上传成功: upload_id={upload_id}, chunk={chunk_index}, progress={result.progress:.2%}")
    return SuccessResponse(data=result.model_dump(), msg="分片上传成功")


@DatasetRouter.post(
    "/upload/complete",
    summary="上传完成",
    description="完成文件上传，合并所有分片",
    response_model=UploadCompleteResponse,
    dependencies=[Depends(RateLimiter(times=100, seconds=60))]  # 放宽限制：1分钟内100次
)
async def upload_complete_controller(
    data: UploadCompleteRequest,
    auth: AuthSchema = Depends(AuthPermission(["module_dataset:upload:complete"]))
) -> JSONResponse:
    """
    上传完成

    功能：
    - 验证所有分片是否已上传
    - 合并分片文件
    - 验证文件完整性
    - 更新数据集状态
    - 清理临时文件

    参数:
    - data (UploadCompleteRequest): 上传完成请求数据
      - upload_id: 上传会话ID
      - verify_hash: 是否验证文件哈希值(默认True)
    - auth (AuthSchema): 认证信息

    返回:
    - UploadCompleteResponse: 上传完成响应
      - dataset_id: 数据集ID
      - upload_id: 上传会话ID
      - storage_path: 最终存储路径
      - file_size: 文件大小
      - file_hash: 文件哈希值
      - hash_verified: 哈希值是否验证通过
      - merge_success: 分片合并是否成功
      - message: 消息
    """
    result = await DatasetUploadService.upload_complete_service(auth=auth, data=data)

    log.info(f"上传完成: dataset_id={result.dataset_id}, size={result.file_size}")
    return SuccessResponse(data=result.model_dump(), msg="上传完成")


@DatasetRouter.post(
    "/upload/resume",
    summary="断点续传查询",
    description="查询上传进度，支持断点续传",
    response_model=ResumeUploadResponse,
    dependencies=[Depends(RateLimiter(times=100, seconds=60))]  # 放宽限制：1分钟内100次
)
async def resume_upload_controller(
    data: ResumeUploadRequest,
    auth: AuthSchema = Depends(AuthPermission(["module_dataset:upload:resume"]))
) -> JSONResponse:
    """
    断点续传查询

    功能：
    - 根据文件哈希值查询上传状态
    - 返回已上传分片列表
    - 支持秒传和断点续传

    参数:
    - data (ResumeUploadRequest): 断点续传请求数据
      - file_hash: 文件哈希值
    - auth (AuthSchema): 认证信息

    返回:
    - ResumeUploadResponse: 断点续传响应
      - can_resume: 是否可以断点续传
      - upload_id: 上传会话ID
      - uploaded_chunks: 已上传的分片索引列表
      - total_chunks: 总分片数
      - progress: 上传进度(0-1)
      - file_exists: 文件是否已完整存在
      - dataset_id: 数据集ID
    """
    result = await DatasetUploadService.resume_upload_service(auth=auth, data=data)

    if result.file_exists:
        log.info(f"文件已存在: file_hash={data.file_hash}")
        return SuccessResponse(data=result.model_dump(), msg="文件已存在")
    elif result.can_resume:
        log.info(f"支持断点续传: upload_id={result.upload_id}, progress={result.progress:.2%}")
        return SuccessResponse(data=result.model_dump(), msg="支持断点续传")
    else:
        return SuccessResponse(data=result.model_dump(), msg="无法续传")


# ==================== 数据集管理 API ====================

@DatasetRouter.get(
    "/detail/{id}",
    summary="获取数据集详情",
    description="根据ID获取数据集详细信息",
    dependencies=[Depends(RateLimiter(times=30, seconds=10))]  # 常规查询限制
)
async def get_dataset_detail_controller(
    id: int = Path(..., description="数据集ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_dataset:dataset:detail"]))
) -> JSONResponse:
    """
    获取数据集详情

    参数:
    - id (int): 数据集ID
    - auth (AuthSchema): 认证信息

    返回:
    - JSONResponse: 数据集详情
    """
    result = await DatasetService.detail_service(auth=auth, id=id)
    log.info(f"获取数据集详情成功: id={id}")
    return SuccessResponse(data=result, msg="获取数据集详情成功")


@DatasetRouter.get(
    "/list",
    summary="查询数据集列表",
    description="分页查询数据集列表",
    dependencies=[Depends(RateLimiter(times=30, seconds=10))]  # 常规查询限制
)
async def get_dataset_list_controller(
    page: PaginationQueryParam = Depends(),
    search: DatasetQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(["module_dataset:dataset:query"]))
) -> JSONResponse:
    """
    查询数据集列表（分页）

    参数:
    - page (PaginationQueryParam): 分页参数
      - page_no: 页码
      - page_size: 每页数量
      - order_by: 排序字段
    - search (DatasetQueryParam): 查询参数
      - name: 数据集名称(模糊查询)
      - original_filename: 原始文件名(模糊查询)
      - upload_status: 上传状态
      - modality: 数据模态类型
      - status: 启用状态
      - created_time: 创建时间范围
      - file_size_min: 最小文件大小
      - file_size_max: 最大文件大小
    - auth (AuthSchema): 认证信息

    返回:
    - JSONResponse: 分页数据
    """
    result = await DatasetService.page_service(
        auth=auth,
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
        order_by=page.order_by
    )
    log.info("查询数据集列表成功")
    return SuccessResponse(data=result, msg="查询数据集列表成功")


@DatasetRouter.put(
    "/update/{id}",
    summary="更新数据集",
    description="更新数据集信息（名称、描述、分析结果等）",
    dependencies=[Depends(RateLimiter(times=20, seconds=10))]  # 更新操作限制
)
async def update_dataset_controller(
    data: DatasetUpdateSchema,
    id: int = Path(..., description="数据集ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_dataset:dataset:update"]))
) -> JSONResponse:
    """
    更新数据集

    参数:
    - data (DatasetUpdateSchema): 更新数据
      - name: 数据集名称
      - status: 启用状态
      - description: 数据集描述
      - modality: 数据模态类型
      - sample_count: 样本数量
      - class_count: 类别数量
      - metadata: 元数据
      - analysis_result: 分析结果
    - id (int): 数据集ID
    - auth (AuthSchema): 认证信息

    返回:
    - JSONResponse: 更新后的数据集信息
    """
    result = await DatasetService.update_service(auth=auth, id=id, data=data)
    log.info(f"更新数据集成功: id={id}, name={result.get('name')}")
    return SuccessResponse(data=result, msg="更新数据集成功")


@DatasetRouter.delete(
    "/delete",
    summary="删除数据集",
    description="批量删除数据集，可选择是否同时删除存储文件",
    dependencies=[Depends(RateLimiter(times=10, seconds=10))]  # 删除操作限制
)
async def delete_dataset_controller(
    ids: list[int] = Body(..., description="数据集ID列表"),
    delete_file: bool = Body(False, description="是否同时删除存储文件"),
    auth: AuthSchema = Depends(AuthPermission(["module_dataset:dataset:delete"]))
) -> JSONResponse:
    """
    删除数据集

    参数:
    - ids (list[int]): 数据集ID列表
    - delete_file (bool): 是否同时删除存储文件(默认False)
    - auth (AuthSchema): 认证信息

    返回:
    - JSONResponse: 删除结果
    """
    await DatasetService.delete_service(auth=auth, ids=ids, delete_file=delete_file)
    log.info(f"删除数据集成功: ids={ids}, delete_file={delete_file}")
    return SuccessResponse(msg="删除数据集成功")


@DatasetRouter.get(
    "/statistics",
    summary="数据集统计",
    description="获取数据集统计信息（总数、上传状态、文件大小、模态分布等）",
    dependencies=[Depends(RateLimiter(times=30, seconds=10))]  # 常规查询限制
)
async def get_dataset_statistics_controller(
    auth: AuthSchema = Depends(AuthPermission(["module_dataset:dataset:statistics"]))
) -> JSONResponse:
    """
    获取数据集统计信息

    参数:
    - auth (AuthSchema): 认证信息

    返回:
    - JSONResponse: 统计信息
      - total_count: 总数据集数量
      - completed_count: 上传完成数量
      - uploading_count: 上传中数量
      - failed_count: 失败数量
      - total_size: 总文件大小(字节)
      - modality_stats: 按模态类型统计
    """
    result = await DatasetService.statistics_service(auth=auth)
    log.info("获取数据集统计信息成功")
    return SuccessResponse(data=result, msg="获取统计信息成功")


# ==================== 数据集分析 API ====================

@DatasetRouter.post(
    "/analyze/{id}",
    summary="启动数据集分析",
    description="启动数据集自动分析任务（基础版本）",
    dependencies=[Depends(RateLimiter(times=10, seconds=10))]  # 分析操作限制
)
async def analyze_dataset_controller(
    id: int = Path(..., description="数据集ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_dataset:dataset:analyze"]))
) -> JSONResponse:
    """
    启动数据集分析（基础版本）

    功能：
    - 检测数据模态类型（基于文件扩展名）
    - 统计样本数量（基于压缩包内文件数）
    - 提取基础元数据

    注：完整的分析功能（特征提取、质量评估等）将在后续版本实现

    参数:
    - id (int): 数据集ID
    - auth (AuthSchema): 认证信息

    返回:
    - JSONResponse: 分析任务信息
    """
    from .crud import DatasetCRUD
    from .model import DatasetModalityEnum
    from pathlib import Path
    import zipfile
    import tarfile

    # 获取数据集
    dataset = await DatasetCRUD(auth).get_by_id_crud(id=id)
    if not dataset:
        return SuccessResponse(code=404, msg="数据集不存在")

    try:
        storage_path = Path(dataset.storage_path)

        if not storage_path.exists():
            return SuccessResponse(code=404, msg="数据集文件不存在")

        # 基础分析：识别模态类型
        modality = DatasetModalityEnum.UNKNOWN.value
        sample_count = 0

        # 尝试解压并分析
        if storage_path.suffix == '.zip':
            with zipfile.ZipFile(storage_path, 'r') as zf:
                file_list = zf.namelist()
                sample_count = len([f for f in file_list if not f.endswith('/')])

                # 简单的模态识别
                extensions = set([Path(f).suffix.lower() for f in file_list])
                if any(ext in extensions for ext in ['.jpg', '.jpeg', '.png', '.bmp']):
                    modality = DatasetModalityEnum.IMAGE.value
                elif any(ext in extensions for ext in ['.wav', '.mp3', '.flac']):
                    modality = DatasetModalityEnum.AUDIO.value
                elif any(ext in extensions for ext in ['.mp4', '.avi', '.mov']):
                    modality = DatasetModalityEnum.VIDEO.value
                elif any(ext in extensions for ext in ['.txt', '.json', '.csv']):
                    modality = DatasetModalityEnum.TEXT.value

        elif storage_path.suffix in ['.tar', '.gz']:
            with tarfile.open(storage_path, 'r') as tf:
                file_list = tf.getnames()
                sample_count = len([f for f in file_list if not f.endswith('/')])

                extensions = set([Path(f).suffix.lower() for f in file_list])
                if any(ext in extensions for ext in ['.jpg', '.jpeg', '.png', '.bmp']):
                    modality = DatasetModalityEnum.IMAGE.value

        # 更新数据集信息
        await DatasetCRUD(auth).update_analysis_result(
            id=id,
            modality=modality,
            sample_count=sample_count,
            analysis_result={
                "status": "completed",
                "modality": modality,
                "sample_count": sample_count,
                "analyzed_at": str(Path(storage_path).stat().st_mtime)
            }
        )

        await auth.db.commit()

        result = {
            "dataset_id": id,
            "modality": modality,
            "sample_count": sample_count,
            "status": "completed",
            "message": "基础分析完成"
        }

        log.info(f"数据集分析完成: id={id}, modality={modality}, samples={sample_count}")
        return SuccessResponse(data=result, msg="分析完成")

    except Exception as e:
        log.error(f"数据集分析失败: {str(e)}")
        return SuccessResponse(code=500, msg=f"分析失败: {str(e)}")


@DatasetRouter.get(
    "/analyze/status/{id}",
    summary="查询分析状态",
    description="查询数据集分析任务状态"
)
async def get_analyze_status_controller(
    id: int = Path(..., description="数据集ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_dataset:dataset:analyze"]))
) -> JSONResponse:
    """
    查询分析状态

    参数:
    - id (int): 数据集ID
    - auth (AuthSchema): 认证信息

    返回:
    - JSONResponse: 分析状态信息
    """
    from .crud import DatasetCRUD
    import json

    dataset = await DatasetCRUD(auth).get_by_id_crud(id=id)
    if not dataset:
        return SuccessResponse(code=404, msg="数据集不存在")

    # 解析分析结果
    analysis_result = {}
    if dataset.analysis_result:
        try:
            analysis_result = json.loads(dataset.analysis_result)
        except:
            analysis_result = {}

    result = {
        "dataset_id": id,
        "modality": dataset.modality,
        "sample_count": dataset.sample_count,
        "class_count": dataset.class_count,
        "analysis_result": analysis_result,
        "status": analysis_result.get("status", "not_started")
    }

    log.info(f"查询分析状态成功: id={id}")
    return SuccessResponse(data=result, msg="查询成功")


# ==================== 数据集预览 API ====================

@DatasetRouter.get(
    "/preview/{id}",
    summary="数据集预览",
    description="获取数据集前N个样本的预览信息"
)
async def preview_dataset_controller(
    id: int = Path(..., description="数据集ID"),
    limit: int = Query(5, ge=1, le=20, description="预览样本数量"),
    auth: AuthSchema = Depends(AuthPermission(["module_dataset:dataset:preview"]))
) -> JSONResponse:
    """
    数据集预览（基础版本）

    功能：
    - 返回数据集中前N个文件的文件名
    - 返回文件大小、格式等基础信息

    注：完整的预览功能（图像缩略图、音频波形等）将在后续版本实现

    参数:
    - id (int): 数据集ID
    - limit (int): 预览样本数量(1-20)
    - auth (AuthSchema): 认证信息

    返回:
    - JSONResponse: 预览信息
    """
    from .crud import DatasetCRUD
    from pathlib import Path
    import zipfile

    dataset = await DatasetCRUD(auth).get_by_id_crud(id=id)
    if not dataset:
        return SuccessResponse(code=404, msg="数据集不存在")

    try:
        storage_path = Path(dataset.storage_path)

        if not storage_path.exists():
            return SuccessResponse(code=404, msg="数据集文件不存在")

        preview_items = []

        # 获取前N个文件的信息
        if storage_path.suffix == '.zip':
            with zipfile.ZipFile(storage_path, 'r') as zf:
                file_list = [f for f in zf.namelist() if not f.endswith('/')][:limit]

                for file_name in file_list:
                    file_info = zf.getinfo(file_name)
                    preview_items.append({
                        "filename": file_name,
                        "size": file_info.file_size,
                        "compressed_size": file_info.compress_size,
                        "extension": Path(file_name).suffix
                    })

        result = {
            "dataset_id": id,
            "total_previewed": len(preview_items),
            "items": preview_items
        }

        log.info(f"数据集预览成功: id={id}, count={len(preview_items)}")
        return SuccessResponse(data=result, msg="预览成功")

    except Exception as e:
        log.error(f"数据集预览失败: {str(e)}")
        return SuccessResponse(code=500, msg=f"预览失败: {str(e)}")

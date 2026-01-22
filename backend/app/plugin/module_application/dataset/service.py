# -*- coding: utf-8 -*-

import os
import hashlib
import shutil
import json
from pathlib import Path
from typing import BinaryIO
from fastapi import UploadFile

from app.core.exceptions import CustomException
from app.core.logger import log
from app.config.setting import settings
from app.utils.common_util import uuid4_str, bytes2human
from app.api.v1.module_system.auth.schema import AuthSchema

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
    DatasetOutSchema,
    DatasetQueryParam,
    ChunkInfo
)
from .crud import DatasetCRUD, DatasetChunkCRUD
from .model import UploadStatusEnum, DatasetModalityEnum


class StorageService:
    """存储管理服务"""

    # 数据集存储根目录 - 修改为 static/dataset/uploads
    DATASET_ROOT = Path(settings.BASE_DIR) / "static" / "dataset" / "uploads"
    # 临时文件目录
    TEMP_ROOT = Path(settings.BASE_DIR) / "storage" / "temp"
    # 分片文件目录
    CHUNK_ROOT = Path(settings.BASE_DIR) / "storage" / "chunks"

    @classmethod
    def ensure_directories(cls) -> None:
        """确保存储目录存在"""
        try:
            cls.DATASET_ROOT.mkdir(parents=True, exist_ok=True)
            cls.TEMP_ROOT.mkdir(parents=True, exist_ok=True)
            cls.CHUNK_ROOT.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            log.error(f"创建存储目录失败: {str(e)}")
            raise CustomException(msg=f"创建存储目录失败: {str(e)}")

    @classmethod
    def get_dataset_path(cls, file_hash: str, filename: str) -> Path:
        """
        获取数据集存储路径

        参数:
        - file_hash (str): 文件哈希值
        - filename (str): 文件名

        返回:
        - Path: 数据集文件路径
        """
        # 使用哈希值的前2位作为子目录，避免单目录文件过多
        subdir = file_hash[:2]
        dataset_dir = cls.DATASET_ROOT / subdir
        dataset_dir.mkdir(parents=True, exist_ok=True)
        return dataset_dir / f"{file_hash}_{filename}"

    @classmethod
    def get_chunk_path(cls, upload_id: str, chunk_index: int) -> Path:
        """
        获取分片存储路径

        参数:
        - upload_id (str): 上传会话ID
        - chunk_index (int): 分片索引

        返回:
        - Path: 分片文件路径
        """
        chunk_dir = cls.CHUNK_ROOT / upload_id
        chunk_dir.mkdir(parents=True, exist_ok=True)
        return chunk_dir / f"chunk_{chunk_index}"

    @classmethod
    def get_temp_path(cls, upload_id: str, filename: str) -> Path:
        """
        获取临时文件路径

        参数:
        - upload_id (str): 上传会话ID
        - filename (str): 文件名

        返回:
        - Path: 临时文件路径
        """
        temp_dir = cls.TEMP_ROOT / upload_id
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir / filename

    @classmethod
    def delete_directory(cls, directory: Path) -> None:
        """
        删除目录及其内容

        参数:
        - directory (Path): 目录路径
        """
        try:
            if directory.exists() and directory.is_dir():
                shutil.rmtree(directory)
                log.info(f"已删除目录: {directory}")
        except Exception as e:
            log.error(f"删除目录失败 {directory}: {str(e)}")
            raise CustomException(msg=f"删除目录失败: {str(e)}")

    @classmethod
    def delete_file(cls, file_path: Path) -> None:
        """
        删除文件，并删除空的父目录

        参数:
        - file_path (Path): 文件路径
        """
        try:
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                log.info(f"已删除文件: {file_path}")

                # 删除文件后，检查并删除空的父目录
                parent_dir = file_path.parent
                # 只删除数据集存储目录下的子目录，不删除根目录
                # Python 3.7 兼容：使用字符串路径比较而不是 is_relative_to
                try:
                    parent_str = str(parent_dir.resolve())
                    root_str = str(cls.DATASET_ROOT.resolve())
                    # 检查是否是子目录且不是根目录
                    if parent_dir != cls.DATASET_ROOT and parent_str.startswith(root_str):
                        # 如果目录为空，删除它
                        if not any(parent_dir.iterdir()):
                            parent_dir.rmdir()
                            log.info(f"已删除空目录: {parent_dir}")
                except Exception as e:
                    # 删除空目录失败不应该影响主流程
                    log.warning(f"删除空目录失败 {parent_dir}: {str(e)}")
        except Exception as e:
            log.error(f"删除文件失败 {file_path}: {str(e)}")
            raise CustomException(msg=f"删除文件失败: {str(e)}")

    @classmethod
    def get_file_size(cls, file_path: Path) -> int:
        """
        获取文件大小

        参数:
        - file_path (Path): 文件路径

        返回:
        - int: 文件大小(字节)
        """
        try:
            if file_path.exists() and file_path.is_file():
                return file_path.stat().st_size
            return 0
        except Exception as e:
            log.error(f"获取文件大小失败 {file_path}: {str(e)}")
            return 0


class HashService:
    """哈希验证服务"""

    @staticmethod
    def calculate_file_hash(file_path: Path, algorithm: str = "md5") -> str:
        """
        计算文件哈希值

        参数:
        - file_path (Path): 文件路径
        - algorithm (str): 哈希算法 (md5/sha256)

        返回:
        - str: 文件哈希值

        异常:
        - CustomException: 计算失败时抛出异常
        """
        try:
            if algorithm == "md5":
                hash_obj = hashlib.md5()
            elif algorithm == "sha256":
                hash_obj = hashlib.sha256()
            else:
                raise CustomException(msg=f"不支持的哈希算法: {algorithm}")

            with open(file_path, "rb") as f:
                # 分块读取，避免大文件占用过多内存
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_obj.update(chunk)

            return hash_obj.hexdigest()
        except Exception as e:
            log.error(f"计算文件哈希值失败 {file_path}: {str(e)}")
            raise CustomException(msg=f"计算文件哈希值失败: {str(e)}")

    @staticmethod
    def calculate_chunk_hash(chunk_data: bytes, algorithm: str = "md5") -> str:
        """
        计算分片哈希值

        参数:
        - chunk_data (bytes): 分片数据
        - algorithm (str): 哈希算法 (md5/sha256)

        返回:
        - str: 分片哈希值

        异常:
        - CustomException: 计算失败时抛出异常
        """
        try:
            if algorithm == "md5":
                hash_obj = hashlib.md5()
            elif algorithm == "sha256":
                hash_obj = hashlib.sha256()
            else:
                raise CustomException(msg=f"不支持的哈希算法: {algorithm}")

            hash_obj.update(chunk_data)
            return hash_obj.hexdigest()
        except Exception as e:
            log.error(f"计算分片哈希值失败: {str(e)}")
            raise CustomException(msg=f"计算分片哈希值失败: {str(e)}")

    @staticmethod
    def verify_file_hash(file_path: Path, expected_hash: str, algorithm: str = "md5") -> bool:
        """
        验证文件哈希值

        参数:
        - file_path (Path): 文件路径
        - expected_hash (str): 期望的哈希值
        - algorithm (str): 哈希算法

        返回:
        - bool: 是否匹配
        """
        try:
            actual_hash = HashService.calculate_file_hash(file_path, algorithm)
            return actual_hash.lower() == expected_hash.lower()
        except Exception as e:
            log.error(f"验证文件哈希值失败: {str(e)}")
            return False


class ChunkService:
    """分片处理服务"""

    @staticmethod
    async def save_chunk(
        upload_file: UploadFile,
        chunk_path: Path,
        expected_hash: str | None = None
    ) -> int:
        """
        保存分片文件

        参数:
        - upload_file (UploadFile): 上传的文件对象
        - chunk_path (Path): 分片保存路径
        - expected_hash (str | None): 期望的哈希值（用于校验）

        返回:
        - int: 分片大小(字节)

        异常:
        - CustomException: 保存失败时抛出异常
        """
        try:
            chunk_data = await upload_file.read()
            chunk_size = len(chunk_data)

            # 验证哈希值
            if expected_hash:
                actual_hash = HashService.calculate_chunk_hash(chunk_data)
                if actual_hash.lower() != expected_hash.lower():
                    raise CustomException(msg="分片哈希值校验失败")

            # 保存分片
            with open(chunk_path, "wb") as f:
                f.write(chunk_data)

            log.info(f"分片保存成功: {chunk_path}, 大小: {bytes2human(chunk_size)}")
            return chunk_size

        except CustomException:
            raise
        except Exception as e:
            log.error(f"保存分片失败: {str(e)}")
            raise CustomException(msg=f"保存分片失败: {str(e)}")

    @staticmethod
    async def merge_chunks(
        upload_id: str,
        total_chunks: int,
        output_path: Path,
        verify_hash: str | None = None
    ) -> tuple[bool, int]:
        """
        合并分片文件

        参数:
        - upload_id (str): 上传会话ID
        - total_chunks (int): 总分片数
        - output_path (Path): 输出文件路径
        - verify_hash (str | None): 验证哈希值

        返回:
        - tuple[bool, int]: (是否成功, 文件大小)

        异常:
        - CustomException: 合并失败时抛出异常
        """
        try:
            chunk_dir = StorageService.CHUNK_ROOT / upload_id
            if not chunk_dir.exists():
                raise CustomException(msg="分片目录不存在")

            total_size = 0

            # 合并分片
            with open(output_path, "wb") as output_file:
                for i in range(total_chunks):
                    chunk_path = chunk_dir / f"chunk_{i}"
                    if not chunk_path.exists():
                        raise CustomException(msg=f"分片 {i} 不存在")

                    with open(chunk_path, "rb") as chunk_file:
                        chunk_data = chunk_file.read()
                        output_file.write(chunk_data)
                        total_size += len(chunk_data)

            log.info(f"分片合并完成: {output_path}, 总大小: {bytes2human(total_size)}")

            # 验证文件哈希
            if verify_hash:
                algorithm = "sha256" if len(verify_hash) == 64 else "md5"
                if not HashService.verify_file_hash(output_path, verify_hash, algorithm):
                    # 删除合并失败的文件
                    StorageService.delete_file(output_path)
                    raise CustomException(msg="文件哈希值校验失败")

            # 删除分片目录
            StorageService.delete_directory(chunk_dir)

            return True, total_size

        except CustomException:
            raise
        except Exception as e:
            log.error(f"合并分片失败: {str(e)}")
            raise CustomException(msg=f"合并分片失败: {str(e)}")


class DatasetUploadService:
    """数据集上传服务"""

    @classmethod
    async def upload_init_service(
        cls,
        auth: AuthSchema,
        data: UploadInitRequest
    ) -> UploadInitResponse:
        """
        上传初始化

        参数:
        - auth (AuthSchema): 认证信息
        - data (UploadInitRequest): 初始化请求数据

        返回:
        - UploadInitResponse: 初始化响应数据
        """
        try:
            # 确保存储目录存在
            StorageService.ensure_directories()

            # 检查文件是否已存在（秒传或断点续传）
            existing_dataset = await DatasetCRUD(auth).get_by_file_hash(data.file_hash)

            # 情况 1: 文件已完成上传（秒传）
            if existing_dataset and existing_dataset.upload_status == UploadStatusEnum.COMPLETED.value:
                log.info(f"文件已存在，秒传成功: {data.filename}")
                return UploadInitResponse(
                    upload_id=existing_dataset.upload_id or "",
                    dataset_id=existing_dataset.id,
                    storage_path=existing_dataset.storage_path,
                    total_chunks=0,
                    chunk_size=data.chunk_size,
                    chunks=[],
                    file_exists=True,
                    uploaded_chunks=[]
                )

            # 情况 2: 文件正在上传中（断点续传）
            if existing_dataset and existing_dataset.upload_status == UploadStatusEnum.UPLOADING.value:
                log.info(f"文件上传未完成，支持断点续传: {data.filename}")

                # 获取已上传的分片信息
                chunk_crud = DatasetChunkCRUD(auth)
                existing_chunks = await chunk_crud.get_chunks_by_upload_id(existing_dataset.upload_id)

                # 计算总分片数
                total_chunks = (data.file_size + data.chunk_size - 1) // data.chunk_size

                # 获取已上传的分片索引列表
                uploaded_chunks = [
                    chunk.chunk_index for chunk in existing_chunks if chunk.is_uploaded
                ]

                # 生成分片信息列表
                chunks_info = []
                for chunk in existing_chunks:
                    chunks_info.append({
                        "chunk_index": chunk.chunk_index,
                        "chunk_size": chunk.chunk_size,
                        "is_uploaded": bool(chunk.is_uploaded)
                    })

                return UploadInitResponse(
                    upload_id=existing_dataset.upload_id,
                    dataset_id=existing_dataset.id,
                    storage_path=existing_dataset.storage_path,
                    total_chunks=total_chunks,
                    chunk_size=data.chunk_size,
                    chunks=chunks_info,
                    file_exists=False,
                    uploaded_chunks=uploaded_chunks
                )

            # 生成上传会话ID
            upload_id = f"UPLOAD_{uuid4_str()}"

            # 计算分片信息
            total_chunks = (data.file_size + data.chunk_size - 1) // data.chunk_size

            # 获取存储路径
            storage_path = str(StorageService.get_dataset_path(data.file_hash, data.filename))

            # 创建数据集记录
            dataset_name = data.name or data.filename
            from .schema import DatasetCreateSchema
            dataset_data = DatasetCreateSchema(
                name=dataset_name,
                original_filename=data.filename,
                file_size=data.file_size,
                storage_path=storage_path,
                file_hash=data.file_hash,
                status="0",
                description=f"上传中的数据集: {data.filename}",
                task_type=data.task_type or "classification"  # 添加任务类型
            )

            dataset = await DatasetCRUD(auth).create_crud(data=dataset_data)

            # 更新上传ID和状态
            dataset.upload_id = upload_id
            dataset.upload_status = UploadStatusEnum.UPLOADING.value
            await auth.db.flush()
            await auth.db.refresh(dataset)

            # 创建分片记录
            chunk_crud = DatasetChunkCRUD(auth)
            chunks_info = []

            for i in range(total_chunks):
                chunk_size = data.chunk_size if i < total_chunks - 1 else (
                    data.file_size - i * data.chunk_size
                )
                chunk_path = str(StorageService.get_chunk_path(upload_id, i))

                await chunk_crud.create_chunk(
                    dataset_id=dataset.id,
                    upload_id=upload_id,
                    chunk_index=i,
                    chunk_hash="",  # 上传时再填充
                    chunk_size=chunk_size,
                    chunk_storage_path=chunk_path
                )

                chunks_info.append(ChunkInfo(
                    chunk_index=i,
                    chunk_size=chunk_size,
                    is_uploaded=False
                ))

            # 提交事务
            await auth.db.commit()

            log.info(f"上传初始化成功: {data.filename}, 上传ID: {upload_id}, 分片数: {total_chunks}")

            return UploadInitResponse(
                upload_id=upload_id,
                dataset_id=dataset.id,
                storage_path=storage_path,
                total_chunks=total_chunks,
                chunk_size=data.chunk_size,
                chunks=chunks_info,
                file_exists=False,
                uploaded_chunks=[]
            )

        except CustomException:
            await auth.db.rollback()
            raise
        except Exception as e:
            await auth.db.rollback()
            log.error(f"上传初始化失败: {str(e)}")
            raise CustomException(msg=f"上传初始化失败: {str(e)}")

    @classmethod
    async def chunk_upload_service(
        cls,
        auth: AuthSchema,
        data: ChunkUploadRequest,
        file: UploadFile
    ) -> ChunkUploadResponse:
        """
        分片上传

        参数:
        - auth (AuthSchema): 认证信息
        - data (ChunkUploadRequest): 分片上传请求数据
        - file (UploadFile): 上传的文件

        返回:
        - ChunkUploadResponse: 分片上传响应数据
        """
        try:
            # 查询数据集
            dataset = await DatasetCRUD(auth).get_by_upload_id(data.upload_id)
            if not dataset:
                raise CustomException(msg="上传会话不存在")

            # 查询分片记录
            chunk_crud = DatasetChunkCRUD(auth)
            chunk = await chunk_crud.get_chunk_by_index(dataset.id, data.chunk_index)
            if not chunk:
                raise CustomException(msg=f"分片 {data.chunk_index} 记录不存在")

            # 检查分片是否已上传
            if chunk.is_uploaded:
                log.info(f"分片 {data.chunk_index} 已上传，跳过")
            else:
                # 保存分片
                chunk_path = Path(chunk.chunk_storage_path)
                actual_size = await ChunkService.save_chunk(file, chunk_path, data.chunk_hash)

                # 更新分片记录
                chunk.chunk_hash = data.chunk_hash
                chunk.chunk_size = actual_size
                chunk.is_uploaded = 1
                await auth.db.flush()
                await auth.db.refresh(chunk)

            # 获取上传进度
            progress_info = await chunk_crud.get_upload_progress(dataset.id)

            await auth.db.commit()

            log.info(f"分片上传成功: {data.chunk_index}, 进度: {progress_info['progress']:.2%}")

            return ChunkUploadResponse(
                upload_id=data.upload_id,
                chunk_index=data.chunk_index,
                chunk_uploaded=True,
                progress=progress_info['progress'],
                uploaded_chunks=progress_info['uploaded_chunks'],
                total_chunks=progress_info['total_chunks']
            )

        except CustomException:
            await auth.db.rollback()
            raise
        except Exception as e:
            await auth.db.rollback()
            log.error(f"分片上传失败: {str(e)}")
            raise CustomException(msg=f"分片上传失败: {str(e)}")

    @classmethod
    async def upload_complete_service(
        cls,
        auth: AuthSchema,
        data: UploadCompleteRequest
    ) -> UploadCompleteResponse:
        """
        上传完成

        参数:
        - auth (AuthSchema): 认证信息
        - data (UploadCompleteRequest): 上传完成请求数据

        返回:
        - UploadCompleteResponse: 上传完成响应数据
        """
        try:
            # 查询数据集
            dataset = await DatasetCRUD(auth).get_by_upload_id(data.upload_id)
            if not dataset:
                raise CustomException(msg="上传会话不存在")

            # 验证所有分片是否已上传
            chunk_crud = DatasetChunkCRUD(auth)
            all_uploaded = await chunk_crud.verify_all_chunks_uploaded(dataset.id)
            if not all_uploaded:
                raise CustomException(msg="存在未上传的分片")

            # 获取分片列表
            chunks = await chunk_crud.get_chunks_by_dataset_id(dataset.id)
            total_chunks = len(chunks)

            # 合并分片
            output_path = Path(dataset.storage_path)
            verify_hash = dataset.file_hash if data.verify_hash else None

            merge_success, file_size = await ChunkService.merge_chunks(
                upload_id=data.upload_id,
                total_chunks=total_chunks,
                output_path=output_path,
                verify_hash=verify_hash
            )

            # 更新数据集状态
            dataset.upload_status = UploadStatusEnum.COMPLETED.value
            dataset.file_size = file_size
            await auth.db.flush()
            await auth.db.refresh(dataset)

            await auth.db.commit()

            log.info(f"上传完成: {dataset.name}, 文件大小: {bytes2human(file_size)}")

            return UploadCompleteResponse(
                dataset_id=dataset.id,
                upload_id=data.upload_id,
                storage_path=dataset.storage_path,
                file_size=file_size,
                file_hash=dataset.file_hash,
                hash_verified=data.verify_hash,
                merge_success=merge_success,
                message="上传完成"
            )

        except CustomException:
            await auth.db.rollback()
            # 更新状态为失败
            try:
                dataset = await DatasetCRUD(auth).get_by_upload_id(data.upload_id)
                if dataset:
                    dataset.upload_status = UploadStatusEnum.FAILED.value
                    await auth.db.commit()
            except:
                pass
            raise
        except Exception as e:
            await auth.db.rollback()
            log.error(f"上传完成处理失败: {str(e)}")
            raise CustomException(msg=f"上传完成处理失败: {str(e)}")

    @classmethod
    async def resume_upload_service(
        cls,
        auth: AuthSchema,
        data: ResumeUploadRequest
    ) -> ResumeUploadResponse:
        """
        断点续传查询

        参数:
        - auth (AuthSchema): 认证信息
        - data (ResumeUploadRequest): 断点续传请求数据

        返回:
        - ResumeUploadResponse: 断点续传响应数据
        """
        try:
            # 查询数据集
            dataset = await DatasetCRUD(auth).get_by_file_hash(data.file_hash)

            if not dataset:
                return ResumeUploadResponse(
                    can_resume=False,
                    upload_id=None,
                    uploaded_chunks=[],
                    total_chunks=None,
                    progress=0.0,
                    file_exists=False,
                    dataset_id=None
                )

            # 文件已完整上传
            if dataset.upload_status == UploadStatusEnum.COMPLETED.value:
                return ResumeUploadResponse(
                    can_resume=False,
                    upload_id=dataset.upload_id,
                    uploaded_chunks=[],
                    total_chunks=0,
                    progress=1.0,
                    file_exists=True,
                    dataset_id=dataset.id
                )

            # 上传中，支持断点续传
            if dataset.upload_status == UploadStatusEnum.UPLOADING.value:
                chunk_crud = DatasetChunkCRUD(auth)
                progress_info = await chunk_crud.get_upload_progress(dataset.id)

                # 获取已上传分片的索引列表
                uploaded_chunks = await chunk_crud.get_uploaded_chunks(dataset.id)
                uploaded_indices = [chunk.chunk_index for chunk in uploaded_chunks]

                return ResumeUploadResponse(
                    can_resume=True,
                    upload_id=dataset.upload_id,
                    uploaded_chunks=uploaded_indices,
                    total_chunks=progress_info['total_chunks'],
                    progress=progress_info['progress'],
                    file_exists=False,
                    dataset_id=dataset.id
                )

            # 其他状态（失败、取消等）
            return ResumeUploadResponse(
                can_resume=False,
                upload_id=dataset.upload_id,
                uploaded_chunks=[],
                total_chunks=None,
                progress=0.0,
                file_exists=False,
                dataset_id=dataset.id
            )

        except Exception as e:
            log.error(f"断点续传查询失败: {str(e)}")
            raise CustomException(msg=f"断点续传查询失败: {str(e)}")


class DatasetService:
    """数据集管理服务"""

    @classmethod
    async def detail_service(cls, auth: AuthSchema, id: int) -> dict:
        """
        数据集详情

        参数:
        - auth (AuthSchema): 认证信息
        - id (int): 数据集ID

        返回:
        - dict: 数据集详情
        """
        dataset = await DatasetCRUD(auth).get_by_id_crud(id=id, preload=['chunks'])
        if not dataset:
            raise CustomException(msg="数据集不存在")
        return DatasetOutSchema.model_validate(dataset).model_dump()

    @classmethod
    async def list_service(
        cls,
        auth: AuthSchema,
        search: DatasetQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None
    ) -> list[dict]:
        """
        数据集列表查询

        参数:
        - auth (AuthSchema): 认证信息
        - search (DatasetQueryParam | None): 查询参数
        - order_by (list[dict[str, str]] | None): 排序参数

        返回:
        - list[dict]: 数据集列表
        """
        search_dict = search.__dict__ if search else None
        dataset_list = await DatasetCRUD(auth).list_crud(search=search_dict, order_by=order_by)
        return [DatasetOutSchema.model_validate(dataset).model_dump() for dataset in dataset_list]

    @classmethod
    async def page_service(
        cls,
        auth: AuthSchema,
        page_no: int,
        page_size: int,
        search: DatasetQueryParam | None = None,
        order_by: list[dict[str, str]] | None = None
    ) -> dict:
        """
        数据集分页查询

        参数:
        - auth (AuthSchema): 认证信息
        - page_no (int): 页码
        - page_size (int): 每页数量
        - search (DatasetQueryParam | None): 查询参数
        - order_by (list[dict[str, str]] | None): 排序参数

        返回:
        - dict: 分页数据
        """
        search_dict = search.__dict__ if search else {}
        order_by_list = order_by or [{'created_time': 'desc'}]
        offset = (page_no - 1) * page_size

        result = await DatasetCRUD(auth).page_crud(
            offset=offset,
            limit=page_size,
            order_by=order_by_list,
            search=search_dict
        )
        return result

    @classmethod
    async def update_service(cls, auth: AuthSchema, id: int, data: DatasetUpdateSchema) -> dict:
        """
        更新数据集

        参数:
        - auth (AuthSchema): 认证信息
        - id (int): 数据集ID
        - data (DatasetUpdateSchema): 更新数据

        返回:
        - dict: 更新后的数据集
        """
        dataset = await DatasetCRUD(auth).get_by_id_crud(id=id)
        if not dataset:
            raise CustomException(msg="数据集不存在")

        updated_dataset = await DatasetCRUD(auth).update_crud(id=id, data=data)
        return DatasetOutSchema.model_validate(updated_dataset).model_dump()

    @classmethod
    async def delete_service(cls, auth: AuthSchema, ids: list[int], delete_file: bool = False) -> None:
        """
        删除数据集

        参数:
        - auth (AuthSchema): 认证信息
        - ids (list[int]): 数据集ID列表
        - delete_file (bool): 是否删除存储文件
        """
        if len(ids) < 1:
            raise CustomException(msg="删除对象不能为空")

        # 检查并删除文件
        if delete_file:
            for id in ids:
                dataset = await DatasetCRUD(auth).get_by_id_crud(id=id)
                if dataset and dataset.storage_path:
                    storage_path = Path(dataset.storage_path)
                    StorageService.delete_file(storage_path)

        # 删除数据库记录（分片记录会级联删除）
        await DatasetCRUD(auth).delete_crud(ids=ids)

    @classmethod
    async def statistics_service(cls, auth: AuthSchema) -> dict:
        """
        获取数据集统计信息

        参数:
        - auth (AuthSchema): 认证信息

        返回:
        - dict: 统计信息
        """
        stats = await DatasetCRUD(auth).get_statistics()
        return stats

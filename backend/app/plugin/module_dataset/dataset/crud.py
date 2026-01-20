# -*- coding: utf-8 -*-

from collections.abc import Sequence
from typing import Optional
from sqlalchemy import select, func, and_, or_
from sqlalchemy.engine import Result

from app.core.base_crud import CRUDBase
from app.core.exceptions import CustomException
from app.api.v1.module_system.auth.schema import AuthSchema

from .model import DatasetModel, DatasetChunkModel, UploadStatusEnum
from .schema import (
    DatasetCreateSchema,
    DatasetUpdateSchema,
    DatasetOutSchema,
    DatasetDetailOutSchema
)


class DatasetCRUD(CRUDBase[DatasetModel, DatasetCreateSchema, DatasetUpdateSchema]):
    """数据集数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        """
        初始化数据集CRUD数据层

        参数:
        - auth (AuthSchema): 认证信息模型
        """
        super().__init__(model=DatasetModel, auth=auth)

    # ==================== 基础 CRUD 操作 ====================

    async def get_by_id_crud(self, id: int, preload: list[str] | None = None) -> DatasetModel | None:
        """
        根据ID获取数据集详情

        参数:
        - id (int): 数据集ID
        - preload (list[str] | None): 预加载关系，未提供时使用模型默认项

        返回:
        - DatasetModel | None: 数据集模型实例或None
        """
        return await self.get(id=id, preload=preload)

    async def list_crud(
        self,
        search: dict | None = None,
        order_by: list[dict] | None = None,
        preload: list[str] | None = None
    ) -> Sequence[DatasetModel]:
        """
        获取数据集列表

        参数:
        - search (dict | None): 查询参数
        - order_by (list[dict] | None): 排序参数
        - preload (list[str] | None): 预加载关系，未提供时使用模型默认项

        返回:
        - Sequence[DatasetModel]: 数据集模型实例序列
        """
        return await self.list(search=search, order_by=order_by, preload=preload)

    async def create_crud(self, data: DatasetCreateSchema) -> DatasetModel | None:
        """
        创建数据集

        参数:
        - data (DatasetCreateSchema): 数据集创建模型

        返回:
        - DatasetModel | None: 数据集模型实例或None
        """
        return await self.create(data=data)

    async def update_crud(self, id: int, data: DatasetUpdateSchema) -> DatasetModel | None:
        """
        更新数据集

        参数:
        - id (int): 数据集ID
        - data (DatasetUpdateSchema): 数据集更新模型

        返回:
        - DatasetModel | None: 数据集模型实例或None
        """
        return await self.update(id=id, data=data)

    async def delete_crud(self, ids: list[int]) -> None:
        """
        批量删除数据集

        参数:
        - ids (list[int]): 数据集ID列表

        返回:
        - None
        """
        return await self.delete(ids=ids)

    async def set_available_crud(self, ids: list[int], status: str) -> None:
        """
        批量设置数据集可用状态

        参数:
        - ids (list[int]): 数据集ID列表
        - status (str): 可用状态(0:启用 1:禁用)

        返回:
        - None
        """
        return await self.set(ids=ids, status=status)

    async def page_crud(
        self,
        offset: int,
        limit: int,
        order_by: list[dict] | None = None,
        search: dict | None = None,
        preload: list | None = None
    ) -> dict:
        """
        数据集分页查询

        参数:
        - offset (int): 偏移量
        - limit (int): 每页数量
        - order_by (list[dict] | None): 排序参数
        - search (dict | None): 查询参数
        - preload (list | None): 预加载关系，未提供时使用模型默认项

        返回:
        - dict: 分页数据
        """
        order_by_list = order_by or [{'created_time': 'desc'}]
        search_dict = search or {}

        return await self.page(
            offset=offset,
            limit=limit,
            order_by=order_by_list,
            search=search_dict,
            out_schema=DatasetOutSchema,
            preload=preload
        )

    # ==================== 扩展查询方法 ====================

    async def get_by_file_hash(self, file_hash: str) -> DatasetModel | None:
        """
        根据文件哈希值查询数据集

        参数:
        - file_hash (str): 文件哈希值

        返回:
        - DatasetModel | None: 数据集模型实例或None

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            return await self.get(file_hash=file_hash)
        except Exception as e:
            raise CustomException(msg=f"根据文件哈希查询失败: {str(e)}")

    async def get_by_upload_id(self, upload_id: str) -> DatasetModel | None:
        """
        根据上传ID查询数据集

        参数:
        - upload_id (str): 上传会话ID

        返回:
        - DatasetModel | None: 数据集模型实例或None

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            return await self.get(upload_id=upload_id, preload=['chunks'])
        except Exception as e:
            raise CustomException(msg=f"根据上传ID查询失败: {str(e)}")

    async def get_uploading_datasets(self) -> Sequence[DatasetModel]:
        """
        获取所有上传中的数据集

        返回:
        - Sequence[DatasetModel]: 上传中的数据集列表

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            search = {"upload_status": ("eq", UploadStatusEnum.UPLOADING.value)}
            return await self.list(search=search, order_by=[{'created_time': 'desc'}])
        except Exception as e:
            raise CustomException(msg=f"查询上传中的数据集失败: {str(e)}")

    async def get_completed_datasets(self) -> Sequence[DatasetModel]:
        """
        获取所有上传完成的数据集

        返回:
        - Sequence[DatasetModel]: 上传完成的数据集列表

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            search = {"upload_status": ("eq", UploadStatusEnum.COMPLETED.value)}
            return await self.list(search=search, order_by=[{'created_time': 'desc'}])
        except Exception as e:
            raise CustomException(msg=f"查询已完成的数据集失败: {str(e)}")

    async def get_datasets_by_modality(self, modality: str) -> Sequence[DatasetModel]:
        """
        根据数据模态类型查询数据集

        参数:
        - modality (str): 数据模态类型

        返回:
        - Sequence[DatasetModel]: 数据集列表

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            search = {"modality": ("eq", modality)}
            return await self.list(search=search, order_by=[{'created_time': 'desc'}])
        except Exception as e:
            raise CustomException(msg=f"根据模态类型查询数据集失败: {str(e)}")

    async def update_upload_status(self, id: int, status: str) -> DatasetModel | None:
        """
        更新数据集上传状态

        参数:
        - id (int): 数据集ID
        - status (str): 上传状态

        返回:
        - DatasetModel | None: 更新后的数据集模型实例

        异常:
        - CustomException: 更新失败时抛出异常
        """
        try:
            dataset = await self.get(id=id)
            if not dataset:
                raise CustomException(msg="数据集不存在")

            dataset.upload_status = status
            await self.auth.db.flush()
            await self.auth.db.refresh(dataset)
            return dataset
        except Exception as e:
            raise CustomException(msg=f"更新上传状态失败: {str(e)}")

    async def update_analysis_result(
        self,
        id: int,
        modality: str | None = None,
        sample_count: int | None = None,
        class_count: int | None = None,
        dataset_metadata: dict | None = None,
        analysis_result: dict | None = None
    ) -> DatasetModel | None:
        """
        更新数据集分析结果

        参数:
        - id (int): 数据集ID
        - modality (str | None): 数据模态类型
        - sample_count (int | None): 样本数量
        - class_count (int | None): 类别数量
        - dataset_metadata (dict | None): 元数据
        - analysis_result (dict | None): 分析结果

        返回:
        - DatasetModel | None: 更新后的数据集模型实例

        异常:
        - CustomException: 更新失败时抛出异常
        """
        try:
            dataset = await self.get(id=id)
            if not dataset:
                raise CustomException(msg="数据集不存在")

            if modality is not None:
                dataset.modality = modality
            if sample_count is not None:
                dataset.sample_count = sample_count
            if class_count is not None:
                dataset.class_count = class_count
            if dataset_metadata is not None:
                import json
                dataset.dataset_metadata = json.dumps(dataset_metadata, ensure_ascii=False)
            if analysis_result is not None:
                import json
                dataset.analysis_result = json.dumps(analysis_result, ensure_ascii=False)

            await self.auth.db.flush()
            await self.auth.db.refresh(dataset)
            return dataset
        except Exception as e:
            raise CustomException(msg=f"更新分析结果失败: {str(e)}")

    async def get_statistics(self) -> dict:
        """
        获取数据集统计信息

        返回:
        - dict: 统计信息字典

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            # 总数据集数量
            total_count_sql = select(func.count(DatasetModel.id))
            total_result = await self.auth.db.execute(total_count_sql)
            total_count = total_result.scalar() or 0

            # 上传完成数量
            completed_count_sql = select(func.count(DatasetModel.id)).where(
                DatasetModel.upload_status == UploadStatusEnum.COMPLETED.value
            )
            completed_result = await self.auth.db.execute(completed_count_sql)
            completed_count = completed_result.scalar() or 0

            # 上传中数量
            uploading_count_sql = select(func.count(DatasetModel.id)).where(
                DatasetModel.upload_status == UploadStatusEnum.UPLOADING.value
            )
            uploading_result = await self.auth.db.execute(uploading_count_sql)
            uploading_count = uploading_result.scalar() or 0

            # 总文件大小
            total_size_sql = select(func.sum(DatasetModel.file_size)).where(
                DatasetModel.upload_status == UploadStatusEnum.COMPLETED.value
            )
            size_result = await self.auth.db.execute(total_size_sql)
            total_size = size_result.scalar()
            # 转换 Decimal 为 int，避免 JSON 序列化错误
            total_size = int(total_size) if total_size is not None else 0

            # 按模态类型统计
            modality_count_sql = select(
                DatasetModel.modality,
                func.count(DatasetModel.id)
            ).group_by(DatasetModel.modality)
            modality_result = await self.auth.db.execute(modality_count_sql)
            modality_stats = {row[0]: row[1] for row in modality_result.all()}

            return {
                "total_count": total_count,
                "completed_count": completed_count,
                "uploading_count": uploading_count,
                "failed_count": total_count - completed_count - uploading_count,
                "total_size": total_size,
                "modality_stats": modality_stats
            }
        except Exception as e:
            raise CustomException(msg=f"获取统计信息失败: {str(e)}")


class DatasetChunkCRUD(CRUDBase[DatasetChunkModel, dict, dict]):
    """数据集分片数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        """
        初始化数据集分片CRUD数据层

        参数:
        - auth (AuthSchema): 认证信息模型
        """
        super().__init__(model=DatasetChunkModel, auth=auth)

    # ==================== 基础 CRUD 操作 ====================

    async def get_by_id_crud(self, id: int) -> DatasetChunkModel | None:
        """
        根据ID获取分片详情

        参数:
        - id (int): 分片ID

        返回:
        - DatasetChunkModel | None: 分片模型实例或None
        """
        return await self.get(id=id)

    async def create_chunk(
        self,
        dataset_id: int,
        upload_id: str,
        chunk_index: int,
        chunk_hash: str,
        chunk_size: int,
        chunk_storage_path: str
    ) -> DatasetChunkModel:
        """
        创建分片记录

        参数:
        - dataset_id (int): 数据集ID
        - upload_id (str): 上传会话ID
        - chunk_index (int): 分片索引
        - chunk_hash (str): 分片哈希值
        - chunk_size (int): 分片大小
        - chunk_storage_path (str): 分片存储路径

        返回:
        - DatasetChunkModel: 分片模型实例

        异常:
        - CustomException: 创建失败时抛出异常
        """
        try:
            chunk_data = {
                "dataset_id": dataset_id,
                "upload_id": upload_id,
                "chunk_index": chunk_index,
                "chunk_hash": chunk_hash,
                "chunk_size": chunk_size,
                "chunk_storage_path": chunk_storage_path,
                "is_uploaded": 0
            }
            return await self.create(data=chunk_data)
        except Exception as e:
            raise CustomException(msg=f"创建分片记录失败: {str(e)}")

    async def delete_chunks_by_dataset_id(self, dataset_id: int) -> None:
        """
        删除数据集的所有分片

        参数:
        - dataset_id (int): 数据集ID

        异常:
        - CustomException: 删除失败时抛出异常
        """
        try:
            chunks = await self.get_chunks_by_dataset_id(dataset_id)
            chunk_ids = [chunk.id for chunk in chunks]
            if chunk_ids:
                await self.delete(ids=chunk_ids)
        except Exception as e:
            raise CustomException(msg=f"删除分片失败: {str(e)}")

    # ==================== 扩展查询方法 ====================

    async def get_chunks_by_dataset_id(self, dataset_id: int) -> Sequence[DatasetChunkModel]:
        """
        获取数据集的所有分片

        参数:
        - dataset_id (int): 数据集ID

        返回:
        - Sequence[DatasetChunkModel]: 分片列表

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            search = {"dataset_id": ("eq", dataset_id)}
            return await self.list(search=search, order_by=[{'chunk_index': 'asc'}])
        except Exception as e:
            raise CustomException(msg=f"获取数据集分片失败: {str(e)}")

    async def get_chunks_by_upload_id(self, upload_id: str) -> Sequence[DatasetChunkModel]:
        """
        根据上传ID获取所有分片

        参数:
        - upload_id (str): 上传会话ID

        返回:
        - Sequence[DatasetChunkModel]: 分片列表

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            search = {"upload_id": ("eq", upload_id)}
            return await self.list(search=search, order_by=[{'chunk_index': 'asc'}])
        except Exception as e:
            raise CustomException(msg=f"根据上传ID获取分片失败: {str(e)}")

    async def get_chunk_by_index(
        self,
        dataset_id: int,
        chunk_index: int
    ) -> DatasetChunkModel | None:
        """
        根据数据集ID和分片索引获取分片

        参数:
        - dataset_id (int): 数据集ID
        - chunk_index (int): 分片索引

        返回:
        - DatasetChunkModel | None: 分片模型实例或None

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            return await self.get(dataset_id=dataset_id, chunk_index=chunk_index)
        except Exception as e:
            raise CustomException(msg=f"获取分片失败: {str(e)}")

    async def get_uploaded_chunks(self, dataset_id: int) -> Sequence[DatasetChunkModel]:
        """
        获取已上传的分片列表

        参数:
        - dataset_id (int): 数据集ID

        返回:
        - Sequence[DatasetChunkModel]: 已上传的分片列表

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            sql = select(DatasetChunkModel).where(
                and_(
                    DatasetChunkModel.dataset_id == dataset_id,
                    DatasetChunkModel.is_uploaded == 1
                )
            ).order_by(DatasetChunkModel.chunk_index.asc())

            result: Result = await self.auth.db.execute(sql)
            return result.scalars().all()
        except Exception as e:
            raise CustomException(msg=f"获取已上传分片失败: {str(e)}")

    async def get_unuploaded_chunks(self, dataset_id: int) -> Sequence[DatasetChunkModel]:
        """
        获取未上传的分片列表

        参数:
        - dataset_id (int): 数据集ID

        返回:
        - Sequence[DatasetChunkModel]: 未上传的分片列表

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            sql = select(DatasetChunkModel).where(
                and_(
                    DatasetChunkModel.dataset_id == dataset_id,
                    DatasetChunkModel.is_uploaded == 0
                )
            ).order_by(DatasetChunkModel.chunk_index.asc())

            result: Result = await self.auth.db.execute(sql)
            return result.scalars().all()
        except Exception as e:
            raise CustomException(msg=f"获取未上传分片失败: {str(e)}")

    async def mark_chunk_uploaded(self, chunk_id: int) -> DatasetChunkModel | None:
        """
        标记分片为已上传

        参数:
        - chunk_id (int): 分片ID

        返回:
        - DatasetChunkModel | None: 更新后的分片模型实例

        异常:
        - CustomException: 更新失败时抛出异常
        """
        try:
            chunk = await self.get(id=chunk_id)
            if not chunk:
                raise CustomException(msg="分片不存在")

            chunk.is_uploaded = 1
            await self.auth.db.flush()
            await self.auth.db.refresh(chunk)
            return chunk
        except Exception as e:
            raise CustomException(msg=f"标记分片已上传失败: {str(e)}")

    async def get_upload_progress(self, dataset_id: int) -> dict:
        """
        获取上传进度

        参数:
        - dataset_id (int): 数据集ID

        返回:
        - dict: 上传进度信息

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            # 总分片数
            total_sql = select(func.count(DatasetChunkModel.id)).where(
                DatasetChunkModel.dataset_id == dataset_id
            )
            total_result = await self.auth.db.execute(total_sql)
            total_chunks = total_result.scalar() or 0

            # 已上传分片数
            uploaded_sql = select(func.count(DatasetChunkModel.id)).where(
                and_(
                    DatasetChunkModel.dataset_id == dataset_id,
                    DatasetChunkModel.is_uploaded == 1
                )
            )
            uploaded_result = await self.auth.db.execute(uploaded_sql)
            uploaded_chunks = uploaded_result.scalar() or 0

            # 计算进度
            progress = uploaded_chunks / total_chunks if total_chunks > 0 else 0.0

            return {
                "total_chunks": total_chunks,
                "uploaded_chunks": uploaded_chunks,
                "progress": progress,
                "is_completed": uploaded_chunks == total_chunks and total_chunks > 0
            }
        except Exception as e:
            raise CustomException(msg=f"获取上传进度失败: {str(e)}")

    async def verify_all_chunks_uploaded(self, dataset_id: int) -> bool:
        """
        验证所有分片是否已上传

        参数:
        - dataset_id (int): 数据集ID

        返回:
        - bool: 是否所有分片都已上传

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            progress = await self.get_upload_progress(dataset_id)
            return progress["is_completed"]
        except Exception as e:
            raise CustomException(msg=f"验证分片上传状态失败: {str(e)}")

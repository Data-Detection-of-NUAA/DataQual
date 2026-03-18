# -*- coding: utf-8 -*-

import json
import time
from datetime import datetime
from collections.abc import Sequence
from typing import Any
from sqlalchemy import select, func, and_, or_, desc, delete
from sqlalchemy.engine import Result

from app.core.base_crud import CRUDBase
from app.core.exceptions import CustomException
from app.api.v1.module_system.auth.schema import AuthSchema

from .model import (
    ModelConfigModel,
    ModelStatusEnum,
    TrainTaskModel,
    TrainTaskStatusEnum,
    TrainProgressModel
)
from .schema import (
    ModelConfigCreateSchema,
    ModelConfigUpdateSchema,
    ModelConfigOutSchema,
    ModelCardSchema,
    ModelDetailSchema,
    TrainTaskCreateRequest,
    TrainTaskStatusUpdateRequest,
    TrainProgressRecordRequest
)


class ModelConfigCRUD(CRUDBase[ModelConfigModel, ModelConfigCreateSchema, ModelConfigUpdateSchema]):
    """模型配置数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        """
        初始化模型配置CRUD数据层

        参数:
        - auth (AuthSchema): 认证信息模型
        """
        super().__init__(model=ModelConfigModel, auth=auth)

    # ==================== 基础 CRUD 操作 ====================

    async def get_by_id_crud(self, id: int, preload: list[str] | None = None) -> ModelConfigModel | None:
        """
        根据ID获取模型配置详情

        参数:
        - id (int): 模型配置ID
        - preload (list[str] | None): 预加载关系，未提供时使用模型默认项

        返回:
        - ModelConfigModel | None: 模型配置模型实例或None
        """
        return await self.get(id=id, preload=preload)

    async def get_by_model_name(self, model_name: str) -> ModelConfigModel | None:
        """
        根据模型名称获取模型配置

        参数:
        - model_name (str): 模型名称（唯一标识）

        返回:
        - ModelConfigModel | None: 模型配置模型实例或None

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            return await self.get(model_name=model_name)
        except Exception as e:
            raise CustomException(msg=f"根据模型名称查询失败: {str(e)}")

    async def list_crud(
        self,
        search: dict | None = None,
        order_by: list[dict] | None = None,
        preload: list[str] | None = None
    ) -> Sequence[ModelConfigModel]:
        """
        获取模型配置列表

        参数:
        - search (dict | None): 查询参数
        - order_by (list[dict] | None): 排序参数
        - preload (list[str] | None): 预加载关系，未提供时使用模型默认项

        返回:
        - Sequence[ModelConfigModel]: 模型配置模型实例序列
        """
        return await self.list(search=search, order_by=order_by, preload=preload)

    async def create_crud(self, data: ModelConfigCreateSchema) -> ModelConfigModel | None:
        """
        创建模型配置

        参数:
        - data (ModelConfigCreateSchema): 模型配置创建模型

        返回:
        - ModelConfigModel | None: 模型配置模型实例或None

        异常:
        - CustomException: 模型名称已存在时抛出异常
        """
        # 检查模型名称是否已存在
        existing = await self.get_by_model_name(data.model_name)
        if existing:
            raise CustomException(msg=f"模型名称 '{data.model_name}' 已存在")

        # 转换列表字段为逗号分隔的字符串
        data_dict = data.model_dump()
        data_dict['supported_modalities'] = ','.join(data.supported_modalities)
        data_dict['supported_task_types'] = ','.join(data.supported_task_types)
        if data.tags:
            data_dict['tags'] = ','.join(data.tags)

        # 转换字典字段为JSON字符串
        if data.pretrained_weights:
            data_dict['pretrained_weights'] = json.dumps(data.pretrained_weights, ensure_ascii=False)
        data_dict['default_train_config'] = json.dumps(data.default_train_config, ensure_ascii=False)
        if data.performance_metrics:
            data_dict['performance_metrics'] = json.dumps(data.performance_metrics, ensure_ascii=False)
        if data.hardware_requirements:
            data_dict['hardware_requirements'] = json.dumps(data.hardware_requirements, ensure_ascii=False)

        return await self.create(data=data_dict)

    async def update_crud(self, id: int, data: ModelConfigUpdateSchema) -> ModelConfigModel | None:
        """
        更新模型配置

        参数:
        - id (int): 模型配置ID
        - data (ModelConfigUpdateSchema): 模型配置更新模型

        返回:
        - ModelConfigModel | None: 模型配置模型实例或None

        异常:
        - CustomException: 模型配置不存在时抛出异常
        """
        # 检查模型是否存在
        model_config = await self.get(id=id)
        if not model_config:
            raise CustomException(msg="模型配置不存在")

        # 转换数据格式
        data_dict = data.model_dump(exclude_none=True)
        if 'supported_modalities' in data_dict and data_dict['supported_modalities']:
            data_dict['supported_modalities'] = ','.join(data_dict['supported_modalities'])
        if 'supported_task_types' in data_dict and data_dict['supported_task_types']:
            data_dict['supported_task_types'] = ','.join(data_dict['supported_task_types'])
        if 'tags' in data_dict and data_dict['tags']:
            data_dict['tags'] = ','.join(data_dict['tags'])

        # 转换JSON字段
        if 'pretrained_weights' in data_dict and data_dict['pretrained_weights']:
            data_dict['pretrained_weights'] = json.dumps(data_dict['pretrained_weights'], ensure_ascii=False)
        if 'default_train_config' in data_dict and data_dict['default_train_config']:
            data_dict['default_train_config'] = json.dumps(data_dict['default_train_config'], ensure_ascii=False)
        if 'performance_metrics' in data_dict and data_dict['performance_metrics']:
            data_dict['performance_metrics'] = json.dumps(data_dict['performance_metrics'], ensure_ascii=False)
        if 'hardware_requirements' in data_dict and data_dict['hardware_requirements']:
            data_dict['hardware_requirements'] = json.dumps(data_dict['hardware_requirements'], ensure_ascii=False)

        return await self.update(id=id, data=data_dict)

    async def delete_crud(self, ids: list[int]) -> None:
        """
        批量删除模型配置

        参数:
        - ids (list[int]): 模型配置ID列表

        返回:
        - None
        """
        return await self.delete(ids=ids)

    async def set_available_crud(self, ids: list[int], status: str) -> None:
        """
        批量设置模型可用状态

        参数:
        - ids (list[int]): 模型配置ID列表
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
        模型配置分页查询

        参数:
        - offset (int): 偏移量
        - limit (int): 每页数量
        - order_by (list[dict] | None): 排序参数
        - search (dict | None): 查询参数
        - preload (list | None): 预加载关系，未提供时使用模型默认项

        返回:
        - dict: 分页数据
        """
        order_by_list = order_by or [{'priority': 'desc'}, {'created_time': 'desc'}]
        search_dict = search or {}

        return await self.page(
            offset=offset,
            limit=limit,
            order_by=order_by_list,
            search=search_dict,
            out_schema=ModelConfigOutSchema,
            preload=preload
        )

    # ==================== 扩展查询方法 ====================

    async def get_active_models(
        self,
        order_by: list[dict] | None = None
    ) -> Sequence[ModelConfigModel]:
        """
        获取所有激活状态的模型

        参数:
        - order_by (list[dict] | None): 排序参数

        返回:
        - Sequence[ModelConfigModel]: 模型配置列表

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            search = {"status": ("eq", ModelStatusEnum.ACTIVE.value)}
            order_by_list = order_by or [{'priority': 'desc'}, {'created_time': 'desc'}]
            return await self.list(search=search, order_by=order_by_list)
        except Exception as e:
            raise CustomException(msg=f"查询激活模型失败: {str(e)}")

    async def get_models_by_modality(
        self,
        modality: str,
        only_active: bool = True
    ) -> Sequence[ModelConfigModel]:
        """
        根据模态类型查询模型

        参数:
        - modality (str): 数据模态类型
        - only_active (bool): 是否仅返回激活状态的模型

        返回:
        - Sequence[ModelConfigModel]: 模型配置列表

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            sql = select(ModelConfigModel).where(
                ModelConfigModel.supported_modalities.like(f"%{modality}%")
            )
            if only_active:
                sql = sql.where(ModelConfigModel.status == ModelStatusEnum.ACTIVE.value)

            sql = sql.order_by(
                ModelConfigModel.priority.desc(),
                ModelConfigModel.created_time.desc()
            )

            result: Result = await self.auth.db.execute(sql)
            return result.scalars().all()
        except Exception as e:
            raise CustomException(msg=f"根据模态类型查询模型失败: {str(e)}")

    async def get_models_by_task_type(
        self,
        task_type: str,
        only_active: bool = True
    ) -> Sequence[ModelConfigModel]:
        """
        根据任务类型查询模型

        参数:
        - task_type (str): 任务类型
        - only_active (bool): 是否仅返回激活状态的模型

        返回:
        - Sequence[ModelConfigModel]: 模型配置列表

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            sql = select(ModelConfigModel).where(
                ModelConfigModel.supported_task_types.like(f"%{task_type}%")
            )
            if only_active:
                sql = sql.where(ModelConfigModel.status == ModelStatusEnum.ACTIVE.value)

            sql = sql.order_by(
                ModelConfigModel.priority.desc(),
                ModelConfigModel.created_time.desc()
            )

            result: Result = await self.auth.db.execute(sql)
            return result.scalars().all()
        except Exception as e:
            raise CustomException(msg=f"根据任务类型查询模型失败: {str(e)}")

    async def recommend_models(
        self,
        modality: str,
        task_type: str | None = None,
        top_k: int = 5,
        only_active: bool = True
    ) -> Sequence[ModelConfigModel]:
        """
        推荐模型（核心推荐逻辑）

        参数:
        - modality (str): 数据模态类型
        - task_type (str | None): 任务类型（可选）
        - top_k (int): 返回的推荐数量
        - only_active (bool): 是否仅返回激活状态的模型

        返回:
        - Sequence[ModelConfigModel]: 推荐的模型配置列表（按优先级排序）

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            # 构建查询条件
            conditions = [
                ModelConfigModel.supported_modalities.like(f"%{modality}%")
            ]

            if task_type:
                conditions.append(
                    ModelConfigModel.supported_task_types.like(f"%{task_type}%")
                )

            if only_active:
                conditions.append(
                    ModelConfigModel.status == ModelStatusEnum.ACTIVE.value
                )

            # 执行查询
            sql = select(ModelConfigModel).where(and_(*conditions)).order_by(
                ModelConfigModel.priority.desc(),
                ModelConfigModel.usage_count.desc(),
                ModelConfigModel.created_time.desc()
            ).limit(top_k)

            result: Result = await self.auth.db.execute(sql)
            return result.scalars().all()
        except Exception as e:
            raise CustomException(msg=f"推荐模型失败: {str(e)}")

    async def get_models_by_framework(
        self,
        framework: str,
        only_active: bool = True
    ) -> Sequence[ModelConfigModel]:
        """
        根据框架查询模型

        参数:
        - framework (str): 深度学习框架
        - only_active (bool): 是否仅返回激活状态的模型

        返回:
        - Sequence[ModelConfigModel]: 模型配置列表

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            search = {"framework": ("eq", framework)}
            if only_active:
                search["status"] = ("eq", ModelStatusEnum.ACTIVE.value)

            return await self.list(
                search=search,
                order_by=[{'priority': 'desc'}, {'created_time': 'desc'}]
            )
        except Exception as e:
            raise CustomException(msg=f"根据框架查询模型失败: {str(e)}")

    async def search_models_by_tag(
        self,
        tag: str,
        only_active: bool = True
    ) -> Sequence[ModelConfigModel]:
        """
        根据标签搜索模型

        参数:
        - tag (str): 标签关键词
        - only_active (bool): 是否仅返回激活状态的模型

        返回:
        - Sequence[ModelConfigModel]: 模型配置列表

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            sql = select(ModelConfigModel).where(
                ModelConfigModel.tags.like(f"%{tag}%")
            )
            if only_active:
                sql = sql.where(ModelConfigModel.status == ModelStatusEnum.ACTIVE.value)

            sql = sql.order_by(
                ModelConfigModel.priority.desc(),
                ModelConfigModel.created_time.desc()
            )

            result: Result = await self.auth.db.execute(sql)
            return result.scalars().all()
        except Exception as e:
            raise CustomException(msg=f"根据标签搜索模型失败: {str(e)}")

    async def increment_usage_count(self, model_id: int) -> ModelConfigModel | None:
        """
        增加模型使用次数

        参数:
        - model_id (int): 模型配置ID

        返回:
        - ModelConfigModel | None: 更新后的模型配置实例

        异常:
        - CustomException: 更新失败时抛出异常
        """
        try:
            model = await self.get(id=model_id)
            if not model:
                raise CustomException(msg="模型配置不存在")

            model.usage_count += 1
            await self.auth.db.flush()
            await self.auth.db.refresh(model)
            return model
        except Exception as e:
            raise CustomException(msg=f"增加使用次数失败: {str(e)}")

    async def update_model_status(
        self,
        model_id: int,
        status: str
    ) -> ModelConfigModel | None:
        """
        更新模型状态

        参数:
        - model_id (int): 模型配置ID
        - status (str): 模型状态（active/inactive/deprecated）

        返回:
        - ModelConfigModel | None: 更新后的模型配置实例

        异常:
        - CustomException: 更新失败时抛出异常
        """
        try:
            # 验证状态值
            valid_statuses = [e.value for e in ModelStatusEnum]
            if status not in valid_statuses:
                raise CustomException(msg=f"无效的状态值: {status}")

            model = await self.get(id=model_id)
            if not model:
                raise CustomException(msg="模型配置不存在")

            model.status = status
            await self.auth.db.flush()
            await self.auth.db.refresh(model)
            return model
        except Exception as e:
            raise CustomException(msg=f"更新模型状态失败: {str(e)}")

    async def get_statistics(self) -> dict:
        """
        获取模型配置统计信息

        返回:
        - dict: 统计信息字典

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            # 总模型数量
            total_count_sql = select(func.count(ModelConfigModel.id))
            total_result = await self.auth.db.execute(total_count_sql)
            total_count = total_result.scalar() or 0

            # 激活模型数量
            active_count_sql = select(func.count(ModelConfigModel.id)).where(
                ModelConfigModel.status == ModelStatusEnum.ACTIVE.value
            )
            active_result = await self.auth.db.execute(active_count_sql)
            active_count = active_result.scalar() or 0

            # 停用模型数量
            inactive_count_sql = select(func.count(ModelConfigModel.id)).where(
                ModelConfigModel.status == ModelStatusEnum.INACTIVE.value
            )
            inactive_result = await self.auth.db.execute(inactive_count_sql)
            inactive_count = inactive_result.scalar() or 0

            # 已弃用模型数量
            deprecated_count_sql = select(func.count(ModelConfigModel.id)).where(
                ModelConfigModel.status == ModelStatusEnum.DEPRECATED.value
            )
            deprecated_result = await self.auth.db.execute(deprecated_count_sql)
            deprecated_count = deprecated_result.scalar() or 0

            # 总使用次数
            total_usage_sql = select(func.sum(ModelConfigModel.usage_count))
            usage_result = await self.auth.db.execute(total_usage_sql)
            total_usage = usage_result.scalar()
            total_usage = int(total_usage) if total_usage is not None else 0

            # 按框架统计
            framework_count_sql = select(
                ModelConfigModel.framework,
                func.count(ModelConfigModel.id)
            ).group_by(ModelConfigModel.framework)
            framework_result = await self.auth.db.execute(framework_count_sql)
            framework_stats = {row[0]: row[1] for row in framework_result.all()}

            return {
                "total_count": total_count,
                "active_count": active_count,
                "inactive_count": inactive_count,
                "deprecated_count": deprecated_count,
                "total_usage": total_usage,
                "framework_stats": framework_stats
            }
        except Exception as e:
            raise CustomException(msg=f"获取统计信息失败: {str(e)}")

    async def get_popular_models(
        self,
        top_k: int = 10,
        only_active: bool = True
    ) -> Sequence[ModelConfigModel]:
        """
        获取热门模型（按使用次数排序）

        参数:
        - top_k (int): 返回的模型数量
        - only_active (bool): 是否仅返回激活状态的模型

        返回:
        - Sequence[ModelConfigModel]: 热门模型列表

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            sql = select(ModelConfigModel)
            if only_active:
                sql = sql.where(ModelConfigModel.status == ModelStatusEnum.ACTIVE.value)

            sql = sql.order_by(
                ModelConfigModel.usage_count.desc(),
                ModelConfigModel.priority.desc()
            ).limit(top_k)

            result: Result = await self.auth.db.execute(sql)
            return result.scalars().all()
        except Exception as e:
            raise CustomException(msg=f"获取热门模型失败: {str(e)}")


class TrainTaskCRUD(CRUDBase[TrainTaskModel, TrainTaskCreateRequest, TrainTaskStatusUpdateRequest]):
    """训练任务数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        super().__init__(model=TrainTaskModel, auth=auth)

    async def create_task_crud(
        self,
        data: TrainTaskCreateRequest,
        dataset_info: dict,
        model_config: dict
    ) -> TrainTaskModel | None:
        """
        创建训练任务

        参数:
        - data: 训练任务创建请求
        - dataset_info: 数据集信息快照
        - model_config: 模型配置快照

        返回:
        - TrainTaskModel: 创建的训练任务

        异常:
        - CustomException: 创建失败时抛出异常
        """
        try:
            # 生成任务ID: TRAIN_timestamp_userid
            timestamp = int(time.time())
            task_id = f"TRAIN_{timestamp}_{self.auth.user.id}"

            # 检查任务ID是否已存在（理论上不会重复，但做双重保险）
            existing = await self.get_by_task_id(task_id)
            if existing:
                raise CustomException(msg=f"任务ID '{task_id}' 已存在")

            # 准备任务数据
            task_data = {
                'task_id': task_id,
                'status': TrainTaskStatusEnum.CREATED.value,
                'dataset_id': data.dataset_id,
                'dataset_info': json.dumps(dataset_info, ensure_ascii=False),
                'model_config_id': data.model_config_id,
                'model_config': json.dumps(model_config, ensure_ascii=False),
                'train_config': json.dumps(data.train_config.model_dump(), ensure_ascii=False),
                'total_epochs': data.train_config.epochs,
                'current_epoch': 0,
                'progress_percentage': 0.0,
                'remarks': data.remarks,
                'created_id': self.auth.user.id,
                'updated_id': self.auth.user.id
            }

            return await self.create(data=task_data)
        except CustomException:
            raise
        except Exception as e:
            raise CustomException(msg=f"创建训练任务失败: {str(e)}")

    async def get_by_task_id(self, task_id: str) -> TrainTaskModel | None:
        """
        根据任务ID获取训练任务

        参数:
        - task_id: 任务ID

        返回:
        - TrainTaskModel | None: 训练任务或None
        """
        try:
            sql = select(TrainTaskModel).where(TrainTaskModel.task_id == task_id)
            result: Result = await self.auth.db.execute(sql)
            return result.scalars().first()
        except Exception as e:
            raise CustomException(msg=f"查询训练任务失败: {str(e)}")

    async def get_by_id_crud(self, task_id: int) -> TrainTaskModel | None:
        """
        根据主键ID获取训练任务详情

        参数:
        - task_id: 主键ID

        返回:
        - TrainTaskModel | None: 训练任务或None
        """
        try:
            return await self.get(id=task_id)
        except Exception as e:
            raise CustomException(msg=f"获取训练任务详情失败: {str(e)}")

    async def update_task_status(
        self,
        task_id: str,
        status: str,
        error_message: str | None = None
    ) -> TrainTaskModel | None:
        """
        更新训练任务状态

        参数:
        - task_id: 任务ID
        - status: 新状态
        - error_message: 错误信息（如果状态为failed）

        返回:
        - TrainTaskModel: 更新后的训练任务

        异常:
        - CustomException: 更新失败时抛出异常
        """
        try:
            # 验证状态值
            valid_statuses = {e.value for e in TrainTaskStatusEnum}
            if status not in valid_statuses:
                raise CustomException(msg=f"无效的状态值: {status}")

            # 获取任务
            task = await self.get_by_task_id(task_id)
            if not task:
                raise CustomException(msg=f"任务 '{task_id}' 不存在")

            # 准备更新数据
            update_data = {
                'status': status,
                'updated_by_id': self.auth.user.id if self.auth.user else None
            }

            # 根据状态设置时间戳
            if status == TrainTaskStatusEnum.RUNNING.value and not task.actual_start_time:
                update_data['actual_start_time'] = datetime.now()
            elif status == TrainTaskStatusEnum.COMPLETED.value:
                update_data['actual_completion_time'] = datetime.now()
                update_data['progress_percentage'] = 100.0
            elif status == TrainTaskStatusEnum.FAILED.value:
                update_data['actual_completion_time'] = datetime.now()
                if error_message:
                    update_data['error_message'] = error_message

            return await self.update(id=task.id, data=update_data)
        except CustomException:
            raise
        except Exception as e:
            raise CustomException(msg=f"更新任务状态失败: {str(e)}")

    async def update_task_progress(
        self,
        task_id: str,
        current_epoch: int,
        progress_percentage: float
    ) -> TrainTaskModel | None:
        """
        更新训练任务进度

        参数:
        - task_id: 任务ID
        - current_epoch: 当前轮次
        - progress_percentage: 进度百分比

        返回:
        - TrainTaskModel: 更新后的训练任务

        异常:
        - CustomException: 更新失败时抛出异常
        """
        try:
            task = await self.get_by_task_id(task_id)
            if not task:
                raise CustomException(msg=f"任务 '{task_id}' 不存在")

            update_data = {
                'current_epoch': current_epoch,
                'progress_percentage': min(progress_percentage, 100.0),
                'updated_by_id': self.auth.user.id if self.auth.user else None
            }

            return await self.update(id=task.id, data=update_data)
        except CustomException:
            raise
        except Exception as e:
            raise CustomException(msg=f"更新任务进度失败: {str(e)}")

    async def get_tasks_by_status(
        self,
        status: str,
        limit: int = 100
    ) -> Sequence[TrainTaskModel]:
        """
        根据状态获取训练任务列表

        参数:
        - status: 任务状态
        - limit: 限制数量

        返回:
        - Sequence[TrainTaskModel]: 训练任务列表
        """
        try:
            sql = select(TrainTaskModel).where(
                TrainTaskModel.status == status
            ).order_by(
                TrainTaskModel.created_time.desc()
            ).limit(limit)

            result: Result = await self.auth.db.execute(sql)
            return result.scalars().all()
        except Exception as e:
            raise CustomException(msg=f"查询任务列表失败: {str(e)}")

    async def get_user_tasks(
        self,
        user_id: int | None = None,
        status: str | None = None,
        limit: int = 100
    ) -> Sequence[TrainTaskModel]:
        """
        获取用户的训练任务列表

        参数:
        - user_id: 用户ID（默认为当前用户）
        - status: 任务状态过滤
        - limit: 限制数量

        返回:
        - Sequence[TrainTaskModel]: 训练任务列表
        """
        try:
            target_user_id = user_id if user_id is not None else self.auth.user.id

            sql = select(TrainTaskModel).where(
                TrainTaskModel.created_id == target_user_id
            )

            if status:
                sql = sql.where(TrainTaskModel.status == status)

            sql = sql.order_by(
                TrainTaskModel.created_time.desc()
            ).limit(limit)

            result: Result = await self.auth.db.execute(sql)
            return result.scalars().all()
        except Exception as e:
            raise CustomException(msg=f"获取用户任务列表失败: {str(e)}")

    async def page_crud(
        self,
        page: int = 1,
        page_size: int = 10,
        status: str | None = None,
        dataset_id: int | None = None,
        model_config_id: int | None = None,
        user_id: int | None = None
    ) -> tuple[Sequence[TrainTaskModel], int]:
        """
        分页查询训练任务列表

        参数:
        - page: 页码
        - page_size: 每页数量
        - status: 状态过滤
        - dataset_id: 数据集ID过滤
        - model_config_id: 模型配置ID过滤
        - user_id: 用户ID过滤

        返回:
        - tuple[Sequence[TrainTaskModel], int]: (任务列表, 总数)
        """
        try:
            sql = select(TrainTaskModel)

            # 应用过滤条件
            if status:
                sql = sql.where(TrainTaskModel.status == status)
            if dataset_id:
                sql = sql.where(TrainTaskModel.dataset_id == dataset_id)
            if model_config_id:
                sql = sql.where(TrainTaskModel.model_config_id == model_config_id)
            if user_id:
                sql = sql.where(TrainTaskModel.created_id == user_id)

            # 获取总数
            count_sql = select(func.count()).select_from(sql.subquery())
            count_result = await self.auth.db.execute(count_sql)
            total = count_result.scalar() or 0

            # 分页查询
            sql = sql.order_by(
                TrainTaskModel.created_time.desc()
            ).limit(page_size).offset((page - 1) * page_size)

            result: Result = await self.auth.db.execute(sql)
            tasks = result.scalars().all()

            return tasks, total
        except Exception as e:
            raise CustomException(msg=f"分页查询训练任务失败: {str(e)}")

    async def delete_task_crud(self, task_id: str) -> bool:
        """
        删除训练任务（包括数据库记录、进度记录和文件）

        参数:
        - task_id: 任务ID

        返回:
        - bool: 是否删除成功

        异常:
        - CustomException: 删除失败时抛出异常
        """
        try:
            from pathlib import Path
            import shutil
            from app.core.logger import log

            task = await self.get_by_task_id(task_id)
            if not task:
                raise CustomException(msg=f"任务 '{task_id}' 不存在")

            # 检查任务状态，不允许删除正在运行的任务
            if task.status == TrainTaskStatusEnum.RUNNING.value:
                raise CustomException(msg="不能删除正在运行的任务，请先停止任务")

            # 1. 删除关联的进度记录（不提交事务）
            try:
                sql = delete(TrainProgressModel).where(
                    TrainProgressModel.task_id == task_id
                )
                await self.auth.db.execute(sql)
                log.info(f"已删除任务 {task_id} 的进度记录")
            except Exception as e:
                log.warning(f"删除进度记录失败: {str(e)}")

            # 2. 删除数据库记录（不提交事务）
            await self.delete([task.id])

            # 3. 提交事务
            await self.auth.db.commit()

            # 4. 删除任务目录和文件（在事务提交后）
            try:
                task_dir = Path("static/train/tasks") / task_id
                if task_dir.exists():
                    shutil.rmtree(task_dir)
                    log.info(f"已删除任务目录: {task_dir}")
            except Exception as e:
                log.warning(f"删除任务目录失败: {str(e)}")

            log.info(f"成功删除训练任务: {task_id}")
            return True

        except CustomException:
            await self.auth.db.rollback()
            raise
        except Exception as e:
            await self.auth.db.rollback()
            raise CustomException(msg=f"删除训练任务失败: {str(e)}")

    async def update_task_result(
        self,
        task_id: str,
        final_metrics: dict,
        model_save_path: str | None = None,
        result_file_path: str | None = None
    ) -> TrainTaskModel | None:
        """
        更新训练任务结果

        参数:
        - task_id: 任务ID
        - final_metrics: 最终评估指标
        - model_save_path: 模型保存路径
        - result_file_path: 结果文件路径

        返回:
        - TrainTaskModel: 更新后的训练任务

        异常:
        - CustomException: 更新失败时抛出异常
        """
        try:
            task = await self.get_by_task_id(task_id)
            if not task:
                raise CustomException(msg=f"任务 '{task_id}' 不存在")

            update_data = {
                'final_metrics': json.dumps(final_metrics, ensure_ascii=False),
                'updated_by_id': self.auth.user.id if self.auth.user else None
            }

            if model_save_path:
                update_data['model_save_path'] = model_save_path
            if result_file_path:
                update_data['result_file_path'] = result_file_path

            return await self.update(id=task.id, data=update_data)
        except CustomException:
            raise
        except Exception as e:
            raise CustomException(msg=f"更新任务结果失败: {str(e)}")


class TrainProgressCRUD(CRUDBase[TrainProgressModel, TrainProgressRecordRequest, TrainProgressRecordRequest]):
    """训练进度数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        super().__init__(model=TrainProgressModel, auth=auth)

    async def create_progress_record(
        self,
        data: TrainProgressRecordRequest
    ) -> TrainProgressModel | None:
        """
        创建训练进度记录

        参数:
        - data: 训练进度记录请求

        返回:
        - TrainProgressModel: 创建的进度记录

        异常:
        - CustomException: 创建失败时抛出异常
        """
        try:
            from app.core.logger import log
            from sqlalchemy import text
            from app.utils.common_util import uuid4_str
            from datetime import datetime

            # 验证任务是否存在
            task_crud = TrainTaskCRUD(auth=self.auth)
            task = await task_crud.get_by_task_id(data.task_id)
            if not task:
                raise CustomException(msg=f"任务 '{data.task_id}' 不存在")

            # 准备进度数据
            progress_data = data.model_dump()

            # 处理可选的JSON字段
            resource_metrics_json = None
            if data.resource_metrics:
                resource_metrics_json = json.dumps(data.resource_metrics, ensure_ascii=False)

            additional_metrics_json = None
            if data.additional_metrics:
                additional_metrics_json = json.dumps(data.additional_metrics, ensure_ascii=False)

            # 生成UUID和时间戳（ModelMixin提供的字段）
            record_uuid = uuid4_str()
            now = datetime.now()

            # 使用原始SQL INSERT来绕过SQLAlchemy ORM的问题
            insert_sql = text("""
                INSERT INTO train_progress (
                    uuid, status, description, created_time, updated_time,
                    task_id, epoch, batch, total_batches,
                    train_loss, train_accuracy, val_loss, val_accuracy,
                    learning_rate, epoch_progress, overall_progress,
                    resource_metrics, additional_metrics, timestamp
                ) VALUES (
                    :uuid, :status, :description, :created_time, :updated_time,
                    :task_id, :epoch, :batch, :total_batches,
                    :train_loss, :train_accuracy, :val_loss, :val_accuracy,
                    :learning_rate, :epoch_progress, :overall_progress,
                    :resource_metrics, :additional_metrics, :timestamp
                )
            """)

            result = await self.auth.db.execute(
                insert_sql,
                {
                    "uuid": record_uuid,
                    "status": "0",
                    "description": None,
                    "created_time": now,
                    "updated_time": now,
                    "task_id": data.task_id,
                    "epoch": data.epoch,
                    "batch": data.batch,
                    "total_batches": data.total_batches,
                    "train_loss": data.train_loss,
                    "train_accuracy": data.train_accuracy,
                    "val_loss": data.val_loss,
                    "val_accuracy": data.val_accuracy,
                    "learning_rate": data.learning_rate,
                    "epoch_progress": data.epoch_progress,
                    "overall_progress": data.overall_progress,
                    "resource_metrics": resource_metrics_json,
                    "additional_metrics": additional_metrics_json,
                    "timestamp": now
                }
            )

            await self.auth.db.commit()

            # 获取刚插入的记录ID
            inserted_id = result.lastrowid

            # 查询并返回创建的记录 - 使用明确的列名
            query_sql = text("""
                SELECT id, uuid, status, description, created_time, updated_time,
                       task_id, epoch, batch, total_batches,
                       train_loss, train_accuracy, val_loss, val_accuracy,
                       learning_rate, epoch_progress, overall_progress,
                       resource_metrics, timestamp, additional_metrics
                FROM train_progress WHERE id = :id
            """)
            query_result = await self.auth.db.execute(query_sql, {"id": inserted_id})
            row = query_result.fetchone()

            if row:
                # 将结果转换为模型对象
                record = TrainProgressModel(
                    id=row[0],
                    uuid=row[1],
                    status=row[2],
                    description=row[3],
                    created_time=row[4],
                    updated_time=row[5],
                    task_id=row[6],
                    epoch=row[7],
                    batch=row[8],
                    total_batches=row[9],
                    train_loss=row[10],
                    train_accuracy=row[11],
                    val_loss=row[12],
                    val_accuracy=row[13],
                    learning_rate=row[14],
                    epoch_progress=row[15],
                    overall_progress=row[16],
                    resource_metrics=json.loads(row[17]) if row[17] else None,
                    timestamp=row[18],
                    additional_metrics=json.loads(row[19]) if row[19] else None
                )

                return record

            return None

        except CustomException:
            raise
        except Exception as e:
            log.error(f"创建进度记录失败: {str(e)}")
            raise CustomException(msg=f"创建进度记录失败: {str(e)}")

    async def get_latest_progress(
        self,
        task_id: str
    ) -> TrainProgressModel | None:
        """
        获取任务的最新进度记录（优先返回有验证指标的记录）

        参数:
        - task_id: 任务ID

        返回:
        - TrainProgressModel | None: 最新进度记录或None
        """
        try:
            # 优先查询有验证指标的最新记录（epoch级别的进度）
            sql_with_val = select(TrainProgressModel).where(
                and_(
                    TrainProgressModel.task_id == task_id,
                    TrainProgressModel.val_loss.isnot(None)
                )
            ).order_by(
                TrainProgressModel.epoch.desc(),
                TrainProgressModel.batch.desc()
            ).limit(1)

            result: Result = await self.auth.db.execute(sql_with_val)
            record = result.scalars().first()

            # 如果没有验证指标的记录，则返回最新的任意记录
            if not record:
                sql = select(TrainProgressModel).where(
                    TrainProgressModel.task_id == task_id
                ).order_by(
                    TrainProgressModel.epoch.desc(),
                    TrainProgressModel.batch.desc()
                ).limit(1)

                result = await self.auth.db.execute(sql)
                record = result.scalars().first()

            return record
        except Exception as e:
            raise CustomException(msg=f"获取最新进度失败: {str(e)}")

    async def get_progress_by_epoch(
        self,
        task_id: str,
        epoch: int
    ) -> Sequence[TrainProgressModel]:
        """
        获取指定epoch的所有进度记录

        参数:
        - task_id: 任务ID
        - epoch: 训练轮次

        返回:
        - Sequence[TrainProgressModel]: 进度记录列表
        """
        try:
            sql = select(TrainProgressModel).where(
                TrainProgressModel.task_id == task_id,
                TrainProgressModel.epoch == epoch
            ).order_by(
                TrainProgressModel.batch.asc()
            )

            result: Result = await self.auth.db.execute(sql)
            return result.scalars().all()
        except Exception as e:
            raise CustomException(msg=f"获取epoch进度失败: {str(e)}")

    async def get_progress_history(
        self,
        task_id: str,
        limit: int = 1000
    ) -> Sequence[TrainProgressModel]:
        """
        获取任务的历史进度记录

        参数:
        - task_id: 任务ID
        - limit: 限制数量

        返回:
        - Sequence[TrainProgressModel]: 进度记录列表
        """
        try:
            sql = select(TrainProgressModel).where(
                TrainProgressModel.task_id == task_id
            ).order_by(
                TrainProgressModel.epoch.asc(),
                TrainProgressModel.batch.asc()
            ).limit(limit)

            result: Result = await self.auth.db.execute(sql)
            return result.scalars().all()
        except Exception as e:
            raise CustomException(msg=f"获取历史进度失败: {str(e)}")

    async def get_progress_curve_data(
        self,
        task_id: str,
        metrics: list[str] | None = None
    ) -> list[dict]:
        """
        获取训练曲线数据（每个epoch的汇总数据，优先选择有验证指标的记录）

        参数:
        - task_id: 任务ID
        - metrics: 需要的指标列表（默认为所有指标）

        返回:
        - list[dict]: 训练曲线数据

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            # 查询所有有验证指标的记录（epoch级别的进度）
            sql = select(TrainProgressModel).where(
                and_(
                    TrainProgressModel.task_id == task_id,
                    TrainProgressModel.val_loss.isnot(None)
                )
            ).order_by(
                TrainProgressModel.epoch.asc()
            )

            result: Result = await self.auth.db.execute(sql)
            records = result.scalars().all()

            # 如果没有验证指标的记录，则查询所有记录并按epoch分组
            if not records:
                sql = select(TrainProgressModel).where(
                    TrainProgressModel.task_id == task_id
                ).order_by(
                    TrainProgressModel.epoch.asc(),
                    TrainProgressModel.batch.desc()
                )

                result = await self.auth.db.execute(sql)
                all_records = result.scalars().all()

                # 按epoch分组，只取每个epoch的最后一条记录
                epoch_records = {}
                for record in all_records:
                    if record.epoch not in epoch_records:
                        epoch_records[record.epoch] = record

                records = [epoch_records[epoch] for epoch in sorted(epoch_records.keys())]

            # 构建曲线数据
            curve_data = []
            for record in records:
                data_point = {
                    'epoch': record.epoch,
                    'train_loss': record.train_loss,
                    'train_accuracy': record.train_accuracy,
                    'val_loss': record.val_loss,
                    'val_accuracy': record.val_accuracy,
                    'learning_rate': record.learning_rate,
                    'epoch_progress': record.epoch_progress,
                    'overall_progress': record.overall_progress
                }

                # 如果指定了metrics，只返回指定的指标
                if metrics:
                    data_point = {k: v for k, v in data_point.items() if k in metrics or k == 'epoch'}

                curve_data.append(data_point)

            return curve_data
        except Exception as e:
            raise CustomException(msg=f"获取训练曲线数据失败: {str(e)}")

    async def delete_task_progress(
        self,
        task_id: str
    ) -> int:
        """
        删除任务的所有进度记录

        参数:
        - task_id: 任务ID

        返回:
        - int: 删除的记录数

        异常:
        - CustomException: 删除失败时抛出异常
        """
        try:
            sql = delete(TrainProgressModel).where(
                TrainProgressModel.task_id == task_id
            )

            result = await self.auth.db.execute(sql)
            await self.auth.db.commit()

            return result.rowcount
        except Exception as e:
            await self.auth.db.rollback()
            raise CustomException(msg=f"删除进度记录失败: {str(e)}")

    async def get_epoch_summary(
        self,
        task_id: str
    ) -> list[dict]:
        """
        获取每个epoch的汇总统计

        参数:
        - task_id: 任务ID

        返回:
        - list[dict]: 每个epoch的统计数据

        异常:
        - CustomException: 查询失败时抛出异常
        """
        try:
            # 按epoch分组统计
            sql = select(
                TrainProgressModel.epoch,
                func.avg(TrainProgressModel.train_loss).label('avg_train_loss'),
                func.min(TrainProgressModel.train_loss).label('min_train_loss'),
                func.max(TrainProgressModel.train_loss).label('max_train_loss'),
                func.avg(TrainProgressModel.train_accuracy).label('avg_train_accuracy'),
                func.avg(TrainProgressModel.val_loss).label('avg_val_loss'),
                func.avg(TrainProgressModel.val_accuracy).label('avg_val_accuracy'),
                func.count().label('batch_count')
            ).where(
                TrainProgressModel.task_id == task_id
            ).group_by(
                TrainProgressModel.epoch
            ).order_by(
                TrainProgressModel.epoch.asc()
            )

            result: Result = await self.auth.db.execute(sql)
            rows = result.all()

            summary = []
            for row in rows:
                summary.append({
                    'epoch': row.epoch,
                    'avg_train_loss': float(row.avg_train_loss) if row.avg_train_loss else None,
                    'min_train_loss': float(row.min_train_loss) if row.min_train_loss else None,
                    'max_train_loss': float(row.max_train_loss) if row.max_train_loss else None,
                    'avg_train_accuracy': float(row.avg_train_accuracy) if row.avg_train_accuracy else None,
                    'avg_val_loss': float(row.avg_val_loss) if row.avg_val_loss else None,
                    'avg_val_accuracy': float(row.avg_val_accuracy) if row.avg_val_accuracy else None,
                    'batch_count': row.batch_count
                })

            return summary
        except Exception as e:
            raise CustomException(msg=f"获取epoch汇总统计失败: {str(e)}")

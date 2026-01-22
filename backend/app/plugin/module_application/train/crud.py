# -*- coding: utf-8 -*-

import json
from collections.abc import Sequence
from typing import Any
from sqlalchemy import select, func, and_, or_
from sqlalchemy.engine import Result

from app.core.base_crud import CRUDBase
from app.core.exceptions import CustomException
from app.api.v1.module_system.auth.schema import AuthSchema

from .model import ModelConfigModel, ModelStatusEnum
from .schema import (
    ModelConfigCreateSchema,
    ModelConfigUpdateSchema,
    ModelConfigOutSchema,
    ModelCardSchema,
    ModelDetailSchema
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

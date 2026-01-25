# -*- coding: utf-8 -*-

from typing import Sequence, Any

from app.core.base_crud import CRUDBase

from app.api.v1.module_system.auth.schema import AuthSchema
from .model import OptimizerTaskModel, OptimizerResultModel, OptimizerExecutionLogModel
from .schema import (
    OptimizerTaskCreateSchema, OptimizerTaskUpdateSchema,
    OptimizerResultCreateSchema, OptimizerResultUpdateSchema,
    OptimizerExecutionLogCreateSchema
)


class OptimizerTaskCRUD(CRUDBase[OptimizerTaskModel, OptimizerTaskCreateSchema, OptimizerTaskUpdateSchema]):
    """优化器任务数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        """
        初始化优化器任务CRUD

        参数:
        - auth (AuthSchema): 认证信息模型
        """
        self.auth = auth
        super().__init__(model=OptimizerTaskModel, auth=auth)

    async def get_obj_by_id_crud(self, id: int, preload: list[str | Any] | None = None) -> OptimizerTaskModel | None:
        """
        获取优化器任务详情

        参数:
        - id (int): 优化器任务ID
        - preload (list[str | Any] | None): 预加载关系，未提供时使用模型默认项

        返回:
        - OptimizerTaskModel | None: 优化器任务模型,如果不存在则为None
        """
        return await self.get(id=id, preload=preload)

    async def get_obj_list_crud(self, search: dict | None = None, order_by: list[dict[str, str]] | None = None, preload: list[str | Any] | None = None) -> Sequence[OptimizerTaskModel]:
        """
        获取优化器任务列表

        参数:
        - search (dict | None): 查询参数字典
        - order_by (list[dict[str, str]] | None): 排序参数列表
        - preload (list[str | Any] | None): 预加载关系，未提供时使用模型默认项

        返回:
        - Sequence[OptimizerTaskModel]: 优化器任务模型序列
        """
        return await self.list(search=search, order_by=order_by, preload=preload)

    async def create_obj_crud(self, data: OptimizerTaskCreateSchema) -> OptimizerTaskModel | None:
        """
        创建优化器任务

        参数:
        - data (OptimizerTaskCreateSchema): 创建优化器任务模型

        返回:
        - OptimizerTaskModel | None: 创建的优化器任务模型,如果创建失败则为None
        """
        return await self.create(data=data)

    async def update_obj_crud(self, id: int, data: OptimizerTaskUpdateSchema) -> OptimizerTaskModel | None:
        """
        更新优化器任务

        参数:
        - id (int): 优化器任务ID
        - data (OptimizerTaskUpdateSchema): 更新优化器任务模型

        返回:
        - OptimizerTaskModel | None: 更新后的优化器任务模型,如果更新失败则为None
        """
        return await self.update(id=id, data=data)

    async def delete_obj_crud(self, ids: list[int]) -> None:
        """
        删除优化器任务

        参数:
        - ids (list[int]): 优化器任务ID列表
        """
        return await self.delete(ids=ids)

    async def set_obj_field_crud(self, ids: list[int], **kwargs) -> None:
        """
        设置优化器任务字段

        参数:
        - ids (list[int]): 优化器任务ID列表
        - kwargs: 其他要设置的字段
        """
        return await self.set(ids=ids, **kwargs)

    async def clear_obj_crud(self) -> None:
        """
        清除优化器任务

        注意:
        - 此操作会删除所有优化器任务,请谨慎操作
        """
        return await self.clear()


class OptimizerResultCRUD(CRUDBase[OptimizerResultModel, OptimizerResultCreateSchema, OptimizerResultUpdateSchema]):
    """优化器结果数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        """
        初始化优化器结果CRUD

        参数:
        - auth (AuthSchema): 认证信息模型
        """
        self.auth = auth
        super().__init__(model=OptimizerResultModel, auth=auth)

    async def get_obj_result_by_id_crud(self, id: int, preload: list[str | Any] | None = None) -> OptimizerResultModel | None:
        """
        获取优化器结果详情

        参数:
        - id (int): 优化器结果ID
        - preload (list[str | Any] | None): 预加载关系，未提供时使用模型默认项

        返回:
        - OptimizerResultModel | None: 优化器结果模型,如果不存在则为None
        """
        return await self.get(id=id, preload=preload)

    async def get_obj_result_list_crud(self, search: dict | None = None, order_by: list[dict[str, str]] | None = None, preload: list[str | Any] | None = None) -> Sequence[OptimizerResultModel]:
        """
        获取优化器结果列表

        参数:
        - search (dict | None): 查询参数字典
        - order_by (list[dict[str, str]] | None): 排序参数列表
        - preload (list[str | Any] | None): 预加载关系，未提供时使用模型默认项

        返回:
        - Sequence[OptimizerResultModel]: 优化器结果模型序列
        """
        return await self.list(search=search, order_by=order_by, preload=preload)

    async def create_obj_result_crud(self, data: OptimizerResultCreateSchema) -> OptimizerResultModel | None:
        """
        创建优化器结果

        参数:
        - data (OptimizerResultCreateSchema): 创建优化器结果模型

        返回:
        - OptimizerResultModel | None: 创建的优化器结果模型,如果创建失败则为None
        """
        return await self.create(data=data)

    async def update_obj_result_crud(self, id: int, data: OptimizerResultUpdateSchema) -> OptimizerResultModel | None:
        """
        更新优化器结果

        参数:
        - id (int): 优化器结果ID
        - data (OptimizerResultUpdateSchema): 更新优化器结果模型

        返回:
        - OptimizerResultModel | None: 更新后的优化器结果模型,如果更新失败则为None
        """
        return await self.update(id=id, data=data)

    async def delete_obj_result_crud(self, ids: list[int]) -> None:
        """
        删除优化器结果

        参数:
        - ids (list[int]): 优化器结果ID列表
        """
        return await self.delete(ids=ids)

    async def clear_obj_result_crud(self) -> None:
        """
        清除优化器结果

        注意:
        - 此操作会删除所有优化器结果,请谨慎操作
        """
        return await self.clear()


class OptimizerExecutionLogCRUD(CRUDBase[OptimizerExecutionLogModel, OptimizerExecutionLogCreateSchema, OptimizerExecutionLogCreateSchema]):
    """优化器执行日志数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        """
        初始化优化器执行日志CRUD

        参数:
        - auth (AuthSchema): 认证信息模型
        """
        self.auth = auth
        super().__init__(model=OptimizerExecutionLogModel, auth=auth)

    async def get_obj_log_by_id_crud(self, id: int, preload: list[str | Any] | None = None) -> OptimizerExecutionLogModel | None:
        """
        获取优化器执行日志详情

        参数:
        - id (int): 优化器执行日志ID
        - preload (list[str | Any] | None): 预加载关系，未提供时使用模型默认项

        返回:
        - OptimizerExecutionLogModel | None: 优化器执行日志模型,如果不存在则为None
        """
        return await self.get(id=id, preload=preload)

    async def get_obj_log_list_crud(self, search: dict | None = None, order_by: list[dict[str, str]] | None = None, preload: list[str | Any] | None = None) -> Sequence[OptimizerExecutionLogModel]:
        """
        获取优化器执行日志列表

        参数:
        - search (dict | None): 查询参数字典
        - order_by (list[dict[str, str]] | None): 排序参数列表
        - preload (list[str | Any] | None): 预加载关系，未提供时使用模型默认项

        返回:
        - Sequence[OptimizerExecutionLogModel]: 优化器执行日志模型序列
        """
        return await self.list(search=search, order_by=order_by, preload=preload)

    async def create_obj_log_crud(self, data: OptimizerExecutionLogCreateSchema) -> OptimizerExecutionLogModel | None:
        """
        创建优化器执行日志

        参数:
        - data (OptimizerExecutionLogCreateSchema): 创建优化器执行日志模型

        返回:
        - OptimizerExecutionLogModel | None: 创建的优化器执行日志模型,如果创建失败则为None
        """
        return await self.create(data=data)

    async def delete_obj_log_crud(self, ids: list[int]) -> None:
        """
        删除优化器执行日志

        参数:
        - ids (list[int]): 优化器执行日志ID列表
        """
        return await self.delete(ids=ids)

    async def clear_obj_log_crud(self) -> None:
        """
        清除优化器执行日志

        注意:
        - 此操作会删除所有优化器执行日志,请谨慎操作
        """
        return await self.clear()

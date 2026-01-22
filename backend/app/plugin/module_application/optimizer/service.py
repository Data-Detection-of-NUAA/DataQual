# -*- coding: utf-8 -*-

from app.core.exceptions import CustomException
from app.utils.excel_util import ExcelUtil
from app.api.v1.module_system.auth.schema import AuthSchema
from .crud import OptimizerTaskCRUD, OptimizerResultCRUD, OptimizerExecutionLogCRUD
from .schema import (
    OptimizerTaskCreateSchema,
    OptimizerTaskUpdateSchema,
    OptimizerTaskOutSchema,
    OptimizerResultCreateSchema,
    OptimizerResultUpdateSchema,
    OptimizerResultOutSchema,
    OptimizerExecutionLogOutSchema,
    OptimizerTaskQueryParam,
    OptimizerResultQueryParam,
    OptimizerExecutionLogQueryParam
)


class OptimizerTaskService:
    """
    优化器任务管理模块服务层
    """

    @classmethod
    async def get_task_detail_service(cls, auth: AuthSchema, id: int) -> dict:
        """
        获取优化器任务详情

        参数:
        - auth (AuthSchema): 认证信息模型
        - id (int): 优化器任务ID

        返回:
        - dict: 优化器任务详情字典
        """
        obj = await OptimizerTaskCRUD(auth).get_obj_by_id_crud(id=id)
        if not obj:
            raise CustomException(msg='获取失败，该优化器任务不存在')
        return OptimizerTaskOutSchema.model_validate(obj).model_dump()

    @classmethod
    async def get_task_list_service(cls, auth: AuthSchema, search: OptimizerTaskQueryParam | None = None, order_by: list[dict[str, str]] | None = None) -> list[dict]:
        """
        获取优化器任务列表

        参数:
        - auth (AuthSchema): 认证信息模型
        - search (OptimizerTaskQueryParam | None): 查询参数模型
        - order_by (list[dict[str, str]] | None): 排序参数列表

        返回:
        - list[dict]: 优化器任务详情字典列表
        """
        obj_list = await OptimizerTaskCRUD(auth).get_obj_list_crud(search=search.__dict__, order_by=order_by)
        return [OptimizerTaskOutSchema.model_validate(obj).model_dump() for obj in obj_list]

    @classmethod
    async def create_task_service(cls, auth: AuthSchema, data: OptimizerTaskCreateSchema) -> dict:
        """
        创建优化器任务

        参数:
        - auth (AuthSchema): 认证信息模型
        - data (OptimizerTaskCreateSchema): 优化器任务创建模型

        返回:
        - dict: 优化器任务详情字典
        """
        exist_obj = await OptimizerTaskCRUD(auth).get(name=data.name)
        if exist_obj:
            raise CustomException(msg='创建失败，该优化器任务名称已存在')

        obj = await OptimizerTaskCRUD(auth).create_obj_crud(data=data)
        if not obj:
            raise CustomException(msg='创建失败，该优化器任务不存在')
        return OptimizerTaskOutSchema.model_validate(obj).model_dump()

    @classmethod
    async def update_task_service(cls, auth: AuthSchema, id: int, data: OptimizerTaskUpdateSchema) -> dict:
        """
        更新优化器任务

        参数:
        - auth (AuthSchema): 认证信息模型
        - id (int): 优化器任务ID
        - data (OptimizerTaskUpdateSchema): 优化器任务更新模型

        返回:
        - dict: 优化器任务详情字典
        """
        exist_obj = await OptimizerTaskCRUD(auth).get_obj_by_id_crud(id=id)
        if not exist_obj:
            raise CustomException(msg='更新失败，该优化器任务不存在')

        obj = await OptimizerTaskCRUD(auth).update_obj_crud(id=id, data=data)
        if not obj:
            raise CustomException(msg='更新失败，该优化器任务不存在')
        return OptimizerTaskOutSchema.model_validate(obj).model_dump()

    @classmethod
    async def delete_task_service(cls, auth: AuthSchema, ids: list[int]) -> None:
        """
        删除优化器任务

        参数:
        - auth (AuthSchema): 认证信息模型
        - ids (list[int]): 优化器任务ID列表
        """
        if len(ids) < 1:
            raise CustomException(msg='删除失败，删除对象不能为空')

        for id in ids:
            exist_obj = await OptimizerTaskCRUD(auth).get_obj_by_id_crud(id=id)
            if not exist_obj:
                raise CustomException(msg='删除失败，该优化器任务不存在')

        await OptimizerTaskCRUD(auth).delete_obj_crud(ids=ids)

    @classmethod
    async def clear_task_service(cls, auth: AuthSchema) -> None:
        """
        清空所有优化器任务

        参数:
        - auth (AuthSchema): 认证信息模型
        """
        await OptimizerResultCRUD(auth).clear_obj_result_crud()
        await OptimizerExecutionLogCRUD(auth).clear_obj_log_crud()
        await OptimizerTaskCRUD(auth).clear_obj_crud()

    @classmethod
    async def export_task_service(cls, data_list: list[dict]) -> bytes:
        """
        导出优化器任务列表

        参数:
        - data_list (list[dict]): 优化器任务列表

        返回:
        - bytes: Excel文件字节流
        """
        mapping_dict = {
            'id': '编号',
            'name': '任务名称',
            'description': '任务描述',
            'task_type': '任务类型',
            'priority': '优先级',
            'status': '状态',
            'created_time': '创建时间',
            'updated_time': '更新时间',
            'created_id': '创建者ID',
            'updated_id': '更新者ID',
        }

        # 复制数据并转换状态
        data = data_list.copy()
        status_map = {'0': '待执行', '1': '执行中', '2': '已完成', '3': '失败', '4': '已取消'}
        for item in data:
            item['status'] = status_map.get(item.get('status', '0'), '未知状态')

        return ExcelUtil.export_list2excel(list_data=data, mapping_dict=mapping_dict)

    @classmethod
    async def run_task_service(cls, auth: AuthSchema, id: int, override_config: dict | None = None) -> dict:
        """
        执行优化器任务

        参数:
        - auth (AuthSchema): 认证信息模型
        - id (int): 优化器任务ID
        - override_config (dict | None): 覆盖配置

        返回:
        - dict: 执行结果
        """
        exist_obj = await OptimizerTaskCRUD(auth).get_obj_by_id_crud(id=id)
        if not exist_obj:
            raise CustomException(msg='执行失败，该优化器任务不存在')

        # 更新任务状态为执行中
        await OptimizerTaskCRUD(auth).set_obj_field_crud(ids=[id], status='1')

        # TODO: 实现具体的任务执行逻辑
        # 这里应该根据 task_type 调用不同的优化引擎

        return {
            'task_id': id,
            'task_name': exist_obj.name,
            'status': 'running',
            'message': '任务已开始执行'
        }

    @classmethod
    async def cancel_task_service(cls, auth: AuthSchema, id: int) -> None:
        """
        取消优化器任务

        参数:
        - auth (AuthSchema): 认证信息模型
        - id (int): 优化器任务ID
        """
        exist_obj = await OptimizerTaskCRUD(auth).get_obj_by_id_crud(id=id)
        if not exist_obj:
            raise CustomException(msg='取消失败，该优化器任务不存在')

        # 更新任务状态为已取消
        await OptimizerTaskCRUD(auth).set_obj_field_crud(ids=[id], status='4')


class OptimizerResultService:
    """
    优化器结果管理模块服务层
    """

    @classmethod
    async def get_result_detail_service(cls, auth: AuthSchema, id: int) -> dict:
        """
        获取优化器结果详情

        参数:
        - auth (AuthSchema): 认证信息模型
        - id (int): 优化器结果ID

        返回:
        - dict: 优化器结果详情字典
        """
        obj = await OptimizerResultCRUD(auth).get_obj_result_by_id_crud(id=id)
        if not obj:
            raise CustomException(msg='获取失败，该优化器结果不存在')
        return OptimizerResultOutSchema.model_validate(obj).model_dump()

    @classmethod
    async def get_result_list_service(cls, auth: AuthSchema, search: OptimizerResultQueryParam | None = None, order_by: list[dict[str, str]] | None = None) -> list[dict]:
        """
        获取优化器结果列表

        参数:
        - auth (AuthSchema): 认证信息模型
        - search (OptimizerResultQueryParam | None): 查询参数模型
        - order_by (list[dict[str, str]] | None): 排序参数列表

        返回:
        - list[dict]: 优化器结果详情字典列表
        """
        obj_list = await OptimizerResultCRUD(auth).get_obj_result_list_crud(search=search.__dict__, order_by=order_by)
        return [OptimizerResultOutSchema.model_validate(obj).model_dump() for obj in obj_list]

    @classmethod
    async def create_result_service(cls, auth: AuthSchema, data: OptimizerResultCreateSchema) -> dict:
        """
        创建优化器结果

        参数:
        - auth (AuthSchema): 认证信息模型
        - data (OptimizerResultCreateSchema): 优化器结果创建模型

        返回:
        - dict: 优化器结果详情字典
        """
        # 检查任务是否存在
        task_obj = await OptimizerTaskCRUD(auth).get_obj_by_id_crud(id=data.task_id)
        if not task_obj:
            raise CustomException(msg='创建失败，关联的优化器任务不存在')

        obj = await OptimizerResultCRUD(auth).create_obj_result_crud(data=data)
        if not obj:
            raise CustomException(msg='创建失败，优化器结果创建失败')
        return OptimizerResultOutSchema.model_validate(obj).model_dump()

    @classmethod
    async def update_result_service(cls, auth: AuthSchema, id: int, data: OptimizerResultUpdateSchema) -> dict:
        """
        更新优化器结果

        参数:
        - auth (AuthSchema): 认证信息模型
        - id (int): 优化器结果ID
        - data (OptimizerResultUpdateSchema): 优化器结果更新模型

        返回:
        - dict: 优化器结果详情字典
        """
        exist_obj = await OptimizerResultCRUD(auth).get_obj_result_by_id_crud(id=id)
        if not exist_obj:
            raise CustomException(msg='更新失败，该优化器结果不存在')

        obj = await OptimizerResultCRUD(auth).update_obj_result_crud(id=id, data=data)
        if not obj:
            raise CustomException(msg='更新失败，该优化器结果不存在')
        return OptimizerResultOutSchema.model_validate(obj).model_dump()

    @classmethod
    async def delete_result_service(cls, auth: AuthSchema, ids: list[int]) -> None:
        """
        删除优化器结果

        参数:
        - auth (AuthSchema): 认证信息模型
        - ids (list[int]): 优化器结果ID列表
        """
        if len(ids) < 1:
            raise CustomException(msg='删除失败，删除对象不能为空')

        for id in ids:
            exist_obj = await OptimizerResultCRUD(auth).get_obj_result_by_id_crud(id=id)
            if not exist_obj:
                raise CustomException(msg='删除失败，该优化器结果不存在')

        await OptimizerResultCRUD(auth).delete_obj_result_crud(ids=ids)

    @classmethod
    async def clear_result_service(cls, auth: AuthSchema) -> None:
        """
        清空所有优化器结果

        参数:
        - auth (AuthSchema): 认证信息模型
        """
        await OptimizerResultCRUD(auth).clear_obj_result_crud()

    @classmethod
    async def export_result_service(cls, data_list: list[dict]) -> bytes:
        """
        导出优化器结果列表

        参数:
        - data_list (list[dict]): 优化器结果列表

        返回:
        - bytes: Excel文件字节流
        """
        mapping_dict = {
            'id': '编号',
            'task_id': '任务ID',
            'result_type': '结果类型',
            'score': '优化评分',
            'improvement': '改进百分比',
            'status': '状态',
            'created_time': '创建时间',
            'updated_time': '更新时间',
            'created_id': '创建者ID',
            'updated_id': '更新者ID',
        }

        # 复制数据并转换状态
        data = data_list.copy()
        status_map = {'0': '待应用', '1': '已应用', '2': '已拒绝'}
        for item in data:
            item['status'] = status_map.get(item.get('status', '0'), '未知状态')

        return ExcelUtil.export_list2excel(list_data=data, mapping_dict=mapping_dict)

    @classmethod
    async def apply_result_service(cls, auth: AuthSchema, id: int, apply_mode: str = "auto", confirm: bool = False) -> dict:
        """
        应用优化器结果

        参数:
        - auth (AuthSchema): 认证信息模型
        - id (int): 优化器结果ID
        - apply_mode (str): 应用模式(auto:自动 manual:手动 preview:预览)
        - confirm (bool): 是否确认应用

        返回:
        - dict: 应用结果
        """
        exist_obj = await OptimizerResultCRUD(auth).get_obj_result_by_id_crud(id=id)
        if not exist_obj:
            raise CustomException(msg='应用失败，该优化器结果不存在')

        if apply_mode == "preview":
            return {
                'result_id': id,
                'mode': 'preview',
                'message': '预览模式，不会实际应用',
                'preview_data': exist_obj.result_data
            }

        if not confirm and apply_mode != "auto":
            raise CustomException(msg='应用失败，需要确认才能应用')

        # TODO: 实现具体的应用逻辑
        # 这里应该根据 result_type 调用不同的应用方法

        # 更新结果状态为已应用
        await OptimizerResultCRUD(auth).update_obj_result_crud(
            id=id,
            data=OptimizerResultUpdateSchema(status='1')
        )

        return {
            'result_id': id,
            'mode': apply_mode,
            'status': 'applied',
            'message': '优化结果已成功应用'
        }


class OptimizerExecutionLogService:
    """
    优化器执行日志管理模块服务层
    """

    @classmethod
    async def get_log_detail_service(cls, auth: AuthSchema, id: int) -> dict:
        """
        获取优化器执行日志详情

        参数:
        - auth (AuthSchema): 认证信息模型
        - id (int): 优化器执行日志ID

        返回:
        - dict: 优化器执行日志详情字典
        """
        obj = await OptimizerExecutionLogCRUD(auth).get_obj_log_by_id_crud(id=id)
        if not obj:
            raise CustomException(msg='获取失败，该优化器执行日志不存在')
        return OptimizerExecutionLogOutSchema.model_validate(obj).model_dump()

    @classmethod
    async def get_log_list_service(cls, auth: AuthSchema, search: OptimizerExecutionLogQueryParam | None = None, order_by: list[dict] | None = None) -> list[dict]:
        """
        获取优化器执行日志列表

        参数:
        - auth (AuthSchema): 认证信息模型
        - search (OptimizerExecutionLogQueryParam | None): 查询参数模型
        - order_by (list[dict] | None): 排序参数列表

        返回:
        - list[dict]: 优化器执行日志详情字典列表
        """
        obj_list = await OptimizerExecutionLogCRUD(auth).get_obj_log_list_crud(search=search.__dict__, order_by=order_by)
        return [OptimizerExecutionLogOutSchema.model_validate(obj).model_dump() for obj in obj_list]

    @classmethod
    async def delete_log_service(cls, auth: AuthSchema, ids: list[int]) -> None:
        """
        删除优化器执行日志

        参数:
        - auth (AuthSchema): 认证信息模型
        - ids (list[int]): 优化器执行日志ID列表
        """
        if len(ids) < 1:
            raise CustomException(msg='删除失败，删除对象不能为空')

        for id in ids:
            exist_obj = await OptimizerExecutionLogCRUD(auth).get_obj_log_by_id_crud(id=id)
            if not exist_obj:
                raise CustomException(msg=f'删除失败，该优化器执行日志ID为{id}的记录不存在')

        await OptimizerExecutionLogCRUD(auth).delete_obj_log_crud(ids=ids)

    @classmethod
    async def clear_log_service(cls, auth: AuthSchema) -> None:
        """
        清空优化器执行日志

        参数:
        - auth (AuthSchema): 认证信息模型
        """
        all_logs = await OptimizerExecutionLogCRUD(auth).get_obj_log_list_crud()
        if all_logs:
            ids = [log.id for log in all_logs]
            await OptimizerExecutionLogCRUD(auth).delete_obj_log_crud(ids=ids)

    @classmethod
    async def export_log_service(cls, data_list: list[dict]) -> bytes:
        """
        导出优化器执行日志列表

        参数:
        - data_list (list[dict]): 优化器执行日志列表

        返回:
        - bytes: Excel文件字节流
        """
        mapping_dict = {
            'id': '编号',
            'task_id': '任务ID',
            'execution_time': '执行时间(秒)',
            'status': '执行状态',
            'error_message': '错误信息',
            'created_time': '创建时间',
        }

        data = data_list.copy()
        status_map = {'0': '成功', '1': '失败'}
        for item in data:
            item['status'] = status_map.get(item.get('status', '0'), '未知')

        return ExcelUtil.export_list2excel(list_data=data, mapping_dict=mapping_dict)

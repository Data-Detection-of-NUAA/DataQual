"""
审计规则Service
"""
from typing import List

from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.exceptions import CustomException
from .crud import AuditRuleCRUD
from .schema import AuditRuleCreate, AuditRuleUpdate, AuditRuleQueryParam
from .seeder import ensure_default_rules


class AuditRuleService:
    """审计规则服务类"""

    @staticmethod
    async def list_service(
        params: AuditRuleQueryParam,
        auth: AuthSchema
    ) -> List[dict]:
        """获取规则列表"""
        await ensure_default_rules(auth.db)
        # 构建搜索条件
        search_conditions = {}
        if params.rule_code is not None:
            search_conditions['rule_code'] = params.rule_code
        if params.rule_name is not None:
            search_conditions['rule_name'] = params.rule_name
        if params.rule_type is not None:
            search_conditions['rule_type'] = params.rule_type
        if params.is_active is not None:
            search_conditions['is_active'] = params.is_active

        # 查询数据
        rules = await AuditRuleCRUD(auth).list(
            search=search_conditions,
            order_by=[{'created_time': 'desc'}]
        )

        return [
            {
                'id': rule.id,
                'rule_code': rule.rule_code,
                'rule_name': rule.rule_name,
                'rule_type': rule.rule_type,
                'rule_description': rule.rule_description,
                'rule_expression': rule.rule_expression,
                'severity': rule.severity,
                'is_active': rule.is_active,
                'remark': rule.remark,
                'created_at': str(rule.created_time) if rule.created_time else None,
                'updated_at': str(rule.updated_time) if rule.updated_time else None,
            }
            for rule in rules
        ]

    @staticmethod
    async def get_all_active_rules(auth: AuthSchema) -> List[dict]:
        """获取所有启用的规则（不分页）"""
        await ensure_default_rules(auth.db)
        rules = await AuditRuleCRUD(auth).list(
            search={'is_active': 1},
            order_by=[{'rule_code': 'asc'}]
        )
        return [
            {
                'id': rule.id,
                'rule_code': rule.rule_code,
                'rule_name': rule.rule_name,
                'rule_type': rule.rule_type,
                'rule_description': rule.rule_description,
                'severity': rule.severity,
            }
            for rule in rules
        ]

    @staticmethod
    async def detail_service(id: int, auth: AuthSchema):
        """获取规则详情"""
        await ensure_default_rules(auth.db)
        rule = await AuditRuleCRUD(auth).get(id=id)
        if not rule:
            raise CustomException(msg="规则不存在", code=404)
        return {
            'id': rule.id,
            'rule_code': rule.rule_code,
            'rule_name': rule.rule_name,
            'rule_type': rule.rule_type,
            'rule_description': rule.rule_description,
            'rule_expression': rule.rule_expression,
            'severity': rule.severity,
            'is_active': rule.is_active,
            'remark': rule.remark,
            'created_at': str(rule.created_time) if rule.created_time else None,
            'updated_at': str(rule.updated_time) if rule.updated_time else None,
        }

    @staticmethod
    async def create_service(
        obj_in: AuditRuleCreate,
        auth: AuthSchema
    ):
        """创建规则"""
        await ensure_default_rules(auth.db)
        # 检查规则编码是否已存在
        existing = await AuditRuleCRUD(auth).get(rule_code=obj_in.rule_code)
        if existing:
            raise CustomException(msg="规则编码已存在", code=400)

        # 创建规则
        rule = await AuditRuleCRUD(auth).create(data=obj_in)
        return {
            'id': rule.id,
            'rule_code': rule.rule_code,
            'rule_name': rule.rule_name,
            'rule_type': rule.rule_type,
            'rule_description': rule.rule_description,
            'rule_expression': rule.rule_expression,
            'severity': rule.severity,
            'is_active': rule.is_active,
            'remark': rule.remark,
        }

    @staticmethod
    async def update_service(
        id: int,
        obj_in: AuditRuleUpdate,
        auth: AuthSchema
    ):
        """更新规则"""
        await ensure_default_rules(auth.db)
        # 检查规则是否存在
        rule = await AuditRuleCRUD(auth).get(id=id)
        if not rule:
            raise CustomException(msg="规则不存在", code=404)

        # 如果更新了规则编码,检查是否重复
        if obj_in.rule_code and obj_in.rule_code != rule.rule_code:
            existing = await AuditRuleCRUD(auth).get(rule_code=obj_in.rule_code)
            if existing:
                raise CustomException(msg="规则编码已存在", code=400)

        # 更新规则
        updated_rule = await AuditRuleCRUD(auth).update(id=id, data=obj_in)
        return {
            'id': updated_rule.id,
            'rule_code': updated_rule.rule_code,
            'rule_name': updated_rule.rule_name,
            'rule_type': updated_rule.rule_type,
            'rule_description': updated_rule.rule_description,
            'rule_expression': updated_rule.rule_expression,
            'severity': updated_rule.severity,
            'is_active': updated_rule.is_active,
            'remark': updated_rule.remark,
        }

    @staticmethod
    async def delete_service(id: int, auth: AuthSchema):
        """删除规则"""
        await ensure_default_rules(auth.db)
        # 检查规则是否存在
        rule = await AuditRuleCRUD(auth).get(id=id)
        if not rule:
            raise CustomException(msg="规则不存在", code=404)

        # 删除规则
        await AuditRuleCRUD(auth).delete(ids=[id])

    @staticmethod
    async def delete_batch_service(ids: List[int], auth: AuthSchema) -> None:
        """批量删除规则"""
        if not ids:
            return
        await ensure_default_rules(auth.db)
        await AuditRuleCRUD(auth).delete(ids=ids)

    @staticmethod
    async def batch_update_service(ids: List[int], is_active: int, auth: AuthSchema) -> None:
        """批量更新规则状态"""
        if not ids:
            return
        await ensure_default_rules(auth.db)
        await AuditRuleCRUD(auth).set(ids=ids, is_active=is_active)

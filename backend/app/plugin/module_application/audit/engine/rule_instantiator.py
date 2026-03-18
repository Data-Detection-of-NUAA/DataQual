"""
规则实例化引擎
根据规则模板和参数，生成具体的审计规则实例
"""
from typing import Dict, Any, List
import json
import re


class RuleInstantiator:
    """规则实例化引擎类"""

    @staticmethod
    def instantiate_rule(
        template: Any,
        instance_parameters: Dict[str, Any],
        rule_code: str,
        rule_name: str,
        rule_description: str,
        severity: str,
        regulation_id: int = None
    ) -> Dict[str, Any]:
        """
        从模板实例化一个具体规则

        Args:
            template: 规则模板对象
            instance_parameters: 实例化参数
            rule_code: 规则编码
            rule_name: 规则名称
            rule_description: 规则描述
            severity: 严重等级
            regulation_id: 关联的法规ID

        Returns:
            规则数据字典，可直接用于创建AuditRule
        """
        # 根据模板类型生成rule_type和rule_expression
        rule_type, rule_expression = RuleInstantiator._generate_rule_type_and_expression(
            template, instance_parameters
        )

        return {
            "rule_code": rule_code,
            "rule_name": rule_name,
            "rule_type": rule_type,
            "rule_description": rule_description,
            "rule_expression": rule_expression,
            "severity": severity,
            "is_active": 1,
            "template_id": template.id,
            "instance_parameters": instance_parameters,
            "regulation_id": regulation_id,
            "auto_generated": 1,
            "remark": f"从模板 {template.template_code} 自动生成"
        }

    @staticmethod
    def _generate_rule_type_and_expression(
        template: Any,
        params: Dict[str, Any]
    ) -> tuple[str, Any]:
        """
        根据模板和参数生成rule_type和rule_expression

        Args:
            template: 规则模板
            params: 实例化参数

        Returns:
            (rule_type, rule_expression) 元组
        """
        template_code = template.template_code
        validation_template = template.validation_template

        # 根据模板类型生成对应的rule_type和rule_expression
        if template_code == "FIELD_REQUIRED":
            # 必填验证 -> custom类型
            return "custom", json.dumps({
                "validation_type": "field_required",
                "field_name": params.get("field_name"),
                "error_message": params.get("error_message", f"{params.get('field_display_name', '')}不能为空")
            }, ensure_ascii=False)

        elif template_code == "FIELD_FORMAT_REGEX":
            # 格式验证 -> 根据字段名推断类型
            field_name = params.get("field_name", "").lower()
            regex_pattern = params.get("regex_pattern", "")

            # 智能推断rule_type
            if "email" in field_name or "@" in regex_pattern:
                return "email", None  # 使用内置email验证

            elif "phone" in field_name or "mobile" in field_name:
                return "phone", None  # 使用内置phone验证

            elif "idcard" in field_name or "id_card" in field_name or "identity" in field_name:
                return "idcard", None  # 使用内置idcard验证

            elif "address" in field_name or "addr" in field_name:
                return "address", None  # 使用内置address验证

            elif "name" in field_name and "username" not in field_name:
                return "name", None  # 使用内置name验证

            else:
                # 自定义正则验证
                return "custom", json.dumps({
                    "validation_type": "regex_match",
                    "field_name": params.get("field_name"),
                    "pattern": regex_pattern,
                    "format_description": params.get("format_description", "格式不正确")
                }, ensure_ascii=False)

        elif template_code == "FIELD_ENUM_VALUES":
            # 枚举验证 -> custom类型
            return "custom", json.dumps({
                "validation_type": "enum_required",
                "field_name": params.get("field_name"),
                "allowed_values": params.get("allowed_values", []),
                "case_sensitive": params.get("case_sensitive", True)
            }, ensure_ascii=False)

        elif template_code == "FIELD_LENGTH_LIMIT":
            # 长度限制 -> custom类型
            return "custom", json.dumps({
                "validation_type": "length_limit",
                "field_name": params.get("field_name"),
                "min_length": params.get("min_length"),
                "max_length": params.get("max_length")
            }, ensure_ascii=False)

        elif template_code == "FIELD_NUMERIC_RANGE":
            # 数值范围 -> custom类型
            return "custom", json.dumps({
                "validation_type": "numeric_range",
                "field_name": params.get("field_name"),
                "min_value": params.get("min_value"),
                "max_value": params.get("max_value"),
                "allow_decimal": params.get("allow_decimal", False)
            }, ensure_ascii=False)

        elif template_code == "FIELD_DATE_VALIDATION":
            # 日期验证 -> custom类型
            return "custom", json.dumps({
                "validation_type": "date_validation",
                "field_name": params.get("field_name"),
                "date_format": params.get("date_format", "YYYY-MM-DD"),
                "min_date": params.get("min_date"),
                "max_date": params.get("max_date")
            }, ensure_ascii=False)

        elif template_code == "FIELD_NO_PII_KEYWORDS":
            # 敏感词检测 -> custom类型
            return "custom", json.dumps({
                "validation_type": "no_pii_keywords",
                "field_name": params.get("field_name"),
                "blocked_keywords": params.get("blocked_keywords", []),
                "case_sensitive": params.get("case_sensitive", False)
            }, ensure_ascii=False)

        elif template_code == "FIELD_DEPENDENCY_CHECK":
            # 依赖关系 -> custom类型
            return "custom", json.dumps({
                "validation_type": "field_dependency",
                "source_field": params.get("source_field"),
                "dependent_field": params.get("dependent_field"),
                "condition": params.get("condition", "not_empty"),
                "condition_value": params.get("condition_value")
            }, ensure_ascii=False)

        elif template_code == "FIELD_UNIQUE_CHECK":
            # 唯一性检查 -> custom类型
            return "custom", json.dumps({
                "validation_type": "uniqueness_check",
                "field_name": params.get("field_name"),
                "ignore_empty": params.get("ignore_empty", True)
            }, ensure_ascii=False)

        elif template_code == "FIELD_CROSS_DATASET_REFERENCE":
            # 跨数据集引用 -> custom类型
            return "custom", json.dumps({
                "validation_type": "reference_check",
                "field_name": params.get("field_name"),
                "reference_dataset": params.get("reference_dataset"),
                "reference_field": params.get("reference_field"),
                "allow_empty": params.get("allow_empty", False)
            }, ensure_ascii=False)

        else:
            # 默认为custom类型
            return "custom", json.dumps({
                "validation_type": "generic",
                "parameters": params
            }, ensure_ascii=False)

    @staticmethod
    def batch_instantiate_rules(
        parsed_requirements: List[Dict[str, Any]],
        templates_map: Dict[int, Any],
        regulation_id: int = None
    ) -> List[Dict[str, Any]]:
        """
        批量实例化规则

        Args:
            parsed_requirements: 解析的法规要求列表
            templates_map: 模板ID到模板对象的映射
            regulation_id: 关联的法规ID

        Returns:
            规则数据列表
        """
        rules = []

        for req in parsed_requirements:
            template_id = req.get("template_id")
            template = templates_map.get(template_id)

            if not template:
                print(f"模板ID {template_id} 不存在，跳过")
                continue

            try:
                rule_data = RuleInstantiator.instantiate_rule(
                    template=template,
                    instance_parameters=req.get("instance_parameters", {}),
                    rule_code=req.get("rule_code", ""),
                    rule_name=req.get("rule_name", ""),
                    rule_description=req.get("rule_description", ""),
                    severity=req.get("severity", template.default_severity),
                    regulation_id=regulation_id
                )
                rules.append(rule_data)
            except Exception as e:
                print(f"实例化规则失败: {str(e)}")
                continue

        return rules

    @staticmethod
    def validate_instantiation(
        template: Any,
        instance_parameters: Dict[str, Any]
    ) -> tuple[bool, str]:
        """
        验证实例化参数是否符合模板要求

        Args:
            template: 规则模板
            instance_parameters: 实例化参数

        Returns:
            (is_valid, error_message)
        """
        params_schema = template.parameters_schema
        required_params = params_schema.get("required", [])

        # 检查必需参数
        for param in required_params:
            if param not in instance_parameters:
                return False, f"缺少必需参数: {param}"

            value = instance_parameters[param]
            if value is None or (isinstance(value, str) and not value.strip()):
                return False, f"参数 {param} 不能为空"

        # 检查参数类型（简单验证）
        properties = params_schema.get("properties", {})
        for param, value in instance_parameters.items():
            if param not in properties:
                continue

            expected_type = properties[param].get("type")
            if expected_type == "string" and not isinstance(value, str):
                return False, f"参数 {param} 必须是字符串类型"
            elif expected_type == "integer" and not isinstance(value, int):
                return False, f"参数 {param} 必须是整数类型"
            elif expected_type == "number" and not isinstance(value, (int, float)):
                return False, f"参数 {param} 必须是数值类型"
            elif expected_type == "boolean" and not isinstance(value, bool):
                return False, f"参数 {param} 必须是布尔类型"
            elif expected_type == "array" and not isinstance(value, list):
                return False, f"参数 {param} 必须是数组类型"

        return True, ""

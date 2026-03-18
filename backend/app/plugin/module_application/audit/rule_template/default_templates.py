"""
默认规则模板定义
这些模板是可参数化的通用规则，可以通过AI解析法规后实例化为具体规则
"""

DEFAULT_RULE_TEMPLATES = [
    {
        "template_code": "FIELD_REQUIRED",
        "template_name": "字段必填验证",
        "template_category": "field_validation",
        "template_description": "验证指定字段不能为空、null或仅包含空格。适用于必填字段的合规要求。",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "field_name": {
                    "type": "string",
                    "description": "要验证的字段名称",
                    "examples": ["email", "phone", "consent_flag"]
                },
                "field_display_name": {
                    "type": "string",
                    "description": "字段的显示名称（用于错误消息）",
                    "examples": ["邮箱", "手机号", "用户同意标识"]
                },
                "error_message": {
                    "type": "string",
                    "description": "自定义错误消息（可选）",
                    "default": "{field_display_name}不能为空"
                }
            },
            "required": ["field_name", "field_display_name"]
        },
        "validation_template": {
            "type": "field_required",
            "logic": "check_not_empty_and_not_null"
        },
        "default_severity": "error",
        "tags": {"category": "基础验证", "gdpr": True, "common": True},
        "is_active": 1,
        "remark": "最常用的模板，用于验证必填字段"
    },
    {
        "template_code": "FIELD_FORMAT_REGEX",
        "template_name": "字段格式正则验证",
        "template_category": "format_check",
        "template_description": "使用正则表达式验证字段格式。适用于各种格式要求（邮箱、手机号、身份证等）。",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "field_name": {
                    "type": "string",
                    "description": "要验证的字段名称"
                },
                "field_display_name": {
                    "type": "string",
                    "description": "字段的显示名称"
                },
                "regex_pattern": {
                    "type": "string",
                    "description": "正则表达式",
                    "examples": [
                        "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                        "^1[3-9]\\d{9}$"
                    ]
                },
                "format_description": {
                    "type": "string",
                    "description": "格式说明（用于错误消息）",
                    "examples": ["有效的邮箱地址", "11位中国大陆手机号"]
                }
            },
            "required": ["field_name", "field_display_name", "regex_pattern", "format_description"]
        },
        "validation_template": {
            "type": "regex_match",
            "logic": "validate_field_against_regex"
        },
        "default_severity": "error",
        "tags": {"category": "格式验证", "gdpr": True, "flexible": True},
        "is_active": 1,
        "remark": "通用格式验证模板，支持任意正则表达式"
    },
    {
        "template_code": "FIELD_ENUM_VALUES",
        "template_name": "字段枚举值限制",
        "template_category": "field_validation",
        "template_description": "验证字段值必须在指定的枚举列表中。适用于状态、类型等有限选项的字段。",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "field_name": {
                    "type": "string",
                    "description": "要验证的字段名称"
                },
                "field_display_name": {
                    "type": "string",
                    "description": "字段的显示名称"
                },
                "allowed_values": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "允许的值列表",
                    "examples": [["Y", "N"], ["train", "eval", "inference_log"]]
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "是否区分大小写",
                    "default": True
                }
            },
            "required": ["field_name", "field_display_name", "allowed_values"]
        },
        "validation_template": {
            "type": "enum_validation",
            "logic": "check_value_in_allowed_list"
        },
        "default_severity": "error",
        "tags": {"category": "业务验证", "gdpr": True},
        "is_active": 1,
        "remark": "用于验证枚举字段，如同意标识、用途标签等"
    },
    {
        "template_code": "FIELD_LENGTH_LIMIT",
        "template_name": "字段长度限制",
        "template_category": "field_validation",
        "template_description": "验证字段长度在指定范围内。适用于姓名、地址等有长度要求的文本字段。",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "field_name": {
                    "type": "string",
                    "description": "要验证的字段名称"
                },
                "field_display_name": {
                    "type": "string",
                    "description": "字段的显示名称"
                },
                "min_length": {
                    "type": "integer",
                    "description": "最小长度（可选）",
                    "minimum": 0
                },
                "max_length": {
                    "type": "integer",
                    "description": "最大长度（可选）",
                    "minimum": 1
                }
            },
            "required": ["field_name", "field_display_name"]
        },
        "validation_template": {
            "type": "length_check",
            "logic": "validate_string_length"
        },
        "default_severity": "warning",
        "tags": {"category": "数据质量", "gdpr": False},
        "is_active": 1,
        "remark": "用于验证文本长度，如姓名2-50字符"
    },
    {
        "template_code": "FIELD_NUMERIC_RANGE",
        "template_name": "数值范围验证",
        "template_category": "field_validation",
        "template_description": "验证数值字段在指定范围内。适用于年龄、保留期限等数值型合规要求。",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "field_name": {
                    "type": "string",
                    "description": "要验证的字段名称"
                },
                "field_display_name": {
                    "type": "string",
                    "description": "字段的显示名称"
                },
                "min_value": {
                    "type": "number",
                    "description": "最小值（可选）"
                },
                "max_value": {
                    "type": "number",
                    "description": "最大值（可选）"
                },
                "allow_decimal": {
                    "type": "boolean",
                    "description": "是否允许小数",
                    "default": False
                }
            },
            "required": ["field_name", "field_display_name"]
        },
        "validation_template": {
            "type": "numeric_range",
            "logic": "validate_number_in_range"
        },
        "default_severity": "warning",
        "tags": {"category": "业务验证", "gdpr": True},
        "is_active": 1,
        "remark": "用于数值范围验证，如保留期限0-24个月"
    },
    {
        "template_code": "FIELD_DATE_VALIDATION",
        "template_name": "日期字段验证",
        "template_category": "format_check",
        "template_description": "验证日期字段格式和有效性。适用于出生日期、同意日期等时间相关字段。",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "field_name": {
                    "type": "string",
                    "description": "要验证的字段名称"
                },
                "field_display_name": {
                    "type": "string",
                    "description": "字段的显示名称"
                },
                "date_format": {
                    "type": "string",
                    "description": "日期格式",
                    "examples": ["YYYY-MM-DD", "YYYY/MM/DD", "DD-MM-YYYY"],
                    "default": "YYYY-MM-DD"
                },
                "min_date": {
                    "type": "string",
                    "description": "最早日期（可选）",
                    "examples": ["1900-01-01", "today-100y"]
                },
                "max_date": {
                    "type": "string",
                    "description": "最晚日期（可选）",
                    "examples": ["2100-12-31", "today"]
                }
            },
            "required": ["field_name", "field_display_name"]
        },
        "validation_template": {
            "type": "date_validation",
            "logic": "validate_date_format_and_range"
        },
        "default_severity": "error",
        "tags": {"category": "格式验证", "gdpr": True},
        "is_active": 1,
        "remark": "用于日期格式和范围验证"
    },
    {
        "template_code": "FIELD_NO_PII_KEYWORDS",
        "template_name": "字段不含敏感词",
        "template_category": "data_quality",
        "template_description": "验证字段不包含指定的敏感关键词。适用于数据最小化和隐私保护。",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "field_name": {
                    "type": "string",
                    "description": "要验证的字段名称"
                },
                "field_display_name": {
                    "type": "string",
                    "description": "字段的显示名称"
                },
                "blocked_keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "禁止出现的关键词列表",
                    "examples": [["密码", "password", "身份证", "idcard"]]
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "是否区分大小写",
                    "default": False
                }
            },
            "required": ["field_name", "field_display_name", "blocked_keywords"]
        },
        "validation_template": {
            "type": "keyword_block",
            "logic": "check_no_sensitive_keywords"
        },
        "default_severity": "warning",
        "tags": {"category": "隐私保护", "gdpr": True},
        "is_active": 1,
        "remark": "用于检测字段中不应出现的敏感信息"
    },
    {
        "template_code": "FIELD_DEPENDENCY_CHECK",
        "template_name": "字段依赖关系验证",
        "template_category": "business_rule",
        "template_description": "验证字段间的依赖关系。例如：如果字段A有值，则字段B也必须有值。",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "source_field": {
                    "type": "string",
                    "description": "源字段名称"
                },
                "source_field_display": {
                    "type": "string",
                    "description": "源字段显示名称"
                },
                "dependent_field": {
                    "type": "string",
                    "description": "依赖字段名称"
                },
                "dependent_field_display": {
                    "type": "string",
                    "description": "依赖字段显示名称"
                },
                "condition": {
                    "type": "string",
                    "description": "触发条件",
                    "enum": ["not_empty", "equals", "contains"],
                    "default": "not_empty"
                },
                "condition_value": {
                    "type": "string",
                    "description": "条件值（当condition为equals或contains时）"
                }
            },
            "required": ["source_field", "source_field_display", "dependent_field", "dependent_field_display"]
        },
        "validation_template": {
            "type": "field_dependency",
            "logic": "validate_field_dependency"
        },
        "default_severity": "error",
        "tags": {"category": "业务规则", "gdpr": True},
        "is_active": 1,
        "remark": "用于验证字段间的业务依赖关系，如合法性基础与用途的一致性"
    },
    {
        "template_code": "FIELD_UNIQUE_CHECK",
        "template_name": "字段唯一性验证",
        "template_category": "data_quality",
        "template_description": "验证字段值在数据集中唯一（无重复）。适用于用户ID、订单号等唯一标识。",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "field_name": {
                    "type": "string",
                    "description": "要验证的字段名称"
                },
                "field_display_name": {
                    "type": "string",
                    "description": "字段的显示名称"
                },
                "ignore_empty": {
                    "type": "boolean",
                    "description": "是否忽略空值",
                    "default": True
                }
            },
            "required": ["field_name", "field_display_name"]
        },
        "validation_template": {
            "type": "uniqueness_check",
            "logic": "validate_no_duplicates"
        },
        "default_severity": "error",
        "tags": {"category": "数据质量", "gdpr": False},
        "is_active": 1,
        "remark": "用于验证唯一性字段不重复"
    },
    {
        "template_code": "FIELD_CROSS_DATASET_REFERENCE",
        "template_name": "跨数据集引用验证",
        "template_category": "business_rule",
        "template_description": "验证字段值必须在另一个数据集/字典中存在。适用于外键、参照完整性等场景。",
        "parameters_schema": {
            "type": "object",
            "properties": {
                "field_name": {
                    "type": "string",
                    "description": "要验证的字段名称"
                },
                "field_display_name": {
                    "type": "string",
                    "description": "字段的显示名称"
                },
                "reference_dataset": {
                    "type": "string",
                    "description": "参考数据集/表名称"
                },
                "reference_field": {
                    "type": "string",
                    "description": "参考字段名称"
                },
                "allow_empty": {
                    "type": "boolean",
                    "description": "是否允许空值",
                    "default": False
                }
            },
            "required": ["field_name", "field_display_name", "reference_dataset", "reference_field"]
        },
        "validation_template": {
            "type": "reference_check",
            "logic": "validate_reference_exists"
        },
        "default_severity": "error",
        "tags": {"category": "参照完整性", "gdpr": False},
        "is_active": 1,
        "remark": "用于验证外键引用完整性"
    }
]

"""
Default GDPR-inspired audit rules that can be loaded into the rule pool.
The rules focus on validating typical PII字段 that常见 in GDPR合规审计场景, and
they intentionally使用现有的 rule_type（email/phone/idcard/custom）以便现有的
AuditEngine 可以直接执行。
"""

DEFAULT_GDPR_RULES = [
    {
        "rule_code": "GDPR-EMAIL-FORMAT",
        "rule_name": "电子邮箱格式符合GDPR",
        "rule_type": "email",
        "rule_description": (
            "GDPR 第5条强调数据准确性。该规则确保 email 字段提供合法邮箱，"
            "可用于验证营销同意、通知和撤回链路。"
        ),
        "rule_expression": None,
        "severity": "error",
        "is_active": 1,
        "remark": "GDPR Article 5(1)(d) - Data accuracy"
    },
    {
        "rule_code": "GDPR-PHONE-FORMAT",
        "rule_name": "手机号格式符合GDPR联系人要求",
        "rule_type": "phone",
        "rule_description": (
            "GDPR 中数据主体联络必须可靠，该规则限制手机号仅接受中国大陆 "
            "段位，确保能够联系到数据主体以履行告知/撤回权利。"
        ),
        "rule_expression": None,
        "severity": "warning",
        "is_active": 1,
        "remark": "GDPR Article 12 - Transparent communication"
    },
    {
        "rule_code": "GDPR-IDCARD-FORMAT",
        "rule_name": "身份证号格式校验",
        "rule_type": "idcard",
        "rule_description": (
            "对特殊类别识别信息进行格式校验，减少录入错误带来的越权访问风险。"
        ),
        "rule_expression": None,
        "severity": "error",
        "is_active": 1,
        "remark": "GDPR Article 9 - Special categories of data"
    },
    {
        "rule_code": "GDPR-CONSENT-FLAG",
        "rule_name": "同意标识仅允许Y/N",
        "rule_type": "custom",
        "rule_description": (
            "记录数据主体是否提供明确同意。只有 Y/N 合法值可以通过，"
            "保证能够追溯 consent 状态。"
        ),
        "rule_expression": {
            "field_name": "consent_flag",
            "pattern": "^(Y|N)$"
        },
        "severity": "error",
        "is_active": 1,
        "remark": "GDPR Article 7 - Conditions for consent"
    },
    {
        "rule_code": "GDPR-RETENTION-PERIOD",
        "rule_name": "数据保留周期不得超过24个月",
        "rule_type": "custom",
        "rule_description": (
            "GDPR 第5条(1)(e) 要求在达到目的后删除数据。该规则假定字段 "
            "`retention_months` 记录保留月数，只允许 0-24。"
        ),
        "rule_expression": {
            "field_name": "retention_months",
            "pattern": r"^([0-9]|1[0-9]|2[0-4])$"
        },
        "severity": "warning",
        "is_active": 1,
        "remark": "GDPR Article 5(1)(e) - Storage limitation"
    },
    {
        "rule_code": "GDPR-DATA-MINIMIZATION",
        "rule_name": "最少化上传字段不得包含空格串",
        "rule_type": "custom",
        "rule_description": (
            "GDPR 要求只收集必要字段。该校验确保 `data_field` 不允许提交仅包含空格，"
            "避免伪造占位符。"
        ),
        "rule_expression": {
            "field_name": "data_field",
            "pattern": r"^(?!\\s*$).+"
        },
        "severity": "info",
        "is_active": 1,
        "remark": "GDPR Article 5(1)(c) - Data minimisation"
    },
    {
        "rule_code": "PURPOSE-TAG-REQUIRED",
        "rule_name": "用途标签必填且合法枚举",
        "rule_type": "custom",
        "rule_description": "所有训练/评估/推理日志必须显式填写 purpose_tag，并且值仅允许 train/eval/inference_log。",
        "rule_expression": {
            "custom_type": "enum_required",
            "field_name": "purpose_tag",
            "allowed_values": ["train", "eval", "inference_log"],
            "required": True
        },
        "severity": "error",
        "is_active": 1,
        "remark": "GDPR Article 5(1)(b) - Purpose limitation"
    },
    {
        "rule_code": "LAWFUL-BASIS-CONSISTENCY",
        "rule_name": "合法性基础与用途一致",
        "rule_type": "custom",
        "rule_description": "当 consent=Y 时必须同时记录 consent_time/consent_version/consent_scope；当 consent=withdrawn 时禁止继续 train 目的。",
        "rule_expression": {
            "custom_type": "lawful_basis_consistency",
            "purpose_field": "purpose_tag",
            "lawful_basis_field": "lawful_basis_tag",
            "require_lawful_basis_for": ["train", "eval", "inference_log"],
            "subject_field": "subject_id",
            "consent_field": "consent_flag",
            "consent_positive_values": ["Y", "granted"],
            "consent_withdrawn_values": ["withdrawn", "N"],
            "required_fields_when_consent": ["consent_time", "consent_version", "consent_scope"],
            "forbidden_purpose_when_withdrawn": ["train"]
        },
        "severity": "error",
        "is_active": 1,
        "remark": "GDPR Articles 6 & 7 - Lawfulness of processing and consent"
    },
    {
        "rule_code": "DSAR-ERASURE-CASCADE",
        "rule_name": "DSAR 删除请求必须级联",
        "rule_type": "custom",
        "rule_description": "当 dsar_action 标记为 erasure 时，需要同时确保向量库、索引与操作日志均删除完毕并留存确认。",
        "rule_expression": {
            "custom_type": "erasure_cascade",
            "trigger_field": "dsar_action",
            "trigger_value": "erasure",
            "subject_field": "subject_id",
            "request_id_field": "dsar_request_id",
            "status_field": "dsar_status",
            "status_fields": {
                "start": "erasure_started_at",
                "end": "erasure_completed_at",
                "failure_reason": "erasure_failure_reason"
            },
            "hit_fields": {
                "before": "vector_hits_before",
                "after": "vector_hits_after"
            },
            "required_confirmations": [
                {"field": "raw_deleted", "label": "Raw data purged"},
                {"field": "feature_deleted", "label": "Feature store purged"},
                {"field": "vector_store_deleted", "label": "Vector/index removed"},
                {"field": "log_scrubbed", "label": "Inference logs scrubbed"}
            ]
        },
        "severity": "warning",
        "is_active": 1,
        "remark": "GDPR Article 17 - Right to erasure"
    },
    {
        "rule_code": "TRAIN-FIELD-WHITELIST",
        "rule_name": "训练字段白名单并阻断 PII",
        "rule_type": "custom",
        "rule_description": "训练输入仅允许提交白名单字段，且包含 email/phone/idcard/address/bank_account 等 PII 字段时必须硬性拦截。",
        "rule_expression": {
            "custom_type": "train_field_whitelist",
            "target_field": "train_inputs",
            "allowed_fields": ["prompt", "completion", "label", "metadata"],
            "pii_fields_block": ["email", "phone", "idcard", "address", "bank_account"]
        },
        "severity": "error",
        "is_active": 1,
        "remark": "GDPR Article 25 - Data protection by design"
    }
]

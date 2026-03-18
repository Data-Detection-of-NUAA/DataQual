"""
审计引擎
核心审计逻辑，支持多种规则类型的数据验证
"""
import json
import re
from collections import Counter, defaultdict
from typing import List, Dict, Any, Optional


class AuditEngine:
    """审计引擎类"""

    @staticmethod
    def audit_dataset(dataset_records: List[Dict[str, Any]], rules: List) -> Dict[str, Any]:
        """
        执行数据集审计

        Args:
            dataset_records: 数据集记录列表
            rules: 审计规则列表

        Returns:
            审计结果
        """
        total_records = len(dataset_records)
        errors: List[Dict[str, Any]] = []
        error_record_set = set()
        rule_contexts: Dict[str, Dict[str, Any]] = {}
        rule_configs: Dict[str, Dict[str, Any]] = {}

        for rule in rules:
            rule_contexts[rule.rule_code] = {"rule": rule, "context": {}}
            if rule.rule_type == 'custom' and rule.rule_expression:
                try:
                    rule_configs[rule.rule_code] = json.loads(rule.rule_expression)
                except json.JSONDecodeError:
                    rule_configs[rule.rule_code] = {}

        for idx, record in enumerate(dataset_records):
            row_number = idx + 1

            for rule in rules:
                context = rule_contexts[rule.rule_code]["context"]
                rule_config = rule_configs.get(rule.rule_code)
                rule_errors = AuditEngine._validate_record(record, rule, row_number, context, rule_config)
                errors.extend(rule_errors)

                if rule_errors:
                    error_record_set.add(row_number)

        rule_statistics = AuditEngine._build_rule_statistics(rule_contexts, total_records)

        return {
            "total_records": total_records,
            "error_records": len(error_record_set),
            "errors": errors,
            "rule_statistics": rule_statistics
        }

    @staticmethod
    def _validate_record(
        record: Dict[str, Any],
        rule,
        row_number: int,
        context: Dict[str, Any],
        rule_config: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        验证单条记录

        Args:
            record: 数据记录
            rule: 审计规则
            row_number: 行号

        Returns:
            错误列表
        """
        errors = []

        # 根据规则类型进行不同的验证
        if rule.rule_type == 'email':
            errors.extend(AuditEngine._validate_email(record, rule, row_number, context))
        elif rule.rule_type == 'phone':
            errors.extend(AuditEngine._validate_phone(record, rule, row_number, context))
        elif rule.rule_type == 'idcard':
            errors.extend(AuditEngine._validate_idcard(record, rule, row_number, context))
        elif rule.rule_type == 'address':
            errors.extend(AuditEngine._validate_address(record, rule, row_number, context))
        elif rule.rule_type == 'name':
            errors.extend(AuditEngine._validate_name(record, rule, row_number, context))
        elif rule.rule_type == 'custom':
            errors.extend(AuditEngine._validate_custom(record, rule, row_number, context, rule_config))

        return errors

    @staticmethod
    def _validate_email(record: Dict[str, Any], rule, row_number: int, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """验证邮箱字段"""
        errors = []
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        context.setdefault('validator', 'email')
        context.setdefault('candidate_count', 0)
        context.setdefault('valid_count', 0)
        context.setdefault('invalid_count', 0)

        # 遍历所有字段，查找可能的邮箱字段
        for field_name, value in record.items():
            if value and isinstance(value, str):
                # 如果字段名包含email或邮箱，或者值看起来像邮箱
                if 'email' in field_name.lower() or 'mail' in field_name.lower() or '@' in value:
                    context['candidate_count'] += 1
                    if not re.match(email_pattern, value):
                        # 找到错误位置
                        start_pos = 0
                        end_pos = len(value)
                        context['invalid_count'] += 1
                        context.setdefault('invalid_samples', []).append(
                            AuditEngine._sample_record(record, row_number, field_name, value, "邮箱格式不符合要求")
                        )

                        errors.append({
                            "error_type": "data",
                            "row_number": row_number,
                            "column_name": field_name,
                            "original_value": value,
                            "error_message": f"邮箱格式不正确: {rule.rule_description}",
                            "rule_id": rule.id,
                            "severity": rule.severity,
                            "start_position": start_pos,
                            "end_position": end_pos
                        })
                    else:
                        context['valid_count'] += 1

        return errors

    @staticmethod
    def _validate_phone(record: Dict[str, Any], rule, row_number: int, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """验证手机号字段"""
        errors = []
        phone_pattern = r'^1[3-9]\d{9}$'
        context.setdefault('validator', 'phone')
        context.setdefault('candidate_count', 0)
        context.setdefault('valid_count', 0)
        context.setdefault('invalid_count', 0)

        for field_name, value in record.items():
            if value and isinstance(value, (str, int)):
                value_str = str(value)
                if 'phone' in field_name.lower() or 'mobile' in field_name.lower() or '手机' in field_name or 'tel' in field_name.lower():
                    context['candidate_count'] += 1
                    if not re.match(phone_pattern, value_str):
                        context['invalid_count'] += 1
                        context.setdefault('invalid_samples', []).append(
                            AuditEngine._sample_record(record, row_number, field_name, value_str, "手机号格式异常")
                        )
                        errors.append({
                            "error_type": "data",
                            "row_number": row_number,
                            "column_name": field_name,
                            "original_value": value_str,
                            "error_message": f"手机号格式不正确: {rule.rule_description}",
                            "rule_id": rule.id,
                            "severity": rule.severity,
                            "start_position": 0,
                            "end_position": len(value_str)
                        })
                    else:
                        context['valid_count'] += 1

        return errors

    @staticmethod
    def _validate_idcard(record: Dict[str, Any], rule, row_number: int, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """验证身份证字段"""
        errors = []
        idcard_pattern = r'^\d{17}[\dXx]$'
        context.setdefault('validator', 'idcard')
        context.setdefault('candidate_count', 0)
        context.setdefault('valid_count', 0)
        context.setdefault('invalid_count', 0)

        for field_name, value in record.items():
            if value and isinstance(value, (str, int)):
                value_str = str(value)
                if 'idcard' in field_name.lower() or 'id_card' in field_name.lower() or '身份证' in field_name or 'identity' in field_name.lower():
                    context['candidate_count'] += 1
                    if not re.match(idcard_pattern, value_str):
                        context['invalid_count'] += 1
                        context.setdefault('invalid_samples', []).append(
                            AuditEngine._sample_record(record, row_number, field_name, value_str, "证件号格式异常")
                        )
                        errors.append({
                            "error_type": "data",
                            "row_number": row_number,
                            "column_name": field_name,
                            "original_value": value_str,
                            "error_message": f"身份证号格式不正确: {rule.rule_description}",
                            "rule_id": rule.id,
                            "severity": rule.severity,
                            "start_position": 0,
                            "end_position": len(value_str)
                        })
                    else:
                        context['valid_count'] += 1

        return errors

    @staticmethod
    def _validate_address(record: Dict[str, Any], rule, row_number: int, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """验证地址字段"""
        errors = []

        for field_name, value in record.items():
            if value and isinstance(value, str):
                if 'address' in field_name.lower() or 'addr' in field_name.lower() or '地址' in field_name:
                    # 检查地址是否过短
                    if len(value.strip()) < 5:
                        errors.append({
                            "error_type": "data",
                            "row_number": row_number,
                            "column_name": field_name,
                            "original_value": value,
                            "error_message": f"地址信息过短，可能不完整: {rule.rule_description}",
                            "rule_id": rule.id,
                            "severity": rule.severity,
                            "start_position": 0,
                            "end_position": len(value)
                        })

        return errors

    @staticmethod
    def _validate_name(record: Dict[str, Any], rule, row_number: int, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """验证姓名字段"""
        errors = []
        # 中文姓名：2-4个汉字
        name_pattern = r'^[\u4e00-\u9fa5]{2,4}$'

        for field_name, value in record.items():
            if value and isinstance(value, str):
                if 'name' in field_name.lower() or '姓名' in field_name or '名称' in field_name:
                    if not re.match(name_pattern, value.strip()):
                        errors.append({
                            "error_type": "data",
                            "row_number": row_number,
                            "column_name": field_name,
                            "original_value": value,
                            "error_message": f"姓名格式不正确（应为2-4个汉字）: {rule.rule_description}",
                            "rule_id": rule.id,
                            "severity": rule.severity,
                            "start_position": 0,
                            "end_position": len(value)
                        })

        return errors

    @staticmethod
    def _validate_custom(
        record: Dict[str, Any],
        rule,
        row_number: int,
        context: Dict[str, Any],
        rule_config: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """验证自定义规则"""
        errors: List[Dict[str, Any]] = []
        config = rule_config or {}

        # 支持两种配置方式：custom_type（旧）和validation_type（新）
        validation_type = config.get('validation_type') or config.get('custom_type')

        # 新的规则模板实例化验证类型
        if validation_type == 'field_required':
            errors.extend(
                AuditEngine._validate_field_required(record, rule, row_number, context, config)
            )
        elif validation_type == 'regex_match':
            errors.extend(
                AuditEngine._validate_regex_match(record, rule, row_number, context, config)
            )
        elif validation_type == 'enum_validation':
            errors.extend(
                AuditEngine._validate_enum_validation(record, rule, row_number, context, config)
            )
        elif validation_type == 'length_limit':
            errors.extend(
                AuditEngine._validate_length_limit(record, rule, row_number, context, config)
            )
        elif validation_type == 'numeric_range':
            errors.extend(
                AuditEngine._validate_numeric_range(record, rule, row_number, context, config)
            )
        elif validation_type == 'date_validation':
            errors.extend(
                AuditEngine._validate_date_validation(record, rule, row_number, context, config)
            )
        elif validation_type == 'no_pii_keywords':
            errors.extend(
                AuditEngine._validate_no_pii_keywords(record, rule, row_number, context, config)
            )
        elif validation_type == 'field_dependency':
            errors.extend(
                AuditEngine._validate_field_dependency(record, rule, row_number, context, config)
            )
        elif validation_type == 'uniqueness_check':
            errors.extend(
                AuditEngine._validate_uniqueness_check(record, rule, row_number, context, config)
            )
        # 旧的验证类型（保持兼容性）
        elif validation_type == 'enum_required':
            context.setdefault('custom_type', 'enum_required')
            errors.extend(
                AuditEngine._validate_enum_required(record, rule, row_number, context, config)
            )
        elif validation_type == 'lawful_basis_consistency':
            context.setdefault('custom_type', 'lawful_basis_consistency')
            errors.extend(
                AuditEngine._validate_lawful_basis_consistency(record, rule, row_number, context, config)
            )
        elif validation_type == 'erasure_cascade':
            context.setdefault('custom_type', 'erasure_cascade')
            errors.extend(
                AuditEngine._validate_erasure_cascade(record, rule, row_number, context, config)
            )
        elif validation_type == 'train_field_whitelist':
            context.setdefault('custom_type', 'train_field_whitelist')
            errors.extend(
                AuditEngine._validate_train_field_whitelist(record, rule, row_number, context, config)
            )
        else:
            # 默认使用pattern验证
            errors.extend(
                AuditEngine._validate_custom_pattern(record, rule, row_number, context, config)
            )

        return errors


    @staticmethod
    def _validate_enum_required(
        record: Dict[str, Any],
        rule,
        row_number: int,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        errors: List[Dict[str, Any]] = []
        field_name = config.get('field_name')
        allowed_values = config.get('allowed_values') or []
        required = config.get('required', False)
        if not field_name:
            return errors

        context.setdefault('field_name', field_name)
        context.setdefault('allowed_values', allowed_values)
        distribution: Counter = context.setdefault('distribution', Counter())
        invalid_records = context.setdefault('invalid_records', [])

        raw_value = record.get(field_name)
        normalized_value = AuditEngine._normalize_value(raw_value)

        if normalized_value is None:
            if required:
                message = f"{field_name} ???????????"
                invalid_records.append(
                    AuditEngine._sample_record(record, row_number, field_name, raw_value, message)
                )
                errors.append({
                    "error_type": "data",
                    "row_number": row_number,
                    "column_name": field_name,
                    "original_value": raw_value,
                    "error_message": f"{field_name} ????????? {allowed_values} ?",
                    "rule_id": rule.id,
                    "severity": rule.severity
                })
        else:
            if normalized_value in allowed_values:
                distribution[normalized_value] += 1
            else:
                message = f"???? {normalized_value} ?????? {allowed_values} ?"
                invalid_records.append(
                    AuditEngine._sample_record(record, row_number, field_name, normalized_value, message)
                )
                errors.append({
                    "error_type": "data",
                    "row_number": row_number,
                    "column_name": field_name,
                    "original_value": normalized_value,
                    "error_message": message,
                    "rule_id": rule.id,
                    "severity": rule.severity
                })

        return errors

    @staticmethod
    def _validate_lawful_basis_consistency(
        record: Dict[str, Any],
        rule,
        row_number: int,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        errors: List[Dict[str, Any]] = []
        purpose_field = config.get('purpose_field', 'purpose_tag')
        lawful_field = config.get('lawful_basis_field', 'lawful_basis_tag')
        subject_field = config.get('subject_field', 'subject_id')
        consent_field = config.get('consent_field')
        consent_positive = {AuditEngine._normalize_value(v) for v in (config.get('consent_positive_values') or ['Y'])}
        consent_withdrawn = {AuditEngine._normalize_value(v) for v in (config.get('consent_withdrawn_values') or ['N'])}
        required_fields = config.get('required_fields_when_consent') or []
        forbidden_purposes = set(config.get('forbidden_purpose_when_withdrawn') or [])
        require_lawful_for = config.get('require_lawful_basis_for')

        purpose = AuditEngine._normalize_value(record.get(purpose_field))
        lawful_basis = AuditEngine._normalize_value(record.get(lawful_field))
        consent_value = AuditEngine._normalize_value(record.get(consent_field)) if consent_field else None

        purpose_map = context.setdefault('purpose_basis_map', defaultdict(Counter))
        key = lawful_basis or '???'
        if purpose:
            purpose_map[purpose][key] += 1
        context.setdefault('purpose_field', purpose_field)
        context.setdefault('lawful_basis_field', lawful_field)

        require_basis = True if not require_lawful_for else (purpose in require_lawful_for)
        if require_basis and not lawful_basis and purpose:
            message = f"?? {purpose} ???????"
            context.setdefault('missing_basis', []).append(
                AuditEngine._sample_record(record, row_number, lawful_field, lawful_basis, message)
            )
            errors.append({
                "error_type": "data",
                "row_number": row_number,
                "column_name": lawful_field,
                "original_value": lawful_basis,
                "error_message": message,
                "rule_id": rule.id,
                "severity": rule.severity
            })

        if lawful_basis == 'consent':
            missing_fields = [f for f in required_fields if AuditEngine._normalize_value(record.get(f)) is None]
            if missing_fields:
                message = f"????????????? {missing_fields}"
                context.setdefault('missing_consent_fields', []).append(
                    AuditEngine._sample_record(record, row_number, lawful_field, lawful_basis, message)
                )
                errors.append({
                    "error_type": "data",
                    "row_number": row_number,
                    "column_name": lawful_field,
                    "original_value": lawful_basis,
                    "error_message": message,
                    "rule_id": rule.id,
                    "severity": rule.severity
                })

        if consent_value in consent_withdrawn and purpose in forbidden_purposes:
            message = f"?????????????? {purpose}"
            context.setdefault('withdrawn_conflicts', []).append(
                AuditEngine._sample_record(record, row_number, consent_field or 'consent', consent_value, message)
            )
            errors.append({
                "error_type": "data",
                "row_number": row_number,
                "column_name": consent_field or 'consent',
                "original_value": consent_value,
                "error_message": message,
                "rule_id": rule.id,
                "severity": rule.severity
            })

        return errors

    @staticmethod
    def _validate_erasure_cascade(
        record: Dict[str, Any],
        rule,
        row_number: int,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        errors: List[Dict[str, Any]] = []
        trigger_field = config.get('trigger_field')
        trigger_value = config.get('trigger_value')

        if trigger_field:
            trigger_actual = AuditEngine._normalize_value(record.get(trigger_field))
            expected_trigger = AuditEngine._normalize_value(trigger_value) if trigger_value is not None else None
            if expected_trigger is not None:
                if trigger_actual != expected_trigger:
                    return errors
            elif not trigger_actual:
                return errors

        subject_id = record.get(config.get('subject_field', 'subject_id'))
        request_id = record.get(config.get('request_id_field', 'dsar_request_id'))
        status_field = config.get('status_field')
        status_value = AuditEngine._normalize_value(record.get(status_field)) if status_field else None
        status_fields = config.get('status_fields', {}) or {}
        start_time = record.get(status_fields.get('start')) if status_fields.get('start') else None
        end_time = record.get(status_fields.get('end')) if status_fields.get('end') else None
        failure_reason = record.get(status_fields.get('failure_reason')) if status_fields.get('failure_reason') else None

        confirmation_results = {}
        missing_targets = []
        for entry in config.get('required_confirmations', []):
            if isinstance(entry, str):
                field = entry
                label = entry
                expected = None
            else:
                field = entry.get('field')
                label = entry.get('label') or entry.get('field')
                expected = entry.get('expected_values')
            if not field:
                continue
            value = record.get(field)
            confirmed = AuditEngine._value_matches_expected(value, expected)
            confirmation_results[label or field] = value
            if not confirmed:
                missing_targets.append(label or field)
                errors.append({
                    "error_type": "data",
                    "row_number": row_number,
                    "column_name": field,
                    "original_value": value,
                    "error_message": f"DSAR ????? {label or field}",
                    "rule_id": rule.id,
                    "severity": rule.severity
                })

        hit_fields = config.get('hit_fields', {}) or {}
        before_hits = AuditEngine._coerce_float(record.get(hit_fields.get('before'))) if hit_fields.get('before') else None
        after_hits = AuditEngine._coerce_float(record.get(hit_fields.get('after'))) if hit_fields.get('after') else None
        if after_hits is not None and after_hits > 0:
            message = f"??????? {after_hits} ??? 0"
            context.setdefault('hit_violations', []).append(
                AuditEngine._sample_record(record, row_number, hit_fields.get('after'), after_hits, message)
            )
            errors.append({
                "error_type": "data",
                "row_number": row_number,
                "column_name": hit_fields.get('after'),
                "original_value": after_hits,
                "error_message": message,
                "rule_id": rule.id,
                "severity": rule.severity
            })

        context['total_requests'] = context.get('total_requests', 0) + 1
        if not missing_targets and (after_hits is None or after_hits == 0):
            context['completed_requests'] = context.get('completed_requests', 0) + 1

        request_entry = {
            "row_number": row_number,
            "request_id": request_id,
            "subject_id": subject_id,
            "status": status_value,
            "start": start_time,
            "end": end_time,
            "failure_reason": failure_reason,
            "missing": missing_targets,
            "confirmations": confirmation_results,
            "before_hits": before_hits,
            "after_hits": after_hits
        }
        context.setdefault('request_records', []).append(request_entry)
        if missing_targets:
            context.setdefault('missing_confirmations', []).append(request_entry)

        return errors

    @staticmethod
    def _validate_train_field_whitelist(
        record: Dict[str, Any],
        rule,
        row_number: int,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        errors: List[Dict[str, Any]] = []
        target_field = config.get('target_field')
        if not target_field:
            return errors

        allowed_fields = set(config.get('allowed_fields') or [])
        pii_fields = {f.lower() for f in (config.get('pii_fields_block') or [])}
        context.setdefault('target_field', target_field)
        context.setdefault('allowed_fields', allowed_fields)
        context.setdefault('pii_fields', pii_fields)
        field_usage: Counter = context.setdefault('field_usage', Counter())
        context['records_checked'] = context.get('records_checked', 0) + 1
        context.setdefault('sample_payloads', [])

        payload, raw_repr = AuditEngine._parse_train_inputs(record.get(target_field))
        if raw_repr and len(context['sample_payloads']) < 10:
            context['sample_payloads'].append(str(raw_repr)[:500])

        fields = AuditEngine._extract_train_fields(payload)
        if not fields:
            return errors

        for field in fields:
            field_usage[field] += 1
        extra_fields = [f for f in fields if f not in allowed_fields]
        if extra_fields:
            message = f"????????: {extra_fields}"
            context.setdefault('violations', []).append(
                AuditEngine._sample_record(record, row_number, target_field, extra_fields, message)
            )
            errors.append({
                "error_type": "data",
                "row_number": row_number,
                "column_name": target_field,
                "original_value": ','.join(extra_fields),
                "error_message": message,
                "rule_id": rule.id,
                "severity": rule.severity
            })

        pii_hits = [f for f in fields if f.lower() in pii_fields]
        if pii_hits:
            message = f"??????? PII ??: {pii_hits}"
            context.setdefault('pii_hits', []).append(
                AuditEngine._sample_record(record, row_number, target_field, pii_hits, message)
            )
            errors.append({
                "error_type": "data",
                "row_number": row_number,
                "column_name": target_field,
                "original_value": ','.join(pii_hits),
                "error_message": message,
                "rule_id": rule.id,
                "severity": rule.severity
            })

        return errors

    @staticmethod
    def _validate_custom_pattern(
        record: Dict[str, Any],
        rule,
        row_number: int,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        errors: List[Dict[str, Any]] = []
        field_name = config.get('field_name')
        pattern = config.get('pattern')
        if not field_name or not pattern or field_name not in record:
            return errors

        context.setdefault('field_name', field_name)
        context.setdefault('pattern', pattern)
        distribution: Counter = context.setdefault('value_distribution', Counter())
        invalid_records = context.setdefault('invalid_records', [])

        raw_value = record.get(field_name)
        value = str(raw_value) if raw_value is not None else ''
        distribution[value or ''] += 1

        if value and not re.match(pattern, value):
            message = f"?? {field_name} ?????? {pattern}"
            invalid_records.append(
                AuditEngine._sample_record(record, row_number, field_name, value, message)
            )
            errors.append({
                "error_type": "data",
                "row_number": row_number,
                "column_name": field_name,
                "original_value": value,
                "error_message": message,
                "rule_id": rule.id,
                "severity": rule.severity
            })

        return errors

    @staticmethod
    def _value_matches_expected(value: Any, expected_values):
        if expected_values is None:
            return AuditEngine._is_truthy(value)
        normalized = AuditEngine._normalize_value(value)
        expected = {AuditEngine._normalize_value(v) for v in expected_values}
        return normalized in expected

    @staticmethod
    def _is_truthy(value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in ('', '0', 'false', 'no', 'n', 'none'):
                return False
        return bool(value)

    @staticmethod
    def _normalize_value(value: Any):
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped if stripped else None
        return str(value)

    @staticmethod
    def _stringify(value: Any) -> str:
        if value is None:
            return ''
        return str(value)

    @staticmethod
    def _parse_train_inputs(value: Any):
        if isinstance(value, str):
            trimmed = value.strip()
            if not trimmed:
                return None, trimmed
            try:
                return json.loads(trimmed), trimmed
            except Exception:
                return trimmed, trimmed
        return value, value

    @staticmethod
    def _extract_train_fields(payload: Any) -> List[str]:
        fields = []
        if isinstance(payload, dict):
            fields.extend(payload.keys())
        elif isinstance(payload, list):
            for item in payload:
                fields.extend(AuditEngine._extract_train_fields(item))
        elif isinstance(payload, str):
            for part in payload.split(','):
                part = part.strip()
                if part:
                    fields.append(part)
        return fields

    @staticmethod
    def _coerce_float(value: Any):
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _sample_record(
        record: Dict[str, Any],
        row_number: int,
        field_name: Optional[str],
        value: Any,
        message: str
    ) -> Dict[str, Any]:
        sample = {
            "row_number": row_number,
            "field": field_name,
            "value": AuditEngine._stringify(value),
            "message": message
        }
        for key in ('record_id', 'subject_id', 'dsar_request_id', 'purpose_tag'):
            if key in record and record.get(key) is not None:
                sample[key] = record[key]
        return sample

    @staticmethod
    def _build_rule_statistics(
        rule_contexts: Dict[str, Dict[str, Any]],
        total_records: int
    ) -> List[Dict[str, Any]]:
        statistics: List[Dict[str, Any]] = []
        for meta in rule_contexts.values():
            rule = meta['rule']
            context = meta.get('context') or {}
            if not context:
                continue
            summary = AuditEngine._summarize_rule(rule, context, total_records)
            if summary:
                statistics.append(summary)
        return statistics

    @staticmethod
    def _summarize_rule(rule, context: Dict[str, Any], total_records: int):
        custom_type = context.get('custom_type')
        if custom_type == 'enum_required':
            return AuditEngine._summarize_enum_required(rule, context, total_records)
        if custom_type == 'lawful_basis_consistency':
            return AuditEngine._summarize_lawful_basis(rule, context)
        if custom_type == 'erasure_cascade':
            return AuditEngine._summarize_erasure(rule, context)
        if custom_type == 'train_field_whitelist':
            return AuditEngine._summarize_train_whitelist(rule, context)
        if rule.rule_type == 'email' or rule.rule_code == 'GDPR-EMAIL-FORMAT':
            return AuditEngine._summarize_contact_field(rule, context, '??')
        if rule.rule_code == 'GDPR-PHONE-FORMAT':
            return AuditEngine._summarize_contact_field(rule, context, '???')
        if rule.rule_code == 'GDPR-IDCARD-FORMAT':
            return AuditEngine._summarize_contact_field(rule, context, '???')
        if rule.rule_code == 'GDPR-CONSENT-FLAG':
            return AuditEngine._summarize_pattern_rule(rule, context, '????')
        if rule.rule_code == 'GDPR-RETENTION-PERIOD':
            return AuditEngine._summarize_pattern_rule(rule, context, '????')
        if rule.rule_code == 'GDPR-DATA-MINIMIZATION':
            return AuditEngine._summarize_pattern_rule(rule, context, '?????')
        return None

    @staticmethod
    def _summarize_enum_required(rule, context: Dict[str, Any], total_records: int):
        distribution: Counter = context.get('distribution', Counter())
        invalid = context.get('invalid_records', [])
        metrics = {
            '????': total_records,
            '???????': sum(distribution.values()),
            '???????': len(invalid)
        }
        table_rows = []
        for purpose, count in distribution.items():
            percent = AuditEngine._format_percentage(count, total_records)
            table_rows.append([purpose, count, percent])
        tables = [
            {
                'title': '????',
                'headers': ['??', '??', '??'],
                'rows': table_rows
            }
        ] if table_rows else []
        return {
            'rule_code': rule.rule_code,
            'rule_name': rule.rule_name,
            'severity': rule.severity,
            'metrics': metrics,
            'tables': tables,
            'samples': invalid[:10]
        }

    @staticmethod
    def _summarize_lawful_basis(rule, context: Dict[str, Any]):
        mapping = context.get('purpose_basis_map', {})
        missing = context.get('missing_basis', [])
        missing_consent = context.get('missing_consent_fields', [])
        withdrawn_conflicts = context.get('withdrawn_conflicts', [])
        rows = []
        for purpose, basis_counter in mapping.items():
            for basis, count in basis_counter.items():
                rows.append([purpose, basis, count])
        tables = []
        if rows:
            tables.append({'title': '??-?????', 'headers': ['??', '?????', '??'], 'rows': rows})
        metrics = {
            '???????': len(missing),
            '??????': len(missing_consent),
            '???????': len(withdrawn_conflicts)
        }
        samples = (missing + missing_consent + withdrawn_conflicts)[:10]
        return {
            'rule_code': rule.rule_code,
            'rule_name': rule.rule_name,
            'severity': rule.severity,
            'metrics': metrics,
            'tables': tables,
            'samples': samples
        }

    @staticmethod
    def _summarize_erasure(rule, context: Dict[str, Any]):
        metrics = {
            '??????': context.get('total_requests', 0),
            '??????': context.get('completed_requests', 0),
            '???????': len(context.get('missing_confirmations', [])),
            '???????': len(context.get('hit_violations', []))
        }
        status_rows = []
        for entry in context.get('request_records', []):
            status_rows.append([
                entry.get('row_number'),
                entry.get('request_id'),
                entry.get('subject_id'),
                entry.get('status'),
                entry.get('start'),
                entry.get('end'),
                entry.get('failure_reason')
            ])
        tables = []
        if status_rows:
            tables.append({
                'title': 'DSAR ????',
                'headers': ['??', '??ID', '??ID', '??', '????', '????', '????'],
                'rows': status_rows
            })
        missing_rows = []
        for entry in context.get('missing_confirmations', []):
            missing_rows.append([
                entry.get('row_number'),
                entry.get('request_id'),
                entry.get('subject_id'),
                ','.join(entry.get('missing') or [])
            ])
        if missing_rows:
            tables.append({
                'title': '??????',
                'headers': ['??', '??ID', '??ID', '????'],
                'rows': missing_rows
            })
        return {
            'rule_code': rule.rule_code,
            'rule_name': rule.rule_name,
            'severity': rule.severity,
            'metrics': metrics,
            'tables': tables,
            'samples': context.get('hit_violations', [])[:10]
        }

    @staticmethod
    def _summarize_train_whitelist(rule, context: Dict[str, Any]):
        metrics = {
            '?????': context.get('records_checked', 0),
            '?????': len(context.get('violations', [])),
            'PII ??': len(context.get('pii_hits', []))
        }
        field_usage: Counter = context.get('field_usage', Counter())
        usage_rows = [[field, count] for field, count in field_usage.most_common()]
        tables = []
        if usage_rows:
            tables.append({'title': '??????', 'headers': ['??', '????'], 'rows': usage_rows})
        samples = (context.get('violations', []) + context.get('pii_hits', []))[:10]
        return {
            'rule_code': rule.rule_code,
            'rule_name': rule.rule_name,
            'severity': rule.severity,
            'metrics': metrics,
            'tables': tables,
            'samples': samples
        }

    @staticmethod
    def _summarize_contact_field(rule, context: Dict[str, Any], label: str):
        metrics = {
            '??????': context.get('candidate_count', 0),
            '????': context.get('invalid_count', 0)
        }
        return {
            'rule_code': rule.rule_code,
            'rule_name': rule.rule_name,
            'severity': rule.severity,
            'metrics': metrics,
            'tables': [],
            'samples': context.get('invalid_samples', [])[:10]
        }

    @staticmethod
    def _summarize_pattern_rule(rule, context: Dict[str, Any], label: str):
        distribution: Counter = context.get('value_distribution', Counter())
        rows = [[value, count] for value, count in distribution.items()]
        tables = []
        if rows:
            tables.append({'title': f'{label}????', 'headers': ['??', '??'], 'rows': rows})
        return {
            'rule_code': rule.rule_code,
            'rule_name': rule.rule_name,
            'severity': rule.severity,
            'metrics': {'????': len(context.get('invalid_records', []))},
            'tables': tables,
            'samples': context.get('invalid_records', [])[:10]
        }

    @staticmethod
    def _format_percentage(count: int, total: int) -> str:
        if not total:
            return '0%'
        return f"{(count / total * 100):.2f}%"

    # ========== 新增：规则模板实例化验证方法 ==========

    @staticmethod
    def _validate_field_required(
        record: Dict[str, Any],
        rule,
        row_number: int,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """验证字段必填"""
        errors: List[Dict[str, Any]] = []
        field_name = config.get('field_name')
        field_display_name = config.get('field_display_name', field_name)
        error_message = config.get('error_message', f'{field_display_name}不能为空')

        if not field_name:
            return errors

        value = record.get(field_name)

        # 检查是否为空、null或仅包含空格
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append({
                "error_type": "data",
                "row_number": row_number,
                "column_name": field_name,
                "original_value": value,
                "error_message": error_message,
                "rule_id": rule.id,
                "severity": rule.severity,
                "start_position": 0,
                "end_position": 0
            })

        return errors

    @staticmethod
    def _validate_regex_match(
        record: Dict[str, Any],
        rule,
        row_number: int,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """验证字段格式（正则表达式）"""
        errors: List[Dict[str, Any]] = []
        field_name = config.get('field_name')
        pattern = config.get('pattern')
        format_description = config.get('format_description', '格式不正确')

        if not field_name or not pattern:
            return errors

        value = record.get(field_name)
        if value and isinstance(value, str):
            if not re.match(pattern, value):
                errors.append({
                    "error_type": "data",
                    "row_number": row_number,
                    "column_name": field_name,
                    "original_value": value,
                    "error_message": f"{format_description}",
                    "rule_id": rule.id,
                    "severity": rule.severity,
                    "start_position": 0,
                    "end_position": len(value)
                })

        return errors

    @staticmethod
    def _validate_enum_validation(
        record: Dict[str, Any],
        rule,
        row_number: int,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """验证枚举值"""
        errors: List[Dict[str, Any]] = []
        field_name = config.get('field_name')
        allowed_values = config.get('allowed_values', [])
        case_sensitive = config.get('case_sensitive', True)

        if not field_name:
            return errors

        value = record.get(field_name)
        if value is not None:
            # 根据是否区分大小写进行比较
            if case_sensitive:
                if value not in allowed_values:
                    errors.append({
                        "error_type": "data",
                        "row_number": row_number,
                        "column_name": field_name,
                        "original_value": value,
                        "error_message": f"值必须是以下之一: {', '.join(map(str, allowed_values))}",
                        "rule_id": rule.id,
                        "severity": rule.severity
                    })
            else:
                # 不区分大小写
                allowed_lower = [str(v).lower() for v in allowed_values]
                if str(value).lower() not in allowed_lower:
                    errors.append({
                        "error_type": "data",
                        "row_number": row_number,
                        "column_name": field_name,
                        "original_value": value,
                        "error_message": f"值必须是以下之一（不区分大小写）: {', '.join(map(str, allowed_values))}",
                        "rule_id": rule.id,
                        "severity": rule.severity
                    })

        return errors

    @staticmethod
    def _validate_length_limit(
        record: Dict[str, Any],
        rule,
        row_number: int,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """验证字段长度"""
        errors: List[Dict[str, Any]] = []
        field_name = config.get('field_name')
        min_length = config.get('min_length')
        max_length = config.get('max_length')

        if not field_name:
            return errors

        value = record.get(field_name)
        if value and isinstance(value, str):
            length = len(value)

            if min_length is not None and length < min_length:
                errors.append({
                    "error_type": "data",
                    "row_number": row_number,
                    "column_name": field_name,
                    "original_value": value,
                    "error_message": f"长度不能小于{min_length}个字符（当前{length}个）",
                    "rule_id": rule.id,
                    "severity": rule.severity
                })

            if max_length is not None and length > max_length:
                errors.append({
                    "error_type": "data",
                    "row_number": row_number,
                    "column_name": field_name,
                    "original_value": value[:50] + "..." if len(value) > 50 else value,
                    "error_message": f"长度不能超过{max_length}个字符（当前{length}个）",
                    "rule_id": rule.id,
                    "severity": rule.severity
                })

        return errors

    @staticmethod
    def _validate_numeric_range(
        record: Dict[str, Any],
        rule,
        row_number: int,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """验证数值范围"""
        errors: List[Dict[str, Any]] = []
        field_name = config.get('field_name')
        min_value = config.get('min_value')
        max_value = config.get('max_value')
        allow_decimal = config.get('allow_decimal', False)

        if not field_name:
            return errors

        value = record.get(field_name)
        if value is not None:
            try:
                if isinstance(value, str):
                    numeric_value = float(value) if allow_decimal else int(value)
                else:
                    numeric_value = value

                # 检查是否为整数（如果不允许小数）
                if not allow_decimal and isinstance(numeric_value, float) and not numeric_value.is_integer():
                    errors.append({
                        "error_type": "data",
                        "row_number": row_number,
                        "column_name": field_name,
                        "original_value": value,
                        "error_message": "必须是整数",
                        "rule_id": rule.id,
                        "severity": rule.severity
                    })
                    return errors

                # 检查范围
                if min_value is not None and numeric_value < min_value:
                    errors.append({
                        "error_type": "data",
                        "row_number": row_number,
                        "column_name": field_name,
                        "original_value": value,
                        "error_message": f"值不能小于{min_value}（当前为{numeric_value}）",
                        "rule_id": rule.id,
                        "severity": rule.severity
                    })

                if max_value is not None and numeric_value > max_value:
                    errors.append({
                        "error_type": "data",
                        "row_number": row_number,
                        "column_name": field_name,
                        "original_value": value,
                        "error_message": f"值不能大于{max_value}（当前为{numeric_value}）",
                        "rule_id": rule.id,
                        "severity": rule.severity
                    })

            except (ValueError, TypeError):
                errors.append({
                    "error_type": "data",
                    "row_number": row_number,
                    "column_name": field_name,
                    "original_value": value,
                    "error_message": "必须是有效的数值",
                    "rule_id": rule.id,
                    "severity": rule.severity
                })

        return errors

    @staticmethod
    def _validate_date_validation(
        record: Dict[str, Any],
        rule,
        row_number: int,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """验证日期字段"""
        errors: List[Dict[str, Any]] = []
        field_name = config.get('field_name')
        date_format = config.get('date_format', 'YYYY-MM-DD')

        if not field_name:
            return errors

        value = record.get(field_name)
        if value and isinstance(value, str):
            # 简单的日期格式验证（可以根据需要扩展）
            date_patterns = {
                'YYYY-MM-DD': r'^\d{4}-\d{2}-\d{2}$',
                'YYYY/MM/DD': r'^\d{4}/\d{2}/\d{2}$',
                'DD-MM-YYYY': r'^\d{2}-\d{2}-\d{4}$',
                'DD/MM/YYYY': r'^\d{2}/\d{2}/\d{4}$',
            }

            pattern = date_patterns.get(date_format)
            if pattern and not re.match(pattern, value):
                errors.append({
                    "error_type": "data",
                    "row_number": row_number,
                    "column_name": field_name,
                    "original_value": value,
                    "error_message": f"日期格式必须为{date_format}",
                    "rule_id": rule.id,
                    "severity": rule.severity
                })

        return errors

    @staticmethod
    def _validate_no_pii_keywords(
        record: Dict[str, Any],
        rule,
        row_number: int,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """验证字段不包含敏感关键词"""
        errors: List[Dict[str, Any]] = []
        field_name = config.get('field_name')
        blocked_keywords = config.get('blocked_keywords', [])
        case_sensitive = config.get('case_sensitive', False)

        if not field_name or not blocked_keywords:
            return errors

        value = record.get(field_name)
        if value and isinstance(value, str):
            search_value = value if case_sensitive else value.lower()

            for keyword in blocked_keywords:
                search_keyword = keyword if case_sensitive else keyword.lower()
                if search_keyword in search_value:
                    errors.append({
                        "error_type": "data",
                        "row_number": row_number,
                        "column_name": field_name,
                        "original_value": value[:50] + "..." if len(value) > 50 else value,
                        "error_message": f"包含禁止的敏感词: {keyword}",
                        "rule_id": rule.id,
                        "severity": rule.severity
                    })
                    break  # 找到一个就够了

        return errors

    @staticmethod
    def _validate_field_dependency(
        record: Dict[str, Any],
        rule,
        row_number: int,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """验证字段依赖关系"""
        errors: List[Dict[str, Any]] = []
        source_field = config.get('source_field')
        dependent_field = config.get('dependent_field')
        condition = config.get('condition', 'not_empty')
        condition_value = config.get('condition_value')

        if not source_field or not dependent_field:
            return errors

        source_value = record.get(source_field)
        dependent_value = record.get(dependent_field)

        # 判断条件是否满足
        condition_met = False
        if condition == 'not_empty':
            condition_met = source_value is not None and (not isinstance(source_value, str) or source_value.strip())
        elif condition == 'equals':
            condition_met = str(source_value) == str(condition_value)
        elif condition == 'contains':
            condition_met = condition_value in str(source_value) if source_value else False

        # 如果条件满足，检查依赖字段
        if condition_met:
            if dependent_value is None or (isinstance(dependent_value, str) and not dependent_value.strip()):
                errors.append({
                    "error_type": "data",
                    "row_number": row_number,
                    "column_name": dependent_field,
                    "original_value": dependent_value,
                    "error_message": f"当{source_field}有值时，{dependent_field}也必须有值",
                    "rule_id": rule.id,
                    "severity": rule.severity
                })

        return errors

    @staticmethod
    def _validate_uniqueness_check(
        record: Dict[str, Any],
        rule,
        row_number: int,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """验证字段唯一性"""
        errors: List[Dict[str, Any]] = []
        field_name = config.get('field_name')
        ignore_empty = config.get('ignore_empty', True)

        if not field_name:
            return errors

        value = record.get(field_name)

        # 如果忽略空值且值为空，直接返回
        if ignore_empty and (value is None or (isinstance(value, str) and not value.strip())):
            return errors

        # 使用context存储已见过的值
        seen_values = context.setdefault('seen_values', {})

        if value in seen_values:
            # 发现重复
            first_row = seen_values[value]
            errors.append({
                "error_type": "data",
                "row_number": row_number,
                "column_name": field_name,
                "original_value": value,
                "error_message": f"值重复，首次出现在第{first_row}行",
                "rule_id": rule.id,
                "severity": rule.severity
            })
        else:
            # 记录首次出现
            seen_values[value] = row_number

        return errors

"""
AI法规解析器
使用AI大模型解析法规文本，提取合规要求并映射到规则模板
"""
from typing import List, Dict, Any
import json
from app.config.setting import settings


class RegulationParser:
    """AI法规解析器类"""

    @staticmethod
    async def parse_regulation(
        regulation_content: str,
        available_templates: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        解析法规内容，提取合规要求并匹配规则模板

        Args:
            regulation_content: 法规文本内容
            available_templates: 可用的规则模板列表

        Returns:
            解析结果列表，每个结果包含：
            {
                "template_id": 模板ID,
                "template_code": 模板编码,
                "instance_parameters": 实例化参数,
                "confidence": 置信度 (0-1),
                "rule_code": 生成的规则编码,
                "rule_name": 生成的规则名称,
                "rule_description": 规则描述,
                "severity": 严重等级,
                "source_text": 来源法规文本片段
            }
        """
        # 检查是否配置了AI服务
        if not settings.OPENAI_API_KEY or not settings.OPENAI_BASE_URL:
            print("AI服务未配置，无法解析法规")
            return []

        # 构建模板描述
        templates_desc = []
        for template in available_templates:
            templates_desc.append({
                "id": template.id,
                "code": template.template_code,
                "name": template.template_name,
                "category": template.template_category,
                "description": template.template_description,
                "parameters": template.parameters_schema
            })

        # 限制法规内容长度
        content_preview = regulation_content[:8000] if len(regulation_content) > 8000 else regulation_content

        # 构建Prompt
        prompt = f"""
你是一个数据合规审计专家。请仔细分析以下法规文本，提取所有需要审计的数据合规要求。

# 任务要求

1. 识别法规中的所有数据合规要求（如字段必填、格式验证、枚举限制等）
2. 对于每个要求，从规则模板池中选择最合适的模板
3. 为每个要求提取实例化参数（字段名、验证条件等）
4. 生成规则编码、名称和描述

# 可用规则模板

{json.dumps(templates_desc, ensure_ascii=False, indent=2)}

# 法规内容

{content_preview}

# 输出格式

请返回JSON数组，每个元素包含以下字段：

{{
  "requirements": [
    {{
      "template_id": <模板ID>,
      "template_code": "<模板编码>",
      "instance_parameters": {{
        // 根据模板的parameters_schema填充具体参数
        "field_name": "email",
        "field_display_name": "用户邮箱",
        ...
      }},
      "confidence": 0.95,  // 置信度 0-1
      "rule_code": "REG-EMAIL-REQUIRED",  // 生成唯一的规则编码
      "rule_name": "用户邮箱必填",  // 简洁的规则名称
      "rule_description": "根据GDPR第X条，用户邮箱为必填项...",  // 详细描述
      "severity": "error",  // error/warning/info
      "source_text": "法规原文片段..."  // 该要求的来源文本
    }}
  ]
}}

# 重要提示

1. 字段名（field_name）要准确，通常是数据库列名或JSON键名
2. 优先使用明确的字段名，如"email"、"phone"、"consent_flag"等
3. 规则编码（rule_code）要唯一且有意义，建议格式：REG-<字段名>-<规则类型>
4. 严重等级根据法规要求判断：强制要求用error，建议用warning
5. 如果法规中没有明确的数据字段要求，返回空数组
6. 实例化参数必须完全符合模板的parameters_schema定义
"""

        try:
            # 动态导入 openai
            import openai

            # 调用OpenAI API
            client = openai.OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL
            )

            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL or "gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的数据合规审计专家，擅长分析法规并提取可执行的审计规则。你总是返回结构化的JSON数据。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # 较低的temperature确保输出稳定
                response_format={"type": "json_object"}
            )

            # 解析响应
            result = json.loads(response.choices[0].message.content)
            requirements = result.get('requirements', [])

            # 验证和过滤结果
            valid_requirements = []
            valid_template_ids = [t.id for t in available_templates]
            template_map = {t.id: t for t in available_templates}

            for req in requirements:
                # 验证必需字段
                if not all(key in req for key in ['template_id', 'template_code', 'instance_parameters']):
                    print(f"跳过无效要求（缺少必需字段）: {req}")
                    continue

                # 验证模板ID有效
                if req['template_id'] not in valid_template_ids:
                    print(f"跳过无效要求（模板ID不存在）: {req['template_id']}")
                    continue

                # 验证实例化参数符合模板定义
                template = template_map[req['template_id']]
                params_schema = template.parameters_schema
                required_params = params_schema.get('required', [])
                instance_params = req['instance_parameters']

                # 检查必需参数是否都存在
                missing_params = [p for p in required_params if p not in instance_params]
                if missing_params:
                    print(f"跳过无效要求（缺少必需参数 {missing_params}）: {req}")
                    continue

                # 添加默认值
                if 'confidence' not in req:
                    req['confidence'] = 0.85
                if 'severity' not in req:
                    req['severity'] = template.default_severity
                if 'rule_code' not in req:
                    req['rule_code'] = f"AUTO-{template.template_code}-{len(valid_requirements)}"
                if 'rule_name' not in req:
                    req['rule_name'] = f"{template.template_name} - 自动生成"

                valid_requirements.append(req)

            print(f"法规解析成功，提取到 {len(valid_requirements)} 个有效要求")
            return valid_requirements

        except ImportError:
            print("openai库未安装，无法解析法规")
            print("提示：请安装 openai: pip install openai")
            return []
        except Exception as e:
            print(f"法规解析失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    async def parse_structured_regulation(
        regulation_dict: Dict[str, Any],
        available_templates: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        解析结构化的法规输入（用户按照模板填写）

        Args:
            regulation_dict: 结构化法规数据，格式如下：
                {
                    "regulation_name": "GDPR用户数据保护条例",
                    "requirements": [
                        {
                            "field_name": "email",
                            "field_display_name": "用户邮箱",
                            "rule_type": "必填",
                            "validation_condition": "不能为空",
                            "severity": "error"
                        },
                        ...
                    ]
                }
            available_templates: 可用的规则模板列表

        Returns:
            解析结果列表（格式同 parse_regulation）
        """
        template_map = {t.template_code: t for t in available_templates}

        # 规则类型到模板编码的映射
        rule_type_mapping = {
            "必填": "FIELD_REQUIRED",
            "格式验证": "FIELD_FORMAT_REGEX",
            "格式": "FIELD_FORMAT_REGEX",
            "正则": "FIELD_FORMAT_REGEX",
            "枚举": "FIELD_ENUM_VALUES",
            "枚举值": "FIELD_ENUM_VALUES",
            "长度限制": "FIELD_LENGTH_LIMIT",
            "长度": "FIELD_LENGTH_LIMIT",
            "数值范围": "FIELD_NUMERIC_RANGE",
            "范围": "FIELD_NUMERIC_RANGE",
            "日期": "FIELD_DATE_VALIDATION",
            "唯一性": "FIELD_UNIQUE_CHECK",
            "依赖关系": "FIELD_DEPENDENCY_CHECK",
            "不含敏感词": "FIELD_NO_PII_KEYWORDS"
        }

        results = []
        requirements = regulation_dict.get('requirements', [])

        for idx, req in enumerate(requirements):
            rule_type = req.get('rule_type', '')
            template_code = rule_type_mapping.get(rule_type)

            if not template_code or template_code not in template_map:
                print(f"未知规则类型: {rule_type}，跳过")
                continue

            template = template_map[template_code]

            # 构建实例化参数
            instance_params = {
                "field_name": req.get('field_name', ''),
                "field_display_name": req.get('field_display_name', req.get('field_name', ''))
            }

            # 根据不同模板类型添加特定参数
            if template_code == "FIELD_REQUIRED":
                # 必填模板只需要field_name和field_display_name
                pass

            elif template_code == "FIELD_FORMAT_REGEX":
                # 格式验证需要regex_pattern
                validation_condition = req.get('validation_condition', '')
                # 尝试提取或推断正则表达式
                regex_pattern = req.get('regex_pattern', validation_condition)
                instance_params['regex_pattern'] = regex_pattern
                instance_params['format_description'] = req.get('format_description', validation_condition)

            elif template_code == "FIELD_ENUM_VALUES":
                # 枚举需要allowed_values
                allowed_values = req.get('allowed_values', [])
                if isinstance(allowed_values, str):
                    # 如果是字符串，尝试解析（如 "Y,N" 或 "Y/N"）
                    allowed_values = [v.strip() for v in allowed_values.replace('/', ',').split(',')]
                instance_params['allowed_values'] = allowed_values
                instance_params['case_sensitive'] = req.get('case_sensitive', True)

            elif template_code == "FIELD_LENGTH_LIMIT":
                # 长度限制
                instance_params['min_length'] = req.get('min_length')
                instance_params['max_length'] = req.get('max_length')

            elif template_code == "FIELD_NUMERIC_RANGE":
                # 数值范围
                instance_params['min_value'] = req.get('min_value')
                instance_params['max_value'] = req.get('max_value')
                instance_params['allow_decimal'] = req.get('allow_decimal', False)

            elif template_code == "FIELD_DATE_VALIDATION":
                # 日期验证
                instance_params['date_format'] = req.get('date_format', 'YYYY-MM-DD')
                instance_params['min_date'] = req.get('min_date')
                instance_params['max_date'] = req.get('max_date')

            # 生成规则编码和名称
            field_name_upper = req.get('field_name', '').upper().replace(' ', '_')
            rule_code = f"REG-{field_name_upper}-{template_code.split('_')[1]}"
            rule_name = f"{req.get('field_display_name', '')} - {rule_type}"

            results.append({
                "template_id": template.id,
                "template_code": template_code,
                "instance_parameters": instance_params,
                "confidence": 1.0,  # 用户手动输入，置信度最高
                "rule_code": rule_code,
                "rule_name": rule_name,
                "rule_description": req.get('validation_condition', ''),
                "severity": req.get('severity', template.default_severity),
                "source_text": f"结构化输入 - 要求{idx + 1}"
            })

        print(f"结构化法规解析成功，提取到 {len(results)} 个要求")
        return results

"""
AI规则匹配器
使用AI大模型智能匹配审计规则
"""
from typing import List, Dict, Any
import json
from app.config.setting import settings


class AIMatcher:
    """AI规则匹配器类"""

    @staticmethod
    async def match_rules(regulation_content: str, all_rules: List) -> Dict[str, Any]:
        """
        使用AI匹配规则

        Args:
            regulation_content: 法规文件内容
            all_rules: 所有规则列表

        Returns:
            {
                "rule_ids": [1, 2, 3],  # 匹配的规则ID列表
                "matches": [            # 详细的匹配信息
                    {"rule_id": 1, "reason": "...", "regulation_ref": "..."},
                    ...
                ]
            }
        """
        # 检查是否配置了AI服务
        if not settings.OPENAI_API_KEY or not settings.OPENAI_BASE_URL:
            print("AI服务未配置，使用默认策略返回所有规则")
            return {
                "rule_ids": [rule.id for rule in all_rules],
                "matches": []
            }

        # 构建规则描述
        rules_desc = "\n".join([
            f"{rule.id}. {rule.rule_name} ({rule.rule_type}): {rule.rule_description}"
            for rule in all_rules
        ])

        # 限制法规内容长度，避免超出token限制
        content_preview = regulation_content[:3000] if len(regulation_content) > 3000 else regulation_content

        # 构建Prompt - 要求返回匹配原因
        prompt = f"""
分析以下法规文件内容，识别需要审计的数据类型，从规则池中匹配相关规则。

请返回JSON格式，包含规则ID、匹配原因和对应的法规条款：
{{
  "matches": [
    {{"rule_id": 1, "reason": "法规要求邮箱格式验证", "regulation_ref": "第一条第2款"}},
    {{"rule_id": 2, "reason": "法规要求手机号验证", "regulation_ref": "第一条第3-4款"}}
  ]
}}

规则池:
{rules_desc}

法规文件内容:
{content_preview}
"""

        try:
            # 动态导入 openai，避免未安装时报错
            import openai

            # 调用OpenAI API
            client = openai.OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL
            )

            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个数据合规审计专家，擅长分析法规文件并匹配审计规则。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
                extra_body={"enable_thinking": False}
            )

            # 解析响应
            result = json.loads(response.choices[0].message.content)

            # 兼容新旧格式
            if 'matches' in result:
                # 新格式：包含匹配原因
                matches = result.get('matches', [])
                matched_ids = [m['rule_id'] for m in matches]

                # 打印匹配详情
                print(f"AI匹配成功，匹配到 {len(matches)} 条规则:")
                for match in matches:
                    print(f"  - 规则{match['rule_id']}: {match.get('reason', '无')} (法规: {match.get('regulation_ref', '无')})")
            else:
                # 旧格式：仅规则ID
                matched_ids = result.get('rule_ids', [])
                print(f"AI匹配成功，匹配到 {len(matched_ids)} 条规则")

            # 验证ID是否有效
            valid_ids = [rule.id for rule in all_rules]
            filtered_ids = [rid for rid in matched_ids if rid in valid_ids]

            # 过滤matches，只保留有效的规则
            if 'matches' in result:
                valid_matches = [m for m in matches if m['rule_id'] in valid_ids]
            else:
                valid_matches = []

            if not filtered_ids:
                # 如果没有匹配到，返回所有规则
                return {
                    "rule_ids": [rule.id for rule in all_rules],
                    "matches": []
                }

            return {
                "rule_ids": filtered_ids,
                "matches": valid_matches
            }

        except ImportError:
            print("openai库未安装，降级策略：返回所有规则")
            print("提示：请安装 openai: pip install openai")
            return {
                "rule_ids": [rule.id for rule in all_rules],
                "matches": []
            }
        except Exception as e:
            print(f"AI匹配失败: {str(e)}")
            print("降级策略：返回所有规则")
            return {
                "rule_ids": [rule.id for rule in all_rules],
                "matches": []
            }

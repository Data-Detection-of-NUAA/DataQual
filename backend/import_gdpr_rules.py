"""
导入GDPR审计规则到数据库
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import AsyncSession, async_engine
from app.plugin.module_audit.rule.model import AuditRule
from sqlalchemy import select


async def import_gdpr_rules():
    """导入GDPR规则到数据库"""

    # GDPR规则数据
    gdpr_rules = [
        # Article 5: 数据处理的七大基本原则
        {
            'rule_code': 'GDPR-5.1.a',
            'rule_name': '合法性原则',
            'rule_type': 'compliance',
            'rule_description': 'GDPR第5条第1款(a)：个人数据必须基于合法依据进行处理（同意、合同、法律义务、切身利益、公共任务或合法利益）',
            'rule_expression': '{"legal_basis": ["consent", "contract", "legal_obligation", "vital_interest", "public_task", "legitimate_interest"]}',
            'severity': 'high',
            'is_active': 1,
            'remark': 'Article 5(1)(a) - 违反可能面临最高级别罚款：2000万欧元或全球年营业额的4%'
        },
        {
            'rule_code': 'GDPR-5.1.a-2',
            'rule_name': '透明性原则',
            'rule_type': 'compliance',
            'rule_description': 'GDPR第5条第1款(a)：数据处理必须对数据主体透明，需清晰告知数据收集的性质、种类、目的和期限',
            'rule_expression': '{"transparency_requirements": ["processing_purpose", "data_categories", "storage_period", "recipients", "data_subject_rights"]}',
            'severity': 'high',
            'is_active': 1,
            'remark': 'Article 5(1)(a) - 需要提供清晰易懂的隐私通知'
        },
        {
            'rule_code': 'GDPR-5.1.b',
            'rule_name': '目的限制原则',
            'rule_type': 'compliance',
            'rule_description': 'GDPR第5条第1款(b)：个人数据必须为明确、具体和合法的目的而收集，不得以与这些目的不相容的方式进一步处理',
            'rule_expression': '{"purpose_specified": true, "purpose_explicit": true, "purpose_legitimate": true, "compatible_use_only": true}',
            'severity': 'high',
            'is_active': 1,
            'remark': 'Article 5(1)(b) - 禁止功能蠕变，数据用途必须与原始目的一致'
        },
        {
            'rule_code': 'GDPR-5.1.c',
            'rule_name': '数据最小化原则',
            'rule_type': 'data_quality',
            'rule_description': 'GDPR第5条第1款(c)：处理的个人数据必须充分、相关，并限于与处理目的相关的必要范围内',
            'rule_expression': '{"collect_only_necessary": true, "adequate_for_purpose": true, "relevant_to_purpose": true}',
            'severity': 'medium',
            'is_active': 1,
            'remark': 'Article 5(1)(c) - 不得过度收集数据，仅收集实现目的所需的最少数据'
        },
        {
            'rule_code': 'GDPR-5.1.d',
            'rule_name': '数据准确性原则',
            'rule_type': 'data_quality',
            'rule_description': 'GDPR第5条第1款(d)：个人数据必须准确，必要时保持最新；必须采取合理措施及时删除或更正不准确的数据',
            'rule_expression': '{"data_accurate": true, "data_up_to_date": true, "error_correction_process": true}',
            'severity': 'medium',
            'is_active': 1,
            'remark': 'Article 5(1)(d) - 需要建立数据更正和删除机制'
        },
        {
            'rule_code': 'GDPR-5.1.e',
            'rule_name': '存储限制原则',
            'rule_type': 'compliance',
            'rule_description': 'GDPR第5条第1款(e)：个人数据的保存形式不得超过实现处理目的所需的时间，应定义数据保留期限并定期审查',
            'rule_expression': '{"retention_period_defined": true, "retention_necessary_only": true, "periodic_review": true}',
            'severity': 'medium',
            'is_active': 1,
            'remark': 'Article 5(1)(e) - 需要制定数据保留政策和删除计划'
        },
        {
            'rule_code': 'GDPR-5.1.f',
            'rule_name': '数据安全原则',
            'rule_type': 'security',
            'rule_description': 'GDPR第5条第1款(f)：个人数据处理必须确保适当的安全性，包括防止未经授权或非法处理，防止意外丢失、破坏或损坏',
            'rule_expression': '{"encryption_required": true, "access_control": true, "security_measures": ["technical", "organizational"], "breach_prevention": true}',
            'severity': 'high',
            'is_active': 1,
            'remark': 'Article 5(1)(f) - 需要采取适当的技术和组织措施保护数据'
        },
        {
            'rule_code': 'GDPR-5.2',
            'rule_name': '问责制原则',
            'rule_type': 'compliance',
            'rule_description': 'GDPR第5条第2款：数据控制者应负责并能够证明符合上述各项原则（问责制），需要记录处理活动并实施数据保护政策',
            'rule_expression': '{"compliance_demonstration": true, "documentation_maintained": true, "dpia_when_required": true, "policies_implemented": true}',
            'severity': 'high',
            'is_active': 1,
            'remark': 'Article 5(2) - 需要维护处理活动记录和合规证明'
        },
        # Article 9: 特殊类别个人数据（敏感数据）
        {
            'rule_code': 'GDPR-9.1',
            'rule_name': '禁止处理敏感数据',
            'rule_type': 'sensitive_data',
            'rule_description': 'GDPR第9条第1款：原则上禁止处理揭示种族、民族、政治观点、宗教信仰、工会成员身份、基因数据、生物识别数据、健康数据、性生活或性取向的个人数据',
            'rule_expression': '{"special_categories": ["racial_origin", "ethnic_origin", "political_opinions", "religious_beliefs", "philosophical_beliefs", "trade_union_membership", "genetic_data", "biometric_data", "health_data", "sex_life", "sexual_orientation"], "processing_prohibited": true}',
            'severity': 'critical',
            'is_active': 1,
            'remark': 'Article 9(1) - 敏感数据处理受严格限制，违反面临最高级别罚款'
        },
        {
            'rule_code': 'GDPR-9.2.a',
            'rule_name': '敏感数据例外-明确同意',
            'rule_type': 'sensitive_data',
            'rule_description': 'GDPR第9条第2款(a)：仅在数据主体就一个或多个特定目的明确同意处理这些个人数据时，才可处理敏感数据',
            'rule_expression': '{"explicit_consent_obtained": true, "consent_specific": true, "consent_informed": true, "consent_freely_given": true}',
            'severity': 'critical',
            'is_active': 1,
            'remark': 'Article 9(2)(a) - 需要获得明确同意，同意必须是自愿、具体、知情和明确的'
        },
        # Article 6: 数据处理的合法性
        {
            'rule_code': 'GDPR-6.1',
            'rule_name': '合法处理基础',
            'rule_type': 'compliance',
            'rule_description': 'GDPR第6条第1款：数据处理必须至少基于以下一种合法依据：同意、合同履行、法律义务、保护切身利益、公共利益任务或合法利益',
            'rule_expression': '{"legal_basis_documented": true, "legal_basis_valid": ["consent", "contract", "legal_obligation", "vital_interests", "public_task", "legitimate_interests"]}',
            'severity': 'high',
            'is_active': 1,
            'remark': 'Article 6(1) - 必须明确并记录处理的合法依据'
        },
        # Article 7: 同意条件
        {
            'rule_code': 'GDPR-7.1',
            'rule_name': '同意可证明性',
            'rule_type': 'compliance',
            'rule_description': 'GDPR第7条第1款：如果处理基于同意，控制者应能够证明数据主体已同意处理其个人数据',
            'rule_expression': '{"consent_demonstrable": true, "consent_record_kept": true}',
            'severity': 'high',
            'is_active': 1,
            'remark': 'Article 7(1) - 需要保留同意记录以供证明'
        },
        {
            'rule_code': 'GDPR-7.2',
            'rule_name': '同意请求清晰性',
            'rule_type': 'compliance',
            'rule_description': 'GDPR第7条第2款：如果在书面声明中提出同意请求，且该声明还涉及其他事项，则同意请求必须以清晰可辨的形式呈现，使用清晰明了的语言',
            'rule_expression': '{"consent_distinguishable": true, "language_clear": true, "language_plain": true}',
            'severity': 'medium',
            'is_active': 1,
            'remark': 'Article 7(2) - 同意请求不得隐藏在其他条款中'
        },
        {
            'rule_code': 'GDPR-7.3',
            'rule_name': '撤回同意权利',
            'rule_type': 'compliance',
            'rule_description': 'GDPR第7条第3款：数据主体有权随时撤回其同意，撤回同意应与给予同意一样简便',
            'rule_expression': '{"consent_withdrawable": true, "withdrawal_as_easy_as_giving": true}',
            'severity': 'medium',
            'is_active': 1,
            'remark': 'Article 7(3) - 需要提供简便的同意撤回机制'
        },
        # Article 12-23: 数据主体权利
        {
            'rule_code': 'GDPR-12.1',
            'rule_name': '透明信息提供',
            'rule_type': 'compliance',
            'rule_description': 'GDPR第12条第1款：控制者应采取适当措施，以简洁、透明、易懂和易获取的形式，使用清晰明了的语言向数据主体提供信息',
            'rule_expression': '{"information_concise": true, "information_transparent": true, "information_intelligible": true, "information_accessible": true, "language_clear": true}',
            'severity': 'medium',
            'is_active': 1,
            'remark': 'Article 12(1) - 隐私通知必须用户友好'
        },
        {
            'rule_code': 'GDPR-15',
            'rule_name': '访问权',
            'rule_type': 'data_subject_rights',
            'rule_description': 'GDPR第15条：数据主体有权从控制者处获得关于其个人数据是否正在被处理的确认，以及访问这些数据和相关信息的权利',
            'rule_expression': '{"access_right_provided": true, "response_within_one_month": true, "information_complete": true}',
            'severity': 'high',
            'is_active': 1,
            'remark': 'Article 15 - 需要在一个月内响应访问请求'
        },
        {
            'rule_code': 'GDPR-16',
            'rule_name': '更正权',
            'rule_type': 'data_subject_rights',
            'rule_description': 'GDPR第16条：数据主体有权要求控制者不拖延地更正有关他或她的不准确个人数据',
            'rule_expression': '{"rectification_right_provided": true, "rectification_without_delay": true}',
            'severity': 'medium',
            'is_active': 1,
            'remark': 'Article 16 - 需要及时更正不准确数据'
        },
        {
            'rule_code': 'GDPR-17',
            'rule_name': '删除权（被遗忘权）',
            'rule_type': 'data_subject_rights',
            'rule_description': 'GDPR第17条：在特定情况下，数据主体有权要求控制者不拖延地删除有关他或她的个人数据',
            'rule_expression': '{"erasure_right_provided": true, "erasure_without_delay": true, "exceptions_documented": true}',
            'severity': 'high',
            'is_active': 1,
            'remark': 'Article 17 - 需要提供数据删除机制（存在例外情况）'
        },
        {
            'rule_code': 'GDPR-18',
            'rule_name': '限制处理权',
            'rule_type': 'data_subject_rights',
            'rule_description': 'GDPR第18条：数据主体有权在特定情况下要求控制者限制对其个人数据的处理',
            'rule_expression': '{"restriction_right_provided": true, "restriction_conditions_met": true}',
            'severity': 'medium',
            'is_active': 1,
            'remark': 'Article 18 - 需要支持限制处理请求'
        },
        {
            'rule_code': 'GDPR-20',
            'rule_name': '数据可携权',
            'rule_type': 'data_subject_rights',
            'rule_description': 'GDPR第20条：数据主体有权以结构化、常用和机器可读的格式接收其提供给控制者的个人数据，并有权将这些数据传输给另一控制者',
            'rule_expression': '{"portability_right_provided": true, "format_structured": true, "format_machine_readable": true}',
            'severity': 'medium',
            'is_active': 1,
            'remark': 'Article 20 - 需要提供数据导出功能（JSON、CSV等格式）'
        },
        {
            'rule_code': 'GDPR-21',
            'rule_name': '反对权',
            'rule_type': 'data_subject_rights',
            'rule_description': 'GDPR第21条：数据主体有权基于其特殊情况反对基于合法利益或公共利益的数据处理',
            'rule_expression': '{"objection_right_provided": true, "objection_honored": true}',
            'severity': 'medium',
            'is_active': 1,
            'remark': 'Article 21 - 需要尊重数据主体的反对权'
        },
        {
            'rule_code': 'GDPR-22',
            'rule_name': '自动化决策和分析',
            'rule_type': 'compliance',
            'rule_description': 'GDPR第22条：数据主体有权不受仅基于自动化处理（包括分析）的决定的约束，该决定对其产生法律效力或类似的重大影响',
            'rule_expression': '{"automated_decision_disclosed": true, "human_intervention_available": true, "right_to_explanation": true}',
            'severity': 'high',
            'is_active': 1,
            'remark': 'Article 22 - 自动化决策需要披露并提供人工干预机会'
        },
        # Article 25: 设计和默认的数据保护
        {
            'rule_code': 'GDPR-25.1',
            'rule_name': '设计阶段的数据保护',
            'rule_type': 'security',
            'rule_description': 'GDPR第25条第1款：考虑到技术现状和实施成本，控制者应在确定处理方式时和处理时采取适当的技术和组织措施实施数据保护原则',
            'rule_expression': '{"privacy_by_design": true, "technical_measures": true, "organizational_measures": true, "pseudonymization": "when_appropriate", "minimization": true}',
            'severity': 'medium',
            'is_active': 1,
            'remark': 'Article 25(1) - 隐私设计，从系统设计阶段就考虑数据保护'
        },
        {
            'rule_code': 'GDPR-25.2',
            'rule_name': '默认的数据保护',
            'rule_type': 'security',
            'rule_description': 'GDPR第25条第2款：控制者应采取适当的技术和组织措施，确保默认情况下仅处理每个特定处理目的所需的个人数据',
            'rule_expression': '{"privacy_by_default": true, "default_minimal_collection": true, "default_minimal_processing": true, "default_minimal_storage": true, "default_minimal_accessibility": true}',
            'severity': 'medium',
            'is_active': 1,
            'remark': 'Article 25(2) - 默认隐私，默认设置应是最保护隐私的'
        },
        # Article 30: 处理活动记录
        {
            'rule_code': 'GDPR-30',
            'rule_name': '处理活动记录',
            'rule_type': 'compliance',
            'rule_description': 'GDPR第30条：控制者应维护其责任下的所有处理活动类别的记录，包括处理目的、数据类别、接收者、传输等信息',
            'rule_expression': '{"record_of_processing": true, "record_includes": ["purposes", "data_categories", "recipients", "transfers", "retention_periods", "security_measures"]}',
            'severity': 'high',
            'is_active': 1,
            'remark': 'Article 30 - 需要维护详细的处理活动记录（ROPA）'
        },
        # Article 32: 处理的安全性
        {
            'rule_code': 'GDPR-32.1',
            'rule_name': '技术和组织安全措施',
            'rule_type': 'security',
            'rule_description': 'GDPR第32条第1款：考虑到技术现状和实施成本，控制者和处理者应采取适当措施确保与风险相称的安全水平',
            'rule_expression': '{"security_measures": ["pseudonymization", "encryption", "confidentiality", "integrity", "availability", "resilience"], "risk_assessment": true, "regular_testing": true}',
            'severity': 'high',
            'is_active': 1,
            'remark': 'Article 32(1) - 需要实施加密、访问控制等安全措施'
        },
        {
            'rule_code': 'GDPR-32.1.a',
            'rule_name': '数据加密',
            'rule_type': 'security',
            'rule_description': 'GDPR第32条第1款(a)：个人数据和处理系统应采用假名化和加密技术',
            'rule_expression': '{"encryption_at_rest": true, "encryption_in_transit": true, "pseudonymization_where_appropriate": true}',
            'severity': 'high',
            'is_active': 1,
            'remark': 'Article 32(1)(a) - 传输和存储时都应加密'
        },
        {
            'rule_code': 'GDPR-32.1.b',
            'rule_name': '系统持续保障',
            'rule_type': 'security',
            'rule_description': 'GDPR第32条第1款(b)：应确保处理系统和服务的持续保密性、完整性、可用性和弹性',
            'rule_expression': '{"confidentiality_ensured": true, "integrity_ensured": true, "availability_ensured": true, "resilience_ensured": true}',
            'severity': 'high',
            'is_active': 1,
            'remark': 'Article 32(1)(b) - 需要业务连续性和灾难恢复计划'
        },
        {
            'rule_code': 'GDPR-32.1.c',
            'rule_name': '数据恢复能力',
            'rule_type': 'security',
            'rule_description': 'GDPR第32条第1款(c)：应具备在发生物理或技术事件后及时恢复个人数据可用性和访问的能力',
            'rule_expression': '{"backup_regular": true, "recovery_tested": true, "recovery_timely": true}',
            'severity': 'medium',
            'is_active': 1,
            'remark': 'Article 32(1)(c) - 需要定期备份和测试恢复能力'
        },
        {
            'rule_code': 'GDPR-32.1.d',
            'rule_name': '安全措施有效性测试',
            'rule_type': 'security',
            'rule_description': 'GDPR第32条第1款(d)：应定期测试、评估和评价技术和组织措施有效性的流程',
            'rule_expression': '{"security_testing_regular": true, "security_assessment": true, "security_evaluation": true}',
            'severity': 'medium',
            'is_active': 1,
            'remark': 'Article 32(1)(d) - 需要定期进行安全审计和渗透测试'
        },
        # Article 33-34: 数据泄露通知
        {
            'rule_code': 'GDPR-33.1',
            'rule_name': '向监管机构报告数据泄露',
            'rule_type': 'security',
            'rule_description': 'GDPR第33条第1款：除非不太可能对个人权利和自由造成风险，否则控制者应在知悉后72小时内向监管机构报告个人数据泄露',
            'rule_expression': '{"breach_detection": true, "breach_notification_within_72h": true, "breach_documentation": true}',
            'severity': 'critical',
            'is_active': 1,
            'remark': 'Article 33(1) - 数据泄露72小时内必须报告给监管机构'
        },
        {
            'rule_code': 'GDPR-34.1',
            'rule_name': '向数据主体通知数据泄露',
            'rule_type': 'security',
            'rule_description': 'GDPR第34条第1款：如果个人数据泄露可能对自然人的权利和自由造成高风险，控制者应不拖延地将泄露通知数据主体',
            'rule_expression': '{"high_risk_breach_notification": true, "notification_without_delay": true, "notification_clear_language": true}',
            'severity': 'critical',
            'is_active': 1,
            'remark': 'Article 34(1) - 高风险泄露需要直接通知受影响个人'
        },
        # Article 35: 数据保护影响评估 (DPIA)
        {
            'rule_code': 'GDPR-35.1',
            'rule_name': '数据保护影响评估',
            'rule_type': 'compliance',
            'rule_description': 'GDPR第35条第1款：如果某类型的处理（特别是使用新技术）可能对自然人的权利和自由造成高风险，控制者应在处理前进行影响评估',
            'rule_expression': '{"dpia_required": true, "dpia_before_processing": true, "high_risk_processing_identified": true}',
            'severity': 'high',
            'is_active': 1,
            'remark': 'Article 35(1) - 高风险处理前必须进行DPIA'
        },
        # Article 44-50: 向第三国传输个人数据
        {
            'rule_code': 'GDPR-44',
            'rule_name': '数据传输一般原则',
            'rule_type': 'compliance',
            'rule_description': 'GDPR第44条：只有在控制者和处理者遵守本章规定条件的情况下，才允许向第三国或国际组织传输个人数据',
            'rule_expression': '{"transfer_to_third_country": false, "adequacy_decision": false, "appropriate_safeguards": false, "transfer_documented": true}',
            'severity': 'critical',
            'is_active': 1,
            'remark': 'Article 44 - 向欧盟外传输数据受严格限制'
        },
        {
            'rule_code': 'GDPR-45',
            'rule_name': '基于充分性决定的传输',
            'rule_type': 'compliance',
            'rule_description': 'GDPR第45条：仅当欧盟委员会已决定该第三国确保充分的保护水平时，才可向该第三国传输数据',
            'rule_expression': '{"adequacy_decision_exists": true, "third_country_adequate": true}',
            'severity': 'critical',
            'is_active': 1,
            'remark': 'Article 45 - 仅可向获得充分性认定的国家/地区传输'
        },
        {
            'rule_code': 'GDPR-46',
            'rule_name': '适当保障措施下的传输',
            'rule_type': 'compliance',
            'rule_description': 'GDPR第46条：在没有充分性决定的情况下，如果控制者提供了适当的保障措施（如标准合同条款、约束性公司规则），则可进行传输',
            'rule_expression': '{"appropriate_safeguards": true, "safeguard_type": ["SCC", "BCR", "approved_code", "certification"], "enforceable_rights": true}',
            'severity': 'critical',
            'is_active': 1,
            'remark': 'Article 46 - 跨境传输需要标准合同条款(SCC)或企业约束性规则(BCR)'
        }
    ]

    async with AsyncSession(async_engine) as session:
        try:
            print("开始导入GDPR规则...")

            # 检查是否已存在规则
            for rule_data in gdpr_rules:
                stmt = select(AuditRule).where(AuditRule.rule_code == rule_data['rule_code'])
                result = await session.execute(stmt)
                existing_rule = result.scalar_one_or_none()

                if existing_rule:
                    print(f"规则 {rule_data['rule_code']} 已存在，跳过")
                else:
                    new_rule = AuditRule(**rule_data)
                    session.add(new_rule)
                    print(f"添加规则: {rule_data['rule_code']} - {rule_data['rule_name']}")

            await session.commit()
            print(f"\n导入完成！共处理 {len(gdpr_rules)} 条规则")

        except Exception as e:
            await session.rollback()
            print(f"导入失败: {str(e)}")
            raise


if __name__ == "__main__":
    asyncio.run(import_gdpr_rules())

-- GDPR审计规则数据
-- 基于GDPR（欧盟通用数据保护条例）的核心条款

-- Article 5: 数据处理的七大基本原则

INSERT INTO audit_rule (rule_code, rule_name, rule_type, rule_description, rule_expression, severity, is_active, remark) VALUES
-- 1. 合法性、公平性和透明性原则
('GDPR-5.1.a', '合法性原则', 'compliance', 'GDPR第5条第1款(a)：个人数据必须基于合法依据进行处理（同意、合同、法律义务、切身利益、公共任务或合法利益）', '{"legal_basis": ["consent", "contract", "legal_obligation", "vital_interest", "public_task", "legitimate_interest"]}', 'high', 1, 'Article 5(1)(a) - 违反可能面临最高级别罚款：2000万欧元或全球年营业额的4%'),

('GDPR-5.1.a-2', '透明性原则', 'compliance', 'GDPR第5条第1款(a)：数据处理必须对数据主体透明，需清晰告知数据收集的性质、种类、目的和期限', '{"transparency_requirements": ["processing_purpose", "data_categories", "storage_period", "recipients", "data_subject_rights"]}', 'high', 1, 'Article 5(1)(a) - 需要提供清晰易懂的隐私通知'),

-- 2. 目的限制原则
('GDPR-5.1.b', '目的限制原则', 'compliance', 'GDPR第5条第1款(b)：个人数据必须为明确、具体和合法的目的而收集，不得以与这些目的不相容的方式进一步处理', '{"purpose_specified": true, "purpose_explicit": true, "purpose_legitimate": true, "compatible_use_only": true}', 'high', 1, 'Article 5(1)(b) - 禁止功能蠕变，数据用途必须与原始目的一致'),

-- 3. 数据最小化原则
('GDPR-5.1.c', '数据最小化原则', 'data_quality', 'GDPR第5条第1款(c)：处理的个人数据必须充分、相关，并限于与处理目的相关的必要范围内', '{"collect_only_necessary": true, "adequate_for_purpose": true, "relevant_to_purpose": true}', 'medium', 1, 'Article 5(1)(c) - 不得过度收集数据，仅收集实现目的所需的最少数据'),

-- 4. 准确性原则
('GDPR-5.1.d', '数据准确性原则', 'data_quality', 'GDPR第5条第1款(d)：个人数据必须准确，必要时保持最新；必须采取合理措施及时删除或更正不准确的数据', '{"data_accurate": true, "data_up_to_date": true, "error_correction_process": true}', 'medium', 1, 'Article 5(1)(d) - 需要建立数据更正和删除机制'),

-- 5. 存储限制原则
('GDPR-5.1.e', '存储限制原则', 'compliance', 'GDPR第5条第1款(e)：个人数据的保存形式不得超过实现处理目的所需的时间，应定义数据保留期限并定期审查', '{"retention_period_defined": true, "retention_necessary_only": true, "periodic_review": true}', 'medium', 1, 'Article 5(1)(e) - 需要制定数据保留政策和删除计划'),

-- 6. 完整性和保密性原则（安全性）
('GDPR-5.1.f', '数据安全原则', 'security', 'GDPR第5条第1款(f)：个人数据处理必须确保适当的安全性，包括防止未经授权或非法处理，防止意外丢失、破坏或损坏', '{"encryption_required": true, "access_control": true, "security_measures": ["technical", "organizational"], "breach_prevention": true}', 'high', 1, 'Article 5(1)(f) - 需要采取适当的技术和组织措施保护数据'),

-- 7. 问责制原则
('GDPR-5.2', '问责制原则', 'compliance', 'GDPR第5条第2款：数据控制者应负责并能够证明符合上述各项原则（问责制），需要记录处理活动并实施数据保护政策', '{"compliance_demonstration": true, "documentation_maintained": true, "dpia_when_required": true, "policies_implemented": true}', 'high', 1, 'Article 5(2) - 需要维护处理活动记录和合规证明'),

-- Article 9: 特殊类别个人数据（敏感数据）
('GDPR-9.1', '禁止处理敏感数据', 'sensitive_data', 'GDPR第9条第1款：原则上禁止处理揭示种族、民族、政治观点、宗教信仰、工会成员身份、基因数据、生物识别数据、健康数据、性生活或性取向的个人数据', '{"special_categories": ["racial_origin", "ethnic_origin", "political_opinions", "religious_beliefs", "philosophical_beliefs", "trade_union_membership", "genetic_data", "biometric_data", "health_data", "sex_life", "sexual_orientation"], "processing_prohibited": true}', 'critical', 1, 'Article 9(1) - 敏感数据处理受严格限制，违反面临最高级别罚款'),

('GDPR-9.2.a', '敏感数据例外-明确同意', 'sensitive_data', 'GDPR第9条第2款(a)：仅在数据主体就一个或多个特定目的明确同意处理这些个人数据时，才可处理敏感数据', '{"explicit_consent_obtained": true, "consent_specific": true, "consent_informed": true, "consent_freely_given": true}', 'critical', 1, 'Article 9(2)(a) - 需要获得明确同意，同意必须是自愿、具体、知情和明确的'),

-- Article 6: 数据处理的合法性
('GDPR-6.1', '合法处理基础', 'compliance', 'GDPR第6条第1款：数据处理必须至少基于以下一种合法依据：同意、合同履行、法律义务、保护切身利益、公共利益任务或合法利益', '{"legal_basis_documented": true, "legal_basis_valid": ["consent", "contract", "legal_obligation", "vital_interests", "public_task", "legitimate_interests"]}', 'high', 1, 'Article 6(1) - 必须明确并记录处理的合法依据'),

-- Article 7: 同意条件
('GDPR-7.1', '同意可证明性', 'compliance', 'GDPR第7条第1款：如果处理基于同意，控制者应能够证明数据主体已同意处理其个人数据', '{"consent_demonstrable": true, "consent_record_kept": true}', 'high', 1, 'Article 7(1) - 需要保留同意记录以供证明'),

('GDPR-7.2', '同意请求清晰性', 'compliance', 'GDPR第7条第2款：如果在书面声明中提出同意请求，且该声明还涉及其他事项，则同意请求必须以清晰可辨的形式呈现，使用清晰明了的语言', '{"consent_distinguishable": true, "language_clear": true, "language_plain": true}', 'medium', 1, 'Article 7(2) - 同意请求不得隐藏在其他条款中'),

('GDPR-7.3', '撤回同意权利', 'compliance', 'GDPR第7条第3款：数据主体有权随时撤回其同意，撤回同意应与给予同意一样简便', '{"consent_withdrawable": true, "withdrawal_as_easy_as_giving": true}', 'medium', 1, 'Article 7(3) - 需要提供简便的同意撤回机制'),

-- Article 12-23: 数据主体权利
('GDPR-12.1', '透明信息提供', 'compliance', 'GDPR第12条第1款：控制者应采取适当措施，以简洁、透明、易懂和易获取的形式，使用清晰明了的语言向数据主体提供信息', '{"information_concise": true, "information_transparent": true, "information_intelligible": true, "information_accessible": true, "language_clear": true}', 'medium', 1, 'Article 12(1) - 隐私通知必须用户友好'),

('GDPR-15', '访问权', 'data_subject_rights', 'GDPR第15条：数据主体有权从控制者处获得关于其个人数据是否正在被处理的确认，以及访问这些数据和相关信息的权利', '{"access_right_provided": true, "response_within_one_month": true, "information_complete": true}', 'high', 1, 'Article 15 - 需要在一个月内响应访问请求'),

('GDPR-16', '更正权', 'data_subject_rights', 'GDPR第16条：数据主体有权要求控制者不拖延地更正有关他或她的不准确个人数据', '{"rectification_right_provided": true, "rectification_without_delay": true}', 'medium', 1, 'Article 16 - 需要及时更正不准确数据'),

('GDPR-17', '删除权（被遗忘权）', 'data_subject_rights', 'GDPR第17条：在特定情况下，数据主体有权要求控制者不拖延地删除有关他或她的个人数据', '{"erasure_right_provided": true, "erasure_without_delay": true, "exceptions_documented": true}', 'high', 1, 'Article 17 - 需要提供数据删除机制（存在例外情况）'),

('GDPR-18', '限制处理权', 'data_subject_rights', 'GDPR第18条：数据主体有权在特定情况下要求控制者限制对其个人数据的处理', '{"restriction_right_provided": true, "restriction_conditions_met": true}', 'medium', 1, 'Article 18 - 需要支持限制处理请求'),

('GDPR-20', '数据可携权', 'data_subject_rights', 'GDPR第20条：数据主体有权以结构化、常用和机器可读的格式接收其提供给控制者的个人数据，并有权将这些数据传输给另一控制者', '{"portability_right_provided": true, "format_structured": true, "format_machine_readable": true}', 'medium', 1, 'Article 20 - 需要提供数据导出功能（JSON、CSV等格式）'),

('GDPR-21', '反对权', 'data_subject_rights', 'GDPR第21条：数据主体有权基于其特殊情况反对基于合法利益或公共利益的数据处理', '{"objection_right_provided": true, "objection_honored": true}', 'medium', 1, 'Article 21 - 需要尊重数据主体的反对权'),

('GDPR-22', '自动化决策和分析', 'compliance', 'GDPR第22条：数据主体有权不受仅基于自动化处理（包括分析）的决定的约束，该决定对其产生法律效力或类似的重大影响', '{"automated_decision_disclosed": true, "human_intervention_available": true, "right_to_explanation": true}', 'high', 1, 'Article 22 - 自动化决策需要披露并提供人工干预机会'),

-- Article 25: 设计和默认的数据保护
('GDPR-25.1', '设计阶段的数据保护', 'security', 'GDPR第25条第1款：考虑到技术现状和实施成本，控制者应在确定处理方式时和处理时采取适当的技术和组织措施实施数据保护原则', '{"privacy_by_design": true, "technical_measures": true, "organizational_measures": true, "pseudonymization": "when_appropriate", "minimization": true}', 'medium', 1, 'Article 25(1) - 隐私设计，从系统设计阶段就考虑数据保护'),

('GDPR-25.2', '默认的数据保护', 'security', 'GDPR第25条第2款：控制者应采取适当的技术和组织措施，确保默认情况下仅处理每个特定处理目的所需的个人数据', '{"privacy_by_default": true, "default_minimal_collection": true, "default_minimal_processing": true, "default_minimal_storage": true, "default_minimal_accessibility": true}', 'medium', 1, 'Article 25(2) - 默认隐私，默认设置应是最保护隐私的'),

-- Article 30: 处理活动记录
('GDPR-30', '处理活动记录', 'compliance', 'GDPR第30条：控制者应维护其责任下的所有处理活动类别的记录，包括处理目的、数据类别、接收者、传输等信息', '{"record_of_processing": true, "record_includes": ["purposes", "data_categories", "recipients", "transfers", "retention_periods", "security_measures"]}', 'high', 1, 'Article 30 - 需要维护详细的处理活动记录（ROPA）'),

-- Article 32: 处理的安全性
('GDPR-32.1', '技术和组织安全措施', 'security', 'GDPR第32条第1款：考虑到技术现状和实施成本，控制者和处理者应采取适当措施确保与风险相称的安全水平', '{"security_measures": ["pseudonymization", "encryption", "confidentiality", "integrity", "availability", "resilience"], "risk_assessment": true, "regular_testing": true}', 'high', 1, 'Article 32(1) - 需要实施加密、访问控制等安全措施'),

('GDPR-32.1.a', '数据加密', 'security', 'GDPR第32条第1款(a)：个人数据和处理系统应采用假名化和加密技术', '{"encryption_at_rest": true, "encryption_in_transit": true, "pseudonymization_where_appropriate": true}', 'high', 1, 'Article 32(1)(a) - 传输和存储时都应加密'),

('GDPR-32.1.b', '系统持续保障', 'security', 'GDPR第32条第1款(b)：应确保处理系统和服务的持续保密性、完整性、可用性和弹性', '{"confidentiality_ensured": true, "integrity_ensured": true, "availability_ensured": true, "resilience_ensured": true}', 'high', 1, 'Article 32(1)(b) - 需要业务连续性和灾难恢复计划'),

('GDPR-32.1.c', '数据恢复能力', 'security', 'GDPR第32条第1款(c)：应具备在发生物理或技术事件后及时恢复个人数据可用性和访问的能力', '{"backup_regular": true, "recovery_tested": true, "recovery_timely": true}', 'medium', 1, 'Article 32(1)(c) - 需要定期备份和测试恢复能力'),

('GDPR-32.1.d', '安全措施有效性测试', 'security', 'GDPR第32条第1款(d)：应定期测试、评估和评价技术和组织措施有效性的流程', '{"security_testing_regular": true, "security_assessment": true, "security_evaluation": true}', 'medium', 1, 'Article 32(1)(d) - 需要定期进行安全审计和渗透测试'),

-- Article 33-34: 数据泄露通知
('GDPR-33.1', '向监管机构报告数据泄露', 'security', 'GDPR第33条第1款：除非不太可能对个人权利和自由造成风险，否则控制者应在知悉后72小时内向监管机构报告个人数据泄露', '{"breach_detection": true, "breach_notification_within_72h": true, "breach_documentation": true}', 'critical', 1, 'Article 33(1) - 数据泄露72小时内必须报告给监管机构'),

('GDPR-34.1', '向数据主体通知数据泄露', 'security', 'GDPR第34条第1款：如果个人数据泄露可能对自然人的权利和自由造成高风险，控制者应不拖延地将泄露通知数据主体', '{"high_risk_breach_notification": true, "notification_without_delay": true, "notification_clear_language": true}', 'critical', 1, 'Article 34(1) - 高风险泄露需要直接通知受影响个人'),

-- Article 35: 数据保护影响评估 (DPIA)
('GDPR-35.1', '数据保护影响评估', 'compliance', 'GDPR第35条第1款：如果某类型的处理（特别是使用新技术）可能对自然人的权利和自由造成高风险，控制者应在处理前进行影响评估', '{"dpia_required": true, "dpia_before_processing": true, "high_risk_processing_identified": true}', 'high', 1, 'Article 35(1) - 高风险处理前必须进行DPIA'),

-- Article 44-50: 向第三国传输个人数据
('GDPR-44', '数据传输一般原则', 'compliance', 'GDPR第44条：只有在控制者和处理者遵守本章规定条件的情况下，才允许向第三国或国际组织传输个人数据', '{"transfer_to_third_country": false, "adequacy_decision": false, "appropriate_safeguards": false, "transfer_documented": true}', 'critical', 1, 'Article 44 - 向欧盟外传输数据受严格限制'),

('GDPR-45', '基于充分性决定的传输', 'compliance', 'GDPR第45条：仅当欧盟委员会已决定该第三国确保充分的保护水平时，才可向该第三国传输数据', '{"adequacy_decision_exists": true, "third_country_adequate": true}', 'critical', 1, 'Article 45 - 仅可向获得充分性认定的国家/地区传输'),

('GDPR-46', '适当保障措施下的传输', 'compliance', 'GDPR第46条：在没有充分性决定的情况下，如果控制者提供了适当的保障措施（如标准合同条款、约束性公司规则），则可进行传输', '{"appropriate_safeguards": true, "safeguard_type": ["SCC", "BCR", "approved_code", "certification"], "enforceable_rights": true}', 'critical', 1, 'Article 46 - 跨境传输需要标准合同条款(SCC)或企业约束性规则(BCR)');

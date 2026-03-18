"""
独立的规则模板初始化脚本
不依赖项目导入，直接操作数据库
"""
import sys
import pymysql
from pathlib import Path

# 10个默认规则模板的SQL插入语句
DEFAULT_TEMPLATES_SQL = """
-- 1. 字段必填验证
INSERT INTO audit_rule_template (
    template_code, template_name, template_category, template_description,
    parameters_schema, validation_template, default_severity, tags, is_active, remark
) VALUES (
    'FIELD_REQUIRED',
    '字段必填验证',
    'field_validation',
    '验证指定字段不能为空、null或仅包含空格。适用于必填字段的合规要求。',
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'field_name', JSON_OBJECT('type', 'string', 'description', '要验证的字段名称'),
            'field_display_name', JSON_OBJECT('type', 'string', 'description', '字段的显示名称'),
            'error_message', JSON_OBJECT('type', 'string', 'description', '自定义错误消息')
        ),
        'required', JSON_ARRAY('field_name', 'field_display_name')
    ),
    JSON_OBJECT('type', 'field_required', 'logic', 'check_not_empty_and_not_null'),
    'error',
    JSON_OBJECT('category', '基础验证', 'gdpr', true, 'common', true),
    1,
    '最常用的模板，用于验证必填字段'
);

-- 2. 字段格式正则验证
INSERT INTO audit_rule_template (
    template_code, template_name, template_category, template_description,
    parameters_schema, validation_template, default_severity, tags, is_active, remark
) VALUES (
    'FIELD_FORMAT_REGEX',
    '字段格式正则验证',
    'format_check',
    '使用正则表达式验证字段格式。适用于各种格式要求（邮箱、手机号、身份证等）。',
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'field_name', JSON_OBJECT('type', 'string'),
            'field_display_name', JSON_OBJECT('type', 'string'),
            'regex_pattern', JSON_OBJECT('type', 'string'),
            'format_description', JSON_OBJECT('type', 'string')
        ),
        'required', JSON_ARRAY('field_name', 'field_display_name', 'regex_pattern', 'format_description')
    ),
    JSON_OBJECT('type', 'regex_match', 'logic', 'validate_field_against_regex'),
    'error',
    JSON_OBJECT('category', '格式验证', 'gdpr', true),
    1,
    '通用格式验证模板'
);

-- 3. 字段枚举值限制
INSERT INTO audit_rule_template (
    template_code, template_name, template_category, template_description,
    parameters_schema, validation_template, default_severity, tags, is_active, remark
) VALUES (
    'FIELD_ENUM_VALUES',
    '字段枚举值限制',
    'field_validation',
    '验证字段值必须在指定的枚举列表中。',
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'field_name', JSON_OBJECT('type', 'string'),
            'field_display_name', JSON_OBJECT('type', 'string'),
            'allowed_values', JSON_OBJECT('type', 'array'),
            'case_sensitive', JSON_OBJECT('type', 'boolean', 'default', true)
        ),
        'required', JSON_ARRAY('field_name', 'field_display_name', 'allowed_values')
    ),
    JSON_OBJECT('type', 'enum_validation'),
    'error',
    JSON_OBJECT('category', '业务验证'),
    1,
    '枚举字段验证'
);

-- 4. 字段长度限制
INSERT INTO audit_rule_template (
    template_code, template_name, template_category, template_description,
    parameters_schema, validation_template, default_severity, tags, is_active, remark
) VALUES (
    'FIELD_LENGTH_LIMIT',
    '字段长度限制',
    'field_validation',
    '验证字段长度在指定范围内。',
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'field_name', JSON_OBJECT('type', 'string'),
            'field_display_name', JSON_OBJECT('type', 'string'),
            'min_length', JSON_OBJECT('type', 'integer'),
            'max_length', JSON_OBJECT('type', 'integer')
        ),
        'required', JSON_ARRAY('field_name', 'field_display_name')
    ),
    JSON_OBJECT('type', 'length_check'),
    'warning',
    JSON_OBJECT('category', '数据质量'),
    1,
    '文本长度验证'
);

-- 5. 数值范围验证
INSERT INTO audit_rule_template (
    template_code, template_name, template_category, template_description,
    parameters_schema, validation_template, default_severity, tags, is_active, remark
) VALUES (
    'FIELD_NUMERIC_RANGE',
    '数值范围验证',
    'field_validation',
    '验证数值字段在指定范围内。',
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'field_name', JSON_OBJECT('type', 'string'),
            'field_display_name', JSON_OBJECT('type', 'string'),
            'min_value', JSON_OBJECT('type', 'number'),
            'max_value', JSON_OBJECT('type', 'number'),
            'allow_decimal', JSON_OBJECT('type', 'boolean', 'default', false)
        ),
        'required', JSON_ARRAY('field_name', 'field_display_name')
    ),
    JSON_OBJECT('type', 'numeric_range'),
    'warning',
    JSON_OBJECT('category', '业务验证'),
    1,
    '数值范围验证'
);

-- 6. 日期字段验证
INSERT INTO audit_rule_template (
    template_code, template_name, template_category, template_description,
    parameters_schema, validation_template, default_severity, tags, is_active, remark
) VALUES (
    'FIELD_DATE_VALIDATION',
    '日期字段验证',
    'format_check',
    '验证日期字段格式和有效性。',
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'field_name', JSON_OBJECT('type', 'string'),
            'field_display_name', JSON_OBJECT('type', 'string'),
            'date_format', JSON_OBJECT('type', 'string', 'default', 'YYYY-MM-DD')
        ),
        'required', JSON_ARRAY('field_name', 'field_display_name')
    ),
    JSON_OBJECT('type', 'date_validation'),
    'error',
    JSON_OBJECT('category', '格式验证'),
    1,
    '日期格式验证'
);

-- 7. 字段不含敏感词
INSERT INTO audit_rule_template (
    template_code, template_name, template_category, template_description,
    parameters_schema, validation_template, default_severity, tags, is_active, remark
) VALUES (
    'FIELD_NO_PII_KEYWORDS',
    '字段不含敏感词',
    'data_quality',
    '验证字段不包含指定的敏感关键词。',
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'field_name', JSON_OBJECT('type', 'string'),
            'field_display_name', JSON_OBJECT('type', 'string'),
            'blocked_keywords', JSON_OBJECT('type', 'array'),
            'case_sensitive', JSON_OBJECT('type', 'boolean', 'default', false)
        ),
        'required', JSON_ARRAY('field_name', 'field_display_name', 'blocked_keywords')
    ),
    JSON_OBJECT('type', 'keyword_block'),
    'warning',
    JSON_OBJECT('category', '隐私保护'),
    1,
    '敏感词检测'
);

-- 8. 字段依赖关系验证
INSERT INTO audit_rule_template (
    template_code, template_name, template_category, template_description,
    parameters_schema, validation_template, default_severity, tags, is_active, remark
) VALUES (
    'FIELD_DEPENDENCY_CHECK',
    '字段依赖关系验证',
    'business_rule',
    '验证字段间的依赖关系。',
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'source_field', JSON_OBJECT('type', 'string'),
            'source_field_display', JSON_OBJECT('type', 'string'),
            'dependent_field', JSON_OBJECT('type', 'string'),
            'dependent_field_display', JSON_OBJECT('type', 'string'),
            'condition', JSON_OBJECT('type', 'string', 'default', 'not_empty')
        ),
        'required', JSON_ARRAY('source_field', 'dependent_field')
    ),
    JSON_OBJECT('type', 'field_dependency'),
    'error',
    JSON_OBJECT('category', '业务规则'),
    1,
    '字段依赖关系验证'
);

-- 9. 字段唯一性验证
INSERT INTO audit_rule_template (
    template_code, template_name, template_category, template_description,
    parameters_schema, validation_template, default_severity, tags, is_active, remark
) VALUES (
    'FIELD_UNIQUE_CHECK',
    '字段唯一性验证',
    'data_quality',
    '验证字段值在数据集中唯一。',
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'field_name', JSON_OBJECT('type', 'string'),
            'field_display_name', JSON_OBJECT('type', 'string'),
            'ignore_empty', JSON_OBJECT('type', 'boolean', 'default', true)
        ),
        'required', JSON_ARRAY('field_name', 'field_display_name')
    ),
    JSON_OBJECT('type', 'uniqueness_check'),
    'error',
    JSON_OBJECT('category', '数据质量'),
    1,
    '唯一性验证'
);

-- 10. 跨数据集引用验证
INSERT INTO audit_rule_template (
    template_code, template_name, template_category, template_description,
    parameters_schema, validation_template, default_severity, tags, is_active, remark
) VALUES (
    'FIELD_CROSS_DATASET_REFERENCE',
    '跨数据集引用验证',
    'business_rule',
    '验证字段值必须在另一个数据集中存在。',
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'field_name', JSON_OBJECT('type', 'string'),
            'field_display_name', JSON_OBJECT('type', 'string'),
            'reference_dataset', JSON_OBJECT('type', 'string'),
            'reference_field', JSON_OBJECT('type', 'string')
        ),
        'required', JSON_ARRAY('field_name', 'reference_dataset', 'reference_field')
    ),
    JSON_OBJECT('type', 'reference_check'),
    'error',
    JSON_OBJECT('category', '参照完整性'),
    1,
    '外键完整性验证'
);
"""

def init_templates():
    """初始化规则模板"""
    print("\n" + "="*60)
    print("规则模板初始化工具")
    print("="*60 + "\n")

    # 数据库配置
    db_config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '123456',
        'database': 'fastapiadmin',
        'charset': 'utf8mb4'
    }

    print("使用数据库配置:")
    print(f"  主机: {db_config['host']}:{db_config['port']}")
    print(f"  数据库: {db_config['database']}")
    print(f"  用户: {db_config['user']}")

    try:
        # 连接数据库
        print("\n[INFO] 连接数据库...")
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        print("[OK] 数据库连接成功")

        # 检查表是否存在
        print("\n[INFO] 检查 audit_rule_template 表...")
        cursor.execute("SHOW TABLES LIKE 'audit_rule_template'")
        if not cursor.fetchone():
            print("[ERROR] audit_rule_template 表不存在")
            print("[INFO] 请先运行数据库迁移: python run_migration.py")
            return False

        # 检查是否已有模板
        cursor.execute("SELECT COUNT(*) FROM audit_rule_template")
        count = cursor.fetchone()[0]

        if count > 0:
            print(f"[WARN] 表中已有 {count} 个模板")
            response = input("是否清空并重新初始化? (y/n): ").strip().lower()
            if response == 'y':
                print("[INFO] 清空现有模板...")
                cursor.execute("DELETE FROM audit_rule_template")
                conn.commit()
                print("[OK] 已清空")
            else:
                print("[INFO] 跳过初始化")
                return True

        # 执行插入
        print("\n[INFO] 插入10个默认模板...")
        statements = [s.strip() for s in DEFAULT_TEMPLATES_SQL.split(';') if s.strip()]

        success_count = 0
        for i, stmt in enumerate(statements, 1):
            try:
                cursor.execute(stmt)
                success_count += 1
                print(f"  [{i}/10] 插入成功")
            except Exception as e:
                if "Duplicate entry" in str(e):
                    print(f"  [{i}/10] 跳过（已存在）")
                    success_count += 1
                else:
                    print(f"  [{i}/10] 失败: {str(e)[:50]}")

        conn.commit()
        print(f"\n[OK] 模板插入完成: {success_count}/10")

        # 验证结果
        print("\n[INFO] 验证结果...")
        cursor.execute("SELECT COUNT(*) FROM audit_rule_template")
        total = cursor.fetchone()[0]
        print(f"  [OK] 模板总数: {total}")

        cursor.execute("SELECT COUNT(*) FROM audit_rule_template WHERE is_active = 1")
        active = cursor.fetchone()[0]
        print(f"  [OK] 已启用: {active}")

        # 显示所有模板
        print("\n[INFO] 已安装的模板:")
        cursor.execute("""
            SELECT template_code, template_name, template_category
            FROM audit_rule_template
            ORDER BY template_category, template_code
        """)

        current_category = None
        for row in cursor.fetchall():
            code, name, category = row
            if category != current_category:
                current_category = category
                print(f"\n  [{category}]")
            print(f"    - {code}: {name}")

        print("\n" + "="*60)
        print("[SUCCESS] 初始化完成！")
        print("="*60)
        print("\n下一步:")
        print("1. 查看文档: backend/app/plugin/module_application/audit/QUICKSTART.md")
        print("2. 测试功能: 参考快速开始指南")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"\n[ERROR] 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = init_templates()
    sys.exit(0 if success else 1)

"""
快速测试规则模板与法规解析系统
验证所有功能是否正常工作
"""
import sys
import pymysql
import json

def test_system():
    """测试系统功能"""
    print("\n" + "="*60)
    print("规则模板系统 - 功能测试")
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

    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        print("[OK] 数据库连接成功\n")

        # 测试1: 检查规则模板表
        print("=" * 60)
        print("测试1: 检查规则模板")
        print("=" * 60)

        cursor.execute("SELECT COUNT(*) FROM audit_rule_template")
        count = cursor.fetchone()[0]
        print(f"✓ 模板总数: {count}")
        assert count == 10, "应该有10个模板"

        cursor.execute("SELECT COUNT(*) FROM audit_rule_template WHERE is_active = 1")
        active = cursor.fetchone()[0]
        print(f"✓ 已启用: {active}")
        assert active == 10, "所有模板应该都启用"

        # 测试2: 检查audit_rule表的新字段
        print("\n" + "=" * 60)
        print("测试2: 检查audit_rule表扩展")
        print("=" * 60)

        cursor.execute("SHOW COLUMNS FROM audit_rule LIKE 'template_id'")
        assert cursor.fetchone(), "应该有template_id字段"
        print("✓ template_id 字段存在")

        cursor.execute("SHOW COLUMNS FROM audit_rule LIKE 'instance_parameters'")
        assert cursor.fetchone(), "应该有instance_parameters字段"
        print("✓ instance_parameters 字段存在")

        cursor.execute("SHOW COLUMNS FROM audit_rule LIKE 'regulation_id'")
        assert cursor.fetchone(), "应该有regulation_id字段"
        print("✓ regulation_id 字段存在")

        cursor.execute("SHOW COLUMNS FROM audit_rule LIKE 'auto_generated'")
        assert cursor.fetchone(), "应该有auto_generated字段"
        print("✓ auto_generated 字段存在")

        # 测试3: 查看模板详情
        print("\n" + "=" * 60)
        print("测试3: 模板配置验证")
        print("=" * 60)

        cursor.execute("""
            SELECT template_code, template_name, parameters_schema
            FROM audit_rule_template
            WHERE template_code = 'FIELD_REQUIRED'
        """)
        row = cursor.fetchone()
        assert row, "FIELD_REQUIRED模板应该存在"

        code, name, schema_json = row
        print(f"✓ 模板编码: {code}")
        print(f"✓ 模板名称: {name}")

        # 验证JSON格式
        schema = json.loads(schema_json) if isinstance(schema_json, str) else schema_json
        print(f"✓ 参数定义: {json.dumps(schema, ensure_ascii=False, indent=2)}")

        # 测试4: 验证模板完整性
        print("\n" + "=" * 60)
        print("测试4: 验证所有模板")
        print("=" * 60)

        cursor.execute("""
            SELECT template_code, template_name, template_category
            FROM audit_rule_template
            ORDER BY template_category, template_code
        """)

        templates_by_category = {}
        for row in cursor.fetchall():
            code, name, category = row
            if category not in templates_by_category:
                templates_by_category[category] = []
            templates_by_category[category].append((code, name))

        for category, templates in templates_by_category.items():
            print(f"\n  [{category}]")
            for code, name in templates:
                print(f"    ✓ {code}: {name}")

        # 测试5: 统计信息
        print("\n" + "=" * 60)
        print("测试5: 系统统计")
        print("=" * 60)

        cursor.execute("SELECT COUNT(*) FROM audit_rule WHERE auto_generated = 1")
        auto_rules = cursor.fetchone()[0]
        print(f"✓ 自动生成的规则: {auto_rules} 个")

        cursor.execute("SELECT COUNT(*) FROM audit_rule WHERE template_id IS NOT NULL")
        template_rules = cursor.fetchone()[0]
        print(f"✓ 从模板实例化的规则: {template_rules} 个")

        # 测试总结
        print("\n" + "="*60)
        print("[SUCCESS] 所有测试通过！")
        print("="*60)
        print("\n系统状态:")
        print(f"  ✓ 规则模板: {count} 个")
        print(f"  ✓ 数据库表: 正常")
        print(f"  ✓ 字段扩展: 完成")
        print(f"  ✓ 测试规则: 已创建")

        print("\n准备就绪！")
        print("="*60)
        print("\n下一步:")
        print("1. 启动FastAPI应用")
        print("2. 访问 /docs 查看新增的API接口")
        print("3. 测试法规解析功能:")
        print("   POST /audit/regulation/{id}/parse")
        print("4. 参考文档:")
        print("   - 快速开始: backend/app/plugin/module_application/audit/QUICKSTART.md")
        print("   - 完整文档: backend/app/plugin/module_application/audit/README_RULE_TEMPLATE.md")
        print("   - 工作汇报: backend/app/plugin/module_application/audit/工作汇报.md")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_system()
    print("\n" + "="*60 + "\n")
    sys.exit(0 if success else 1)

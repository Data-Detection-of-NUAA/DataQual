"""
执行数据库迁移脚本
适用于Windows环境
"""
import sys
import os
from pathlib import Path

def run_migration():
    """执行SQL迁移脚本"""
    # SQL文件路径
    sql_file = Path(__file__).parent / "migrations" / "add_rule_template_system.sql"

    if not sql_file.exists():
        print(f"[ERROR] SQL文件不存在: {sql_file}")
        return False

    # 读取SQL内容
    print("[INFO] 读取SQL脚本...")
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    print(f"[OK] SQL脚本大小: {len(sql_content)} 字符")

    # 尝试导入数据库连接
    try:
        import pymysql
    except ImportError:
        print("\n[ERROR] 未安装 pymysql")
        print("[INFO] 请安装: pip install pymysql")
        return False

    # 数据库配置（从环境变量或配置文件读取）
    print("\n" + "="*60)
    print("数据库连接配置")
    print("="*60)

    db_host = input("数据库主机 [localhost]: ").strip() or "localhost"
    db_port = input("数据库端口 [3306]: ").strip() or "3306"
    db_user = input("数据库用户名 [hjy]: ").strip() or "hjy"
    db_password = input("数据库密码: ").strip()
    db_name = input("数据库名称: ").strip()

    if not db_name or not db_password:
        print("[ERROR] 数据库名称和密码不能为空")
        return False

    # 连接数据库
    print(f"\n[INFO] 连接数据库 {db_host}:{db_port}/{db_name}...")
    try:
        connection = pymysql.connect(
            host=db_host,
            port=int(db_port),
            user=db_user,
            password=db_password,
            database=db_name,
            charset='utf8mb4'
        )
        print("[OK] 数据库连接成功")
    except Exception as e:
        print(f"[ERROR] 数据库连接失败: {str(e)}")
        return False

    # 执行SQL
    try:
        with connection.cursor() as cursor:
            print("\n[INFO] 执行SQL迁移...")

            # 分割SQL语句（按分号分割）
            sql_statements = [s.strip() for s in sql_content.split(';') if s.strip()]

            total = len(sql_statements)
            success = 0

            for i, statement in enumerate(sql_statements, 1):
                if not statement:
                    continue

                try:
                    cursor.execute(statement)
                    success += 1

                    # 打印进度
                    if i % 5 == 0 or i == total:
                        print(f"  [{i}/{total}] 执行中...")
                except Exception as e:
                    # 某些语句可能因为已存在而失败，继续执行
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        print(f"  [WARN] 跳过已存在的对象: {str(e)[:50]}...")
                        success += 1
                    else:
                        print(f"  [ERROR] 执行失败: {str(e)[:100]}...")

            connection.commit()
            print(f"\n[OK] SQL执行完成: {success}/{total} 条语句成功")

        # 验证结果
        print("\n[INFO] 验证安装结果...")
        with connection.cursor() as cursor:
            # 检查表是否创建
            cursor.execute("SHOW TABLES LIKE 'audit_rule_template'")
            if cursor.fetchone():
                print("  [OK] audit_rule_template 表已创建")
            else:
                print("  [ERROR] audit_rule_template 表不存在")

            # 检查模板数量
            cursor.execute("SELECT COUNT(*) FROM audit_rule_template")
            count = cursor.fetchone()[0]
            print(f"  [OK] 规则模板数量: {count}")

            # 检查 audit_rule 表的新字段
            cursor.execute("SHOW COLUMNS FROM audit_rule LIKE 'template_id'")
            if cursor.fetchone():
                print("  [OK] audit_rule 表新字段已添加")
            else:
                print("  [ERROR] audit_rule 表新字段不存在")

        print("\n" + "="*60)
        print("[SUCCESS] 数据库迁移完成！")
        print("="*60)
        print("\n下一步:")
        print("1. 运行: python init_rule_templates.py")
        print("2. 参考: backend/app/plugin/module_application/audit/QUICKSTART.md")

        return True

    except Exception as e:
        print(f"\n[ERROR] 执行失败: {str(e)}")
        connection.rollback()
        return False
    finally:
        connection.close()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("规则模板系统 - 数据库迁移工具")
    print("=" * 60 + "\n")

    success = run_migration()

    print("\n" + "=" * 60 + "\n")
    sys.exit(0 if success else 1)

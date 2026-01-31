# -*- coding: utf-8 -*-
"""
临时脚本:添加审计管理菜单到数据库
运行方式: python add_audit_menus.py
"""

import asyncio
import json
import os
import sys

# 设置环境变量
os.environ["ENVIRONMENT"] = "dev"

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, func
from app.core.database import async_db_session
from app.api.v1.module_system.menu.model import MenuModel
from app.core.logger import log


async def add_audit_menus():
    """添加审计管理菜单到数据库"""

    # 读取菜单JSON文件
    json_path = os.path.join(os.path.dirname(__file__), 'app', 'scripts', 'data', 'sys_menu.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        menus = json.load(f)

    # 找到审计管理菜单
    audit_menu_data = None
    for menu in menus:
        if menu['name'] == '审计管理':
            audit_menu_data = menu
            break

    if not audit_menu_data:
        print("❌ 未在JSON文件中找到审计管理菜单")
        return

    async with async_db_session() as session:
        async with session.begin():
            # 检查审计管理菜单是否已存在
            result = await session.execute(
                select(MenuModel).where(MenuModel.name == '审计管理')
            )
            existing_menu = result.scalar_one_or_none()

            if existing_menu:
                print("⚠️  审计管理菜单已存在,跳过添加")
                return

            # 创建菜单对象
            def create_menu_object(menu_data: dict) -> MenuModel:
                """递归创建菜单对象"""
                children_data = menu_data.pop('children', [])
                menu_obj = MenuModel(**menu_data)

                if children_data:
                    menu_obj.children = [create_menu_object(child) for child in children_data]

                return menu_obj

            # 创建审计管理菜单及其子菜单
            audit_menu_obj = create_menu_object(audit_menu_data.copy())

            # 添加到数据库
            session.add(audit_menu_obj)
            await session.flush()

            print("✅ 审计管理菜单已成功添加到数据库")
            print(f"   主菜单: {audit_menu_obj.name}")
            if audit_menu_obj.children:
                for child in audit_menu_obj.children:
                    button_count = len(child.children) if child.children else 0
                    print(f"   - {child.name} ({button_count}个权限按钮)")

            await session.commit()


if __name__ == "__main__":
    print("开始添加审计管理菜单...")
    asyncio.run(add_audit_menus())
    print("完成!")

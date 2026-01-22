# -*- coding: utf-8 -*-

"""
模型配置初始化脚本

用于初始化模型配置表(model_config)的基础数据
包含常用的深度学习模型配置
"""

import asyncio
import json
from pathlib import Path
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import log
from app.core.database import async_db_session, create_tables
from app.config.path_conf import SCRIPT_DIR
from app.plugin.module_train.train.model import ModelConfigModel
from app.api.v1.module_system.user.model import UserModel  # 导入以解析关系


class InitializeModelConfig:
    """初始化模型配置数据"""

    async def init_model_config(self) -> None:
        """
        执行模型配置初始化流程
        """
        # 先确保表已创建
        log.info("📋 检查并创建数据库表...")
        await create_tables()
        log.info("✅ 数据库表检查完成")

        async with async_db_session() as session:
            async with session.begin():
                await self.__init_model_config_data(session)
                await session.commit()
                log.info("✅ 模型配置初始化完成")

    async def __init_model_config_data(self, db: AsyncSession) -> None:
        """
        初始化模型配置数据

        参数:
        - db (AsyncSession): 异步数据库会话
        """
        table_name = ModelConfigModel.__tablename__

        # 检查表中是否已经有数据
        count_result = await db.execute(select(func.count()).select_from(ModelConfigModel))
        existing_count = count_result.scalar()

        if existing_count and existing_count > 0:
            log.warning(f"⚠️  跳过 {table_name} 表数据初始化（表已存在 {existing_count} 条记录）")
            return

        # 读取初始化数据
        data = await self.__get_model_config_data()
        if not data:
            log.warning(f"⚠️  跳过 {table_name} 表，无初始化数据")
            return

        try:
            objs = []
            for item in data:
                # 转换JSON字段为字符串
                if item.get('pretrained_weights'):
                    item['pretrained_weights'] = json.dumps(item['pretrained_weights'], ensure_ascii=False)
                if item.get('default_train_config'):
                    item['default_train_config'] = json.dumps(item['default_train_config'], ensure_ascii=False)
                if item.get('performance_metrics'):
                    item['performance_metrics'] = json.dumps(item['performance_metrics'], ensure_ascii=False)
                if item.get('hardware_requirements'):
                    item['hardware_requirements'] = json.dumps(item['hardware_requirements'], ensure_ascii=False)

                # 创建模型对象
                obj = ModelConfigModel(**item)
                objs.append(obj)

            db.add_all(objs)
            await db.flush()
            log.info(f"✅ 已向 {table_name} 表写入 {len(objs)} 条初始化数据")

        except Exception as e:
            log.error(f"❌ 初始化 {table_name} 表数据失败: {str(e)}")
            raise

    async def __get_model_config_data(self) -> list[dict]:
        """
        读取模型配置数据文件

        返回:
        - list[dict]: 解析后的 JSON 数据列表
        """
        json_path = SCRIPT_DIR / 'model_config.json'
        if not json_path.exists():
            log.error(f"❌ 文件不存在: {json_path}")
            return []

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.loads(f.read())
                log.info(f"📖 成功读取模型配置文件: {json_path}")
                return data
        except json.JSONDecodeError as e:
            log.error(f"❌ 解析 {json_path} 失败: {str(e)}")
            raise
        except Exception as e:
            log.error(f"❌ 读取 {json_path} 失败: {str(e)}")
            raise


async def main():
    """
    主函数 - 执行模型配置初始化
    """
    log.info("=" * 60)
    log.info("开始初始化模型配置数据...")
    log.info("=" * 60)

    initializer = InitializeModelConfig()
    await initializer.init_model_config()

    log.info("=" * 60)
    log.info("模型配置初始化完成！")
    log.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

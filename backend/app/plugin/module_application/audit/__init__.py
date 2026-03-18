"""
数据集合规审计系统模块
提供数据集合规审计功能，包括规则管理和审计任务管理
"""

__version__ = "1.0.0"
__author__ = "FastapiAdmin"
__description__ = "数据集合规审计系统"

# 导出路由
from .rule.controller import RuleRouter
from .task.controller import TaskRouter
from .regulation.controller import RegulationRouter
from .rule_template.controller import RuleTemplateRouter
from .common_controller import CommonRouter

__all__ = [
    'RuleRouter',
    'TaskRouter',
    'RegulationRouter',
    'RuleTemplateRouter',
    'CommonRouter'
]

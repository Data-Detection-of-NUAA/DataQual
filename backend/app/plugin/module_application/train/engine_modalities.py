# -*- coding: utf-8 -*-
"""
训练引擎模块初始化
自动注册所有模态和模型池
"""

# 导入核心架构
from .engine_core import (
    BaseDatasetLoader,
    BaseModelBuilder,
    BaseModelPool,
    ModalityManager,
    ModelPoolManager,
    ConfigTemplateManager
)

# 导入并注册所有模态
from . import modality_image  # 自动注册图像模态
from . import modality_text   # 自动注册文本模态
from . import modality_audio  # 自动注册音频模态

# 导出公共接口
__all__ = [
    # 核心类
    'BaseDatasetLoader',
    'BaseModelBuilder',
    'BaseModelPool',
    # 管理器
    'ModalityManager',
    'ModelPoolManager',
    'ConfigTemplateManager',
]


# 打印已注册的模态和模型（用于调试）
def print_registered_info():
    """打印已注册的模态和模型信息"""
    print("=" * 60)
    print("训练引擎已注册的模态和模型")
    print("=" * 60)

    # 打印模态
    modalities = ModalityManager.list_modalities()
    print(f"\n支持的模态 ({len(modalities)}):")
    for modality in modalities:
        print(f"  - {modality}")

    # 打印每个模态的模型
    all_models = ModelPoolManager.list_all_models()
    print(f"\n可用模型:")
    for modality, models in all_models.items():
        print(f"  {modality} ({len(models)} 个模型):")
        for model in models:
            print(f"    - {model}")

    print("=" * 60)


# 如果直接运行此模块，打印注册信息
if __name__ == "__main__":
    print_registered_info()

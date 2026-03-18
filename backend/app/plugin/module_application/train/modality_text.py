# -*- coding: utf-8 -*-
"""
文本模态实现（占位）
后续可扩展添加 BERT, GPT, T5 等文本模型
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from typing import Tuple, Dict, Any

from .engine_core import (
    BaseDatasetLoader,
    BaseModelBuilder,
    BaseModelPool,
    ModalityManager,
    ModelPoolManager
)


# ==================== 文本数据加载器 ====================

class TextDatasetLoader(BaseDatasetLoader):
    """文本数据集加载器（占位实现）"""

    def load(
        self,
        dataset_path: str,
        config: 'TrainingConfig'
    ) -> Tuple[DataLoader, DataLoader, int]:
        """加载文本数据集"""
        raise NotImplementedError(
            "文本数据集加载功能待实现。"
            "请实现此方法以支持文本模态训练。"
        )

    def get_transforms(self, config: 'TrainingConfig', is_train: bool):
        """获取文本预处理变换"""
        raise NotImplementedError("文本预处理功能待实现")


# ==================== 文本模型构建器（示例）====================

class BERTBuilder(BaseModelBuilder):
    """BERT 模型构建器（占位）"""

    def build(
        self,
        num_classes: int,
        pretrained: bool = True,
        **kwargs
    ) -> nn.Module:
        raise NotImplementedError(
            "BERT 模型构建功能待实现。"
            "可使用 transformers 库实现。"
        )

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "learning_rate": 2e-5,
            "batch_size": 16,
            "optimizer": "adamw",
            "scheduler": "linear"
        }


# ==================== 文本模型池 ====================

class TextModelPool(BaseModelPool):
    """文本模型池"""

    def register_models(self):
        """注册所有文本模型"""
        # 占位 - 后续添加实际模型
        # self.register('bert', BERTBuilder)
        # self.register('gpt2', GPT2Builder)
        # self.register('t5', T5Builder)
        pass


# ==================== 注册到管理器 ====================

def register_text_modality():
    """注册文本模态到管理器"""
    ModalityManager.register_loader('text', TextDatasetLoader)
    ModelPoolManager.register_pool('text', TextModelPool)


# 自动注册
register_text_modality()

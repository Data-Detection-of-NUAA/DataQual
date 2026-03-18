# -*- coding: utf-8 -*-
"""
音频模态实现（占位）
后续可扩展添加音频分类、语音识别等模型
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


# ==================== 音频数据加载器 ====================

class AudioDatasetLoader(BaseDatasetLoader):
    """音频数据集加载器（占位实现）"""

    def load(
        self,
        dataset_path: str,
        config: 'TrainingConfig'
    ) -> Tuple[DataLoader, DataLoader, int]:
        """加载音频数据集"""
        raise NotImplementedError(
            "音频数据集加载功能待实现。"
            "请实现此方法以支持音频模态训练。"
        )

    def get_transforms(self, config: 'TrainingConfig', is_train: bool):
        """获取音频预处理变换"""
        raise NotImplementedError("音频预处理功能待实现")


# ==================== 音频模型构建器（示例）====================

class Wav2VecBuilder(BaseModelBuilder):
    """Wav2Vec 模型构建器（占位）"""

    def build(
        self,
        num_classes: int,
        pretrained: bool = True,
        **kwargs
    ) -> nn.Module:
        raise NotImplementedError(
            "Wav2Vec 模型构建功能待实现。"
            "可使用 transformers 库实现。"
        )

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "learning_rate": 1e-4,
            "batch_size": 8,
            "optimizer": "adamw",
            "scheduler": "cosine"
        }


# ==================== 音频模型池 ====================

class AudioModelPool(BaseModelPool):
    """音频模型池"""

    def register_models(self):
        """注册所有音频模型"""
        # 占位 - 后续添加实际模型
        # self.register('wav2vec', Wav2VecBuilder)
        # self.register('hubert', HuBERTBuilder)
        # self.register('whisper', WhisperBuilder)
        pass


# ==================== 注册到管理器 ====================

def register_audio_modality():
    """注册音频模态到管理器"""
    ModalityManager.register_loader('audio', AudioDatasetLoader)
    ModelPoolManager.register_pool('audio', AudioModelPool)


# 自动注册
register_audio_modality()

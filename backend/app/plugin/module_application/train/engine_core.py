# -*- coding: utf-8 -*-
"""
训练引擎核心架构
实现模态分离和模型池管理的可扩展架构
"""

from abc import ABC, abstractmethod
from typing import Tuple, List, Dict, Any, Type
from torch.utils.data import DataLoader
import torch.nn as nn


# ==================== 基础抽象类 ====================

class BaseDatasetLoader(ABC):
    """数据集加载器基类"""

    @abstractmethod
    def load(
        self,
        dataset_path: str,
        config: 'TrainingConfig'
    ) -> Tuple[DataLoader, DataLoader, int]:
        """
        加载数据集

        参数:
        - dataset_path: 数据集路径
        - config: 训练配置

        返回:
        - train_loader: 训练数据加载器
        - val_loader: 验证数据加载器
        - train_size: 训练集大小
        """
        pass

    @abstractmethod
    def get_transforms(self, config: 'TrainingConfig', is_train: bool):
        """
        获取数据增强变换

        参数:
        - config: 训练配置
        - is_train: 是否为训练集

        返回:
        - transforms: 数据变换组合
        """
        pass


class BaseModelBuilder(ABC):
    """模型构建器基类"""

    @abstractmethod
    def build(
        self,
        num_classes: int,
        pretrained: bool = True,
        **kwargs
    ) -> nn.Module:
        """
        构建模型

        参数:
        - num_classes: 分类数量
        - pretrained: 是否使用预训练权重
        - **kwargs: 其他模型参数

        返回:
        - model: 模型实例
        """
        pass

    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]:
        """
        获取模型的默认训练配置

        返回:
        - config: 默认配置字典
        """
        pass


class BaseModelPool(ABC):
    """模型池基类"""

    def __init__(self):
        self.models: Dict[str, Type[BaseModelBuilder]] = {}
        self.register_models()

    @abstractmethod
    def register_models(self):
        """注册模型到池中 - 子类必须实现"""
        pass

    def register(self, model_name: str, builder_class: Type[BaseModelBuilder]):
        """
        注册单个模型

        参数:
        - model_name: 模型名称
        - builder_class: 模型构建器类
        """
        self.models[model_name.lower()] = builder_class

    def get_builder(self, model_name: str) -> BaseModelBuilder:
        """
        获取模型构建器实例

        参数:
        - model_name: 模型名称

        返回:
        - builder: 模型构建器实例
        """
        builder_class = self.models.get(model_name.lower())
        if not builder_class:
            available = ', '.join(self.models.keys())
            raise ValueError(
                f"模型 '{model_name}' 不存在于池中。"
                f"可用模型: {available}"
            )
        return builder_class()

    def list_models(self) -> List[str]:
        """
        列出所有可用模型

        返回:
        - models: 模型名称列表
        """
        return list(self.models.keys())

    def has_model(self, model_name: str) -> bool:
        """
        检查模型是否存在

        参数:
        - model_name: 模型名称

        返回:
        - exists: 是否存在
        """
        return model_name.lower() in self.models


# ==================== 管理器类 ====================

class ModalityManager:
    """
    模态管理器
    管理不同数据模态的加载器
    """

    _loaders: Dict[str, Type[BaseDatasetLoader]] = {}

    @classmethod
    def register_loader(
        cls,
        modality: str,
        loader_class: Type[BaseDatasetLoader]
    ):
        """
        注册模态加载器

        参数:
        - modality: 模态名称 (image/text/audio/video/sensor)
        - loader_class: 加载器类
        """
        cls._loaders[modality.lower()] = loader_class

    @classmethod
    def get_loader(cls, modality: str) -> BaseDatasetLoader:
        """
        根据模态获取对应的数据加载器

        参数:
        - modality: 模态名称

        返回:
        - loader: 数据加载器实例
        """
        loader_class = cls._loaders.get(modality.lower())
        if not loader_class:
            available = ', '.join(cls._loaders.keys())
            raise ValueError(
                f"不支持的模态: '{modality}'。"
                f"可用模态: {available}"
            )
        return loader_class()

    @classmethod
    def list_modalities(cls) -> List[str]:
        """
        列出所有支持的模态

        返回:
        - modalities: 模态名称列表
        """
        return list(cls._loaders.keys())

    @classmethod
    def has_modality(cls, modality: str) -> bool:
        """
        检查模态是否支持

        参数:
        - modality: 模态名称

        返回:
        - supported: 是否支持
        """
        return modality.lower() in cls._loaders


class ModelPoolManager:
    """
    模型池管理器
    管理不同模态的模型池
    """

    _pools: Dict[str, Type[BaseModelPool]] = {}

    @classmethod
    def register_pool(
        cls,
        modality: str,
        pool_class: Type[BaseModelPool]
    ):
        """
        注册模态的模型池

        参数:
        - modality: 模态名称
        - pool_class: 模型池类
        """
        cls._pools[modality.lower()] = pool_class

    @classmethod
    def get_pool(cls, modality: str) -> BaseModelPool:
        """
        根据模态获取对应的模型池

        参数:
        - modality: 模态名称

        返回:
        - pool: 模型池实例
        """
        pool_class = cls._pools.get(modality.lower())
        if not pool_class:
            available = ', '.join(cls._pools.keys())
            raise ValueError(
                f"模态 '{modality}' 没有对应的模型池。"
                f"可用模态: {available}"
            )
        return pool_class()

    @classmethod
    def get_model_builder(
        cls,
        modality: str,
        model_name: str
    ) -> BaseModelBuilder:
        """
        获取指定模态和模型的构建器

        参数:
        - modality: 模态名称
        - model_name: 模型名称

        返回:
        - builder: 模型构建器实例
        """
        pool = cls.get_pool(modality)
        return pool.get_builder(model_name)

    @classmethod
    def list_models(cls, modality: str) -> List[str]:
        """
        列出指定模态的所有可用模型

        参数:
        - modality: 模态名称

        返回:
        - models: 模型名称列表
        """
        pool = cls.get_pool(modality)
        return pool.list_models()

    @classmethod
    def list_all_models(cls) -> Dict[str, List[str]]:
        """
        列出所有模态的所有模型

        返回:
        - all_models: {modality: [model1, model2, ...]}
        """
        result = {}
        for modality in cls._pools.keys():
            result[modality] = cls.list_models(modality)
        return result


# ==================== 配置模板管理器 ====================

class ConfigTemplateManager:
    """配置模板管理器 - 管理模型配置模板"""

    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """
        获取默认训练配置

        返回:
        - config: 默认配置字典
        """
        return {
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 50,
            "optimizer": "adam",
            "optimizer_params": {
                "weight_decay": 0.0001
            },
            "scheduler": "step",
            "scheduler_params": {
                "step_size": 30,
                "gamma": 0.1
            },
            "early_stopping_patience": 10,
            "checkpoint_freq": 5,
            "use_augmentation": True,
            "val_split": 0.2,
            "device": "cuda",
            "use_amp": True,
            "num_workers": 4,
            "seed": 42
        }

    @staticmethod
    def merge_configs(
        base_config: Dict[str, Any],
        user_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        合并用户配置和基础配置

        参数:
        - base_config: 基础配置
        - user_config: 用户配置

        返回:
        - merged: 合并后的配置
        """
        merged = base_config.copy()

        for key, value in user_config.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                # 递归合并嵌套字典
                merged[key] = ConfigTemplateManager.merge_configs(merged[key], value)
            else:
                merged[key] = value

        return merged

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """
        验证配置的有效性

        参数:
        - config: 配置字典

        返回:
        - valid: 是否有效
        """
        required_keys = [
            "learning_rate", "batch_size", "epochs",
            "optimizer", "device"
        ]

        for key in required_keys:
            if key not in config:
                raise ValueError(f"配置缺少必需字段: {key}")

        # 验证数值范围
        if config["learning_rate"] <= 0:
            raise ValueError("learning_rate 必须大于 0")

        if config["batch_size"] <= 0:
            raise ValueError("batch_size 必须大于 0")

        if config["epochs"] <= 0:
            raise ValueError("epochs 必须大于 0")

        return True

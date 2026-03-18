# -*- coding: utf-8 -*-
"""
图像模态实现
包含图像数据加载器和图像模型池
"""

import torch
import torch.nn as nn
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader, random_split
from typing import Tuple, Dict, Any
from pathlib import Path

from .engine_core import (
    BaseDatasetLoader,
    BaseModelBuilder,
    BaseModelPool,
    ModalityManager,
    ModelPoolManager
)


# ==================== 图像数据加载器 ====================

class ImageDatasetLoader(BaseDatasetLoader):
    """图像数据集加载器"""

    def load(
        self,
        dataset_path: str,
        config: 'TrainingConfig'
    ) -> Tuple[DataLoader, DataLoader, int]:
        """加载图像数据集"""
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"加载图像数据集: {dataset_path}")

        # 获取数据变换
        train_transform = self.get_transforms(config, is_train=True)
        val_transform = self.get_transforms(config, is_train=False)

        try:
            # 尝试使用 ImageFolder 格式（分类任务）
            full_dataset = datasets.ImageFolder(
                root=dataset_path,
                transform=train_transform
            )

            # 划分训练集和验证集
            total_size = len(full_dataset)
            val_size = int(total_size * config.val_split)
            train_size = total_size - val_size

            train_dataset, val_dataset = random_split(
                full_dataset,
                [train_size, val_size],
                generator=torch.Generator().manual_seed(config.seed)
            )

            # 为验证集设置不同的 transform
            val_dataset.dataset.transform = val_transform

            logger.info(f"数据集加载成功 - 训练集: {train_size}, 验证集: {val_size}")

        except Exception as e:
            logger.error(f"使用 ImageFolder 加载失败: {e}, 尝试使用 CIFAR10")
            # 降级方案：使用 CIFAR10
            train_dataset = datasets.CIFAR10(
                root=dataset_path,
                train=True,
                download=True,
                transform=train_transform
            )
            val_dataset = datasets.CIFAR10(
                root=dataset_path,
                train=False,
                download=True,
                transform=val_transform
            )
            train_size = len(train_dataset)

        # 创建 DataLoader
        train_loader = DataLoader(
            train_dataset,
            batch_size=config.batch_size,
            shuffle=True,
            num_workers=config.num_workers,
            pin_memory=True if config.device == "cuda" else False
        )

        val_loader = DataLoader(
            val_dataset,
            batch_size=config.batch_size,
            shuffle=False,
            num_workers=config.num_workers,
            pin_memory=True if config.device == "cuda" else False
        )

        return train_loader, val_loader, train_size

    def get_transforms(self, config: 'TrainingConfig', is_train: bool):
        """获取图像数据增强变换"""
        if is_train and config.use_augmentation:
            return transforms.Compose([
                transforms.RandomResizedCrop(224),
                transforms.RandomHorizontalFlip(),
                transforms.ColorJitter(
                    brightness=0.2,
                    contrast=0.2,
                    saturation=0.2
                ),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])
        else:
            return transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])


# ==================== 图像模型构建器 ====================

class ResNet50Builder(BaseModelBuilder):
    """ResNet50 模型构建器"""

    def build(
        self,
        num_classes: int,
        pretrained: bool = True,
        **kwargs
    ) -> nn.Module:
        model = models.resnet50(pretrained=pretrained)
        num_features = model.fc.in_features
        model.fc = nn.Linear(num_features, num_classes)
        return model

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "learning_rate": 0.001,
            "batch_size": 32,
            "optimizer": "adam",
            "scheduler": "step"
        }


class ResNet101Builder(BaseModelBuilder):
    """ResNet101 模型构建器"""

    def build(
        self,
        num_classes: int,
        pretrained: bool = True,
        **kwargs
    ) -> nn.Module:
        model = models.resnet101(pretrained=pretrained)
        num_features = model.fc.in_features
        model.fc = nn.Linear(num_features, num_classes)
        return model

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "learning_rate": 0.0005,
            "batch_size": 16,
            "optimizer": "sgd",
            "scheduler": "cosine"
        }


class VGG16Builder(BaseModelBuilder):
    """VGG16 模型构建器"""

    def build(
        self,
        num_classes: int,
        pretrained: bool = True,
        **kwargs
    ) -> nn.Module:
        model = models.vgg16(pretrained=pretrained)
        num_features = model.classifier[6].in_features
        model.classifier[6] = nn.Linear(num_features, num_classes)
        return model

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "learning_rate": 0.0001,
            "batch_size": 16,
            "optimizer": "sgd",
            "scheduler": "step"
        }


class EfficientNetB0Builder(BaseModelBuilder):
    """EfficientNet-B0 模型构建器"""

    def build(
        self,
        num_classes: int,
        pretrained: bool = True,
        **kwargs
    ) -> nn.Module:
        model = models.efficientnet_b0(pretrained=pretrained)
        num_features = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(num_features, num_classes)
        return model

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "learning_rate": 0.001,
            "batch_size": 64,
            "optimizer": "adamw",
            "scheduler": "cosine"
        }


class MobileNetV2Builder(BaseModelBuilder):
    """MobileNetV2 模型构建器"""

    def build(
        self,
        num_classes: int,
        pretrained: bool = True,
        **kwargs
    ) -> nn.Module:
        model = models.mobilenet_v2(pretrained=pretrained)
        num_features = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(num_features, num_classes)
        return model

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "learning_rate": 0.001,
            "batch_size": 64,
            "optimizer": "adam",
            "scheduler": "step"
        }


class DenseNet121Builder(BaseModelBuilder):
    """DenseNet121 模型构建器"""

    def build(
        self,
        num_classes: int,
        pretrained: bool = True,
        **kwargs
    ) -> nn.Module:
        model = models.densenet121(pretrained=pretrained)
        num_features = model.classifier.in_features
        model.classifier = nn.Linear(num_features, num_classes)
        return model

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "learning_rate": 0.001,
            "batch_size": 32,
            "optimizer": "adam",
            "scheduler": "step"
        }


# ==================== 图像模型池 ====================

class ImageModelPool(BaseModelPool):
    """图像模型池 - 管理所有图像分类模型"""

    def register_models(self):
        """注册所有图像模型"""
        self.register('resnet50', ResNet50Builder)
        self.register('resnet101', ResNet101Builder)
        self.register('vgg16', VGG16Builder)
        self.register('efficientnet_b0', EfficientNetB0Builder)
        self.register('efficientnet-b0', EfficientNetB0Builder)  # 别名
        self.register('mobilenet_v2', MobileNetV2Builder)
        self.register('mobilenetv2', MobileNetV2Builder)  # 别名
        self.register('densenet121', DenseNet121Builder)


# ==================== 注册到管理器 ====================

def register_image_modality():
    """注册图像模态到管理器"""
    ModalityManager.register_loader('image', ImageDatasetLoader)
    ModelPoolManager.register_pool('image', ImageModelPool)


# 自动注册
register_image_modality()

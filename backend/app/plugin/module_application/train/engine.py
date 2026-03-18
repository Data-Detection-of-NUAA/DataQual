# -*- coding: utf-8 -*-
"""
训练执行引擎
与 FastAPI Admin 平台集成
负责实际执行模型训练任务
"""

import os
import sys
import json
import time
import logging
import asyncio
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, random_split
from torchvision import datasets, transforms, models
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import requests

# 添加项目根目录到 Python 路径（用于独立运行时）
current_file = Path(__file__).resolve()
backend_root = current_file.parent.parent.parent.parent.parent  # 回到 backend 目录
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

# 导入新的模块化架构
try:
    from app.plugin.module_application.train.engine_modalities import ModalityManager, ModelPoolManager
    USE_NEW_ARCHITECTURE = True
    logger_init = logging.getLogger(__name__)
    logger_init.info("使用新的模块化训练架构")
except ImportError as e:
    USE_NEW_ARCHITECTURE = False
    logger_init = logging.getLogger(__name__)
    logger_init.warning(f"新架构导入失败，使用旧架构: {e}")

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局日志文件路径（将在引擎初始化时设置）
_log_file_path = None

def setup_file_logging(log_file_path: str):
    """
    设置文件日志处理器

    参数:
    - log_file_path: 日志文件路径
    """
    global _log_file_path
    _log_file_path = log_file_path

    # 创建文件处理器
    file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    # 添加到logger
    logger.addHandler(file_handler)
    logger.info(f"日志文件已设置: {log_file_path}")


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TrainingConfig:
    """
    训练配置
    从 API 层传递过来的配置，包含用户选择的所有训练参数
    """
    # 任务标识
    task_id: str

    # 数据集信息（从 DatasetModel 获取）
    dataset_id: int
    dataset_path: str
    dataset_modality: str  # image/audio/text等
    num_classes: int
    sample_count: int

    # 模型配置（从 ModelConfigModel 获取）
    model_config_id: int
    model_name: str
    model_architecture: dict  # 模型架构参数
    pretrained: bool = True

    # 训练超参数（从用户选择或推荐获取）
    num_epochs: int = 50
    batch_size: int = 32
    learning_rate: float = 0.001

    # 优化器配置（从 train_config 获取）
    optimizer: str = "adam"
    optimizer_params: dict = field(default_factory=dict)  # weight_decay, momentum等

    # 学习率调度器（从 train_config 获取）
    scheduler: str = "step"
    scheduler_params: dict = field(default_factory=dict)  # step_size, gamma等

    # 训练策略
    early_stopping_patience: int = 10
    checkpoint_freq: int = 5

    # 数据增强
    use_augmentation: bool = True
    augmentation_config: dict = field(default_factory=dict)

    # 验证集配置
    val_split: float = 0.2

    # 硬件配置
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    use_amp: bool = True  # 混合精度训练
    num_workers: int = 4

    # 输出配置
    output_dir: str = ""

    # 其他配置
    seed: int = 42

    # API 回调地址（用于上报进度）
    api_base_url: str = "http://localhost:8000"
    api_token: str = ""


class DatasetLoader:
    """数据集加载器 - 根据数据集模态加载不同类型的数据"""

    @staticmethod
    def load_image_dataset(
        dataset_path: str,
        config: TrainingConfig
    ) -> Tuple[DataLoader, DataLoader, int]:
        """
        加载图像数据集

        参数:
        - dataset_path: 数据集存储路径
        - config: 训练配置

        返回:
        - train_loader: 训练数据加载器
        - val_loader: 验证数据加载器
        - train_size: 训练集大小
        """
        logger.info(f"加载图像数据集: {dataset_path}")

        # 构建数据增强
        if config.use_augmentation:
            train_transform = transforms.Compose([
                transforms.RandomResizedCrop(224),
                transforms.RandomHorizontalFlip(),
                transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
        else:
            train_transform = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])

        val_transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        # 加载数据集
        try:
            # 尝试使用 ImageFolder 格式（分类任务）
            # 分别加载两份，各自携带独立的 transform，避免 random_split 后共享
            # 底层 dataset 导致 val_dataset.dataset.transform 覆盖训练集 transform 的 bug
            train_full = datasets.ImageFolder(root=dataset_path, transform=train_transform)
            val_full   = datasets.ImageFolder(root=dataset_path, transform=val_transform)

            # 自动修正 num_classes（防止配置值与数据集实际类别数不一致触发 CUDA assert）
            actual_num_classes = len(train_full.classes)
            if actual_num_classes != config.num_classes:
                logger.warning(
                    f"num_classes 配置值 {config.num_classes} 与数据集实际类别数 "
                    f"{actual_num_classes} 不符，自动修正为 {actual_num_classes}"
                )
                config.num_classes = actual_num_classes

            # 用相同随机种子生成分割索引，保证 train/val 不重叠
            total_size = len(train_full)
            val_size   = int(total_size * config.val_split)
            train_size = total_size - val_size

            indices = torch.randperm(
                total_size,
                generator=torch.Generator().manual_seed(config.seed)
            ).tolist()

            from torch.utils.data import Subset
            train_dataset = Subset(train_full, indices[:train_size])
            val_dataset   = Subset(val_full,   indices[train_size:])

            logger.info(f"数据集加载成功 - 训练集: {train_size}, 验证集: {val_size}, 类别数: {actual_num_classes}")

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
            # CIFAR10 固定 10 类，同步修正 num_classes
            if config.num_classes != 10:
                logger.warning(f"CIFAR10 固定 10 类，num_classes 从 {config.num_classes} 修正为 10")
                config.num_classes = 10

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

    @staticmethod
    def load_dataset(config: TrainingConfig) -> Tuple[DataLoader, DataLoader, int]:
        """
        根据模态加载数据集

        参数:
        - config: 训练配置

        返回:
        - train_loader, val_loader, train_size
        """
        modality = config.dataset_modality.lower()

        if modality == "image":
            return DatasetLoader.load_image_dataset(config.dataset_path, config)
        elif modality == "text":
            # TODO: 实现文本数据集加载
            raise NotImplementedError("文本数据集加载功能待实现")
        elif modality == "audio":
            # TODO: 实现音频数据集加载
            raise NotImplementedError("音频数据集加载功能待实现")
        else:
            raise ValueError(f"不支持的数据模态: {modality}")


class ModelBuilder:
    """模型构建器 - 根据模型配置构建模型实例"""

    # 支持的模型注册表
    IMAGE_MODELS = {
        'resnet18': models.resnet18,
        'resnet34': models.resnet34,
        'resnet50': models.resnet50,
        'resnet101': models.resnet101,
        'vgg16': models.vgg16,
        'vgg19': models.vgg19,
        'densenet121': models.densenet121,
        'mobilenet_v2': models.mobilenet_v2,
        'efficientnet_b0': models.efficientnet_b0,
    }

    @staticmethod
    def build_image_model(config: TrainingConfig, device: torch.device) -> nn.Module:
        """
        构建图像分类模型

        参数:
        - config: 训练配置
        - device: 训练设备

        返回:
        - model: 模型实例
        """
        model_name_lower = config.model_name.lower().replace('-', '').replace('_', '')

        # 查找匹配的模型
        model_fn = None
        for key, fn in ModelBuilder.IMAGE_MODELS.items():
            if key.replace('_', '') in model_name_lower:
                model_fn = fn
                break

        if model_fn is None:
            logger.warning(f"未找到匹配的模型 {config.model_name}, 使用默认 ResNet18")
            model_fn = models.resnet18

        # 创建模型
        logger.info(f"创建模型: {config.model_name}, 预训练: {config.pretrained}")
        model = model_fn(pretrained=config.pretrained)

        # 修改输出层以适应分类数
        if 'resnet' in model_name_lower:
            num_features = model.fc.in_features
            model.fc = nn.Linear(num_features, config.num_classes)
        elif 'vgg' in model_name_lower:
            num_features = model.classifier[6].in_features
            model.classifier[6] = nn.Linear(num_features, config.num_classes)
        elif 'densenet' in model_name_lower:
            num_features = model.classifier.in_features
            model.classifier = nn.Linear(num_features, config.num_classes)
        elif 'mobilenet' in model_name_lower:
            num_features = model.classifier[1].in_features
            model.classifier[1] = nn.Linear(num_features, config.num_classes)
        elif 'efficientnet' in model_name_lower:
            num_features = model.classifier[1].in_features
            model.classifier[1] = nn.Linear(num_features, config.num_classes)

        # 移动到设备
        model = model.to(device)

        # 多GPU支持
        if torch.cuda.device_count() > 1:
            logger.info(f"使用 {torch.cuda.device_count()} 个GPU")
            model = nn.DataParallel(model)

        param_count = sum(p.numel() for p in model.parameters())
        logger.info(f"模型参数量: {param_count:,}")

        return model

    @staticmethod
    def build_model(config: TrainingConfig, device: torch.device) -> nn.Module:
        """
        根据模态构建模型

        参数:
        - config: 训练配置
        - device: 训练设备

        返回:
        - model: 模型实例
        """
        modality = config.dataset_modality.lower()

        if modality == "image":
            return ModelBuilder.build_image_model(config, device)
        else:
            raise NotImplementedError(f"模态 {modality} 的模型构建功能待实现")


class ProgressReporter:
    """进度上报器 - 向 API 层上报训练进度"""

    def __init__(self, config: TrainingConfig):
        self.config = config
        self.api_base_url = config.api_base_url.rstrip('/')
        self.task_id = config.task_id
        self.headers = {
            'Content-Type': 'application/json',
        }
        if config.api_token:
            self.headers['Authorization'] = f'Bearer {config.api_token}'

    def report_progress(self, data: dict) -> bool:
        """
        上报训练进度

        参数:
        - data: 进度数据

        返回:
        - bool: 是否成功
        """
        try:
            # 调用 API: POST /train/tasks/{task_id}/progress (内部接口，由引擎调用)
            url = f"{self.api_base_url}/train/tasks/{self.task_id}/progress/report"

            response = requests.post(url, json=data, headers=self.headers, timeout=5)

            if response.status_code == 200:
                return True
            else:
                logger.warning(f"上报进度失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.warning(f"上报进度异常: {e}")
            return False

    def update_task_status(self, status: str, error_message: str = None) -> bool:
        """
        更新任务状态

        参数:
        - status: 任务状态
        - error_message: 错误信息

        返回:
        - bool: 是否成功
        """
        try:
            url = f"{self.api_base_url}/train/tasks/{self.task_id}/status"

            data = {'status': status}
            if error_message:
                data['error_message'] = error_message

            response = requests.put(url, json=data, headers=self.headers, timeout=5)

            return response.status_code == 200
        except Exception as e:
            logger.warning(f"更新任务状态异常: {e}")
            return False

    def update_task_result(self, final_metrics: dict, model_path: str, result_path: str) -> bool:
        """
        更新训练结果

        参数:
        - final_metrics: 最终指标
        - model_path: 模型保存路径
        - result_path: 结果文件路径

        返回:
        - bool: 是否成功
        """
        try:
            url = f"{self.api_base_url}/train/tasks/{self.task_id}/result"

            data = {
                'final_metrics': final_metrics,
                'model_save_path': model_path,
                'result_file_path': result_path
            }

            response = requests.post(url, json=data, headers=self.headers, timeout=10)

            return response.status_code == 200
        except Exception as e:
            logger.warning(f"更新训练结果异常: {e}")
            return False


class TrainingEngine:
    """
    训练执行引擎
    负责实际执行训练任务
    """

    def __init__(self, config: TrainingConfig):
        """
        初始化训练引擎

        参数:
        - config: 训练配置
        """
        self.config = config
        self.device = torch.device(config.device)

        # 设置随机种子
        self._set_seed(config.seed)

        # 初始化组件
        self.model = None
        self.train_loader = None
        self.val_loader = None
        self.optimizer = None
        self.criterion = None
        self.scheduler = None
        self.scaler = None

        # 训练状态
        self.current_epoch = 0
        self.best_accuracy = 0.0
        self.best_loss = float('inf')
        self.metrics_history = []
        self.start_time = None

        # 输出目录
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 检查点目录
        self.checkpoint_dir = self.output_dir / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # 设置日志文件
        self.log_file = self.output_dir / "engine.log"
        setup_file_logging(str(self.log_file))

        # 进度上报器
        self.reporter = ProgressReporter(config)

        # 进度文件
        self.progress_file = self.output_dir / "progress.json"

        logger.info(f"训练引擎初始化完成 - 设备: {self.device}, 输出目录: {self.output_dir}")

    def _set_seed(self, seed: int):
        """设置随机种子"""
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        np.random.seed(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    def _create_datasets(self):
        """创建数据集"""
        logger.info("加载数据集...")

        if USE_NEW_ARCHITECTURE:
            # 使用新的模块化架构
            try:
                loader = ModalityManager.get_loader(self.config.dataset_modality)
                self.train_loader, self.val_loader, train_size = loader.load(
                    self.config.dataset_path,
                    self.config
                )
                logger.info(f"数据集加载完成（新架构）- 模态: {self.config.dataset_modality}")
            except Exception as e:
                logger.warning(f"新架构加载失败，回退到旧架构: {e}")
                self.train_loader, self.val_loader, train_size = DatasetLoader.load_dataset(self.config)
        else:
            # 使用旧架构
            self.train_loader, self.val_loader, train_size = DatasetLoader.load_dataset(self.config)

        logger.info(f"数据集加载完成")

    def _create_model(self):
        """创建模型"""
        logger.info("创建模型...")

        if USE_NEW_ARCHITECTURE:
            # 使用新的模块化架构
            try:
                builder = ModelPoolManager.get_model_builder(
                    self.config.dataset_modality,
                    self.config.model_name
                )
                self.model = builder.build(
                    num_classes=self.config.num_classes,
                    pretrained=self.config.pretrained
                )
                self.model = self.model.to(self.device)

                # 多GPU支持
                if torch.cuda.device_count() > 1:
                    logger.info(f"使用 {torch.cuda.device_count()} 个GPU")
                    self.model = nn.DataParallel(self.model)

                param_count = sum(p.numel() for p in self.model.parameters())
                logger.info(f"模型创建完成（新架构）- 模型: {self.config.model_name}, 参数量: {param_count:,}")
            except Exception as e:
                logger.warning(f"新架构创建模型失败，回退到旧架构: {e}")
                self.model = ModelBuilder.build_model(self.config, self.device)
        else:
            # 使用旧架构
            self.model = ModelBuilder.build_model(self.config, self.device)

        logger.info("模型创建完成")

    def _create_optimizer(self):
        """创建优化器和学习率调度器"""
        # 创建优化器
        optimizer_name = self.config.optimizer.lower()

        if optimizer_name == "adam":
            self.optimizer = optim.Adam(
                self.model.parameters(),
                lr=self.config.learning_rate,
                **self.config.optimizer_params
            )
        elif optimizer_name == "sgd":
            self.optimizer = optim.SGD(
                self.model.parameters(),
                lr=self.config.learning_rate,
                momentum=self.config.optimizer_params.get('momentum', 0.9),
                weight_decay=self.config.optimizer_params.get('weight_decay', 5e-4)
            )
        elif optimizer_name == "adamw":
            self.optimizer = optim.AdamW(
                self.model.parameters(),
                lr=self.config.learning_rate,
                **self.config.optimizer_params
            )
        else:
            logger.warning(f"未知优化器 {optimizer_name}, 使用默认 Adam")
            self.optimizer = optim.Adam(self.model.parameters(), lr=self.config.learning_rate)

        # 创建学习率调度器
        scheduler_name = self.config.scheduler.lower()

        if scheduler_name == "step":
            step_size = self.config.scheduler_params.get('step_size', 30)
            gamma = self.config.scheduler_params.get('gamma', 0.1)
            self.scheduler = optim.lr_scheduler.StepLR(
                self.optimizer,
                step_size=step_size,
                gamma=gamma
            )
        elif scheduler_name == "cosine":
            self.scheduler = optim.lr_scheduler.CosineAnnealingLR(
                self.optimizer,
                T_max=self.config.num_epochs
            )
        elif scheduler_name == "reduce":
            self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
                self.optimizer,
                mode='min',
                factor=0.1,
                patience=5
            )
        elif scheduler_name == "none" or scheduler_name == "":
            self.scheduler = None
        else:
            logger.warning(f"未知调度器 {scheduler_name}, 不使用调度器")
            self.scheduler = None

        # 损失函数
        self.criterion = nn.CrossEntropyLoss()

        # 混合精度训练
        if self.config.use_amp and self.device.type == 'cuda':
            self.scaler = torch.cuda.amp.GradScaler()
            logger.info("启用混合精度训练")

        logger.info(f"优化器: {optimizer_name}, 学习率: {self.config.learning_rate}")
        if self.scheduler:
            logger.info(f"学习率调度器: {scheduler_name}")

    def _train_epoch(self, epoch: int) -> Dict[str, float]:
        """训练一个 epoch"""
        self.model.train()
        train_loss = 0.0
        correct = 0
        total = 0

        total_batches = len(self.train_loader)

        for batch_idx, (inputs, targets) in enumerate(self.train_loader):
            inputs, targets = inputs.to(self.device), targets.to(self.device)

            # 混合精度训练
            if self.scaler:
                with torch.cuda.amp.autocast():
                    outputs = self.model(inputs)
                    loss = self.criterion(outputs, targets)

                self.optimizer.zero_grad()
                self.scaler.scale(loss).backward()
                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                outputs = self.model(inputs)
                loss = self.criterion(outputs, targets)

                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()

            # 统计
            train_loss += loss.item()
            _, predicted = outputs.max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()

            # 每 50 个 batch 输出一次并上报进度
            if batch_idx % 50 == 0 or batch_idx == total_batches - 1:
                batch_accuracy = 100. * correct / total
                logger.info(
                    f'Epoch: {epoch+1}/{self.config.num_epochs} '
                    f'[{batch_idx}/{total_batches} ({100. * batch_idx / total_batches:.0f}%)] '
                    f'Loss: {loss.item():.4f} | Acc: {batch_accuracy:.2f}%'
                )

                # 上报 batch 级别进度
                self.reporter.report_progress({
                    'current_epoch': epoch + 1,
                    'total_epochs': self.config.num_epochs,
                    'current_step': batch_idx,
                    'total_steps': total_batches,
                    'train_loss': loss.item(),
                    'train_accuracy': batch_accuracy / 100.0,
                    'learning_rate': self.optimizer.param_groups[0]['lr']
                })

        # 计算 epoch 指标
        epoch_loss = train_loss / total_batches
        epoch_accuracy = 100. * correct / total

        return {
            'train_loss': epoch_loss,
            'train_accuracy': epoch_accuracy
        }

    def _validate(self) -> Dict[str, float]:
        """验证模型"""
        self.model.eval()
        val_loss = 0.0
        correct = 0
        total = 0

        with torch.no_grad():
            for inputs, targets in self.val_loader:
                inputs, targets = inputs.to(self.device), targets.to(self.device)

                outputs = self.model(inputs)
                loss = self.criterion(outputs, targets)

                val_loss += loss.item()
                _, predicted = outputs.max(1)
                total += targets.size(0)
                correct += predicted.eq(targets).sum().item()

        val_loss = val_loss / len(self.val_loader)
        val_accuracy = 100. * correct / total

        return {
            'val_loss': val_loss,
            'val_accuracy': val_accuracy
        }

    def _save_checkpoint(self, epoch: int, metrics: Dict[str, float], is_best: bool = False):
        """保存检查点"""
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict() if self.scheduler else None,
            'best_accuracy': self.best_accuracy,
            'best_loss': self.best_loss,
            'metrics': metrics,
            'config': self.config.__dict__
        }

        # 保存常规检查点
        checkpoint_path = self.checkpoint_dir / f'checkpoint_epoch_{epoch+1}.pth'
        torch.save(checkpoint, checkpoint_path)
        logger.info(f"检查点已保存: {checkpoint_path}")

        # 保存最佳模型
        if is_best:
            best_path = self.checkpoint_dir / 'best_model.pth'
            torch.save(checkpoint, best_path)
            logger.info(f"最佳模型已保存: {best_path}")

    def _save_progress(self, epoch: int, train_metrics: Dict, val_metrics: Dict):
        """保存训练进度到本地文件"""
        progress_data = {
            'task_id': self.config.task_id,
            'epoch': epoch + 1,
            'train_metrics': train_metrics,
            'val_metrics': val_metrics,
            'timestamp': datetime.now().isoformat(),
            'learning_rate': self.optimizer.param_groups[0]['lr']
        }

        self.metrics_history.append(progress_data)

        # 保存到文件
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.metrics_history, f, indent=2, ensure_ascii=False)

    def _check_early_stopping(self, val_loss: float, patience_counter: int) -> Tuple[bool, int]:
        """检查是否应该早停"""
        if val_loss < self.best_loss:
            self.best_loss = val_loss
            return False, 0
        else:
            patience_counter += 1
            if patience_counter >= self.config.early_stopping_patience:
                logger.info(
                    f"早停触发，验证损失 {val_loss:.4f} "
                    f"未改善超过 {self.config.early_stopping_patience} 个 epoch"
                )
                return True, patience_counter
            return False, patience_counter

    def train(self) -> bool:
        """执行训练"""
        try:
            logger.info(f"开始训练任务: {self.config.task_id}")
            self.reporter.update_task_status(TaskStatus.RUNNING.value)
            self.start_time = time.time()

            # 1. 创建数据集
            logger.info("步骤 1/4: 加载数据集...")
            self._create_datasets()

            # 2. 创建模型
            logger.info("步骤 2/4: 创建模型...")
            self._create_model()

            # 3. 创建优化器
            logger.info("步骤 3/4: 创建优化器...")
            self._create_optimizer()

            # 4. 训练循环
            logger.info("步骤 4/4: 开始训练循环...")
            patience_counter = 0

            for epoch in range(self.config.num_epochs):
                self.current_epoch = epoch
                logger.info(f"\n{'='*60}")
                logger.info(f"Epoch {epoch+1}/{self.config.num_epochs}")
                logger.info(f"{'='*60}")

                # 训练
                train_start = time.time()
                train_metrics = self._train_epoch(epoch)
                train_time = time.time() - train_start

                # 验证
                val_start = time.time()
                val_metrics = self._validate()
                val_time = time.time() - val_start

                # 更新学习率
                if self.scheduler:
                    if isinstance(self.scheduler, optim.lr_scheduler.ReduceLROnPlateau):
                        self.scheduler.step(val_metrics['val_loss'])
                    else:
                        self.scheduler.step()

                # 合并指标
                epoch_metrics = {
                    **train_metrics,
                    **val_metrics,
                    'epoch_time': train_time + val_time,
                    'learning_rate': self.optimizer.param_groups[0]['lr']
                }

                # 打印 epoch 结果
                logger.info(
                    f"训练结果 - 损失: {train_metrics['train_loss']:.4f}, "
                    f"准确率: {train_metrics['train_accuracy']:.2f}%"
                )
                logger.info(
                    f"验证结果 - 损失: {val_metrics['val_loss']:.4f}, "
                    f"准确率: {val_metrics['val_accuracy']:.2f}%"
                )
                logger.info(
                    f"耗时: {epoch_metrics['epoch_time']:.2f}s, "
                    f"学习率: {epoch_metrics['learning_rate']:.6f}"
                )

                # 保存进度
                self._save_progress(epoch, train_metrics, val_metrics)

                # 上报 epoch 进度
                self.reporter.report_progress({
                    'current_epoch': epoch + 1,
                    'total_epochs': self.config.num_epochs,
                    'train_loss': train_metrics['train_loss'],
                    'train_accuracy': train_metrics['train_accuracy'] / 100.0,
                    'val_loss': val_metrics['val_loss'],
                    'val_accuracy': val_metrics['val_accuracy'] / 100.0,
                    'learning_rate': epoch_metrics['learning_rate'],
                    'epoch_time': epoch_metrics['epoch_time']
                })

                # 检查是否是最佳模型
                is_best = val_metrics['val_accuracy'] > self.best_accuracy
                if is_best:
                    self.best_accuracy = val_metrics['val_accuracy']
                    logger.info(f"[BEST] 新的最佳准确率: {self.best_accuracy:.2f}%")

                # 保存检查点
                if (epoch + 1) % self.config.checkpoint_freq == 0 or is_best:
                    self._save_checkpoint(epoch, epoch_metrics, is_best)

                # 检查早停
                should_stop, patience_counter = self._check_early_stopping(
                    val_metrics['val_loss'], patience_counter
                )
                if should_stop:
                    logger.info("训练因早停而终止")
                    break

            # 5. 训练完成
            total_time = time.time() - self.start_time
            logger.info(f"\n{'='*60}")
            logger.info(f"训练完成!")
            logger.info(f"总耗时: {total_time:.2f}s ({total_time/60:.2f}分钟)")
            logger.info(f"最佳验证准确率: {self.best_accuracy:.2f}%")
            logger.info(f"{'='*60}")

            # 保存最终模型
            final_model_path = self.output_dir / "final_model.pth"
            torch.save(self.model.state_dict(), final_model_path)
            logger.info(f"最终模型已保存: {final_model_path}")

            # 生成训练报告
            report_path = self._generate_training_report(total_time)

            # 上报最终结果
            final_metrics = {
                'final_train_loss': self.metrics_history[-1]['train_metrics']['train_loss'],
                'final_train_accuracy': self.metrics_history[-1]['train_metrics']['train_accuracy'] / 100.0,
                'final_val_loss': self.metrics_history[-1]['val_metrics']['val_loss'],
                'final_val_accuracy': self.metrics_history[-1]['val_metrics']['val_accuracy'] / 100.0,
                'best_accuracy': self.best_accuracy / 100.0,
                'best_loss': self.best_loss,
                'total_epochs': self.current_epoch + 1,
                'total_time_seconds': total_time
            }

            self.reporter.update_task_result(
                final_metrics=final_metrics,
                model_path=str(final_model_path.absolute()),
                result_path=str(report_path.absolute())
            )

            # 更新任务状态为完成
            self.reporter.update_task_status(
                TaskStatus.COMPLETED.value,
                f"训练完成，最佳准确率: {self.best_accuracy:.2f}%"
            )

            return True

        except Exception as e:
            logger.error(f"训练失败: {e}", exc_info=True)
            self.reporter.update_task_status(TaskStatus.FAILED.value, str(e))
            return False

    def _generate_training_report(self, total_time: float) -> Path:
        """生成训练报告"""
        report = {
            'task_id': self.config.task_id,
            'status': 'completed',
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'end_time': datetime.now().isoformat(),
            'total_time_seconds': total_time,
            'total_epochs': self.current_epoch + 1,
            'best_metrics': {
                'best_accuracy': self.best_accuracy,
                'best_loss': self.best_loss
            },
            'final_metrics': self.metrics_history[-1] if self.metrics_history else {},
            'config': {
                'task_id': self.config.task_id,
                'dataset_id': self.config.dataset_id,
                'model_config_id': self.config.model_config_id,
                'model_name': self.config.model_name,
                'num_epochs': self.config.num_epochs,
                'batch_size': self.config.batch_size,
                'learning_rate': self.config.learning_rate,
                'optimizer': self.config.optimizer,
                'scheduler': self.config.scheduler
            },
            'hardware_info': self._get_hardware_info(),
            'model_info': {
                'name': self.config.model_name,
                'parameters': sum(p.numel() for p in self.model.parameters()),
                'path': str((self.output_dir / "final_model.pth").absolute())
            },
            'metrics_history': self.metrics_history
        }

        # 保存报告
        report_path = self.output_dir / "training_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"训练报告已生成: {report_path}")
        return report_path

    def _get_hardware_info(self) -> Dict[str, Any]:
        """获取硬件信息"""
        info = {
            'device': str(self.device),
            'cuda_available': torch.cuda.is_available(),
            'cuda_version': torch.version.cuda if torch.cuda.is_available() else None,
            'gpu_count': torch.cuda.device_count() if torch.cuda.is_available() else 0,
        }

        if torch.cuda.is_available():
            info['gpus'] = []
            for i in range(torch.cuda.device_count()):
                gpu_info = {
                    'id': i,
                    'name': torch.cuda.get_device_name(i),
                    'memory_allocated_mb': torch.cuda.memory_allocated(i) / 1024**2,
                    'memory_reserved_mb': torch.cuda.memory_reserved(i) / 1024**2,
                }
                info['gpus'].append(gpu_info)

        return info


def run_training_from_config(config_file: str) -> bool:
    """
    从配置文件启动训练任务

    参数:
    - config_file: 配置文件路径（JSON 格式）

    返回:
    - bool: 是否成功
    """
    try:
        logger.info(f"从配置文件加载训练任务: {config_file}")

        # 加载配置
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        # 创建配置对象
        config = TrainingConfig(**config_data)

        # 创建训练引擎
        engine = TrainingEngine(config)

        # 执行训练
        success = engine.train()

        if success:
            logger.info(f"任务 {config.task_id} 执行成功")
            return True
        else:
            logger.error(f"任务 {config.task_id} 执行失败")
            return False

    except Exception as e:
        logger.error(f"运行训练任务失败: {e}", exc_info=True)
        return False


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='训练执行引擎')
    parser.add_argument('--config', type=str, required=True, help='配置文件路径（JSON）')

    args = parser.parse_args()

    # 运行训练任务
    success = run_training_from_config(args.config)

    if success:
        print("[SUCCESS] 训练任务执行成功")
        sys.exit(0)
    else:
        print("[FAILED] 训练任务执行失败")
        sys.exit(1)


if __name__ == "__main__":
    main()

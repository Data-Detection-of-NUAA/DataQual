# 模型配置初始化说明

## 📋 概述

本目录包含模型配置表的初始化数据和脚本，用于在系统首次部署或数据库重置后初始化模型配置。

## 📁 文件说明

- `model_config.json` - 模型配置初始化数据文件
- `init_model_config.py` - 模型配置初始化脚本

## 🎯 包含的模型

当前初始化数据包含以下 8 个预配置模型：

### 图像模型 (Image)
1. **ResNet50** - 经典残差网络，适合图像分类和目标检测
2. **YOLOv8** - 最新版YOLO，实时目标检测
3. **EfficientNetB0** - 轻量级高效网络，适合资源受限场景
4. **ViT-B16** - Vision Transformer，高精度图像分类
5. **MobileNetV3** - 超轻量级，移动端友好

### 音频模型 (Audio)
6. **Wav2Vec2** - 语音识别，支持多语言

### 文本模型 (Text)
7. **BERT** - NLP领域经典模型，适合文本理解任务

### 时序模型 (Text/Sensor)
8. **LSTM** - 长短期记忆网络，适合时序数据

## 🚀 使用方法

### 方法1：直接运行初始化脚本

在项目根目录执行：

```bash
cd backend
python -m app.scripts.init_model_config
```

### 方法2：集成到主初始化流程

在 `app/scripts/initialize.py` 中添加：

```python
from app.scripts.init_model_config import InitializeModelConfig

# 在 __init_data 方法中添加
async def __init_data(self, db: AsyncSession) -> None:
    # ... 现有初始化代码 ...

    # 初始化模型配置
    model_config_init = InitializeModelConfig()
    await model_config_init._InitializeModelConfig__init_model_config_data(db)
```

### 方法3：通过 API 导入（推荐用于后续维护）

系统启动后，可以通过管理后台 API 批量导入模型配置：

```bash
POST /api/v1/train/model/batch-create
```

## 📊 数据结构说明

每个模型配置包含以下字段：

### 基本信息
- `model_name` - 模型名称（唯一标识）
- `display_name` - 显示名称
- `model_version` - 版本号
- `description` - 模型简介
- `architecture_summary` - 架构说明

### 适用范围
- `supported_modalities` - 支持的数据模态（逗号分隔）
- `supported_task_types` - 支持的任务类型（逗号分隔）

### 配置信息
- `pretrained_weights` - 预训练权重信息（JSON）
- `default_train_config` - 默认训练配置（JSON）
- `performance_metrics` - 性能指标（JSON）
- `hardware_requirements` - 硬件要求（JSON）

### 框架信息
- `framework` - 深度学习框架
- `framework_version` - 框架版本要求
- `model_code_path` - 模型代码路径
- `config_template_path` - 配置模板路径

### 管理字段
- `priority` - 推荐优先级（0-100）
- `status` - 模型状态（active/inactive/deprecated）
- `usage_count` - 使用次数统计
- `tags` - 标签（逗号分隔）
- `reference_url` - 参考链接
- `remarks` - 备注信息

## 🔧 自定义模型配置

### 添加新模型

1. 编辑 `model_config.json` 文件
2. 按照现有格式添加新的模型配置对象
3. 运行初始化脚本

示例：

```json
{
  "model_name": "CustomModel",
  "display_name": "自定义模型",
  "model_version": "1.0.0",
  "supported_modalities": "image",
  "supported_task_types": "image_classification",
  "description": "这是一个自定义模型",
  "default_train_config": {
    "learning_rate": 0.001,
    "batch_size": 32,
    "epochs": 100
  },
  "framework": "PyTorch",
  "priority": 50,
  "status": "active",
  "usage_count": 0
}
```

### 修改现有模型

直接编辑 `model_config.json` 中对应模型的配置，然后重新运行脚本。

**注意**：如果表中已有数据，脚本会跳过初始化。需要先清空表或者通过 API 更新。

## ⚠️ 注意事项

1. **数据检查**：脚本会检查表中是否已有数据，如果有则跳过初始化
2. **JSON格式**：确保 JSON 文件格式正确，特别是嵌套的 JSON 对象
3. **必填字段**：以下字段为必填
   - model_name（唯一）
   - display_name
   - supported_modalities
   - supported_task_types
   - description
   - default_train_config
   - framework
4. **权重文件**：pretrained_weights 中的 URL 应该是可访问的下载地址
5. **代码路径**：model_code_path 和 config_template_path 应该指向实际存在的文件

## 🔍 验证初始化结果

初始化完成后，可以通过以下方式验证：

### 1. 查看日志输出

```
✅ 已向 model_config 表写入 8 条初始化数据
✅ 模型配置初始化完成
```

### 2. 通过 API 查询

```bash
GET /api/v1/train/model/list?page_no=1&page_size=10
```

### 3. 查看数据库

```sql
SELECT COUNT(*) FROM model_config;
SELECT model_name, display_name, status, priority FROM model_config ORDER BY priority DESC;
```

### 4. 测试推荐功能

```bash
POST /api/v1/train/recommend
{
    "dataset_id": 1,
    "top_k": 5
}
```

## 📈 后续扩展

建议后续根据实际需求添加更多模型配置：

### 图像领域
- DenseNet系列
- Inception系列
- SENet
- RegNet
- ConvNeXt

### 目标检测
- Faster R-CNN
- Mask R-CNN
- RetinaNet
- DETR

### 语音领域
- Whisper
- DeepSpeech
- HuBERT

### NLP领域
- RoBERTa
- GPT系列
- T5
- XLNet

### 视频领域
- I3D
- SlowFast
- TimeSformer

## 🆘 故障排除

### 问题1：脚本执行失败

**错误**：`ModuleNotFoundError: No module named 'app'`

**解决**：确保在 backend 目录下执行脚本

```bash
cd backend
python -m app.scripts.init_model_config
```

### 问题2：JSON解析错误

**错误**：`json.JSONDecodeError`

**解决**：检查 JSON 文件格式，特别是：
- 最后一个对象后不能有逗号
- 字符串必须用双引号
- JSON对象的嵌套括号是否匹配

### 问题3：数据库连接失败

**错误**：`Connection refused`

**解决**：
1. 检查数据库服务是否启动
2. 检查 `.env` 文件中的数据库配置
3. 确认数据库表已创建

### 问题4：重复执行脚本

**现象**：脚本提示"表已存在记录"跳过初始化

**解决**：如需重新初始化，可以：
1. 清空表：`TRUNCATE TABLE model_config;`
2. 或通过 API 批量删除后重新导入

## 📝 更新日志

- **2025-01-20**: 初始版本，包含8个基础模型配置
- 未来计划添加更多模型和领域支持

## 📞 联系支持

如有问题或建议，请联系开发团队或提交 Issue。

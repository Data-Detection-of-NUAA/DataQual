# Design: 图片标签错误检测（Image Label Mismatch Detection）

**Date:** 2026-03-17
**Status:** Approved
**Author:** Claude Code

---

## 1. 目标

在 dqscan 系统中新增**图片分类标签错误检测**能力。用户上传图片数据集（图片 + CSV 标签文件），系统自动检测哪些图片的分类标签可能标错，输出疑似错标的图片列表及建议标签。

### 交付物
1. **图片标签错误检测算法**：SimiFeat KNN（主线）+ pHash 离群（兜底）
2. **前端重构**：将 dqscan 的 index.vue（~5800 行）拆分为组件化文件结构
3. **缺陷树按模态隔离**：表格/图片模态各展示自己的缺陷节点
4. **文档与 PPT**：算法说明 + 演示材料

### 非目标
- 不涉及目标检测（object detection）或语义分割的标签检测
- 不涉及文本/音频模态
- 暂不实现在线标注修正（只检测，不自动纠错）

---

## 2. 数据输入协议

### 用户上传内容
1. **图片压缩包**（ZIP）：解压后为图片文件（支持 jpg/jpeg/png/bmp/webp）
2. **CSV 标签文件**：至少包含两列
   - `image_path`：图片相对路径（相对于解压根目录）
   - `label`：分类标签（字符串或整数）

### 示例 CSV
```csv
image_path,label
train/cat_001.jpg,cat
train/dog_015.jpg,dog
train/cat_042.jpg,cat
```

### 目录结构示例
```
upload.zip
├── train/
│   ├── cat_001.jpg
│   ├── dog_015.jpg
│   └── ...
└── labels.csv
```

### ZIP 上传安全规范
- 解压前检查总大小（限制 2GB）和文件数量（限制 50000）
- **Zip Slip 防护**：验证每个条目的解压路径不越过目标目录（`os.path.commonpath` 校验）
- 解压到 `backend/static/dqscan/uploads/{task_id}/images/` 下
- 仅提取图片格式文件（jpg/jpeg/png/bmp/webp），跳过其他文件
- CSV 标签文件可在 ZIP 内或单独上传

---

## 3. 算法设计

### 3.1 主线算法：SimiFeat KNN（`simifeat_knn`）

**原理**：Training-free，基于预训练视觉模型（CLIP ViT-B/32）提取图片 embedding，通过 KNN 邻域投票检测标签不一致的样本。

**流程**：
1. 用 CLIP ViT-B/32 提取所有图片的 embedding 向量（**512 维**）
2. 对每张图片，找到其 K 个最近邻（cosine similarity）
3. 统计 K 个邻居中与当前图片标签不同的比例（`neighbor_disagreement`）
4. 如果 disagreement > threshold，则标记为疑似错标
5. 基于邻居中最多的标签作为 `suggested_label`
6. 按 disagreement 排名，输出 Top-N 疑似错标

**参数**：
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| k | int | 10 | KNN 邻居数 |
| threshold | float | 0.5 | 邻域不一致率阈值（>threshold 为疑似错标） |
| max_samples | int | 5000 | 最大处理图片数（超过则采样） |
| max_examples | int | 500 | 最大输出错标数 |
| batch_size | int | 32 | CLIP 推理批大小 |
| device | str | "auto" | 推理设备：auto/cpu/cuda（auto 优先用 GPU） |
| model_name | str | "openai/clip-vit-base-patch32" | CLIP 模型名称或本地路径 |

**依赖**：torch, transformers (CLIP), Pillow

**降级策略**：若 torch/transformers 不可用，自动降级到 `phash_outlier`，并在结果中记录 warning

**设备与内存管理**：
- `device=auto`：检测 CUDA 可用性，优先 GPU
- 模型**按需加载、用完释放**（`del model; torch.cuda.empty_cache()`），避免常驻内存
- CUDA OOM 时自动 fallback 到 CPU 重试
- 预估性能：GPU ~30s/5000 张，CPU ~10-30min/5000 张

### 3.2 兜底算法：pHash 类内离群（`phash_outlier`）

**原理**：用感知哈希（pHash）提取图片指纹，同类内计算**平均成对汉明距离**，偏离度过高的样本为疑似错标。

**流程**：
1. 用 pHash 对每张图片生成哈希值
2. 按标签分组
3. 对每张图片，计算它到**同类所有其他图片**的平均汉明距离（`avg_intra_dist`）
4. 同时计算它到**每个其他类所有图片**的平均汉明距离，取最小值（`min_inter_dist`）
5. 计算 `outlier_score = avg_intra_dist - min_inter_dist`
6. `outlier_score > 0` 且排名靠前的样本为疑似错标
7. `suggested_label` 为距离最近的其他类

**局限性说明**：pHash 适合视觉特征相对一致的类别（如数字、图标）。对视觉多样性高的类别（如"狗"含多种品种），检测精度有限。仅作为无深度学习环境的降级兜底。

**参数**：
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| hash_size | int | 16 | pHash 尺寸（输出 hash_size^2 bits） |
| max_samples | int | 10000 | 最大处理图片数 |
| max_examples | int | 500 | 最大输出错标数 |

**依赖**：Pillow, imagehash（纯 CPU，无 GPU 需求）

### 3.3 输出 Schema

与表格 label_mismatch 对齐：

```python
{
  "image_label_mismatch_count": int,
  "image_label_mismatch_rate": float,
  "total_issues": int,
  "issue_percentage": float,
  "algorithm": "SimiFeat KNN (CLIP ViT-B/32)" | "pHash 类内离群",
  "detailed_issues": [
    {
      "data_id": "train/cat_042.jpg",
      "issue_type": "疑似错标（图片）",
      "severity": "severe|moderate|light",
      "details": {
        "given_label": "cat",
        "suggested_label": "dog",
        "confidence_score": 0.85,
        "neighbor_agreement": 0.8,
        "image_path": "train/cat_042.jpg",
        "thumbnail_url": "/static/dqscan/uploads/{task_id}/thumbnails/cat_042_thumb.jpg"
      }
    }
  ],
  "per_class_issue_rate": {"cat": 0.03, "dog": 0.01},
  "confusion_pairs_top": [
    {"given_label": "cat", "suggested_label": "dog", "count": 12}
  ]
}
```

**缩略图策略**：生成 64x64 JPEG 缩略图文件到 `{task_dir}/thumbnails/` 目录，结果中仅存储 URL 路径（而非 base64），避免 result.json 膨胀。

---

## 4. 引擎架构设计

### 4.1 新增 ImageQualityEngine

**不修改现有 `TabularQualityEngine`**，而是新增独立的 `ImageQualityEngine`：

```python
# dqscan/engine/algorithms/image/image_quality_engine.py
class ImageQualityEngine(BaseAlgorithm):
    spec = AlgorithmSpec(
        name="image_quality_engine",
        display_name="Image Quality Engine",
        supported_data_types=["image"]
    )

    def run(self, input_path: str, params: dict, ...) -> dict:
        """
        input_path: 解压后的图片目录路径
        params 中必须包含:
          - label_csv_path: CSV 标签文件路径（相对于 input_path 或绝对路径）
          - image_column: CSV 中图片路径列名（默认 "image_path"）
          - label_column: CSV 中标签列名（默认 "label"）
          - defects.selected: 启用的缺陷检测项
        """
```

### 4.2 Registry 注册

```python
# dqscan/engine/registry.py
registry.register(ImageQualityEngine)
```

### 4.3 数据流

```
Frontend (模态=image)
  → create_task(algorithm="image_quality_engine", data_type="image", ...)
  → service.create_task()
    → _TaskState(data_type="image", ...)
    → _validate_params_image()  # 图片模态专用校验
  → _run_task()
    → get_algorithm("image_quality_engine")
    → ImageQualityEngine.run(
        input_path="/uploads/{task_id}/images/",
        params={
          "label_csv_path": "labels.csv",
          "image_column": "image_path",
          "label_column": "label",
          "defects": {"selected": {"dirty_data.image_label_mismatch": {...}}}
        }
      )
    → ImageLabelMismatchScanner.scan()
    → 生成缩略图 → result.json
```

---

## 5. 缺陷树设计（按模态隔离）

### 核心原则
**不同模态的缺陷树完全独立**，用户选择模态后只看到该模态的缺陷节点。

### 后端变更

1. 所有缺陷项新增 `modality` 字段（现有表格缺陷统一标记为 `"tabular"`）
2. `/defects` API 接受 `?modality=image|tabular` 参数，按模态筛选返回
3. 移除 `get_defects_catalog` 中 `modality != "tabular"` 的硬拒逻辑
4. `_TaskState` 新增 `data_type: str` 字段
5. `_validate_params` 按 `data_type` 分派（表格 vs 图片各有独立校验）

### 图片模态缺陷树

```python
_IMAGE_DEFECT_CATALOG = {
  "dirty_data.image_label_mismatch": {
    "key": "dirty_data.image_label_mismatch",
    "modality": "image",
    "module": "dirty_data",
    "label": "图片分类错标检测",
    "desc": "检测图片数据集中标签可能标错的样本，基于视觉特征与标签一致性分析",
    "group": "group_label",
    "group_label": "标签质量",
    "status": "ready",
    "algorithms": [
      {"key": "simifeat_knn", "label": "SimiFeat KNN (CLIP)", "status": "ready", "badge": "推荐"},
      {"key": "phash_outlier", "label": "pHash 类内离群", "status": "ready", "badge": "轻量"}
    ],
    "params_schema": {
      "label_column": {"type": "string", "required": True, "default": "label"},
      "image_column": {"type": "string", "required": True, "default": "image_path"},
      "k": {"type": "int", "default": 10, "min": 3, "max": 50},
      "threshold": {"type": "float", "default": 0.5, "min": 0.1, "max": 0.9}
    }
  }
}
```

### 前端筛选逻辑
```javascript
// 根据当前选择的模态过滤缺陷树
const filteredDefects = defectCatalog.filter(d => d.modality === selectedModality)
```

---

## 6. 前端重构方案

### 当前问题
`frontend/src/views/module_application/dqscan/index.vue` 单文件约 **5800 行**，包含所有步骤的 UI + 逻辑，维护困难。

### 目标文件结构
```
frontend/src/views/module_application/dqscan/
├── index.vue                    # 主入口：步骤容器 + 路由（目标 < 200 行）
├── components/
│   ├── StepModality.vue         # 步骤0：模态选择
│   ├── StepUpload.vue           # 步骤1：文件上传（支持 CSV + ZIP）
│   ├── StepConfig.vue           # 步骤2：算法配置
│   │   ├── DefectTree.vue       # 缺陷树（按模态筛选）
│   │   ├── TabularParamPanel.vue  # 表格模态参数面板
│   │   ├── ImageParamPanel.vue    # 图片模态参数面板（新增）
│   │   └── PhysicsRules.vue     # 物理规则配置
│   ├── StepExecution.vue        # 步骤3：执行监控
│   ├── StepReport.vue           # 步骤4：报告展示
│   │   ├── ReportOverview.vue   # 概览卡片
│   │   ├── ReportTable.vue      # 指标表格
│   │   ├── ReportIssues.vue     # 问题详情
│   │   ├── LabelMismatchTable.vue  # 表格错标详情
│   │   └── ImageMismatchGallery.vue # 图片错标画廊（新增）
│   └── shared/
│       ├── FileUploader.vue     # 通用上传组件
│       └── WebSocketLog.vue     # WebSocket 日志
├── composables/
│   ├── useTaskManager.ts        # 任务管理逻辑
│   ├── useDefectTree.ts         # 缺陷树状态
│   ├── useWebSocket.ts          # WebSocket 连接
│   └── useReport.ts             # 报告数据处理
└── types/
    └── dqscan.ts                # TypeScript 类型定义
```

### 重构策略
- **渐进式拆分**：先按步骤拆分为 5 个 Step 组件，再逐步细化
- **状态管理**：通过 composables 共享状态（provide/inject 或 reactive store）
- **向后兼容**：index.vue 变为纯容器，组合各 Step 组件
- 每次拆分后执行 `npx vite build` 验证无回归

---

## 7. 后端 Service 层变更

### Upload API 变更
- 支持 `.zip` 文件上传（新增到允许后缀列表）
- ZIP 上传时自动解压到 `{task_dir}/images/`
- 在 ZIP 内或同次上传中查找 CSV 标签文件
- 返回解压后的文件列表和图片数量

### TaskState 变更
```python
@dataclass
class _TaskState:
    task_id: str
    data_type: str = "tabular"  # 新增：tabular | image
    # ... 其他字段不变
```

### 参数校验分派
```python
def _validate_params(self, params: dict, data_type: str):
    if data_type == "tabular":
        self._validate_params_tabular(params)
    elif data_type == "image":
        self._validate_params_image(params)
```

---

## 8. 实施阶段

### Phase 14：图片标签错误检测

| 子阶段 | 内容 | 负责 | 依赖 |
|--------|------|------|------|
| **14.0** | **接口契约定义**：ImageQualityEngine 接口、input_path 语义、params schema | all | 无（最先完成） |
| 14.1 | 前端重构：index.vue 拆分为组件化结构 | frontend-dev | 无 |
| 14.2 | 后端：缺陷树按模态隔离 + ZIP 上传 + TaskState.data_type | backend-dev | 14.0 |
| 14.3 | 算法：ImageLabelMismatchScanner（simifeat_knn + phash_outlier） | algorithm-dev | 14.0 |
| 14.4 | 引擎：ImageQualityEngine + registry 注册 | algorithm-dev | 14.3 |
| 14.5 | 前端：图片模态配置 + 报告展示（含缩略图画廊） | frontend-dev | 14.1, 14.2 |
| 14.6 | 评估：合成噪声注入 + precision@k/recall@k | algorithm-dev | 14.3 |
| 14.7 | 文档与 PPT | all | 14.1-14.6 |

### 团队分工（3 个并行 Agent）
| Agent | 职责 | 主要文件 |
|-------|------|----------|
| **frontend-dev** | 前端重构 + 图片模态 UI | `frontend/src/views/module_application/dqscan/` |
| **backend-dev** | 后端 API + 缺陷树 + ZIP 处理 | `backend/app/plugin/.../service.py` |
| **algorithm-dev** | Scanner 算法 + 引擎集成 + 评估 | `dqscan/scanner/`, `dqscan/engine/` |

---

## 9. 风险与缓解

| 风险 | 缓解 |
|------|------|
| CLIP 模型下载慢/大（~600MB） | 支持配置 model_name 本地路径；首次使用时提示下载；phash 兜底 |
| GPU 内存溢出 | CUDA OOM 自动 fallback CPU；batch 推理；模型用完释放 |
| 大量图片内存溢出 | max_samples 采样；batch 推理；延迟加载 |
| 图片格式不统一 | Pillow 统一转换；异常格式跳过并记录 warning |
| ZIP path traversal（Zip Slip） | 解压前校验所有条目路径不越出目标目录 |
| 前端重构引入回归 | 渐进式拆分；每步 vite build 验证 |
| pHash 对视觉多样性类精度低 | 文档中明确说明局限性；推荐使用 simifeat_knn |
| backend-dev / algorithm-dev 接口耦合 | Phase 14.0 先定义接口契约，再并行开发 |

---

## 10. 成功标准

1. 在合成噪声（5%/10%）下，simifeat_knn 的 precision@100 >= 0.8
2. phash_outlier 在无 torch 环境下可正常运行并输出结果
3. 前端重构后 index.vue < 200 行，各组件职责清晰
4. 缺陷树按模态正确筛选，表格/图片缺陷不交叉展示
5. 输出完整的算法说明文档和演示 PPT
6. 图片报告页展示缩略图画廊，可直观查看疑似错标图片

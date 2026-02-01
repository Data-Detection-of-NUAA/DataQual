<template>
  <div class="model-trainer">
    <!-- 如果没有选择数据集，显示提示 -->
    <el-empty v-if="!dataset || !dataset.datasetId" description="请先在步骤1中选择数据集">
      <el-button type="primary" @click="$emit('prev')">返回选择数据集</el-button>
    </el-empty>

    <!-- 模型推荐区域 -->
    <div v-else class="model-recommendation">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading" :size="40">
          <Loading />
        </el-icon>
        <p>正在分析数据集并推荐合适的模型...</p>
      </div>

      <!-- 推荐结果 -->
      <div v-else-if="recommendations.length > 0" class="recommendation-results">
        <!-- 数据集信息摘要 -->
        <el-alert
          :title="`基于数据集 &quot;${datasetInfo?.name}&quot; 的推荐结果`"
          type="info"
          :closable="false"
          class="dataset-summary"
        >
          <template #default>
            <div class="dataset-meta">
              <el-tag type="primary" size="small">
                {{ getModalityText(datasetInfo?.modality) }}
              </el-tag>
              <el-tag type="success" size="small">
                {{ getTaskTypeText(datasetInfo?.task_type) }}
              </el-tag>
              <span v-if="datasetInfo?.sample_count" class="meta-item">
                样本数: {{ datasetInfo.sample_count }}
              </span>
              <span v-if="datasetInfo?.class_count" class="meta-item">
                类别数: {{ datasetInfo.class_count }}
              </span>
            </div>
          </template>
        </el-alert>

        <!-- 推荐模型表格 -->
        <el-table
          :data="recommendations"
          stripe
          style="width: 100%; margin-top: 20px"
          :row-class-name="getRowClassName"
          @row-click="handleRowClick"
          highlight-current-row
        >
          <!-- 选择列 -->
          <el-table-column width="60" align="center">
            <template #default="{ row }">
              <el-radio
                v-model="selectedModelId"
                :label="row.model_id"
                @click.stop="selectModel(row)"
              >
                <span></span>
              </el-radio>
            </template>
          </el-table-column>

          <!-- 模型列 -->
          <el-table-column label="模型" width="280">
            <template #default="{ row, $index }">
              <div class="model-cell">
                <div class="model-icon" :style="{ backgroundColor: getModelIconColor($index) }">
                  <span class="icon-text">{{ row.display_name.substring(0, 2) }}</span>
                </div>
                <div class="model-info">
                  <div class="model-name">{{ row.display_name }}</div>
                  <div class="model-subtitle">{{ row.model_name }}</div>
                </div>
              </div>
            </template>
          </el-table-column>

          <!-- 模型类型列 -->
          <el-table-column label="模型类型" width="150" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.tags && row.tags[0]" effect="plain">
                {{ row.tags[0] }}
              </el-tag>
            </template>
          </el-table-column>

          <!-- 适用场景列 -->
          <el-table-column label="适用场景" width="280">
            <template #default="{ row }">
              <div class="task-types">
                {{ formatTaskTypes(row) }}
              </div>
            </template>
          </el-table-column>

          <!-- 简介列 -->
          <el-table-column label="简介" min-width="350">
            <template #default="{ row }">
              <div class="description">
                {{ row.description }}
              </div>
            </template>
          </el-table-column>
        </el-table>

        <!-- 更多推荐提示 -->
        <div v-if="totalRecommended > recommendations.length" class="more-tip">
          <el-text type="info">
            还有 {{ totalRecommended - recommendations.length }} 个模型符合要求，
            <el-button text type="primary" @click="loadMore">查看更多</el-button>
          </el-text>
        </div>
      </div>

      <!-- 无推荐结果 -->
      <el-empty v-else description="暂无推荐模型">
        <el-button type="primary" @click="loadRecommendations">刷新推荐</el-button>
      </el-empty>
    </div>

    <!-- 已选择的模型配置 -->
    <el-divider v-if="selectedModelInfo" />
    <div v-if="selectedModelInfo" class="selected-model-config">
      <h4>
        <el-icon><Setting /></el-icon>
        训练配置 - {{ selectedModelInfo.display_name }}
      </h4>

      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      >
        以下参数已自动填充为该模型的推荐配置，您可以根据需要调整
      </el-alert>

      <el-form :model="localData.trainingConfig" label-width="140px" label-position="right" class="evaluation-form">
        <!-- 训练参数 -->
        <div class="training-params">
          <el-form-item label="训练轮数" required>
            <el-input-number
              v-model="localData.trainingConfig.trainingEpochs"
              :min="1"
              :max="500"
              :step="10"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>

          <el-form-item label="批次大小" required>
            <el-input-number
              v-model="localData.trainingConfig.batchSize"
              :min="1"
              :max="512"
              :step="1"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>

          <el-form-item label="学习率" required>
            <el-input-number
              v-model="localData.trainingConfig.learningRate"
              :min="0.00001"
              :max="1"
              :step="0.0001"
              :precision="5"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>

          <el-form-item label="优化器" required>
            <el-select v-model="localData.trainingConfig.optimizer" placeholder="请选择优化器" style="width: 100%">
              <el-option label="Adam" value="Adam" />
              <el-option label="SGD" value="SGD" />
              <el-option label="RMSprop" value="RMSprop" />
              <el-option label="AdamW" value="AdamW" />
            </el-select>
          </el-form-item>

          <el-form-item label="损失函数" required>
            <el-select v-model="localData.trainingConfig.lossFunction" placeholder="请选择损失函数" style="width: 100%">
              <el-option label="CrossEntropyLoss" value="CrossEntropyLoss" />
              <el-option label="MSELoss" value="MSELoss" />
              <el-option label="BCELoss" value="BCELoss" />
              <el-option label="NLLLoss" value="NLLLoss" />
            </el-select>
          </el-form-item>

          <el-form-item label="学习率调度器">
            <el-select v-model="localData.trainingConfig.scheduler" placeholder="请选择调度器" style="width: 100%">
              <el-option label="StepLR" value="StepLR" />
              <el-option label="CosineAnnealingLR" value="CosineAnnealingLR" />
              <el-option label="ReduceLROnPlateau" value="ReduceLROnPlateau" />
              <el-option label="无" value="None" />
            </el-select>
          </el-form-item>

          <el-form-item label="权重衰减">
            <el-input-number
              v-model="localData.trainingConfig.weightDecay"
              :min="0"
              :max="1"
              :step="0.00001"
              :precision="5"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>

          <el-form-item label="动量（Momentum）" v-if="localData.trainingConfig.optimizer === 'SGD'">
            <el-input-number
              v-model="localData.trainingConfig.momentum"
              :min="0"
              :max="1"
              :step="0.1"
              :precision="2"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>
        </div>
      </el-form>

      <!-- 开始训练按钮 -->
      <div v-if="!training && !trainingComplete" class="start-training-button-container">
        <el-button type="success" size="large" @click="startTraining">
          <el-icon class="mr-2"><VideoPlay /></el-icon>
          开始训练
        </el-button>
      </div>
    </div>

    <!-- 训练进行中 -->
    <div v-if="training" class="training-panel">
      <div class="training-animation">
        <el-icon :size="80" class="rotating-icon" color="#67c23a">
          <Loading />
        </el-icon>
      </div>
      <h3 class="training-text">模型训练中...</h3>
      <p class="training-hint">正在训练模型，请耐心等待</p>
      <el-progress
        :percentage="trainingProgress"
        :stroke-width="16"
        :striped="true"
        :striped-flow="true"
        status="success"
        class="progress-bar"
      />
      <div class="training-metrics">
        <div class="metric-item">
          <span class="metric-label">当前轮次:</span>
          <span class="metric-value">{{ currentEpoch }} / {{ localData.trainingConfig.trainingEpochs }}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">训练损失:</span>
          <span class="metric-value">{{ trainingLoss.toFixed(4) }}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">训练准确率:</span>
          <span class="metric-value">{{ trainingAccuracy.toFixed(2) }}%</span>
        </div>
      </div>
      <p class="progress-text">已完成: {{ trainingProgress }}%</p>
    </div>

    <!-- 训练完成 -->
    <div v-if="trainingComplete" class="training-complete-panel">
      <div class="complete-header">
        <el-icon :size="64" color="#67c23a">
          <CircleCheck />
        </el-icon>
        <h3>训练完成</h3>
      </div>
      <el-descriptions :column="2" border class="training-result">
        <el-descriptions-item label="模型名称">
          {{ selectedModelInfo?.display_name }}
        </el-descriptions-item>
        <el-descriptions-item label="训练轮数">
          {{ localData.trainingConfig.trainingEpochs }}
        </el-descriptions-item>
        <el-descriptions-item label="最终损失">
          {{ trainingLoss.toFixed(4) }}
        </el-descriptions-item>
        <el-descriptions-item label="最终准确率">
          {{ trainingAccuracy.toFixed(2) }}%
        </el-descriptions-item>
        <el-descriptions-item label="数据集名称">
          {{ datasetInfo?.name || '未知' }}
        </el-descriptions-item>
        <el-descriptions-item label="优化器">
          {{ localData.trainingConfig.optimizer }}
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- 下一步按钮 -->
    <div v-if="trainingComplete" class="next-button-container">
      <el-button type="primary" size="large" @click="$emit('next')">
        下一步：对抗策略选择
        <el-icon class="ml-2"><ArrowRight /></el-icon>
      </el-button>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting, Loading, ArrowRight, VideoPlay, CircleCheck } from '@element-plus/icons-vue'

// ==================== 类型定义 ====================

interface ModelRecommendationItem {
  model_id: number
  display_name: string
  model_name: string
  framework?: string
  modality?: string
  task_type?: string
  description?: string
  tags?: string[]
  recommendation_reason?: string
  default_config_preview?: {
    epochs?: number
    batch_size?: number
    learning_rate?: number
    optimizer?: string
    loss_function?: string
    scheduler?: string
    weight_decay?: number
    momentum?: number
  }
}

interface DatasetInfoForRecommendation {
  name?: string
  modality?: string
  task_type?: string
  sample_count?: number
  class_count?: number
}

interface Props {
  modelValue: {
    modelId: number | null
    trainingConfig: any
  }
  dataset: any
}

interface Emits {
  (e: 'update:modelValue', value: Props['modelValue']): void
  (e: 'prev'): void
  (e: 'next'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// ==================== 推荐相关状态 ====================

const loading = ref(false)
const recommendations = ref<ModelRecommendationItem[]>([])
const datasetInfo = ref<DatasetInfoForRecommendation | null>(null)
const totalRecommended = ref(0)
const selectedModelId = ref<number | undefined>(undefined)

// ==================== 训练配置状态 ====================

const selectedModelInfo = ref<ModelRecommendationItem | null>(null)

// 训练状态
const training = ref(false)
const trainingComplete = ref(false)
const trainingProgress = ref(0)
const currentEpoch = ref(0)
const trainingLoss = ref(2.5)
const trainingAccuracy = ref(0)
const trainingDuration = ref(0)

const localData = ref({
  modelId: null as number | null,
  trainingConfig: {
    trainingEpochs: 10,
    batchSize: 32,
    learningRate: 0.001,
    optimizer: 'Adam',
    lossFunction: 'CrossEntropyLoss',
    scheduler: 'StepLR',
    weightDecay: 0.0001,
    momentum: 0.9
  },
  ...props.modelValue
})

// ==================== Computed ====================

const selectedModel = computed(() => {
  return recommendations.value.find((rec) => rec.model_id === selectedModelId.value)
})

// ==================== 推荐相关方法 ====================

/**
 * 加载推荐模型
 */
async function loadRecommendations() {
  if (!props.dataset?.datasetId) {
    ElMessage.warning("请先选择数据集")
    return
  }

  loading.value = true
  try {
    // 模拟 API 延迟
    await new Promise(resolve => setTimeout(resolve, 800))

    // Mock 数据集信息
    datasetInfo.value = {
      name: props.dataset.name || "数据集-" + props.dataset.datasetId,
      modality: props.dataset.modality || "image",
      task_type: props.dataset.task || "classification",
      sample_count: props.dataset.sampleCount || 10000,
      class_count: props.dataset.classCount || 10
    }

    // Mock 推荐模型数据
    const mockRecommendations: ModelRecommendationItem[] = [
      {
        model_id: 1,
        display_name: "ResNet-50",
        model_name: "resnet50",
        framework: "PyTorch",
        modality: props.dataset.modality || "image",
        task_type: props.dataset.task || "classification",
        description: "深度残差网络，适用于图像分类任务，具有良好的泛化能力和训练稳定性。在ImageNet等大规模数据集上表现优异。",
        tags: ["CNN", "残差网络"],
        recommendation_reason: "适合图像分类任务，性能稳定",
        default_config_preview: {
          epochs: 50,
          batch_size: 32,
          learning_rate: 0.001,
          optimizer: "Adam",
          loss_function: "CrossEntropyLoss",
          scheduler: "StepLR",
          weight_decay: 0.0001,
          momentum: 0.9
        }
      },
      {
        model_id: 2,
        display_name: "EfficientNet-B0",
        model_name: "efficientnet_b0",
        framework: "PyTorch",
        modality: props.dataset.modality || "image",
        task_type: props.dataset.task || "classification",
        description: "高效的卷积神经网络，在参数量和精度之间取得良好平衡，训练速度快，适合快速实验。",
        tags: ["CNN", "轻量级"],
        recommendation_reason: "轻量级模型，训练速度快",
        default_config_preview: {
          epochs: 40,
          batch_size: 64,
          learning_rate: 0.001,
          optimizer: "Adam",
          loss_function: "CrossEntropyLoss",
          scheduler: "CosineAnnealingLR",
          weight_decay: 0.00001,
          momentum: 0.9
        }
      },
      {
        model_id: 3,
        display_name: "Vision Transformer (ViT-B/16)",
        model_name: "vit_base_patch16",
        framework: "PyTorch",
        modality: props.dataset.modality || "image",
        task_type: props.dataset.task || "classification",
        description: "基于Transformer架构的视觉模型，在大规模数据集上性能优异，具有强大的特征提取能力。",
        tags: ["Transformer", "注意力机制"],
        recommendation_reason: "适合大规模数据集，特征提取能力强",
        default_config_preview: {
          epochs: 30,
          batch_size: 16,
          learning_rate: 0.0003,
          optimizer: "AdamW",
          loss_function: "CrossEntropyLoss",
          scheduler: "CosineAnnealingLR",
          weight_decay: 0.0001,
          momentum: 0.9
        }
      },
      {
        model_id: 4,
        display_name: "MobileNet-V3",
        model_name: "mobilenet_v3_large",
        framework: "PyTorch",
        modality: props.dataset.modality || "image",
        task_type: props.dataset.task || "classification",
        description: "专为移动设备优化的轻量级网络，推理速度极快，适合资源受限环境部署。",
        tags: ["轻量级", "移动端"],
        recommendation_reason: "超轻量级，适合资源受限环境",
        default_config_preview: {
          epochs: 60,
          batch_size: 128,
          learning_rate: 0.001,
          optimizer: "RMSprop",
          loss_function: "CrossEntropyLoss",
          scheduler: "StepLR",
          weight_decay: 0.00004,
          momentum: 0.9
        }
      },
      {
        model_id: 5,
        display_name: "DenseNet-121",
        model_name: "densenet121",
        framework: "PyTorch",
        modality: props.dataset.modality || "image",
        task_type: props.dataset.task || "classification",
        description: "密集连接卷积网络，特征重用效率高，参数效率好，适合中等规模数据集。",
        tags: ["CNN", "密集连接"],
        recommendation_reason: "参数效率高，适合中等规模数据集",
        default_config_preview: {
          epochs: 45,
          batch_size: 32,
          learning_rate: 0.0001,
          optimizer: "SGD",
          loss_function: "CrossEntropyLoss",
          scheduler: "ReduceLROnPlateau",
          weight_decay: 0.0001,
          momentum: 0.9
        }
      }
    ]

    recommendations.value = mockRecommendations.slice(0, 5)
    totalRecommended.value = mockRecommendations.length

    if (recommendations.value.length > 0) {
      ElMessage.success(`为您推荐了 ${recommendations.value.length} 个合适的模型`)
    } else {
      ElMessage.info("未找到合适的模型")
    }
    
    console.log("===== 模型推荐完成 =====")
    console.log("推荐了", recommendations.value.length, "个模型")
  } catch (error: any) {
    console.error("===== 模型推荐错误 =====")
    console.error("错误详情:", error)
    ElMessage.error(error.message || "模型推荐失败，请稍后重试")
  } finally {
    loading.value = false
  }
}

/**
 * 选择模型
 */
function selectModel(rec: ModelRecommendationItem) {
  selectedModelId.value = rec.model_id
  selectedModelInfo.value = rec
  localData.value.modelId = rec.model_id

  // 自动填充所有训练配置参数（来自预训练配置）
  if (rec.default_config_preview) {
    const config = rec.default_config_preview

    // 基础训练参数
    if (config.epochs) localData.value.trainingConfig.trainingEpochs = config.epochs
    if (config.batch_size) localData.value.trainingConfig.batchSize = config.batch_size
    if (config.learning_rate) localData.value.trainingConfig.learningRate = config.learning_rate

    // 优化器相关
    if (config.optimizer) localData.value.trainingConfig.optimizer = config.optimizer
    if (config.momentum !== undefined) localData.value.trainingConfig.momentum = config.momentum
    if (config.weight_decay !== undefined) localData.value.trainingConfig.weightDecay = config.weight_decay

    // 损失函数和调度器
    if (config.loss_function) localData.value.trainingConfig.lossFunction = config.loss_function
    if (config.scheduler) localData.value.trainingConfig.scheduler = config.scheduler
  }

  ElMessage.success(`已选择模型: ${rec.display_name}，训练配置已自动填充`)
}

/**
 * 表格行点击事件
 */
function handleRowClick(row: ModelRecommendationItem) {
  selectModel(row)
}

/**
 * 表格行类名
 */
function getRowClassName({ row }: { row: ModelRecommendationItem }): string {
  return row.model_id === selectedModelId.value ? 'selected-row' : ''
}

/**
 * 加载更多推荐
 */
function loadMore() {
  ElMessage.info("加载更多功能开发中")
}

/**
 * 获取模态类型文本
 */
function getModalityText(modality?: string): string {
  const map: Record<string, string> = {
    image: "图像",
    audio: "音频",
    video: "视频",
    text: "文本",
    sensor: "传感器",
    multimodal: "多模态",
    unknown: "未知",
  }
  return map[modality || ""] || modality || ""
}

/**
 * 获取任务类型文本
 */
function getTaskTypeText(taskType?: string): string {
  const map: Record<string, string> = {
    classification: "分类",
    object_detection: "目标检测",
    speech_recognition: "语音识别",
    regression: "回归",
    generation: "生成",
    anomaly_detection: "异常检测",
    segmentation: "分割",
    recommendation: "推荐",
    image_classification: "图像分类",
    text_classification: "文本分类",
    named_entity_recognition: "命名实体识别",
    instance_segmentation: "实例分割",
    audio_classification: "音频分类",
    sentiment_analysis: "情感分析",
    time_series_classification: "时序分类",
  }
  return map[taskType || ""] || taskType || ""
}

/**
 * 格式化任务类型列表
 */
function formatTaskTypes(rec: ModelRecommendationItem): string {
  const tasks = rec.recommendation_reason || ""
  return tasks.replace(/，建议.*$/, "")
}

/**
 * 获取模型图标颜色
 */
function getModelIconColor(index: number): string {
  const colors = [
    "#3b82f6", // 蓝色
    "#8b5cf6", // 紫色
    "#ec4899", // 粉色
    "#f59e0b", // 橙色
    "#10b981", // 绿色
  ]
  return colors[index % colors.length]
}

/**
 * 开始训练
 */
function startTraining() {
  if (!selectedModelInfo.value) {
    ElMessage.warning('请先选择模型')
    return
  }

  training.value = true
  trainingComplete.value = false
  trainingProgress.value = 0
  currentEpoch.value = 0
  trainingLoss.value = 2.5
  trainingAccuracy.value = 0
  const startTime = Date.now()

  ElMessage.success('开始训练模型...')

  // 模拟训练过程
  const totalEpochs = localData.value.trainingConfig.trainingEpochs
  const epochDuration = 500 // 每轮500ms

  const trainingInterval = setInterval(() => {
    if (currentEpoch.value < totalEpochs) {
      currentEpoch.value++
      trainingProgress.value = Math.floor((currentEpoch.value / totalEpochs) * 100)
      
      // 模拟loss下降和accuracy上升
      trainingLoss.value = 2.5 * Math.exp(-0.15 * currentEpoch.value) + Math.random() * 0.1
      trainingAccuracy.value = Math.min(95, 30 + (currentEpoch.value / totalEpochs) * 65 + Math.random() * 5)
    } else {
      clearInterval(trainingInterval)
      trainingProgress.value = 100
      training.value = false
      trainingComplete.value = true
      trainingDuration.value = Math.floor((Date.now() - startTime) / 1000)
      ElMessage.success('模型训练完成！')
    }
  }, epochDuration)
}

// ==================== Watchers ====================

// 监听数据集ID变化，自动加载推荐
watch(
  () => props.dataset?.datasetId,
  (newId) => {
    if (newId) {
      loadRecommendations()
    }
  },
  { immediate: true }
)

// 监听本地数据变化
watch(localData, (newVal) => {
  emit('update:modelValue', newVal)
}, { deep: true })

// 监听props变化
watch(() => props.modelValue, (newVal) => {
  localData.value = { ...localData.value, ...newVal }
}, { deep: true })
</script>

<style lang="scss" scoped>
.model-trainer {
  // ==================== 模型推荐区域样式 ====================
  .model-recommendation {
    padding: 20px;
    min-height: 400px;

    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 400px;
      color: var(--el-text-color-secondary);

      p {
        margin-top: 16px;
        font-size: 14px;
      }
    }

    .recommendation-results {
      .dataset-summary {
        margin-bottom: 24px;

        .dataset-meta {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-top: 8px;

          .meta-item {
            font-size: 13px;
            color: var(--el-text-color-secondary);
          }
        }
      }

      // 表格样式
      :deep(.el-table) {
        .selected-row {
          background-color: var(--el-color-primary-light-9) !important;
        }

        .el-table__row {
          cursor: pointer;
          transition: background-color 0.2s;

          &:hover {
            background-color: var(--el-fill-color-light);
          }
        }

        // 单元格内边距
        .el-table__cell {
          padding: 16px 12px;
        }
      }

      // 模型单元格样式
      .model-cell {
        display: flex;
        align-items: center;
        gap: 12px;

        .model-icon {
          width: 48px;
          height: 48px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);

          .icon-text {
            color: white;
            font-size: 18px;
            font-weight: bold;
          }
        }

        .model-info {
          flex: 1;
          min-width: 0;

          .model-name {
            font-size: 16px;
            font-weight: 600;
            color: var(--el-text-color-primary);
            margin-bottom: 4px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }

          .model-subtitle {
            font-size: 12px;
            color: var(--el-text-color-secondary);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
        }
      }

      // 任务类型样式
      .task-types {
        font-size: 14px;
        color: var(--el-text-color-regular);
        line-height: 1.6;
      }

      // 简介样式
      .description {
        font-size: 14px;
        color: var(--el-text-color-regular);
        line-height: 1.6;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      // 单选框样式
      :deep(.el-radio) {
        .el-radio__label {
          display: none;
        }

        .el-radio__input {
          margin: 0;
        }
      }

      .more-tip {
        text-align: center;
        padding: 16px;
        background: var(--el-fill-color-light);
        border-radius: 4px;
        margin-top: 16px;
      }
    }
  }

  // ==================== 训练配置区域样式 ====================
  .selected-model-config {
    padding: 24px;
    margin-top: 24px;
    background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
    border-radius: 12px;
    border: 1px solid var(--el-border-color-light);

    h4 {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0 0 20px 0;
      font-size: 16px;
      font-weight: 600;
      color: var(--el-text-color-primary);

      .el-icon {
        color: var(--el-color-primary);
      }
    }

    .training-params {
      padding: 16px;
      background: white;
      border-radius: 8px;
      margin-bottom: 16px;
    }

    .el-form-item {
      margin-bottom: 20px;
    }
  }

  // ==================== 开始训练按钮样式 ====================
  .start-training-button-container {
    display: flex;
    justify-content: center;
    padding: 32px 0 24px;

    .el-button {
      min-width: 280px;
      font-size: 15px;
      font-weight: 500;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(103, 194, 58, 0.3);
      transition: all 0.3s ease;

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(103, 194, 58, 0.4);
      }
    }
  }

  // ==================== 训练进行中样式 ====================
  .training-panel {
    max-width: 600px;
    margin: 0 auto;
    padding: 48px 32px;
    text-align: center;
    background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
    border-radius: 12px;
    border: 1px solid var(--el-border-color-light);

    .training-animation {
      margin-bottom: 24px;

      .rotating-icon {
        animation: rotate 2s linear infinite;
      }
    }

    .training-text {
      font-size: 24px;
      font-weight: 600;
      margin-bottom: 12px;
      color: var(--el-text-color-primary);
    }

    .training-hint {
      color: var(--el-text-color-secondary);
      margin-bottom: 32px;
    }

    .progress-bar {
      margin-bottom: 24px;
    }

    .training-metrics {
      display: flex;
      justify-content: space-around;
      gap: 20px;
      margin-bottom: 16px;
      padding: 20px;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);

      .metric-item {
        display: flex;
        flex-direction: column;
        gap: 8px;

        .metric-label {
          font-size: 12px;
          color: var(--el-text-color-secondary);
        }

        .metric-value {
          font-size: 18px;
          font-weight: 600;
          color: var(--el-color-success);
        }
      }
    }

    .progress-text {
      font-size: 14px;
      color: var(--el-text-color-secondary);
    }
  }

  // ==================== 训练完成样式 ====================
  .training-complete-panel {
    max-width: 700px;
    margin: 0 auto;
    padding: 32px;
    background: linear-gradient(135deg, #f0f9ff 0%, #ffffff 100%);
    border-radius: 12px;
    border: 1px solid var(--el-border-color-light);

    .complete-header {
      display: flex;
      flex-direction: column;
      gap: 16px;
      align-items: center;
      margin-bottom: 32px;

      h3 {
        margin: 0;
        font-size: 24px;
        font-weight: 600;
        color: var(--el-color-success);
      }
    }

    .training-result {
      border-radius: 8px;
      overflow: hidden;
    }
  }

  // ==================== 下一步按钮样式 ====================
  .next-button-container {
    display: flex;
    justify-content: center;
    padding: 32px 0 24px;

    .el-button {
      min-width: 280px;
      font-size: 15px;
      font-weight: 500;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
      transition: all 0.3s ease;

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
      }
    }
  }

  .evaluation-form {
    max-width: 800px;
    margin: 0 auto;
  }

  // ==================== 动画定义 ====================
  @keyframes rotate {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
}
</style>
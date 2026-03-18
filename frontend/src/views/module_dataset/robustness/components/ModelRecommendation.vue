<!-- 模型推荐组件 -->
<template>
  <div class="model-recommendation">
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
              :value="row.model_id"
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

    <!-- 无推荐结果 -->
    <el-empty v-else description="暂无推荐模型">
      <el-button type="primary" @click="$emit('refresh')">刷新推荐</el-button>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { ElMessage } from "element-plus";
import {
  Loading,
  CircleCheckFilled,
} from "@element-plus/icons-vue";
import ModelAPI, {
  type ModelRecommendationRequest,
  type ModelRecommendationItem,
  type DatasetInfoForRecommendation,
} from "@/api/module_train/model";

// ==================== Props & Emits ====================

interface Props {
  datasetId: number | null;
  modality?: string;
  taskType?: string;
  topK?: number;
}

const props = withDefaults(defineProps<Props>(), {
  topK: 5,
});

const emit = defineEmits<{
  (e: "select", modelId: number, modelInfo: ModelRecommendationItem): void;
  (e: "refresh"): void;
}>();

// ==================== State ====================

const loading = ref(false);
const recommendations = ref<ModelRecommendationItem[]>([]);
const datasetInfo = ref<DatasetInfoForRecommendation | null>(null);
const totalRecommended = ref(0);
const selectedModelId = ref<number | undefined>(undefined);

// ==================== Computed ====================

const selectedModel = computed(() => {
  return recommendations.value.find((rec) => rec.model_id === selectedModelId.value);
});

// ==================== Methods ====================

/**
 * 加载推荐模型
 */
async function loadRecommendations() {
  if (!props.datasetId) {
    ElMessage.warning("请先选择数据集");
    return;
  }

  loading.value = true;
  try {
    const params: ModelRecommendationRequest = {
      dataset_id: props.datasetId,
      top_k: props.topK,
      only_active: true,
    };

    if (props.modality) {
      params.modality = props.modality;
    }
    if (props.taskType) {
      params.task_type = props.taskType;
    }

    // 调试信息
    console.log("===== 模型推荐调试信息 =====");
    console.log("Props:", {
      datasetId: props.datasetId,
      modality: props.modality,
      taskType: props.taskType,
      topK: props.topK
    });
    console.log("发送的参数:", params);

    const { data } = await ModelAPI.recommend(params);

    console.log("API响应:", data);

    if (data.code === 200 || data.code === 0) {
      if (data.data) {
        console.log("推荐结果:", {
          total: data.data.total_recommended,
          count: data.data.recommendations?.length,
          recommendations: data.data.recommendations
        });
        console.log("数据集信息:", data.data.dataset_info);

        recommendations.value = data.data.recommendations;
        datasetInfo.value = data.data.dataset_info;
        totalRecommended.value = data.data.total_recommended;

        if (recommendations.value.length > 0) {
          ElMessage.success(`为您推荐了 ${recommendations.value.length} 个合适的模型`);
        } else {
          ElMessage.info("未找到合适的模型");
        }
      }
    } else {
      console.warn("API返回了意外的状态码:", data.code);
      ElMessage.warning("推荐请求失败");
    }
    console.log("===== 调试信息结束 =====");
  } catch (error: any) {
    console.error("===== 模型推荐错误 =====");
    console.error("错误详情:", error);
    console.error("错误响应:", error.response?.data);
    console.error("===== 错误信息结束 =====");
    ElMessage.error(error.message || "模型推荐失败，请稍后重试");
  } finally {
    loading.value = false;
  }
}

/**
 * 选择模型
 */
function selectModel(rec: ModelRecommendationItem) {
  selectedModelId.value = rec.model_id;
  emit("select", rec.model_id, rec);

  // 增加使用次数
  ModelAPI.incrementUsage(rec.model_id).catch((err) => {
    console.warn("更新使用次数失败:", err);
  });
}

/**
 * 表格行点击事件
 */
function handleRowClick(row: ModelRecommendationItem) {
  selectModel(row);
}

/**
 * 表格行类名
 */
function getRowClassName({ row }: { row: ModelRecommendationItem }): string {
  return row.model_id === selectedModelId.value ? 'selected-row' : '';
}

/**
 * 加载更多推荐
 */
function loadMore() {
  // TODO: 实现加载更多逻辑
  ElMessage.info("加载更多功能开发中");
}

/**
 * 获取评分颜色
 */
function getScoreColor(score: number): string {
  if (score >= 0.9) return "#67c23a";
  if (score >= 0.7) return "#409eff";
  if (score >= 0.5) return "#e6a23c";
  return "#f56c6c";
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
  };
  return map[modality || ""] || modality || "";
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
  };
  return map[taskType || ""] || taskType || "";
}

/**
 * 格式化任务类型列表
 */
function formatTaskTypes(rec: ModelRecommendationItem): string {
  // 从后端获取的支持任务类型可能在 rec 对象中
  // 这里暂时显示推荐理由中的任务信息
  const tasks = rec.recommendation_reason || "";
  return tasks.replace(/，建议.*$/, ""); // 去掉建议部分，只保留任务描述
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
  ];
  return colors[index % colors.length];
}

/**
 * 获取评分颜色（徽章背景）
 */
function getScoreColorBadge(score: number): string {
  if (score >= 0.9) return "#10b981"; // 绿色
  if (score >= 0.8) return "#3b82f6"; // 蓝色
  if (score >= 0.7) return "#f59e0b"; // 橙色
  return "#6b7280"; // 灰色
}

/**
 * 格式化指标键名
 */
function formatMetricKey(key: string): string {
  const map: Record<string, string> = {
    accuracy: "准确率",
    precision: "精确率",
    recall: "召回率",
    f1_score: "F1分数",
    map: "mAP",
    inference_speed: "推理速度",
    model_size: "模型大小",
    params: "参数量",
  };
  return map[key] || key;
}

/**
 * 格式化指标值
 */
function formatMetricValue(value: any): string {
  if (typeof value === "number") {
    if (value < 1) {
      return (value * 100).toFixed(2) + "%";
    }
    return value.toString();
  }
  return String(value);
}

/**
 * 格式化配置键名
 */
function formatConfigKey(key: string): string {
  const map: Record<string, string> = {
    learning_rate: "学习率",
    batch_size: "批次大小",
    epochs: "训练轮数",
    optimizer: "优化器",
    loss_function: "损失函数",
    gpu_memory: "GPU显存",
    cpu_cores: "CPU核心数",
    ram: "内存",
  };
  return map[key] || key;
}

// ==================== Watchers ====================

// 监听数据集ID变化，自动加载推荐
watch(
  () => props.datasetId,
  (newId) => {
    if (newId) {
      loadRecommendations();
    }
  },
  { immediate: true }
);

// ==================== Expose ====================

defineExpose({
  loadRecommendations,
  selectedModelId,
  selectedModel,
});
</script>

<style scoped lang="scss">
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
    }
  }
}
</style>

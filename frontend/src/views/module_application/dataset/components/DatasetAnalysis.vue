<!-- 数据集分析结果展示组件 -->
<template>
  <div class="dataset-analysis-container">
    <el-card shadow="hover" class="analysis-card">
      <template #header>
        <div class="card-header">
          <span class="font-semibold">数据集分析结果</span>
          <el-button
            v-if="!analyzing && !analysisComplete"
            type="primary"
            :loading="analyzing"
            @click="startAnalysis"
          >
            <el-icon class="mr-2"><DataAnalysis /></el-icon>
            开始分析
          </el-button>
          <el-button
            v-else-if="analysisComplete"
            type="success"
            @click="downloadReport"
          >
            <el-icon class="mr-2"><Download /></el-icon>
            下载报告
          </el-button>
        </div>
      </template>

      <!-- 分析进度 -->
      <div v-if="analyzing" class="analyzing-section">
        <div class="analyzing-animation">
          <el-icon :size="64" class="rotating-icon" color="#409eff">
            <Loading />
          </el-icon>
        </div>
        <p class="analyzing-text">正在分析数据集...</p>
        <p class="analyzing-hint">正在识别模态类型、统计样本数量、提取元数据</p>

        <el-progress
          :percentage="analysisProgress"
          :stroke-width="12"
          :striped="true"
          :striped-flow="true"
          class="mt-6"
        />
      </div>

      <!-- 分析结果 -->
      <div v-else-if="analysisComplete && analysisData" class="analysis-results">
        <!-- 基础信息 -->
        <div class="result-section">
          <h3 class="section-title">基础信息</h3>
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="info-card">
                <div class="info-icon" style="background: #e1f5fe">
                  <el-icon :size="24" color="#0288d1">
                    <DataLine />
                  </el-icon>
                </div>
                <div class="info-content">
                  <div class="info-label">模态类型</div>
                  <div class="info-value">{{ getModalityText(analysisData.modality) }}</div>
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-card">
                <div class="info-icon" style="background: #f3e5f5">
                  <el-icon :size="24" color="#7b1fa2">
                    <DocumentCopy />
                  </el-icon>
                </div>
                <div class="info-content">
                  <div class="info-label">样本数量</div>
                  <div class="info-value">{{ formatNumber(analysisData.sample_count) }}</div>
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-card">
                <div class="info-icon" style="background: #e8f5e9">
                  <el-icon :size="24" color="#388e3c">
                    <Grid />
                  </el-icon>
                </div>
                <div class="info-content">
                  <div class="info-label">类别数量</div>
                  <div class="info-value">
                    {{ analysisData.class_count || "未知" }}
                  </div>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 分析结果详情 -->
        <div v-if="analysisData.analysis_result" class="result-section">
          <h3 class="section-title">分析详情</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="分析状态">
              <el-tag :type="getStatusType(analysisData.analysis_result.status)">
                {{ getStatusText(analysisData.analysis_result.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="分析时间">
              {{ formatDateTime(analysisData.analysis_result.analyzed_at) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 数据集预览 -->
        <div v-if="previewData && previewData.items.length > 0" class="result-section">
          <h3 class="section-title">数据集预览 (前{{ previewData.items.length }}个样本)</h3>
          <el-table :data="previewData.items" stripe border>
            <el-table-column type="index" label="#" width="60" />
            <el-table-column prop="filename" label="文件名" min-width="200" show-overflow-tooltip />
            <el-table-column label="文件大小" width="120">
              <template #default="{ row }">
                {{ formatFileSize(row.size) }}
              </template>
            </el-table-column>
            <el-table-column label="压缩大小" width="120">
              <template #default="{ row }">
                {{ formatFileSize(row.compressed_size) }}
              </template>
            </el-table-column>
            <el-table-column prop="extension" label="格式" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ row.extension }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <!-- 未开始分析 -->
      <div v-else class="empty-state">
        <el-empty description="暂无分析结果，点击开始分析按钮进行数据集分析" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import {
  DataAnalysis,
  Download,
  Loading,
  DataLine,
  DocumentCopy,
  Grid,
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import DatasetAPI, {
  type DatasetAnalysisStatus,
  type DatasetPreviewResponse,
} from "@/api/module_application/dataset";
import { formatToDateTime } from "@/utils/dateUtil";

// Props
const props = defineProps<{
  datasetId: number;
}>();

// Emits
const emit = defineEmits(["analysis-complete"]);

// 分析状态
const analyzing = ref(false);
const analysisComplete = ref(false);
const analysisProgress = ref(0);
const analysisData = ref<DatasetAnalysisStatus | null>(null);
const previewData = ref<DatasetPreviewResponse | null>(null);

// 模态类型映射
const modalityMap: Record<string, string> = {
  image: "图像",
  audio: "音频",
  video: "视频",
  text: "文本",
  sensor: "传感器",
  multimodal: "多模态",
  unknown: "未知",
};

// 获取模态类型文本
function getModalityText(modality: string): string {
  return modalityMap[modality] || modality;
}

// 获取状态类型
function getStatusType(status: string): "success" | "info" | "warning" | "danger" {
  const typeMap: Record<string, "success" | "info" | "warning" | "danger"> = {
    completed: "success",
    running: "info",
    pending: "warning",
    failed: "danger",
  };
  return typeMap[status] || "info";
}

// 获取状态文本
function getStatusText(status: string): string {
  const textMap: Record<string, string> = {
    completed: "已完成",
    running: "分析中",
    pending: "待分析",
    failed: "失败",
    not_started: "未开始",
  };
  return textMap[status] || status;
}

// 格式化数字
function formatNumber(num: number | undefined): string {
  if (num === undefined) return "未知";
  return num.toLocaleString();
}

// 格式化文件大小
function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

// 格式化日期时间
function formatDateTime(dateStr: string | undefined): string {
  if (!dateStr) return "未知";
  try {
    return formatToDateTime(dateStr, "YYYY-MM-DD HH:mm:ss");
  } catch {
    return dateStr;
  }
}

// 开始分析
async function startAnalysis() {
  analyzing.value = true;
  analysisProgress.value = 0;

  // 模拟进度
  const progressInterval = setInterval(() => {
    if (analysisProgress.value < 90) {
      analysisProgress.value += 10;
    }
  }, 300);

  try {
    // 调用分析接口
    await DatasetAPI.analyze(props.datasetId);

    // 轮询获取分析状态
    let retryCount = 0;
    const maxRetries = 30;

    const checkStatus = async () => {
      if (retryCount >= maxRetries) {
        clearInterval(progressInterval);
        ElMessage.error("分析超时，请稍后重试");
        analyzing.value = false;
        return;
      }

      try {
        const response = await DatasetAPI.getAnalyzeStatus(props.datasetId);
        const data = response.data.data;

        if (data.status === "completed") {
          clearInterval(progressInterval);
          analysisProgress.value = 100;
          analysisData.value = data;
          analyzing.value = false;
          analysisComplete.value = true;

          // 加载预览数据
          await loadPreviewData();

          ElMessage.success("数据集分析完成!");
          emit("analysis-complete", data);
        } else if (data.status === "failed") {
          clearInterval(progressInterval);
          ElMessage.error("数据集分析失败");
          analyzing.value = false;
        } else {
          // 继续轮询
          retryCount++;
          setTimeout(checkStatus, 1000);
        }
      } catch (error: any) {
        clearInterval(progressInterval);
        ElMessage.error("获取分析状态失败: " + (error.message || "未知错误"));
        analyzing.value = false;
      }
    };

    // 开始轮询
    setTimeout(checkStatus, 1000);
  } catch (error: any) {
    clearInterval(progressInterval);
    ElMessage.error("启动分析失败: " + (error.message || "未知错误"));
    analyzing.value = false;
  }
}

// 加载预览数据
async function loadPreviewData() {
  try {
    const response = await DatasetAPI.preview(props.datasetId, 5);
    previewData.value = response.data.data;
  } catch (error: any) {
    console.error("加载预览数据失败:", error);
  }
}

// 下载报告
function downloadReport() {
  ElMessage.info("下载功能开发中...");
}

// 初始化
onMounted(async () => {
  // 尝试加载已有的分析结果
  try {
    const response = await DatasetAPI.getAnalyzeStatus(props.datasetId);
    const data = response.data.data;

    if (data.status === "completed") {
      analysisData.value = data;
      analysisComplete.value = true;
      await loadPreviewData();
    }
  } catch (error) {
    // 忽略错误，可能是还未分析
    console.log("暂无分析结果");
  }
});
</script>

<script lang="ts">
export default {
  name: "DatasetAnalysis",
};
</script>

<style lang="scss" scoped>
.dataset-analysis-container {
  .analysis-card {
    border-radius: 16px;
    overflow: hidden;
  }

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .analyzing-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 300px;
    padding: 48px 24px;

    .analyzing-animation {
      margin-bottom: 24px;

      .rotating-icon {
        animation: rotate 2s linear infinite;
      }
    }

    .analyzing-text {
      margin: 0 0 8px;
      font-size: 18px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }

    .analyzing-hint {
      margin: 0 0 24px;
      font-size: 14px;
      color: var(--el-text-color-secondary);
    }
  }

  @keyframes rotate {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  .analysis-results {
    .result-section {
      margin-bottom: 32px;

      &:last-child {
        margin-bottom: 0;
      }

      .section-title {
        margin: 0 0 16px;
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }

      .info-card {
        display: flex;
        gap: 16px;
        align-items: center;
        padding: 20px;
        background: var(--el-bg-color);
        border: 1px solid var(--el-border-color-lighter);
        border-radius: 12px;
        transition: all 0.3s ease;

        &:hover {
          border-color: var(--el-color-primary);
          box-shadow: 0 4px 12px rgba(var(--el-color-primary-rgb), 0.15);
          transform: translateY(-2px);
        }

        .info-icon {
          display: flex;
          flex-shrink: 0;
          align-items: center;
          justify-content: center;
          width: 56px;
          height: 56px;
          border-radius: 12px;
        }

        .info-content {
          flex: 1;
          min-width: 0;

          .info-label {
            margin-bottom: 6px;
            font-size: 13px;
            color: var(--el-text-color-secondary);
          }

          .info-value {
            overflow: hidden;
            text-overflow: ellipsis;
            font-size: 24px;
            font-weight: 700;
            color: var(--el-text-color-primary);
            white-space: nowrap;
          }
        }
      }
    }
  }

  .empty-state {
    min-height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}
</style>

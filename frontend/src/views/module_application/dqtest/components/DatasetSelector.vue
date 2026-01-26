<!-- 数据集选择 - 集成上传、列表、分析功能 -->
<template>
  <div class="app-container dataset-management">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #e1f5fe">
              <el-icon :size="32" color="#0288d1">
                <DataBoard />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">总数据集</div>
              <div class="stat-value">{{ statistics.total_count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #e8f5e9">
              <el-icon :size="32" color="#388e3c">
                <CircleCheck />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">上传完成</div>
              <div class="stat-value">{{ statistics.completed_count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #fff3e0">
              <el-icon :size="32" color="#f57c00">
                <Loading />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">上传中</div>
              <div class="stat-value">{{ statistics.uploading_count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #fce4ec">
              <el-icon :size="32" color="#c2185b">
                <FolderOpened />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">总存储</div>
              <div class="stat-value">{{ formatFileSize(statistics.total_size) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 选中的数据集提示 -->
    <el-card v-if="selectedDataset" shadow="hover" class="selected-dataset-card">
      <div class="selected-dataset-content">
        <div class="selected-icon">
          <el-icon :size="32" color="#67c23a">
            <CircleCheck />
          </el-icon>
        </div>
        <div class="selected-info">
          <div class="selected-title">已选择数据集</div>
          <div class="selected-name">{{ selectedDataset.name }}</div>
          <div class="selected-meta">
            <el-tag :type="getModalityTagType(selectedDataset.modality)" size="small">
              {{ getModalityText(selectedDataset.modality) }}
            </el-tag>
            <span class="meta-divider">·</span>
            <span>{{ formatFileSize(selectedDataset.file_size) }}</span>
            <span class="meta-divider">·</span>
            <span>{{ selectedDataset.sample_count || '未知' }} 样本</span>
          </div>
        </div>
        <el-button type="danger" text @click="clearSelection">
          <el-icon><Close /></el-icon>
          取消选择
        </el-button>
      </div>
    </el-card>

    <!-- Tab 切换 -->
    <el-card shadow="hover" class="main-card">
      <el-tabs v-model="activeTab" type="border-card" class="dataset-tabs">
        <!-- 数据集上传 -->
        <el-tab-pane label="上传新数据集" name="upload">
          <template #label>
            <span class="tab-label">
              <el-icon><Upload /></el-icon>
              上传新数据集
            </span>
          </template>

          <div class="tab-content">
            <!-- 上传区域 -->
            <div v-if="!uploadedFile" class="upload-zone" :class="{ 'upload-zone-dragover': dragover }" @dragover.prevent="handleDragOver" @dragleave.prevent="handleDragLeave" @drop.prevent="handleDrop" @click="triggerFileInput">
              <input ref="fileInputRef" type="file" accept=".zip,.tar,.gz,.rar,.7z,.tar.gz,.tar.bz2" style="display: none" @change="handleFileChange" />

              <div class="upload-icon">
                <el-icon :size="64" color="#409eff">
                  <UploadFilled />
                </el-icon>
              </div>

              <div class="upload-text">
                <p class="upload-title">点击或拖拽文件到此处上传</p>
                <p class="upload-hint">支持格式: ZIP, TAR, GZ, RAR, 7Z</p>
                <p class="upload-hint">支持 10GB+ 大文件、断点续传</p>
              </div>

              <el-button type="primary" size="large" class="mt-4">
                <el-icon class="mr-2"><Upload /></el-icon>
                选择文件
              </el-button>
            </div>

            <!-- 上传进度显示 -->
            <div v-else class="upload-progress-container">
              <el-card shadow="hover" class="file-info-card">
                <template #header>
                  <div class="card-header">
                    <span class="font-semibold">文件信息</span>
                    <el-button v-if="!uploading && uploadProgress < 100" type="danger" link @click="cancelUpload">
                      <el-icon><Close /></el-icon>
                      取消上传
                    </el-button>
                  </div>
                </template>

                <div class="file-info">
                  <div class="file-icon">
                    <el-icon :size="48" color="#409eff">
                      <Document />
                    </el-icon>
                  </div>
                  <div class="file-details">
                    <div class="file-name">{{ uploadedFile.name }}</div>
                    <div class="file-size">{{ formatFileSize(uploadedFile.size) }}</div>
                  </div>
                </div>

                <el-divider />
                <el-form :model="datasetForm" label-width="100px" label-position="left">
                  <el-form-item label="数据集名称">
                    <el-input v-model="datasetForm.name" placeholder="请输入数据集名称" :disabled="uploading || uploadProgress >= 100" />
                  </el-form-item>
                  <el-form-item label="任务类型" required>
                    <el-select v-model="datasetForm.taskType" placeholder="请选择任务类型" :disabled="uploading || uploadProgress >= 100" style="width: 100%" filterable>
                      <el-option v-for="task in taskTypes" :key="task.value" :label="task.label" :value="task.value" />
                    </el-select>
                  </el-form-item>
                </el-form>

                <!-- 上传进度条 -->
                <div v-if="uploadProgress > 0" class="progress-section">
                  <div class="progress-header">
                    <span class="progress-label">上传进度</span>
                    <span class="progress-value">{{ uploadProgress.toFixed(1) }}%</span>
                  </div>

                  <el-progress :percentage="uploadProgress" :status="uploadStatus" :stroke-width="18" :striped="uploading" :striped-flow="uploading" />

                  <div class="progress-stats">
                    <div class="stat-item">
                      <el-icon><Clock /></el-icon>
                      <span>剩余时间: {{ remainingTime }}</span>
                    </div>
                    <div class="stat-item">
                      <el-icon><Odometer /></el-icon>
                      <span>速度: {{ uploadSpeed }} MB/s</span>
                    </div>
                    <div class="stat-item">
                      <el-icon><Checked /></el-icon>
                      <span>已上传: {{ uploadedChunks }} / {{ totalChunks }} 分片</span>
                    </div>
                  </div>
                </div>

                <!-- 操作按钮 -->
                <div class="action-buttons">
                  <el-button v-if="!uploading && uploadProgress === 0" type="primary" size="large" @click="startUpload">
                    <el-icon class="mr-2"><Upload /></el-icon>
                    开始上传
                  </el-button>

                  <template v-else-if="uploading && uploadProgress < 100">
                    <el-button type="warning" size="large" @click="pauseUpload">
                      <el-icon class="mr-2"><VideoPause /></el-icon>
                      暂停
                    </el-button>
                  </template>

                  <template v-else-if="uploadPaused && uploadProgress < 100">
                    <el-button type="success" size="large" @click="resumeUpload">
                      <el-icon class="mr-2"><VideoPlay /></el-icon>
                      继续上传
                    </el-button>
                    <el-button type="danger" size="large" @click="cancelUpload">
                      <el-icon class="mr-2"><Close /></el-icon>
                      取消
                    </el-button>
                  </template>

                  <template v-else-if="uploadProgress >= 100">
                    <el-button type="success" size="large" disabled>
                      <el-icon class="mr-2"><CircleCheck /></el-icon>
                      上传完成
                    </el-button>
                    <el-button type="primary" size="large" @click="proceedToAnalysis">
                      下一步：数据集分析
                      <el-icon class="ml-2"><ArrowRight /></el-icon>
                    </el-button>
                  </template>
                </div>
              </el-card>

              <!-- 上传日志 -->
              <el-card v-if="uploadLogs.length > 0" shadow="hover" class="log-card mt-4">
                <template #header>
                  <div class="card-header">
                    <span class="font-semibold">上传日志</span>
                    <el-button type="primary" link @click="uploadLogs = []">
                      <el-icon><Delete /></el-icon>
                      清空
                    </el-button>
                  </div>
                </template>

                <div class="log-container">
                  <div v-for="(log, index) in uploadLogs" :key="index" class="log-item" :class="`log-${log.type}`">
                    <span class="log-time">{{ log.time }}</span>
                    <span class="log-message">{{ log.message }}</span>
                  </div>
                </div>
              </el-card>
            </div>
          </div>
        </el-tab-pane>

        <!-- 数据集列表 -->
        <el-tab-pane label="选择已有数据集" name="list">
          <template #label>
            <span class="tab-label">
              <el-icon><List /></el-icon>
              选择已有数据集
            </span>
          </template>

          <div class="tab-content">
            <!-- 模态类型选择 -->
            <div class="modality-selector">
              <div class="selector-label">* 模态类型</div>
              <div class="modality-buttons">
                <el-button
                  v-for="modality in modalityOptions"
                  :key="modality.value"
                  :type="selectedModality === modality.value ? 'primary' : ''"
                  @click="selectModality(modality.value)"
                  class="modality-btn"
                >
                  {{ modality.label }}
                </el-button>
              </div>
            </div>

            <!-- 数据集选择下拉框 -->
            <div class="dataset-selector">
              <div class="selector-label">* 数据集选择</div>
              <el-select
                v-model="selectedDatasetName"
                placeholder="请选择数据集"
                @change="handleDatasetSelect"
                style="width: 100%"
                size="large"
                filterable
              >
                <el-option
                  v-for="dataset in filteredDatasets"
                  :key="dataset.id"
                  :label="dataset.name"
                  :value="dataset.name"
                >
                  <span style="float: left">{{ dataset.name }}</span>
                  <span style="float: right; color: var(--el-text-color-secondary); font-size: 13px">
                    {{ formatFileSize(dataset.file_size) }}
                  </span>
                </el-option>
              </el-select>
            </div>

            <!-- 数据集详情 -->
            <div v-if="selectedDataset" class="dataset-details">
              <div class="details-title">数据集详情</div>
              <div class="details-grid">
                <div class="detail-row">
                  <div class="detail-label">数据集名称</div>
                  <div class="detail-value">{{ selectedDataset.name }}</div>
                </div>
                <div class="detail-row">
                  <div class="detail-label">原始文件名</div>
                  <div class="detail-value">{{ selectedDataset.original_filename }}</div>
                </div>
                <div class="detail-row">
                  <div class="detail-label">文件大小</div>
                  <div class="detail-value">{{ formatFileSize(selectedDataset.file_size) }}</div>
                </div>
                <div class="detail-row">
                  <div class="detail-label">任务类型</div>
                  <div class="detail-value">
                    <el-tag size="small">{{ getTaskTypeText(selectedDataset.task_type) }}</el-tag>
                  </div>
                </div>
                <div class="detail-row">
                  <div class="detail-label">样本数量</div>
                  <div class="detail-value">{{ selectedDataset.sample_count || '未知' }}</div>
                </div>
                <div class="detail-row">
                  <div class="detail-label">类别数量</div>
                  <div class="detail-value">{{ selectedDataset.class_count || '未知' }}</div>
                </div>
                <div class="detail-row">
                  <div class="detail-label">上传状态</div>
                  <div class="detail-value">
                    <el-tag :type="getStatusTagType(selectedDataset.upload_status)" size="small">
                      {{ getStatusText(selectedDataset.upload_status) }}
                    </el-tag>
                  </div>
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="detail-actions">
                <el-button type="primary" @click="handleAnalyzeDataset(selectedDataset)">
                  <el-icon><DataAnalysis /></el-icon>
                  分析数据集
                </el-button>
                <el-button @click="handleDeleteDataset(selectedDataset)">
                  <el-icon><Delete /></el-icon>
                  删除数据集
                </el-button>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 数据集分析 -->
        <el-tab-pane v-if="currentDatasetId" label="数据集分析" name="analysis">
          <template #label>
            <span class="tab-label">
              <el-icon><DataAnalysis /></el-icon>
              数据集分析
            </span>
          </template>

          <div class="tab-content">
            <!-- 分析组件内容 -->
            <el-card shadow="hover" class="analysis-card">
              <template #header>
                <div class="card-header">
                  <span class="font-semibold">数据集分析结果</span>
                  <el-button v-if="!analyzing && !analysisComplete" type="primary" :loading="analyzing" @click="startAnalysis">
                    <el-icon class="mr-2"><DataAnalysis /></el-icon>
                    开始分析
                  </el-button>
                  <el-button v-else-if="analysisComplete" type="success" @click="downloadReport">
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

                <el-progress :percentage="analysisProgress" :stroke-width="12" :striped="true" :striped-flow="true" class="mt-6" />
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
                          <div class="info-value">{{ analysisData.class_count || "未知" }}</div>
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
                      <el-tag :type="getAnalysisStatusType(analysisData.analysis_result.status)">
                        {{ getAnalysisStatusText(analysisData.analysis_result.status) }}
                      </el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="分析时间">
                      {{ formatDateTime(analysisData.analysis_result.analyzed_at) }}
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
              </div>

              <!-- 未开始分析 -->
              <div v-else class="empty-state">
                <el-empty description="暂无分析结果，点击开始分析按钮进行数据集分析" />
              </div>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 数据集详情弹窗 -->
    <el-drawer v-model="detailDrawerVisible" title="数据集详情" :size="600" direction="rtl">
      <div v-if="currentDataset" class="dataset-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="数据集名称">
            {{ currentDataset.name }}
          </el-descriptions-item>
          <el-descriptions-item label="原始文件名">
            {{ currentDataset.original_filename }}
          </el-descriptions-item>
          <el-descriptions-item label="模态类型">
            <el-tag :type="getModalityTagType(currentDataset.modality)" size="small">
              {{ getModalityText(currentDataset.modality) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="上传状态">
            <el-tag :type="getStatusTagType(currentDataset.upload_status)" size="small">
              {{ getStatusText(currentDataset.upload_status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="文件大小">
            {{ formatFileSize(currentDataset.file_size) }}
          </el-descriptions-item>
          <el-descriptions-item label="样本数量">
            {{ currentDataset.sample_count || "未分析" }}
          </el-descriptions-item>
          <el-descriptions-item label="类别数量">
            {{ currentDataset.class_count || "未分析" }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">
            {{ formatDateTime(currentDataset.created_time) }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ currentDataset.description || "暂无描述" }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-drawer>

    <!-- 编辑弹窗 -->
    <el-drawer v-model="editDrawerVisible" title="编辑数据集" :size="600" direction="rtl" @close="handleCloseEditDrawer">
      <el-form ref="editFormRef" :model="editFormData" :rules="editFormRules" label-width="100px" label-position="right">
        <el-form-item label="数据集名称" prop="name">
          <el-input v-model="editFormData.name" placeholder="请输入数据集名称" />
        </el-form-item>
        <el-form-item label="模态类型" prop="modality">
          <el-select v-model="editFormData.modality" placeholder="请选择模态类型">
            <el-option label="图像" value="image" />
            <el-option label="音频" value="audio" />
            <el-option label="视频" value="video" />
            <el-option label="文本" value="text" />
            <el-option label="传感器" value="sensor" />
            <el-option label="多模态" value="multimodal" />
          </el-select>
        </el-form-item>
        <el-form-item label="样本数量" prop="sample_count">
          <el-input-number v-model="editFormData.sample_count" :min="0" :controls="true" style="width: 100%" />
        </el-form-item>
        <el-form-item label="类别数量" prop="class_count">
          <el-input-number v-model="editFormData.class_count" :min="0" :controls="true" style="width: 100%" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="editFormData.description" type="textarea" :rows="4" placeholder="请输入数据集描述" maxlength="200" show-word-limit />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleCloseEditDrawer">取消</el-button>
          <el-button type="primary" @click="handleSubmitEdit">确定</el-button>
        </div>
      </template>
    </el-drawer>

    <!-- 操作按钮 -->
    <div class="action-buttons-footer">
      <el-button type="primary" @click="handleNext">
        下一步：模型训练
        <el-icon class="ml-2"><ArrowRight /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from "vue";
import {
  DataBoard,
  CircleCheck,
  Loading,
  FolderOpened,
  Upload,
  UploadFilled,
  List,
  DataAnalysis,
  View,
  Edit,
  Delete,
  Document,
  Close,
  Clock,
  Odometer,
  Checked,
  VideoPause,
  VideoPlay,
  ArrowRight,
  Download,
  DataLine,
  DocumentCopy,
  Grid,
} from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";

defineOptions({
  name: "DatasetSelector",
  inheritAttrs: false,
});

// Emits
const emit = defineEmits(["update:modelValue", "next", "prev"]);

// Tab 切换
const activeTab = ref("upload");

// ==================== 统计数据 ====================
const statistics = ref({
  total_count: 12,
  completed_count: 8,
  uploading_count: 2,
  failed_count: 2,
  total_size: 15728640000, // 15GB
  modality_stats: {},
});

// ==================== 数据集上传相关 ====================
const fileInputRef = ref<HTMLInputElement>();
const dragover = ref(false);
const uploadedFile = ref<File | null>(null);
const uploading = ref(false);
const uploadPaused = ref(false);
const uploadProgress = ref(0);
const uploadSpeed = ref("0");
const remainingTime = ref("--:--");
const uploadedChunks = ref(0);
const totalChunks = ref(0);

const datasetForm = reactive({
  name: "",
  taskType: "classification",
  description: "",
});

const taskTypes = [
  { value: "classification", label: "分类" },
  { value: "object_detection", label: "目标检测" },
  { value: "speech_recognition", label: "语音识别" },
  { value: "regression", label: "回归" },
  { value: "generation", label: "生成" },
  { value: "anomaly_detection", label: "异常检测" },
  { value: "segmentation", label: "分割" },
  { value: "recommendation", label: "推荐" },
];

const uploadLogs = ref<Array<{ time: string; message: string; type: string }>>([]);

const uploadStatus = computed(() => {
  if (uploadProgress.value >= 100) return "success";
  if (uploadPaused.value) return "warning";
  return undefined;
});

// ==================== 数据集列表相关 ====================
const queryFormRef = ref();
const loading = ref(false);
const total = ref(0);
const datasetList = ref<any[]>([]);
const queryFormData = reactive({
  page_no: 1,
  page_size: 10,
  name: undefined,
  modality: undefined,
  upload_status: undefined,
});

// ==================== 当前数据集 ====================
const currentDatasetId = ref<number | null>(null);
const currentDataset = ref<any | null>(null);

// ==================== 选中的数据集 ====================
const selectedDatasetId = ref<number | null>(null);
const selectedDataset = ref<any | null>(null);

// ==================== 模态类型和数据集选择 ====================
const selectedModality = ref<string>('image');
const selectedDatasetName = ref<string>('');

const modalityOptions = [
  { label: '图像', value: 'image' },
  { label: '音频', value: 'audio' },
  { label: '视频', value: 'video' },
  { label: '文本', value: 'text' },
  { label: '传感器', value: 'sensor' },
  { label: '多模态', value: 'multimodal' },
];

const filteredDatasets = computed(() => {
  return datasetList.value.filter(dataset => dataset.modality === selectedModality.value);
});

// ==================== 详情和编辑弹窗 ====================
const detailDrawerVisible = ref(false);
const editDrawerVisible = ref(false);
const editFormRef = ref();
const editFormData = reactive({
  name: "",
  modality: "",
  sample_count: 0,
  class_count: 0,
  description: "",
});

const editFormRules = reactive({
  name: [{ required: true, message: "请输入数据集名称", trigger: "blur" }],
  modality: [{ required: true, message: "请选择模态类型", trigger: "change" }],
});

// ==================== 数据集分析相关 ====================
const analyzing = ref(false);
const analysisComplete = ref(false);
const analysisProgress = ref(0);
const analysisData = ref<any | null>(null);

// ==================== 工具函数 ====================
const modalityMap: Record<string, string> = {
  image: "图像",
  audio: "音频",
  video: "视频",
  text: "文本",
  sensor: "传感器",
  multimodal: "多模态",
  unknown: "未知",
};

function getModalityText(modality: string): string {
  return modalityMap[modality] || modality;
}

function getModalityTagType(modality: string): "success" | "info" | "warning" | "danger" | "" {
  const typeMap: Record<string, "success" | "info" | "warning" | "danger"> = {
    image: "success",
    audio: "warning",
    video: "danger",
    text: "info",
  };
  return typeMap[modality] || "";
}

function getStatusText(status: string): string {
  const textMap: Record<string, string> = {
    init: "初始化",
    uploading: "上传中",
    completed: "已完成",
    failed: "失败",
  };
  return textMap[status] || status;
}

function getStatusTagType(status: string): "success" | "info" | "warning" | "danger" | "" {
  const typeMap: Record<string, "success" | "info" | "warning" | "danger"> = {
    completed: "success",
    uploading: "info",
    init: "warning",
    failed: "danger",
  };
  return typeMap[status] || "";
}

function getTaskTypeText(taskType: string | undefined): string {
  const taskMap: Record<string, string> = {
    classification: "分类",
    object_detection: "目标检测",
    speech_recognition: "语音识别",
    regression: "回归",
    generation: "生成",
    anomaly_detection: "异常检测",
    segmentation: "分割",
    recommendation: "推荐",
  };
  return taskType ? (taskMap[taskType] || taskType) : "未知";
}

function getAnalysisStatusText(status: string): string {
  const textMap: Record<string, string> = {
    completed: "已完成",
    running: "分析中",
    pending: "待分析",
    failed: "失败",
    not_started: "未开始",
  };
  return textMap[status] || status;
}

function getAnalysisStatusType(status: string): "success" | "info" | "warning" | "danger" {
  const typeMap: Record<string, "success" | "info" | "warning" | "danger"> = {
    completed: "success",
    running: "info",
    pending: "warning",
    failed: "danger",
  };
  return typeMap[status] || "info";
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

function formatDateTime(dateStr: string | undefined): string {
  if (!dateStr) return "-";
  try {
    const date = new Date(dateStr);
    return date.toLocaleString("zh-CN");
  } catch {
    return dateStr;
  }
}

function formatNumber(num: number | undefined): string {
  if (num === undefined) return "未知";
  return num.toLocaleString();
}

// ==================== 上传功能 ====================
function handleDragOver() {
  dragover.value = true;
}

function handleDragLeave() {
  dragover.value = false;
}

function handleDrop(event: DragEvent) {
  dragover.value = false;
  const file = event.dataTransfer?.files[0];
  if (file) {
    selectFile(file);
  }
}

function triggerFileInput() {
  fileInputRef.value?.click();
}

function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (file) {
    selectFile(file);
  }
  target.value = "";
}

function selectFile(file: File) {
  const validExtensions = [".zip", ".tar", ".gz", ".rar", ".7z", ".tar.gz", ".tar.bz2"];
  const fileName = file.name.toLowerCase();
  const isValid = validExtensions.some((ext) => fileName.endsWith(ext));

  if (!isValid) {
    ElMessage.error("不支持的文件格式，请上传 ZIP、TAR、GZ、RAR 或 7Z 格式文件");
    return;
  }

  const maxSize = 100 * 1024 * 1024 * 1024;
  if (file.size > maxSize) {
    ElMessage.error("文件大小超过 100GB 限制");
    return;
  }

  uploadedFile.value = file;
  extractDatasetName(file.name);
  addLog("INFO", `已选择文件: ${file.name} (${formatFileSize(file.size)})`);
}

function extractDatasetName(fileName: string) {
  let name = fileName.replace(/\.[^/.]+$/, "");
  name = name.replace(/(_dataset|_data|_train|_test|_val)$/i, "");
  name = name.replace(/[_-]/g, " ");
  name = name.replace(/\b\w/g, (char) => char.toUpperCase());

  datasetForm.name = name || "未命名数据集";
  datasetForm.description = `基于 ${name} 数据集构建的多模态鲁棒性评估模型`;
}

async function startUpload() {
  if (!uploadedFile.value) return;

  uploading.value = true;
  uploadPaused.value = false;
  uploadProgress.value = 0;
  addLog("INFO", "开始上传文件...");

  // Mock上传过程
  const chunkSize = 5 * 1024 * 1024;
  totalChunks.value = Math.ceil(uploadedFile.value.size / chunkSize);
  uploadedChunks.value = 0;

  const startTime = Date.now();
  const uploadInterval = setInterval(() => {
    if (uploadPaused.value || uploadProgress.value >= 100) {
      clearInterval(uploadInterval);
      return;
    }

    uploadedChunks.value++;
    uploadProgress.value = (uploadedChunks.value / totalChunks.value) * 100;

    // 计算速度和剩余时间
    const elapsedSeconds = (Date.now() - startTime) / 1000;
    const uploadedBytes = uploadedChunks.value * chunkSize;
    const speed = uploadedBytes / elapsedSeconds / (1024 * 1024);
    uploadSpeed.value = speed.toFixed(2);

    const remainingBytes = uploadedFile.value!.size - uploadedBytes;
    const remainingSeconds = Math.ceil(remainingBytes / (speed * 1024 * 1024));
    const minutes = Math.floor(remainingSeconds / 60);
    const seconds = remainingSeconds % 60;
    remainingTime.value = `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;

    if (uploadedChunks.value % 10 === 0) {
      addLog("INFO", `已上传 ${uploadedChunks.value}/${totalChunks.value} 分片`);
    }

    if (uploadProgress.value >= 100) {
      clearInterval(uploadInterval);
      uploading.value = false;
      ElMessage.success("文件上传成功!");
      addLog("SUCCESS", "文件上传并验证成功");
      
      // 更新统计数据
      statistics.value.total_count++;
      statistics.value.completed_count++;
      loadDatasetList();
    }
  }, 200);
}

function pauseUpload() {
  uploadPaused.value = true;
  uploading.value = false;
  addLog("WARN", "上传已暂停");
}

function resumeUpload() {
  uploadPaused.value = false;
  uploading.value = true;
  addLog("INFO", "继续上传...");
  startUpload();
}

function cancelUpload() {
  uploadedFile.value = null;
  uploading.value = false;
  uploadPaused.value = false;
  uploadProgress.value = 0;
  uploadedChunks.value = 0;
  totalChunks.value = 0;
  datasetForm.name = "";
  datasetForm.taskType = "classification";
  datasetForm.description = "";
  uploadLogs.value = [];
  ElMessage.info("已取消上传");
}

function proceedToAnalysis() {
  const newDatasetId = Date.now(); // Mock ID
  currentDatasetId.value = newDatasetId;
  
  // 自动选中刚上传的数据集
  const newDataset = {
    id: newDatasetId,
    name: datasetForm.name,
    original_filename: uploadedFile.value?.name || '',
    modality: 'unknown',
    file_size: uploadedFile.value?.size || 0,
    task_type: datasetForm.taskType,
    upload_status: 'completed',
    created_time: new Date().toISOString(),
    description: datasetForm.description,
  };
  
  selectedDatasetId.value = newDatasetId;
  selectedDataset.value = newDataset;
  
  emit('update:modelValue', {
    datasetId: newDataset.id,
    name: newDataset.name,
    modality: newDataset.modality,
    task: newDataset.task_type,
    sampleCount: newDataset.sample_count,
    classCount: newDataset.class_count,
    fileSize: newDataset.file_size,
  });
  
  activeTab.value = "analysis";
}

function addLog(type: string, message: string) {
  const now = new Date();
  const time = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}:${now.getSeconds().toString().padStart(2, "0")}`;
  uploadLogs.value.push({ time, message, type: type.toLowerCase() });

  if (uploadLogs.value.length > 50) {
    uploadLogs.value.shift();
  }
}

// ==================== 数据集列表功能 ====================
async function loadDatasetList() {
  loading.value = true;
  
  // Mock数据
  setTimeout(() => {
    const mockData = [
      { id: 1, name: "CIFAR-10", original_filename: "cifar10.zip", modality: "image", file_size: 170000000, sample_count: 60000, class_count: 10, upload_status: "completed", created_time: "2026-01-20T10:30:00", description: "经典图像分类数据集" },
      { id: 2, name: "ImageNet-Mini", original_filename: "imagenet_mini.tar", modality: "image", file_size: 5000000000, sample_count: 120000, class_count: 100, upload_status: "completed", created_time: "2026-01-19T14:20:00", description: "ImageNet子集" },
      { id: 3, name: "ESC-50", original_filename: "esc50.zip", modality: "audio", file_size: 600000000, sample_count: 2000, class_count: 50, upload_status: "completed", created_time: "2026-01-18T09:15:00", description: "环境声音分类" },
      { id: 4, name: "AG News", original_filename: "ag_news.tar.gz", modality: "text", file_size: 30000000, sample_count: 127600, class_count: 4, upload_status: "uploading", created_time: "2026-01-17T16:45:00", description: "新闻分类数据集" },
      { id: 5, name: "ModelNet40", original_filename: "modelnet40.zip", modality: "sensor", file_size: 450000000, sample_count: 12311, class_count: 40, upload_status: "completed", created_time: "2026-01-16T11:20:00", description: "3D点云分类" },
    ];
    
    datasetList.value = mockData;
    total.value = mockData.length;
    loading.value = false;
  }, 500);
}

async function handleQuery() {
  queryFormData.page_no = 1;
  await loadDatasetList();
}

async function handleResetQuery() {
  queryFormRef.value?.resetFields();
  queryFormData.page_no = 1;
  await loadDatasetList();
}

// 选择数据集
function handleRowSelect(row: any) {
  selectedDatasetId.value = row.id;
  selectedDataset.value = row;
  emit('update:modelValue', {
    datasetId: row.id,
    name: row.name,
    modality: row.modality,
    task: row.task_type || 'classification',
    sampleCount: row.sample_count,
    classCount: row.class_count,
    fileSize: row.file_size,
  });
  ElMessage.success(`已选择数据集: ${row.name}`);
}

function handleRadioClick(row: any) {
  handleRowSelect(row);
}

function getRowClassName({ row }: { row: any }): string {
  return row.id === selectedDatasetId.value ? 'selected-row' : '';
}

function clearSelection() {
  selectedDatasetId.value = null;
  selectedDataset.value = null;
  selectedDatasetName.value = '';
  emit('update:modelValue', {
    datasetId: null,
    name: '',
    modality: '',
    task: '',
    sampleCount: 0,
    classCount: 0,
    fileSize: 0,
  });
  ElMessage.info('已取消选择');
}

// ==================== 模态类型和数据集选择方法 ====================
function selectModality(modality: string) {
  selectedModality.value = modality;
  selectedDatasetName.value = '';
  selectedDataset.value = null;
  selectedDatasetId.value = null;
}

function handleDatasetSelect(datasetName: string) {
  const dataset = filteredDatasets.value.find(d => d.name === datasetName);
  if (dataset) {
    selectedDataset.value = dataset;
    selectedDatasetId.value = dataset.id;
    emit('update:modelValue', {
      datasetId: dataset.id,
      name: dataset.name,
      modality: dataset.modality,
      task: dataset.task_type || 'classification',
      sampleCount: dataset.sample_count,
      classCount: dataset.class_count,
      fileSize: dataset.file_size,
    });
    ElMessage.success(`已选择数据集: ${dataset.name}`);
  }
}

async function handleViewDataset(row: any) {
  currentDataset.value = row;
  detailDrawerVisible.value = true;
}

function handleAnalyzeDataset(row: any) {
  currentDatasetId.value = row.id;
  activeTab.value = "analysis";
}

function handleEditDataset(row: any) {
  currentDataset.value = row;
  Object.assign(editFormData, {
    name: row.name,
    modality: row.modality,
    sample_count: row.sample_count,
    class_count: row.class_count,
    description: row.description,
  });
  editDrawerVisible.value = true;
}

async function handleDeleteDataset(row: any) {
  try {
    await ElMessageBox.confirm("确认删除该数据集？", "警告", {
      confirmButtonText: "确认",
      cancelButtonText: "取消",
      type: "warning",
    });

    ElMessage.success("数据集删除成功");
    await loadDatasetList();
    statistics.value.total_count--;
    statistics.value.completed_count--;
  } catch (error: any) {
    if (error !== "cancel") {
      ElMessage.error("删除失败");
    }
  }
}

async function handleSubmitEdit() {
  try {
    await editFormRef.value?.validate();
    ElMessage.success("更新成功");
    editDrawerVisible.value = false;
    await loadDatasetList();
  } catch (error: any) {
    if (error !== "cancel") {
      ElMessage.error("更新失败");
    }
  }
}

function handleCloseEditDrawer() {
  editDrawerVisible.value = false;
  editFormRef.value?.resetFields();
}

// ==================== 数据集分析功能 ====================
async function startAnalysis() {
  analyzing.value = true;
  analysisProgress.value = 0;

  // Mock分析过程
  const analysisInterval = setInterval(() => {
    analysisProgress.value += 10;

    if (analysisProgress.value >= 100) {
      clearInterval(analysisInterval);
      analyzing.value = false;
      analysisComplete.value = true;
      
      // Mock分析结果
      analysisData.value = {
        modality: "image",
        sample_count: 60000,
        class_count: 10,
        analysis_result: {
          status: "completed",
          analyzed_at: new Date().toISOString(),
        },
      };
      
      ElMessage.success("数据集分析完成!");
    }
  }, 300);
}

function downloadReport() {
  ElMessage.info("下载功能开发中...");
}

// ==================== 导航功能 ====================
function handleNext() {
  // 检查是否选中了数据集
  if (!selectedDatasetId.value || !selectedDataset.value) {
    ElMessage.warning("请先选择一个数据集");
    activeTab.value = "list"; // 切换到列表页面
    return;
  }
  
  // 再次确认传递数据集信息
  emit('update:modelValue', {
    datasetId: selectedDataset.value.id,
    name: selectedDataset.value.name,
    modality: selectedDataset.value.modality,
    task: selectedDataset.value.task_type || 'classification',
    sampleCount: selectedDataset.value.sample_count,
    classCount: selectedDataset.value.class_count,
    fileSize: selectedDataset.value.file_size,
  });
  
  emit("next");
}

// ==================== 初始化 ====================
onMounted(async () => {
  await loadDatasetList();
});
</script>

<style lang="scss" scoped>
.dataset-management {
  .selected-dataset-card {
    margin-bottom: 20px;
    border-radius: 12px;
    border: 2px solid var(--el-color-success);
    background: linear-gradient(135deg, rgba(103, 194, 58, 0.05) 0%, rgba(103, 194, 58, 0.02) 100%);

    .selected-dataset-content {
      display: flex;
      gap: 16px;
      align-items: center;

      .selected-icon {
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 56px;
        height: 56px;
        background: rgba(103, 194, 58, 0.1);
        border-radius: 12px;
      }

      .selected-info {
        flex: 1;
        min-width: 0;

        .selected-title {
          margin-bottom: 4px;
          font-size: 12px;
          color: var(--el-text-color-secondary);
        }

        .selected-name {
          margin-bottom: 6px;
          overflow: hidden;
          text-overflow: ellipsis;
          font-size: 18px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          white-space: nowrap;
        }

        .selected-meta {
          display: flex;
          gap: 8px;
          align-items: center;
          font-size: 13px;
          color: var(--el-text-color-regular);

          .meta-divider {
            color: var(--el-border-color);
          }
        }
      }
    }
  }

  .stats-row {
    margin-bottom: 20px;

    .stat-card {
      border-radius: 12px;
      overflow: hidden;
      transition: all 0.3s ease;

      &:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
      }

      .stat-content {
        display: flex;
        gap: 16px;
        align-items: center;

        .stat-icon {
          display: flex;
          flex-shrink: 0;
          align-items: center;
          justify-content: center;
          width: 64px;
          height: 64px;
          border-radius: 12px;
        }

        .stat-info {
          flex: 1;

          .stat-label {
            margin-bottom: 8px;
            font-size: 14px;
            color: var(--el-text-color-secondary);
          }

          .stat-value {
            font-size: 28px;
            font-weight: 700;
            color: var(--el-text-color-primary);
          }
        }
      }
    }
  }

  .main-card {
    border-radius: 16px;
    overflow: hidden;

    .dataset-tabs {
      :deep(.el-tabs__header) {
        margin: 0;
        background: var(--el-fill-color-light);
      }

      .tab-label {
        display: flex;
        gap: 6px;
        align-items: center;
      }

      .tab-content {
        padding: 24px;
        min-height: 500px;
      }
    }
  }

  .dataset-table {
    margin-top: 16px;

    :deep(.el-table__row) {
      cursor: pointer;
      transition: background-color 0.2s;

      &.selected-row {
        background-color: var(--el-color-success-light-9) !important;

        &:hover {
          background-color: var(--el-color-success-light-8) !important;
        }
      }
    }

    :deep(.el-radio) {
      .el-radio__label {
        display: none;
      }
    }
  }

  .pagination-container {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
  }

  .dataset-detail {
    .analysis-result-card {
      pre {
        margin: 0;
        overflow-x: auto;
        font-family: "Courier New", monospace;
        font-size: 13px;
        line-height: 1.6;
        color: var(--el-text-color-regular);
      }
    }
  }

  .action-buttons-footer {
    display: flex;
    justify-content: flex-end;
    margin-top: 24px;
    padding-top: 24px;
    border-top: 1px solid var(--el-border-color-lighter);
    gap: 12px;
  }
}

// 上传组件样式
.upload-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 48px 24px;
  background: linear-gradient(145deg, var(--el-bg-color) 0%, var(--el-bg-color-page) 100%);
  border: 2px dashed var(--el-border-color);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover,
  &.upload-zone-dragover {
    border-color: var(--el-color-primary);
    background: linear-gradient(145deg, rgba(64, 158, 255, 0.05) 0%, rgba(64, 158, 255, 0.02) 100%);
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(64, 158, 255, 0.15);
  }
}

.upload-icon {
  margin-bottom: 24px;
  animation: bounce 2s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.upload-text {
  text-align: center;

  .upload-title {
    margin: 0 0 12px;
    font-size: 20px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }

  .upload-hint {
    margin: 6px 0;
    font-size: 14px;
    color: var(--el-text-color-secondary);
  }
}

.upload-progress-container {
  .file-info-card {
    border-radius: 16px;
    overflow: hidden;
  }

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .file-info {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 12px;
    background: var(--el-fill-color-light);
    border-radius: 12px;

    .file-icon {
      flex-shrink: 0;
    }

    .file-details {
      flex: 1;
      min-width: 0;

      .file-name {
        margin-bottom: 4px;
        overflow: hidden;
        text-overflow: ellipsis;
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        white-space: nowrap;
      }

      .file-size {
        font-size: 14px;
        color: var(--el-text-color-secondary);
      }
    }
  }

  .progress-section {
    margin-top: 24px;

    .progress-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;

      .progress-label {
        font-size: 14px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }

      .progress-value {
        font-size: 16px;
        font-weight: 700;
        color: var(--el-color-primary);
      }
    }

    .progress-stats {
      display: flex;
      gap: 24px;
      align-items: center;
      justify-content: space-around;
      margin-top: 16px;
      padding: 12px;
      background: var(--el-fill-color-light);
      border-radius: 8px;

      .stat-item {
        display: flex;
        gap: 6px;
        align-items: center;
        font-size: 13px;
        color: var(--el-text-color-regular);

        .el-icon {
          color: var(--el-color-primary);
        }
      }
    }
  }

  .action-buttons {
    display: flex;
    gap: 12px;
    align-items: center;
    justify-content: center;
    margin-top: 24px;
  }

  .log-card {
    border-radius: 16px;
    overflow: hidden;

    .log-container {
      max-height: 300px;
      overflow-y: auto;
      font-family: "Courier New", monospace;
      font-size: 13px;
      line-height: 1.6;
      background: var(--el-fill-color-darker);
      border-radius: 8px;

      .log-item {
        display: flex;
        gap: 12px;
        padding: 8px 12px;
        border-bottom: 1px solid var(--el-border-color-lighter);

        &:last-child {
          border-bottom: none;
        }

        .log-time {
          flex-shrink: 0;
          color: var(--el-text-color-secondary);
        }

        .log-message {
          flex: 1;
          color: var(--el-text-color-regular);
        }

        &.log-info .log-message {
          color: var(--el-color-info);
        }

        &.log-success .log-message {
          color: var(--el-color-success);
        }

        &.log-warn .log-message {
          color: var(--el-color-warning);
        }

        &.log-error .log-message {
          color: var(--el-color-danger);
        }
      }
    }
  }
}

// 分析组件样式
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

// ==================== 模态类型和数据集选择器样式 ====================
.modality-selector {
  margin-bottom: 24px;

  .selector-label {
    margin-bottom: 12px;
    font-size: 14px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }

  .modality-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;

    .modality-btn {
      min-width: 100px;
      border-radius: 8px;
      transition: all 0.3s ease;

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      }
    }
  }
}

.dataset-selector {
  margin-bottom: 32px;

  .selector-label {
    margin-bottom: 12px;
    font-size: 14px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
}

.dataset-details {
  padding: 24px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
  border-radius: 12px;

  .details-title {
    margin-bottom: 20px;
    font-size: 16px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }

  .details-grid {
    display: grid;
    gap: 16px;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    margin-bottom: 24px;

    .detail-row {
      display: flex;
      align-items: center;
      padding: 12px 16px;
      background: var(--el-bg-color);
      border-radius: 8px;
      transition: all 0.2s ease;

      &:hover {
        background: var(--el-fill-color-lighter);
      }

      .detail-label {
        flex-shrink: 0;
        width: 120px;
        font-size: 14px;
        font-weight: 500;
        color: var(--el-text-color-secondary);
      }

      .detail-value {
        flex: 1;
        font-size: 14px;
        color: var(--el-text-color-primary);
        word-break: break-all;
      }
    }
  }

  .detail-actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
    padding-top: 16px;
    border-top: 1px solid var(--el-border-color-lighter);
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
        box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
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

.mt-4 {
  margin-top: 16px;
}

.mt-6 {
  margin-top: 24px;
}

.mr-2 {
  margin-right: 8px;
}

.ml-2 {
  margin-left: 8px;
}

.font-semibold {
  font-weight: 600;
}
</style>
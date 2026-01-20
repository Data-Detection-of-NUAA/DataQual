<!-- 鲁棒性评估主页面 -->
<template>
  <div class="app-container robustness-evaluation">
    <!-- 评估卡片 -->
    <el-card shadow="hover" class="evaluation-card">
      <!-- 步骤条 -->
      <el-steps :active="currentStep" align-center finish-status="success" class="steps-container">
        <el-step title="数据集选择" icon="FolderOpened" />
        <el-step title="模型选择与训练" icon="Cpu" />
        <el-step title="鲁棒性评估策略与选择" icon="Calendar" />
        <el-step title="参数配置" icon="Setting" />
        <el-step title="指标与输出" icon="DataAnalysis" />
        <el-step title="运行控制" icon="VideoPlay" />
        <el-step title="结果总览" icon="DocumentChecked" />
      </el-steps>

      <!-- 步骤内容 -->
      <div class="step-content">
        <!-- 步骤1: 数据集选择 -->
        <div v-show="currentStep === 0" class="step-panel">
          <!-- Tab切换: 上传 / 选择已有数据集 -->
          <el-tabs v-model="datasetTabType" class="dataset-tabs">
            <el-tab-pane label="上传新数据集" name="upload">
              <DatasetUpload
                v-if="datasetTabType === 'upload'"
                @upload-success="handleUploadSuccess"
              />
            </el-tab-pane>

            <el-tab-pane label="选择已有数据集" name="select">
              <el-form :model="evaluationForm" label-width="120px" label-position="right" class="evaluation-form">
                <el-form-item label="模态类型" required>
                  <el-radio-group v-model="evaluationForm.modality" @change="handleModalityChange">
                    <el-radio-button value="image">图像</el-radio-button>
                    <el-radio-button value="audio">音频</el-radio-button>
                    <el-radio-button value="video">视频</el-radio-button>
                    <el-radio-button value="text">文本</el-radio-button>
                    <el-radio-button value="sensor">传感器</el-radio-button>
                    <el-radio-button value="multimodal">多模态</el-radio-button>
                  </el-radio-group>
                </el-form-item>

                <el-form-item label="数据集选择" required>
                  <el-select
                    v-model="evaluationForm.datasetId"
                    placeholder="请选择数据集"
                    filterable
                    style="width: 100%"
                    :loading="datasetsLoading"
                    @change="handleDatasetChange"
                  >
                    <el-option
                      v-for="dataset in filteredDatasets"
                      :key="dataset.id"
                      :label="dataset.name"
                      :value="dataset.id!"
                    >
                      <div class="dataset-option">
                        <span class="dataset-name">{{ dataset.name }}</span>
                        <span class="dataset-info">
                          <el-tag :type="getModalityTagType(dataset.modality)" size="small">
                            {{ getModalityText(dataset.modality) }}
                          </el-tag>
                          <span class="dataset-size">{{ formatFileSize(dataset.file_size) }}</span>
                          <span class="dataset-samples">{{ dataset.sample_count || "未知" }}个样本</span>
                        </span>
                      </div>
                    </el-option>
                  </el-select>
                </el-form-item>

                <!-- 数据集详情预览 -->
                <el-form-item v-if="selectedDataset" label="数据集详情">
                  <div class="dataset-detail-container">
                    <el-descriptions :column="2" border size="small">
                      <el-descriptions-item label="数据集名称">
                        {{ selectedDataset.name }}
                      </el-descriptions-item>
                      <el-descriptions-item label="原始文件名">
                        {{ selectedDataset.original_filename }}
                      </el-descriptions-item>
                      <el-descriptions-item label="文件大小">
                        {{ formatFileSize(selectedDataset.file_size) }}
                      </el-descriptions-item>
                      <el-descriptions-item label="任务类型">
                        <el-select v-model="selectedDataset.task_type" placeholder="请选择任务类型" size="small" style="width: 200px">
                          <el-option label="分类" value="classification" />
                          <el-option label="目标检测" value="object_detection" />
                          <el-option label="语音识别" value="speech_recognition" />
                          <el-option label="回归" value="regression" />
                          <el-option label="生成" value="generation" />
                          <el-option label="异常检测" value="anomaly_detection" />
                          <el-option label="分割" value="segmentation" />
                          <el-option label="推荐" value="recommendation" />
                        </el-select>
                      </el-descriptions-item>
                      <el-descriptions-item label="样本数量">
                        {{ selectedDataset.sample_count || "未知" }}
                      </el-descriptions-item>
                      <el-descriptions-item label="类别数量">
                        {{ selectedDataset.class_count || "未知" }}
                      </el-descriptions-item>
                      <el-descriptions-item label="上传状态">
                        <el-tag :type="getStatusTagType(selectedDataset.upload_status)" size="small">
                          {{ getStatusText(selectedDataset.upload_status) }}
                        </el-tag>
                      </el-descriptions-item>
                    </el-descriptions>

                    <!-- 数据集操作按钮 -->
                    <div class="dataset-actions">
                      <el-button type="danger" plain size="small" @click="handleDeleteDataset">
                        <el-icon class="mr-1"><Delete /></el-icon>
                        删除数据集
                      </el-button>
                    </div>
                  </div>
                </el-form-item>
              </el-form>
            </el-tab-pane>
          </el-tabs>
        </div>

        <!-- 步骤2: 模型选择与训练 -->
        <div v-show="currentStep === 1" class="step-panel">
          <el-form :model="evaluationForm" label-width="140px" label-position="right" class="evaluation-form">
            <el-form-item label="模型选择" required>
              <el-select v-model="evaluationForm.modelType" placeholder="请选择模型" style="width: 100%">
                <el-option label="ResNet-50" value="resnet50" />
                <el-option label="VGG-16" value="vgg16" />
                <el-option label="MobileNet" value="mobilenet" />
                <el-option label="EfficientNet" value="efficientnet" />
                <el-option label="自定义模型" value="custom" />
              </el-select>
            </el-form-item>

            <el-form-item label="模型路径">
              <el-input
                v-model="evaluationForm.modelPath"
                placeholder="请输入模型文件路径或上传模型"
                maxlength="500"
              />
            </el-form-item>

            <el-form-item label="是否需要训练">
              <el-radio-group v-model="evaluationForm.needTraining">
                <el-radio :value="false">使用已训练模型</el-radio>
                <el-radio :value="true">重新训练模型</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item v-if="evaluationForm.needTraining" label="训练轮数">
              <el-input-number
                v-model="evaluationForm.trainingEpochs"
                :min="1"
                :max="200"
                :step="1"
                controls-position="right"
              />
            </el-form-item>

            <el-form-item v-if="evaluationForm.needTraining" label="学习率">
              <el-input-number
                v-model="evaluationForm.learningRate"
                :min="0.0001"
                :max="0.1"
                :step="0.0001"
                :precision="4"
                controls-position="right"
              />
            </el-form-item>
          </el-form>
        </div>

        <!-- 步骤3: 鲁棒性评估策略与选择 -->
        <div v-show="currentStep === 2" class="step-panel">
          <el-form :model="evaluationForm" label-width="140px" label-position="right" class="evaluation-form">
            <el-form-item label="攻击方法" required>
              <el-checkbox-group v-model="evaluationForm.attackMethods">
                <el-checkbox value="fgsm">FGSM (快速梯度符号攻击)</el-checkbox>
                <el-checkbox value="pgd">PGD (投影梯度下降)</el-checkbox>
                <el-checkbox value="deepfool">DeepFool</el-checkbox>
                <el-checkbox value="cw">C&W (Carlini & Wagner)</el-checkbox>
                <el-checkbox value="noise">高斯噪声</el-checkbox>
                <el-checkbox value="blur">模糊</el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <el-form-item label="扰动强度">
              <el-slider
                v-model="evaluationForm.perturbationStrength"
                :min="0"
                :max="100"
                :step="5"
                show-stops
                show-input
              />
            </el-form-item>

            <el-form-item label="评估策略">
              <el-radio-group v-model="evaluationForm.evaluationStrategy">
                <el-radio value="full">完整评估</el-radio>
                <el-radio value="sample">采样评估</el-radio>
                <el-radio value="adaptive">自适应评估</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-form>
        </div>

        <!-- 步骤4: 参数配置 -->
        <div v-show="currentStep === 3" class="step-panel">
          <el-form :model="evaluationForm" label-width="140px" label-position="right" class="evaluation-form">
            <el-form-item label="评估名称" required>
              <el-input
                v-model="evaluationForm.evaluationName"
                placeholder="请输入评估任务名称"
                maxlength="100"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="批次大小">
              <el-input-number
                v-model="evaluationForm.batchSize"
                :min="1"
                :max="128"
                :step="1"
                controls-position="right"
              />
            </el-form-item>

            <el-form-item label="并行线程数">
              <el-input-number
                v-model="evaluationForm.numWorkers"
                :min="1"
                :max="16"
                :step="1"
                controls-position="right"
              />
            </el-form-item>

            <el-form-item label="GPU设备">
              <el-select v-model="evaluationForm.gpuDevice" placeholder="请选择GPU设备" style="width: 100%">
                <el-option label="CPU" value="cpu" />
                <el-option label="GPU 0" value="cuda:0" />
                <el-option label="GPU 1" value="cuda:1" />
                <el-option label="自动选择" value="auto" />
              </el-select>
            </el-form-item>

            <el-form-item label="评估描述">
              <el-input
                v-model="evaluationForm.description"
                type="textarea"
                :rows="4"
                placeholder="请输入评估任务描述"
                maxlength="500"
                show-word-limit
              />
            </el-form-item>
          </el-form>
        </div>

        <!-- 步骤5: 指标与输出 -->
        <div v-show="currentStep === 4" class="step-panel">
          <el-form :model="evaluationForm" label-width="140px" label-position="right" class="evaluation-form">
            <el-form-item label="评估指标" required>
              <el-checkbox-group v-model="evaluationForm.metrics">
                <el-checkbox value="accuracy">准确率</el-checkbox>
                <el-checkbox value="precision">精确率</el-checkbox>
                <el-checkbox value="recall">召回率</el-checkbox>
                <el-checkbox value="f1">F1分数</el-checkbox>
                <el-checkbox value="robustness_score">鲁棒性得分</el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <el-form-item label="输出格式">
              <el-checkbox-group v-model="evaluationForm.outputFormats">
                <el-checkbox value="json">JSON</el-checkbox>
                <el-checkbox value="csv">CSV</el-checkbox>
                <el-checkbox value="pdf">PDF报告</el-checkbox>
                <el-checkbox value="html">HTML报告</el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <el-form-item label="保存路径">
              <el-input
                v-model="evaluationForm.savePath"
                placeholder="请输入结果保存路径"
                maxlength="500"
              />
            </el-form-item>

            <el-form-item label="生成可视化">
              <el-switch v-model="evaluationForm.generateVisuals" />
            </el-form-item>
          </el-form>
        </div>

        <!-- 步骤6: 运行控制 -->
        <div v-show="currentStep === 5" class="step-panel">
          <div class="confirm-panel">
            <div class="confirm-header">
              <el-icon :size="64" color="#409eff">
                <InfoFilled />
              </el-icon>
              <h3>确认评估信息</h3>
            </div>

            <el-descriptions :column="2" border>
              <el-descriptions-item label="评估名称">
                {{ evaluationForm.evaluationName }}
              </el-descriptions-item>
              <el-descriptions-item label="数据集">
                {{ selectedDataset?.name }}
              </el-descriptions-item>
              <el-descriptions-item label="模型类型">
                {{ evaluationForm.modelType }}
              </el-descriptions-item>
              <el-descriptions-item label="样本数量">
                {{ selectedDataset?.sample_count || "未知" }}
              </el-descriptions-item>
              <el-descriptions-item label="攻击方法">
                <el-tag
                  v-for="method in evaluationForm.attackMethods"
                  :key="method"
                  type="info"
                  size="small"
                  style="margin-right: 4px"
                >
                  {{ getAttackMethodText(method) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="评估指标">
                <el-tag
                  v-for="metric in evaluationForm.metrics"
                  :key="metric"
                  type="success"
                  size="small"
                  style="margin-right: 4px"
                >
                  {{ getMetricText(metric) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="扰动强度">
                {{ evaluationForm.perturbationStrength }}%
              </el-descriptions-item>
              <el-descriptions-item label="批次大小">
                {{ evaluationForm.batchSize }}
              </el-descriptions-item>
            </el-descriptions>

            <div class="start-button-container">
              <el-button
                type="primary"
                size="large"
                :loading="evaluating"
                :disabled="evaluating"
                @click="startEvaluation"
              >
                <el-icon v-if="!evaluating" class="mr-2"><VideoPlay /></el-icon>
                {{ evaluating ? "评估进行中..." : "开始评估" }}
              </el-button>
            </div>
          </div>
        </div>

        <!-- 步骤7: 结果总览 -->
        <div v-show="currentStep === 6" class="step-panel">
          <!-- 评估进行中 -->
          <div v-if="evaluating" class="evaluating-panel">
            <div class="evaluating-animation">
              <el-icon :size="80" class="rotating-icon" color="#409eff">
                <Loading />
              </el-icon>
            </div>
            <h3 class="evaluating-text">评估进行中...</h3>
            <p class="evaluating-hint">正在对数据集进行鲁棒性测试，请耐心等待</p>
            <el-progress
              :percentage="evaluationProgress"
              :stroke-width="16"
              :striped="true"
              :striped-flow="true"
              status="success"
              class="progress-bar"
            />
            <p class="progress-text">已完成: {{ evaluationProgress }}%</p>
          </div>

          <!-- 评估完成 -->
          <div v-else-if="evaluationComplete && evaluationResult" class="result-panel">
            <div class="result-header">
              <el-icon :size="64" color="#67c23a">
                <CircleCheck />
              </el-icon>
              <h3>评估完成</h3>
            </div>

            <!-- 评估概览 -->
            <el-row :gutter="20" class="result-stats">
              <el-col :span="6">
                <div class="stat-card">
                  <div class="stat-icon" style="background: #e1f5fe">
                    <el-icon :size="32" color="#0288d1">
                      <Document />
                    </el-icon>
                  </div>
                  <div class="stat-content">
                    <div class="stat-label">总样本数</div>
                    <div class="stat-value">{{ evaluationResult.totalSamples }}</div>
                  </div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="stat-card">
                  <div class="stat-icon" style="background: #e8f5e9">
                    <el-icon :size="32" color="#388e3c">
                      <SuccessFilled />
                    </el-icon>
                  </div>
                  <div class="stat-content">
                    <div class="stat-label">鲁棒样本</div>
                    <div class="stat-value">{{ evaluationResult.robustSamples }}</div>
                  </div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="stat-card">
                  <div class="stat-icon" style="background: #fff3e0">
                    <el-icon :size="32" color="#f57c00">
                      <WarningFilled />
                    </el-icon>
                  </div>
                  <div class="stat-content">
                    <div class="stat-label">脆弱样本</div>
                    <div class="stat-value">{{ evaluationResult.vulnerableSamples }}</div>
                  </div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="stat-card">
                  <div class="stat-icon" style="background: #f3e5f5">
                    <el-icon :size="32" color="#7b1fa2">
                      <TrophyBase />
                    </el-icon>
                  </div>
                  <div class="stat-content">
                    <div class="stat-label">鲁棒性得分</div>
                    <div class="stat-value">{{ evaluationResult.robustnessScore }}%</div>
                  </div>
                </div>
              </el-col>
            </el-row>

            <!-- 详细结果 -->
            <el-card shadow="never" class="result-details">
              <template #header>
                <span class="font-semibold">详细评估结果</span>
              </template>

              <el-descriptions :column="2" border>
                <el-descriptions-item label="评估名称">
                  {{ evaluationForm.evaluationName }}
                </el-descriptions-item>
                <el-descriptions-item label="数据集">
                  {{ selectedDataset?.name }}
                </el-descriptions-item>
                <el-descriptions-item label="准确率">
                  {{ evaluationResult.metrics.accuracy }}%
                </el-descriptions-item>
                <el-descriptions-item label="精确率">
                  {{ evaluationResult.metrics.precision }}%
                </el-descriptions-item>
                <el-descriptions-item label="召回率">
                  {{ evaluationResult.metrics.recall }}%
                </el-descriptions-item>
                <el-descriptions-item label="F1分数">
                  {{ evaluationResult.metrics.f1 }}%
                </el-descriptions-item>
                <el-descriptions-item label="评估时长">
                  {{ evaluationResult.duration }}秒
                </el-descriptions-item>
                <el-descriptions-item label="完成时间">
                  {{ formatDateTime(evaluationResult.completedAt) }}
                </el-descriptions-item>
              </el-descriptions>
            </el-card>

            <!-- 操作按钮 -->
            <div class="result-actions">
              <el-button type="primary" @click="downloadReport">
                <el-icon class="mr-2"><Download /></el-icon>
                下载报告
              </el-button>
              <el-button type="success" @click="viewDetailedResults">
                <el-icon class="mr-2"><View /></el-icon>
                查看详细结果
              </el-button>
              <el-button @click="resetEvaluation">
                <el-icon class="mr-2"><RefreshRight /></el-icon>
                重新评估
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部操作按钮 -->
      <div class="step-actions">
        <el-button v-if="currentStep > 0 && currentStep < 6" @click="previousStep">
          <el-icon class="mr-2"><ArrowLeft /></el-icon>
          上一步
        </el-button>
        <el-button
          v-if="currentStep < 5"
          type="primary"
          :disabled="!canProceed"
          @click="nextStep"
        >
          下一步
          <el-icon class="ml-2"><ArrowRight /></el-icon>
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from "vue";
import {
  FolderOpened,
  Cpu,
  Calendar,
  Setting,
  DataAnalysis,
  VideoPlay,
  DocumentChecked,
  InfoFilled,
  Loading,
  CircleCheck,
  Document,
  SuccessFilled,
  WarningFilled,
  TrophyBase,
  Download,
  View,
  RefreshRight,
  ArrowLeft,
  ArrowRight,
  Delete,
} from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { formatToDateTime } from "@/utils/dateUtil";
import DatasetAPI, { type DatasetInfo } from "@/api/module_dataset/dataset";
import DatasetUpload from "@/views/module_dataset/dataset/components/DatasetUpload.vue";

defineOptions({
  name: "RobustnessEvaluation",
  inheritAttrs: false,
});

// 当前步骤
const currentStep = ref(0);

// 数据集Tab类型: select-选择已有 / upload-上传新的
const datasetTabType = ref("upload");

// 数据集列表
const datasets = ref<DatasetInfo[]>([]);
const datasetsLoading = ref(false);
const selectedDataset = ref<DatasetInfo | null>(null);

// 评估表单
const evaluationForm = reactive({
  modality: "image",
  datasetId: null as number | null,
  evaluationName: "",
  // 步骤2: 模型相关
  modelType: "resnet50",
  modelPath: "",
  needTraining: false,
  trainingEpochs: 10,
  learningRate: 0.001,
  // 步骤3: 鲁棒性评估策略
  attackMethods: [] as string[],
  perturbationStrength: 50,
  evaluationStrategy: "full",
  // 步骤4: 参数配置
  batchSize: 32,
  numWorkers: 4,
  gpuDevice: "auto",
  description: "",
  // 步骤5: 指标与输出
  metrics: ["accuracy", "robustness_score"] as string[],
  outputFormats: ["json", "pdf"] as string[],
  savePath: "",
  generateVisuals: true,
});

// 评估状态
const evaluating = ref(false);
const evaluationComplete = ref(false);
const evaluationProgress = ref(0);
const evaluationResult = ref<any>(null);

// 筛选后的数据集
const filteredDatasets = computed(() => {
  if (!evaluationForm.modality) return datasets.value;
  return datasets.value.filter((d) => d.modality === evaluationForm.modality);
});

// 是否可以进入下一步
const canProceed = computed(() => {
  // 步骤0: 数据集选择
  if (currentStep.value === 0) {
    return evaluationForm.datasetId !== null && evaluationForm.modality !== "";
  }
  // 步骤1: 模型选择与训练
  if (currentStep.value === 1) {
    return evaluationForm.modelType !== "";
  }
  // 步骤2: 鲁棒性评估策略
  if (currentStep.value === 2) {
    return evaluationForm.attackMethods.length > 0;
  }
  // 步骤3: 参数配置
  if (currentStep.value === 3) {
    return evaluationForm.evaluationName.trim() !== "";
  }
  // 步骤4: 指标与输出
  if (currentStep.value === 4) {
    return evaluationForm.metrics.length > 0;
  }
  return true;
});

// 模态类型映射
const modalityMap: Record<string, string> = {
  image: "图像",
  audio: "音频",
  video: "视频",
  text: "文本",
  sensor: "传感器",
  multimodal: "多模态",
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

// 状态映射
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

// 攻击方法文本
function getAttackMethodText(method: string): string {
  const methodMap: Record<string, string> = {
    fgsm: "FGSM",
    pgd: "PGD",
    deepfool: "DeepFool",
    cw: "C&W",
    noise: "高斯噪声",
    blur: "模糊",
  };
  return methodMap[method] || method;
}

// 指标文本
function getMetricText(metric: string): string {
  const metricMap: Record<string, string> = {
    accuracy: "准确率",
    precision: "精确率",
    recall: "召回率",
    f1: "F1分数",
    robustness_score: "鲁棒性得分",
  };
  return metricMap[metric] || metric;
}

// 格式化文件大小
function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

// 格式化日期时间
function formatDateTime(dateStr: string | undefined): string {
  if (!dateStr) return "-";
  try {
    return formatToDateTime(dateStr, "YYYY-MM-DD HH:mm:ss");
  } catch {
    return dateStr;
  }
}

// 加载数据集列表
async function loadDatasets() {
  datasetsLoading.value = true;
  try {
    const response = await DatasetAPI.getList({
      page_no: 1,
      page_size: 100,  // 修改为100,符合后端限制
      upload_status: "completed",
    });
    datasets.value = response.data.data.items;
  } catch (error: any) {
    ElMessage.error("加载数据集列表失败: " + (error.message || "未知错误"));
  } finally {
    datasetsLoading.value = false;
  }
}

// 模态类型改变
function handleModalityChange() {
  evaluationForm.datasetId = null;
  selectedDataset.value = null;
}

// 数据集改变
async function handleDatasetChange(datasetId: number) {
  try {
    const response = await DatasetAPI.getDetail(datasetId);
    selectedDataset.value = response.data.data;
  } catch (error: any) {
    ElMessage.error("加载数据集详情失败: " + (error.message || "未知错误"));
  }
}

// 上传成功回调
async function handleUploadSuccess(datasetId?: number | string) {
  ElMessage.success("数据集上传成功!");
  // 刷新数据集列表
  await loadDatasets();

  // 如果返回了datasetId,自动选择该数据集并触发分析
  if (datasetId) {
    const id = typeof datasetId === 'string' ? parseInt(datasetId) : datasetId;
    // 切换到选择Tab
    datasetTabType.value = "select";
    evaluationForm.datasetId = id;
    // 从刷新后的列表中找到该数据集
    const dataset = datasets.value.find(d => d.id === id);
    if (dataset) {
      evaluationForm.modality = dataset.modality;
      selectedDataset.value = dataset;

      // 自动触发数据集分析
      try {
        ElMessage.info("正在分析数据集,请稍候...");
        await DatasetAPI.analyze(id);

        // 等待分析完成(轮询查询状态)
        let retries = 0;
        const maxRetries = 30; // 最多30次,每次2秒
        const pollInterval = setInterval(async () => {
          try {
            const statusResponse = await DatasetAPI.getAnalyzeStatus(id);
            const status = statusResponse.data.data?.status;

            if (status === 'completed') {
              clearInterval(pollInterval);
              ElMessage.success("数据集分析完成!");
              // 重新加载数据集详情以获取分析结果
              const detailResponse = await DatasetAPI.getDetail(id);
              selectedDataset.value = detailResponse.data.data;
              // 更新模态类型到表单
              if (selectedDataset.value?.modality) {
                evaluationForm.modality = selectedDataset.value.modality;
              }
            } else if (status === 'failed') {
              clearInterval(pollInterval);
              ElMessage.error("数据集分析失败");
            }

            retries++;
            if (retries >= maxRetries) {
              clearInterval(pollInterval);
              ElMessage.warning("分析超时,请稍后手动刷新");
            }
          } catch (error: any) {
            clearInterval(pollInterval);
            console.error("查询分析状态失败:", error);
          }
        }, 2000); // 每2秒查询一次

      } catch (error: any) {
        ElMessage.error("启动分析失败: " + (error.message || "未知错误"));
      }
    }
  }
}

// 删除数据集
async function handleDeleteDataset() {
  if (!selectedDataset.value) return;

  try {
    await ElMessageBox.confirm(
      `确定要删除数据集"${selectedDataset.value.name}"吗？此操作将同时删除数据库记录和存储文件,不可恢复!`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      }
    );

    await DatasetAPI.delete([selectedDataset.value.id!], true);
    ElMessage.success('数据集删除成功!');

    // 清除选择状态
    selectedDataset.value = null;
    evaluationForm.datasetId = null;

    // 刷新数据集列表
    await loadDatasets();
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.message || '未知错误'));
    }
  }
}

// 下一步
function nextStep() {
  if (!canProceed.value) {
    ElMessage.warning("请完成当前步骤的必填项");
    return;
  }
  currentStep.value++;
}

// 上一步
function previousStep() {
  currentStep.value--;
}

// 开始评估
async function startEvaluation() {
  evaluating.value = true;
  evaluationProgress.value = 0;
  currentStep.value = 6; // 跳转到步骤7: 结果总览

  // 模拟评估进度
  const progressInterval = setInterval(() => {
    if (evaluationProgress.value < 95) {
      evaluationProgress.value += 5;
    }
  }, 500);

  // 模拟评估过程
  setTimeout(() => {
    clearInterval(progressInterval);
    evaluationProgress.value = 100;

    // 模拟评估结果
    evaluationResult.value = {
      totalSamples: selectedDataset.value?.sample_count || 1000,
      robustSamples: 750,
      vulnerableSamples: 250,
      robustnessScore: 75,
      metrics: {
        accuracy: 92.5,
        precision: 90.3,
        recall: 88.7,
        f1: 89.5,
      },
      duration: 120,
      completedAt: new Date().toISOString(),
    };

    evaluating.value = false;
    evaluationComplete.value = true;
    ElMessage.success("评估完成!");
  }, 5000);
}

// 下载报告
function downloadReport() {
  ElMessage.info("下载功能开发中...");
}

// 查看详细结果
function viewDetailedResults() {
  ElMessage.info("详细结果页面开发中...");
}

// 重置评估
function resetEvaluation() {
  currentStep.value = 0;
  evaluating.value = false;
  evaluationComplete.value = false;
  evaluationProgress.value = 0;
  evaluationResult.value = null;
  Object.assign(evaluationForm, {
    modality: "image",
    datasetId: null,
    evaluationName: "",
    attackMethods: [],
    perturbationStrength: 50,
    metrics: ["accuracy", "robustness_score"],
    batchSize: 32,
    description: "",
  });
  selectedDataset.value = null;
}

// 初始化
onMounted(async () => {
  await loadDatasets();
});
</script>


<style lang="scss" scoped>
.robustness-evaluation {
  .evaluation-card {
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    transition: box-shadow 0.3s ease;

    &:hover {
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    }

    .steps-container {
      margin-bottom: 40px;
      padding: 32px 24px;
      background: linear-gradient(to right, #f8f9fa 0%, #e9ecef 100%);
    }

    .step-content {
      min-height: 400px;
      padding: 0 24px 24px;

      .step-panel {
        .dataset-tabs {
          margin-bottom: 24px;

          :deep(.el-tabs__header) {
            margin-bottom: 24px;
          }

          :deep(.el-tabs__item) {
            font-size: 15px;
            font-weight: 500;
          }

          :deep(.el-tabs__item.is-active) {
            color: #667eea;
          }
        }

        .dataset-detail-container {
          display: flex;
          flex-direction: column;
          gap: 16px;

          .dataset-actions {
            display: flex;
            justify-content: flex-end;
            padding-top: 8px;
            border-top: 1px solid #e9ecef;
          }
        }

        .evaluation-form {
          max-width: 800px;
          margin: 0 auto;

          .dataset-option {
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
            padding: 4px 0;

            .dataset-name {
              flex: 1;
              font-weight: 500;
              color: var(--el-text-color-primary);
            }

            .dataset-info {
              display: flex;
              gap: 12px;
              align-items: center;
              font-size: 12px;
              color: var(--el-text-color-secondary);

              .dataset-size,
              .dataset-samples {
                padding: 2px 8px;
                background: #f5f5f5;
                border-radius: 4px;
              }
            }
          }

          :deep(.el-descriptions) {
            border-radius: 8px;
            overflow: hidden;
          }
        }

        .confirm-panel {
          max-width: 800px;
          margin: 0 auto;

          .confirm-header {
            display: flex;
            flex-direction: column;
            gap: 16px;
            align-items: center;
            margin-bottom: 32px;

            h3 {
              margin: 0;
              font-size: 24px;
              font-weight: 600;
              color: var(--el-text-color-primary);
            }
          }

          .start-button-container {
            display: flex;
            justify-content: center;
            margin-top: 32px;
          }
        }

        .evaluating-panel {
          max-width: 600px;
          margin: 0 auto;
          padding: 48px 32px;
          text-align: center;

          .evaluating-animation {
            margin-bottom: 24px;

            .rotating-icon {
              animation: rotate 2s linear infinite;
            }
          }

          .evaluating-text {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 12px;
            color: var(--el-text-color-primary);
          }

          .evaluating-hint {
            color: var(--el-text-color-secondary);
            margin-bottom: 32px;
          }

          .progress-bar {
            margin-bottom: 16px;
          }

          .progress-text {
            font-size: 14px;
            color: var(--el-text-color-secondary);
          }
        }

        .result-panel {
          .result-header {
            display: flex;
            flex-direction: column;
            gap: 16px;
            align-items: center;
            margin-bottom: 32px;

            h3 {
              margin: 0;
              font-size: 28px;
              font-weight: 600;
              color: var(--el-color-success);
            }
          }

          .result-stats {
            margin-bottom: 32px;

            .stat-card {
              display: flex;
              gap: 16px;
              align-items: center;
              padding: 20px;
              background: var(--el-bg-color);
              border: 1px solid var(--el-border-color);
              border-radius: 12px;
              transition: all 0.3s ease;

              &:hover {
                border-color: var(--el-color-primary);
                box-shadow: 0 4px 12px rgba(var(--el-color-primary-rgb), 0.15);
                transform: translateY(-2px);
              }

              .stat-icon {
                display: flex;
                flex-shrink: 0;
                align-items: center;
                justify-content: center;
                width: 56px;
                height: 56px;
                border-radius: 12px;
              }

              .stat-content {
                flex: 1;

                .stat-label {
                  margin-bottom: 6px;
                  font-size: 13px;
                  color: var(--el-text-color-secondary);
                }

                .stat-value {
                  font-size: 24px;
                  font-weight: 700;
                  color: var(--el-text-color-primary);
                }
              }
            }
          }

          .result-details {
            margin-bottom: 24px;
          }

          .result-actions {
            display: flex;
            gap: 12px;
            justify-content: center;
          }
        }
      }
    }

    .step-actions {
      display: flex;
      gap: 16px;
      justify-content: center;
      padding: 32px 24px;
      background: linear-gradient(to top, #f8f9fa 0%, white 100%);
      border-top: 1px solid #e9ecef;

      .el-button {
        min-width: 120px;
        height: 40px;
        font-size: 15px;
        font-weight: 500;
        border-radius: 8px;
        transition: all 0.3s ease;

        &.el-button--primary {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border: none;

          &:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
          }
        }

        &:not(.el-button--primary) {
          &:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          }
        }
      }
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

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
}
</style>

<!-- 创建训练任务页面 -->
<template>
  <div class="app-container train-create">
    <el-card shadow="hover">
      <!-- 步骤条 -->
      <el-steps :active="currentStep" align-center finish-status="success" class="steps-container">
        <el-step title="数据集选择" icon="FolderOpened" />
        <el-step title="模型选择" icon="Cpu" />
        <el-step title="训练配置" icon="Setting" />
        <el-step title="确认创建" icon="Check" />
      </el-steps>

      <!-- 步骤内容 -->
      <div class="step-content">
        <!-- 步骤1: 数据集选择 -->
        <div v-show="currentStep === 0" class="step-panel">
          <el-form :model="form" label-width="120px">
            <el-form-item label="模态类型" required>
              <el-radio-group v-model="form.modality" @change="handleModalityChange">
                <el-radio-button value="image">图像</el-radio-button>
                <el-radio-button value="audio">音频</el-radio-button>
                <el-radio-button value="video">视频</el-radio-button>
                <el-radio-button value="text">文本</el-radio-button>
                <el-radio-button value="sensor">传感器</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="数据集选择" required>
              <el-select
                v-model="form.dataset_id"
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
                      <el-tag size="small">{{ dataset.modality }}</el-tag>
                      <span>{{ dataset.sample_count || 0 }}个样本</span>
                    </span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>

            <!-- 数据集详情 -->
            <el-form-item v-if="selectedDataset" label="数据集详情">
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="数据集名称">
                  {{ selectedDataset.name }}
                </el-descriptions-item>
                <el-descriptions-item label="文件大小">
                  {{ formatFileSize(selectedDataset.file_size) }}
                </el-descriptions-item>
                <el-descriptions-item label="样本数量">
                  {{ selectedDataset.sample_count || 0 }}
                </el-descriptions-item>
                <el-descriptions-item label="类别数量">
                  {{ selectedDataset.class_count || 0 }}
                </el-descriptions-item>
              </el-descriptions>
            </el-form-item>
          </el-form>
        </div>

        <!-- 步骤2: 模型选择 -->
        <div v-show="currentStep === 1" class="step-panel">
          <ModelRecommendation
            v-if="form.dataset_id"
            ref="modelRecommendationRef"
            :dataset-id="form.dataset_id"
            :modality="selectedDataset?.modality"
            :task-type="selectedDataset?.task_type"
            :top-k="5"
            @select="handleModelSelect"
          />
          <el-empty v-else description="请先在步骤1中选择数据集">
            <el-button type="primary" @click="currentStep = 0">返回选择数据集</el-button>
          </el-empty>
        </div>

        <!-- 步骤3: 训练配置 -->
        <div v-show="currentStep === 2" class="step-panel">
          <el-form :model="form" label-width="140px" class="train-config-form">
            <el-alert
              type="info"
              :closable="false"
              show-icon
              style="margin-bottom: 20px"
            >
              以下参数已自动填充为推荐配置，您可以根据需要调整
            </el-alert>

            <el-form-item label="训练轮数" required>
              <el-input-number
                v-model="form.train_config.epochs"
                :min="1"
                :max="500"
                controls-position="right"
                style="width: 160px"
              />
            </el-form-item>

            <el-form-item label="批次大小" required>
              <el-input-number
                v-model="form.train_config.batch_size"
                :min="1"
                :max="256"
                controls-position="right"
                style="width: 160px"
              />
            </el-form-item>

            <el-form-item label="学习率" required>
              <el-input-number
                v-model="form.train_config.learning_rate"
                :min="0.00001"
                :max="1"
                :step="0.0001"
                :precision="5"
                controls-position="right"
                style="width: 160px"
              />
            </el-form-item>

            <el-form-item label="优化器" required>
              <el-select v-model="form.train_config.optimizer" style="width: 200px">
                <el-option label="Adam" value="Adam" />
                <el-option label="SGD" value="SGD" />
                <el-option label="AdamW" value="AdamW" />
                <el-option label="RMSprop" value="RMSprop" />
              </el-select>
            </el-form-item>

            <el-form-item label="损失函数" required>
              <el-select v-model="form.train_config.loss_function" style="width: 250px">
                <el-option label="交叉熵损失 (CrossEntropyLoss)" value="CrossEntropyLoss" />
                <el-option label="均方误差 (MSELoss)" value="MSELoss" />
                <el-option label="二元交叉熵 (BCELoss)" value="BCELoss" />
                <el-option label="Focal Loss" value="FocalLoss" />
              </el-select>
            </el-form-item>

            <el-form-item label="学习率调度器">
              <el-select v-model="form.train_config.scheduler" clearable style="width: 250px">
                <el-option label="StepLR (按步衰减)" value="StepLR" />
                <el-option label="CosineAnnealingLR (余弦退火)" value="CosineAnnealingLR" />
                <el-option label="ReduceLROnPlateau (自适应)" value="ReduceLROnPlateau" />
              </el-select>
            </el-form-item>

            <el-form-item label="权重衰减">
              <el-input-number
                v-model="form.train_config.weight_decay"
                :min="0"
                :max="0.01"
                :step="0.00001"
                :precision="5"
                controls-position="right"
                style="width: 160px"
              />
            </el-form-item>

            <el-form-item label="设备选择">
              <el-select v-model="form.train_config.device" style="width: 200px">
                <el-option label="自动选择" value="auto" />
                <el-option label="CPU" value="cpu" />
                <el-option label="GPU 0" value="cuda:0" />
                <el-option label="GPU 1" value="cuda:1" />
              </el-select>
            </el-form-item>

            <el-form-item label="任务描述">
              <el-input
                v-model="form.description"
                type="textarea"
                :rows="3"
                placeholder="请输入训练任务描述（可选）"
                maxlength="500"
                show-word-limit
              />
            </el-form-item>
          </el-form>
        </div>

        <!-- 步骤4: 确认创建 -->
        <div v-show="currentStep === 3" class="step-panel">
          <div class="confirm-panel">
            <div class="confirm-header">
              <el-icon :size="64" color="#409eff">
                <InfoFilled />
              </el-icon>
              <h3>确认训练信息</h3>
            </div>

            <el-descriptions :column="2" border>
              <el-descriptions-item label="数据集">
                {{ selectedDataset?.name }}
              </el-descriptions-item>
              <el-descriptions-item label="模型">
                {{ selectedModel?.display_name }}
              </el-descriptions-item>
              <el-descriptions-item label="训练轮数">
                {{ form.train_config.epochs }}
              </el-descriptions-item>
              <el-descriptions-item label="批次大小">
                {{ form.train_config.batch_size }}
              </el-descriptions-item>
              <el-descriptions-item label="学习率">
                {{ form.train_config.learning_rate }}
              </el-descriptions-item>
              <el-descriptions-item label="优化器">
                {{ form.train_config.optimizer }}
              </el-descriptions-item>
              <el-descriptions-item label="损失函数">
                {{ form.train_config.loss_function }}
              </el-descriptions-item>
              <el-descriptions-item label="设备">
                {{ form.train_config.device }}
              </el-descriptions-item>
            </el-descriptions>

            <div class="create-button-container">
              <el-button
                type="primary"
                size="large"
                :loading="creating"
                @click="handleCreate"
              >
                <el-icon v-if="!creating"><Check /></el-icon>
                {{ creating ? '创建中...' : '创建训练任务' }}
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部操作按钮 -->
      <div class="step-actions">
        <el-button v-if="currentStep > 0" @click="previousStep">
          <el-icon><ArrowLeft /></el-icon>
          上一步
        </el-button>
        <el-button
          v-if="currentStep < 3"
          type="primary"
          :disabled="!canProceed"
          @click="nextStep"
        >
          下一步
          <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import {
  FolderOpened,
  Cpu,
  Setting,
  Check,
  InfoFilled,
  ArrowLeft,
  ArrowRight,
} from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import DatasetAPI, { type DatasetInfo } from '@/api/module_application/dataset';
import { TrainTaskAPI, type ModelRecommendationItem } from '@/api/module_application/train';
import ModelRecommendation from './components/ModelRecommendation.vue';

defineOptions({
  name: 'TrainCreate',
  inheritAttrs: false,
});

const router = useRouter();

// 当前步骤
const currentStep = ref(0);

// 数据集
const datasets = ref<DatasetInfo[]>([]);
const datasetsLoading = ref(false);
const selectedDataset = ref<DatasetInfo | null>(null);

// 模型
const modelRecommendationRef = ref<InstanceType<typeof ModelRecommendation>>();
const selectedModel = ref<ModelRecommendationItem | null>(null);

// 表单
const form = reactive({
  modality: 'image',
  dataset_id: null as number | null,
  model_config_id: null as number | null,
  description: '',
  train_config: {
    epochs: 10,
    batch_size: 32,
    learning_rate: 0.001,
    optimizer: 'Adam',
    loss_function: 'CrossEntropyLoss',
    scheduler: 'StepLR',
    weight_decay: 0.0001,
    device: 'auto',
  },
});

// 创建状态
const creating = ref(false);

// 筛选后的数据集
const filteredDatasets = computed(() => {
  if (!form.modality) return datasets.value;
  return datasets.value.filter((d) => d.modality === form.modality);
});

// 是否可以进入下一步
const canProceed = computed(() => {
  if (currentStep.value === 0) {
    return form.dataset_id !== null;
  }
  if (currentStep.value === 1) {
    return form.model_config_id !== null;
  }
  if (currentStep.value === 2) {
    return true;
  }
  return true;
});

// 加载数据集列表
async function loadDatasets() {
  datasetsLoading.value = true;
  try {
    const response = await DatasetAPI.getList({
      page_no: 1,
      page_size: 100,
      upload_status: 'completed',
    });
    datasets.value = response.data.data.items;
  } catch (error: any) {
    ElMessage.error('加载数据集列表失败: ' + (error.message || '未知错误'));
  } finally {
    datasetsLoading.value = false;
  }
}

// 模态类型改变
function handleModalityChange() {
  form.dataset_id = null;
  selectedDataset.value = null;
}

// 数据集改变
async function handleDatasetChange(datasetId: number) {
  try {
    const response = await DatasetAPI.getDetail(datasetId);
    selectedDataset.value = response.data.data;
  } catch (error: any) {
    ElMessage.error('加载数据集详情失败: ' + (error.message || '未知错误'));
  }
}

// 模型选择回调
function handleModelSelect(modelId: number, modelInfo: ModelRecommendationItem) {
  selectedModel.value = modelInfo;
  form.model_config_id = modelId;

  // 自动填充训练配置
  if (modelInfo.default_config_preview) {
    const config = modelInfo.default_config_preview;
    if (config.epochs) form.train_config.epochs = config.epochs;
    if (config.batch_size) form.train_config.batch_size = config.batch_size;
    if (config.learning_rate) form.train_config.learning_rate = config.learning_rate;
    if (config.optimizer) form.train_config.optimizer = config.optimizer;
    if (config.loss_function) form.train_config.loss_function = config.loss_function;
    if (config.scheduler) form.train_config.scheduler = config.scheduler;
    if (config.weight_decay !== undefined) form.train_config.weight_decay = config.weight_decay;
  }

  ElMessage.success(`已选择模型: ${modelInfo.display_name}`);
}

// 下一步
function nextStep() {
  if (!canProceed.value) {
    ElMessage.warning('请完成当前步骤的必填项');
    return;
  }
  currentStep.value++;
}

// 上一步
function previousStep() {
  currentStep.value--;
}

// 创建训练任务
async function handleCreate() {
  if (!form.dataset_id || !form.model_config_id) {
    ElMessage.warning('请完成所有必填项');
    return;
  }

  creating.value = true;
  try {
    const response = await TrainTaskAPI.create({
      dataset_id: form.dataset_id,
      model_config_id: form.model_config_id,
      train_config: form.train_config,
      description: form.description,
    });

    const taskId = response.data.data.task_id;
    ElMessage.success('训练任务创建成功！');

    // 跳转到监控页面
    router.push(`/train/monitor/${taskId}`);
  } catch (error: any) {
    ElMessage.error('创建失败: ' + (error.message || '未知错误'));
  } finally {
    creating.value = false;
  }
}

// 格式化文件大小
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 初始化
onMounted(() => {
  loadDatasets();
});
</script>

<style lang="scss" scoped>
.train-create {
  .steps-container {
    margin-bottom: 40px;
    padding: 32px 24px;
    background: linear-gradient(to right, #f8f9fa 0%, #e9ecef 100%);
  }

  .step-content {
    min-height: 400px;
    padding: 0 24px 24px;

    .step-panel {
      max-width: 800px;
      margin: 0 auto;

      .dataset-option {
        display: flex;
        align-items: center;
        justify-content: space-between;
        width: 100%;

        .dataset-name {
          flex: 1;
          font-weight: 500;
        }

        .dataset-info {
          display: flex;
          gap: 12px;
          align-items: center;
          font-size: 12px;
          color: var(--el-text-color-secondary);
        }
      }

      .train-config-form {
        padding: 20px;
        background: var(--el-bg-color);
        border-radius: 8px;
      }

      .confirm-panel {
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
          }
        }

        .create-button-container {
          display: flex;
          justify-content: center;
          margin-top: 32px;
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
  }
}
</style>

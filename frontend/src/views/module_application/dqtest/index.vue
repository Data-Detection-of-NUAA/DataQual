<template>
  <div class="dqtest-page">
    <!-- 顶部进度指示器 -->
    <div class="sticky top-0 z-10">
      <div class="bg-white/90 backdrop-blur-md border-b border-gray-200 shadow-sm px-6 py-4">
        <div class="max-w-7xl mx-auto">
          <div class="flex items-center justify-between mb-4">
            <div>
              <p class="text-sm text-gray-500">多模态数据集鲁棒性评估与测试平台</p>
            </div>
            <div class="flex items-center gap-2">
              <el-tag :type="getTaskStatusType()" size="small">{{ getTaskStatusText() }}</el-tag>
            </div>
          </div>
          
          <!-- 步骤指示器 - 可点击导航 -->
          <div class="flex items-center justify-center gap-4">
            <div 
              v-for="(step, index) in steps" 
              :key="step.id"
              @click="navigateToStep(index + 1)"
              :class="[
                'flex items-center gap-2 px-3 py-3 rounded-xl transition-all cursor-pointer',
                'border-2 w-48 justify-start',
                currentStep === index + 1
                  ? 'bg-indigo-600 text-white border-indigo-600 shadow-lg shadow-indigo-200'
                  : currentStep > index + 1
                  ? 'bg-white text-gray-700 border-emerald-400 hover:bg-emerald-50'
                  : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
              ]"
            >
              <span 
                :class="[
                  'w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0',
                  currentStep === index + 1
                    ? 'bg-white text-indigo-600'
                    : currentStep > index + 1
                    ? 'bg-emerald-400 text-white'
                    : 'bg-gray-200 text-gray-600'
                ]"
              >
                {{ index + 1 }}
              </span>
              <el-icon :size="16" class="flex-shrink-0">
                <component :is="step.icon" />
              </el-icon>
              <span class="font-medium text-sm truncate">{{ step.title }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="max-w-7xl mx-auto px-6 py-8">
      <!-- 第1步：数据集选择 -->
      <DatasetSelector
        v-if="currentStep === 1"
        v-model="taskData.dataset"
        @next="currentStep = 2"
      />

      <!-- 第2步：模型训练 -->
      <ModelTrainer
        v-else-if="currentStep === 2"
        v-model="taskData.model"
        :dataset="taskData.dataset"
        @prev="currentStep = 1"
        @next="currentStep = 3"
      />

      <!-- 第3步：策略选择 -->
      <StrategySelector
        v-else-if="currentStep === 3"
        v-model="taskData.strategy"
        @prev="currentStep = 2"
        @next="currentStep = 4"
      />

      <!-- 第4步：参数配置 -->
      <ParameterConfig
        v-else-if="currentStep === 4"
        v-model="taskData.parameters"
        :strategy="taskData.strategy"
        @prev="currentStep = 3"
        @next="currentStep = 5"
      />

      <!-- 第5步：指标与输出 -->
      <MetricsConfig
        v-else-if="currentStep === 5"
        v-model="taskData.metrics"
        @prev="currentStep = 4"
        @next="currentStep = 6"
      />

      <!-- 第6步：运行控制 -->
      <RunControl
        v-else-if="currentStep === 6"
        :task-data="taskData"
        :is-running="isTaskRunning"
        @start="handleTaskStart"
        @pause="handleTaskPause"
        @resume="handleTaskResume"
        @stop="handleTaskStop"
        @prev="currentStep = 5"
        @next="currentStep = 7"
      />

      <!-- 第7步：结果总览 -->
      <ResultDashboard
        v-else-if="currentStep === 7"
        :task-status="taskStatus"
        :task-data="taskData"
        @restart="handleRestart"
        @prev="currentStep = 6"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Folder,
  Cpu,
  Operation,
  Setting,
  PieChart,
  DataAnalysis,
  TrendCharts
} from '@element-plus/icons-vue'

// 组件导入 - 使用正确的组件名称
import DatasetSelector from './components/DatasetSelector.vue'
import ModelTrainer from './components/ModelTrainer.vue'
import StrategySelector from './components/StrategySelector.vue'
import ParameterConfig from './components/ParameterConfig.vue'
import MetricsConfig from './components/MetricsConfig.vue'
import RunControl from './components/RunControl.vue'
import ResultDashboard from './components/ResultDashboard.vue'

// 步骤配置
const steps = [
  { id: 'dataset', title: '数据集选择', icon: Folder },
  { id: 'model', title: '模型选择与训练', icon: Cpu },
  { id: 'strategy', title: '对抗策略选择', icon: Operation },
  { id: 'params', title: '对抗参数选择', icon: Setting },
  { id: 'metrics', title: '评估方法配置', icon: PieChart },
  { id: 'run', title: '评估运行控制', icon: DataAnalysis },
  { id: 'results', title: '结果总览', icon: TrendCharts }
]

// 状态管理
const currentStep = ref(1)
const taskStatus = ref<'idle' | 'running' | 'paused' | 'completed' | 'failed'>('idle')
const isTaskRunning = ref(false)

// 任务数据
const taskData = ref({
  dataset: {
    datasetId: null,
    name: '',
    modality: '',
    task: '',
    sampleCount: 0,
    classCount: 0,
    fileSize: 0
  },
  model: {
    modelId: null,
    trainingConfig: {
      trainingEpochs: 10,
      batchSize: 32,
      learningRate: 0.001,
      optimizer: 'Adam',
      lossFunction: 'CrossEntropyLoss',
      scheduler: 'StepLR',
      weightDecay: 0.0001,
      momentum: 0.9
    }
  },
  strategy: {
    mode: 'attack', // 'attack' | 'external_dataset'
    threatModel: 'whitebox',
    attacks: [],
    externalDataset: {
      loaded: false,
      name: '',
      size: 0,
      stats: {}
    }
  },
  parameters: {
    // 攻击参数或外部数据集参数
  },
  metrics: {
    selected: ['clean_acc', 'robust_acc', 'asr'],
    outputs: {
      save_adv: true,
      export_csv: true,
      export_json: true
    },
    topK: 5,
    confidenceThreshold: 0.5
  },
  results: {
    summary: {},
    history: [],
    completed: false
  }
})

// 计算属性
const getTaskStatusType = () => {
  const statusTypes: Record<string, string> = {
    idle: 'info',
    running: 'success',
    paused: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return statusTypes[taskStatus.value] || 'info'
}

const getTaskStatusText = () => {
  const statusTexts: Record<string, string> = {
    idle: '就绪',
    running: '运行中',
    paused: '已暂停',
    completed: '已完成',
    failed: '失败'
  }
  return statusTexts[taskStatus.value] || '未知'
}

// 导航方法
const navigateToStep = (stepNumber: number) => {
  // 允许用户点击任何步骤进行导航
  currentStep.value = stepNumber
  ElMessage.info(`切换到步骤${stepNumber}：${steps[stepNumber - 1].title}`)
}

// 任务控制方法
const handleTaskStart = () => {
  taskStatus.value = 'running'
  isTaskRunning.value = true
  ElMessage.success('DqTest评估任务已启动')
}

const handleTaskPause = () => {
  taskStatus.value = 'paused'
  isTaskRunning.value = false
  ElMessage.warning('任务已暂停')
}

const handleTaskResume = () => {
  taskStatus.value = 'running'
  isTaskRunning.value = true
  ElMessage.info('任务已继续')
}

const handleTaskStop = () => {
  taskStatus.value = 'failed'
  isTaskRunning.value = false
  ElMessage.error('任务已停止')
}

const handleRestart = () => {
  taskStatus.value = 'idle'
  isTaskRunning.value = false
  currentStep.value = 1
  
  // 重置部分数据
  taskData.value.results.completed = false
  
  ElMessage.info('正在重新开始评估流程')
}
</script>

<style lang="scss" scoped>
.dqtest-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  
  .sticky {
    position: sticky;
  }
  
  .top-0 {
    top: 0;
  }
  
  .z-10 {
    z-index: 10;
  }
  
  .backdrop-blur-md {
    backdrop-filter: blur(12px);
  }
}

// Tailwind-like utility classes
.max-w-7xl { max-width: 80rem; }
.mx-auto { margin-left: auto; margin-right: auto; }
.px-6 { padding-left: 1.5rem; padding-right: 1.5rem; }
.py-4 { padding-top: 1rem; padding-bottom: 1rem; }
.py-8 { padding-top: 2rem; padding-bottom: 2rem; }
.mb-4 { margin-bottom: 1rem; }
.mt-1 { margin-top: 0.25rem; }
.gap-2 { gap: 0.5rem; }
.flex { display: flex; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.text-2xl { font-size: 1.5rem; }
.text-sm { font-size: 0.875rem; }
.text-xs { font-size: 0.75rem; }
.font-bold { font-weight: 700; }
.font-medium { font-weight: 500; }
.text-gray-900 { color: rgb(17 24 39); }
.text-gray-600 { color: rgb(75 85 99); }
.text-gray-500 { color: rgb(107 114 128); }
.text-indigo-700 { color: rgb(67 56 202); }
.text-emerald-700 { color: rgb(4 120 87); }
.text-white { color: rgb(255 255 255); }
.bg-white { background-color: rgb(255 255 255); }
.bg-indigo-600 { background-color: rgb(79 70 229); }
.bg-emerald-50 { background-color: rgb(236 253 245); }
.bg-emerald-300 { background-color: rgb(110 231 183); }
.bg-gray-300 { background-color: rgb(209 213 219); }
.border { border-width: 1px; }
.border-b { border-bottom-width: 1px; }
.border-gray-200 { border-color: rgb(229 231 235); }
.border-indigo-200 { border-color: rgb(199 210 254); }
.border-emerald-200 { border-color: rgb(187 247 208); }
.rounded-lg { border-radius: 0.5rem; }
.shadow-sm { box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05); }
.shadow { box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1); }
.w-6 { width: 1.5rem; }
.h-6 { height: 1.5rem; }
.h-px { height: 1px; }
.w-8 { width: 2rem; }
.px-3 { padding-left: 0.75rem; padding-right: 0.75rem; }
.py-2 { padding-top: 0.5rem; padding-bottom: 0.5rem; }
.mx-2 { margin-left: 0.5rem; margin-right: 0.5rem; }
.transition-colors { transition-property: color, background-color, border-color; }
.cursor-pointer { cursor: pointer; }

// 悬停效果
.hover\:bg-emerald-100:hover { background-color: rgb(220 252 231); }
.hover\:bg-gray-50:hover { background-color: rgb(249 250 251); }

// 渐变背景
.bg-gradient-to-r { background-image: linear-gradient(to right, var(--tw-gradient-stops)); }
.from-indigo-50 { --tw-gradient-from: #eef2ff; --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgb(238 242 255 / 0)); }
.to-purple-50 { --tw-gradient-to: #faf5ff; }
</style>
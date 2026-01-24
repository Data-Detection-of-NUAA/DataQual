<template>
  <div class="dqtest-container">
    <!-- 顶部导航 -->
    <div class="header-section">
      <el-breadcrumb>
        <el-breadcrumb-item to="/">首页</el-breadcrumb-item>
        <el-breadcrumb-item>DqTest - 鲁棒性评估平台</el-breadcrumb-item>
      </el-breadcrumb>
      
      <div class="header-content">
        <div class="title-section">
          <h1>DqTest - 多模态鲁棒性评估平台</h1>
          <p>数据集/模型联动 · 鲁棒性评估策略选择 · 参数配置 · 鲁棒指标展示</p>
        </div>
        
        <div class="action-buttons">
          <el-button @click="exportDqtestConfig" type="info" plain>
            <template #icon>
              <el-icon><Download /></el-icon>
            </template>
            导出DqTest配置
          </el-button>
          <el-button @click="startDqtestEvaluation" type="danger" :loading="isDqtestRunning">
            <template #icon>
              <el-icon><VideoPlay /></el-icon>
            </template>
            启动DqTest评估
          </el-button>
        </div>
      </div>
    </div>

    <!-- Tab导航 -->
    <div class="tab-navigation">
      <el-tabs v-model="activeDqtestTab" @tab-click="handleDqtestTabClick">
        <el-tab-pane 
          v-for="(tab, index) in dqtestTabs" 
          :key="tab.id"
          :label="tab.title"
          :name="tab.id"
        >
          <template #label>
            <div class="tab-label">
              <span class="step-number">{{ index + 1 }}</span>
              <el-icon><component :is="tab.icon" /></el-icon>
              <span>{{ tab.title }}</span>
            </div>
          </template>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 内容区域 -->
    <div class="content-area">
      <el-card shadow="never">
        <transition name="fade" mode="out-in">
          <!-- 数据集选择 -->
          <DatasetSelector 
            v-if="activeDqtestTab === 'dataset'"
            v-model="dqtestFormData.dataset"
            @next="switchToDqtestTab('model')"
          />
          
          <!-- 模型选择与训练 -->
          <ModelTrainer 
            v-else-if="activeDqtestTab === 'model'"
            v-model="dqtestFormData.model"
            :dataset="dqtestFormData.dataset"
            @prev="switchToDqtestTab('dataset')"
            @next="switchToDqtestTab('strategy')"
          />
          
          <!-- 策略选择 -->
          <StrategySelector 
            v-else-if="activeDqtestTab === 'strategy'"
            v-model="dqtestFormData.strategy"
            @prev="switchToDqtestTab('model')"
            @next="switchToDqtestTab('params')"
          />
          
          <!-- 参数配置 -->
          <ParameterConfig 
            v-else-if="activeDqtestTab === 'params'"
            v-model="dqtestFormData.parameters"
            :strategy="dqtestFormData.strategy"
            @prev="switchToDqtestTab('strategy')"
            @next="switchToDqtestTab('metrics')"
          />
          
          <!-- 指标与输出 -->
          <MetricsConfig 
            v-else-if="activeDqtestTab === 'metrics'"
            v-model="dqtestFormData.metrics"
            @prev="switchToDqtestTab('params')"
            @next="switchToDqtestTab('run')"
          />
          
          <!-- 运行控制 -->
          <RunControl 
            v-else-if="activeDqtestTab === 'run'"
            :task-data="dqtestFormData"
            :is-running="isDqtestRunning"
            @start="handleStartDqtestTask"
            @pause="handlePauseDqtestTask" 
            @stop="handleStopDqtestTask"
            @prev="switchToDqtestTab('metrics')"
            @next="switchToDqtestTab('results')"
          />
          
          <!-- 结果总览 -->
          <ResultDashboard 
            v-else-if="activeDqtestTab === 'results'"
            :task="currentDqtestTask"
            @prev="switchToDqtestTab('run')"
          />
        </transition>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Download, 
  VideoPlay, 
  Database,
  Cpu,
  Operation,
  Setting,
  PieChart,
  DataAnalysis
} from '@element-plus/icons-vue'

// 导入子组件
import DatasetSelector from './components/DatasetSelector.vue'
import ModelTrainer from './components/ModelTrainer.vue'
import StrategySelector from './components/StrategySelector.vue'
import ParameterConfig from './components/ParameterConfig.vue'
import MetricsConfig from './components/MetricsConfig.vue'
import RunControl from './components/RunControl.vue'
import ResultDashboard from './components/ResultDashboard.vue'

// 🚨 暂时注释掉API导入，避免加载错误
// import { DqtestApi } from '@/api/module_application/dqtest'

// 页面状态
const activeDqtestTab = ref('dataset')
const isDqtestRunning = ref(false)
const currentDqtestTask = ref(null)

// DqTest Tab配置
const dqtestTabs = [
  { id: 'dataset', title: '数据集选择', icon: 'Database' },
  { id: 'model', title: '模型选择与训练', icon: 'Cpu' },
  { id: 'strategy', title: '策略选择', icon: 'Operation' },
  { id: 'params', title: '参数配置', icon: 'Setting' },
  { id: 'metrics', title: '指标与输出', icon: 'PieChart' },
  { id: 'run', title: '运行控制', icon: 'VideoPlay' },
  { id: 'results', title: '结果总览', icon: 'DataAnalysis' },
]

// DqTest表单数据
const dqtestFormData = reactive({
  dataset: {
    modality: 'image',
    datasetId: '',
    uploadedFile: null,
    name: '',
    stats: {}
  },
  model: {
    modelId: '',
    trainingConfig: {},
    trainedModel: null
  },
  strategy: {
    mode: 'attack', // 'attack' or 'external_dataset'
    threatModel: 'whitebox',
    attacks: [],
    externalDataset: null
  },
  parameters: {},
  metrics: {
    selected: ['clean_acc', 'robust_acc', 'asr'],
    outputs: {
      save_adv: true,
      export_csv: true,
      export_json: true
    }
  }
})

// 方法
const switchToDqtestTab = (tabId: string) => {
  activeDqtestTab.value = tabId
}

const handleDqtestTabClick = (tab: any) => {
  // 可以在这里添加tab切换的验证逻辑
}

const startDqtestEvaluation = async () => {
  // 快速验证并跳转到运行控制tab
  if (validateDqtestBasicForm()) {
    activeDqtestTab.value = 'run'
    await handleStartDqtestTask()
  }
}

const validateDqtestBasicForm = (): boolean => {
  if (!dqtestFormData.dataset.datasetId && !dqtestFormData.dataset.uploadedFile) {
    ElMessage.error('请选择DqTest数据集')
    activeDqtestTab.value = 'dataset'
    return false
  }
  
  if (!dqtestFormData.model.modelId) {
    ElMessage.error('请选择或训练DqTest模型')
    activeDqtestTab.value = 'model'
    return false
  }
  
  return true
}

const handleStartDqtestTask = async () => {
  try {
    isDqtestRunning.value = true
    
    // 🚨 暂时注释掉API调用
    /*
    const dqtestTaskConfig = {
      name: `DqTest评估-${new Date().toLocaleString()}`,
      ...dqtestFormData
    }
    
    const response = await DqtestApi.createTask(dqtestTaskConfig)
    currentDqtestTask.value = response.data
    */
    
    ElMessage.success('DqTest评估任务已启动（演示模式）')
    
  } catch (error: any) {
    ElMessage.error(error.message || 'DqTest任务启动失败')
    isDqtestRunning.value = false
  }
}

const handlePauseDqtestTask = () => {
  ElMessage.info('DqTest暂停功能开发中')
}

const handleStopDqtestTask = async () => {
  try {
    await ElMessageBox.confirm('确认要停止当前DqTest任务吗？', '确认操作', {
      type: 'warning'
    })
    
    isDqtestRunning.value = false
    ElMessage.success('DqTest任务已停止')
  } catch {
    // 用户取消
  }
}

const exportDqtestConfig = () => {
  const config = JSON.stringify(dqtestFormData, null, 2)
  const blob = new Blob([config], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'dqtest-config.json'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  
  ElMessage.success('DqTest配置已导出')
}

onMounted(() => {
  // DqTest初始化操作
  console.log('DqTest页面已加载')
})
</script>

<style lang="scss" scoped>
.dqtest-container {
  min-height: calc(100vh - 84px);
  background-color: #f8fafc;
  
  .header-section {
    background: white;
    border-bottom: 1px solid #e5e7eb;
    padding: 1.5rem 2rem;
    
    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 1rem;
      
      .title-section {
        h1 {
          font-size: 1.875rem;
          font-weight: 700;
          color: #111827;
          margin: 0 0 0.5rem 0;
        }
        
        p {
          color: #6b7280;
          margin: 0;
        }
      }
      
      .action-buttons {
        display: flex;
        gap: 0.75rem;
      }
    }
  }
  
  .tab-navigation {
    background: white;
    padding: 0 2rem;
    border-bottom: 1px solid #e5e7eb;
    
    :deep(.el-tabs__header) {
      margin: 0;
    }
    
    .tab-label {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      
      .step-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1.5rem;
        height: 1.5rem;
        background: #f3f4f6;
        color: #6b7280;
        border-radius: 0.375rem;
        font-size: 0.75rem;
        font-weight: 600;
      }
    }
    
    :deep(.el-tabs__item.is-active) {
      .step-number {
        background: #4f46e5;
        color: white;
      }
    }
  }
  
  .content-area {
    padding: 2rem;
    
    :deep(.el-card__body) {
      padding: 0;
    }
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
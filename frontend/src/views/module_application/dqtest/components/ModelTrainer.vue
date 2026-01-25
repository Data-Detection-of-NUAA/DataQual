<template>
  <div class="model-trainer">
    <div class="section-header">
      <div class="flex items-center gap-3">
        <span class="w-7 h-7 rounded-lg bg-indigo-600 text-white text-sm font-bold flex items-center justify-center shadow">2</span>
        <div>
          <h3 class="font-bold text-gray-900">模型选择与训练</h3>
          <p class="text-sm text-gray-500 mt-1">基于已选择的数据集进行模型选择和训练</p>
        </div>
      </div>
      <div class="flex items-center gap-2 text-xs text-gray-500">
        <el-icon><Monitor /></el-icon>
        <span>Model Panel</span>
      </div>
    </div>

    <!-- 数据集信息展示 -->
    <div class="p-4 bg-gray-50 border border-gray-200 rounded-lg mb-6">
      <div class="flex items-center justify-between mb-3">
        <div>
          <div class="font-medium text-gray-900">当前数据集</div>
          <div class="text-sm text-gray-600 mt-1">
            {{ dataset.name || '未选择' }} · {{ dataset.modality || 'image' }} · {{ dataset.task || 'classification' }}
          </div>
        </div>
        <el-tag :type="dataset.uploadedFile ? 'success' : 'info'" size="small">
          {{ dataset.uploadedFile ? '自定义数据集' : '预置数据集' }}
        </el-tag>
      </div>
      <div v-if="dataset.uploadedFile" class="text-xs text-gray-600">
        文件：{{ dataset.uploadedFile.name }} · {{ formatFileSize(dataset.uploadedFile.size) }}
      </div>
    </div>

    <!-- 推荐模型表格 -->
    <div class="mb-8">
      <h4 class="font-bold text-gray-900 mb-4">推荐模型</h4>
      <div class="overflow-hidden border border-gray-200 rounded-xl">
        <el-table 
          :data="recommendedModels" 
          style="width: 100%" 
          @row-click="selectTrainModel"
          class="model-table"
        >
          <el-table-column width="80">
            <template #default="{ row }">
              <div class="flex items-center justify-center">
                <div :class="[
                  'w-5 h-5 rounded-full border-2 flex items-center justify-center cursor-pointer',
                  localData.modelId === row.id ? 'border-indigo-600 bg-indigo-600' : 'border-gray-300'
                ]">
                  <el-icon v-if="localData.modelId === row.id" class="w-3 h-3 text-white"><Check /></el-icon>
                </div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="模型" width="200">
            <template #default="{ row }">
              <div class="flex items-center gap-3">
                <div :class="[
                  'w-10 h-10 rounded-lg flex items-center justify-center text-white',
                  row.color
                ]">
                  <el-icon class="w-5 h-5"><component :is="row.icon" /></el-icon>
                </div>
                <div>
                  <div class="font-medium text-gray-900">{{ row.name }}</div>
                  <div class="text-xs text-gray-500">{{ row.abbr }}</div>
                </div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="模型类型" width="120">
            <template #default="{ row }">
              <el-tag :class="row.typeClass" size="small">{{ row.type }}</el-tag>
            </template>
          </el-table-column>
          
          <el-table-column label="适用场景" width="200">
            <template #default="{ row }">
              <span class="text-sm text-gray-700">{{ row.scenario }}</span>
            </template>
          </el-table-column>
          
          <el-table-column label="简介" min-width="300">
            <template #default="{ row }">
              <span class="text-sm text-gray-600">{{ row.description }}</span>
            </template>
          </el-table-column>
          
          <el-table-column label="推荐指数" width="150">
            <template #default="{ row }">
              <div class="flex items-center gap-2">
                <div class="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    :class="['h-full rounded-full', row.ratingColor]"
                    :style="{ width: row.rating * 20 + '%' }"
                  ></div>
                </div>
                <span class="text-sm font-bold text-gray-900">{{ row.rating }}/5</span>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 训练参数配置 -->
    <div class="mb-8">
      <div class="flex items-center justify-between mb-4">
        <h4 class="font-bold text-gray-900">训练参数配置</h4>
        <div class="flex items-center gap-2">
          <span class="text-sm text-gray-600">已选择：</span>
          <span class="font-bold text-indigo-600">{{ selectedTrainModelName }}</span>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- 网络结构配置 -->
        <div class="space-y-6">
          <div>
            <h5 class="font-medium text-gray-900 mb-3">网络结构</h5>
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">层数</label>
                <div class="flex gap-2">
                  <label 
                    v-for="layer in layers" 
                    :key="layer"
                    :class="[
                      'flex-1 p-3 border rounded-lg cursor-pointer text-center transition-all',
                      localData.trainingConfig.layers === layer 
                        ? 'border-indigo-500 bg-indigo-50 text-indigo-700 font-medium' 
                        : 'border-gray-300 hover:border-gray-400'
                    ]"
                    @click="localData.trainingConfig.layers = layer"
                  >
                    {{ layer }}层
                  </label>
                </div>
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">隐藏单元</label>
                <div class="grid grid-cols-3 gap-2">
                  <label 
                    v-for="unit in hiddenUnits" 
                    :key="unit"
                    :class="[
                      'p-3 border rounded-lg cursor-pointer text-center transition-all',
                      localData.trainingConfig.hiddenUnits === unit 
                        ? 'border-purple-500 bg-purple-50 text-purple-700 font-medium' 
                        : 'border-gray-300 hover:border-gray-400'
                    ]"
                    @click="localData.trainingConfig.hiddenUnits = unit"
                  >
                    {{ unit }}
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 训练参数 -->
        <div class="space-y-6">
          <div>
            <h5 class="font-medium text-gray-900 mb-3">训练参数</h5>
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">学习率</label>
                <div class="grid grid-cols-3 gap-2">
                  <label 
                    v-for="lr in learningRates" 
                    :key="lr"
                    :class="[
                      'p-3 border rounded-lg cursor-pointer text-center transition-all',
                      localData.trainingConfig.learningRate === lr 
                        ? 'border-green-500 bg-green-50 text-green-700 font-medium' 
                        : 'border-gray-300 hover:border-gray-400'
                    ]"
                    @click="localData.trainingConfig.learningRate = lr"
                  >
                    {{ lr }}
                  </label>
                </div>
              </div>
              
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">批次大小</label>
                  <div class="flex gap-2">
                    <label 
                      v-for="batch in batchSizes" 
                      :key="batch"
                      :class="[
                        'flex-1 p-3 border rounded-lg cursor-pointer text-center transition-all text-sm',
                        localData.trainingConfig.batchSize === batch 
                          ? 'border-blue-500 bg-blue-50 text-blue-700 font-medium' 
                          : 'border-gray-300 hover:border-gray-400'
                      ]"
                      @click="localData.trainingConfig.batchSize = batch"
                    >
                      {{ batch }}
                    </label>
                  </div>
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">优化器</label>
                  <div class="flex gap-2">
                    <label 
                      v-for="optimizer in optimizers" 
                      :key="optimizer"
                      :class="[
                        'flex-1 p-2 border rounded-lg cursor-pointer text-center transition-all text-sm',
                        localData.trainingConfig.optimizer === optimizer 
                          ? 'border-orange-500 bg-orange-50 text-orange-700 font-medium' 
                          : 'border-gray-300 hover:border-gray-400'
                      ]"
                      @click="localData.trainingConfig.optimizer = optimizer"
                    >
                      {{ optimizer }}
                    </label>
                  </div>
                </div>
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">训练轮数</label>
                <div class="grid grid-cols-3 gap-2">
                  <label 
                    v-for="epoch in epochs" 
                    :key="epoch"
                    :class="[
                      'p-3 border rounded-lg cursor-pointer text-center transition-all',
                      localData.trainingConfig.epochs === epoch 
                        ? 'border-red-500 bg-red-50 text-red-700 font-medium' 
                        : 'border-gray-300 hover:border-gray-400'
                    ]"
                    @click="localData.trainingConfig.epochs = epoch"
                  >
                    {{ epoch }}
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 训练进度 -->
    <div class="mb-8">
      <h4 class="font-bold text-gray-900 mb-4">训练进度</h4>
      
      <div v-if="!trainingStarted && !trainingCompleted" class="text-center p-8 border-2 border-dashed border-gray-300 rounded-xl bg-gray-50">
        <el-icon class="w-12 h-12 text-gray-400 mx-auto mb-4"><VideoPlay /></el-icon>
        <p class="text-gray-600 mb-4">点击下方按钮开始模型训练</p>
        <el-button 
          @click="startTraining"
          type="success"
          size="large"
        >
          <el-icon class="mr-2"><VideoPlay /></el-icon>
          开始训练
        </el-button>
      </div>
      
      <!-- 训练中 -->
      <div v-else-if="trainingStarted" class="space-y-6">
        <!-- 总体进度 -->
        <div>
          <div class="flex justify-between items-center mb-3">
            <span class="font-medium text-gray-900">总体训练进度</span>
            <span class="font-bold text-indigo-600">{{ overallProgress }}%</span>
          </div>
          <div class="h-3 bg-gray-200 rounded-full overflow-hidden">
            <div 
              class="h-full rounded-full transition-all duration-1000 progress-bar"
              :style="{ width: overallProgress + '%' }"
            ></div>
          </div>
        </div>
        
        <!-- 详细指标 -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-xl">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm text-gray-700">当前轮次</span>
              <span class="font-bold text-blue-600">{{ currentEpoch }}/{{ localData.trainingConfig.epochs || 50 }}</span>
            </div>
            <div class="h-2 bg-blue-100 rounded-full overflow-hidden">
              <div 
                class="h-full bg-blue-500 rounded-full" 
                :style="{ width: (currentEpoch / (localData.trainingConfig.epochs || 50)) * 100 + '%' }"
              ></div>
            </div>
          </div>
          
          <div class="p-4 bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-xl">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm text-gray-700">损失值</span>
              <span class="font-bold text-green-600">{{ lossValue.toFixed(4) }}</span>
            </div>
            <div class="flex items-center text-xs text-green-600">
              <el-icon class="w-4 h-4 mr-1"><TrendCharts /></el-icon>
              下降趋势良好
            </div>
          </div>
          
          <div class="p-4 bg-gradient-to-br from-purple-50 to-pink-50 border border-purple-200 rounded-xl">
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm text-gray-700">准确率</span>
              <span class="font-bold text-purple-600">{{ accuracy.toFixed(2) }}%</span>
            </div>
            <div class="flex items-center text-xs text-purple-600">
              <el-icon class="w-4 h-4 mr-1"><TrendCharts /></el-icon>
              持续上升中
            </div>
          </div>
        </div>
        
        <!-- 训练日志 -->
        <div class="border border-gray-200 rounded-xl overflow-hidden">
          <div class="px-4 py-3 bg-gray-50 border-b border-gray-200">
            <h5 class="font-medium text-gray-900">训练日志</h5>
          </div>
          <div class="p-4 max-h-40 overflow-y-auto">
            <div v-for="(log, index) in trainingLogs" :key="index" class="text-sm font-mono mb-2">
              <span class="text-gray-500">[{{ log.time }}]</span>
              <span :class="log.type === 'info' ? 'text-gray-700' : 'text-green-600'">
                {{ log.message }}
              </span>
            </div>
          </div>
        </div>
        
        <!-- 训练控制按钮 -->
        <div class="flex justify-center gap-3">
          <el-button @click="toggleTraining" :type="trainingPaused ? 'success' : 'warning'">
            <el-icon class="mr-2"><component :is="trainingPaused ? 'VideoPlay' : 'VideoPause'" /></el-icon>
            {{ trainingPaused ? '继续训练' : '暂停训练' }}
          </el-button>
          <el-button @click="restartTraining" type="info" plain>
            <el-icon class="mr-2"><RefreshRight /></el-icon>
            重新训练
          </el-button>
        </div>
      </div>
      
      <!-- 训练完成 -->
      <div v-else-if="trainingCompleted" class="space-y-6">
        <!-- 训练完成提示 -->
        <div class="p-6 bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-300 rounded-xl">
          <div class="flex items-start gap-4">
            <div class="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
              <el-icon class="w-8 h-8 text-white"><CircleCheckFilled /></el-icon>
            </div>
            <div class="flex-1">
              <h5 class="text-xl font-bold text-gray-900 mb-2">模型训练完成！</h5>
              <p class="text-gray-700 mb-3">模型已成功训练并保存，可用于后续的对抗攻击测试。</p>
              
              <!-- 模型文件信息 -->
              <div class="mt-4 p-4 bg-white border border-green-200 rounded-lg">
                <div class="flex items-center justify-between mb-3">
                  <h6 class="font-medium text-gray-900">生成的模型文件</h6>
                  <div class="flex gap-2">
                    <el-button 
                      @click="downloadModel"
                      type="success"
                      size="small"
                      plain
                    >
                      <el-icon class="mr-1"><Download /></el-icon>
                      下载
                    </el-button>
                    <el-button 
                      @click="viewModelDetails"
                      size="small"
                      plain
                    >
                      <el-icon class="mr-1"><View /></el-icon>
                      查看
                    </el-button>
                  </div>
                </div>
                <div class="space-y-2">
                  <div class="flex items-center gap-3 p-2 bg-gray-50 rounded">
                    <el-icon class="w-4 h-4 text-green-600"><Files /></el-icon>
                    <div class="flex-1">
                      <div class="font-medium text-sm text-gray-900">{{ generatedModelFile.name }}</div>
                      <div class="text-xs text-gray-500">{{ generatedModelFile.type }} · {{ formatFileSize(generatedModelFile.size) }}</div>
                    </div>
                    <el-tag type="success" size="small">已保存</el-tag>
                  </div>
                  <div class="text-xs text-gray-600 pl-7">
                    保存路径: <code class="bg-gray-100 px-1 rounded">{{ generatedModelFile.path }}</code>
                  </div>
                </div>
              </div>
              
              <!-- 模型性能摘要 -->
              <div class="grid grid-cols-2 gap-4 mt-4">
                <div class="p-3 bg-white border border-gray-200 rounded-lg">
                  <div class="text-xs text-gray-600 mb-1">最终准确率</div>
                  <div class="text-xl font-bold text-green-600">{{ accuracy.toFixed(2) }}%</div>
                </div>
                <div class="p-3 bg-white border border-gray-200 rounded-lg">
                  <div class="text-xs text-gray-600 mb-1">最终损失值</div>
                  <div class="text-xl font-bold text-blue-600">{{ lossValue.toFixed(4) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 训练日志（查看模式） -->
        <div class="border border-gray-200 rounded-xl overflow-hidden">
          <div class="px-4 py-3 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
            <h5 class="font-medium text-gray-900">训练日志</h5>
            <span class="text-xs text-gray-500">{{ trainingLogs.length }} 条记录</span>
          </div>
          <div class="p-4 max-h-60 overflow-y-auto">
            <div v-for="(log, index) in trainingLogs" :key="index" class="text-sm font-mono mb-2">
              <span class="text-gray-500">[{{ log.time }}]</span>
              <span :class="log.type === 'info' ? 'text-gray-700' : 'text-green-600'">
                {{ log.message }}
              </span>
            </div>
          </div>
        </div>
        
        <!-- 完成后操作按钮 -->
        <div class="flex justify-center gap-3">
          <el-button @click="restartTraining" type="primary" plain>
            <el-icon class="mr-2"><RefreshRight /></el-icon>
            重新训练
          </el-button>
          <el-button @click="downloadModel" type="success">
            <el-icon class="mr-2"><Download /></el-icon>
            下载模型
          </el-button>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button @click="$emit('prev')">
        <el-icon class="mr-2"><ArrowLeft /></el-icon>
        上一步：数据集选择
      </el-button>
      
      <div class="flex gap-3">
        <el-button 
          @click="$emit('next')"
          type="primary" 
          :disabled="!trainingCompleted"
        >
          下一步：鲁棒性评估策略选择
          <el-icon class="ml-2"><ArrowRight /></el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Monitor,
  Check,
  VideoPlay,
  VideoPause,
  TrendCharts,
  CircleCheckFilled,
  Download,
  View,
  Files,
  RefreshRight,
  ArrowLeft,
  ArrowRight
} from '@element-plus/icons-vue'

interface Props {
  modelValue: {
    modelId: string
    trainingConfig: any
    trainedModel: any
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

// 本地数据
const localData = ref({
  modelId: '',
  trainingConfig: {
    layers: 2,
    hiddenUnits: 64,
    learningRate: 0.001,
    batchSize: 32,
    optimizer: 'Adam',
    epochs: 50
  },
  trainedModel: null,
  ...props.modelValue
})

// 训练状态
const trainingStarted = ref(false)
const trainingPaused = ref(false)
const trainingCompleted = ref(false)
const overallProgress = ref(0)
const currentEpoch = ref(0)
const lossValue = ref(2.5)
const accuracy = ref(50.0)
const trainingLogs = ref<Array<{time: string, message: string, type: string}>>([])

// 生成的模型文件信息
const generatedModelFile = ref({
  name: 'trained_model.pth',
  type: 'PyTorch Model File',
  size: 4587520, // 4.5 MB
  path: '/models/trained/' + Date.now() + '_model.pth'
})

// 配置选项
const layers = [1, 2, 3]
const hiddenUnits = [32, 64, 128]
const learningRates = [0.01, 0.001, 0.0001]
const batchSizes = [16, 32, 64]
const optimizers = ['Adam', 'SGD', 'RMSprop']
const epochs = [30, 50, 100]

// 推荐模型列表
const recommendedModels = ref([
  {
    id: 'lstm',
    name: 'LSTM',
    abbr: 'Long Short-Term Memory',
    type: '时序模型',
    typeClass: 'bg-blue-100 text-blue-800',
    scenario: '时间序列预测、自然语言处理',
    description: '适用于处理序列数据的循环神经网络变体，能够学习长期依赖关系',
    icon: 'TrendCharts',
    color: 'bg-gradient-to-br from-blue-500 to-blue-600',
    rating: 4.5,
    ratingColor: 'bg-yellow-500'
  },
  {
    id: 'transformer',
    name: 'Transformer',
    abbr: 'Attention Mechanism',
    type: '通用模型',
    typeClass: 'bg-purple-100 text-purple-800',
    scenario: '文本翻译、图像识别、语音处理',
    description: '基于自注意力机制的模型，并行计算能力强，适合多模态任务',
    icon: 'Monitor',
    color: 'bg-gradient-to-br from-purple-500 to-purple-600',
    rating: 5,
    ratingColor: 'bg-green-500'
  },
  {
    id: 'tcn',
    name: 'TCN',
    abbr: 'Temporal Convolutional Network',
    type: '时序模型',
    typeClass: 'bg-green-100 text-green-800',
    scenario: '时间序列分类、事件预测',
    description: '基于卷积神经网络的时间序列模型，感受野大，训练效率高',
    icon: 'TrendCharts',
    color: 'bg-gradient-to-br from-green-500 to-green-600',
    rating: 4,
    ratingColor: 'bg-blue-500'
  },
  {
    id: 'resnet',
    name: 'ResNet-50',
    abbr: 'Residual Network',
    type: '图像模型',
    typeClass: 'bg-red-100 text-red-800',
    scenario: '图像分类、目标检测',
    description: '深度残差网络，解决深度网络训练中的梯度消失问题',
    icon: 'Files',
    color: 'bg-gradient-to-br from-red-500 to-red-600',
    rating: 4.8,
    ratingColor: 'bg-yellow-500'
  },
  {
    id: 'bert',
    name: 'BERT',
    abbr: 'Bidirectional Encoder',
    type: '文本模型',
    typeClass: 'bg-orange-100 text-orange-800',
    scenario: '文本分类、问答系统',
    description: '基于Transformer的双向预训练语言模型',
    icon: 'Files',
    color: 'bg-gradient-to-br from-orange-500 to-orange-600',
    rating: 4.7,
    ratingColor: 'bg-green-500'
  }
])

// 计算属性
const selectedTrainModelName = computed(() => {
  const model = recommendedModels.value.find(m => m.id === localData.value.modelId)
  return model ? model.name : '未选择'
})

// 方法
const selectTrainModel = (row: any) => {
  localData.value.modelId = row.id
  ElMessage.success(`已选择模型：${row.name}`)
}

const startTraining = () => {
  trainingStarted.value = true
  trainingCompleted.value = false
  overallProgress.value = 0
  currentEpoch.value = 0
  lossValue.value = 2.5
  accuracy.value = 50.0
  trainingLogs.value = []
  
  // 生成模型文件名
  const timestamp = new Date().getTime()
  const modelName = localData.value.modelId.toUpperCase()
  const datasetName = props.dataset.name || 'Dataset'
  generatedModelFile.value = {
    name: `${datasetName.replace(/\s+/g, '_')}_${modelName}_${timestamp}.pth`,
    type: 'PyTorch Model File',
    size: Math.floor(Math.random() * 3000000) + 2000000, // 2-5 MB
    path: `/models/trained/${datasetName.replace(/\s+/g, '_')}_${modelName}_${timestamp}.pth`
  }
  
  // 添加初始日志
  addTrainingLog(`开始训练模型: ${selectedTrainModelName.value}`)
  addTrainingLog(`数据集: ${props.dataset.name || '未知'}`)
  addTrainingLog(`配置: ${localData.value.trainingConfig.layers}层, ${localData.value.trainingConfig.hiddenUnits}隐藏单元, LR=${localData.value.trainingConfig.learningRate}`)
  addTrainingLog(`目标轮次: ${localData.value.trainingConfig.epochs}, 批次大小: ${localData.value.trainingConfig.batchSize}`)
  
  ElMessage.success('模型训练已开始')
  
  // 模拟训练过程
  simulateTraining()
}

const restartTraining = () => {
  trainingStarted.value = false
  trainingCompleted.value = false
  overallProgress.value = 0
  currentEpoch.value = 0
  lossValue.value = 2.5
  accuracy.value = 50.0
  trainingLogs.value = []
  ElMessage.info('训练已重置')
}

const toggleTraining = () => {
  trainingPaused.value = !trainingPaused.value
  addTrainingLog(trainingPaused.value ? '训练已暂停' : '训练已继续')
  ElMessage.info(trainingPaused.value ? '训练已暂停' : '训练已继续')
}

const simulateTraining = () => {
  if (trainingCompleted.value) return
  
  const interval = setInterval(() => {
    if (trainingPaused.value) return
    
    // 更新进度
    overallProgress.value = Math.min(overallProgress.value + 0.5, 100)
    currentEpoch.value = Math.floor((overallProgress.value / 100) * localData.value.trainingConfig.epochs)
    
    // 模拟损失下降和准确率上升
    if (lossValue.value > 0.1) {
      lossValue.value -= 0.01
    }
    if (accuracy.value < 95) {
      accuracy.value += 0.25
    }
    
    // 添加训练日志
    if (Math.random() > 0.7) {
      addTrainingLog(`Epoch ${currentEpoch.value}: Loss = ${lossValue.value.toFixed(4)}, Acc = ${accuracy.value.toFixed(2)}%`)
    }
    
    // 训练完成
    if (overallProgress.value >= 100) {
      clearInterval(interval)
      trainingCompleted.value = true
      trainingStarted.value = false
      addTrainingLog('模型训练完成!', 'success')
      addTrainingLog(`最终准确率: ${accuracy.value.toFixed(2)}%, 最终损失: ${lossValue.value.toFixed(4)}`, 'success')
      addTrainingLog(`模型已保存至: ${generatedModelFile.value.path}`, 'success')
      
      // 更新本地数据
      localData.value.trainedModel = {
        name: generatedModelFile.value.name,
        path: generatedModelFile.value.path,
        accuracy: accuracy.value,
        loss: lossValue.value
      }
      
      ElMessage.success('模型训练完成！')
    }
  }, 100)
}

const addTrainingLog = (message: string, type = 'info') => {
  const now = new Date()
  const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
  trainingLogs.value.push({ time, message, type })
  
  // 保持日志数量不超过20条
  if (trainingLogs.value.length > 20) {
    trainingLogs.value.shift()
  }
}

const downloadModel = () => {
  addTrainingLog('开始下载模型文件...')
  ElMessage.success('模型下载功能开发中')
  // 模拟下载
  setTimeout(() => {
    addTrainingLog(`模型文件 ${generatedModelFile.value.name} 下载完成`, 'success')
  }, 1000)
}

const viewModelDetails = () => {
  addTrainingLog('查看模型详细信息...')
  const info = `模型信息:\n名称: ${generatedModelFile.value.name}\n类型: ${generatedModelFile.value.type}\n大小: ${formatFileSize(generatedModelFile.value.size)}\n路径: ${generatedModelFile.value.path}`
  ElMessage.info(info)
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

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
  padding: 2rem;
  
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    
    h3 {
      font-size: 1.25rem;
      font-weight: 600;
      margin: 0;
    }
  }
  
  .action-buttons {
    display: flex;
    justify-content: space-between;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
  }
}

// 表格样式
:deep(.model-table) {
  .el-table__row {
    cursor: pointer;
    transition: background-color 0.2s ease;
  }
  
  .el-table__row:hover {
    background-color: #f8fafc;
  }
}

// 进度条动画
.progress-bar {
  background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 50%, #a855f7 100%);
  background-size: 200% 100%;
  animation: gradient-shift 2s ease infinite;
}

@keyframes gradient-shift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

// Tailwind-like classes
.flex { display: flex; }
.items-center { align-items: center; }
.items-start { align-items: flex-start; }
.justify-between { justify-content: space-between; }
.justify-center { justify-content: center; }
.gap-2 { gap: 0.5rem; }
.gap-3 { gap: 0.75rem; }
.gap-4 { gap: 1rem; }
.gap-6 { gap: 1.5rem; }
.gap-8 { gap: 2rem; }
.w-3 { width: 0.75rem; }
.h-3 { height: 0.75rem; }
.w-4 { width: 1rem; }
.h-4 { height: 1rem; }
.w-5 { width: 1.25rem; }
.h-5 { height: 1.25rem; }
.w-7 { width: 1.75rem; }
.h-7 { height: 1.75rem; }
.w-8 { width: 2rem; }
.h-8 { height: 2rem; }
.w-10 { width: 2.5rem; }
.h-10 { height: 2.5rem; }
.w-12 { width: 3rem; }
.h-12 { height: 3rem; }
.w-16 { width: 4rem; }
.h-16 { height: 4rem; }
.w-24 { width: 6rem; }
.h-2 { height: 0.5rem; }
.h-3 { height: 0.75rem; }
.rounded-lg { border-radius: 0.5rem; }
.rounded-xl { border-radius: 0.75rem; }
.rounded-full { border-radius: 9999px; }
.bg-indigo-600 { background-color: rgb(79 70 229); }
.bg-indigo-50 { background-color: rgb(238 242 255); }
.bg-purple-50 { background-color: rgb(250 245 255); }
.bg-green-50 { background-color: rgb(240 253 244); }
.bg-green-500 { background-color: rgb(34 197 94); }
.bg-blue-50 { background-color: rgb(239 246 255); }
.bg-blue-100 { background-color: rgb(219 234 254); }
.bg-blue-500 { background-color: rgb(59 130 246); }
.bg-orange-50 { background-color: rgb(255 247 237); }
.bg-red-50 { background-color: rgb(254 242 242); }
.bg-gray-50 { background-color: rgb(249 250 251); }
.bg-gray-100 { background-color: rgb(243 244 246); }
.bg-gray-200 { background-color: rgb(229 231 235); }
.bg-yellow-500 { background-color: rgb(234 179 8); }
.text-white { color: rgb(255 255 255); }
.text-gray-900 { color: rgb(17 24 39); }
.text-gray-700 { color: rgb(55 65 81); }
.text-gray-600 { color: rgb(75 85 99); }
.text-gray-500 { color: rgb(107 114 128); }
.text-indigo-600 { color: rgb(79 70 229); }
.text-indigo-700 { color: rgb(67 56 202); }
.text-blue-600 { color: rgb(37 99 235); }
.text-blue-700 { color: rgb(29 78 216); }
.text-green-600 { color: rgb(22 163 74); }
.text-green-700 { color: rgb(21 128 61); }
.text-purple-600 { color: rgb(147 51 234); }
.text-purple-700 { color: rgb(126 34 206); }
.text-orange-700 { color: rgb(194 65 12); }
.text-red-700 { color: rgb(185 28 28); }
.text-sm { font-size: 0.875rem; }
.text-xs { font-size: 0.75rem; }
.text-xl { font-size: 1.25rem; }
.font-bold { font-weight: 700; }
.font-semibold { font-weight: 600; }
.font-medium { font-weight: 500; }
.font-mono { font-family: ui-monospace, SFMono-Regular, 'SF Mono', monospace; }
.shadow { box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1); }
.border { border-width: 1px; }
.border-2 { border-width: 2px; }
.border-dashed { border-style: dashed; }
.border-gray-200 { border-color: rgb(229 231 235); }
.border-gray-300 { border-color: rgb(209 213 219); }
.border-indigo-500 { border-color: rgb(99 102 241); }
.border-indigo-600 { border-color: rgb(79 70 229); }
.border-purple-500 { border-color: rgb(168 85 247); }
.border-purple-200 { border-color: rgb(221 214 254); }
.border-green-200 { border-color: rgb(187 247 208); }
.border-green-300 { border-color: rgb(134 239 172); }
.border-blue-200 { border-color: rgb(191 219 254); }
.border-blue-500 { border-color: rgb(59 130 246); }
.border-orange-500 { border-color: rgb(249 115 22); }
.border-red-500 { border-color: rgb(239 68 68); }
.p-2 { padding: 0.5rem; }
.p-3 { padding: 0.75rem; }
.p-4 { padding: 1rem; }
.p-6 { padding: 1.5rem; }
.p-8 { padding: 2rem; }
.px-1 { padding-left: 0.25rem; padding-right: 0.25rem; }
.px-4 { padding-left: 1rem; padding-right: 1rem; }
.py-3 { padding-top: 0.75rem; padding-bottom: 0.75rem; }
.pl-7 { padding-left: 1.75rem; }
.mb-1 { margin-bottom: 0.25rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-3 { margin-bottom: 0.75rem; }
.mb-4 { margin-bottom: 1rem; }
.mb-6 { margin-bottom: 1.5rem; }
.mb-8 { margin-bottom: 2rem; }
.mt-1 { margin-top: 0.25rem; }
.mt-3 { margin-top: 0.75rem; }
.mt-4 { margin-top: 1rem; }
.mr-1 { margin-right: 0.25rem; }
.mr-2 { margin-right: 0.5rem; }
.ml-2 { margin-left: 0.5rem; }
.mx-auto { margin-left: auto; margin-right: auto; }
.space-y-4 > * + * { margin-top: 1rem; }
.space-y-6 > * + * { margin-top: 1.5rem; }
.grid { display: grid; }
.grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.text-center { text-align: center; }
.cursor-pointer { cursor: pointer; }
.transition-all { transition-property: all; }
.duration-1000 { transition-duration: 1000ms; }
.overflow-hidden { overflow: hidden; }
.overflow-y-auto { overflow-y: auto; }
.block { display: block; }
.flex-1 { flex: 1 1 0%; }
.flex-shrink-0 { flex-shrink: 0; }
.max-h-40 { max-height: 10rem; }
.max-h-60 { max-height: 15rem; }

// 响应式
@media (min-width: 768px) {
  .md\:grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}

@media (min-width: 1024px) {
  .lg\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

// 悬停效果
.hover\:border-gray-400:hover { border-color: rgb(156 163 175); }

// Element Plus标签样式
.bg-blue-100.text-blue-800 { 
  background-color: rgb(219 234 254); 
  color: rgb(30 64 175); 
}
.bg-purple-100.text-purple-800 { 
  background-color: rgb(243 232 255); 
  color: rgb(107 33 168); 
}
.bg-green-100.text-green-800 { 
  background-color: rgb(220 252 231); 
  color: rgb(22 101 52); 
}
.bg-red-100.text-red-800 { 
  background-color: rgb(254 226 226); 
  color: rgb(153 27 27); 
}
.bg-orange-100.text-orange-800 { 
  background-color: rgb(255 237 213); 
  color: rgb(154 52 18); 
}
</style>
<template>
  <div class="dataset-selector">
    <div class="section-header">
      <div class="flex items-center gap-3">
        <span class="w-7 h-7 rounded-lg bg-indigo-600 text-white text-sm font-bold flex items-center justify-center shadow">1</span>
        <div>
          <h3 class="font-bold text-gray-900">数据集选择</h3>
          <p class="text-sm text-gray-500 mt-1">选择预置数据集或上传自定义数据集</p>
        </div>
      </div>
      <div class="flex items-center gap-2 text-xs text-gray-500">
        <el-icon><Folder /></el-icon>
        <span>Dataset Panel</span>
      </div>
    </div>

    <div class="form-content space-y-6">
      <!-- 模态选择 -->
      <div>
        <label class="block text-xs font-semibold text-gray-600 mb-3 uppercase tracking-wider">模态类型</label>
        <el-select v-model="localData.modality" @change="handleModalityChange" class="w-full">
          <el-option value="image" label="图像 Image" />
          <el-option value="text" label="文本 Text" />
          <el-option value="audio" label="音频 Audio" />
          <el-option value="structured" label="结构化数据 Structured Data" />
          <el-option value="pointcloud" label="点云 Point Cloud" />
        </el-select>
      </div>

      <!-- 预置数据集选择 -->
      <div>
        <label class="block text-xs font-semibold text-gray-600 mb-3">预置数据集</label>
        <el-select v-model="localData.datasetId" @change="handleDatasetChange" placeholder="请选择数据集..." class="w-full">
          <el-option
            v-for="d in availableDatasets"
            :key="d.id"
            :value="d.id"
            :label="`${d.name} · ${d.task}`"
          />
        </el-select>
      </div>

      <!-- 数据集信息展示 -->
      <div v-if="selectedDataset" class="p-4 bg-gray-50 rounded-lg border border-gray-200">
        <div class="text-xs text-gray-500 mb-2">数据集信息</div>
        <div class="grid grid-cols-2 gap-3 text-sm">
          <div>
            <div class="text-xs text-gray-500">任务</div>
            <div class="font-medium text-gray-900">{{ selectedDataset.task }}</div>
          </div>
          <div>
            <div class="text-xs text-gray-500">样本数</div>
            <div class="font-medium text-gray-900">{{ selectedDataset.stats?.samples?.toLocaleString() }}</div>
          </div>
          <div>
            <div class="text-xs text-gray-500">类别数</div>
            <div class="font-medium text-gray-900">{{ selectedDataset.stats?.classes }}</div>
          </div>
          <div>
            <div class="text-xs text-gray-500">输入</div>
            <div class="font-medium text-gray-900">{{ selectedDataset.stats?.input }}</div>
          </div>
        </div>
      </div>

      <!-- 数据集上传区域 -->
      <div class="border-t border-gray-200 pt-6">
        <div class="mb-4">
          <h4 class="text-lg font-semibold text-gray-900 mb-2">自定义数据集上传</h4>
          <p class="text-gray-600">上传您的数据集以进行后续的模型训练和评估</p>
        </div>

        <!-- 上传区域 -->
        <div 
          @click="triggerFileUpload"
          @dragover.prevent="dragover = true"
          @dragleave.prevent="dragover = false"
          @drop.prevent="handleDrop"
          :class="[
            'border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-300 mb-6',
            dragover ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 hover:border-indigo-400 hover:bg-gray-50',
            localData.uploadedFile ? 'border-green-500 bg-green-50' : ''
          ]"
        >
          <div class="mb-4">
            <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center">
              <el-icon class="w-8 h-8 text-indigo-600"><UploadFilled /></el-icon>
            </div>
            <template v-if="!localData.uploadedFile">
              <h3 class="text-lg font-semibold text-gray-900 mb-2">拖放文件到此处</h3>
              <p class="text-gray-500 mb-4">或点击选择文件</p>
              <el-button type="primary">选择文件</el-button>
            </template>
            <template v-else>
              <h3 class="text-lg font-semibold text-gray-900 mb-2">文件已上传</h3>
              <p class="text-gray-500 mb-2">{{ localData.uploadedFile.name }}</p>
              <p class="text-sm text-green-600 font-medium">上传成功</p>
            </template>
          </div>
          <input 
            type="file" 
            ref="fileInputRef"
            @change="handleFileSelect"
            class="hidden"
            accept=".csv,.json,.txt,.zip,.tar.gz,.h5,.pkl,.pt"
          />
        </div>

        <!-- 上传进度 -->
        <div v-if="uploading" class="mb-6">
          <div class="flex justify-between items-center mb-2">
            <span class="text-sm font-medium text-gray-700">上传进度</span>
            <span class="font-bold text-indigo-600">{{ uploadProgress }}%</span>
          </div>
          <div class="h-2.5 bg-gray-200 rounded-full overflow-hidden">
            <div 
              class="h-full bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full transition-all duration-500 progress-bar"
              :style="{ width: uploadProgress + '%' }"
            ></div>
          </div>
          
          <div class="grid grid-cols-2 gap-4 mt-4">
            <div class="p-3 bg-gray-50 rounded-lg">
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600">速度：</span>
                <span class="font-mono text-sm font-bold text-indigo-600">{{ uploadSpeed }} MB/s</span>
              </div>
            </div>
            <div class="p-3 bg-gray-50 rounded-lg">
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600">剩余时间：</span>
                <span class="font-mono text-sm font-bold text-indigo-600">{{ remainingTime }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 数据集配置信息 -->
        <div v-if="localData.uploadedFile" class="mb-6">
          <h4 class="text-lg font-semibold text-gray-900 mb-4">数据集配置信息</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- 左侧配置 -->
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">数据集名称</label>
                <el-input 
                  v-model="datasetName"
                  placeholder="从上传文件名自动提取"
                />
                <p class="text-xs text-gray-500 mt-1">从上传的文件名中自动提取，可手动修改</p>
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">数据模态选择</label>
                <div class="grid grid-cols-2 gap-2">
                  <label 
                    v-for="modality in dataModalities" 
                    :key="modality.id"
                    :class="[
                      'p-3 border rounded-lg cursor-pointer transition-all text-center',
                      selectedModality === modality.id 
                        ? 'border-indigo-500 bg-indigo-50 text-indigo-700 font-medium' 
                        : 'border-gray-300 hover:border-gray-400'
                    ]"
                    @click="selectedModality = modality.id"
                  >
                    <el-icon class="mr-2"><component :is="modality.icon" /></el-icon>
                    {{ modality.label }}
                  </label>
                </div>
              </div>
            </div>
            
            <!-- 右侧配置 -->
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">任务类型选择</label>
                <div class="grid grid-cols-2 gap-2">
                  <label 
                    v-for="task in taskTypes" 
                    :key="task.id"
                    :class="[
                      'p-3 border rounded-lg cursor-pointer transition-all text-center',
                      selectedTask === task.id 
                        ? 'border-purple-500 bg-purple-50 text-purple-700 font-medium' 
                        : 'border-gray-300 hover:border-gray-400'
                    ]"
                    @click="selectedTask = task.id"
                  >
                    {{ task.label }}
                  </label>
                </div>
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">数据描述</label>
                <el-input 
                  v-model="datasetDescription"
                  type="textarea"
                  :rows="3"
                  placeholder="请描述您的数据集..."
                />
              </div>
            </div>
          </div>
        </div>

        <!-- 上传控制按钮 -->
        <div v-if="uploading" class="flex justify-between">
          <el-button @click="toggleUpload" type="warning" plain>
            {{ uploadPaused ? '继续上传' : '暂停上传' }}
          </el-button>
          
          <el-button @click="cancelUpload" type="danger" plain>
            取消上传
          </el-button>
        </div>
      </div>

      <!-- 数据集上传信息展示 -->
      <div v-if="localData.uploadedFile" class="p-4 bg-gray-50 rounded-lg border border-gray-200">
        <div class="flex items-center justify-between mb-3">
          <div>
            <div class="text-sm font-semibold text-gray-900">已上传数据集</div>
            <div class="text-xs text-gray-600 mt-1">
              文件：{{ localData.uploadedFile.name }} · {{ formatFileSize(localData.uploadedFile.size) }}
            </div>
          </div>
          <el-tag type="success" size="small">已加载</el-tag>
        </div>
        
        <div class="flex flex-wrap gap-2 mt-3">
          <el-button size="small" plain>采样预览</el-button>
          <el-button size="small" plain>字段映射</el-button>
          <el-button size="small" plain>统计信息</el-button>
          <el-button @click="clearUploadedFile" size="small" type="danger" plain>重新上传</el-button>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <div></div>
      <el-button 
        @click="$emit('next')" 
        type="primary" 
        :disabled="!canProceed"
      >
        下一步：模型选择与训练
        <el-icon class="ml-2"><ArrowRight /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  UploadFilled, 
  ArrowRight, 
  Folder,
  Picture,
  Document,
  Headset,
  Monitor
} from '@element-plus/icons-vue'

interface Props {
  modelValue: {
    modality: string
    datasetId: string
    uploadedFile: File | null
    name: string
    stats: any
  }
}

interface Emits {
  (e: 'update:modelValue', value: Props['modelValue']): void
  (e: 'next'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const localData = ref({ ...props.modelValue })
const fileInputRef = ref()
const dragover = ref(false)

// 上传相关状态
const uploading = ref(false)
const uploadPaused = ref(false)
const uploadProgress = ref(0)
const uploadSpeed = ref(2.5)
const remainingTime = ref('02:30')

// 数据集配置
const datasetName = ref('')
const selectedModality = ref('image')
const selectedTask = ref('classification')
const datasetDescription = ref('')

// 配置选项 - 使用正确的Element Plus图标
const dataModalities = [
  { id: 'image', label: '图像数据', icon: 'Picture' },
  { id: 'text', label: '文本数据', icon: 'Document' },
  { id: 'audio', label: '音频数据', icon: 'Headset' },
  { id: 'time', label: '时序数据', icon: 'Monitor' }
]

const taskTypes = [
  { id: 'classification', label: '分类任务' },
  { id: 'regression', label: '回归任务' },
  { id: 'detection', label: '检测任务' },
  { id: 'generation', label: '生成任务' }
]

// Mock数据
const mockDatasets = {
  image: [
    { id: "ds-img-cifar10", name: "CIFAR-10", task: "classification", stats: { samples: 10000, classes: 10, input: "32×32×3" } },
    { id: "ds-img-imagenet-mini", name: "ImageNet-Mini", task: "classification", stats: { samples: 5000, classes: 100, input: "224×224×3" } },
  ],
  text: [
    { id: "ds-txt-agnews", name: "AG News", task: "classification", stats: { samples: 7600, classes: 4, input: "tokenized" } },
  ],
  audio: [
    { id: "ds-aud-esc50-mini", name: "ESC-50-Mini", task: "classification", stats: { samples: 2000, classes: 50, input: "1×T@16kHz" } },
  ],
  structured: [
    { id: "ds-struct-adult", name: "Adult Income", task: "classification", stats: { samples: 16281, classes: 2, input: "14 features" } },
  ],
  pointcloud: [
    { id: "ds-pc-modelnet40", name: "ModelNet40", task: "classification", stats: { samples: 2468, classes: 40, input: "Nx3 points" } },
  ]
}

// 计算属性
const availableDatasets = computed(() => {
  return mockDatasets[localData.value.modality as keyof typeof mockDatasets] || []
})

const selectedDataset = computed(() => {
  return availableDatasets.value.find(d => d.id === localData.value.datasetId)
})

const canProceed = computed(() => {
  return localData.value.datasetId || localData.value.uploadedFile
})

// 方法
const handleModalityChange = () => {
  localData.value.datasetId = ''
  localData.value.uploadedFile = null
  ElMessage.info(`已切换到 ${localData.value.modality} 模态`)
}

const handleDatasetChange = () => {
  localData.value.uploadedFile = null
  ElMessage.success('数据集选择成功')
}

const triggerFileUpload = () => {
  fileInputRef.value?.click()
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    localData.value.uploadedFile = file
    localData.value.datasetId = ''
    extractDatasetName(file.name)
    startUploadSimulation()
    ElMessage.success('文件选择成功')
  }
}

const handleDrop = (event: DragEvent) => {
  dragover.value = false
  const file = event.dataTransfer?.files[0]
  if (file) {
    localData.value.uploadedFile = file
    localData.value.datasetId = ''
    extractDatasetName(file.name)
    startUploadSimulation()
    ElMessage.success('文件上传成功')
  }
}

const extractDatasetName = (fileName: string) => {
  let name = fileName.replace(/\.[^/.]+$/, "")
  name = name.replace(/(_dataset|_data|_train|_test|_val)$/i, "")
  name = name.replace(/[_-]/g, " ")
  name = name.replace(/\b\w/g, char => char.toUpperCase())
  
  datasetName.value = name || '未命名数据集'
  datasetDescription.value = `基于 ${name} 数据集构建的多模态鲁棒性评估模型`
}

const startUploadSimulation = () => {
  uploading.value = true
  uploadPaused.value = false
  uploadProgress.value = 0
  
  const interval = setInterval(() => {
    if (!uploadPaused.value && uploadProgress.value < 100) {
      uploadProgress.value += 2
      uploadSpeed.value = parseFloat((1.5 + Math.random()).toFixed(1))
      
      const remainingPercent = 100 - uploadProgress.value
      const totalSeconds = Math.round((remainingPercent / 2) * 50)
      const minutes = Math.floor(totalSeconds / 60)
      const seconds = totalSeconds % 60
      remainingTime.value = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
      
      if (uploadProgress.value >= 100) {
        clearInterval(interval)
        uploading.value = false
        ElMessage.success(`数据集上传完成: ${localData.value.uploadedFile?.name}`)
      }
    }
  }, 200)
}

const toggleUpload = () => {
  uploadPaused.value = !uploadPaused.value
  ElMessage.info(uploadPaused.value ? '上传已暂停' : '上传已继续')
}

const cancelUpload = () => {
  localData.value.uploadedFile = null
  uploading.value = false
  uploadProgress.value = 0
  datasetName.value = ''
  datasetDescription.value = ''
  ElMessage.warning('数据集上传已取消')
}

const clearUploadedFile = () => {
  localData.value.uploadedFile = null
  datasetName.value = ''
  datasetDescription.value = ''
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
  ElMessage.info('已清空上传文件')
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
  localData.value = { ...newVal }
}, { deep: true })
</script>

<style lang="scss" scoped>
.dataset-selector {
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
  
  .form-content {
    margin-bottom: 2rem;
  }
  
  .action-buttons {
    display: flex;
    justify-content: space-between;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
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

// Tailwind-like CSS classes
.flex { display: flex; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.gap-2 { gap: 0.5rem; }
.gap-3 { gap: 0.75rem; }
.gap-4 { gap: 1rem; }
.gap-6 { gap: 1.5rem; }
.w-7 { width: 1.75rem; }
.h-7 { height: 1.75rem; }
.w-8 { width: 2rem; }
.h-8 { height: 2rem; }
.w-16 { width: 4rem; }
.h-16 { height: 4rem; }
.rounded-lg { border-radius: 0.5rem; }
.rounded-xl { border-radius: 0.75rem; }
.rounded-full { border-radius: 9999px; }
.bg-indigo-600 { background-color: rgb(79 70 229); }
.bg-indigo-50 { background-color: rgb(238 242 255); }
.bg-indigo-100 { background-color: rgb(224 231 255); }
.bg-purple-100 { background-color: rgb(243 232 255); }
.bg-gray-50 { background-color: rgb(249 250 251); }
.bg-green-50 { background-color: rgb(240 253 244); }
.text-white { color: rgb(255 255 255); }
.text-gray-900 { color: rgb(17 24 39); }
.text-gray-600 { color: rgb(75 85 99); }
.text-gray-500 { color: rgb(107 114 128); }
.text-gray-700 { color: rgb(55 65 81); }
.text-indigo-600 { color: rgb(79 70 229); }
.text-indigo-700 { color: rgb(67 56 202); }
.text-green-600 { color: rgb(22 163 74); }
.text-purple-700 { color: rgb(126 34 206); }
.text-sm { font-size: 0.875rem; }
.text-xs { font-size: 0.75rem; }
.text-lg { font-size: 1.125rem; }
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
.border-indigo-200 { border-color: rgb(199 210 254); }
.border-indigo-500 { border-color: rgb(99 102 241); }
.border-green-500 { border-color: rgb(34 197 94); }
.border-purple-500 { border-color: rgb(168 85 247); }
.border-t { border-top-width: 1px; }
.p-3 { padding: 0.75rem; }
.p-4 { padding: 1rem; }
.p-12 { padding: 3rem; }
.pt-6 { padding-top: 1.5rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-3 { margin-bottom: 0.75rem; }
.mb-4 { margin-bottom: 1rem; }
.mb-6 { margin-bottom: 1.5rem; }
.mt-1 { margin-top: 0.25rem; }
.mt-3 { margin-top: 0.75rem; }
.mt-4 { margin-top: 1rem; }
.ml-2 { margin-left: 0.5rem; }
.mr-2 { margin-right: 0.5rem; }
.mx-auto { margin-left: auto; margin-right: auto; }
.space-y-4 > * + * { margin-top: 1rem; }
.space-y-6 > * + * { margin-top: 1.5rem; }
.grid { display: grid; }
.grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.text-center { text-align: center; }
.cursor-pointer { cursor: pointer; }
.transition-all { transition-property: all; }
.duration-300 { transition-duration: 300ms; }
.duration-500 { transition-duration: 500ms; }
.uppercase { text-transform: uppercase; }
.tracking-wider { letter-spacing: 0.05em; }
.overflow-hidden { overflow: hidden; }
.block { display: block; }
.hidden { display: none; }
.w-full { width: 100%; }
.h-2\.5 { height: 0.625rem; }
.flex-wrap { flex-wrap: wrap; }

// 响应式
@media (min-width: 768px) {
  .md\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

// 悬停效果
.hover\:border-indigo-400:hover { border-color: rgb(129 140 248); }
.hover\:bg-gray-50:hover { background-color: rgb(249 250 251); }
.hover\:border-gray-400:hover { border-color: rgb(156 163 175); }
</style>
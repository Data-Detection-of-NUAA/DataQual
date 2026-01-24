<template>
  <div class="dataset-selector">
    <div class="section-header">
      <h3>数据集选择</h3>
      <p>选择预置数据集或上传自定义数据集</p>
    </div>
    
    <div class="form-content">
      <!-- 模态选择 -->
      <el-form-item label="数据模态">
        <el-radio-group v-model="localData.modality">
          <el-radio value="image">图像数据</el-radio>
          <el-radio value="text">文本数据</el-radio>
          <el-radio value="audio">音频数据</el-radio>
          <el-radio value="structured">结构化数据</el-radio>
        </el-radio-group>
      </el-form-item>
      
      <!-- 数据集选择 -->
      <el-form-item label="预置数据集">
        <el-select v-model="localData.datasetId" placeholder="请选择数据集" style="width: 100%">
          <el-option
            v-for="dataset in availableDatasets"
            :key="dataset.id"
            :label="dataset.name"
            :value="dataset.id"
          />
        </el-select>
      </el-form-item>
      
      <!-- 文件上传 -->
      <el-form-item label="或上传自定义数据集">
        <el-upload
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleFileChange"
          drag
        >
          <div class="upload-area">
            <el-icon class="upload-icon"><UploadFilled /></el-icon>
            <div v-if="!localData.uploadedFile">
              <p>拖拽文件到此处或点击上传</p>
              <p class="upload-hint">支持 CSV, JSON, ZIP 等格式</p>
            </div>
            <div v-else>
              <p class="file-name">{{ localData.uploadedFile.name }}</p>
              <p class="file-size">{{ formatFileSize(localData.uploadedFile.size) }}</p>
            </div>
          </div>
        </el-upload>
      </el-form-item>
    </div>
    
    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button @click="$emit('next')" type="primary" :disabled="!canProceed">
        下一步
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'

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

// 本地数据
const localData = ref({ ...props.modelValue })

// Mock数据
const mockDatasets = {
  image: [
    { id: 'ds-cifar10', name: 'CIFAR-10 数据集' },
    { id: 'ds-imagenet', name: 'ImageNet 数据集' }
  ],
  text: [
    { id: 'ds-agnews', name: 'AG News 数据集' }
  ],
  audio: [
    { id: 'ds-esc50', name: 'ESC-50 数据集' }
  ],
  structured: [
    { id: 'ds-adult', name: 'Adult Income 数据集' }
  ]
}

const availableDatasets = computed(() => {
  return mockDatasets[localData.value.modality as keyof typeof mockDatasets] || []
})

const canProceed = computed(() => {
  return localData.value.datasetId || localData.value.uploadedFile
})

// 监听本地数据变化，同步到父组件
watch(localData, (newVal) => {
  emit('update:modelValue', newVal)
}, { deep: true })

// 文件上传处理
const handleFileChange = (file: any) => {
  localData.value.uploadedFile = file.raw
  localData.value.datasetId = '' // 清空数据集选择
}

// 文件大小格式化
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
</script>

<style lang="scss" scoped>
.dataset-selector {
  padding: 2rem;
  
  .section-header {
    margin-bottom: 2rem;
    
    h3 {
      font-size: 1.25rem;
      font-weight: 600;
      margin: 0 0 0.5rem 0;
    }
    
    p {
      color: #6b7280;
      margin: 0;
    }
  }
  
  .form-content {
    margin-bottom: 2rem;
    
    .upload-area {
      padding: 3rem;
      text-align: center;
      
      .upload-icon {
        font-size: 3rem;
        color: #9ca3af;
        margin-bottom: 1rem;
      }
      
      .upload-hint {
        color: #9ca3af;
        font-size: 0.875rem;
      }
      
      .file-name {
        font-weight: 600;
        color: #059669;
      }
      
      .file-size {
        color: #6b7280;
        font-size: 0.875rem;
      }
    }
  }
  
  .action-buttons {
    display: flex;
    justify-content: flex-end;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
  }
}
</style>
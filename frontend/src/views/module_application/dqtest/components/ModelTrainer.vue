<template>
  <div class="model-trainer">
    <div class="section-header">
      <h3>模型选择与训练</h3>
      <p>选择预训练模型或训练新模型</p>
    </div>
    
    <div class="form-content">
      <el-form label-width="120px">
        <!-- 预训练模型选择 -->
        <el-form-item label="预训练模型">
          <el-select v-model="localData.modelId" placeholder="请选择模型" style="width: 100%">
            <el-option
              v-for="model in availableModels"
              :key="model.id"
              :label="model.name"
              :value="model.id"
            />
          </el-select>
        </el-form-item>
        
        <!-- 训练状态 -->
        <el-form-item v-if="localData.modelId" label="模型状态">
          <el-tag :type="getModelStatusType(selectedModel?.status)">
            {{ selectedModel?.status || '未知' }}
          </el-tag>
        </el-form-item>
      </el-form>
    </div>
    
    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button @click="$emit('prev')">上一步</el-button>
      <el-button @click="$emit('next')" type="primary" :disabled="!canProceed">
        下一步
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

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
const localData = ref({ ...props.modelValue })

// Mock数据
const availableModels = ref([
  { id: 'resnet18', name: 'ResNet-18', status: '已训练' },
  { id: 'resnet50', name: 'ResNet-50', status: '已训练' },
  { id: 'bert-base', name: 'BERT-Base', status: '已训练' },
])

const selectedModel = computed(() => {
  return availableModels.value.find(m => m.id === localData.value.modelId)
})

const canProceed = computed(() => {
  return localData.value.modelId
})

// 监听本地数据变化
watch(localData, (newVal) => {
  emit('update:modelValue', newVal)
}, { deep: true })

const getModelStatusType = (status: string) => {
  switch (status) {
    case '已训练': return 'success'
    case '训练中': return 'warning'
    case '未训练': return 'info'
    default: return 'info'
  }
}
</script>

<style lang="scss" scoped>
.model-trainer {
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
  }
  
  .action-buttons {
    display: flex;
    justify-content: space-between;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
  }
}
</style>
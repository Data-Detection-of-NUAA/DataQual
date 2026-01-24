<template>
  <div class="metrics-config">
    <div class="section-header">
      <h3>指标与输出</h3>
      <p>选择评估指标和输出选项</p>
    </div>
    
    <div class="form-content">
      <el-form label-width="120px">
        <!-- 评估指标 -->
        <el-form-item label="评估指标">
          <el-checkbox-group v-model="localData.selected">
            <el-checkbox v-for="metric in availableMetrics" :key="metric.key" :value="metric.key">
              {{ metric.label }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        
        <!-- 输出选项 -->
        <el-form-item label="输出选项">
          <el-checkbox v-model="localData.outputs.save_adv">保存对抗样本</el-checkbox>
          <el-checkbox v-model="localData.outputs.export_csv">导出CSV</el-checkbox>
          <el-checkbox v-model="localData.outputs.export_json">导出JSON</el-checkbox>
        </el-form-item>
      </el-form>
    </div>
    
    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button @click="$emit('prev')">上一步</el-button>
      <el-button @click="$emit('next')" type="primary" :disabled="!canProceed">下一步</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface Props {
  modelValue: {
    selected: string[]
    outputs: {
      save_adv: boolean
      export_csv: boolean
      export_json: boolean
    }
  }
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

const availableMetrics = ref([
  { key: 'clean_acc', label: 'Clean Accuracy' },
  { key: 'robust_acc', label: 'Robust Accuracy' },
  { key: 'asr', label: 'Attack Success Rate' },
])

const canProceed = computed(() => {
  return localData.value.selected.length > 0
})

// 监听本地数据变化
watch(localData, (newVal) => {
  emit('update:modelValue', newVal)
}, { deep: true })
</script>

<style lang="scss" scoped>
.metrics-config {
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
    
    :deep(.el-checkbox) {
      display: block;
      margin-bottom: 0.5rem;
    }
  }
  
  .action-buttons {
    display: flex;
    justify-content: space-between;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
  }
}
</style>
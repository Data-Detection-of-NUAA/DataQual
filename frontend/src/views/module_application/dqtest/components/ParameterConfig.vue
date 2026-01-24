<template>
  <div class="parameter-config">
    <div class="section-header">
      <h3>参数配置</h3>
      <p>配置攻击和评估参数</p>
    </div>
    
    <div class="form-content">
      <el-form label-width="120px">
        <!-- 攻击参数 -->
        <el-form-item v-if="strategy.mode === 'attack'" label="epsilon">
          <el-input-number v-model="localData.epsilon" :min="0" :max="1" :step="0.01" />
        </el-form-item>
        
        <el-form-item v-if="strategy.mode === 'attack'" label="步数">
          <el-input-number v-model="localData.steps" :min="1" :max="100" />
        </el-form-item>
        
        <!-- 通用参数 -->
        <el-form-item label="批次大小">
          <el-input-number v-model="localData.batchSize" :min="1" :max="128" />
        </el-form-item>
      </el-form>
    </div>
    
    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button @click="$emit('prev')">上一步</el-button>
      <el-button @click="$emit('next')" type="primary">下一步</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface Props {
  modelValue: any
  strategy: any
}

interface Emits {
  (e: 'update:modelValue', value: any): void
  (e: 'prev'): void
  (e: 'next'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 本地数据
const localData = ref({
  epsilon: 0.03,
  steps: 10,
  batchSize: 32,
  ...props.modelValue
})

// 监听本地数据变化
watch(localData, (newVal) => {
  emit('update:modelValue', newVal)
}, { deep: true })
</script>

<style lang="scss" scoped>
.parameter-config {
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
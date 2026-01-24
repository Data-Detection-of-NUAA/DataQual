<template>
  <div class="strategy-selector">
    <div class="section-header">
      <h3>策略选择</h3>
      <p>选择鲁棒性评估策略</p>
    </div>
    
    <div class="form-content">
      <el-form label-width="120px">
        <!-- 评估模式 -->
        <el-form-item label="评估模式">
          <el-radio-group v-model="localData.mode">
            <el-radio value="attack">对抗攻击评估</el-radio>
            <el-radio value="external_dataset">外部数据集评估</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <!-- 威胁模型 -->
        <el-form-item v-if="localData.mode === 'attack'" label="威胁模型">
          <el-radio-group v-model="localData.threatModel">
            <el-radio value="whitebox">白盒攻击</el-radio>
            <el-radio value="blackbox">黑盒攻击</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <!-- 攻击方法 -->
        <el-form-item v-if="localData.mode === 'attack'" label="攻击方法">
          <el-checkbox-group v-model="localData.attacks">
            <el-checkbox v-for="attack in availableAttacks" :key="attack.id" :value="attack.id">
              {{ attack.name }}
            </el-checkbox>
          </el-checkbox-group>
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
    mode: string
    threatModel: string
    attacks: string[]
    externalDataset: any
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

// Mock数据
const availableAttacks = ref([
  { id: 'fgsm', name: 'FGSM' },
  { id: 'pgd', name: 'PGD' },
  { id: 'cw', name: 'C&W' },
])

const canProceed = computed(() => {
  if (localData.value.mode === 'attack') {
    return localData.value.attacks.length > 0
  }
  return true
})

// 监听本地数据变化
watch(localData, (newVal) => {
  emit('update:modelValue', newVal)
}, { deep: true })
</script>

<style lang="scss" scoped>
.strategy-selector {
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
<template>
  <div class="run-control">
    <div class="section-header">
      <h3>运行控制</h3>
      <p>监控任务执行状态和进度</p>
    </div>
    
    <div class="form-content">
      <!-- 进度条 -->
      <div class="progress-section">
        <el-progress :percentage="progress" :status="progressStatus" />
        <p class="progress-text">{{ progressText }}</p>
      </div>
      
      <!-- 控制按钮 -->
      <div class="control-buttons">
        <el-button @click="$emit('start')" type="success" :disabled="isRunning">开始</el-button>
        <el-button @click="$emit('pause')" type="warning" :disabled="!isRunning">暂停</el-button>
        <el-button @click="$emit('stop')" type="danger" :disabled="!isRunning">停止</el-button>
      </div>
      
      <!-- 日志显示 -->
      <div class="log-section">
        <h4>运行日志</h4>
        <div class="log-content">
          <p v-for="(log, index) in logs" :key="index" class="log-item">
            {{ log }}
          </p>
        </div>
      </div>
    </div>
    
    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button @click="$emit('prev')">上一步</el-button>
      <el-button @click="$emit('next')" type="primary" :disabled="!isCompleted">查看结果</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  taskData: any
  isRunning: boolean
}

interface Emits {
  (e: 'start'): void
  (e: 'pause'): void
  (e: 'stop'): void
  (e: 'prev'): void
  (e: 'next'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 模拟数据
const progress = ref(0)
const logs = ref(['系统准备就绪', '等待开始...'])

const progressStatus = computed(() => {
  if (progress.value === 100) return 'success'
  if (props.isRunning) return undefined
  return 'exception'
})

const progressText = computed(() => {
  if (progress.value === 0) return '等待开始'
  if (progress.value === 100) return '完成'
  if (props.isRunning) return '运行中...'
  return '已暂停'
})

const isCompleted = computed(() => {
  return progress.value === 100
})
</script>

<style lang="scss" scoped>
.run-control {
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
    
    .progress-section {
      margin-bottom: 2rem;
      
      .progress-text {
        margin-top: 0.5rem;
        text-align: center;
        color: #6b7280;
      }
    }
    
    .control-buttons {
      display: flex;
      gap: 1rem;
      justify-content: center;
      margin-bottom: 2rem;
    }
    
    .log-section {
      h4 {
        margin: 0 0 1rem 0;
        font-size: 1rem;
      }
      
      .log-content {
        max-height: 200px;
        overflow-y: auto;
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 0.375rem;
        padding: 1rem;
        
        .log-item {
          margin: 0.25rem 0;
          font-family: monospace;
          font-size: 0.875rem;
        }
      }
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
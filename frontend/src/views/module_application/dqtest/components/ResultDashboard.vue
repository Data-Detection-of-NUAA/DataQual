<template>
  <div class="result-dashboard">
    <div class="section-header">
      <h3>结果总览</h3>
      <p>查看评估结果和分析报告</p>
    </div>
    
    <div class="form-content">
      <!-- 结果统计 -->
      <div class="result-stats">
        <div class="stat-card">
          <h4>Clean Accuracy</h4>
          <p class="stat-value">{{ results.cleanAcc }}%</p>
        </div>
        <div class="stat-card">
          <h4>Robust Accuracy</h4>
          <p class="stat-value">{{ results.robustAcc }}%</p>
        </div>
        <div class="stat-card">
          <h4>Attack Success Rate</h4>
          <p class="stat-value">{{ results.asr }}%</p>
        </div>
      </div>
      
      <!-- 结果详情 -->
      <div class="result-details">
        <h4>详细结���</h4>
        <el-table :data="resultTableData" stripe>
          <el-table-column prop="metric" label="指标" />
          <el-table-column prop="value" label="数值" />
          <el-table-column prop="description" label="描述" />
        </el-table>
      </div>
      
      <!-- 导出按钮 -->
      <div class="export-buttons">
        <el-button type="primary">导出报告</el-button>
        <el-button>下载数据</el-button>
      </div>
    </div>
    
    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button @click="$emit('prev')">上一步</el-button>
      <el-button type="success">完成</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  task: any
}

interface Emits {
  (e: 'prev'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 模拟结果数据
const results = ref({
  cleanAcc: 95.2,
  robustAcc: 78.6,
  asr: 17.5
})

const resultTableData = ref([
  { metric: 'Clean Accuracy', value: '95.2%', description: '原始数据集上的准确率' },
  { metric: 'Robust Accuracy', value: '78.6%', description: '对抗样本上的准确率' },
  { metric: 'Attack Success Rate', value: '17.5%', description: '攻击成功率' },
])
</script>

<style lang="scss" scoped>
.result-dashboard {
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
    
    .result-stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;
      
      .stat-card {
        padding: 1.5rem;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        text-align: center;
        
        h4 {
          margin: 0 0 0.5rem 0;
          color: #6b7280;
          font-size: 0.875rem;
        }
        
        .stat-value {
          margin: 0;
          font-size: 2rem;
          font-weight: 600;
          color: #1f2937;
        }
      }
    }
    
    .result-details {
      margin-bottom: 2rem;
      
      h4 {
        margin: 0 0 1rem 0;
        font-size: 1rem;
      }
    }
    
    .export-buttons {
      display: flex;
      gap: 1rem;
      justify-content: center;
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
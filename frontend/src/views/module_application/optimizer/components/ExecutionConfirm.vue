<template>
  <div class="execution-confirm">
    <el-card shadow="never">
      <template #header>
        <span>执行确认</span>
      </template>

      <!-- 1. 执行摘要 -->
      <el-row :gutter="20">
        <el-col :span="24">
          <el-card header="执行任务清单" class="summary-card">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="检索补入">
                {{ estimation.retrievalCount }} 条
              </el-descriptions-item>
              <el-descriptions-item label="增强处理">
                {{ estimation.augmentationCount }} 条
              </el-descriptions-item>
              <el-descriptions-item label="总计新增">
                <b>{{ estimation.totalNewCount }} 条</b>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
      </el-row>

      <!-- 2. 资源预测 -->
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="12">
          <el-card header="资源预测" class="resource-card">
            <div class="resource-item">
              <el-icon><Cpu /></el-icon>
              <span>GPU 预计耗时: 2 hours</span>
            </div>
            <div class="resource-item">
              <el-icon><FolderOpened /></el-icon>
              <span>存储空间增量: +5GB</span>
            </div>
            <div class="resource-item">
              <el-icon><Money /></el-icon>
              <span>费用估算: $30</span>
            </div>
          </el-card>
        </el-col>

        <el-col :span="12">
          <el-card header="性能提升预测" class="performance-card">
            <el-statistic title="新版本 mAP 预测" :value="70.8" suffix="%" />
            <div class="improvement">
              <el-tag type="success">+9.0%</el-tag>
              <span style="margin-left: 8px; color: #67c23a;">相比当前版本提升</span>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 3. 执行流程视图 -->
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
          <el-card header="执行流程" class="process-card">
            <el-row :gutter="20">
              <el-col :span="12">
                <div class="process-item">
                  <h4>检索任务</h4>
                  <el-progress :percentage="100" status="success" />
                  <div class="process-status">已完成</div>
                  <el-button size="small" link>View Log</el-button>
                </div>
              </el-col>

              <el-col :span="12">
                <div class="process-item">
                  <h4>增强写回</h4>
                  <el-progress :percentage="30" />
                  <div class="process-status">进行中...</div>
                  <el-button size="small" link>View Log</el-button>
                </div>
              </el-col>
            </el-row>
          </el-card>
        </el-col>
      </el-row>

      <!-- 3.5 优化效果对比 (仅在执行完成后显示) -->
      <el-row v-if="executionCompleted" :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
          <el-card class="result-comparison-card">
            <template #header>
              <div class="comparison-header">
                <el-icon><TrendCharts /></el-icon>
                <span>优化效果对比</span>
              </div>
            </template>

            <!-- mAP 统计 -->
            <el-row :gutter="20" style="margin-bottom: 24px;">
              <el-col :span="8">
                <el-statistic title="优化前 mAP" :value="executionResult.originalMap" suffix="%" />
              </el-col>
              <el-col :span="8">
                <el-statistic title="优化后 mAP" :value="executionResult.finalMap" suffix="%">
                  <template #suffix>
                    <span style="font-size: 20px; color: #67c23a;">%</span>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="8">
                <el-statistic title="实际提升" :value="executionResult.actualImprovement" suffix="%">
                  <template #prefix>
                    <el-icon style="color: #67c23a;"><CaretTop /></el-icon>
                  </template>
                </el-statistic>
              </el-col>
            </el-row>

            <!-- 对比图表 -->
            <div ref="mapComparisonChartRef" style="height: 350px; width: 100%;"></div>

            <!-- 类别级 AP 对比表格 -->
            <el-table :data="executionResult.categoryAPComparison" style="margin-top: 24px;" border>
              <el-table-column prop="category" label="类别" width="150" />
              <el-table-column prop="originalAP" label="优化前 AP" width="120">
                <template #default="scope">
                  {{ scope.row.originalAP.toFixed(3) }}
                </template>
              </el-table-column>
              <el-table-column prop="finalAP" label="优化后 AP" width="120">
                <template #default="scope">
                  <span :style="{ color: scope.row.finalAP > scope.row.originalAP ? '#67c23a' : '#303133' }">
                    {{ scope.row.finalAP.toFixed(3) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="improvement" label="提升" width="120">
                <template #default="scope">
                  <el-tag :type="scope.row.improvement > 0 ? 'success' : 'info'" size="small">
                    {{ scope.row.improvement > 0 ? '+' : '' }}{{ scope.row.improvement.toFixed(3) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态">
                <template #default="scope">
                  <el-tag :type="scope.row.finalAP >= 0.5 ? 'success' : 'warning'" size="small">
                    {{ scope.row.finalAP >= 0.5 ? '已达标' : '仍需优化' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
      </el-row>

      <!-- 4. 输出结果与操作 -->
      <el-card class="output-card" style="margin-top: 20px;">
        <div class="output-actions">
          <div class="action-buttons">
            <el-button>
              <el-icon><Download /></el-icon>
              导出优化方案
            </el-button>
            <el-button>
              <el-icon><Download /></el-icon>
              下载新增样本包
            </el-button>
          </div>
          <el-button
            v-if="!executionCompleted"
            type="primary"
            size="large"
            @click="handleExecute"
            :loading="executing"
          >
            <el-icon><VideoPlay /></el-icon>
            触发训练
          </el-button>
        </div>
      </el-card>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { ElMessage } from 'element-plus';
import { Cpu, FolderOpened, Money, Download, VideoPlay, TrendCharts, CaretTop } from '@element-plus/icons-vue';
import * as echarts from 'echarts';

interface Props {
  datasetId?: string;
  strategyConfig?: any;
  acceptedIds?: string[];
}

const props = defineProps<Props>();

const emit = defineEmits<{
  next: [];
}>();

const executing = ref(false);
const executionCompleted = ref(false);

// 执行估算数据 - 与 Step2 策略对应
const estimation = ref({
  retrievalCount: 11000,  // 3000 + 2500 + 2000 + 1800 + 1700
  augmentationCount: 5000,  // 1200 + 1000 + 800 + 900 + 1100
  totalNewCount: 16000,  // 检索 + 增强
});

// 执行结果数据
const executionResult = ref({
  originalMap: 61.8,
  finalMap: 70.8,
  actualImprovement: 9.0,
  categoryAPComparison: [] as Array<{
    category: string;
    originalAP: number;
    finalAP: number;
    improvement: number;
  }>,
});

const mapComparisonChartRef = ref<HTMLElement>();
let mapComparisonChartInstance: echarts.ECharts | null = null;

// 初始化 mAP 对比图表
const initMapComparisonChart = () => {
  if (!mapComparisonChartRef.value || executionResult.value.categoryAPComparison.length === 0) return;

  mapComparisonChartInstance = echarts.init(mapComparisonChartRef.value);

  const categories = executionResult.value.categoryAPComparison.map(item => item.category);
  const originalData = executionResult.value.categoryAPComparison.map(item => item.originalAP);
  const finalData = executionResult.value.categoryAPComparison.map(item => item.finalAP);

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['优化前', '优化后']
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: {
        rotate: 45,
        interval: 0
      }
    },
    yAxis: {
      type: 'value',
      name: 'AP',
      max: 1,
      axisLabel: { formatter: '{value}' }
    },
    series: [
      {
        name: '优化前',
        type: 'bar',
        data: originalData,
        itemStyle: { color: '#909399' }
      },
      {
        name: '优化后',
        type: 'bar',
        data: finalData,
        itemStyle: { color: '#67c23a' }
      }
    ]
  };

  mapComparisonChartInstance.setOption(option);
};

// 加载执行结果 - 直接使用模拟数据
const loadExecutionResult = async () => {
  // 使用模拟数据 - 与前面步骤对应
  executionResult.value = {
    originalMap: 61.8,
    finalMap: 70.8,
    actualImprovement: 9.0,
    categoryAPComparison: [
      { category: '行人', originalAP: 0.42, finalAP: 0.62, improvement: 0.20 },
      { category: '骑车人', originalAP: 0.46, finalAP: 0.63, improvement: 0.17 },
      { category: '语音指令', originalAP: 0.48, finalAP: 0.64, improvement: 0.16 },
      { category: '文本描述', originalAP: 0.44, finalAP: 0.60, improvement: 0.16 },
      { category: '交通标志', originalAP: 0.49, finalAP: 0.66, improvement: 0.17 },
    ],
  };
  executionCompleted.value = true;

  setTimeout(() => {
    initMapComparisonChart();
  }, 100);
};

const handleExecute = async () => {
  executing.value = true;

  // 模拟执行过程
  await new Promise(resolve => setTimeout(resolve, 2000));

  executing.value = false;
  ElMessage.success('训练任务已触发！');

  // 加载执行结果
  await loadExecutionResult();

  emit('next');
};

onMounted(() => {
  // 响应式调整图表大小
  const resizeHandler = () => {
    mapComparisonChartInstance?.resize();
  };
  window.addEventListener('resize', resizeHandler);
});

onUnmounted(() => {
  mapComparisonChartInstance?.dispose();
});
</script>

<style scoped lang="scss">
.execution-confirm {
  .summary-card {
    :deep(.el-card__header) {
      font-weight: 600;
      font-size: 16px;
    }
  }

  .resource-card,
  .performance-card {
    height: 100%;

    .resource-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 0;
      border-bottom: 1px solid #ebeef5;

      &:last-child {
        border-bottom: none;
      }

      .el-icon {
        font-size: 24px;
        color: #409eff;
      }
    }

    .improvement {
      margin-top: 12px;
      display: flex;
      align-items: center;
    }
  }

  .process-card {
    .process-item {
      text-align: center;

      h4 {
        margin-bottom: 12px;
        color: #303133;
      }

      .process-status {
        margin: 8px 0;
        color: #909399;
        font-size: 14px;
      }
    }
  }

  .result-comparison-card {
    .comparison-header {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 16px;
      font-weight: 600;
    }

    :deep(.el-statistic__head) {
      font-weight: 600;
      color: #606266;
    }

    :deep(.el-statistic__content) {
      font-size: 28px;
      font-weight: 600;
      color: #303133;
    }
  }

  .output-card {
    .output-actions {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .action-buttons {
        display: flex;
        gap: 12px;
      }
    }
  }
}
</style>

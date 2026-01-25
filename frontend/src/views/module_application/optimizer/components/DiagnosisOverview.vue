<template>
  <div class="diagnosis-overview">
    <!-- 数据集基本信息 -->
    <el-card v-if="datasetInfo.id" class="dataset-info-card" shadow="never" style="margin-bottom: 16px;">
      <div class="dataset-header">
        <h2>{{ datasetInfo.name }}</h2>
        <el-tag :type="getDataTypeColor(datasetInfo.dataType)">
          {{ getDataTypeLabel(datasetInfo.dataType) }}
        </el-tag>
      </div>
      <el-descriptions :column="4" border size="small">
        <el-descriptions-item label="样本总数">
          {{ datasetInfo.sampleCount }}
        </el-descriptions-item>
        <el-descriptions-item label="当前 mAP">
          <span class="map-value">{{ modelEvaluation.currentMap }}%</span>
        </el-descriptions-item>
        <el-descriptions-item label="类别数">
          {{ modelEvaluation.categories?.length || 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="低 AP 类别">
          <el-tag type="danger" size="small">{{ lowAPCategories.length }} 个</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 数据缺陷分析和 AP 分布 -->
    <el-row :gutter="16">
      <!-- 左侧:数据缺陷分布饼图 -->
      <el-col :span="10">
        <el-card shadow="never" style="height: 400px;">
          <template #header>
            <div class="panel-header">
              <el-icon><PieChart /></el-icon>
              <span>数据缺陷分布</span>
            </div>
          </template>
          <div ref="chartRef" style="height: 320px; width: 100%;"></div>
        </el-card>
      </el-col>

      <!-- 右侧:AP 分布柱状图 -->
      <el-col :span="14">
        <el-card shadow="never" style="height: 400px;">
          <template #header>
            <span>类别 AP 分布</span>
          </template>
          <div ref="apChartRef" style="height: 320px; width: 100%;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 底部操作按钮 -->
    <div class="footer-actions">
      <el-button type="primary" @click="handleNext" size="large">
        前往策略配置
        <el-icon class="el-icon--right"><ArrowRight /></el-icon>
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import {
  PieChart,
  ArrowRight
} from '@element-plus/icons-vue';
import * as echarts from 'echarts';
import OptimizerAPI from '@/api/module_application/optimizer';
import type { DatasetInfo, ModelEvaluationDetail, CategoryAP } from '@/types/optimizer';
import { getDataTypeLabel, getDataTypeColor } from '@/utils/dataTypeUtils';

const route = useRoute();

const emit = defineEmits<{
  next: [data: any];
}>();

const chartRef = ref<HTMLElement>();
const apChartRef = ref<HTMLElement>();
let chartInstance: echarts.ECharts | null = null;
let apChartInstance: echarts.ECharts | null = null;

// 数据集信息 - 使用假数据
const datasetId = ref<string>('dataset_001');
const datasetInfo = ref<DatasetInfo>({
  id: 'dataset_001',
  name: '自动驾驶目标检测数据集',
  dataType: 'multimodal',
  sampleCount: 15000,
  currentMap: 72.5,
  status: 'pending',
  createdAt: '2026-01-15',
  updatedAt: '2026-01-19',
});

// 模型评估结果 - 使用假数据
const modelEvaluation = ref<ModelEvaluationDetail>({
  currentMap: 61.8,
  categories: [
    { name: '行人', ap: 0.42, dataTypes: ['image'] },
    { name: '骑车人', ap: 0.46, dataTypes: ['image', 'video'] },
    { name: '语音指令', ap: 0.48, dataTypes: ['audio'] },
    { name: '文本描述', ap: 0.44, dataTypes: ['text'] },
    { name: '交通标志', ap: 0.49, dataTypes: ['image'] },
    { name: '汽车', ap: 0.78, dataTypes: ['image'] },
    { name: '卡车', ap: 0.82, dataTypes: ['image'] },
    { name: '交通灯', ap: 0.71, dataTypes: ['image'] },
  ],
  lowAPCategories: [
    { name: '行人', ap: 0.42, dataTypes: ['image'] },
    { name: '骑车人', ap: 0.46, dataTypes: ['image', 'video'] },
    { name: '语音指令', ap: 0.48, dataTypes: ['audio'] },
    { name: '文本描述', ap: 0.44, dataTypes: ['text'] },
    { name: '交通标志', ap: 0.49, dataTypes: ['image'] },
  ],
});

// 低 AP 类别列表
const lowAPCategories = computed(() => modelEvaluation.value.lowAPCategories || []);

// 建议补充的数据类型
const suggestedDataTypes = computed(() => {
  const types = new Set<string>();
  lowAPCategories.value.forEach(cat => {
    cat.dataTypes?.forEach(type => types.add(type));
  });
  return Array.from(types);
});

// 初始化 AP 柱状图
const initAPChart = () => {
  if (!apChartRef.value || modelEvaluation.value.categories.length === 0) return;

  apChartInstance = echarts.init(apChartRef.value);

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: modelEvaluation.value.categories.map(c => c.name),
      axisLabel: {
        rotate: 30,
        interval: 0,
        fontSize: 11
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
        name: 'AP 值',
        type: 'bar',
        data: modelEvaluation.value.categories.map(c => ({
          value: c.ap,
          itemStyle: {
            color: c.ap < 0.5 ? '#f56c6c' : '#67c23a'
          }
        })),
        markLine: {
          data: [{ yAxis: 0.5, label: { formatter: 'AP 阈值 0.5' } }],
          lineStyle: { color: '#e6a23c', type: 'dashed', width: 2 }
        }
      }
    ]
  };

  apChartInstance.setOption(option);
};

// 初始化图表
const initChart = () => {
  try {
    if (!chartRef.value) {
      console.warn('图表容器未找到');
      return;
    }

    chartInstance = echarts.init(chartRef.value);

    const option = {
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c}% ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        data: ['标注错误', '分布偏移', '对抗脆弱']
      },
      series: [
        {
          name: '缺陷类型',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 20,
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: false
          },
          data: [
            { value: 40, name: '标注错误', itemStyle: { color: '#f56c6c' } },
            { value: 35, name: '分布偏移', itemStyle: { color: '#e6a23c' } },
            { value: 25, name: '对抗脆弱', itemStyle: { color: '#409eff' } }
          ]
        }
      ]
    };

    chartInstance.setOption(option);
  } catch (error) {
    console.error('图表初始化失败:', error);
  }
};

const handleNext = () => {
  emit('next', {
    datasetId: datasetId.value,
    datasetInfo: datasetInfo.value,
    modelEvaluation: modelEvaluation.value,
    lowAPCategories: lowAPCategories.value,
  });
  ElMessage.success('进入策略配置');
};

onMounted(async () => {
  // 直接使用假数据,初始化图表
  setTimeout(() => {
    initChart();
    initAPChart();
  }, 100);

  // 响应式调整图表大小
  const resizeHandler = () => {
    chartInstance?.resize();
    apChartInstance?.resize();
  };
  window.addEventListener('resize', resizeHandler);
});

onUnmounted(() => {
  chartInstance?.dispose();
  apChartInstance?.dispose();
});
</script>

<style scoped lang="scss">
.diagnosis-overview {
  .dataset-info-card {
    .dataset-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;

      h2 {
        margin: 0;
        font-size: 20px;
        font-weight: 600;
        color: #303133;
      }
    }

    .map-value {
      font-size: 18px;
      font-weight: 600;
      color: #409eff;
    }
  }

  .panel-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 600;
  }

  .footer-actions {
    margin-top: 20px;
    text-align: center;
  }
}
</style>

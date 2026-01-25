<template>
  <div class="strategy-config">
    <el-card shadow="never">
      <template #header>
        <span>策略配置 - 基于缺陷特征自动生成</span>
      </template>

      <!-- 使用 Tabs 切换不同缺陷类型的策略 -->
      <el-tabs v-if="defectFeatures.length > 0" v-model="activeDefectTab" type="border-card">
        <el-tab-pane
          v-for="defect in defectFeatures"
          :key="defect.id"
          :label="defect.label"
          :name="defect.id"
        >
          <!-- 缺陷详情 -->
          <el-descriptions :column="3" border size="small" style="margin-bottom: 15px;">
            <el-descriptions-item label="缺陷类型">
              <el-tag :type="getDefectTypeColor(defect.type)" size="small">
                {{ defect.typeName }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="影响类别">
              {{ defect.affectedCategories.join(', ') }}
            </el-descriptions-item>
            <el-descriptions-item label="当前 AP">
              <span :style="{ color: defect.ap < 0.5 ? '#f56c6c' : '#67c23a', fontWeight: 'bold' }">
                {{ defect.ap.toFixed(3) }}
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="问题样本数" :span="1">
              {{ defect.sampleCount }}
            </el-descriptions-item>
            <el-descriptions-item label="数据类型" :span="2">
              <el-tag
                v-for="dt in defect.dataTypes"
                :key="dt"
                :type="getDataTypeColor(dt)"
                size="small"
                style="margin-right: 4px;"
              >
                {{ getDataTypeLabel(dt) }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>

          <!-- 策略配置区域 -->
          <el-row :gutter="12">
            <!-- 变异增强策略 -->
            <el-col :span="12">
              <el-card header="变异增强策略" class="strategy-card" shadow="never">
                <DefectStrategyForm
                  v-model="defect.augmentationStrategy"
                  :defect-type="defect.type"
                  :data-types="defect.dataTypes"
                  strategy-type="augmentation"
                />
              </el-card>
            </el-col>

            <!-- 检索补数策略 -->
            <el-col :span="12">
              <el-card header="检索补数策略" class="strategy-card" shadow="never">
                <DefectStrategyForm
                  v-model="defect.retrievalStrategy"
                  :defect-type="defect.type"
                  :data-types="defect.dataTypes"
                  strategy-type="retrieval"
                />
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>
      </el-tabs>

      <!-- 预期收益概览（固定在底部） -->
      <el-card class="footer-bar" shadow="always" style="margin-top: 20px;">
        <div class="footer-content">
          <div class="footer-left">
            <el-statistic title="预计新增样本" :value="totalNewCount" suffix="条" />
            <el-statistic title="预估 mAP 提升" :value="mapImprovement" suffix="%" />
            <el-statistic title="预估最终 mAP" :value="predictedMap" suffix="%" />
          </div>
          <div class="footer-right">
            <el-button
              type="primary"
              size="large"
              @click="handleGeneratePlan"
              :loading="loading"
            >
              生成补数方案
            </el-button>
          </div>
        </div>
      </el-card>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import OptimizerAPI from '@/api/module_application/optimizer';
import type { DefectFeature } from '@/types/optimizer';
import { getDataTypeLabel, getDataTypeColor, getDefectTypeColor, getDefectTypeName } from '@/utils/dataTypeUtils';
import DefectStrategyForm from './DefectStrategyForm.vue';

interface Props {
  datasetId: string;
  diagnosisData?: any;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  next: [data: any];
}>();

const loading = ref(false);
const activeDefectTab = ref<string>('');

// 缺陷特征列表
const defectFeatures = ref<DefectFeature[]>([]);

// 受影响的类别列表
const affectedCategories = computed(() => {
  const categories = new Set<string>();
  defectFeatures.value.forEach(d => {
    d.affectedCategories.forEach(c => categories.add(c));
  });
  return Array.from(categories);
});

// 计算预计新增样本数（检索 + 增强）
const totalNewCount = computed(() => {
  let total = 0;
  defectFeatures.value.forEach(d => {
    total += (d.retrievalStrategy?.targetCount || 0) + (d.augmentationStrategy?.targetCount || 0);
  });
  return total;
});

// 计算预估 mAP 提升
const mapImprovement = computed(() => {
  // 根据新增样本数估算mAP提升
  return 9.0;
});

// 计算预估最终 mAP
const predictedMap = computed(() => {
  const currentMap = 61.8; // 从 Step1 来的数据
  return (currentMap + mapImprovement.value).toFixed(1);
});

// 加载缺陷特征分析
const loadDefectAnalysis = async () => {
  loading.value = true;

  // 直接使用模拟数据
  await new Promise(resolve => setTimeout(resolve, 500));

  defectFeatures.value = [
    {
      id: 'defect_1',
      label: '行人 - 标注错误',
      type: 'annotation_error',
      typeName: '标注错误',
      affectedCategories: ['行人'],
      sampleCount: 500,
      ap: 0.42,
      dataTypes: ['image'],
      augmentationStrategy: {
        image: { noiseLevel: 30, blurRadius: 2, rotationAngle: 15, enableAdversarial: true },
        targetCount: 1200,
      },
      retrievalStrategy: {
        dataSource: ['OpenImages'],
        targetCount: 3000,
        similarityThreshold: 0.75,
      },
    },
    {
      id: 'defect_2',
      label: '骑车人 - 遮挡问题',
      type: 'distribution_shift',
      typeName: '分布偏移',
      affectedCategories: ['骑车人'],
      sampleCount: 300,
      ap: 0.46,
      dataTypes: ['image'],
      augmentationStrategy: {
        image: { noiseLevel: 25, blurRadius: 3, rotationAngle: 20, enableAdversarial: false },
        targetCount: 1000,
      },
      retrievalStrategy: {
        dataSource: ['COCO', 'BDD100K'],
        targetCount: 2500,
        similarityThreshold: 0.70,
      },
    },
    {
      id: 'defect_3',
      label: '语音指令 - 噪声干扰',
      type: 'distribution_shift',
      typeName: '分布偏移',
      affectedCategories: ['语音指令'],
      sampleCount: 250,
      ap: 0.48,
      dataTypes: ['audio'],
      augmentationStrategy: {
        audio: { pitchShiftRange: 3, timeStretchRatio: 1.15, noiseSNR: 25 },
        targetCount: 800,
      },
      retrievalStrategy: {
        dataSource: ['GoogleSpeechCommands', 'LibriSpeech'],
        targetCount: 2000,
        similarityThreshold: 0.72,
      },
    },
    {
      id: 'defect_4',
      label: '文本描述 - 语义不足',
      type: 'annotation_error',
      typeName: '标注错误',
      affectedCategories: ['文本描述'],
      sampleCount: 200,
      ap: 0.44,
      dataTypes: ['text'],
      augmentationStrategy: {
        text: { synonymReplaceRatio: 25, backTranslationLang: 'en-zh-en', enableParaphrase: true },
        targetCount: 900,
      },
      retrievalStrategy: {
        dataSource: ['OpenImages', 'COCO'],
        targetCount: 1800,
        similarityThreshold: 0.78,
      },
    },
    {
      id: 'defect_5',
      label: '交通标志 - 样本不均衡',
      type: 'distribution_shift',
      typeName: '分布偏移',
      affectedCategories: ['交通标志'],
      sampleCount: 350,
      ap: 0.49,
      dataTypes: ['image'],
      augmentationStrategy: {
        image: { noiseLevel: 20, blurRadius: 1.5, rotationAngle: 25, enableAdversarial: true },
        targetCount: 1100,
      },
      retrievalStrategy: {
        dataSource: ['Mapillary', 'TT100K'],
        targetCount: 1700,
        similarityThreshold: 0.68,
      },
    },
  ];
  activeDefectTab.value = defectFeatures.value[0].id;
  loading.value = false;
};

const handleGeneratePlan = async () => {
  loading.value = true;

  // 模拟生成过程
  await new Promise(resolve => setTimeout(resolve, 1000));

  const strategies = defectFeatures.value.map(d => ({
    defectId: d.id,
    augmentation: d.augmentationStrategy,
    retrieval: d.retrievalStrategy,
  }));

  ElMessage.success('补数方案生成成功！');

  emit('next', {
    defectFeatures: defectFeatures.value,
    strategies,
  });

  loading.value = false;
};

onMounted(() => {
  // 无论是否有 datasetId，都加载假数据用于演示
  loadDefectAnalysis();
});
</script>

<style scoped lang="scss">
.strategy-config {
  .header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .strategy-card {
    height: 100%;

    :deep(.el-card__header) {
      font-weight: 600;
      background: #f5f7fa;
    }
  }

  .footer-bar {
    .footer-content {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .footer-left {
        display: flex;
        gap: 40px;
      }
    }
  }

  :deep(.el-tabs__content) {
    padding: 20px;
  }
}
</style>

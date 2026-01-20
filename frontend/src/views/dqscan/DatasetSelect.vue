<template>
  <div class="dataset-select-container">
    <el-card shadow="never">
      <template #header>
        <div class="header-row">
          <span class="header-title">选择多模态数据集</span>
        </div>
      </template>

      <!-- 筛选栏 -->
      <div class="filter-bar">
        <el-select v-model="filters.dataType" placeholder="数据类型" style="width: 150px;">
          <el-option label="全部" value="all" />
          <el-option label="图片" value="image" />
          <el-option label="文本" value="text" />
          <el-option label="音频" value="audio" />
          <el-option label="多模态混合" value="multimodal" />
        </el-select>
        <el-select v-model="filters.status" placeholder="状态" style="width: 150px;">
          <el-option label="全部" value="all" />
          <el-option label="待优化" value="pending" />
          <el-option label="优化中" value="in_progress" />
          <el-option label="已完成" value="completed" />
        </el-select>
        <el-input
          v-model="searchKeyword"
          placeholder="搜索数据集名称"
          style="width: 300px;"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <!-- 数据集网格 -->
      <div v-loading="loading">
        <el-empty v-if="filteredDatasets.length === 0" description="暂无数据集" />
        <el-row v-else :gutter="20" style="margin-top: 20px;">
          <el-col
            :span="8"
            v-for="dataset in paginatedDatasets"
            :key="dataset.id"
            style="margin-bottom: 20px;"
          >
            <el-card
              class="dataset-card"
              @click="handleSelectDataset(dataset)"
              shadow="hover"
              :body-style="{ padding: '20px' }"
            >
              <div class="dataset-info">
                <h3 class="dataset-name">{{ dataset.name }}</h3>
                <div class="dataset-tags">
                  <el-tag :type="getDataTypeColor(dataset.dataType)" size="small">
                    {{ getDataTypeLabel(dataset.dataType) }}
                  </el-tag>
                  <el-tag :type="getStatusColor(dataset.status)" size="small">
                    {{ getStatusLabel(dataset.status) }}
                  </el-tag>
                </div>
                <div class="dataset-meta">
                  <div class="meta-item">
                    <span class="label">样本数:</span>
                    <span class="value">{{ dataset.sampleCount }}</span>
                  </div>
                  <div class="meta-item">
                    <span class="label">当前 mAP:</span>
                    <span class="value">{{ dataset.currentMap }}%</span>
                  </div>
                  <div class="meta-item">
                    <span class="label">更新时间:</span>
                    <span class="value">{{ formatDate(dataset.updatedAt) }}</span>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 分页 -->
        <el-pagination
          v-if="filteredDatasets.length > 0"
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="filteredDatasets.length"
          :page-sizes="[6, 12, 24, 48]"
          layout="total, sizes, prev, pager, next, jumper"
          style="margin-top: 20px; justify-content: center;"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Search } from '@element-plus/icons-vue';
import OptimizerAPI from '@/api/module_optimizer/optimizer';
import type { DatasetInfo } from '@/types/optimizer';
import { getDataTypeLabel, getDataTypeColor } from '@/utils/dataTypeUtils';

const router = useRouter();

const loading = ref(false);
const searchKeyword = ref('');
const currentPage = ref(1);
const pageSize = ref(6);

// 筛选条件
const filters = ref({
  dataType: 'all',
  status: 'all',
});

// 数据集列表
const datasets = ref<DatasetInfo[]>([]);

// 过滤后的数据集
const filteredDatasets = computed(() => {
  let result = datasets.value;

  // 按数据类型筛选
  if (filters.value.dataType !== 'all') {
    result = result.filter(d => d.dataType === filters.value.dataType);
  }

  // 按状态筛选
  if (filters.value.status !== 'all') {
    result = result.filter(d => d.status === filters.value.status);
  }

  // 按名称搜索
  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.trim().toLowerCase();
    result = result.filter(d => d.name.toLowerCase().includes(keyword));
  }

  return result;
});

// 分页后的数据集
const paginatedDatasets = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  const end = start + pageSize.value;
  return filteredDatasets.value.slice(start, end);
});

// 获取状态标签颜色
const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    pending: 'warning',
    in_progress: 'primary',
    completed: 'success',
  };
  return colorMap[status] || 'info';
};

// 获取状态标签文本
const getStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    pending: '待优化',
    in_progress: '优化中',
    completed: '已完成',
  };
  return labelMap[status] || status;
};

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleDateString('zh-CN');
};

// 加载数据集列表
const loadDatasets = async () => {
  loading.value = true;
  try {
    // 模拟 API 调用
    await new Promise(resolve => setTimeout(resolve, 500));

    // 使用假数据
    datasets.value = [
      {
        id: 'dataset_001',
        name: '自动驾驶目标检测数据集',
        dataType: 'multimodal',
        status: 'pending',
        sampleCount: 15000,
        currentMap: 61.8,
        description: '城市道路场景下的车辆、行人、交通标志检测',
        createdAt: '2026-01-08T13:45:00',
        updatedAt: '2026-01-17T11:30:00',
      },
      {
        id: 'dataset_002',
        name: 'COCO目标检测数据集',
        dataType: 'multimodal',
        status: 'pending',
        sampleCount: 120000,
        currentMap: 65.4,
        description: '包含80类物体的通用目标检测数据集',
        createdAt: '2026-01-08T13:45:00',
        updatedAt: '2026-01-17T11:30:00',
      },
      {
        id: 'dataset_003',
        name: 'ImageNet图像分类数据集',
        dataType: 'multimodal',
        status: 'pending',
        sampleCount: 1500000,
        currentMap: 72.8,
        description: '大规模图像分类数据集',
        createdAt: '2026-01-08T13:45:00',
        updatedAt: '2026-01-17T11:30:00',
      },
      {
        id: 'dataset_004',
        name: 'LibriSpeech语音识别数据集',
        dataType: 'multimodal',
        status: 'pending',
        sampleCount: 98000,
        currentMap: 58.2,
        description: '英语语音识别和语音合成数据集',
        createdAt: '2026-01-08T13:45:00',
        updatedAt: '2026-01-17T11:30:00',
      },
      {
        id: 'dataset_005',
        name: 'SNLI文本推理数据集',
        dataType: 'multimodal',
        status: 'pending',
        sampleCount: 570000,
        currentMap: 68.5,
        description: '自然语言推理数据集',
        createdAt: '2026-01-08T13:45:00',
        updatedAt: '2026-01-17T11:30:00',
      },
      {
        id: 'dataset_006',
        name: 'YouTube-BBM视频动作识别数据集',
        dataType: 'multimodal',
        status: 'pending',
        sampleCount: 45000,
        currentMap: 62.1,
        description: '多模态视频动作识别数据集',
        createdAt: '2026-01-08T13:45:00',
        updatedAt: '2026-01-17T11:30:00',
      },
      {
        id: 'dataset_007',
        name: 'nuScenes自动驾驶数据集',
        dataType: 'multimodal',
        status: 'pending',
        sampleCount: 15000,
        currentMap: 55.8,
        description: '多传感器自动驾驶数据集',
        createdAt: '2026-01-08T13:45:00',
        updatedAt: '2026-01-17T11:30:00',
      },
    ];

    loading.value = false;
  } catch (error) {
    console.error('加载数据集失败:', error);
    ElMessage.error('加载数据集失败');
    loading.value = false;
  }
};

// 选择数据集
const handleSelectDataset = (dataset: DatasetInfo) => {
  if (dataset.status === 'in_progress') {
    ElMessage.warning('该数据集正在优化中,请稍后再试');
    return;
  }

  // 跳转到诊断页面,携带数据集 ID
  router.push({
    name: 'DQScan',
    query: { datasetId: dataset.id }
  });
};

onMounted(() => {
  loadDatasets();
});
</script>

<style scoped lang="scss">
.dataset-select-container {
  padding: 20px;

  .header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-title {
      font-size: 18px;
      font-weight: 600;
    }
  }

  .filter-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
    flex-wrap: wrap;
  }

  .dataset-card {
    cursor: pointer;
    transition: transform 0.2s;

    &:hover {
      transform: translateY(-4px);
    }

    .dataset-info {
      .dataset-name {
        font-size: 16px;
        font-weight: 600;
        margin: 0 0 12px 0;
        color: #303133;
      }

      .dataset-tags {
        display: flex;
        gap: 8px;
        margin-bottom: 16px;
      }

      .dataset-meta {
        display: flex;
        flex-direction: column;
        gap: 8px;

        .meta-item {
          display: flex;
          justify-content: space-between;
          font-size: 14px;

          .label {
            color: #909399;
          }

          .value {
            font-weight: 500;
            color: #303133;
          }
        }
      }
    }
  }
}
</style>

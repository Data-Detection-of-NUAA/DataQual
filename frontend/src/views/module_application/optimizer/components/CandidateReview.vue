<template>
  <div class="candidate-review">
    <el-card shadow="never">
      <template #header>
        <span>补数审核 - 方案列表</span>
      </template>

      <!-- 方案列表（折叠面板） -->
      <el-collapse v-model="activePlanIds">
        <el-collapse-item
          v-for="plan in augmentationPlans"
          :key="plan.id"
          :name="plan.id"
        >
          <template #title>
            <div class="plan-header">
              <span class="plan-title">{{ plan.title }}</span>
              <el-badge :value="plan.candidateCount" type="primary" style="margin-left: 12px;" />
              <div class="plan-actions" @click.stop>
                <el-button
                  :type="plan.status === 'accepted' ? 'success' : ''"
                  size="small"
                  @click="handleAcceptPlan(plan)"
                  :disabled="plan.status === 'accepted'"
                >
                  {{ plan.status === 'accepted' ? '✓ 已采纳' : '采纳方案' }}
                </el-button>
                <el-button
                  :type="plan.status === 'rejected' ? 'danger' : ''"
                  size="small"
                  @click="handleRejectPlan(plan)"
                  :disabled="plan.status === 'rejected'"
                >
                  {{ plan.status === 'rejected' ? '✗ 已拒绝' : '拒绝方案' }}
                </el-button>
              </div>
            </div>
          </template>

          <!-- 方案详情 -->
          <el-descriptions :column="2" border style="margin-bottom: 16px;">
            <el-descriptions-item label="缺陷类型">
              {{ plan.defectTypeName }}
            </el-descriptions-item>
            <el-descriptions-item label="目标类别">
              {{ plan.targetCategories.join(', ') }}
            </el-descriptions-item>
            <el-descriptions-item label="涉及数据类型">
              <el-tag
                v-for="dt in plan.dataTypes"
                :key="dt"
                :type="getDataTypeColor(dt)"
                size="small"
                style="margin-right: 4px;"
              >
                {{ getDataTypeLabel(dt) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="候选数据数量">
              {{ plan.candidateCount }} 条
            </el-descriptions-item>
          </el-descriptions>

          <!-- 该方案的候选样本列表 -->
          <el-divider content-position="left">候选样本列表</el-divider>

          <!-- 候选数据表格 -->
          <el-table
            :data="getPlanCandidates(plan.id)"
            style="width: 100%"
            @selection-change="(selection) => handlePlanSelectionChange(plan.id, selection)"
            max-height="400"
          >
            <el-table-column type="selection" width="55" />

            <el-table-column label="预览" width="120">
              <template #default="scope">
                <!-- 图片预览 -->
                <el-image
                  v-if="scope.row.dataType === 'image'"
                  :src="scope.row.thumbnail"
                  style="width: 80px; height: 60px"
                  fit="cover"
                  :preview-src-list="[scope.row.thumbnail]"
                  preview-teleported
                />
                <!-- 音频预览 -->
                <div v-else-if="scope.row.dataType === 'audio'" class="audio-preview">
                  <el-icon :size="32"><Microphone /></el-icon>
                  <span class="duration">{{ scope.row.duration }}</span>
                </div>
                <!-- 文本预览 -->
                <div v-else-if="scope.row.dataType === 'text'" class="text-preview">
                  <el-icon :size="32"><Document /></el-icon>
                  <span class="text-length">{{ scope.row.textLength }}字</span>
                </div>
              </template>
            </el-table-column>

            <el-table-column label="数据类型" width="100">
              <template #default="scope">
                <el-tag :type="getDataTypeColor(scope.row.dataType)" size="small">
                  {{ getDataTypeLabel(scope.row.dataType) }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column label="来源" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.source === 'retrieval' ? 'primary' : 'warning'">
                  {{ scope.row.source === 'retrieval' ? '🔵 检索' : '🟠 增强' }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column label="置信度" width="140">
              <template #default="scope">
                <el-progress :percentage="scope.row.confidence * 100" :stroke-width="8" />
              </template>
            </el-table-column>

            <el-table-column prop="description" label="详情描述" min-width="200" />

            <el-table-column label="操作" width="200" fixed="right">
              <template #default="scope">
                <el-button
                  size="small"
                  type="success"
                  @click="handleAccept(scope.row)"
                  :disabled="scope.row.status === 'accepted'"
                >
                  ✅ 采纳
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  @click="handleReject(scope.row)"
                  :disabled="scope.row.status === 'rejected'"
                >
                  ❌ 拒绝
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页控件 -->
          <el-pagination
            v-model:current-page="plan.currentPage"
            v-model:page-size="plan.pageSize"
            :total="getPlanCandidatesTotal(plan.id)"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next, jumper"
            style="margin-top: 16px; justify-content: center"
            @current-change="() => {}"
            @size-change="() => {}"
          />
        </el-collapse-item>
      </el-collapse>

      <!-- 底部操作 -->
      <div class="footer-actions" style="margin-top: 20px;">
        <el-statistic title="已采纳总数" :value="acceptedCount" suffix="条" style="display: inline-block; margin-right: 20px;" />
        <el-button type="primary" size="large" @click="handleNext" :disabled="acceptedCount === 0">
          下一步 (已采纳 {{ acceptedCount }} 条)
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Microphone, Document, VideoPlay, Picture, Headset } from '@element-plus/icons-vue';
import OptimizerAPI from '@/api/module_application/optimizer';
import type { AugmentationPlan } from '@/types/optimizer';
import { getDataTypeLabel, getDataTypeColor } from '@/utils/dataTypeUtils';

interface Props {
  datasetId: string;
  strategyConfig?: any;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  next: [data: any];
}>();

// 补数方案列表
const augmentationPlans = ref<any[]>([]);
const activePlanIds = ref<string[]>([]);

// 总候选数据数量
const totalCandidatesCount = computed(() => {
  return augmentationPlans.value.reduce((sum, plan) => sum + plan.candidateCount, 0);
});

// 已采纳方案数量
const acceptedPlansCount = computed(() => {
  return augmentationPlans.value.filter(p => p.status === 'accepted').length;
});

// 筛选条件
const filters = ref({
  source: 'all',
  dataType: 'all',
  confidence: 'all',
  category: 'all',
});

// 视图模式
const viewMode = ref('list');

// 分页
const currentPage = ref(1);
const pageSize = ref(12);

// 选择
const selectAll = ref(false);
const selectedIds = ref<string[]>([]);

// 候选样本数据 - 根据步骤2的策略动态生成
const candidates = ref<any[]>([]);

// 过滤后的候选数据
const filteredCandidates = computed(() => {
  let result = candidates.value;

  if (filters.value.source !== 'all') {
    result = result.filter(c => c.source === filters.value.source);
  }

  if (filters.value.dataType !== 'all') {
    result = result.filter(c => c.dataType === filters.value.dataType);
  }

  if (filters.value.confidence !== 'all') {
    result = result.filter(c => {
      if (filters.value.confidence === 'high') return c.confidence > 0.9;
      if (filters.value.confidence === 'medium') return c.confidence >= 0.7 && c.confidence <= 0.9;
      if (filters.value.confidence === 'low') return c.confidence < 0.7;
      return true;
    });
  }

  if (filters.value.category !== 'all') {
    result = result.filter(c => c.category === filters.value.category);
  }

  return result;
});

// 分页后的数据
const paginatedCandidates = computed(() => {
  return filteredCandidates.value.slice(
    (currentPage.value - 1) * pageSize.value,
    currentPage.value * pageSize.value
  );
});

// 已采纳数量
const acceptedCount = computed(() => {
  return candidates.value.filter(c => c.status === 'accepted').length;
});

// 获取指定方案的候选数据（带分页）
const getPlanCandidates = (planId: string) => {
  const plan = augmentationPlans.value.find(p => p.id === planId);
  if (!plan) return [];

  const planCandidates = candidates.value.filter(c => c.planId === planId);
  const currentPage = plan.currentPage || 1;
  const pageSize = plan.pageSize || 10;
  const start = (currentPage - 1) * pageSize;
  const end = start + pageSize;

  return planCandidates.slice(start, end);
};

// 获取指定方案的候选数据总数
const getPlanCandidatesTotal = (planId: string) => {
  return candidates.value.filter(c => c.planId === planId).length;
};

// 处理方案内的选择变化
const handlePlanSelectionChange = (planId: string, selection: any[]) => {
  // 可以在这里处理方案内的批量选择
  console.log(`Plan ${planId} selection:`, selection);
};

// 数据类型图标方法
const getDataTypeIcon = (type: string) => {
  const icons: Record<string, any> = {
    image: Picture,
    audio: Microphone,
    text: Document,
    video: VideoPlay,
  };
  return icons[type] || Document;
};

const getDataTypeIconColor = (type: string) => {
  const colors: Record<string, string> = {
    image: '#67c23a',
    audio: '#e6a23c',
    text: '#409eff',
    video: '#f56c6c',
  };
  return colors[type] || '#909399';
};

const handleSelectAll = (val: boolean) => {
  if (val) {
    selectedIds.value = paginatedCandidates.value.map(c => c.id);
  } else {
    selectedIds.value = [];
  }
};

const handleSelectionChange = (selection: any[]) => {
  selectedIds.value = selection.map(s => s.id);
};

const handleAccept = (row: any) => {
  row.status = 'accepted';
  ElMessage.success(`已采纳: ${row.description.substring(0, 30)}...`);
};

const handleReject = (row: any) => {
  row.status = 'rejected';
  ElMessage.warning(`已拒绝: ${row.description.substring(0, 30)}...`);
};

const batchAccept = () => {
  selectedIds.value.forEach(id => {
    const item = candidates.value.find(c => c.id === id);
    if (item) item.status = 'accepted';
  });
  ElMessage.success(`已批量采纳 ${selectedIds.value.length} 条数据`);
  selectedIds.value = [];
};

const batchReject = () => {
  selectedIds.value.forEach(id => {
    const item = candidates.value.find(c => c.id === id);
    if (item) item.status = 'rejected';
  });
  ElMessage.warning(`已批量拒绝 ${selectedIds.value.length} 条数据`);
  selectedIds.value = [];
};

const viewDetails = (row: any) => {
  ElMessageBox.alert(
    `
    <div style="text-align: left;">
      <p><strong>数据类型:</strong> ${getDataTypeLabel(row.dataType)}</p>
      <p><strong>来源:</strong> ${row.source === 'retrieval' ? '检索' : '增强'}</p>
      <p><strong>置信度:</strong> ${(row.confidence * 100).toFixed(1)}%</p>
      <p><strong>详细描述:</strong> ${row.description}</p>
      ${row.dataType === 'image' ? '<p><strong>缩略图:</strong></p><img src="' + row.thumbnail + '" style="width: 100%; max-width: 400px; border-radius: 4px;" />' : ''}
    </div>
    `,
    '数据详情',
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '关闭',
    }
  );
};

// 处理方案采纳
const handleAcceptPlan = async (plan: any) => {
  // 采纳该方案下的所有候选数据
  const planCandidates = candidates.value.filter(c => c.planId === plan.id);
  planCandidates.forEach(c => {
    c.status = 'accepted';
  });

  plan.status = 'accepted';
  ElMessage.success(`已采纳方案: ${plan.title}，共 ${planCandidates.length} 条数据`);
};

// 处理方案拒绝
const handleRejectPlan = async (plan: any) => {
  // 拒绝该方案下的所有候选数据
  const planCandidates = candidates.value.filter(c => c.planId === plan.id);
  planCandidates.forEach(c => {
    c.status = 'rejected';
  });

  plan.status = 'rejected';
  ElMessage.warning(`已拒绝方案: ${plan.title}，共 ${planCandidates.length} 条数据`);
};

// 加载补数方案列表
const loadAugmentationPlans = async () => {
  // 根据步骤2的策略配置动态生成候选方案
  if (!props.strategyConfig || !props.strategyConfig.defectFeatures) {
    // 如果没有策略配置，使用与 Step2 一致的默认模拟数据
    augmentationPlans.value = [
      {
        id: 'plan_1',
        title: '行人 - 标注错误 (变异增强+检索补数)',
        strategyType: 'mixed',
        defectTypeName: '标注错误',
        targetCategories: ['行人'],
        dataTypes: ['image'],
        candidateCount: 4200, // augmentation: 1200 + retrieval: 3000
        status: 'pending',
        filters: { dataType: 'all', confidence: 'all' },
        currentPage: 1,
        pageSize: 10,
      },
      {
        id: 'plan_2',
        title: '骑车人 - 遮挡问题 (变异增强+检索补数)',
        strategyType: 'mixed',
        defectTypeName: '分布偏移',
        targetCategories: ['骑车人'],
        dataTypes: ['image'],
        candidateCount: 3500, // augmentation: 1000 + retrieval: 2500
        status: 'pending',
        filters: { dataType: 'all', confidence: 'all' },
        currentPage: 1,
        pageSize: 10,
      },
      {
        id: 'plan_3',
        title: '语音指令 - 噪声干扰 (变异增强+检索补数)',
        strategyType: 'mixed',
        defectTypeName: '分布偏移',
        targetCategories: ['语音指令'],
        dataTypes: ['audio'],
        candidateCount: 2800, // augmentation: 800 + retrieval: 2000
        status: 'pending',
        filters: { dataType: 'all', confidence: 'all' },
        currentPage: 1,
        pageSize: 10,
      },
      {
        id: 'plan_4',
        title: '文本描述 - 语义不足 (变异增强+检索补数)',
        strategyType: 'mixed',
        defectTypeName: '标注错误',
        targetCategories: ['文本描述'],
        dataTypes: ['text'],
        candidateCount: 2700, // augmentation: 900 + retrieval: 1800
        status: 'pending',
        filters: { dataType: 'all', confidence: 'all' },
        currentPage: 1,
        pageSize: 10,
      },
      {
        id: 'plan_5',
        title: '交通标志 - 样本不均衡 (变异增强+检索补数)',
        strategyType: 'mixed',
        defectTypeName: '分布偏移',
        targetCategories: ['交通标志'],
        dataTypes: ['image'],
        candidateCount: 2800, // augmentation: 1100 + retrieval: 1700
        status: 'pending',
        filters: { dataType: 'all', confidence: 'all' },
        currentPage: 1,
        pageSize: 10,
      },
    ];
  } else {
    // 根据步骤2的策略配置动态生成
    augmentationPlans.value = props.strategyConfig.defectFeatures.map((defect: any, index: number) => {
      const augmentationCount = defect.augmentationStrategy?.targetCount || 0;
      const retrievalCount = defect.retrievalStrategy?.targetCount || 0;
      const totalCount = augmentationCount + retrievalCount;

      return {
        id: `plan_${index + 1}`,
        title: `${defect.label} (变异增强+检索补数)`,
        strategyType: 'mixed',
        defectTypeName: defect.typeName,
        targetCategories: defect.affectedCategories,
        dataTypes: defect.dataTypes,
        candidateCount: totalCount,
        status: 'pending',
        filters: { dataType: 'all', confidence: 'all' },
        currentPage: 1,
        pageSize: 10,
      };
    });
  }

  // 默认展开第一个方案
  if (augmentationPlans.value.length > 0) {
    activePlanIds.value = [augmentationPlans.value[0].id];
  }

  // 同时生成对应的候选样本数据
  generateCandidates();
};

// 根据补数方案生成候选样本数据
const generateCandidates = () => {
  const allCandidates: any[] = [];
  let globalId = 1;

  // 如果有步骤2的策略配置，根据策略生成候选样本
  if (props.strategyConfig && props.strategyConfig.defectFeatures) {
    props.strategyConfig.defectFeatures.forEach((defect: any) => {
      const category = defect.affectedCategories[0];
      const augStrategy = defect.augmentationStrategy;
      const retStrategy = defect.retrievalStrategy;

      // 生成增强样本
      const augCount = augStrategy?.targetCount || 0;
      for (let i = 0; i < Math.min(augCount, 6); i++) {
        allCandidates.push({
          id: `${globalId++}`,
          dataType: defect.dataTypes[0] || 'image',
          thumbnail: `https://picsum.photos/400/300?random=${globalId}`,
          source: 'augmentation',
          confidence: 0.85 + Math.random() * 0.14,
          description: `类别: ${category}; 增强方式: 旋转${augStrategy?.image?.rotationAngle || 15}度 + 噪声${augStrategy?.image?.noiseLevel || 30}`,
          status: 'pending',
          category: category.toLowerCase(),
          planId: defect.id,
        });
      }

      // 生成检索样本
      const retCount = retStrategy?.targetCount || 0;
      const sources = retStrategy?.dataSource || [];
      for (let i = 0; i < Math.min(retCount, 6); i++) {
        allCandidates.push({
          id: `${globalId++}`,
          dataType: defect.dataTypes[0] || 'image',
          thumbnail: `https://picsum.photos/400/300?random=${globalId}`,
          source: 'retrieval',
          confidence: 0.75 + Math.random() * 0.24,
          description: `类别: ${category}; 来源库: ${sources.join(', ')}; 相似度: ${(retStrategy?.similarityThreshold || 0.75).toFixed(2)}`,
          status: 'pending',
          category: category.toLowerCase(),
          planId: defect.id,
        });
      }
    });
  } else {
    // 如果没有策略配置，使用默认数据（与备份的augmentationPlans对应）
    augmentationPlans.value.forEach((plan) => {
      const { targetCategories, dataTypes, candidateCount } = plan;
      const category = targetCategories[0];

      // 根据 plan id 确定增强和检索的比例
      let augCount = 0;
      let retCount = 0;

      if (plan.id === 'plan_1') {
        augCount = 1200;
        retCount = 3000;
      } else if (plan.id === 'plan_2') {
        augCount = 1000;
        retCount = 2500;
      } else if (plan.id === 'plan_3') {
        augCount = 800;
        retCount = 2000;
      } else if (plan.id === 'plan_4') {
        augCount = 900;
        retCount = 1800;
      } else if (plan.id === 'plan_5') {
        augCount = 1100;
        retCount = 1700;
      }

      // 生成增强样本（显示部分示例）
      for (let i = 0; i < Math.min(augCount, 6); i++) {
        allCandidates.push({
          id: `${globalId++}`,
          dataType: dataTypes[0] || 'image',
          thumbnail: `https://picsum.photos/400/300?random=${globalId}`,
          source: 'augmentation',
          confidence: 0.85 + Math.random() * 0.14,
          description: `类别: ${category}; 增强方式: 旋转${Math.floor(Math.random() * 30)}度 + 噪声`,
          status: 'pending',
          category: category.toLowerCase(),
          planId: plan.id,
          duration: dataTypes[0] === 'audio' ? '3.2s' : undefined,
          textLength: dataTypes[0] === 'text' ? 120 : undefined,
        });
      }

      // 生成检索样本（显示部分示例）
      for (let i = 0; i < Math.min(retCount, 6); i++) {
        allCandidates.push({
          id: `${globalId++}`,
          dataType: dataTypes[0] || 'image',
          thumbnail: `https://picsum.photos/400/300?random=${globalId}`,
          source: 'retrieval',
          confidence: 0.75 + Math.random() * 0.24,
          description: `类别: ${category}; 来源库: ${['OpenImages', 'COCO', 'BDD100K'][Math.floor(Math.random() * 3)]}`,
          status: 'pending',
          category: category.toLowerCase(),
          planId: plan.id,
          duration: dataTypes[0] === 'audio' ? '2.8s' : undefined,
          textLength: dataTypes[0] === 'text' ? 95 : undefined,
        });
      }
    });
  }

  candidates.value = allCandidates;
};

const handleNext = () => {
  const acceptedIds = candidates.value
    .filter(c => c.status === 'accepted')
    .map(c => c.id);

  if (acceptedIds.length === 0) {
    ElMessage.warning('请至少采纳一条数据');
    return;
  }

  emit('next', acceptedIds);
  ElMessage.success(`已采纳 ${acceptedIds.length} 条数据，进入执行确认步骤`);
};

// 挂载时加载补数方案列表
onMounted(() => {
  // 无论是否有 datasetId，都加载假数据用于演示
  loadAugmentationPlans();
});
</script>

<style scoped lang="scss">
.candidate-review {
  .plan-header {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;

    .plan-title {
      font-weight: 600;
      color: #303133;
    }

    .plan-actions {
      margin-left: auto;
      display: flex;
      gap: 8px;
    }
  }

  .candidates-preview {
    padding: 12px;
    background: #f5f7fa;
    border-radius: 4px;
  }

  .filter-section {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  .filter-bar {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;

    .filter-left {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }
  }

  .batch-actions {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
    padding: 12px;
    background: #f5f7fa;
    border-radius: 4px;
    align-items: center;
  }

  .confidence-wrapper {
    display: flex;
    align-items: center;
    gap: 12px;

    .confidence-value {
      font-size: 12px;
      font-weight: 600;
      color: #409eff;
      min-width: 45px;
    }
  }

  .audio-preview,
  .text-preview,
  .video-preview {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;

    .duration,
    .text-length {
      font-size: 11px;
      color: #909399;
    }
  }

  .grid-view {
    .grid-card {
      margin-bottom: 16px;
      transition: all 0.3s;

      &:hover {
        transform: translateY(-4px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
      }

      .grid-item {
        .grid-preview {
          margin-bottom: 12px;

          .other-type {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 150px;
            background: #f5f7fa;
            border-radius: 4px;

            span {
              margin-top: 8px;
              font-size: 12px;
              color: #909399;
            }
          }
        }

        .grid-info {
          .grid-tags {
            display: flex;
            gap: 6px;
            margin-bottom: 8px;
          }

          .grid-confidence {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;

            .confidence-value {
              font-size: 12px;
              font-weight: 600;
              color: #409eff;
              min-width: 40px;
            }
          }

          .grid-description {
            font-size: 13px;
            color: #606266;
            line-height: 1.5;
            margin: 0 0 12px 0;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            height: 40px;
          }

          .grid-actions {
            display: flex;
            gap: 6px;
          }
        }
      }
    }
  }

  .footer-actions {
    margin-top: 20px;
    text-align: right;
  }
}
</style>

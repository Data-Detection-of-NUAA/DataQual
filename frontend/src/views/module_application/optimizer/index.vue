<template>
  <div class="dqscan-container">
    <!-- 顶部标题栏 -->
    <div class="header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="handleBack" text>返回</el-button>
        <span class="title">数据集缺陷优化工具</span>
      </div>
    </div>

    <!-- 步骤导航 - 只显示，不可点击 -->
    <el-card class="wizard-card" shadow="never">
      <el-steps :active="activeStep - 1" finish-status="success" align-center>
        <el-step title="诊断概览" description="Step 1" />
        <el-step title="策略配置" description="Step 2" />
        <el-step title="补数审核" description="Step 3" />
        <el-step title="执行确认" description="Step 4" />
      </el-steps>
    </el-card>

    <!-- 步骤内容 - 不使用 tabs，直接条件渲染 -->
    <div class="step-content">
      <el-card shadow="never">
        <!-- 顶部导航按钮 -->
        <div class="step-navigation">
          <el-button
            v-if="activeStep > 1"
            @click="handlePrevious"
            :icon="ArrowLeft"
          >
            上一步
          </el-button>
          <div class="step-info">
            <span class="current-step">当前步骤: {{ activeStep }}/4</span>
          </div>
        </div>

        <!-- 步骤内容区域 -->
        <div class="step-wrapper">
          <!-- Step 1: 诊断概览 -->
          <DiagnosisOverview
            v-show="activeStep === 1"
            @next="handleNext"
          />

          <!-- Step 2: 策略配置 -->
          <StrategyConfig
            v-show="activeStep === 2"
            :dataset-id="datasetId"
            :diagnosis-data="diagnosisData"
            @next="handleNext"
          />

          <!-- Step 3: 补数审核 -->
          <CandidateReview
            v-show="activeStep === 3"
            :dataset-id="datasetId"
            :strategy-config="strategyConfig"
            @next="handleNext"
          />

          <!-- Step 4: 执行确认 -->
          <ExecutionConfirm
            v-show="activeStep === 4"
            :dataset-id="datasetId"
            :strategy-config="strategyConfig"
            :accepted-ids="acceptedIds"
            @next="handleComplete"
          />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { ArrowLeft } from "@element-plus/icons-vue";
import { useRouter, useRoute } from "vue-router";

// 导入步骤组件
import DiagnosisOverview from "./components/DiagnosisOverview.vue";
import StrategyConfig from "./components/StrategyConfig.vue";
import CandidateReview from "./components/CandidateReview.vue";
import ExecutionConfirm from "./components/ExecutionConfirm.vue";
import { ElMessage } from "element-plus";

// 定义 props
interface Props {
  datasetId?: string;
}

const props = defineProps<Props>();

// 定义 emits
const emit = defineEmits<{
  back: [];
}>();

const router = useRouter();
const route = useRoute();

// 当前激活的步骤 (1-4)
const activeStep = ref(1);

// 数据集 ID - 优先使用 props，否则从路由获取
const datasetId = ref<string>(props.datasetId || '');

// 数据传递
const diagnosisData = ref<any>({});
const strategyConfig = ref({});
const acceptedIds = ref<string[]>([]);

// 前进到下一步
const handleNext = (data?: any) => {
  // 保存当前步骤的数据
  if (data) {
    if (activeStep.value === 1) {
      diagnosisData.value = data;
    } else if (activeStep.value === 2) {
      strategyConfig.value = data;
    } else if (activeStep.value === 3) {
      acceptedIds.value = data;
    }
  }

  // 前进到下一步
  if (activeStep.value < 4) {
    activeStep.value++;
    ElMessage.success(`已进入步骤 ${activeStep.value}`);
  }
};

// 返回上一步
const handlePrevious = () => {
  if (activeStep.value > 1) {
    activeStep.value--;
    ElMessage.info(`已返回步骤 ${activeStep.value}`);
  }
};

// 完成所有步骤
const handleComplete = () => {
  ElMessage.success('训练完毕！数据优化流程已执行。');
};

// 返回上一页
const handleBack = () => {
  // 如果是通过 props 传入的 datasetId，说明是嵌入在 DatasetSelect 中
  if (props.datasetId) {
    emit('back');
  } else {
    // 否则是通过路由访问的，使用路由返回
    router.back();
  }
};

// 初始化
onMounted(() => {
  // 如果没有通过 props 传入 datasetId，则从路由获取
  if (!props.datasetId) {
    datasetId.value = route.query.datasetId as string;
  }

  if (!datasetId.value) {
    ElMessage.warning('未选择数据集,请先选择数据集');
    // 可选：跳转回数据集选择页面
    // router.push('/dqscan/dataset-select');
  }
});
</script>

<style scoped lang="scss">
.dqscan-container {
  min-height: 100vh;
  background: #f5f7fa;

  .header {
    background: white;
    padding: 16px 24px;
    display: flex;
    align-items: center;
    border-bottom: 1px solid #dcdfe6;

    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;

      .title {
        font-size: 20px;
        font-weight: 500;
        color: #303133;
      }
    }
  }

  .wizard-card {
    margin: 20px;

    // 禁用 Steps 组件的点击事件
    :deep(.el-step) {
      cursor: default !important;

      .el-step__head {
        cursor: default !important;
      }
    }
  }

  .step-content {
    padding: 20px;

    .step-navigation {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 16px;
      border-bottom: 1px solid #ebeef5;
      margin-bottom: 20px;

      .step-info {
        .current-step {
          font-size: 14px;
          color: #909399;
          font-weight: 500;
        }
      }
    }

    .step-wrapper {
      min-height: 400px;
    }
  }
}
</style>

<!-- 训练监控页面 -->
<template>
  <div class="app-container train-monitor">
    <el-card shadow="hover">
      <!-- 任务基本信息 -->
      <div class="task-header">
        <div class="task-title">
          <h2>训练任务监控</h2>
          <el-tag :type="getStatusTagType(taskInfo?.status)" size="large">
            {{ getStatusText(taskInfo?.status) }}
          </el-tag>
        </div>
        <div class="task-id">任务ID: {{ taskId }}</div>
      </div>

      <!-- 任务详情 -->
      <el-descriptions v-if="taskInfo" :column="3" border class="task-details">
        <el-descriptions-item label="数据集">
          {{ taskInfo.dataset_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="模型">
          {{ taskInfo.model_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="当前轮次">
          {{ taskInfo.current_epoch }} / {{ taskInfo.total_epochs }}
        </el-descriptions-item>
        <el-descriptions-item label="开始时间">
          {{ formatDateTime(taskInfo.actual_start_time) }}
        </el-descriptions-item>
        <el-descriptions-item label="完成时间">
          {{ formatDateTime(taskInfo.actual_completion_time) }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- 训练进度 -->
      <div class="progress-section">
        <h3>训练进度</h3>
        <el-progress
          :percentage="taskInfo?.progress_percentage || 0"
          :status="getProgressStatus(taskInfo?.status)"
          :stroke-width="24"
          :striped="taskInfo?.status === 'running'"
          :striped-flow="taskInfo?.status === 'running'"
        />
        <div class="progress-info">
          <span>已完成: {{ taskInfo?.progress_percentage?.toFixed(2) || 0 }}%</span>
          <span v-if="latestProgress">
            当前损失: {{ latestProgress.train_loss?.toFixed(4) || '-' }}
          </span>
          <span v-if="latestProgress">
            当前准确率: {{ ((latestProgress.train_accuracy || 0) * 100).toFixed(2) }}%
          </span>
          <span v-if="latestProgress && latestProgress.val_loss !== undefined">
            验证损失: {{ latestProgress.val_loss?.toFixed(4) || '-' }}
          </span>
          <span v-if="latestProgress && latestProgress.val_accuracy !== undefined">
            验证准确率: {{ ((latestProgress.val_accuracy || 0) * 100).toFixed(2) }}%
          </span>
        </div>
      </div>

      <!-- 训练曲线 -->
      <div v-if="progressCurve" class="charts-section">
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="chart-card">
              <h4>损失曲线</h4>
              <div ref="lossChartRef" class="chart"></div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="chart-card">
              <h4>准确率曲线</h4>
              <div ref="accuracyChartRef" class="chart"></div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 实时日志 -->
      <div class="logs-section">
        <h3>实时日志</h3>
        <div class="log-container">
          <div v-for="(log, index) in logs" :key="index" class="log-item">
            <span class="log-time">{{ log.time }}</span>
            <span class="log-content">{{ log.message }}</span>
          </div>
          <div v-if="logs.length === 0" class="log-empty">
            暂无日志信息
          </div>
        </div>
      </div>

      <!-- 控制按钮 -->
      <div class="control-buttons">
        <el-button
          v-if="taskInfo?.status === 'running'"
          type="warning"
          @click="handlePause"
        >
          <el-icon><VideoPause /></el-icon>
          暂停训练
        </el-button>
        <el-button
          v-if="taskInfo?.status === 'paused'"
          type="primary"
          @click="handleResume"
        >
          <el-icon><VideoPlay /></el-icon>
          恢复训练
        </el-button>
        <el-button
          v-if="['running', 'pending', 'paused'].includes(taskInfo?.status || '')"
          type="danger"
          @click="handleCancel"
        >
          <el-icon><Close /></el-icon>
          取消训练
        </el-button>
        <el-button @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
        <!-- 如果训练完成且来自鲁棒性评估，显示继续评估按钮 -->
        <el-button
          v-if="taskInfo?.status === 'completed' && isFromRobustness"
          type="success"
          @click="handleContinueRobustness"
        >
          <el-icon><Right /></el-icon>
          继续鲁棒性评估
        </el-button>
        <el-button @click="handleBack">
          <el-icon><Back /></el-icon>
          返回列表
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  VideoPause,
  VideoPlay,
  Close,
  Refresh,
  Back,
  Right,
} from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import * as echarts from 'echarts';
import type { ECharts } from 'echarts';
import {
  TrainTaskAPI,
  type TrainTaskDetailInfo,
  type TrainProgressInfo,
  type TrainProgressCurveResponse,
} from '@/api/module_application/train';
import { formatToDateTime } from '@/utils/dateUtil';

defineOptions({
  name: 'TrainMonitor',
  inheritAttrs: false,
});

const route = useRoute();
const router = useRouter();

const taskId = ref(route.params.taskId as string);
const isFromRobustness = ref(route.query.from === 'robustness');
const taskInfo = ref<TrainTaskDetailInfo | null>(null);
const latestProgress = ref<TrainProgressInfo | null>(null);
const progressCurve = ref<TrainProgressCurveResponse | null>(null);
const logs = ref<Array<{ time: string; message: string }>>([]);

// 图表
const lossChartRef = ref<HTMLElement>();
const accuracyChartRef = ref<HTMLElement>();
let lossChart: ECharts | null = null;
let accuracyChart: ECharts | null = null;

// WebSocket
let ws: WebSocket | null = null;
let reconnectTimer: number | null = null;
let refreshTimer: number | null = null;

// 加载任务详情
async function loadTaskDetail() {
  try {
    const response = await TrainTaskAPI.getDetail(taskId.value);
    taskInfo.value = response.data.data;
  } catch (error: any) {
    ElMessage.error('加载任务详情失败: ' + (error.message || '未知错误'));
  }
}

// 加载最新进度
async function loadLatestProgress() {
  try {
    const response = await TrainTaskAPI.getLatestProgress(taskId.value);
    latestProgress.value = response.data.data;
  } catch (error: any) {
    console.error('加载最新进度失败:', error);
  }
}

// 加载进度曲线
async function loadProgressCurve() {
  try {
    const response = await TrainTaskAPI.getProgressCurve(taskId.value);
    progressCurve.value = response.data.data;
    await nextTick();
    initCharts();
  } catch (error: any) {
    console.error('加载进度曲线失败:', error);
  }
}

// 加载训练日志
async function loadLogs() {
  try {
    const response = await TrainTaskAPI.getLogs(taskId.value, 100);
    const logsData = response.data.data;
    if (logsData && logsData.logs) {
      logs.value = logsData.logs.map((log: any) => ({
        time: log.time,
        message: log.message
      }));
    }
  } catch (error: any) {
    console.error('加载训练日志失败:', error);
  }
}

// 初始化图表
function initCharts() {
  if (!progressCurve.value || !lossChartRef.value || !accuracyChartRef.value) return;

  const epochs = progressCurve.value.data_points.map((p) => p.epoch);
  const trainLoss = progressCurve.value.data_points.map((p) => p.train_loss);
  const valLoss = progressCurve.value.data_points.map((p) => p.val_loss);
  const trainAcc = progressCurve.value.data_points.map((p) =>
    p.train_accuracy ? p.train_accuracy * 100 : null
  );
  const valAcc = progressCurve.value.data_points.map((p) =>
    p.val_accuracy ? p.val_accuracy * 100 : null
  );

  // 损失曲线
  lossChart = echarts.init(lossChartRef.value);
  lossChart.setOption({
    tooltip: {
      trigger: 'axis',
    },
    legend: {
      data: ['训练损失', '验证损失'],
    },
    xAxis: {
      type: 'category',
      data: epochs,
      name: 'Epoch',
    },
    yAxis: {
      type: 'value',
      name: 'Loss',
    },
    series: [
      {
        name: '训练损失',
        type: 'line',
        data: trainLoss,
        smooth: true,
      },
      {
        name: '验证损失',
        type: 'line',
        data: valLoss,
        smooth: true,
      },
    ],
  });

  // 准确率曲线
  accuracyChart = echarts.init(accuracyChartRef.value);
  accuracyChart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: '{b}<br/>{a0}: {c0}%<br/>{a1}: {c1}%',
    },
    legend: {
      data: ['训练准确率', '验证准确率'],
    },
    xAxis: {
      type: 'category',
      data: epochs,
      name: 'Epoch',
    },
    yAxis: {
      type: 'value',
      name: 'Accuracy (%)',
      min: 0,
      max: 100,
    },
    series: [
      {
        name: '训练准确率',
        type: 'line',
        data: trainAcc,
        smooth: true,
      },
      {
        name: '验证准确率',
        type: 'line',
        data: valAcc,
        smooth: true,
      },
    ],
  });
}

// 初始化WebSocket
function initWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/train/ws/${taskId.value}`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('WebSocket connected');
    addLog('WebSocket连接成功');
    // 发送订阅消息
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'subscribe' }));
    }
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    addLog('WebSocket连接错误');
  };

  ws.onclose = () => {
    console.log('WebSocket closed');
    addLog('WebSocket连接已关闭');
    // 尝试重连
    reconnectTimer = window.setTimeout(() => {
      if (taskInfo.value?.status === 'running') {
        initWebSocket();
      }
    }, 5000);
  };
}

// 处理WebSocket消息
function handleWebSocketMessage(data: any) {
  if (data.type === 'progress') {
    latestProgress.value = data.data;
    if (taskInfo.value) {
      taskInfo.value.current_epoch = data.data.epoch;
      taskInfo.value.progress_percentage = data.data.overall_progress * 100;
    }
    // 更新图表
    loadProgressCurve();
  } else if (data.type === 'status') {
    if (taskInfo.value) {
      taskInfo.value.status = data.data.status;
    }
    addLog(`任务状态变更: ${getStatusText(data.data.status)}`);
  } else if (data.type === 'log') {
    addLog(data.data.message);
  }
}

// 添加日志
function addLog(message: string) {
  const time = new Date().toLocaleTimeString();
  logs.value.push({ time, message });
  // 保持最多100条日志
  if (logs.value.length > 100) {
    logs.value.shift();
  }
}

// 暂停任务
async function handlePause() {
  try {
    await ElMessageBox.confirm('确定要暂停该训练任务吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });

    await TrainTaskAPI.pause(taskId.value);
    ElMessage.success('任务已暂停');
    loadTaskDetail();
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('暂停失败: ' + (error.message || '未知错误'));
    }
  }
}

// 恢复任务
async function handleResume() {
  try {
    await TrainTaskAPI.resume(taskId.value);
    ElMessage.success('任务已恢复');
    loadTaskDetail();
  } catch (error: any) {
    ElMessage.error('恢复失败: ' + (error.message || '未知错误'));
  }
}

// 取消任务
async function handleCancel() {
  try {
    await ElMessageBox.confirm('确定要取消该训练任务吗？取消后无法恢复！', '警告', {
      confirmButtonText: '确定取消',
      cancelButtonText: '不取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger',
    });

    await TrainTaskAPI.cancel(taskId.value);
    ElMessage.success('任务已取消');
    loadTaskDetail();
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('取消失败: ' + (error.message || '未知错误'));
    }
  }
}

// 刷新数据
function handleRefresh() {
  loadTaskDetail();
  loadLatestProgress();
  loadProgressCurve();
  loadLogs();
}

// 返回列表
function handleBack() {
  router.push('/train/tasks');
}

// 继续鲁棒性评估
function handleContinueRobustness() {
  ElMessageBox.confirm(
    '训练已完成，是否继续进行鲁棒性评估？',
    '提示',
    {
      confirmButtonText: '继续评估',
      cancelButtonText: '稍后再说',
      type: 'success',
    }
  )
    .then(() => {
      // 返回到鲁棒性评估页面，并跳转到步骤3（鲁棒性评估策略与选择）
      router.push({
        path: '/robustness',
        query: { step: '2', taskId: taskId.value },
      });
    })
    .catch(() => {
      // 用户取消
    });
}

// 获取状态文本
function getStatusText(status: string | undefined): string {
  if (!status) return '-';
  const statusMap: Record<string, string> = {
    created: '已创建',
    pending: '等待中',
    running: '运行中',
    paused: '已暂停',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  };
  return statusMap[status] || status;
}

// 获取状态标签类型
function getStatusTagType(status: string | undefined): 'success' | 'info' | 'warning' | 'danger' | '' {
  if (!status) return '';
  const typeMap: Record<string, 'success' | 'info' | 'warning' | 'danger'> = {
    completed: 'success',
    running: 'info',
    pending: 'info',
    paused: 'warning',
    failed: 'danger',
    cancelled: 'danger',
    created: 'info',
  };
  return typeMap[status] || '';
}

// 获取进度状态
function getProgressStatus(status: string | undefined): 'success' | 'exception' | 'warning' | '' {
  if (!status) return '';
  if (status === 'completed') return 'success';
  if (status === 'failed' || status === 'cancelled') return 'exception';
  if (status === 'paused') return 'warning';
  return '';
}

// 格式化日期时间
function formatDateTime(dateStr: string | undefined): string {
  if (!dateStr) return '-';
  try {
    return formatToDateTime(dateStr, 'YYYY-MM-DD HH:mm:ss');
  } catch {
    return dateStr;
  }
}

// 初始化
onMounted(async () => {
  await loadTaskDetail();
  await loadLatestProgress();
  await loadProgressCurve();
  await loadLogs();

  // 如果任务正在运行，初始化WebSocket
  if (taskInfo.value?.status === 'running') {
    initWebSocket();
  }

  // 定时刷新数据
  refreshTimer = window.setInterval(() => {
    if (taskInfo.value?.status === 'running') {
      loadTaskDetail();
      loadLatestProgress();
      loadLogs(); // 定时刷新日志
    }
  }, 10000); // 每10秒刷新一次
});

// 清理
onUnmounted(() => {
  if (ws) {
    ws.close();
  }
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
  }
  if (refreshTimer) {
    clearInterval(refreshTimer);
  }
  if (lossChart) {
    lossChart.dispose();
  }
  if (accuracyChart) {
    accuracyChart.dispose();
  }
});
</script>

<style lang="scss" scoped>
.train-monitor {
  .task-header {
    margin-bottom: 24px;

    .task-title {
      display: flex;
      align-items: center;
      gap: 16px;
      margin-bottom: 8px;

      h2 {
        margin: 0;
        font-size: 24px;
        font-weight: 600;
      }
    }

    .task-id {
      font-size: 14px;
      color: var(--el-text-color-secondary);
    }
  }

  .task-details {
    margin-bottom: 24px;
  }

  .progress-section {
    margin-bottom: 24px;

    h3 {
      margin: 0 0 16px 0;
      font-size: 18px;
      font-weight: 600;
    }

    .progress-info {
      display: flex;
      justify-content: space-around;
      margin-top: 12px;
      font-size: 14px;
      color: var(--el-text-color-secondary);
    }
  }

  .charts-section {
    margin-bottom: 24px;

    .chart-card {
      padding: 16px;
      background: var(--el-bg-color);
      border: 1px solid var(--el-border-color);
      border-radius: 8px;

      h4 {
        margin: 0 0 16px 0;
        font-size: 16px;
        font-weight: 600;
      }

      .chart {
        width: 100%;
        height: 300px;
      }
    }
  }

  .logs-section {
    margin-bottom: 24px;

    h3 {
      margin: 0 0 16px 0;
      font-size: 18px;
      font-weight: 600;
    }

    .log-container {
      max-height: 300px;
      overflow-y: auto;
      padding: 12px;
      background: #1e1e1e;
      border-radius: 8px;
      font-family: 'Courier New', monospace;
      font-size: 13px;

      .log-item {
        display: flex;
        gap: 12px;
        margin-bottom: 4px;
        color: #d4d4d4;

        .log-time {
          color: #858585;
          flex-shrink: 0;
        }

        .log-content {
          flex: 1;
        }
      }

      .log-empty {
        text-align: center;
        color: #858585;
        padding: 20px;
      }
    }
  }

  .control-buttons {
    display: flex;
    gap: 12px;
    justify-content: center;
  }
}
</style>

<!-- 训练任务列表页面 -->
<template>
  <div class="app-container train-tasks">
    <el-card shadow="hover">
      <!-- 搜索和筛选 -->
      <el-form :inline="true" :model="queryForm" class="search-form">
        <el-form-item label="任务ID">
          <el-input
            v-model="queryForm.task_id"
            placeholder="请输入任务ID"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="任务状态">
          <el-select v-model="queryForm.status" placeholder="全部状态" clearable style="width: 150px">
            <el-option label="全部" value="" />
            <el-option label="已创建" value="created" />
            <el-option label="等待中" value="pending" />
            <el-option label="运行中" value="running" />
            <el-option label="已暂停" value="paused" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 操作按钮 -->
      <!-- <div class="toolbar">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          创建训练任务
        </el-button>
        <el-button
          type="danger"
          :disabled="selectedTasks.length === 0"
          @click="handleBatchDelete"
        >
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
      </div> -->

      <!-- 任务列表表格 -->
      <el-table
        v-loading="loading"
        :data="taskList"
        border
        stripe
      >
        <!-- <el-table-column type="selection" width="55" align="center" /> -->
        <el-table-column prop="task_id" label="任务ID" width="180" show-overflow-tooltip />
        <el-table-column prop="dataset_name" label="数据集" width="150" show-overflow-tooltip />
        <el-table-column prop="model_name" label="模型" width="150" show-overflow-tooltip />
        <el-table-column label="训练进度" width="200">
          <template #default="{ row }">
            <div class="progress-cell">
              <el-progress
                :percentage="row.progress_percentage"
                :status="getProgressStatus(row.status)"
                :stroke-width="16"
              />
              <span class="progress-text">
                {{ row.current_epoch }} / {{ row.total_epochs }} 轮
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_time" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="320" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              link
              @click="handleView(row.task_id)"
            >
              <el-icon><View /></el-icon>
              查看
            </el-button>
            <el-button
              v-if="row.status === 'completed' && row.model_save_path"
              size="small"
              type="success"
              link
              @click="handleDownloadModel(row)"
            >
              <el-icon><Download /></el-icon>
              下载模型
            </el-button>
            <el-button
              v-if="row.status === 'running'"
              size="small"
              type="warning"
              link
              @click="handlePause(row.task_id)"
            >
              <el-icon><VideoPause /></el-icon>
              暂停
            </el-button>
            <el-button
              v-if="row.status === 'paused'"
              size="small"
              type="success"
              link
              @click="handleResume(row.task_id)"
            >
              <el-icon><VideoPlay /></el-icon>
              恢复
            </el-button>
            <el-button
              v-if="['running', 'pending', 'paused'].includes(row.status)"
              size="small"
              type="danger"
              link
              @click="handleCancel(row.task_id)"
            >
              <el-icon><Close /></el-icon>
              取消
            </el-button>
            <el-button
              size="small"
              type="danger"
              link
              @click="handleDelete(row.task_id)"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="queryForm.page_no"
        v-model:page-size="queryForm.page_size"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleQuery"
        @current-change="handleQuery"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import {
  Search,
  Refresh,
  Plus,
  Delete,
  View,
  VideoPause,
  VideoPlay,
  Close,
  Download,
} from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { TrainTaskAPI, type TrainTaskInfo } from '@/api/module_application/train';
import { formatToDateTime } from '@/utils/dateUtil';

defineOptions({
  name: 'TrainTasks',
  inheritAttrs: false,
});

const router = useRouter();

// 查询表单
const queryForm = ref({
  page_no: 1,
  page_size: 10,
  task_id: '',
  status: '',
});

// 数据
const loading = ref(false);
const taskList = ref<TrainTaskInfo[]>([]);
const total = ref(0);
const selectedTasks = ref<TrainTaskInfo[]>([]);

// 加载任务列表
async function loadTasks() {
  loading.value = true;
  try {
    const response = await TrainTaskAPI.getList(queryForm.value);
    taskList.value = response.data.data.items;
    total.value = response.data.data.total;
  } catch (error: any) {
    ElMessage.error('加载任务列表失败: ' + (error.message || '未知错误'));
  } finally {
    loading.value = false;
  }
}

// 查询
function handleQuery() {
  queryForm.value.page_no = 1;
  loadTasks();
}

// 重置
function handleReset() {
  queryForm.value = {
    page_no: 1,
    page_size: 10,
    task_id: '',
    status: '',
  };
  loadTasks();
}

// 创建任务
function handleCreate() {
  router.push('/train');
}

// 查看任务
function handleView(taskId: string) {
  router.push(`/train/monitor/${taskId}`);
}

// 暂停任务
async function handlePause(taskId: string) {
  try {
    await ElMessageBox.confirm('确定要暂停该训练任务吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });

    await TrainTaskAPI.pause(taskId);
    ElMessage.success('任务已暂停');
    loadTasks();
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('暂停失败: ' + (error.message || '未知错误'));
    }
  }
}

// 恢复任务
async function handleResume(taskId: string) {
  try {
    await TrainTaskAPI.resume(taskId);
    ElMessage.success('任务已恢复');
    loadTasks();
  } catch (error: any) {
    ElMessage.error('恢复失败: ' + (error.message || '未知错误'));
  }
}

// 取消任务
async function handleCancel(taskId: string) {
  try {
    await ElMessageBox.confirm('确定要取消该训练任务吗？取消后无法恢复！', '警告', {
      confirmButtonText: '确定取消',
      cancelButtonText: '不取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger',
    });

    await TrainTaskAPI.cancel(taskId);
    ElMessage.success('任务已取消');
    loadTasks();
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('取消失败: ' + (error.message || '未知错误'));
    }
  }
}

// 删除任务
async function handleDelete(taskId: string) {
  try {
    await ElMessageBox.confirm('确定要删除该训练任务吗？此操作不可恢复！', '警告', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger',
    });

    await TrainTaskAPI.delete([taskId]);
    ElMessage.success('删除成功');
    loadTasks();
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.message || '未知错误'));
    }
  }
}

// 下载模型
async function handleDownloadModel(row: TrainTaskInfo) {
  if (!row.model_save_path) {
    ElMessage.warning('该任务暂无可下载的模型文件');
    return;
  }
  try {
    await TrainTaskAPI.downloadModel(row.task_id, row.model_save_path);
  } catch (error: any) {
    ElMessage.error('下载失败: ' + (error.message || '未知错误'));
  }
}

// 批量删除
async function handleBatchDelete() {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedTasks.value.length} 个训练任务吗？此操作不可恢复！`,
      '警告',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      }
    );

    const taskIds = selectedTasks.value.map((task) => task.task_id);
    await TrainTaskAPI.delete(taskIds);
    ElMessage.success('批量删除成功');
    loadTasks();
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败: ' + (error.message || '未知错误'));
    }
  }
}

// 选择变化
function handleSelectionChange(selection: TrainTaskInfo[]) {
  selectedTasks.value = selection;
}

// 获取状态文本
function getStatusText(status: string): string {
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
function getStatusTagType(status: string): 'success' | 'info' | 'warning' | 'danger' | '' {
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
function getProgressStatus(status: string): 'success' | 'exception' | 'warning' | '' {
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
onMounted(() => {
  loadTasks();
});
</script>

<style lang="scss" scoped>
.train-tasks {
  .search-form {
    margin-bottom: 16px;
  }

  .toolbar {
    margin-bottom: 16px;
    display: flex;
    gap: 12px;
  }

  .progress-cell {
    display: flex;
    flex-direction: column;
    gap: 4px;

    .progress-text {
      font-size: 12px;
      color: var(--el-text-color-secondary);
      text-align: center;
    }
  }

  .el-pagination {
    margin-top: 16px;
    justify-content: flex-end;
  }
}
</style>

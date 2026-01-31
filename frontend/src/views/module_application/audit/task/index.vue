<!-- 审计任务管理 -->
<template>
  <div class="app-container">
    <!-- 搜索区域 -->
    <div class="search-container">
      <el-form
        ref="queryFormRef"
        :model="queryFormData"
        :inline="true"
        label-suffix=":"
        @submit.prevent="handleQuery"
      >
        <el-form-item prop="task_name" label="任务名称">
          <el-input v-model="queryFormData.task_name" placeholder="请输入任务名称" clearable />
        </el-form-item>
        <el-form-item prop="task_status" label="任务状态">
          <el-select
            v-model="queryFormData.task_status"
            placeholder="请选择任务状态"
            style="width: 167.5px"
            clearable
          >
            <el-option value="pending" label="待处理" />
            <el-option value="regulation_uploaded" label="合规文件已上传" />
            <el-option value="rules_matched" label="规则已匹配" />
            <el-option value="rules_confirmed" label="规则已确认" />
            <el-option value="dataset_uploaded" label="数据集已上传" />
            <el-option value="processing" label="审计中" />
            <el-option value="completed" label="已完成" />
            <el-option value="failed" label="失败" />
          </el-select>
        </el-form-item>
        <!-- 查询、重置按钮 -->
        <el-form-item class="search-buttons">
          <el-button type="primary" icon="search" native-type="submit">查询</el-button>
          <el-button icon="refresh" @click="handleResetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 内容区域 -->
    <el-card class="data-table">
      <template #header>
        <div class="card-header">
          <span>
            <el-tooltip content="审计任务管理，执行数据合规性审计流程。">
              <QuestionFilled class="w-4 h-4 mx-1" />
            </el-tooltip>
            审计任务列表
          </span>
        </div>
      </template>

      <!-- 功能区域 -->
      <div class="data-table__toolbar">
        <div class="data-table__toolbar--left">
          <el-row :gutter="10">
            <el-col :span="1.5">
              <el-button type="success" icon="plus" @click="handleOpenDialog('create')">
                新建任务
              </el-button>
            </el-col>
            <el-col :span="1.5">
              <el-button
                type="danger"
                icon="delete"
                :disabled="selectIds.length === 0"
                @click="handleDelete(selectIds)"
              >
                批量删除
              </el-button>
            </el-col>
          </el-row>
        </div>
        <div class="data-table__toolbar--right">
          <el-row :gutter="10">
            <el-col :span="1.5">
              <el-tooltip content="刷新">
                <el-button type="primary" icon="refresh" circle @click="handleRefresh" />
              </el-tooltip>
            </el-col>
          </el-row>
        </div>
      </div>

      <!-- 表格区域 -->
      <el-table
        ref="dataTableRef"
        v-loading="loading"
        :data="pageTableData"
        highlight-current-row
        class="data-table__content"
        height="450"
        max-height="450"
        border
        stripe
        @selection-change="handleSelectionChange"
      >
        <template #empty>
          <el-empty :image-size="80" description="暂无数据" />
        </template>
        <el-table-column type="selection" min-width="55" align="center" />
        <el-table-column type="index" fixed label="序号" min-width="60">
          <template #default="scope">
            {{ (queryFormData.page_no - 1) * queryFormData.page_size + scope.$index + 1 }}
          </template>
        </el-table-column>
        <el-table-column label="任务名称" prop="task_name" min-width="180" show-overflow-tooltip />
        <el-table-column label="任务状态" prop="task_status" min-width="140">
          <template #default="scope">
            <el-tag v-if="scope.row.task_status === 'pending'" type="info">待处理</el-tag>
            <el-tag v-else-if="scope.row.task_status === 'regulation_uploaded'" type="primary">
              合规文件已上传
            </el-tag>
            <el-tag v-else-if="scope.row.task_status === 'rules_matched'">规则已匹配</el-tag>
            <el-tag v-else-if="scope.row.task_status === 'rules_confirmed'" type="warning">
              规则已确认
            </el-tag>
            <el-tag v-else-if="scope.row.task_status === 'dataset_uploaded'">
              数据集已上传
            </el-tag>
            <el-tag v-else-if="scope.row.task_status === 'processing'" type="warning">
              审计中
            </el-tag>
            <el-tag v-else-if="scope.row.task_status === 'completed'" type="success">
              已完成
            </el-tag>
            <el-tag v-else-if="scope.row.task_status === 'failed'" type="danger">失败</el-tag>
            <el-tag v-else>{{ scope.row.task_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="总记录数" prop="total_records" min-width="100" align="center" />
        <el-table-column label="错误记录数" prop="error_records" min-width="100" align="center">
          <template #default="scope">
            <el-tag v-if="scope.row.error_records > 0" type="danger">
              {{ scope.row.error_records }}
            </el-tag>
            <span v-else>{{ scope.row.error_records || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" prop="created_time" min-width="180" sortable />
        <el-table-column fixed="right" label="操作" align="center" min-width="240">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              link
              icon="Memo"
              @click="goToWorkflow(scope.row)"
            >
              合规流程
            </el-button>
            <el-button
              v-if="scope.row.task_status === 'completed'"
              type="success"
              size="small"
              link
              icon="download"
              @click="handleDownloadReport(scope.row.id)"
            >
              下载报告
            </el-button>
            <el-button
              type="danger"
              size="small"
              link
              icon="delete"
              @click="handleDelete([scope.row.id])"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页区域 -->
      <template #footer>
        <pagination
          v-model:total="total"
          v-model:page="queryFormData.page_no"
          v-model:limit="queryFormData.page_size"
          @pagination="loadingData"
        />
      </template>
    </el-card>

    <!-- 新建任务弹窗 -->
    <el-dialog
      v-model="dialogVisible.visible"
      :title="dialogVisible.title"
      width="500px"
      @close="handleCloseDialog"
    >
      <el-form
        ref="dataFormRef"
        :model="formData"
        :rules="rules"
        label-suffix=":"
        label-width="auto"
        label-position="right"
      >
        <el-form-item label="任务名称" prop="task_name">
          <el-input v-model="formData.task_name" placeholder="请输入任务名称" :maxlength="100" />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleCloseDialog">取消</el-button>
          <el-button type="primary" @click="handleSubmit">确定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
defineOptions({
  name: "AuditTask",
  inheritAttrs: false,
});

import { useRouter } from "vue-router";
import AuditTaskAPI, {
  AuditTaskTable,
  AuditTaskForm,
  AuditTaskPageQuery,
} from "@/api/module_application/audit/task";

const queryFormRef = ref();
const dataFormRef = ref();
const total = ref(0);
const selectIds = ref<number[]>([]);
const loading = ref(false);
const router = useRouter();

// 分页表单
const pageTableData = ref<AuditTaskTable[]>([]);

// 分页查询参数
const queryFormData = reactive<AuditTaskPageQuery>({
  page_no: 1,
  page_size: 10,
  task_name: undefined,
  task_status: undefined,
});

// 编辑表单
const formData = reactive<AuditTaskForm>({
  id: undefined,
  task_name: "",
});

// 弹窗状态
const dialogVisible = reactive({
  title: "",
  visible: false,
  type: "create" as "create" | "update" | "detail",
});

// 表单验证规则
const rules = reactive({
  task_name: [{ required: true, message: "请输入任务名称", trigger: "blur" }],
});

// 列表刷新
async function handleRefresh() {
  await loadingData();
}

// 加载表格数据
async function loadingData() {
  loading.value = true;
  try {
    const response = await AuditTaskAPI.listTask(queryFormData);
    pageTableData.value = response.data.data.items;
    total.value = response.data.data.total;
  } catch (error: any) {
    console.error(error);
  } finally {
    loading.value = false;
  }
}

// 查询
async function handleQuery() {
  queryFormData.page_no = 1;
  loadingData();
}

// 重置查询
async function handleResetQuery() {
  queryFormRef.value.resetFields();
  queryFormData.page_no = 1;
  return loadingData();
}

// 定义初始表单数据常量
const initialFormData: AuditTaskForm = {
  id: undefined,
  task_name: "",
};

// 重置表单
async function resetForm() {
  if (dataFormRef.value) {
    dataFormRef.value.resetFields();
    dataFormRef.value.clearValidate();
  }
  Object.assign(formData, initialFormData);
}

// 行复选框选中项变化
async function handleSelectionChange(selection: any) {
  selectIds.value = selection.map((item: any) => item.id);
}

// 关闭弹窗
async function handleCloseDialog() {
  dialogVisible.visible = false;
  resetForm();
}

// 打开弹窗
async function handleOpenDialog(type: "create") {
  dialogVisible.type = type;
  dialogVisible.title = "新建任务";
  formData.id = undefined;
  dialogVisible.visible = true;
}

// 新建任务
async function handleSubmit() {
  dataFormRef.value.validate(async (valid: any) => {
    if (valid) {
      loading.value = true;
      try {
        const form = new FormData();
        form.append("task_name", formData.task_name);
        const { data } = await AuditTaskAPI.createTask(form);
        const newTaskId = data.data?.id;
        dialogVisible.visible = false;
        resetForm();
        await handleResetQuery();
        ElMessage.success("任务创建成功");
        if (newTaskId) {
          ElMessageBox.confirm("是否立即进入流程上传法规？", "提示", {
            confirmButtonText: "前往流程",
            cancelButtonText: "稍后再说",
            type: "info",
          })
            .then(() => {
              goToWorkflow({ id: newTaskId } as AuditTaskTable);
            })
            .catch(() => {
              ElMessageBox.close();
            });
        }
      } catch (error: any) {
        console.error(error);
      } finally {
        loading.value = false;
      }
    }
  });
}

// 删除、批量删除
async function handleDelete(ids: number[]) {
  ElMessageBox.confirm("确认删除该项数据?", "警告", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning",
  })
    .then(async () => {
      try {
        loading.value = true;
        await AuditTaskAPI.deleteTask(ids);
        handleResetQuery();
      } catch (error: any) {
        console.error(error);
      } finally {
        loading.value = false;
      }
    })
    .catch(() => {
      ElMessageBox.close();
    });
}

// 跳转到工作流页面
function goToWorkflow(task: AuditTaskTable) {
  if (!task.id) return;
  router.push({
    path: "/module_application/audit/task/workflow",
    query: { taskId: task.id },
  });
}

// 下载报告
async function handleDownloadReport(taskId: number) {
  try {
    loading.value = true;
    const { data } = await AuditTaskAPI.downloadReport(taskId);
    const blob = data;
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `audit_report_${taskId}_${Date.now()}.xlsx`;
    link.click();
    window.URL.revokeObjectURL(url);
    ElMessage.success("报告下载成功");
  } catch (error: any) {
    console.error(error);
    ElMessage.error("报告下载失败");
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadingData();
});
</script>

<style lang="scss" scoped></style>

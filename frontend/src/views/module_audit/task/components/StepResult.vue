<template>
  <div class="step-panel">
    <el-alert
      v-if="taskStatus === 'completed'"
      title="审计已完成，可下载报告或查看错误详情"
      type="success"
      :closable="false"
      show-icon
    />
    <el-alert
      v-else-if="taskStatus === 'failed'"
      title="审计失败，请重新上传或联系管理员"
      type="error"
      :closable="false"
      show-icon
    />
    <el-alert
      v-else
      title="审计正在进行中，请稍候..."
      type="info"
      :closable="false"
      show-icon
    />

    <el-descriptions class="mt-4" :column="2" border>
      <el-descriptions-item label="任务名称">
        {{ taskDetail?.task_name }}
      </el-descriptions-item>
      <el-descriptions-item label="任务状态">
        <el-tag>
          {{ taskDetail?.task_status }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="总记录数">
        {{ taskDetail?.total_records || 0 }}
      </el-descriptions-item>
      <el-descriptions-item label="错误记录数">
        <el-tag :type="(taskDetail?.error_records || 0) > 0 ? 'danger' : 'success'">
          {{ taskDetail?.error_records || 0 }}
        </el-tag>
      </el-descriptions-item>
    </el-descriptions>

    <div class="action-area">
      <el-button type="primary" icon="download" :disabled="!canDownload" @click="$emit('download')">
        下载报告
      </el-button>
      <el-button type="info" icon="view" :disabled="!canDownload" @click="$emit('toggleErrors')">
        {{ showErrors ? "收起错误详情" : "查看错误详情" }}
      </el-button>
    </div>

    <div v-if="showErrors" class="mt-4">
      <el-table :data="errors" border stripe height="320">
        <el-table-column type="index" label="#" width="60" />
        <el-table-column label="类型" prop="error_type" width="100" />
        <el-table-column label="行号" prop="row_number" width="100" />
        <el-table-column label="字段名" prop="field_name" width="140" />
        <el-table-column label="原始值" prop="original_value" min-width="160" show-overflow-tooltip />
        <el-table-column label="错误描述" prop="error_message" min-width="200" show-overflow-tooltip />
        <el-table-column label="严重级别" prop="severity" width="120" />
      </el-table>
      <div class="mt-3">
        <pagination
          v-model:total="pagination.total"
          v-model:page="pagination.page_no"
          v-model:limit="pagination.page_size"
          @pagination="handlePagerChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { PropType } from "vue";
import type { AuditTaskTable, AuditErrorTable } from "@/api/module_audit/task";

interface ErrorPagination {
  page_no: number;
  page_size: number;
  total: number;
}

const props = defineProps({
  taskDetail: Object as PropType<AuditTaskTable | null>,
  errors: {
    type: Array as PropType<AuditErrorTable[]>,
    default: () => [],
  },
  pagination: {
    type: Object as PropType<ErrorPagination>,
    required: true,
  },
  showErrors: { type: Boolean, default: false },
});

const emit = defineEmits<{
  (e: "download"): void;
  (e: "toggleErrors"): void;
  (e: "changePage", pager: { page: number; limit: number }): void;
}>();

const taskStatus = computed(() => props.taskDetail?.task_status || "");
const canDownload = computed(() => taskStatus.value === "completed" && !!props.taskDetail?.audit_report_path);

function handlePagerChange(pager: { page: number; limit: number }) {
  emit("changePage", pager);
}
</script>

<style scoped>
.step-panel {
  padding: 12px 0;
}

.action-area {
  margin-top: 20px;
  display: flex;
  gap: 12px;
}
</style>

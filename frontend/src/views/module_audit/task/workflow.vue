<template>
  <div class="workflow-page">
    <el-page-header content="合规审计流程" @back="router.back()" />

    <el-empty v-if="!taskId" class="mt-6" description="请先从任务列表选择一个任务" />
    <div v-else>
      <el-card class="mt-4" shadow="never">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="任务ID">
            {{ taskDetail?.id || taskId }}
          </el-descriptions-item>
          <el-descriptions-item label="任务名称">
            {{ taskDetail?.task_name || "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag>{{ taskDetail?.task_status || "pending" }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <el-steps :active="currentStep" align-center class="mt-4">
        <el-step title="上传法规" />
        <el-step title="选择规则" />
        <el-step title="上传数据集" />
        <el-step title="执行并查看结果" />
      </el-steps>

      <el-card class="mt-4" shadow="never" v-loading="loading">
        <StepRegulation
          v-if="currentStep === 0"
          :loading="regulationUploading"
          :selecting="assigningRegulation"
          :regulation-file-name="taskDetail?.regulation_file_name"
          :regulation-id="taskDetail?.regulation_id"
          :regulations="regulationOptions"
          @upload="handleUploadRegulation"
          @use="handleUseRegulation"
        />

        <StepRuleSelect
          v-else-if="currentStep === 1"
          :matching="matching"
          :confirming="confirming"
          :all-rules="availableRules"
          :matched-rule-ids="matchedRuleIds"
          :selected-rule-ids="selectedRuleIds"
          @match="handleMatchRules"
          @confirm="handleConfirmRules"
          @update:selectedRuleIds="handleSelectedRuleChange"
        />

        <StepDataset
          v-else-if="currentStep === 2"
          :loading="datasetUploading"
          :dataset-file-name="taskDetail?.dataset_file_name"
          @upload="handleUploadDataset"
        />

        <StepResult
          v-else
          :task-detail="taskDetail"
          :errors="errorList"
          :pagination="errorPagination"
          :show-errors="showErrors"
          @download="handleDownloadReport"
          @toggleErrors="toggleErrors"
          @changePage="handleErrorPageChange"
        />
        <template #footer>
          <div class="workflow-footer">
            <el-button @click="handleBackToList">返回任务列表</el-button>
            <el-button
              type="primary"
              :loading="executing"
              :disabled="!canExecute"
              @click="handleExecuteAudit"
            >
              执行审计
            </el-button>
          </div>
        </template>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import AuditTaskAPI, {
  AuditTaskTable,
  AuditErrorTable,
  MatchedRuleSummary,
} from "@/api/module_audit/task";
import AuditRuleAPI, { AuditRuleTable } from "@/api/module_audit/rule";
import AuditRegulationAPI, { AuditRegulationOption } from "@/api/module_audit/regulation";
import StepRegulation from "./components/StepRegulation.vue";
import StepRuleSelect from "./components/StepRuleSelect.vue";
import StepDataset from "./components/StepDataset.vue";
import StepResult from "./components/StepResult.vue";

const route = useRoute();
const router = useRouter();

const taskId = computed(() => Number(route.query.taskId));
const taskDetail = ref<AuditTaskTable | null>(null);
const allRules = ref<AuditRuleTable[]>([]);
const regulationOptions = ref<AuditRegulationOption[]>([]);
const selectedRuleIds = ref<number[]>([]);
const matchedRuleIds = ref<number[]>([]);
const loading = ref(false);
const regulationUploading = ref(false);
const datasetUploading = ref(false);
const matching = ref(false);
const confirming = ref(false);
const executing = ref(false);
const assigningRegulation = ref(false);
const showErrors = ref(false);
const errorList = ref<AuditErrorTable[]>([]);
const errorPagination = reactive<{ page_no: number; page_size: number; total: number }>({
  page_no: 1,
  page_size: 10,
  total: 0,
});

const availableRules = computed<MatchedRuleSummary[]>(() =>
  allRules.value
    .filter((rule): rule is AuditRuleTable & { id: number } => typeof rule.id === "number")
    .map((rule) => ({
      id: rule.id,
      rule_code: rule.rule_code,
      rule_name: rule.rule_name,
      rule_type: rule.rule_type,
      rule_description: rule.rule_description,
      severity: rule.severity,
    }))
);

const currentStep = computed(() => {
  switch (taskDetail.value?.task_status) {
    case "regulation_uploaded":
    case "rules_matched":
      return 1;
    case "rules_confirmed":
      return 2;
    case "dataset_uploaded":
    case "processing":
    case "completed":
    case "failed":
      return 3;
    default:
      return 0;
  }
});

const canExecute = computed(() => {
  if (!taskDetail.value) return false;
  return ["dataset_uploaded", "processing", "completed", "failed"].includes(
    taskDetail.value.task_status || ""
  );
});

watch(
  () => route.query.taskId,
  () => {
    resetState();
    if (taskId.value) {
      loadTaskDetail();
      loadRuleOptions();
    }
    loadRegulationOptions();
  },
  { immediate: true }
);

async function loadTaskDetail() {
  if (!taskId.value) return;
  loading.value = true;
  try {
    const { data } = await AuditTaskAPI.detailTask(taskId.value);
    taskDetail.value = data.data;
    selectedRuleIds.value = data.data?.selected_rule_ids ?? [];
    matchedRuleIds.value = data.data?.matched_rule_ids ?? [];
  } catch (error) {
    console.error(error);
  } finally {
    loading.value = false;
  }
}

async function loadRuleOptions() {
  try {
    const { data } = await AuditRuleAPI.optionRule();
    allRules.value = data.data || [];
  } catch (error) {
    console.error(error);
  }
}

async function loadRegulationOptions() {
  try {
    const { data } = await AuditRegulationAPI.optionRegulation();
    regulationOptions.value = data.data || [];
  } catch (error) {
    console.error(error);
  }
}

async function handleUploadRegulation(file: File) {
  if (!taskId.value) return;
  regulationUploading.value = true;
  try {
    await AuditTaskAPI.uploadRegulation(taskId.value, file);
    ElMessage.success("法规上传成功");
    await loadTaskDetail();
    await loadRegulationOptions();
  } catch (error) {
    console.error(error);
  } finally {
    regulationUploading.value = false;
  }
}

async function handleUseRegulation(regulationId: number) {
  if (!taskId.value) return;
  assigningRegulation.value = true;
  try {
    await AuditTaskAPI.useRegulation(taskId.value, regulationId);
    ElMessage.success("法规选择成功");
    await loadTaskDetail();
  } catch (error) {
    console.error(error);
  } finally {
    assigningRegulation.value = false;
  }
}

async function handleMatchRules() {
  if (!taskId.value) return;
  matching.value = true;
  try {
    const { data } = await AuditTaskAPI.aiMatchRules(taskId.value);
    matchedRuleIds.value = data.data?.matched_rule_ids || [];
    selectedRuleIds.value = [...matchedRuleIds.value];
    ElMessage.success("AI 匹配完成");
  } catch (error) {
    console.error(error);
  } finally {
    matching.value = false;
  }
}

async function handleConfirmRules() {
  if (!taskId.value) return;
  if (!selectedRuleIds.value.length) {
    ElMessage.warning("请至少选择一条规则");
    return;
  }
  confirming.value = true;
  try {
    await AuditTaskAPI.confirmRules(taskId.value, selectedRuleIds.value);
    ElMessage.success("规则确认成功");
    await loadTaskDetail();
  } catch (error) {
    console.error(error);
  } finally {
    confirming.value = false;
  }
}

async function handleUploadDataset(file: File) {
  if (!taskId.value) return;
  datasetUploading.value = true;
  try {
    await AuditTaskAPI.uploadDataset(taskId.value, file);
    ElMessage.success("数据集上传成功");
    await loadTaskDetail();
  } catch (error) {
    console.error(error);
  } finally {
    datasetUploading.value = false;
  }
}

async function handleExecuteAudit() {
  if (!taskId.value) return;
  executing.value = true;
  try {
    await AuditTaskAPI.executeAudit(taskId.value);
    ElMessage.success("已触发审计流程");
    await loadTaskDetail();
  } catch (error) {
    console.error(error);
  } finally {
    executing.value = false;
  }
}

async function handleDownloadReport() {
  if (!taskId.value) return;
  try {
    const { data } = await AuditTaskAPI.downloadReport(taskId.value);
    const blob = data;
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `audit_report_${taskId.value}_${Date.now()}.xlsx`;
    link.click();
    window.URL.revokeObjectURL(url);
    ElMessage.success("报告下载成功");
  } catch (error) {
    console.error(error);
    ElMessage.error("报告下载失败");
  }
}

function toggleErrors() {
  showErrors.value = !showErrors.value;
  if (showErrors.value) {
    loadErrors();
  }
}

async function loadErrors() {
  if (!taskId.value) return;
  try {
    const { data } = await AuditTaskAPI.getTaskErrors(taskId.value, {
      page_no: errorPagination.page_no,
      page_size: errorPagination.page_size,
      error_type: undefined,
    });
    errorList.value = data.data.items || [];
    errorPagination.total = data.data.total || 0;
  } catch (error) {
    console.error(error);
  }
}

function handleErrorPageChange(pager: { page: number; limit: number }) {
  errorPagination.page_no = pager.page;
  errorPagination.page_size = pager.limit;
  loadErrors();
}

function handleSelectedRuleChange(ids: number[]) {
  selectedRuleIds.value = [...ids];
}

function handleBackToList() {
  router
    .push({ name: "AuditTask" })
    .catch(() => router.push("/audit/task"))
    .catch(() => router.push("/"));
}

function resetState() {
  taskDetail.value = null;
  selectedRuleIds.value = [];
  matchedRuleIds.value = [];
  showErrors.value = false;
  errorPagination.page_no = 1;
  errorPagination.total = 0;
}

onMounted(() => {
  if (taskId.value) {
    loadRuleOptions();
  }
  loadRegulationOptions();
});
</script>

<style scoped>
.workflow-page {
  padding: 24px;
}

.mt-4 {
  margin-top: 16px;
}

.mt-6 {
  margin-top: 24px;
}

.workflow-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>

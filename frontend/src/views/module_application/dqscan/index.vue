<template>
  <div class="app-container">
    <el-card shadow="hover">
      <template #header>
        <div class="flex-x-between">
          <div class="flex items-center gap-2">
            <div class="i-svg:table w-5 h-5" />
            <span class="font-bold">数据集质量探测引擎</span>
            <el-tag type="info" effect="plain" size="small">V3</el-tag>
          </div>
          <div class="flex items-center gap-2">
            <el-tag :type="statusTagType" effect="plain">{{ statusText }}</el-tag>
            <el-button icon="refresh" @click="resetAll">重置</el-button>
          </div>
        </div>
      </template>

      <!-- 顶部流程条（按你截图的箭头样式） -->
      <div class="step-bar">
        <div class="step-arrow" :class="stepClass(0)" @click="gotoStep(0)">
          <div class="flex items-center justify-center gap-2">
            <div class="i-svg:menu w-4 h-4" />
            <span>选择数据模态</span>
          </div>
        </div>
        <div class="step-arrow" :class="stepClass(1)" @click="gotoStep(1)">
          <div class="flex items-center justify-center gap-2">
            <div class="i-svg:file w-4 h-4" />
            <span>上传文件</span>
          </div>
        </div>
        <div class="step-arrow" :class="stepClass(2)" @click="gotoStep(2)">
          <div class="flex items-center justify-center gap-2">
            <div class="i-svg:setting w-4 h-4" />
            <span>选择算法</span>
          </div>
        </div>
        <div class="step-arrow" :class="stepClass(3)" @click="gotoStep(3)">
          <div class="flex items-center justify-center gap-2">
            <div class="i-svg:monitor w-4 h-4" />
            <span>检测运行</span>
          </div>
        </div>
        <div class="step-arrow" :class="stepClass(4)" @click="gotoStep(4)">
          <div class="flex items-center justify-center gap-2">
            <div class="i-svg:search w-4 h-4" />
            <span>查看结果</span>
          </div>
        </div>
      </div>

      <!-- Step 0: modality -->
      <el-card v-show="activeStep === 0" shadow="never" class="mt-4">
        <template #header>
          <div class="font-bold">选择数据模态</div>
        </template>
        <el-row :gutter="12">
          <el-col v-for="m in modalities" :key="m.value" :span="6" :xs="12" class="mb-3">
            <el-card
              shadow="hover"
              class="modality-card"
              :class="{ 'is-active': selectedModality === m.value, 'is-disabled': m.disabled }"
              @click="!m.disabled && (selectedModality = m.value)"
            >
              <div class="flex items-center gap-2">
                <div :class="`i-svg:${m.icon}`" class="w-6 h-6" />
                <div class="flex flex-col">
                  <div class="font-bold">{{ m.label }}</div>
                  <div class="text-xs text-gray">{{ m.desc }}</div>
                </div>
              </div>
              <el-divider class="my-2" />
              <el-tag v-if="m.disabled" type="info" effect="plain" size="small">后续支持</el-tag>
              <el-tag v-else-if="selectedModality === m.value" type="success" effect="plain" size="small"
                >已选择</el-tag
              >
              <el-tag v-else type="info" effect="plain" size="small">可用</el-tag>
            </el-card>
          </el-col>
        </el-row>
        <div class="mt-2 flex justify-end">
          <el-button type="primary" :disabled="!selectedModality" @click="gotoStep(1)">下一步</el-button>
        </div>
      </el-card>

      <!-- Step 1: upload -->
      <el-card v-show="activeStep === 1" shadow="never" class="mt-4">
        <template #header>
          <div class="font-bold">上传文件（CSV/TXT，最大500MB）</div>
        </template>
        <el-upload
          ref="uploadRef"
          drag
          :auto-upload="false"
          :limit="1"
          :file-list="fileList"
          accept=".csv,.txt"
          @change="onFileChange"
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">将文件拖到此处，或 <em>点击选择</em></div>
        </el-upload>

        <div class="mt-3 flex items-center gap-2">
          <el-button type="primary" :loading="uploading" :disabled="!selectedFile" @click="doUpload">
            上传并继续
          </el-button>
          <el-text v-if="uploadedFile" type="info">
            已上传：{{ uploadedFile.filename }}（{{ formatBytes(uploadedFile.file_size) }}）
          </el-text>
        </div>
      </el-card>

      <!-- Step 2: choose modules -->
      <el-card v-show="activeStep === 2" shadow="never" class="mt-4">
        <template #header>
          <div class="font-bold">选择算法（四大检测模块）</div>
        </template>

        <el-alert
          type="info"
          show-icon
          :closable="false"
          title="当前仅实现表格数据闭环；其他模态后续接入。每个模块会生成 JSON 摘要与 Word 报告，可在结果页下载。"
          class="mb-3"
        />

        <el-card shadow="never" class="mb-3">
          <div class="flex items-start gap-2">
            <div class="i-svg:api w-5 h-5 mt-1" />
            <div class="flex-1">
              <div class="font-bold">{{ selectedAlgorithmLabel }}</div>
              <div class="text-sm text-gray mt-1">{{ selectedAlgorithmDesc }}</div>
              <div class="text-xs text-gray mt-1">算法ID：{{ selectedAlgorithm }}</div>
            </div>
          </div>
        </el-card>

        <el-checkbox-group v-model="selectedModules" class="grid grid-cols-1 md:grid-cols-2 gap-2">
          <el-checkbox v-for="m in modules" :key="m.key" :label="m.key" border class="!h-auto !items-start">
            <div class="flex flex-col">
              <div class="font-bold">{{ m.title }}</div>
              <div class="text-sm text-gray mt-1">{{ m.desc }}</div>
            </div>
          </el-checkbox>
        </el-checkbox-group>

        <div class="mt-3 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <el-button icon="refresh" :loading="algorithmsLoading" @click="loadAlgorithms">刷新算法列表</el-button>
            <el-text type="info">未勾选默认按全选四模块执行</el-text>
          </div>
          <div class="flex items-center gap-2">
            <el-button @click="gotoStep(1)">上一步</el-button>
            <el-button type="success" :disabled="!canStart" :loading="starting" icon="video-play" @click="startScan">
              开始检测
            </el-button>
          </div>
        </div>
      </el-card>

      <!-- Step 3: run -->
      <el-card v-show="activeStep === 3" shadow="never" class="mt-4">
        <template #header>
          <div class="flex-x-between">
            <div class="font-bold">检测运行 / 实时日志</div>
            <div class="flex items-center gap-2">
              <el-progress :percentage="progress" :status="progressStatus" style="width: 260px" />
              <el-button v-if="taskId" icon="refresh" @click="refreshTask">刷新状态</el-button>
            </div>
          </div>
        </template>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <el-card shadow="never" class="md:col-span-1">
            <div class="text-sm text-gray">任务ID</div>
            <div class="mt-1 font-mono text-sm break-all">{{ taskId || "-" }}</div>
            <el-divider />
            <div class="text-sm text-gray">状态</div>
            <div class="mt-1">
              <el-tag :type="statusTagType" effect="plain">{{ statusText }}</el-tag>
            </div>
            <el-divider />
            <div class="text-sm text-gray">错误</div>
            <div class="mt-1 text-sm break-all">{{ taskError || "-" }}</div>
          </el-card>

          <el-card shadow="never" class="md:col-span-2">
            <el-scrollbar height="260px">
              <pre class="log-pre">{{ logs.join("\n") }}</pre>
            </el-scrollbar>
          </el-card>
        </div>

        <div class="mt-3 flex justify-end gap-2">
          <el-button @click="gotoStep(2)">返回选择</el-button>
          <el-button type="primary" :disabled="!resultReady" @click="gotoStep(4)">查看结果</el-button>
        </div>
      </el-card>

      <!-- Step 4: results -->
      <el-card v-show="activeStep === 4" shadow="never" class="mt-4">
        <template #header>
          <div class="flex-x-between">
            <div class="font-bold">查看结果</div>
            <div class="flex items-center gap-2">
              <el-button v-if="taskId" icon="refresh" @click="fetchResult">刷新结果</el-button>
              <el-button v-if="taskId" type="primary" icon="download" @click="downloadResultJson">
                下载 result.json
              </el-button>
            </div>
          </div>
        </template>

        <el-empty v-if="!result" description="暂无结果（请先运行检测）" />

        <div v-else>
          <el-descriptions :column="4" border>
            <el-descriptions-item label="状态">{{ result.summary?.status ?? "-" }}</el-descriptions-item>
            <el-descriptions-item label="模态">{{ result.summary?.data_type ?? "-" }}</el-descriptions-item>
            <el-descriptions-item label="模块">{{ (result.summary?.modules || []).join(", ") }}</el-descriptions-item>
            <el-descriptions-item label="耗时(s)">{{ result.summary?.elapsed_seconds ?? "-" }}</el-descriptions-item>
          </el-descriptions>

          <el-divider />

          <el-tabs>
            <el-tab-pane label="模块结果">
              <el-row :gutter="12">
                <el-col v-for="m in resultModules" :key="m.key" :span="12" :xs="24" class="mb-3">
                  <el-card shadow="hover">
                    <template #header>
                      <div class="flex-x-between">
                        <div class="font-bold">{{ moduleTitle(m.key) }}</div>
                        <el-tag :type="m.hasIssues ? 'warning' : 'success'" effect="plain">{{
                          m.hasIssues ? "有风险" : "正常"
                        }}</el-tag>
                      </div>
                    </template>

                    <el-descriptions :column="2" border>
                      <el-descriptions-item label="算法">{{ m.algorithm }}</el-descriptions-item>
                      <el-descriptions-item label="问题数">{{ m.totalIssues }}</el-descriptions-item>
                      <el-descriptions-item label="问题比例">{{ m.issuePercentage }}</el-descriptions-item>
                      <el-descriptions-item v-if="m.extraLabel" :label="m.extraLabel">{{ m.extraValue }}</el-descriptions-item>
                    </el-descriptions>

                    <el-divider />

                    <div class="flex items-center gap-2">
                      <el-button
                        v-if="m.docxPath"
                        type="primary"
                        icon="download"
                        @click="downloadArtifact(m.docxPath, `${m.key}.docx`)"
                      >
                        下载 Word 报告
                      </el-button>
                      <el-button
                        v-if="m.summaryPath"
                        icon="download"
                        @click="downloadArtifact(m.summaryPath, `${m.key}_summary.json`)"
                      >
                        下载摘要(JSON)
                      </el-button>
                      <el-tooltip v-if="m.docxError" :content="m.docxError">
                        <el-tag type="danger" effect="plain">报告生成失败</el-tag>
                      </el-tooltip>
                    </div>
                  </el-card>
                </el-col>
              </el-row>
            </el-tab-pane>

            <el-tab-pane label="原始JSON">
              <el-scrollbar height="420px">
                <pre class="log-pre">{{ prettyResult }}</pre>
              </el-scrollbar>
            </el-tab-pane>
          </el-tabs>
        </div>
      </el-card>
    </el-card>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: "DQScan", inheritAttrs: false });

import { saveAs } from "file-saver";
import type { UploadFile } from "element-plus";
import { UploadFilled } from "@element-plus/icons-vue";
import DQScanAPI, { type DQScanAlgorithmOut, type DQScanUploadOut } from "@/api/module_application/dqscan";

type TaskStatus = "IDLE" | "PENDING" | "RUNNING" | "SUCCESS" | "FAILED";

const uploadRef = ref();
const activeStep = ref(0);

const modalities = [
  { value: "tabular", label: "表格数据", icon: "table", desc: "CSV/TXT", disabled: false },
  { value: "timeseries", label: "时序数据", icon: "monitor", desc: "后续接入", disabled: true },
  { value: "image", label: "图像数据", icon: "browser", desc: "后续接入", disabled: true },
  { value: "text", label: "文本数据", icon: "document", desc: "后续接入", disabled: true },
];
const selectedModality = ref<string>("tabular");

const fileList = ref<UploadFile[]>([]);
const selectedFile = ref<File | null>(null);
const uploading = ref(false);
const uploadedFile = ref<DQScanUploadOut | null>(null);

const algorithmsLoading = ref(false);
const algorithms = ref<DQScanAlgorithmOut[]>([]);
const selectedAlgorithm = ref<string>("tabular_quality_engine_v3");

const modules = [
  { key: "distribution", title: "分布式偏差检测", desc: "检测训练/测试分布漂移（默认按 70/30 切分）" },
  { key: "dirty_data", title: "脏数据扫描", desc: "异常/缺失/重复/值域违规等" },
  { key: "adversarial", title: "对抗性检测", desc: "对抗扰动下模型脆弱性（演示模型 + 攻击）" },
  { key: "physics", title: "物理保真度扫描", desc: "基于规则/约束的物理合理性校验（列名启发式）" },
];
const selectedModules = ref<string[]>(["dirty_data", "distribution", "adversarial", "physics"]);

const starting = ref(false);
const taskId = ref<string | null>(null);
const progress = ref(0);
const logs = ref<string[]>([]);
const taskStatus = ref<TaskStatus>("IDLE");
const taskError = ref<string | null>(null);
const result = ref<any | null>(null);

let ws: WebSocket | null = null;
let pollTimer: number | null = null;

const canStart = computed(() => !!uploadedFile.value?.file_id && !!selectedAlgorithm.value && !starting.value);
const resultReady = computed(() => taskStatus.value === "SUCCESS" && !!result.value);

const selectedAlgorithmLabel = computed(() => {
  const alg = algorithms.value.find((a) => a.name === selectedAlgorithm.value);
  return alg?.label || "表格数据质量探测引擎（V3：四模块）";
});
const selectedAlgorithmDesc = computed(() => {
  const alg = algorithms.value.find((a) => a.name === selectedAlgorithm.value);
  return alg?.description || "脏数据扫描 / 分布偏差 / 对抗性 / 物理保真度，并生成报告";
});

const statusText = computed(() => {
  const map: Record<TaskStatus, string> = {
    IDLE: "未开始",
    PENDING: "排队中",
    RUNNING: "运行中",
    SUCCESS: "已完成",
    FAILED: "失败",
  };
  return map[taskStatus.value] || "未知";
});

const statusTagType = computed(() => {
  switch (taskStatus.value) {
    case "SUCCESS":
      return "success";
    case "FAILED":
      return "danger";
    case "RUNNING":
      return "primary";
    case "PENDING":
      return "warning";
    default:
      return "info";
  }
});

const progressStatus = computed(() => {
  if (taskStatus.value === "FAILED") return "exception";
  if (taskStatus.value === "SUCCESS") return "success";
  return undefined;
});

const prettyResult = computed(() => (result.value ? JSON.stringify(result.value, null, 2) : ""));

function formatBytes(bytes: number) {
  const units = ["B", "KB", "MB", "GB"];
  let v = bytes;
  let i = 0;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i += 1;
  }
  return `${v.toFixed(i === 0 ? 0 : 2)} ${units[i]}`;
}

function pushLog(line: string) {
  if (!line) return;
  logs.value.push(line);
  if (logs.value.length > 800) logs.value.splice(0, logs.value.length - 800);
}

function resetWs() {
  try {
    ws?.close(1000, "reset");
  } catch {}
  ws = null;
}

function clearPoll() {
  if (pollTimer) {
    window.clearInterval(pollTimer);
    pollTimer = null;
  }
}

function resetAll() {
  resetWs();
  clearPoll();
  activeStep.value = 0;
  fileList.value = [];
  selectedFile.value = null;
  uploading.value = false;
  uploadedFile.value = null;
  starting.value = false;
  taskId.value = null;
  progress.value = 0;
  logs.value = [];
  taskStatus.value = "IDLE";
  taskError.value = null;
  result.value = null;
}

function gotoStep(step: number) {
  activeStep.value = step;
}

function stepClass(idx: number) {
  if (activeStep.value === idx) return "active";
  if (activeStep.value > idx) return "completed";
  return "";
}

function onFileChange(file: UploadFile, files: UploadFile[]) {
  fileList.value = (files || []).slice(-1);
  const raw = (fileList.value[0]?.raw || file.raw) as File | undefined;
  selectedFile.value = raw || null;
}

async function loadAlgorithms() {
  algorithmsLoading.value = true;
  try {
    const res = await DQScanAPI.listAlgorithms();
    algorithms.value = res.data.data || [];
    if (algorithms.value.some((a) => a.name === "tabular_quality_engine_v3")) {
      selectedAlgorithm.value = "tabular_quality_engine_v3";
    } else if (algorithms.value.length > 0) {
      selectedAlgorithm.value = algorithms.value[0].name;
    }
  } finally {
    algorithmsLoading.value = false;
  }
}

async function doUpload() {
  if (!selectedFile.value) return;
  uploading.value = true;
  try {
    const res = await DQScanAPI.uploadFile(selectedFile.value);
    uploadedFile.value = res.data.data;
    gotoStep(2);
    pushLog(`上传成功：${uploadedFile.value?.filename}`);
  } finally {
    uploading.value = false;
  }
}

function connectWs(id: string) {
  resetWs();
  const base = import.meta.env.VITE_APP_WS_ENDPOINT || "";
  const url = `${base}/api/v1/application/dqscan/ws/${id}`;
  ws = new WebSocket(url);

  ws.onopen = () => {
    pushLog("WebSocket 已连接");
  };
  ws.onmessage = async (evt) => {
    try {
      const msg = JSON.parse(evt.data);
      if (msg.type === "snapshot") {
        pushLog(`任务快照：${msg.status}，progress=${msg.progress}`);
        progress.value = Number(msg.progress ?? progress.value);
        taskStatus.value = (msg.status as TaskStatus) ?? taskStatus.value;
        if (msg.error) taskError.value = String(msg.error);
        return;
      }
      if (msg.type === "log") {
        pushLog(msg.message);
      } else if (msg.type === "progress") {
        progress.value = Number(msg.value ?? progress.value);
      } else if (msg.type === "done") {
        pushLog(msg.message || "完成");
        taskStatus.value = "SUCCESS";
        progress.value = 100;
        clearPoll();
        await fetchResult();
        gotoStep(4);
      } else if (msg.type === "error") {
        pushLog(`错误：${msg.message}`);
        taskStatus.value = "FAILED";
        taskError.value = msg.message;
        clearPoll();
      }
    } catch {
      pushLog(String(evt.data));
    }
  };
  ws.onclose = () => {
    pushLog("WebSocket 已断开");
  };
  ws.onerror = () => {
    pushLog("WebSocket 错误");
  };
}

async function refreshTask() {
  if (!taskId.value) return;
  const res = await DQScanAPI.getTask(taskId.value);
  const data = res.data.data;
  taskStatus.value = (data.status as TaskStatus) ?? taskStatus.value;
  progress.value = Number(data.progress ?? progress.value);
  taskError.value = data.error || null;
}

async function fetchResult() {
  if (!taskId.value) return;
  try {
    const res = await DQScanAPI.getResult(taskId.value);
    result.value = res.data.data;
  } catch (e: any) {
    pushLog(`获取结果失败：${e?.message || e}`);
  }
}

async function startScan() {
  if (!uploadedFile.value?.file_id) return;
  starting.value = true;
  result.value = null;
  taskError.value = null;
  logs.value = [];
  progress.value = 0;
  taskStatus.value = "PENDING";
  gotoStep(3);

  try {
    const res = await DQScanAPI.createTask({
      file_id: uploadedFile.value.file_id,
      algorithm: selectedAlgorithm.value,
      params: {
        modules: selectedModules.value?.length ? selectedModules.value : undefined,
      },
    });
    taskId.value = res.data.data.task_id;
    pushLog(`任务已创建：${taskId.value}`);
    taskStatus.value = "RUNNING";
    connectWs(taskId.value);

    clearPoll();
    pollTimer = window.setInterval(async () => {
      try {
        await refreshTask();
        if (taskStatus.value === "SUCCESS") {
          clearPoll();
          await fetchResult();
        } else if (taskStatus.value === "FAILED") {
          clearPoll();
        }
      } catch {}
    }, 2000);
  } finally {
    starting.value = false;
  }
}

async function downloadResultJson() {
  if (!taskId.value) return;
  const res = await DQScanAPI.downloadResult(taskId.value);
  const blob = (res as any).data as Blob;
  saveAs(blob, "result.json");
}

async function downloadArtifact(path: string, filename: string) {
  if (!taskId.value) return;
  const res = await DQScanAPI.downloadArtifact(taskId.value, path);
  const blob = (res as any).data as Blob;
  saveAs(blob, filename);
}

function moduleTitle(key: string) {
  return modules.find((m) => m.key === key)?.title || key;
}

const resultModules = computed(() => {
  const r = result.value;
  if (!r?.modules) return [];
  return Object.keys(r.modules).map((k) => {
    const mr = r.modules[k] || {};
    const rep = r.reports?.[k]?.paths || {};
    const extra = (() => {
      if (k === "dirty_data") return { label: "异常率", value: mr.anomaly_rate };
      if (k === "distribution") return { label: "p_value", value: mr.p_value };
      if (k === "adversarial") return { label: "攻击成功率", value: mr.attack_success_rate };
      if (k === "physics") return { label: "违规率", value: mr.violation_rate };
      return null;
    })();
    return {
      key: k,
      algorithm: String(mr.algorithm || "-"),
      hasIssues: !!mr.has_issues,
      totalIssues: Number(mr.total_issues ?? 0),
      issuePercentage: Number(mr.issue_percentage ?? 0),
      extraLabel: extra?.label,
      extraValue: extra?.value ?? "-",
      docxPath: rep.docx_report || null,
      summaryPath: rep.summary_report || null,
      docxError: rep.docx_report_error || null,
    };
  });
});

onMounted(() => {
  loadAlgorithms();
});

onBeforeUnmount(() => {
  resetWs();
  clearPoll();
});
</script>

<style scoped lang="scss">
.step-bar {
  display: flex;
  overflow: hidden;
  background: var(--el-fill-color-light);
  border-radius: 10px;
}

.step-arrow {
  position: relative;
  flex: 1;
  padding: 14px 16px;
  cursor: pointer;
  color: var(--el-text-color-regular);
  text-align: center;
  user-select: none;
  transition: all 0.2s ease;
}

.step-arrow::after {
  position: absolute;
  top: 0;
  right: -18px;
  width: 0;
  height: 0;
  content: "";
  border-top: 24px solid transparent;
  border-bottom: 24px solid transparent;
  border-left: 18px solid var(--el-fill-color-light);
  z-index: 1;
  transition: all 0.2s ease;
}

.step-arrow.active {
  color: #fff;
  background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
}

.step-arrow.active::after {
  border-left-color: #6366f1;
}

.step-arrow.completed {
  color: #fff;
  background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
  opacity: 0.9;
}

.step-arrow.completed::after {
  border-left-color: #6366f1;
}

.step-arrow:last-child::after {
  display: none;
}

.modality-card {
  cursor: pointer;
  transition: all 0.15s ease;
}
.modality-card.is-active {
  border-color: var(--el-color-primary);
}
.modality-card.is-disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.log-pre {
  padding: 10px;
  margin: 0;
  font-family: ui-monospace, sfmono-regular, menlo, monaco, consolas, "Liberation Mono", "Courier New",
    monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>

<template>
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
</template>

<script setup lang="ts">
import { useDqscanInject } from "../composables/useDqscanState";

const {
  activeStep, gotoStep,
  taskId, progress, logs, taskError,
  taskStatus, statusText, statusTagType, progressStatus,
  resultReady, refreshTask,
} = useDqscanInject();
</script>

<style scoped>
.log-pre {
  padding: 10px;
  margin: 0;
  font-family: ui-monospace, sfmono-regular, menlo, monaco, consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>

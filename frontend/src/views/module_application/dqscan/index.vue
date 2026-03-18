<template>
  <div class="app-container">
    <el-card shadow="hover">
      <template #header>
        <div class="flex-x-between">
          <div class="flex items-center gap-2">
            <div class="i-svg:table w-5 h-5" />
            <span class="font-bold">数据集质量探测引擎</span>
          </div>
          <div class="flex items-center gap-2">
            <el-tag :type="statusTagType" effect="plain">{{ statusText }}</el-tag>
            <el-button icon="refresh" @click="resetAll">重置</el-button>
          </div>
        </div>
      </template>

      <!-- 顶部流程条（箭头样式） -->
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

      <!-- Step components -->
      <StepUpload />
      <StepConfig />
      <StepExecution />
      <StepReport />
    </el-card>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: "DQScan", inheritAttrs: false });

import { provide } from "vue";
import { DqscanStateKey, useDqscanState } from "./composables/useDqscanState";
import StepUpload from "./components/StepUpload.vue";
import StepConfig from "./components/StepConfig.vue";
import StepExecution from "./components/StepExecution.vue";
import StepReport from "./components/StepReport.vue";

const state = useDqscanState();
provide(DqscanStateKey, state);

const {
  activeStep, gotoStep, stepClass,
  statusTagType, statusText, resetAll,
  initDerivedState, setupWatchers, setupLifecycle,
} = state;

// Initialize derived state, watchers, and lifecycle hooks
initDerivedState();
setupWatchers();
setupLifecycle();
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

/* report metric cards */
.report-metric-card {
  text-align: center;
}

.report-metric-value {
  font-size: 32px;
  font-weight: 700;
  line-height: 1.1;
}

.report-metric-label {
  margin-top: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

/* defect tree */
.dqscan-defect-tree {
  margin-top: 10px;
  padding: 4px 2px;
  border-radius: 10px;
  background: var(--el-fill-color-light);
}

.dqscan-defect-tree :deep(.el-tree-node__content) {
  align-items: flex-start;
  padding-top: 6px;
  padding-bottom: 6px;
}

.dqscan-defect-node-title {
  display: flex;
  align-items: center;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.dqscan-defect-node-desc {
  margin-top: 2px;
  font-size: 12px;
  line-height: 1.3;
  color: var(--el-text-color-secondary);
}

/* stat blocks */
.dqscan-stat {
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--el-fill-color-light);
}

.dqscan-stat-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.dqscan-stat-value {
  margin-top: 2px;
  font-size: 22px;
  font-weight: 800;
  color: var(--el-text-color-primary);
}

/* module pane */
.dqscan-module-pane {
  min-height: 680px;
}

/* utility list */
.dqscan-ul {
  padding-left: 18px;
  margin: 0;
}
.dqscan-ul li {
  margin: 6px 0;
  color: var(--el-text-color-regular);
}

/* defect/module workbench */
.dqscan-defect-workbench :deep(.el-collapse-item__header) {
  padding-left: 10px;
  padding-right: 10px;
}

.dqscan-defect-workbench :deep(.el-collapse-item__content) {
  padding: 12px 10px 18px;
}

.dqscan-module-workbench :deep(.el-collapse-item__header) {
  padding-left: 10px;
  padding-right: 10px;
}

.dqscan-module-workbench :deep(.el-collapse-item__content) {
  padding: 12px 10px 18px;
}

/* module tabs */
.dqscan-module-tabs :deep(.el-tabs__content) {
  padding: 10px;
}

.dqscan-module-tabs :deep(.el-tabs__item) {
  height: 44px;
  line-height: 44px;
  font-weight: 700;
}

/* panel card */
.dqscan-panel-card {
  border-radius: 12px;
}

/* collapse title */
.dqscan-collapse-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 10px;
}

.dqscan-collapse-title-text {
  font-weight: 800;
  color: var(--el-text-color-primary);
}

/* config tabs */
.dqscan-config-tabs :deep(.el-tabs__content) {
  padding-left: 8px;
}

.dqscan-config-tabs :deep(.el-tabs__item) {
  height: 44px;
  line-height: 44px;
}

/* algorithm select popper (global) */
:global(.dqscan-algo-select-popper) {
  min-width: 520px !important;
  max-width: calc(100vw - 40px) !important;
}

:global(.dqscan-algo-select-popper .el-select-dropdown__item) {
  height: auto !important;
  line-height: 1.3 !important;
  padding: 10px 12px !important;
  white-space: normal !important;
}

:global(.dqscan-algo-select-popper .dqscan-algo-option) {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  justify-content: space-between;
}

:global(.dqscan-algo-select-popper .dqscan-algo-option-title) {
  font-weight: 700;
  color: var(--el-text-color-primary);
}

:global(.dqscan-algo-select-popper .dqscan-algo-option-desc) {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.4;
  color: var(--el-text-color-secondary);
}

/* missing executor row highlight */
.dqscan-module-tabs :deep(.dqscan-row-missing-executor td) {
  background-color: var(--el-color-danger-light-9);
}

/* issue table row highlights */
.dqscan-issue-table :deep(.dqscan-issue-anomaly td) {
  background-color: rgba(220, 53, 69, 0.06);
}
.dqscan-issue-table :deep(.dqscan-issue-missing td) {
  background-color: rgba(255, 193, 7, 0.10);
}
.dqscan-issue-table :deep(.dqscan-issue-duplicate td) {
  background-color: rgba(23, 162, 184, 0.06);
}
.dqscan-issue-table :deep(.dqscan-issue-label_mismatch td) {
  background-color: rgba(111, 66, 193, 0.06);
}
.dqscan-issue-table :deep(.dqscan-issue-anomaly td:first-child) {
  box-shadow: inset 4px 0 0 #DC3545;
}
.dqscan-issue-table :deep(.dqscan-issue-missing td:first-child) {
  box-shadow: inset 4px 0 0 #FFC107;
}
.dqscan-issue-table :deep(.dqscan-issue-duplicate td:first-child) {
  box-shadow: inset 4px 0 0 #17A2B8;
}
.dqscan-issue-table :deep(.dqscan-issue-label_mismatch td:first-child) {
  box-shadow: inset 4px 0 0 #6F42C1;
}

/* log pre */
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

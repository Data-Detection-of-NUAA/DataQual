<template>
  <!-- Step 4: results -->
  <el-card v-show="activeStep === 4" shadow="never" class="mt-4">
    <template #header>
      <div class="flex-x-between">
        <div class="font-bold">查看结果</div>
        <div class="flex items-center gap-2">
          <el-button v-if="taskId" icon="refresh" @click="fetchResult">刷新结果</el-button>
          <el-button v-if="taskId" type="primary" icon="download" @click="downloadResultJson">
            下载原始结果
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
                    下载摘要
                  </el-button>
                  <el-tooltip v-if="m.docxError" :content="m.docxError">
                    <el-tag type="danger" effect="plain">报告生成失败</el-tag>
                  </el-tooltip>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>

        <!-- 图片错标检测专用 Tab -->
        <el-tab-pane v-if="isImageResult" label="图片错标检测">
          <el-card shadow="never" class="mb-3">
            <template #header><div class="font-bold">检测概览</div></template>
            <el-descriptions :column="4" border>
              <el-descriptions-item label="算法">{{ imageResult?.algorithm ?? "-" }}</el-descriptions-item>
              <el-descriptions-item label="检测数量">{{ imageResult?.image_label_mismatch_count ?? 0 }}</el-descriptions-item>
              <el-descriptions-item label="错标率">{{ ((imageResult?.image_label_mismatch_rate ?? 0) * 100).toFixed(2) }}%</el-descriptions-item>
              <el-descriptions-item label="总图片数">{{ imageResult?.total_images ?? "-" }}</el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- 混淆对 Top -->
          <el-card v-if="imageConfusionPairs.length" shadow="never" class="mb-3">
            <template #header><div class="font-bold">高频混淆对 Top-{{ imageConfusionPairs.length }}</div></template>
            <el-table :data="imageConfusionPairs" border size="small">
              <el-table-column label="原始标签" width="180">
                <template #default="{ row }">
                  <el-tag size="small" type="danger" effect="plain">{{ row.given_label }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="" width="36">
                <template #default><span class="text-gray text-xs">&rarr;</span></template>
              </el-table-column>
              <el-table-column label="建议标签" width="180">
                <template #default="{ row }">
                  <el-tag size="small" type="success" effect="plain">{{ row.suggested_label }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="count" label="数量" width="100" />
            </el-table>
          </el-card>

          <!-- 各类错标率 -->
          <el-card v-if="imagePerClassIssueRateRows.length" shadow="never" class="mb-3">
            <template #header><div class="font-bold">各类别错标率</div></template>
            <el-table :data="imagePerClassIssueRateRows" border size="small">
              <el-table-column prop="label" label="类别" min-width="150" />
              <el-table-column label="错标率" width="120">
                <template #default="{ row }">
                  <span :style="{ color: row.rate > 0.1 ? '#DC3545' : row.rate > 0.05 ? '#FFC107' : '#28A745' }">
                    {{ (row.rate * 100).toFixed(2) }}%
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </el-card>

          <!-- 错标图片列表 -->
          <el-card shadow="never">
            <template #header>
              <div class="flex-x-between">
                <div class="font-bold">疑似错标图片</div>
                <el-tag type="warning" effect="plain" size="small">共 {{ imageIssues.length }} 条</el-tag>
              </div>
            </template>
            <el-table :data="imageIssues" border size="small" class="dqscan-issue-table">
              <el-table-column label="图片" width="80">
                <template #default="{ row }">
                  <el-image
                    v-if="row.thumbnailUrl"
                    :src="row.thumbnailUrl"
                    :preview-src-list="[row.thumbnailUrl]"
                    fit="cover"
                    class="w-14 h-14 rounded"
                    preview-teleported
                  />
                  <span v-else class="text-gray text-xs">无缩略图</span>
                </template>
              </el-table-column>
              <el-table-column prop="image_path" label="路径" min-width="200" show-overflow-tooltip>
                <template #default="{ row }">
                  <span class="font-mono text-xs">{{ row.image_path }}</span>
                </template>
              </el-table-column>
              <el-table-column label="原始标签" width="130">
                <template #default="{ row }">
                  <el-tag size="small" type="danger" effect="plain">{{ row.given_label }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="" width="36">
                <template #default><span class="text-gray text-xs">&rarr;</span></template>
              </el-table-column>
              <el-table-column label="建议标签" width="130">
                <template #default="{ row }">
                  <el-tag size="small" type="success" effect="plain">{{ row.suggested_label }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="置信度" width="100">
                <template #default="{ row }">
                  <span class="font-bold" :style="{ color: row.confidence > 0.8 ? '#DC3545' : '#FFC107' }">
                    {{ (row.confidence * 100).toFixed(1) }}%
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="severity" label="严重度" width="90">
                <template #default="{ row }">
                  <el-tag size="small" effect="plain" :type="severityTagType(row.severity)">{{ row.severity }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="报告视图">
          <el-skeleton v-if="reportsLoading" animated :rows="8" />
          <el-empty v-else-if="!hasReports" description="暂无报告数据（请先运行检测）" />

          <div v-else>
            <el-tabs v-model="activeReportModule" type="border-card">
              <el-tab-pane v-for="m in resultModules" :key="m.key" :label="moduleTitle(m.key)" :name="m.key">
                <el-alert v-if="activeReportError" type="warning" show-icon :closable="false" :title="activeReportError" />

                <div v-else>
                  <div class="flex-x-between mb-2">
                    <div class="text-sm text-gray">
                      生成时间：{{ activeReportGeneratedAt }}
                    </div>
                    <div class="flex items-center gap-2">
                      <el-button
                        v-if="activeReportModuleMeta?.docxPath"
                        type="primary"
                        icon="download"
                        @click="downloadArtifact(activeReportModuleMeta.docxPath, `${activeReportModule}.docx`)"
                      >
                        导出 Word
                      </el-button>
                      <el-button
                        v-if="activeReportModuleMeta?.summaryPath"
                        icon="download"
                        @click="downloadArtifact(activeReportModuleMeta.summaryPath, `${activeReportModule}_summary.json`)"
                      >
                        下载摘要
                      </el-button>
                    </div>
                  </div>

                  <el-row :gutter="12" class="mb-3">
                    <el-col :span="6" :xs="12" class="mb-2">
                      <el-card shadow="never" class="report-metric-card">
                        <div class="report-metric-value" :style="{ color: scoreColor(activeReportScore) }">
                          {{ activeReportScore.toFixed(0) }}
                        </div>
                        <div class="report-metric-label">总分</div>
                      </el-card>
                    </el-col>
                    <el-col :span="6" :xs="12" class="mb-2">
                      <el-card shadow="never" class="report-metric-card">
                        <div class="report-metric-value text-gray">{{ activeReportGradeFull }}</div>
                        <div class="report-metric-label">等级</div>
                      </el-card>
                    </el-col>
                    <el-col :span="6" :xs="12" class="mb-2">
                      <el-card shadow="never" class="report-metric-card">
                        <div class="report-metric-value text-primary">{{ activeReportDataTypeCount }}</div>
                        <div class="report-metric-label">数据类型</div>
                      </el-card>
                    </el-col>
                    <el-col :span="6" :xs="12" class="mb-2">
                      <el-card shadow="never" class="report-metric-card">
                        <div class="report-metric-value" :style="{ color: activeReportIssueCount > 0 ? '#DC3545' : '#28A745' }">
                          {{ activeReportIssueCount }}
                        </div>
                        <div class="report-metric-label">问题数</div>
                      </el-card>
                    </el-col>
                  </el-row>

                  <el-card shadow="never" class="mb-3">
                    <ECharts :options="dataTypeScoreChartOptions" height="280px" />
                  </el-card>

                  <el-card shadow="never" class="mb-3">
                    <template #header>
                      <div class="font-bold">1. 检测总览</div>
                    </template>

                    <el-table :data="reportOverviewRows" border size="small">
                      <el-table-column prop="dataTypeLabel" label="数据类型" width="110" />
                      <el-table-column prop="algorithm" label="算法" min-width="160" />

                      <template v-if="activeReportModuleType === 'distribution'">
                        <el-table-column prop="pValue" label="p值" width="110" />
                        <el-table-column prop="drift" label="漂移检测" width="90" />
                      </template>

                      <template v-else-if="activeReportModuleType === 'dirty_data'">
                        <el-table-column v-if="dirtyReportShowAnomaly" prop="anomalyRate" label="异常率" width="90" />
                        <el-table-column v-if="dirtyReportShowMissing" prop="missingRate" label="缺失率" width="90" />
                        <el-table-column v-if="dirtyReportShowDuplicate" prop="duplicateRate" label="重复率" width="90" />
                        <el-table-column v-if="dirtyReportShowLabelMismatch" prop="labelMismatchRate" label="疑似错标率" width="110" />
                      </template>

                      <template v-else-if="activeReportModuleType === 'adversarial'">
                        <el-table-column prop="attackSuccessRate" label="攻击成功率" width="110" />
                        <el-table-column prop="robustnessScore" label="鲁棒性" width="90" />
                      </template>

                      <template v-else-if="activeReportModuleType === 'physics'">
                        <el-table-column prop="violationRate" label="违规率" width="90" />
                        <el-table-column prop="fidelityLevel" label="保真度" width="110" />
                      </template>

                      <el-table-column prop="score" label="评分" width="80">
                        <template #default="{ row }">
                          <span class="font-bold" :style="{ color: scoreColor(row.score) }">{{ row.score }}</span>
                        </template>
                      </el-table-column>
                      <el-table-column prop="status" label="状态" width="80">
                        <template #default="{ row }">
                          <el-tag :type="row.statusTag" effect="plain">{{ row.statusText }}</el-tag>
                        </template>
                      </el-table-column>
                    </el-table>

                    <el-card v-if="activeReportModuleType === 'dirty_data' && dirtyReportShowRateChart" shadow="never" class="mt-3">
                      <ECharts :options="dirtyRateChartOptions" height="320px" />
                    </el-card>
                  </el-card>

                  <el-card shadow="never" class="mb-3">
                    <template #header>
                      <div class="font-bold">2. 检测详情</div>
                    </template>
                    <el-collapse>
                      <el-collapse-item v-for="d in reportDetailItems" :key="d.dataTypeKey" :name="d.dataTypeKey">
                        <template #title>
                          <div class="flex items-center gap-2">
                            <span class="font-bold">{{ d.dataTypeLabel }}</span>
                            <el-tag :type="d.hasIssues ? 'warning' : 'success'" effect="plain" size="small">{{
                              d.hasIssues ? "有风险" : "正常"
                            }}</el-tag>
                          </div>
                        </template>

                        <el-descriptions :column="4" border size="small">
                          <el-descriptions-item label="算法">{{ d.algorithm }}</el-descriptions-item>
                          <el-descriptions-item label="问题数">{{ d.totalIssues }}</el-descriptions-item>
                          <el-descriptions-item label="问题比例">{{ d.issuePercentage }}</el-descriptions-item>
                          <el-descriptions-item label="评分">
                            <span class="font-bold" :style="{ color: scoreColor(d.score) }">{{ d.score }}</span>
                          </el-descriptions-item>
                        </el-descriptions>

                        <el-descriptions v-if="d.extraMetrics.length" :column="4" border size="small" class="mt-2">
                          <el-descriptions-item v-for="x in d.extraMetrics" :key="x.label" :label="x.label">{{
                            x.value
                          }}</el-descriptions-item>
                        </el-descriptions>

                        <!-- 疑似错标专用展示区 -->
                        <template v-if="d.labelMismatchIssues?.length">
                          <div class="flex items-center gap-2 mt-3 mb-2">
                            <span class="font-bold">疑似错标清单</span>
                            <el-tag type="warning" effect="plain" size="small">
                              共 {{ d.labelMismatchIssues.length }} 条
                            </el-tag>
                          </div>
                          <el-table
                            :data="d.labelMismatchIssues"
                            border
                            size="small"
                            class="dqscan-issue-table"
                          >
                            <el-table-column type="expand" width="42">
                              <template #default="{ row }">
                                <div class="p-2">
                                  <el-table v-if="row.previewRows?.length" :data="row.previewRows" border size="small">
                                    <el-table-column prop="field" label="字段" min-width="180" />
                                    <el-table-column prop="value" label="值" min-width="220" />
                                  </el-table>
                                  <el-empty v-else description="暂无样本预览" />
                                </div>
                              </template>
                            </el-table-column>
                            <el-table-column prop="data_id" label="样本 ID" width="130">
                              <template #default="{ row }">
                                <span class="font-mono text-xs">{{ row.data_id }}</span>
                              </template>
                            </el-table-column>
                            <el-table-column label="原始标签" width="150">
                              <template #default="{ row }">
                                <el-tag size="small" type="danger" effect="plain">{{ row.given_label }}</el-tag>
                              </template>
                            </el-table-column>
                            <el-table-column label="" width="36">
                              <template #default>
                                <span class="text-gray text-xs">&rarr;</span>
                              </template>
                            </el-table-column>
                            <el-table-column label="建议标签" width="150">
                              <template #default="{ row }">
                                <el-tag size="small" type="success" effect="plain">{{ row.suggested_label }}</el-tag>
                              </template>
                            </el-table-column>
                            <el-table-column prop="prob_given" label="原始置信度" width="100" />
                            <el-table-column prop="prob_suggested" label="预测置信度" width="100" />
                            <el-table-column prop="severity" label="严重度" width="90">
                              <template #default="{ row }">
                                <el-tag size="small" effect="plain" :type="severityTagType(row.severity)">{{ row.severity }}</el-tag>
                              </template>
                            </el-table-column>
                          </el-table>
                        </template>

                        <el-table
                          v-if="d.sampleRows.length"
                          :data="d.sampleRows"
                          border
                          size="small"
                          class="mt-2 dqscan-issue-table"
                          :row-class-name="issueRowClassName"
                        >
                          <el-table-column prop="issue_type" label="问题类型" width="140">
                            <template #default="{ row }">
                              <el-tag size="small" effect="plain" :style="issueTagStyle(row.issue_type)">{{ row.issue_type }}</el-tag>
                            </template>
                          </el-table-column>
                          <el-table-column prop="data_id" label="样本" width="160">
                            <template #default="{ row }">
                              <span class="font-mono text-xs">{{ row.data_id }}</span>
                            </template>
                          </el-table-column>
                          <el-table-column prop="severity" label="严重度" width="90">
                            <template #default="{ row }">
                              <el-tag size="small" effect="plain" :type="severityTagType(row.severity)">{{ row.severity }}</el-tag>
                            </template>
                          </el-table-column>

                          <el-table-column v-for="c in d.sampleColumns" :key="c" :label="c" min-width="140" show-overflow-tooltip>
                            <template #default="{ row }">
                              <span class="text-xs">{{ row.row_preview?.[c] ?? "-" }}</span>
                            </template>
                          </el-table-column>
                        </el-table>

                        <el-table
                          v-if="d.issues.length"
                          :data="d.issues"
                          border
                          size="small"
                          class="mt-2 dqscan-issue-table"
                          :row-class-name="issueRowClassName"
                        >
                          <el-table-column type="expand" width="42">
                            <template #default="{ row }">
                              <div class="p-2">
                                <div class="flex items-center gap-2 mb-2">
                                  <el-tag size="small" effect="plain" :style="issueTagStyle(row.issue_type)">{{ row.issue_type }}</el-tag>
                                  <span class="font-mono text-xs text-gray">{{ row.data_id }}</span>
                                  <el-tag size="small" effect="plain" :type="severityTagType(row.severity)">{{ row.severity }}</el-tag>
                                </div>
                                <el-text type="info" class="block">{{ row.detailsText }}</el-text>

                                <el-divider class="my-2" />

                                <el-table v-if="row.previewRows?.length" :data="row.previewRows" border size="small">
                                  <el-table-column prop="field" label="字段" min-width="180" />
                                  <el-table-column prop="value" label="值" min-width="220" />
                                </el-table>
                                <el-empty v-else description="暂无样本预览" />
                              </div>
                            </template>
                          </el-table-column>
                          <el-table-column prop="issue_type" label="问题类型" width="140">
                            <template #default="{ row }">
                              <el-tag size="small" effect="plain" :style="issueTagStyle(row.issue_type)">{{ row.issue_type }}</el-tag>
                            </template>
                          </el-table-column>
                          <el-table-column prop="data_id" label="位置/字段" width="160">
                            <template #default="{ row }">
                              <span class="font-mono text-xs">{{ row.data_id }}</span>
                            </template>
                          </el-table-column>
                          <el-table-column prop="severity" label="严重度" width="90">
                            <template #default="{ row }">
                              <el-tag size="small" effect="plain" :type="severityTagType(row.severity)">{{ row.severity }}</el-tag>
                            </template>
                          </el-table-column>
                          <el-table-column prop="detailsText" label="详情" min-width="180" />
                        </el-table>

                        <el-empty v-else description="无问题" />
                      </el-collapse-item>
                    </el-collapse>
                  </el-card>

                  <el-card shadow="never">
                    <template #header>
                      <div class="font-bold">3. 评分说明</div>
                    </template>

                    <el-alert type="info" show-icon :closable="false" :title="activeScoringExplain" class="mb-2" />

                    <el-table v-if="scoringRuleRows.length" :data="scoringRuleRows" border size="small" class="mb-3">
                      <el-table-column v-for="c in scoringRuleColumns" :key="c.key" :prop="c.key" :label="c.label" :width="c.width" />
                    </el-table>

                    <div class="font-bold mb-2">3.2 评级标准</div>
                    <el-table :data="gradeRuleRows" border size="small">
                      <el-table-column prop="grade" label="等级" width="80" />
                      <el-table-column prop="range" label="分数范围" width="120" />
                      <el-table-column prop="desc" label="说明" min-width="160" />
                    </el-table>
                  </el-card>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>
        </el-tab-pane>

      </el-tabs>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from "vue";
import ECharts from "@/components/ECharts/index.vue";
import {
  useDqscanInject,
  scoreColor, gradeFull, severityTagType, issueTagStyle, issueRowClassName, issueKindFromType,
  type IssueKind, ISSUE_COLORS,
} from "../composables/useDqscanState";

const {
  activeStep, selectedModality,
  taskId, result, reports, reportsLoading, activeReportModule,
  fetchResult, downloadResultJson, downloadArtifact, moduleTitle,
} = useDqscanInject();

// ───────────────────────── local helpers ─────────────────────────

function statusFromScore(score: number): { statusTag: "success" | "warning" | "danger"; statusText: string } {
  if (score >= 90) return { statusTag: "success", statusText: "[OK]" };
  if (score >= 70) return { statusTag: "warning", statusText: "[!]" };
  return { statusTag: "danger", statusText: "[X]" };
}

function dataTypeLabel(dt: string): string {
  const map: Record<string, string> = { tabular: "表格数据", timeseries: "时序数据", image: "图像数据", text: "文本数据" };
  return map[dt] || dt;
}

function issueDetailsText(details: any): string {
  if (!details) return "";
  if (typeof details === "string") return details;
  try {
    if (typeof details === "object") {
      const pairs = Object.entries(details)
        .slice(0, 6)
        .map(([k, v]) => `${k}=${typeof v === "object" ? JSON.stringify(v) : String(v)}`);
      return pairs.join("; ");
    }
    return String(details);
  } catch {
    return String(details);
  }
}

// ───────────────────────── image report ─────────────────────────

const isImageResult = computed(() => {
  return selectedModality.value === "image" || result.value?.summary?.data_type === "image";
});

const imageResult = computed(() => {
  const r = result.value;
  if (!r) return null;
  // Image result may be in modules.dirty_data or top-level
  const dd = r.modules?.dirty_data;
  if (dd?.image_label_mismatch_count != null) return dd;
  // Fallback: check if the result itself has image fields
  if (r.image_label_mismatch_count != null) return r;
  return dd || null;
});

const imageConfusionPairs = computed(() => {
  return Array.isArray(imageResult.value?.confusion_pairs_top) ? imageResult.value.confusion_pairs_top : [];
});

const imagePerClassIssueRateRows = computed(() => {
  const rates = imageResult.value?.per_class_issue_rate;
  if (!rates || typeof rates !== "object") return [];
  return Object.entries(rates)
    .map(([label, rate]) => ({ label, rate: Number(rate) }))
    .sort((a, b) => b.rate - a.rate);
});

const imageIssues = computed(() => {
  const issues = imageResult.value?.detailed_issues;
  if (!Array.isArray(issues)) return [];
  return issues.slice(0, 500).map((it: any) => ({
    image_path: String(it?.details?.image_path || it?.data_id || "-"),
    given_label: String(it?.details?.given_label ?? "-"),
    suggested_label: String(it?.details?.suggested_label ?? "-"),
    confidence: Number(it?.details?.confidence_score ?? 0),
    severity: String(it?.severity ?? "-"),
    thumbnailUrl: it?.details?.thumbnail_path
      ? `/api/application/dqscan/tasks/${taskId.value}/artifact?path=${encodeURIComponent(it.details.thumbnail_path)}`
      : null,
  }));
});

// ───────────────────────── computed: module results ─────────────────────────

const resultModules = computed(() => {
  const r = result.value;
  if (!r?.modules) return [];
  return Object.keys(r.modules).map((k) => {
    const mr = r.modules[k] || {};
    const rep = r.reports?.[k]?.paths || {};
    const extra = (() => {
      if (k === "dirty_data") {
        const checks = Array.isArray(mr.enabled_checks) ? mr.enabled_checks.map((x: any) => String(x)) : [];
        if (!checks.length) return { label: "异常率", value: mr.anomaly_rate };
        const hasAnomaly = checks.includes("anomaly");
        const hasMissing = checks.includes("missing");
        const hasDuplicate = checks.includes("duplicate");
        const hasRange = checks.includes("range");
        const hasLabelMismatch = checks.includes("label_mismatch");
        if (hasLabelMismatch && !(hasAnomaly || hasMissing || hasDuplicate || hasRange)) {
          return { label: "疑似错标率", value: mr.label_mismatch_rate };
        }
        if (hasAnomaly) return { label: "异常率", value: mr.anomaly_rate };
        if (hasMissing) return { label: "缺失率", value: mr.missing_rate };
        if (hasDuplicate) return { label: "重复率", value: mr.duplicate_rate };
        if (hasLabelMismatch) return { label: "疑似错标率", value: mr.label_mismatch_rate };
        if (hasRange) return { label: "值域违规数", value: mr?.range_violations?.total_violations ?? 0 };
        return null;
      }
      if (k === "distribution") return { label: "p值", value: mr.p_value };
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

// ───────────────────────── computed: report view ─────────────────────────

const hasReports = computed(() => Object.keys(reports.value || {}).length > 0);
const activeReport = computed(() => (activeReportModule.value ? reports.value?.[activeReportModule.value] : null));
const activeReportError = computed(() => {
  const r = activeReport.value;
  if (!r) return null;
  return r.error ? String(r.error) : null;
});
const activeReportModuleType = computed(() => {
  const r = activeReport.value;
  return String(r?.metadata?.module_type || activeReportModule.value || "");
});
const activeReportGeneratedAt = computed(() => String(activeReport.value?.metadata?.generated_at || "-"));
const activeReportScore = computed(() => Number(activeReport.value?.scoring?.total_score ?? 0));
const activeReportGradeFull = computed(() => gradeFull(activeReportScore.value));
const activeReportDataTypeCount = computed(() => Object.keys(activeReport.value?.results || {}).length);
const activeReportIssueCount = computed(() => {
  const rs = activeReport.value?.results || {};
  return Object.values(rs).reduce((acc: number, v: any) => acc + Number(v?.total_issues ?? 0), 0);
});
const activeReportModuleMeta = computed(() => resultModules.value.find((x) => x.key === activeReportModule.value) || null);

// ───────────────────────── dirty report checks ─────────────────────────

const dirtyReportEnabledChecks = computed(() => {
  if (activeReportModuleType.value !== "dirty_data") return new Set<string>();
  const rs: Record<string, any> = activeReport.value?.results || {};
  const out = new Set<string>();
  for (const dt of Object.keys(rs)) {
    const checks = rs?.[dt]?.enabled_checks;
    if (!Array.isArray(checks)) continue;
    for (const c of checks) {
      const cc = String(c || "").trim();
      if (cc) out.add(cc);
    }
  }
  return out;
});
const dirtyReportShowCheck = (check: string) => {
  const s = dirtyReportEnabledChecks.value;
  if (!s.size) return true;
  return s.has(check);
};
const dirtyReportShowAnomaly = computed(() => dirtyReportShowCheck("anomaly"));
const dirtyReportShowMissing = computed(() => dirtyReportShowCheck("missing"));
const dirtyReportShowDuplicate = computed(() => dirtyReportShowCheck("duplicate"));
const dirtyReportShowLabelMismatch = computed(() => dirtyReportShowCheck("label_mismatch"));
const dirtyReportShowRateChart = computed(
  () =>
    dirtyReportShowAnomaly.value ||
    dirtyReportShowMissing.value ||
    dirtyReportShowDuplicate.value ||
    dirtyReportShowLabelMismatch.value,
);

// ───────────────────────── charts ─────────────────────────

const dataTypeScoreChartOptions = computed(() => {
  const dtScores: Record<string, any> = activeReport.value?.scoring?.data_type_scores || {};
  const order = ["text", "image", "timeseries", "tabular"];
  const keys = [...order.filter((k) => k in dtScores), ...Object.keys(dtScores).filter((k) => !order.includes(k))];
  const labels = keys.map((k) => dataTypeLabel(k));
  const values = keys.map((k) => Number(dtScores[k]?.score ?? 0));
  return {
    title: { text: "各数据类型评分", left: "center", textStyle: { fontSize: 16, fontWeight: "bold" } },
    grid: { left: 90, right: 60, top: 60, bottom: 50 },
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    xAxis: {
      type: "value",
      min: 0,
      max: 110,
      name: "分数",
      splitLine: { lineStyle: { type: "dashed" } },
    },
    yAxis: { type: "category", data: labels, axisTick: { show: false } },
    series: [
      {
        type: "bar",
        data: values.map((v) => ({ value: v, itemStyle: { color: scoreColor(v) } })),
        label: { show: true, position: "right" },
        barWidth: 22,
        markLine: {
          symbol: ["none", "none"],
          label: { show: false },
          lineStyle: { type: "dashed", color: "#DEE2E6" },
          data: [{ xAxis: 60 }, { xAxis: 70 }, { xAxis: 80 }, { xAxis: 90 }],
        },
      },
    ],
  } as any;
});

const dirtyRateChartOptions = computed(() => {
  const rs: Record<string, any> = activeReport.value?.results || {};
  const order = ["tabular", "timeseries", "image", "text"];
  const keys = [...order.filter((k) => k in rs), ...Object.keys(rs).filter((k) => !order.includes(k))];
  const labels = keys.map((k) => dataTypeLabel(k).replace("数据", ""));
  const anomaly = keys.map((k) => Number(rs[k]?.anomaly_rate ?? 0) * 100);
  const missing = keys.map((k) => Number(rs[k]?.missing_rate ?? 0) * 100);
  const duplicate = keys.map((k) => Number(rs[k]?.duplicate_rate ?? 0) * 100);
  const labelMismatch = keys.map((k) => Number(rs[k]?.label_mismatch_rate ?? 0) * 100);

  const series: any[] = [];
  const legend: string[] = [];
  if (dirtyReportShowAnomaly.value) {
    legend.push("异常率");
    series.push({
      name: "异常率",
      type: "bar",
      data: anomaly,
      itemStyle: { color: "#DC3545" },
      markLine: {
        symbol: ["none", "none"],
        label: { show: false },
        lineStyle: { type: "dashed" },
        data: [
          { yAxis: 5, lineStyle: { color: "#28A745" } },
          { yAxis: 10, lineStyle: { color: "#FFC107" } },
        ],
      },
    });
  }
  if (dirtyReportShowMissing.value) {
    legend.push("缺失率");
    series.push({ name: "缺失率", type: "bar", data: missing, itemStyle: { color: "#FFC107" } });
  }
  if (dirtyReportShowDuplicate.value) {
    legend.push("重复率");
    series.push({ name: "重复率", type: "bar", data: duplicate, itemStyle: { color: "#17A2B8" } });
  }
  if (dirtyReportShowLabelMismatch.value) {
    legend.push("疑似错标率");
    series.push({ name: "疑似错标率", type: "bar", data: labelMismatch, itemStyle: { color: "#6F42C1" } });
  }
  return {
    title: { text: "问题率对比", left: "center", textStyle: { fontSize: 16, fontWeight: "bold" } },
    grid: { left: 70, right: 30, top: 60, bottom: 50 },
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    legend: { top: 30, right: 10, data: legend },
    xAxis: { type: "category", data: labels },
    yAxis: { type: "value", name: "百分比 (%)", min: 0, max: 100 },
    series,
  } as any;
});

// ───────────────────────── overview table ─────────────────────────

const reportOverviewRows = computed(() => {
  const payload = activeReport.value;
  if (!payload) return [];
  const moduleType = String(payload?.metadata?.module_type || "");
  const rs: Record<string, any> = payload.results || {};
  const dtScores: Record<string, any> = payload.scoring?.data_type_scores || {};
  return Object.keys(rs).map((dt) => {
    const dtResult = rs[dt] || {};
    const dtScore = dtScores?.[dt] || {};
    const score = Number(dtScore?.score ?? 0);
    const status = statusFromScore(score);
    const base: Record<string, any> = {
      dataTypeKey: dt,
      dataTypeLabel: dataTypeLabel(dt),
      algorithm: String(dtResult.algorithm || "N/A"),
      score: Number.isFinite(score) ? Number(score.toFixed(0)) : 0,
      statusTag: status.statusTag,
      statusText: status.statusText,
    };
    if (moduleType === "distribution") {
      base.pValue = Number(dtScore?.p_value ?? dtResult.p_value ?? 1).toFixed(4);
      base.drift = dtResult.drift_detected ? "是" : "否";
    } else if (moduleType === "dirty_data") {
      if (dirtyReportShowAnomaly.value) base.anomalyRate = `${(Number(dtResult.anomaly_rate ?? 0) * 100).toFixed(1)}%`;
      if (dirtyReportShowMissing.value) base.missingRate = `${(Number(dtResult.missing_rate ?? 0) * 100).toFixed(1)}%`;
      if (dirtyReportShowDuplicate.value) base.duplicateRate = `${(Number(dtResult.duplicate_rate ?? 0) * 100).toFixed(1)}%`;
      if (dirtyReportShowLabelMismatch.value) base.labelMismatchRate = `${(Number(dtResult.label_mismatch_rate ?? 0) * 100).toFixed(1)}%`;
    } else if (moduleType === "adversarial") {
      base.attackSuccessRate = `${(Number(dtResult.attack_success_rate ?? 0) * 100).toFixed(1)}%`;
      base.robustnessScore = `${(Number(dtResult.robustness_score ?? 0) * 100).toFixed(1)}%`;
    } else if (moduleType === "physics") {
      base.violationRate = `${(Number(dtResult.violation_rate ?? 0) * 100).toFixed(1)}%`;
      base.fidelityLevel = String(dtScore?.fidelity_level || "N/A");
    }
    return base;
  });
});

// ───────────────────────── detail items ─────────────────────────

const reportDetailItems = computed(() => {
  const payload = activeReport.value;
  if (!payload) return [];
  const moduleType = String(payload?.metadata?.module_type || "");
  const rs: Record<string, any> = payload.results || {};
  const dtScores: Record<string, any> = payload.scoring?.data_type_scores || {};

  return Object.keys(rs).map((dt) => {
    const dtResult = rs[dt] || {};
    const dtScore = dtScores?.[dt] || {};
    const score = Number(dtScore?.score ?? 0);
    const extraMetrics: { label: string; value: string }[] = [];

    if (moduleType === "distribution") {
      extraMetrics.push({ label: "p值", value: String(Number(dtScore?.p_value ?? dtResult.p_value ?? 1).toFixed(6)) });
      extraMetrics.push({ label: "显著性", value: String(dtScore?.significance || "N/A") });
      extraMetrics.push({ label: "漂移检测", value: dtResult.drift_detected ? "是" : "否" });
    } else if (moduleType === "dirty_data") {
      extraMetrics.push({ label: "异常率", value: `${(Number(dtResult.anomaly_rate ?? 0) * 100).toFixed(2)}%` });
      extraMetrics.push({ label: "缺失率", value: `${(Number(dtResult.missing_rate ?? 0) * 100).toFixed(2)}%` });
      extraMetrics.push({ label: "重复率", value: `${(Number(dtResult.duplicate_rate ?? 0) * 100).toFixed(2)}%` });
      extraMetrics.push({ label: "疑似错标率", value: `${(Number(dtResult.label_mismatch_rate ?? 0) * 100).toFixed(2)}%` });
    } else if (moduleType === "adversarial") {
      extraMetrics.push({ label: "攻击成功率", value: `${(Number(dtResult.attack_success_rate ?? 0) * 100).toFixed(2)}%` });
      extraMetrics.push({ label: "鲁棒性", value: `${(Number(dtResult.robustness_score ?? 0) * 100).toFixed(2)}%` });
      if (dtResult.total_issues != null && dtResult.total_samples != null) {
        extraMetrics.push({ label: "成功攻击数", value: `${dtResult.total_issues}/${dtResult.total_samples}` });
      }
    } else if (moduleType === "physics") {
      extraMetrics.push({ label: "违规率", value: `${(Number(dtResult.violation_rate ?? 0) * 100).toFixed(2)}%` });
      extraMetrics.push({ label: "因果得分", value: `${(Number(dtResult.causality_score ?? 0) * 100).toFixed(2)}%` });
      extraMetrics.push({ label: "保真度", value: String(dtScore?.fidelity_level || "N/A") });
      const dd = dtResult.data_driven;
      if (dd && typeof dd === "object" && dd.enabled !== false && dd.methods_used) {
        extraMetrics.push({ label: "数据驱动方法", value: (dd.methods_used || []).join(", ") || "无" });
        extraMetrics.push({ label: "数据驱动异常数", value: String(dd.anomaly_count ?? 0) });
        extraMetrics.push({ label: "数据驱动异常率", value: `${(Number(dd.anomaly_rate ?? 0) * 100).toFixed(2)}%` });
      }
    }

    // Prefer full issues from task `result.json` (not compacted like report json).
    const fullModuleRes = (result.value?.modules || {})?.[activeReportModule.value];
    const fullIssues = Array.isArray(fullModuleRes?.detailed_issues) ? fullModuleRes.detailed_issues : null;
    const allRawIssues = fullIssues || (Array.isArray(dtResult.detailed_issues) ? dtResult.detailed_issues : []);
    const lmRaw = allRawIssues.filter((it: any) => issueKindFromType(it?.issue_type) === "label_mismatch");
    const otherRaw = allRawIssues.filter((it: any) => issueKindFromType(it?.issue_type) !== "label_mismatch");

    const normalizedIssues = otherRaw.slice(0, 50).map((it: any) => ({
      issue_type: String(it?.issue_type ?? "未知"),
      data_id: String(it?.data_id ?? "-"),
      severity: String(it?.severity ?? "-"),
      detailsText: issueDetailsText(it?.details),
      issue_kind: issueKindFromType(it?.issue_type),
      row_preview: (() => {
        const rp = it?.details?.row_preview;
        if (!rp || typeof rp !== "object" || Array.isArray(rp)) return null;
        return rp as Record<string, any>;
      })(),
      previewRows: (() => {
        const rp = it?.details?.row_preview;
        if (!rp || typeof rp !== "object") return [];
        try {
          return Object.entries(rp)
            .slice(0, 30)
            .map(([k, v]) => ({
              field: String(k),
              value: typeof v === "object" ? JSON.stringify(v) : String(v),
            }));
        } catch {
          return [];
        }
      })(),
    }));

    const labelMismatchIssues = lmRaw.slice(0, 500).map((it: any) => ({
      data_id: String(it?.data_id ?? "-"),
      given_label: String(it?.details?.given_label ?? "-"),
      suggested_label: String(it?.details?.suggested_label ?? "-"),
      prob_given: `${(Number(it?.details?.prob_given ?? 0) * 100).toFixed(1)}%`,
      prob_suggested: `${(Number(it?.details?.prob_suggested ?? 0) * 100).toFixed(1)}%`,
      severity: String(it?.severity ?? "-"),
      previewRows: (() => {
        const rp = it?.details?.row_preview;
        if (!rp || typeof rp !== "object") return [];
        try {
          return Object.entries(rp)
            .slice(0, 30)
            .map(([k, v]) => ({
              field: String(k),
              value: typeof v === "object" ? JSON.stringify(v) : String(v),
            }));
        } catch {
          return [];
        }
      })(),
    }));

    const sampleRows = normalizedIssues
      .filter((x: any) => x?.row_preview && ["anomaly", "duplicate"].includes(x.issue_kind))
      .slice(0, 20)
      .map((x: any) => ({
        issue_type: x.issue_type,
        data_id: x.data_id,
        severity: x.severity,
        row_preview: x.row_preview,
      }));
    const sampleColumns = (() => {
      const first = sampleRows[0]?.row_preview;
      if (!first) return [];
      try {
        return Object.keys(first).slice(0, 10);
      } catch {
        return [];
      }
    })();

    return {
      dataTypeKey: dt,
      dataTypeLabel: dataTypeLabel(dt),
      algorithm: String(dtResult.algorithm || "N/A"),
      hasIssues: !!dtResult.has_issues,
      totalIssues: Number(dtResult.total_issues ?? 0),
      issuePercentage: `${(Number(dtResult.issue_percentage ?? 0) * 100).toFixed(2)}%`,
      score: Number.isFinite(score) ? Number(score.toFixed(0)) : 0,
      extraMetrics,
      sampleRows,
      sampleColumns,
      issues: normalizedIssues,
      labelMismatchIssues,
    };
  });
});

// ───────────────────────── scoring rules ─────────────────────────

const activeScoringExplain = computed(() => {
  switch (activeReportModuleType.value) {
    case "distribution":
      return "评分基于统计显著性 p 值";
    case "dirty_data":
      return "评分采用扣分制（满分 100）";
    case "adversarial":
      return "评分基于攻击成功率评估鲁棒性";
    case "physics":
      return "评分基于约束违规率评估保真度（规则驱动 + 数据驱动）";
    default:
      return "评分说明";
  }
});

const scoringRuleColumns = computed(() => {
  if (activeReportModuleType.value === "dirty_data") {
    return [
      { key: "metric", label: "指标", width: 90 },
      { key: "t1", label: "<=阈值1", width: 120 },
      { key: "t2", label: "阈值1~2", width: 130 },
      { key: "t3", label: "阈值2~3", width: 130 },
      { key: "t4", label: ">阈值3", width: 130 },
    ];
  }
  return [
    { key: "c1", label: "范围", width: 180 },
    { key: "c2", label: "等级/显著性", width: 140 },
    { key: "c3", label: "评分", width: 100 },
  ];
});

const scoringRuleRows = computed(() => {
  const t = activeReportModuleType.value;
  if (t === "distribution") {
    return [
      { c1: "p >= 0.05", c2: "不显著", c3: "100分" },
      { c1: "0.01 <= p < 0.05", c2: "弱显著", c3: "80分" },
      { c1: "0.001 <= p < 0.01", c2: "显著", c3: "60分" },
      { c1: "p < 0.001", c2: "高度显著", c3: "40分" },
    ];
  }
  if (t === "adversarial") {
    return [
      { c1: "<= 10%", c2: "高鲁棒", c3: "100分" },
      { c1: "10% ~ 30%", c2: "中等鲁棒", c3: "80分" },
      { c1: "30% ~ 50%", c2: "低鲁棒", c3: "60分" },
      { c1: "> 50%", c2: "极低鲁棒", c3: "40分" },
    ];
  }
  if (t === "physics") {
    return [
      { c1: "<= 1%", c2: "高保真", c3: "100分" },
      { c1: "1% ~ 5%", c2: "中等保真", c3: "80分" },
      { c1: "5% ~ 15%", c2: "低保真", c3: "60分" },
      { c1: "> 15%", c2: "极低保真", c3: "40分" },
    ];
  }
  if (t === "dirty_data") {
    return [
      { metric: "异常率", t1: "<=5%: 0", t2: "5-10%: -20", t3: "10-20%: -40", t4: ">20%: -60" },
      { metric: "缺失率", t1: "<=1%: 0", t2: "1-5%: -10", t3: "5-15%: -25", t4: ">15%: -40" },
      { metric: "重复率", t1: "<=5%: 0", t2: "5-15%: -10", t3: "15-30%: -20", t4: ">30%: -30" },
      { metric: "疑似错标率", t1: "<=2%: 0", t2: "2-5%: -20", t3: "5-10%: -40", t4: ">10%: -70" },
    ];
  }
  return [];
});

const gradeRuleRows = computed(() => [
  { grade: "S", range: "90-100", desc: "优秀" },
  { grade: "A", range: "80-89", desc: "良好" },
  { grade: "B", range: "70-79", desc: "中等" },
  { grade: "C", range: "60-69", desc: "及格" },
  { grade: "D", range: "0-59", desc: "不及格" },
]);
</script>

<style scoped lang="scss">
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
</style>

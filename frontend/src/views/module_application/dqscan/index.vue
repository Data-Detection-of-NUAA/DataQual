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
            <el-button class="accent-btn" icon="refresh" @click="resetAll">重置</el-button>
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
          <div class="font-bold">上传数据文件（CSV/TXT，最大500MB）</div>
        </template>

        <el-alert
          type="info"
          show-icon
          :closable="false"
          title="请上传待检测的数据文件。基线文件可在下一步的【分布偏差检测】参数中上传。"
          class="mb-3"
        />

        <el-upload
          ref="currentUploadRef"
          drag
          :auto-upload="false"
          :limit="1"
          :file-list="currentFileList"
          accept=".csv,.txt"
          @change="onCurrentFileChange"
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">将数据文件拖到此处，或 <em>点击选择</em></div>
        </el-upload>

        <div class="mt-3 flex items-center gap-2">
          <el-button type="primary" :loading="currentUploading" :disabled="!currentSelectedFile" @click="doUploadCurrent">
            上传文件并继续
          </el-button>
          <el-text v-if="currentUploadedFile" type="success">
            已上传：{{ currentUploadedFile.filename }}（{{ formatBytes(currentUploadedFile.file_size) }}）
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

        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div
            v-for="m in modules"
            :key="m.key"
            class="module-card"
            :class="{ active: selectedModules.includes(m.key) }"
            @click="toggleModule(m.key)"
          >
            <div class="flex items-start justify-between mb-2">
              <el-icon :size="20" :color="selectedModules.includes(m.key) ? '#a78bfa' : '#909399'">
                <component :is="getModuleIcon(m.key)" />
              </el-icon>
              <el-checkbox
                :model-value="selectedModules.includes(m.key)"
                @click.stop
                @change="toggleModule(m.key)"
              />
            </div>
            <div class="font-bold text-sm mb-1">{{ m.title }}</div>
            <div class="text-xs text-gray">{{ m.desc }}</div>
          </div>
        </div>

        <el-card v-if="selectedModules.includes('distribution')" shadow="never" class="mt-3">
          <template #header>
            <div class="flex-x-between">
              <div class="font-bold">分布偏差检测</div>
              <el-tag type="info" effect="plain" size="small">仅对该模块生效</el-tag>
            </div>
          </template>

          <el-form label-width="150px">
            <el-form-item label="基线文件（可选）">
              <div class="w-full">
                <el-alert
                  type="info"
                  show-icon
                  :closable="false"
                  title="上传基线文件可进行【基线 vs 当前】对比检测；不上传则在当前文件内切分对比。"
                  class="mb-3"
                />

                <el-upload
                  ref="baselineUploadRef"
                  drag
                  :auto-upload="false"
                  :limit="1"
                  :file-list="baselineFileList"
                  accept=".csv,.txt"
                  @change="onBaselineFileChange"
                  class="mb-3"
                >
                  <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                  <div class="el-upload__text">将基线文件拖到此处，或 <em>点击选择</em></div>
                </el-upload>

                <div class="flex items-center gap-2">
                  <el-button
                    type="primary"
                    size="small"
                    :loading="baselineUploading"
                    :disabled="!baselineSelectedFile"
                    @click="doUploadBaseline"
                  >
                    上传基线文件
                  </el-button>
                  <el-button class="accent-btn" v-if="baselineUploadedFile" size="small" @click="clearBaseline">
                    清除
                  </el-button>
                  <el-text v-if="baselineUploadedFile" type="success">
                    已上传：{{ baselineUploadedFile.filename }}（{{ formatBytes(baselineUploadedFile.file_size) }}）
                  </el-text>
                </div>
              </div>
            </el-form-item>

            <el-divider />

            <el-form-item label="敏感度 p_val">
              <div class="w-full">
                <el-slider v-model="distributionPVal" :min="0.001" :max="0.2" :step="0.001" show-input />
                <el-text type="info">越小越严格、越不容易报警；列很多时建议用 0.01 或更小。</el-text>
              </div>
            </el-form-item>

            <el-form-item label="排除列 exclude_columns">
              <div class="w-full">
                <el-popover placement="bottom-start" :width="420" trigger="click">
                  <template #reference>
                    <el-input :model-value="excludeColumnsDisplay" readonly placeholder="点击选择要排除的列" />
                  </template>

                  <div v-if="columnsLoading" class="text-sm text-gray">正在解析列名...</div>
                  <div v-else-if="columnsError" class="text-sm text-red">{{ columnsError }}</div>
                  <div v-else-if="!columnOptions.length" class="text-sm text-gray">请先上传数据文件以解析列名</div>
                  <el-scrollbar v-else height="220px">
                    <el-checkbox-group v-model="distributionExcludeColumns" class="flex flex-col gap-1">
                      <el-checkbox v-for="c in columnOptions" :key="c" :label="c">{{ c }}</el-checkbox>
                    </el-checkbox-group>
                  </el-scrollbar>

                  <div class="mt-2 flex justify-end gap-2">
                    <el-button class="accent-btn" size="small" @click="distributionExcludeColumns = []">
                      清空
                    </el-button>
                  </div>
                </el-popover>

                <el-text type="info">建议排除 id/时间戳/唯一标识 等列，避免它们导致误报。</el-text>
              </div>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card v-if="selectedModules.includes('dirty_data')" shadow="never" class="mt-3">
          <template #header>
            <div class="flex-x-between">
              <div class="font-bold">脏数据扫描</div>
              <el-tag type="info" effect="plain" size="small">仅对该模块生效</el-tag>
            </div>
          </template>

          <el-form label-width="150px">
            <!-- 此处可添加具体的脏数据扫描参数 -->
            <el-empty description="参数配置区域，待实现" :image-size="60" />
          </el-form>
        </el-card>

        <el-card v-if="selectedModules.includes('adversarial')" shadow="never" class="mt-3 adversarial-card">
          <template #header>
            <div class="flex-x-between">
              <div class="font-bold">对抗性检测</div>
              <el-tag type="info" effect="plain" size="small">仅对该模块生效</el-tag>
            </div>
          </template>

          <el-form label-width="150px">
            <el-form-item label="检测方法">
              <el-checkbox-group v-model="adversarialMethods">
                <el-checkbox value="mahalanobis">马氏距离检测</el-checkbox>
                <el-checkbox value="perturbation">对抗扰动测试</el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <!-- 马氏距离参数 -->
            <template v-if="adversarialMethods.includes('mahalanobis')">
              <el-divider content-position="left">
                <span class="text-sm font-bold text-gray-600">马氏距离参数</span>
              </el-divider>

              <el-form-item label="异常阈值">
                <div class="w-full">
                  <el-slider v-model="mahalanobisThreshold" :min="1" :max="10" :step="0.1" show-input />
                  <el-text type="info">马氏距离阈值，超过此值判定为异常，建议范围 2-5</el-text>
                </div>
              </el-form-item>

              <el-form-item label="数据标准化">
                <el-switch v-model="mahalanobisNormalize" />
                <el-text type="info" class="ml-2">是否在计算前对数据进行标准化处理</el-text>
              </el-form-item>
            </template>

            <!-- 对抗扰动参数 -->
            <template v-if="adversarialMethods.includes('perturbation')">
              <el-divider content-position="left">
                <span class="text-sm font-bold text-gray-600">对抗扰动参数</span>
              </el-divider>

              <el-form-item label="攻击算法">
                <el-select v-model="perturbationAlgorithm" placeholder="请选择攻击算法" popper-class="adversarial-select-dropdown">
                  <el-option label="FGSM (快速梯度符号法)" value="fgsm" />
                  <el-option label="PGD (投影梯度下降)" value="pgd" />
                </el-select>
              </el-form-item>

              <el-form-item label="扰动幅度 Epsilon">
                <div class="w-full">
                  <el-slider v-model="perturbationEpsilon" :min="0.001" :max="0.15" :step="0.001" show-input />
                  <el-text type="info">控制最大扰动强度，建议 0.03 (8/255) 左右</el-text>
                </div>
              </el-form-item>

              <template v-if="perturbationAlgorithm === 'pgd'">
                <el-form-item label="步长 Alpha">
                  <div class="w-full">
                    <el-slider v-model="perturbationAlpha" :min="0.001" :max="0.05" :step="0.001" show-input />
                    <el-text type="info">PGD 每步的扰动大小，建议 0.008 (2/255)</el-text>
                  </div>
                </el-form-item>

                <el-form-item label="迭代次数">
                  <el-input-number v-model="perturbationIterations" :min="1" :max="100" :step="1" />
                  <el-text type="info" class="ml-2">PGD 攻击的迭代次数，建议 20-40 次</el-text>
                </el-form-item>

                <el-form-item label="随机初始化">
                  <el-switch v-model="perturbationRandomStart" />
                  <el-text type="info" class="ml-2">是否从随机扰动开始迭代</el-text>
                </el-form-item>
              </template>
            </template>
          </el-form>
        </el-card>

        <el-card v-if="selectedModules.includes('physics')" shadow="never" class="mt-3">
          <template #header>
            <div class="flex-x-between">
              <div class="font-bold">物理保真度扫描</div>
              <el-tag type="info" effect="plain" size="small">仅对该模块生效</el-tag>
            </div>
          </template>

          <el-form label-width="150px">
            <!-- 此处可添加具体的物理保真度扫描参数 -->
            <el-empty description="参数配置区域，待实现" :image-size="60" />
          </el-form>
        </el-card>

        <div class="mt-3 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <el-button
              class="accent-btn"
              icon="refresh"
              :loading="algorithmsLoading"
              @click="loadAlgorithms"
            >
              刷新算法列表
            </el-button>
            <el-text type="info">未勾选默认按全选四模块执行</el-text>
          </div>
          <div class="flex items-center gap-2">
            <el-button class="accent-btn" @click="gotoStep(1)">上一步</el-button>
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
              <el-button class="accent-btn" v-if="taskId" icon="refresh" @click="refreshTask">
                刷新状态
              </el-button>
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
          <el-button class="accent-btn" @click="gotoStep(2)">返回选择</el-button>
          <el-button type="primary" :disabled="!resultReady" @click="gotoStep(4)">查看结果</el-button>
        </div>
      </el-card>

      <!-- Step 4: results -->
      <el-card v-show="activeStep === 4" shadow="never" class="mt-4 result-view">
        <template #header>
          <div class="flex-x-between">
            <div class="font-bold">查看结果</div>
            <div class="flex items-center gap-2">
              <el-button class="accent-btn" v-if="taskId" icon="refresh" @click="fetchResult">刷新结果</el-button>
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
                        class="accent-btn"
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
                            class="accent-btn"
                            icon="download"
                            @click="downloadArtifact(activeReportModuleMeta.summaryPath, `${activeReportModule}_summary.json`)"
                          >
                            下载摘要(JSON)
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
                            <div class="report-metric-value text-accent">{{ activeReportDataTypeCount }}</div>
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
                            <el-table-column prop="anomalyRate" label="异常率" width="90" />
                            <el-table-column prop="missingRate" label="缺失率" width="90" />
                            <el-table-column prop="duplicateRate" label="重复率" width="90" />
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

                        <el-card v-if="activeReportModuleType === 'dirty_data'" shadow="never" class="mt-3">
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

                            <el-table v-if="d.issues.length" :data="d.issues" border size="small" class="mt-2">
                              <el-table-column prop="issue_type" label="问题类型" width="140" />
                              <el-table-column prop="data_id" label="位置/字段" width="160" />
                              <el-table-column prop="severity" label="严重度" width="90" />
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
	import { UploadFilled, TrendCharts, Warning, Lock, DataAnalysis } from "@element-plus/icons-vue";
	import ECharts from "@/components/ECharts/index.vue";
	import DQScanAPI, { type DQScanAlgorithmOut, type DQScanUploadOut } from "@/api/module_application/dqscan";

type TaskStatus = "IDLE" | "PENDING" | "RUNNING" | "SUCCESS" | "FAILED";

	const baselineUploadRef = ref();
	const currentUploadRef = ref();
	const activeStep = ref(0);

const modalities = [
  { value: "tabular", label: "表格数据", icon: "table", desc: "CSV/TXT", disabled: false },
  { value: "timeseries", label: "时序数据", icon: "monitor", desc: "后续接入", disabled: true },
  { value: "image", label: "图像数据", icon: "browser", desc: "后续接入", disabled: true },
  { value: "text", label: "文本数据", icon: "document", desc: "后续接入", disabled: true },
];
const selectedModality = ref<string>("tabular");

	const baselineFileList = ref<UploadFile[]>([]);
	const baselineSelectedFile = ref<File | null>(null);
	const baselineUploading = ref(false);
	const baselineUploadedFile = ref<DQScanUploadOut | null>(null);

	const currentFileList = ref<UploadFile[]>([]);
	const currentSelectedFile = ref<File | null>(null);
	const currentUploading = ref(false);
	const currentUploadedFile = ref<DQScanUploadOut | null>(null);

const algorithmsLoading = ref(false);
const algorithms = ref<DQScanAlgorithmOut[]>([]);
const selectedAlgorithm = ref<string>("tabular_quality_engine");

	const modules = [
	  { key: "distribution", title: "分布偏差检测", desc: "检测数据分布漂移（支持基线对比）" },
	  { key: "dirty_data", title: "脏数据扫描", desc: "异常/缺失/重复/值域违规等" },
	  { key: "adversarial", title: "对抗性检测", desc: "对抗扰动下模型脆弱性" },
	  { key: "physics", title: "物理保真度扫描", desc: "基于规则/约束的物理合理性校验" },
	];
const selectedModules = ref<string[]>(["dirty_data", "distribution", "adversarial", "physics"]);

	const starting = ref(false);
	const taskId = ref<string | null>(null);
	const progress = ref(0);
	const logs = ref<string[]>([]);
		const taskStatus = ref<TaskStatus>("IDLE");
		const taskError = ref<string | null>(null);
		const result = ref<any | null>(null);

		// 报告视图（从后端读取 reports/*.json，用于页面展示）
		const reportsLoading = ref(false);
		const reports = ref<Record<string, any>>({});
		const activeReportModule = ref<string>("");

	// 分布偏差模块参数（UI 侧）
	const distributionPVal = ref(0.05);
	const distributionExcludeColumns = ref<string[]>([]);
	const columnOptions = ref<string[]>([]);
	const columnsLoading = ref(false);
	const columnsError = ref<string | null>(null);
	const excludeColumnsDisplay = computed(() => {
	  const n = distributionExcludeColumns.value.length;
	  if (n === 0) return "未选择（默认不排除）";
	  if (n <= 3) return distributionExcludeColumns.value.join(", ");
	  return `${distributionExcludeColumns.value.slice(0, 3).join(", ")} 等${n}项`;
	});

	// 对抗性检测模块参数（UI 侧）
	const adversarialMethods = ref<string[]>(["mahalanobis"]);
	// 马氏距离参数
	const mahalanobisThreshold = ref(3.0);
	const mahalanobisNormalize = ref(true);
	// 对抗扰动参数
	const perturbationAlgorithm = ref<string>("fgsm");
	const perturbationEpsilon = ref(0.031); // 8/255 ≈ 0.031
	const perturbationAlpha = ref(0.008); // 2/255 ≈ 0.008
	const perturbationIterations = ref(40);
	const perturbationRandomStart = ref(true);

	let ws: WebSocket | null = null;
	let pollTimer: number | null = null;

	const canStart = computed(() => !!currentUploadedFile.value?.file_id && !!selectedAlgorithm.value && !starting.value);
	const resultReady = computed(() => taskStatus.value === "SUCCESS" && !!result.value);

const selectedAlgorithmLabel = computed(() => {
  const alg = algorithms.value.find((a) => a.name === selectedAlgorithm.value);
  return alg?.label || "表格数据质量探测引擎";
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
	  baselineFileList.value = [];
	  baselineSelectedFile.value = null;
	  baselineUploading.value = false;
	  baselineUploadedFile.value = null;
	  currentFileList.value = [];
	  currentSelectedFile.value = null;
	  currentUploading.value = false;
	  currentUploadedFile.value = null;
	  distributionPVal.value = 0.05;
	  distributionExcludeColumns.value = [];
	  columnOptions.value = [];
	  columnsLoading.value = false;
	  columnsError.value = null;
	  adversarialMethods.value = ["mahalanobis"];
	  mahalanobisThreshold.value = 3.0;
	  mahalanobisNormalize.value = true;
	  perturbationAlgorithm.value = "fgsm";
	  perturbationEpsilon.value = 0.031;
	  perturbationAlpha.value = 0.008;
	  perturbationIterations.value = 40;
	  perturbationRandomStart.value = true;
	  starting.value = false;
	  taskId.value = null;
	  progress.value = 0;
	  logs.value = [];
		  taskStatus.value = "IDLE";
		  taskError.value = null;
		  result.value = null;
		  reportsLoading.value = false;
		  reports.value = {};
		  activeReportModule.value = "";
		}

function gotoStep(step: number) {
  activeStep.value = step;
}

function stepClass(idx: number) {
  if (activeStep.value === idx) return "active";
  if (activeStep.value > idx) return "completed";
  return "";
}

	function onBaselineFileChange(file: UploadFile, files: UploadFile[]) {
	  baselineFileList.value = (files || []).slice(-1);
	  const raw = (baselineFileList.value[0]?.raw || file.raw) as File | undefined;
	  baselineSelectedFile.value = raw || null;
	}

	function onCurrentFileChange(file: UploadFile, files: UploadFile[]) {
	  currentFileList.value = (files || []).slice(-1);
	  const raw = (currentFileList.value[0]?.raw || file.raw) as File | undefined;
	  currentSelectedFile.value = raw || null;
	  void refreshColumnsFromCurrentFile();
	}

	function detectDelimiter(line: string): string {
	  const candidates = [",", "\t", ";", "|"];
	  let best = ",";
	  let bestCount = -1;
	  for (const d of candidates) {
	    const count = line.split(d).length - 1;
	    if (count > bestCount) {
	      bestCount = count;
	      best = d;
	    }
	  }
	  return best;
	}

	function parseDelimitedHeader(line: string, delimiter: string): string[] {
	  const out: string[] = [];
	  let cur = "";
	  let inQuotes = false;
	  const s = line.replace(/^\ufeff/, ""); // BOM
	  for (let i = 0; i < s.length; i += 1) {
	    const ch = s[i];
	    if (ch === '"') {
	      // 处理双引号转义："" -> "
	      if (inQuotes && s[i + 1] === '"') {
	        cur += '"';
	        i += 1;
	      } else {
	        inQuotes = !inQuotes;
	      }
	      continue;
	    }
	    if (ch === delimiter && !inQuotes) {
	      out.push(cur);
	      cur = "";
	      continue;
	    }
	    cur += ch;
	  }
	  out.push(cur);
	  return out
	    .map((x) => x.trim().replace(/^"|"$/g, "").trim())
	    .filter((x) => !!x);
	}

	async function extractColumnsFromFile(file: File): Promise<string[]> {
	  const text = await file.slice(0, 64 * 1024).text();
	  const firstLine = text.split(/\r?\n/).find((l) => l.trim().length > 0) || "";
	  if (!firstLine) return [];
	  const delimiter = detectDelimiter(firstLine);
	  const cols = parseDelimitedHeader(firstLine.replace(/\r$/, ""), delimiter);
	  const seen = new Set<string>();
	  const uniq: string[] = [];
	  for (const c of cols) {
	    if (!seen.has(c)) {
	      seen.add(c);
	      uniq.push(c);
	    }
	  }
	  return uniq;
	}

	async function refreshColumnsFromCurrentFile() {
	  if (!currentSelectedFile.value) {
	    columnOptions.value = [];
	    columnsError.value = null;
	    return;
	  }
	  columnsLoading.value = true;
	  columnsError.value = null;
	  try {
	    const cols = await extractColumnsFromFile(currentSelectedFile.value);
	    columnOptions.value = cols;
	    distributionExcludeColumns.value = distributionExcludeColumns.value.filter((c) => cols.includes(c));
	  } catch (e: any) {
	    columnOptions.value = [];
	    columnsError.value = e?.message ? String(e.message) : "解析列名失败";
	  } finally {
	    columnsLoading.value = false;
	  }
	}

async function loadAlgorithms() {
  algorithmsLoading.value = true;
  try {
    const res = await DQScanAPI.listAlgorithms();
    algorithms.value = res.data.data || [];
    if (algorithms.value.some((a) => a.name === "tabular_quality_engine")) {
      selectedAlgorithm.value = "tabular_quality_engine";
    } else if (algorithms.value.length > 0) {
      selectedAlgorithm.value = algorithms.value[0].name;
    }
  } finally {
    algorithmsLoading.value = false;
  }
}

	function clearBaseline() {
	  baselineFileList.value = [];
	  baselineSelectedFile.value = null;
	  baselineUploading.value = false;
	  baselineUploadedFile.value = null;
	}

	async function doUploadBaseline() {
	  if (!baselineSelectedFile.value) return;
	  baselineUploading.value = true;
	  try {
	    const res = await DQScanAPI.uploadFile(baselineSelectedFile.value);
	    baselineUploadedFile.value = res.data.data;
	    pushLog(`基线文件上传成功：${baselineUploadedFile.value?.filename}`);
	  } finally {
	    baselineUploading.value = false;
	  }
	}

	async function doUploadCurrent() {
	  if (!currentSelectedFile.value) return;
	  currentUploading.value = true;
	  try {
	    const res = await DQScanAPI.uploadFile(currentSelectedFile.value);
	    currentUploadedFile.value = res.data.data;
	    gotoStep(2);
	    pushLog(`当前文件上传成功：${currentUploadedFile.value?.filename}`);
	  } finally {
	    currentUploading.value = false;
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
	    await fetchReports();
	  } catch (e: any) {
	    pushLog(`获取结果失败：${e?.message || e}`);
	  }
	}

	async function fetchReports() {
	  if (!taskId.value) return;
	  reportsLoading.value = true;
	  try {
	    const res = await DQScanAPI.getReports(taskId.value, { report_type: "json" });
	    reports.value = res.data.data.reports || {};
	    if (!activeReportModule.value) {
	      activeReportModule.value = Object.keys(reports.value)[0] || Object.keys(result.value?.modules || {})[0] || "";
	    }
	  } catch (e: any) {
	    pushLog(`获取报告失败：${e?.message || e}`);
	    reports.value = {};
	  } finally {
	    reportsLoading.value = false;
	  }
	}

		async function startScan() {
	  if (!currentUploadedFile.value?.file_id) return;
		  starting.value = true;
		  result.value = null;
		  reports.value = {};
		  activeReportModule.value = "";
		  taskError.value = null;
  logs.value = [];
  progress.value = 0;
  taskStatus.value = "PENDING";
  gotoStep(3);

	  try {
	    const params: Record<string, any> = {
	      modules: selectedModules.value?.length ? selectedModules.value : undefined,
	    };
	    if (selectedModules.value.includes("distribution")) {
	      params.p_val = distributionPVal.value;
	      if (distributionExcludeColumns.value.length) {
	        params.exclude_columns = distributionExcludeColumns.value;
	      }
	    }
	    if (selectedModules.value.includes("adversarial")) {
	      params.adversarial_methods = adversarialMethods.value;
	      if (adversarialMethods.value.includes("mahalanobis")) {
	        params.mahalanobis_threshold = mahalanobisThreshold.value;
	        params.mahalanobis_normalize = mahalanobisNormalize.value;
	      }
	      if (adversarialMethods.value.includes("perturbation")) {
	        params.perturbation_algorithm = perturbationAlgorithm.value;
	        params.perturbation_epsilon = perturbationEpsilon.value;
	        if (perturbationAlgorithm.value === "pgd") {
	          params.perturbation_alpha = perturbationAlpha.value;
	          params.perturbation_iterations = perturbationIterations.value;
	          params.perturbation_random_start = perturbationRandomStart.value;
	        }
	      }
	    }
	    const res = await DQScanAPI.createTask({
	      file_id: currentUploadedFile.value.file_id,
	      baseline_file_id: baselineUploadedFile.value?.file_id,
	      algorithm: selectedAlgorithm.value,
	      params,
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

function toggleModule(key: string) {
  const index = selectedModules.value.indexOf(key);
  if (index > -1) {
    selectedModules.value.splice(index, 1);
  } else {
    selectedModules.value.push(key);
  }
}

function getModuleIcon(key: string) {
  const iconMap: Record<string, any> = {
    distribution: TrendCharts,
    dirty_data: Warning,
    adversarial: Lock,
    physics: DataAnalysis,
  };
  return iconMap[key] || DataAnalysis;
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

	function scoreColor(score: number): string {
	  if (score >= 90) return "#28A745";
	  if (score >= 80) return "#17A2B8";
	  if (score >= 70) return "#FFC107";
	  return "#DC3545";
	}

	function gradeFull(score: number): string {
	  if (score >= 90) return "S (优秀)";
	  if (score >= 80) return "A (良好)";
	  if (score >= 70) return "B (中等)";
	  if (score >= 60) return "C (及格)";
	  return "D (不及格)";
	}

	function statusFromScore(score: number): { statusTag: "success" | "warning" | "danger"; statusText: string } {
	  if (score >= 90) return { statusTag: "success", statusText: "[OK]" };
	  if (score >= 70) return { statusTag: "warning", statusText: "[!]" };
	  return { statusTag: "danger", statusText: "[X]" };
	}

	function dataTypeLabel(dt: string): string {
	  const map: Record<string, string> = { tabular: "表格数据", timeseries: "时序数据", image: "图像数据", text: "文本数据" };
	  return map[dt] || dt;
	}

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
	  return {
	    title: { text: "问题率对比", left: "center", textStyle: { fontSize: 16, fontWeight: "bold" } },
	    grid: { left: 70, right: 30, top: 60, bottom: 50 },
	    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
	    legend: { top: 30, right: 10, data: ["异常率", "缺失率", "重复率"] },
	    xAxis: { type: "category", data: labels },
	    yAxis: { type: "value", name: "百分比 (%)", min: 0, max: 100 },
	    series: [
	      {
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
	      },
	      { name: "缺失率", type: "bar", data: missing, itemStyle: { color: "#FFC107" } },
	      { name: "重复率", type: "bar", data: duplicate, itemStyle: { color: "#17A2B8" } },
	    ],
	  } as any;
	});

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
	      base.anomalyRate = `${(Number(dtResult.anomaly_rate ?? 0) * 100).toFixed(1)}%`;
	      base.missingRate = `${(Number(dtResult.missing_rate ?? 0) * 100).toFixed(1)}%`;
	      base.duplicateRate = `${(Number(dtResult.duplicate_rate ?? 0) * 100).toFixed(1)}%`;
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
	    }

	    const issues = Array.isArray(dtResult.detailed_issues) ? dtResult.detailed_issues : [];
	    const normalizedIssues = issues.slice(0, 50).map((it: any) => ({
	      issue_type: String(it?.issue_type ?? "未知"),
	      data_id: String(it?.data_id ?? "-"),
	      severity: String(it?.severity ?? "-"),
	      detailsText: issueDetailsText(it?.details),
	    }));

	    return {
	      dataTypeKey: dt,
	      dataTypeLabel: dataTypeLabel(dt),
	      algorithm: String(dtResult.algorithm || "N/A"),
	      hasIssues: !!dtResult.has_issues,
	      totalIssues: Number(dtResult.total_issues ?? 0),
	      issuePercentage: `${(Number(dtResult.issue_percentage ?? 0) * 100).toFixed(2)}%`,
	      score: Number.isFinite(score) ? Number(score.toFixed(0)) : 0,
	      extraMetrics,
	      issues: normalizedIssues,
	    };
	  });
	});

	const activeScoringExplain = computed(() => {
	  switch (activeReportModuleType.value) {
	    case "distribution":
	      return "评分基于统计显著性 p 值";
	    case "dirty_data":
	      return "评分采用扣分制（满分 100）";
	    case "adversarial":
	      return "评分基于攻击成功率评估鲁棒性";
	    case "physics":
	      return "评分基于约束违规率评估保真度";
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

onMounted(() => {
  loadAlgorithms();
});

onBeforeUnmount(() => {
  resetWs();
  clearPoll();
});
</script>

<style scoped lang="scss">
/* 覆盖 Element Plus 主题色为浅紫色 */
:deep(.el-button--primary) {
  --el-button-bg-color: #a78bfa;
  --el-button-border-color: #a78bfa;
  --el-button-hover-bg-color: #8b5cf6;
  --el-button-hover-border-color: #8b5cf6;
  --el-button-active-bg-color: #7c3aed;
  --el-button-active-border-color: #7c3aed;
  --el-button-disabled-bg-color: rgba(167, 139, 250, 0.5);
  --el-button-disabled-border-color: rgba(167, 139, 250, 0.5);
}

:deep(.el-button--success) {
  background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
  border-color: #a78bfa;
}

:deep(.el-button--success:hover) {
  background: linear-gradient(135deg, #7c3aed 0%, #8b5cf6 100%);
  border-color: #8b5cf6;
}

:deep(.el-button--success.is-disabled) {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.5) 0%, rgba(167, 139, 250, 0.5) 100%);
  border-color: rgba(167, 139, 250, 0.5);
}

:deep(.el-progress__text) {
  color: #a78bfa !important;
}

:deep(.el-progress-bar__inner) {
  background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%) !important;
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #a78bfa;
  border-color: #a78bfa;
}

:deep(.el-checkbox__input.is-checked + .el-checkbox__label) {
  color: #a78bfa;
}

:deep(.el-checkbox__input.is-indeterminate .el-checkbox__inner) {
  background-color: #a78bfa;
  border-color: #a78bfa;
}

:deep(.el-checkbox__input.is-focus .el-checkbox__inner) {
  border-color: #a78bfa;
}

:deep(.el-tag--primary) {
  --el-tag-bg-color: rgba(167, 139, 250, 0.1);
  --el-tag-border-color: rgba(167, 139, 250, 0.2);
  --el-tag-text-color: #a78bfa;
}

:deep(.el-link--primary) {
  --el-link-text-color: #a78bfa;
  --el-link-hover-text-color: #8b5cf6;
}

:deep(.el-slider__button) {
  border-color: #a78bfa;
}

:deep(.el-input-number__increase:hover),
:deep(.el-input-number__decrease:hover) {
  color: #7c3aed;
}

:deep(.el-input-number__increase:hover ~ .el-input__wrapper),
:deep(.el-input-number__decrease:hover ~ .el-input__wrapper),
:deep(.el-input-number__increase:focus),
:deep(.el-input-number__decrease:focus) {
  border-color: #7c3aed;
}

:deep(.el-slider__bar) {
  background-color: #a78bfa;
}

:deep(.el-input__inner:focus) {
  border-color: #a78bfa;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #a78bfa inset;
}

:deep(.el-select .el-input.is-focus .el-input__inner) {
  border-color: #a78bfa;
}

:deep(.el-tabs__item.is-active) {
  color: #7c3aed;
}

:deep(.el-tabs__active-bar) {
  background-color: #7c3aed;
}

:deep(.el-tabs__item:hover) {
  color: #a78bfa;
}

.result-view {
  :deep(.el-tabs--border-card > .el-tabs__header .el-tabs__item:hover) {
    color: #a78bfa;
    background-color: rgba(167, 139, 250, 0.12);
  }

  :deep(.el-tabs--border-card > .el-tabs__header .el-tabs__item.is-active) {
    color: #7c3aed;
    background-color: rgba(124, 58, 237, 0.12);
  }
}

:deep(.el-upload-dragger:hover) {
  border-color: #a78bfa;
}

:deep(.el-upload__text) {
  em {
    color: #7c3aed;
    font-style: normal;
    font-weight: 600;
  }
}

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
  background: linear-gradient(135deg, #7c3aed 0%, #8b5cf6 100%);
}

.step-arrow.active::after {
  border-left-color: #8b5cf6;
}

.step-arrow.completed {
  color: #fff;
  background: linear-gradient(135deg, #7c3aed 0%, #8b5cf6 100%);
  opacity: 0.9;
}

.step-arrow.completed::after {
  border-left-color: #8b5cf6;
}

.step-arrow:last-child::after {
  display: none;
}

.modality-card {
  cursor: pointer;
  transition: all 0.15s ease;
}
.modality-card.is-active {
  border-color: #a78bfa;
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

.module-card {
  padding: 16px;
  border: 2px solid var(--el-border-color-light);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  background-color: var(--el-bg-color);
  height: 100%;
  min-height: 110px;
}

.module-card:hover {
  border-color: #7c3aed;
  box-shadow: 0 2px 8px rgba(167, 139, 250, 0.15);
  transform: translateY(-2px);
}

.module-card.active {
  border-color: #a78bfa;
  background-color: rgba(167, 139, 250, 0.05);
  box-shadow: 0 2px 12px rgba(167, 139, 250, 0.25);
}

.module-card.active:hover {
  border-color: #a78bfa;
  box-shadow: 0 4px 16px rgba(167, 139, 250, 0.35);
}

.accent-btn:hover {
  color: #7c3aed;
  border-color: #7c3aed;
  background-color: rgba(124, 58, 237, 0.08);
}

.text-accent {
  color: #7c3aed;
}

/* 对抗性检测卡片专用紫色样式 */
.adversarial-card {
  :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
    background-color: #a78bfa;
    border-color: #a78bfa;
  }

  :deep(.el-checkbox__input.is-indeterminate .el-checkbox__inner) {
    background-color: #a78bfa;
    border-color: #a78bfa;
  }

  :deep(.el-checkbox__input.is-focus .el-checkbox__inner) {
    border-color: #a78bfa;
  }

  :deep(.el-checkbox__inner:hover) {
    border-color: #a78bfa;
  }

  :deep(.el-slider__button) {
    border-color: #a78bfa;
  }

  :deep(.el-slider__bar) {
    background-color: #a78bfa;
  }

  :deep(.el-switch.is-checked .el-switch__core) {
    background-color: #a78bfa;
    border-color: #a78bfa;
  }

  :deep(.el-input-number__increase:hover),
  :deep(.el-input-number__decrease:hover) {
    color: #a78bfa;
  }

  :deep(.el-input-number__increase:active),
  :deep(.el-input-number__decrease:active) {
    color: #7c3aed;
  }

  :deep(.el-input-number:hover .el-input__wrapper) {
    box-shadow: 0 0 0 1px #a78bfa inset !important;
  }

  :deep(.el-input-number.is-controls-right .el-input__wrapper:focus-within),
  :deep(.el-input-number .el-input__wrapper:focus-within),
  :deep(.el-input-number.is-focus .el-input__wrapper),
  :deep(.el-input-number:focus-within .el-input__wrapper) {
    box-shadow: 0 0 0 1px #a78bfa inset !important;
  }

  :deep(.el-input__wrapper.is-focus) {
    box-shadow: 0 0 0 1px #a78bfa inset !important;
  }

  /* el-select 新版使用 el-select__wrapper */
  :deep(.el-select__wrapper) {
    &.is-focused {
      box-shadow: 0 0 0 1px #a78bfa inset !important;
    }
    &:hover {
      box-shadow: 0 0 0 1px #a78bfa inset !important;
    }
  }

  :deep(.el-select .el-select__wrapper.is-focused) {
    box-shadow: 0 0 0 1px #a78bfa inset !important;
  }

  :deep(.el-select.is-focused .el-select__wrapper) {
    box-shadow: 0 0 0 1px #a78bfa inset !important;
  }
}

.text-gray-600 {
  color: #6b7280;
}
</style>

<style lang="scss">
/* 对抗性检测下拉框选项紫色（全局样式） */
.adversarial-select-dropdown {
  .el-select-dropdown__item.is-selected {
    color: #a78bfa !important;
    font-weight: 600;
  }

  .el-select-dropdown__item.is-hovering {
    background-color: rgba(167, 139, 250, 0.1);
  }
}

/* 对抗性检测下拉框边框紫色（全局样式） */
.adversarial-card {
  .el-select__wrapper.is-focused,
  .el-select__wrapper:hover,
  .el-select.is-focused .el-select__wrapper,
  .el-select:focus-within .el-select__wrapper {
    box-shadow: 0 0 0 1px #a78bfa inset !important;
  }

  .el-input-number:hover .el-input__wrapper,
  .el-input-number.is-controls-right .el-input__wrapper:focus-within,
  .el-input-number .el-input__wrapper:focus-within,
  .el-input-number.is-focus .el-input__wrapper,
  .el-input-number:focus-within .el-input__wrapper {
    box-shadow: 0 0 0 1px #a78bfa inset !important;
  }
}
</style>

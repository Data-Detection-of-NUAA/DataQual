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

        <el-alert
          type="info"
          show-icon
          :closable="false"
          title="分布偏差支持两种方式"
          description="① 基线文件 vs 当前文件（推荐）；② 仅当前文件：自动切分模拟（免基线）"
          class="mb-3"
        />

        <el-card shadow="never" class="mb-3">
          <template #header>
            <div class="flex-x-between">
              <div class="font-bold">分布偏差对比方式</div>
              <el-tag type="info" effect="plain" size="small">仅影响分布偏差模块</el-tag>
            </div>
          </template>
          <el-radio-group v-model="distributionCompareMode">
            <el-radio-button label="baseline_file">基线文件 vs 当前文件</el-radio-button>
            <el-radio-button label="in_file_split">仅当前文件（免基线）</el-radio-button>
          </el-radio-group>
          <el-text type="info" class="block mt-2">
            免基线模式会按“切分比例”将同一文件分成两段进行漂移对比。
          </el-text>
        </el-card>

        <el-card v-if="distributionCompareMode === 'baseline_file'" shadow="never" class="mb-3">
          <template #header>
            <div class="flex-x-between">
              <div class="font-bold">基线文件（可选）</div>
              <div class="flex items-center gap-2">
                <el-button v-if="baselineUploadedFile" @click="clearBaseline">清除基线</el-button>
                <el-tag type="info" effect="plain" size="small">用于分布偏差模块</el-tag>
              </div>
            </div>
          </template>

          <el-upload
            ref="baselineUploadRef"
            drag
            :auto-upload="false"
            :limit="1"
            :file-list="baselineFileList"
            accept=".csv,.txt"
            @change="onBaselineFileChange"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">将基线文件拖到此处，或 <em>点击选择</em></div>
          </el-upload>

          <div class="mt-3 flex items-center gap-2">
            <el-button type="primary" :loading="baselineUploading" :disabled="!baselineSelectedFile" @click="doUploadBaseline">
              上传基线文件
            </el-button>
            <el-text v-if="baselineUploadedFile" type="info">
              已上传：{{ baselineUploadedFile.filename }}（{{ formatBytes(baselineUploadedFile.file_size) }}）
            </el-text>
          </div>
        </el-card>

        <el-alert
          v-else
          type="success"
          show-icon
          :closable="false"
          title="已选择免基线模式：无需上传基线文件"
          class="mb-3"
        />

        <el-card shadow="never">
          <template #header>
            <div class="flex-x-between">
              <div class="font-bold">当前文件（必选）</div>
              <el-tag type="success" effect="plain" size="small">扫描对象</el-tag>
            </div>
          </template>

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
            <div class="el-upload__text">将当前文件拖到此处，或 <em>点击选择</em></div>
          </el-upload>

          <div class="mt-3 flex items-center gap-2">
            <el-button type="primary" :loading="currentUploading" :disabled="!currentSelectedFile" @click="doUploadCurrent">
              上传当前文件并继续
            </el-button>
            <el-text v-if="currentUploadedFile" type="info">
              已上传：{{ currentUploadedFile.filename }}（{{ formatBytes(currentUploadedFile.file_size) }}）
            </el-text>
          </div>
        </el-card>
      </el-card>

      <!-- Step 2: choose modules -->
      <el-card v-show="activeStep === 2" shadow="never" class="mt-4">
        <template #header>
          <div class="font-bold">选择缺陷与算法（缺陷体系）</div>
        </template>

        <el-alert
          type="info"
          show-icon
          :closable="false"
          title="当前支持表格数据（CSV/TXT）质量检测"
          description="运行完成后可在结果页查看摘要与下载报告。"
          class="mb-3"
        />

        <el-card shadow="never" class="mb-3">
          <div class="flex items-start gap-2">
            <div class="i-svg:api w-5 h-5 mt-1" />
            <div class="flex-1">
              <div class="font-bold">{{ selectedAlgorithmLabel }}</div>
              <div class="text-sm text-gray mt-1">{{ selectedAlgorithmDesc }}</div>
            </div>
          </div>
        </el-card>

        <el-row :gutter="12">
          <el-col :md="8" :xs="24">
            <el-card shadow="never" class="mb-3">
              <template #header>
                <div class="flex-x-between">
                  <div class="font-bold">缺陷体系</div>
                  <el-tag type="info" effect="plain" size="small">可多选</el-tag>
                </div>
              </template>

              <el-input v-model="defectSearch" clearable placeholder="搜索缺陷/关键词" />
              <div class="mt-2 flex flex-wrap gap-2">
                <el-button size="small" @click="selectAllDefects">全选</el-button>
                <el-button size="small" type="primary" @click="selectRecommendedDefects">推荐</el-button>
                <el-button size="small" @click="clearDefects">清空</el-button>
              </div>

              <el-divider class="my-2" />

              <el-tree
                ref="defectTreeRef"
                class="dqscan-defect-tree"
                :data="defectTreeData"
                show-checkbox
                node-key="key"
                :props="defectTreeProps"
                :default-expanded-keys="defaultExpandedDefectKeys"
                :default-checked-keys="checkedDefectKeys"
                :highlight-current="true"
                :current-node-key="activeDefectKey"
                :filter-node-method="filterDefectNode"
                @node-click="onDefectNodeClick"
                @check="onDefectCheck"
              >
                <template #default="{ data }">
                  <div class="dqscan-defect-node">
                    <div class="dqscan-defect-node-title">
                      <span>{{ data.label }}</span>
                      <el-tag
                        v-if="data.badge"
                        :type="data.badge.type"
                        effect="plain"
                        size="small"
                        class="ml-2 shrink-0"
                      >
                        {{ data.badge.text }}
                      </el-tag>
                    </div>
                    <div v-if="data.desc" class="dqscan-defect-node-desc">{{ data.desc }}</div>
                  </div>
                </template>
              </el-tree>

              <el-divider class="my-2" />

              <el-row :gutter="12">
                <el-col :span="12" :xs="12">
                  <div class="dqscan-stat">
                    <div class="dqscan-stat-label">已选缺陷</div>
                    <div class="dqscan-stat-value">{{ selectedLeafDefectCount }}</div>
                  </div>
                </el-col>
                <el-col :span="12" :xs="12">
                  <div class="dqscan-stat">
                    <div class="dqscan-stat-label">已选算法</div>
                    <div class="dqscan-stat-value">{{ selectedDefectAlgorithmCount }}</div>
                  </div>
                </el-col>
              </el-row>
            </el-card>

            <el-card shadow="never">
              <template #header>
                <div class="flex-x-between">
                  <div class="font-bold">运行策略</div>
                  <el-tag type="info" effect="plain" size="small">全局</el-tag>
                </div>
              </template>

              <el-form label-width="110px">
                <el-form-item label="扫描模式">
                  <el-radio-group v-model="scanPreset">
                    <el-radio-button label="fast">快速</el-radio-button>
                    <el-radio-button label="balanced">均衡</el-radio-button>
                    <el-radio-button label="thorough">深度</el-radio-button>
                  </el-radio-group>
                </el-form-item>
                <el-form-item label="抽样上限">
                  <el-input-number v-model="globalMaxSamples" :min="100" :max="500000" :step="100" />
                </el-form-item>
                <el-form-item label="并行度">
                  <el-slider v-model="globalParallelism" :min="1" :max="8" :step="1" show-input />
                </el-form-item>
                <el-form-item label="随机种子">
                  <el-input-number v-model="globalSeed" :min="0" :max="999999" :step="1" />
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>

          <el-col :md="16" :xs="24">
            <el-card shadow="never" class="mb-3">
              <template #header>
                <div class="flex-x-between">
                  <div class="flex items-center gap-2">
                    <div class="font-bold">{{ activeDefectMeta?.label || "缺陷配置" }}</div>
                    <el-tag
                      v-if="activeDefectMeta?.status"
                      :type="activeDefectMeta.status === 'ready' ? 'success' : 'warning'"
                      effect="plain"
                      size="small"
                    >
                      {{ activeDefectMeta.status === "ready" ? "可用" : "即将上线" }}
                    </el-tag>
                  </div>
                  <div class="flex items-center gap-2">
                    <el-switch
                      v-model="activeDefectEnabled"
                      :disabled="activeDefectMeta?.status !== 'ready'"
                      active-text="已启用"
                      inactive-text="未启用"
                    />
                  </div>
                </div>
              </template>

              <el-empty v-if="!activeDefectMeta" description="请在左侧缺陷树中选择一个缺陷类型进行配置" />

              <div v-else>
                <el-alert type="info" show-icon :closable="false" :title="activeDefectMeta.label" :description="activeDefectMeta.desc" class="mb-3" />

                <el-tabs v-model="activeDefectTab" type="border-card">
                  <el-tab-pane label="算法选择" name="algo">
                    <el-select
                      v-model="activeDefectAlgorithms"
                      multiple
                      filterable
                      collapse-tags
                      collapse-tags-tooltip
                      :max-collapse-tags="3"
                      placeholder="选择算法（可多选）"
                      style="width: 100%"
                      popper-class="dqscan-algo-select-popper"
                    >
                      <el-option
                        v-for="a in activeDefectMeta.algorithms"
                        :key="a.key"
                        :label="a.label"
                        :value="a.key"
                        :disabled="a.status !== 'ready'"
                      >
                        <div class="dqscan-algo-option">
                          <div class="dqscan-algo-option-main">
                            <div class="dqscan-algo-option-title">{{ a.label }}</div>
                            <div class="dqscan-algo-option-desc">{{ a.desc }}</div>
                          </div>
                          <el-tag
                            :type="a.status === 'ready' ? 'success' : 'warning'"
                            effect="plain"
                            size="small"
                            class="shrink-0"
                          >
                            {{ a.status === "ready" ? "可用" : "即将上线" }}
                          </el-tag>
                        </div>
                      </el-option>
                    </el-select>

                    <el-divider class="my-3" />

                    <el-descriptions :column="2" border size="small">
                      <el-descriptions-item label="缺陷路径">{{ activeDefectPathText }}</el-descriptions-item>
                      <el-descriptions-item label="已选算法">{{ activeDefectAlgorithms.length }}</el-descriptions-item>
                    </el-descriptions>
                  </el-tab-pane>

                  <el-tab-pane label="参数配置" name="params">
                    <div v-if="activeDefectKey === 'dirty_data.anomaly'">
                      <el-form label-width="160px">
                        <el-form-item label="异常比例">
                          <div class="w-full">
                            <el-slider v-model="dirtyContamination" :min="0" :max="0.5" :step="0.01" show-input />
                            <el-text type="info">用于无监督异常检测的预期异常比例；越大越敏感。</el-text>
                          </div>
                        </el-form-item>
                        <el-form-item label="采样上限">
                          <el-input-number v-model="globalMaxSamples" :min="100" :max="500000" :step="100" />
                        </el-form-item>
                        <el-form-item label="输出样例数">
                          <el-input-number v-model="dirtyMaxExamples" :min="10" :max="500" :step="10" />
                        </el-form-item>
                      </el-form>
                    </div>

                    <div v-else-if="activeDefectKey === 'dirty_data.missing'">
                      <el-form label-width="160px">
                        <el-form-item label="缺失率阈值">
                          <div class="w-full">
                            <el-slider v-model="dirtyMissingThreshold" :min="0" :max="0.5" :step="0.01" show-input />
                            <el-text type="info">用于判断某字段是否“缺失严重”。</el-text>
                          </div>
                        </el-form-item>
                        <el-form-item label="字段白名单（可选）">
                          <el-select v-model="dirtyWhitelistColumns" multiple filterable clearable placeholder="不选表示全字段参与">
                            <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                          </el-select>
                        </el-form-item>
                        <el-form-item label="字段黑名单（可选）">
                          <el-select v-model="dirtyBlacklistColumns" multiple filterable clearable placeholder="排除不需要的字段">
                            <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                          </el-select>
                        </el-form-item>
                      </el-form>
                    </div>

                    <div v-else-if="activeDefectKey === 'dirty_data.duplicate'">
                      <el-form label-width="160px">
                        <el-form-item label="重复率阈值">
                          <div class="w-full">
                            <el-slider v-model="dirtyDuplicateThreshold" :min="0" :max="0.2" :step="0.005" show-input />
                            <el-text type="info">用于判断数据集是否“重复严重”。</el-text>
                          </div>
                        </el-form-item>
                        <el-form-item label="关键字段（可选）">
                          <el-select v-model="duplicateKeyColumns" multiple filterable clearable placeholder="不选表示按整行判断">
                            <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                          </el-select>
                        </el-form-item>
                        <el-form-item label="相似度阈值">
                          <div class="w-full">
                            <el-slider v-model="duplicateSimilarity" :min="0.5" :max="1" :step="0.01" show-input />
                            <el-text type="info">用于“近重复/模糊重复”检测（即将上线）。</el-text>
                          </div>
                        </el-form-item>
                      </el-form>
                    </div>

                    <div v-else-if="activeDefectKey === 'dirty_data.range'">
                      <el-form label-width="160px">
                        <el-form-item label="检测方式">
                          <el-radio-group v-model="rangeMethod">
                            <el-radio-button label="sigma">3σ</el-radio-button>
                            <el-radio-button label="iqr">IQR</el-radio-button>
                            <el-radio-button label="rules">自定义规则</el-radio-button>
                          </el-radio-group>
                        </el-form-item>
                        <el-form-item v-if="rangeMethod === 'sigma'" label="σ 阈值">
                          <el-slider v-model="rangeSigma" :min="2" :max="6" :step="0.5" show-input />
                        </el-form-item>
                        <el-form-item v-else-if="rangeMethod === 'iqr'" label="IQR 系数">
                          <el-slider v-model="rangeIqrFactor" :min="1" :max="5" :step="0.25" show-input />
                        </el-form-item>
                        <el-form-item label="字段白名单（可选）">
                          <el-select v-model="rangeOnlyColumns" multiple filterable clearable placeholder="不选表示全字段参与">
                            <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                          </el-select>
                        </el-form-item>
                      </el-form>
                    </div>

                    <div v-else-if="activeDefectKey === 'dirty_data.label_mismatch'">
                      <el-form label-width="160px">
                        <el-form-item label="标签列">
                          <el-select v-model="labelMismatchLabelColumn" filterable clearable placeholder="选择标签列">
                            <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                          </el-select>
                          <el-text type="info" class="block mt-2">
                            用于检测“疑似错标”样本（例如猫被标成狗）。该能力后端对接后即可生效。
                          </el-text>
                        </el-form-item>
                        <el-form-item label="抽样上限">
                          <el-input-number v-model="labelMismatchMaxSamples" :min="100" :max="500000" :step="100" />
                        </el-form-item>
                        <el-form-item label="置信度阈值">
                          <el-slider v-model="labelMismatchConfidence" :min="0.5" :max="0.99" :step="0.01" show-input />
                        </el-form-item>
                        <el-form-item label="交叉验证折数">
                          <el-input-number v-model="labelMismatchFolds" :min="2" :max="10" :step="1" />
                        </el-form-item>
                        <el-form-item label="输出样例数">
                          <el-input-number v-model="labelMismatchMaxExamples" :min="10" :max="500" :step="10" />
                        </el-form-item>
                      </el-form>
                    </div>

                    <div v-else-if="activeDefectKey === 'distribution.numeric_drift' || activeDefectKey === 'distribution.categorical_drift'">
                      <el-form label-width="160px">
                        <el-form-item label="对比方式">
                          <el-radio-group v-model="distributionCompareMode">
                            <el-radio-button label="baseline_file">基线文件对比</el-radio-button>
                            <el-radio-button label="in_file_split">仅当前文件（免基线）</el-radio-button>
                          </el-radio-group>
                        </el-form-item>
                        <el-form-item v-if="distributionCompareMode === 'baseline_file'" label="基线文件">
                          <div class="flex items-center gap-2">
                            <el-tag v-if="baselineUploadedFile" type="success" effect="plain">已上传</el-tag>
                            <el-tag v-else type="warning" effect="plain">未上传</el-tag>
                            <el-button size="small" @click="gotoStep(1)">去上传</el-button>
                            <el-button v-if="baselineUploadedFile" size="small" @click="clearBaseline">清除</el-button>
                          </div>
                        </el-form-item>
                        <el-form-item v-else label="切分比例">
                          <el-slider v-model="distributionTrainTestSplit" :min="0.1" :max="0.9" :step="0.05" show-input />
                        </el-form-item>
                        <el-form-item label="敏感度">
                          <el-slider v-model="distributionPVal" :min="0.001" :max="0.2" :step="0.001" show-input />
                        </el-form-item>
                        <el-form-item label="排除字段">
                          <el-popover placement="bottom-start" :width="420" trigger="click">
                            <template #reference>
                              <el-input :model-value="excludeColumnsDisplay" readonly placeholder="点击选择要排除的列" />
                            </template>
                            <div v-if="columnsLoading" class="text-sm text-gray">正在解析列名...</div>
                            <div v-else-if="columnsError" class="text-sm text-red">{{ columnsError }}</div>
                            <el-scrollbar v-else height="220px">
                              <el-checkbox-group v-model="distributionExcludeColumns" class="flex flex-col gap-1">
                                <el-checkbox v-for="c in columnOptions" :key="c" :label="c">{{ c }}</el-checkbox>
                              </el-checkbox-group>
                            </el-scrollbar>
                            <div class="mt-2 flex justify-end gap-2">
                              <el-button size="small" @click="distributionExcludeColumns = []">清空</el-button>
                            </div>
                          </el-popover>
                        </el-form-item>
                      </el-form>
                    </div>

                    <div v-else-if="activeDefectKey === 'distribution.label_shift'">
                      <el-form label-width="160px">
                        <el-form-item label="标签列">
                          <el-select v-model="distributionLabelColumn" clearable filterable placeholder="选择标签列">
                            <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                          </el-select>
                          <el-text type="info" class="block mt-2">用于检测“标签分布变化”（label shift）。</el-text>
                        </el-form-item>
                        <el-form-item label="敏感度">
                          <el-slider v-model="distributionPVal" :min="0.001" :max="0.2" :step="0.001" show-input />
                        </el-form-item>
                      </el-form>
                    </div>

                    <div v-else-if="activeDefectKey?.startsWith('adversarial')">
                      <el-form label-width="170px">
                        <el-form-item label="扰动强度">
                          <el-slider v-model="adversarialEpsilon" :min="0" :max="0.3" :step="0.005" show-input />
                        </el-form-item>
                        <el-form-item label="最大迭代次数">
                          <el-input-number v-model="adversarialMaxIter" :min="1" :max="500" :step="5" />
                        </el-form-item>
                        <el-form-item label="搜索次数">
                          <el-input-number v-model="adversarialRandomTrials" :min="1" :max="500" :step="5" />
                        </el-form-item>
                        <el-form-item label="扰动特征数">
                          <el-input-number v-model="adversarialRandomFeatures" :min="1" :max="50" :step="1" />
                        </el-form-item>
                        <el-form-item label="采样上限">
                          <el-input-number v-model="adversarialMaxSamples" :min="10" :max="5000" :step="10" />
                        </el-form-item>
                        <el-form-item label="随机种子">
                          <el-input-number v-model="adversarialSeed" :min="0" :max="999999" :step="1" />
                        </el-form-item>
                      </el-form>
                    </div>

                    <div v-else-if="activeDefectKey?.startsWith('physics')">
                      <el-form label-width="170px">
                        <el-form-item label="启用守恒/一致性约束">
                          <el-switch v-model="physicsCheckConservation" />
                        </el-form-item>
                        <el-form-item label="自动启发式约束">
                          <el-switch v-model="physicsAutoConstraints" />
                        </el-form-item>
                      </el-form>
                      <el-divider class="my-3" />
                      <div class="flex-x-between mb-2">
                        <div class="font-bold">自定义约束（min/max）</div>
                        <el-button size="small" type="primary" @click="addPhysicsConstraint">添加约束</el-button>
                      </div>
                      <el-table :data="physicsConstraints" border size="small" style="width: 100%">
                        <el-table-column label="字段" min-width="160">
                          <template #default="{ row }">
                            <el-select v-model="row.column" filterable clearable placeholder="选择字段">
                              <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                            </el-select>
                          </template>
                        </el-table-column>
                        <el-table-column label="min" width="140">
                          <template #default="{ row }">
                            <el-input-number v-model="row.min" :step="1" />
                          </template>
                        </el-table-column>
                        <el-table-column label="max" width="140">
                          <template #default="{ row }">
                            <el-input-number v-model="row.max" :step="1" />
                          </template>
                        </el-table-column>
                        <el-table-column label="操作" width="90" fixed="right">
                          <template #default="{ row }">
                            <el-button link type="danger" @click="removePhysicsConstraint(row.id)">删除</el-button>
                          </template>
                        </el-table-column>
                      </el-table>
                      <el-text type="info" class="block mt-2">未设置 min/max 的行会被忽略；字段名来源于当前文件表头解析。</el-text>
                    </div>

                    <el-empty v-else description="该缺陷暂未提供可配置参数" />
                  </el-tab-pane>

                  <el-tab-pane label="输出设置" name="output">
                    <el-form label-width="140px">
                      <el-form-item label="导出 Word 报告">
                        <el-switch v-model="reportOptions.docx" />
                      </el-form-item>
                      <el-form-item label="导出摘要">
                        <el-switch v-model="reportOptions.summary" />
                      </el-form-item>
                      <el-form-item label="样例数量">
                        <el-input-number v-model="reportOptions.max_examples" :min="10" :max="500" :step="10" />
                      </el-form-item>
                    </el-form>
                    <el-text type="info">结果页可查看摘要并下载报告。</el-text>
                  </el-tab-pane>
                </el-tabs>
              </div>
            </el-card>

            <el-card shadow="never">
              <template #header>
                <div class="flex-x-between">
                  <div class="font-bold">配置预览</div>
                  <el-tag type="info" effect="plain" size="small">摘要</el-tag>
                </div>
              </template>

              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="启用模块">{{ selectedModulesDisplay }}</el-descriptions-item>
                <el-descriptions-item label="已选缺陷">{{ selectedDefectsDisplay }}</el-descriptions-item>
                <el-descriptions-item label="已选算法">{{ selectedAlgorithmsDisplay }}</el-descriptions-item>
                <el-descriptions-item label="扫描模式">{{ scanPresetLabel }}</el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>
        </el-row>

        <div class="mt-3 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <el-button icon="refresh" :loading="algorithmsLoading" @click="loadAlgorithms">刷新算法列表</el-button>
            <el-text type="info">可在右侧为选中的缺陷配置算法与参数</el-text>
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
			  { key: "distribution", title: "分布偏差检测", desc: "基线对比 / 免基线切分模拟" },
			  { key: "dirty_data", title: "脏数据扫描", desc: "异常/缺失/重复/值域违规" },
			  { key: "adversarial", title: "对抗性检测", desc: "扰动攻击下模型脆弱性评估" },
			  { key: "physics", title: "物理保真度扫描", desc: "规则/约束一致性校验" },
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
	type DistributionCompareMode = "baseline_file" | "in_file_split";
	const distributionCompareMode = ref<DistributionCompareMode>("baseline_file");
	const distributionTrainTestSplit = ref(0.7);
	const distributionLabelColumn = ref<string>("");
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

		type AlgoOptionStatus = "ready" | "planned";
		type AlgoOption = { key: string; label: string; desc: string; status: AlgoOptionStatus };
		type DefectStatus = AlgoOptionStatus;
		type DefectBadge = { text: string; type: "success" | "warning" | "info" | "danger" };
		type DefectTreeNode = {
		  key: string;
		  label: string;
		  desc?: string;
		  badge?: DefectBadge;
		  status?: DefectStatus;
		  disabled?: boolean;
		  module?: "dirty_data" | "distribution" | "adversarial" | "physics";
		  algorithms?: AlgoOption[];
		  children?: DefectTreeNode[];
		};

		const activeModuleTab = ref<string>("distribution");

	const distributionAlgorithmOptions: AlgoOption[] = [
	  {
	    key: "mmd_ks_chi2",
	    label: "MMD + KS + 卡方（两样本）",
	    desc: "对数值列做 MMD/KS，对类别列做卡方检验，输出 drift_detected 与 p_value。",
	    status: "ready",
	  },
		  {
		    key: "psi",
		    label: "PSI（Population Stability Index）",
		    desc: "更适合离散/分箱场景，输出稳定性指数。",
		    status: "planned",
		  },
		  {
		    key: "wasserstein",
		    label: "Wasserstein 距离",
		    desc: "对连续分布的距离度量，可用于分布差异排序。",
		    status: "planned",
		  },
		  {
		    key: "embedding_mmd",
		    label: "Embedding 分布漂移（文本/图像）",
		    desc: "对非结构化数据先做 embedding，再做分布对比。",
		    status: "planned",
		  },
		];

	const dirtyDataAlgorithmOptions: AlgoOption[] = [
		  {
		    key: "ecod_3sigma",
		    label: "ECOD + 3σ",
		    desc: "优先 ECOD（pyod），无依赖时降级为 3σ 规则。",
		    status: "ready",
		  },
		  {
		    key: "isolation_forest",
		    label: "IsolationForest",
		    desc: "对高维数值更稳定的异常检测。",
		    status: "planned",
		  },
		  {
		    key: "ruleset",
		    label: "可配置规则引擎",
		    desc: "按字段类型/业务规则进行检查。",
		    status: "planned",
		  },
		  {
		    key: "autoencoder",
		    label: "AutoEncoder 异常检测",
		    desc: "适合大规模/非线性异常。",
		    status: "planned",
		  },
		];

	const adversarialAlgorithmOptions: AlgoOption[] = [
		  {
		    key: "zoo_or_random",
		    label: "ZOO（ART）/ 随机扰动",
		    desc: "有 ART 则用 ZOO 黑盒攻击；无 ART 则使用随机扰动搜索降级。",
		    status: "ready",
		  },
		  { key: "fgsm", label: "FGSM（白盒）", desc: "快速白盒攻击，需要梯度支持。", status: "planned" },
		  { key: "pgd", label: "PGD（白盒）", desc: "更强的迭代攻击，需要梯度支持。", status: "planned" },
		  { key: "cw", label: "C&W（白盒）", desc: "优化式攻击，需要梯度支持。", status: "planned" },
		];

		const physicsAlgorithmOptions: AlgoOption[] = [
			  {
			    key: "pandera_or_fallback",
			    label: "Pandera Schema / 基础校验",
			    desc: "有 pandera 则 schema 校验，否则使用基本 min/max 规则验证。",
			    status: "ready",
			  },
		  {
		    key: "cross_constraints",
		    label: "跨字段约束（守恒/一致性）",
		    desc: "启用输入输出守恒等跨字段启发式规则（已接入）。",
		    status: "ready",
		  },
			  {
			    key: "causal_graph",
			    label: "因果图一致性",
			    desc: "基于因果图做一致性检查。",
			    status: "planned",
			  },
			  {
			    key: "temporal_rules",
			    label: "时序物理规律",
			    desc: "适用于时序数据的物理规律校验。",
			    status: "planned",
			  },
			];

		const dirtyMissingAlgorithmOptions: AlgoOption[] = [
		  {
		    key: "missing_stats_threshold",
		    label: "缺失统计 + 阈值",
		    desc: "统计每列缺失率，超过阈值则告警，并输出影响字段与缺失分布。",
		    status: "ready",
		  },
		  {
		    key: "missing_pattern_mcar",
		    label: "缺失模式分析（MCAR/MAR）",
		    desc: "分析缺失是否与其他字段相关，定位系统性缺失与采集偏差。",
		    status: "planned",
		  },
		  {
		    key: "auto_imputation_suggest",
		    label: "自动补全建议（KNN/Iterative）",
		    desc: "给出补全策略与风险提示，辅助数据修复。",
		    status: "planned",
		  },
		  {
		    key: "missing_correlation_heatmap",
		    label: "缺失相关性热力图",
		    desc: "以可视化方式呈现缺失相关结构，便于快速排查。",
		    status: "planned",
		  },
		];

		const dirtyDuplicateAlgorithmOptions: AlgoOption[] = [
		  {
		    key: "exact_duplicate",
		    label: "完全重复检测",
		    desc: "按整行或关键字段判断重复，输出重复率与示例行。",
		    status: "ready",
		  },
		  {
		    key: "near_duplicate_similarity",
		    label: "近重复（相似度）",
		    desc: "支持“近重复/模糊重复”识别（例如文本字段轻微差异）。",
		    status: "planned",
		  },
		  {
		    key: "minhash_lsh",
		    label: "MinHash + LSH",
		    desc: "适合大规模去重的近似方法。",
		    status: "planned",
		  },
		  {
		    key: "record_linkage",
		    label: "Record Linkage（实体对齐）",
		    desc: "针对多字段拼接的“同一实体多条记录”识别。",
		    status: "planned",
		  },
		];

		const dirtyRangeAlgorithmOptions: AlgoOption[] = [
		  { key: "sigma_rule", label: "3σ 规则", desc: "用均值±kσ 的启发式方式发现可疑极值。", status: "ready" },
		  { key: "iqr_rule", label: "IQR 规则", desc: "对长尾分布更稳健的四分位距方法。", status: "planned" },
		  { key: "domain_rules", label: "业务规则（min/max/枚举）", desc: "按字段业务约束检查取值范围。", status: "planned" },
		  { key: "schema_constraints", label: "Schema 约束联动", desc: "与 Pandera/规则库联动，统一落地字段约束。", status: "planned" },
		];

		const labelMismatchAlgorithmOptions: AlgoOption[] = [
		  {
		    key: "cv_consistency",
		    label: "交叉验证一致性",
		    desc: "通过交叉验证训练并找出“模型强烈不认可的标签”样本。",
		    status: "planned",
		  },
		  {
		    key: "embedding_knn",
		    label: "Embedding + KNN 近邻一致性",
		    desc: "在特征/embedding 空间中检查近邻标签一致性，发现疑似错标。",
		    status: "planned",
		  },
		  {
		    key: "confidence_margin",
		    label: "置信度边界样本",
		    desc: "识别高不确定样本与置信度异常样本，辅助人工复核。",
		    status: "planned",
		  },
		];

		const scanPreset = ref<"fast" | "balanced" | "thorough">("balanced");
		const globalMaxSamples = ref(20000);
		const globalParallelism = ref(2);
		const globalSeed = ref(42);
		const reportOptions = reactive({ docx: true, summary: true, max_examples: 50 });

		const scanPresetLabel = computed(() => {
		  const map: Record<string, string> = { fast: "快速", balanced: "均衡", thorough: "深度" };
		  return map[scanPreset.value] || scanPreset.value;
		});

		const defectSearch = ref("");
		const defectTreeRef = ref<any>();
		const defectTreeProps = { label: "label", children: "children", disabled: "disabled" } as const;

		const defectTreeData = ref<DefectTreeNode[]>([
		  {
		    key: "dirty_data",
		    label: "脏数据体系",
		    desc: "完整性 / 一致性 / 异常与噪声 / 标注质量",
		    children: [
		      {
		        key: "dirty_data.group_integrity",
		        label: "完整性（Completeness）",
		        desc: "缺失、空值、字段缺失等",
		        children: [
		          {
		            key: "dirty_data.missing",
		            label: "缺失值异常",
		            desc: "统计缺失率与缺失模式，定位缺失严重字段。",
		            badge: { text: "推荐", type: "success" },
		            status: "ready",
		            module: "dirty_data",
		            algorithms: dirtyMissingAlgorithmOptions,
		          },
		        ],
		      },
		      {
		        key: "dirty_data.group_noise",
		        label: "异常与噪声（Outliers）",
		        desc: "异常点、极值、噪声样本",
		        children: [
		          {
		            key: "dirty_data.anomaly",
		            label: "异常样本（Outlier）",
		            desc: "无监督异常检测，定位疑似异常行与可疑字段。",
		            badge: { text: "推荐", type: "success" },
		            status: "ready",
		            module: "dirty_data",
		            algorithms: dirtyDataAlgorithmOptions,
		          },
		          {
		            key: "dirty_data.range",
		            label: "值域违规",
		            desc: "用统计规则或业务规则识别异常取值范围。",
		            status: "ready",
		            module: "dirty_data",
		            algorithms: dirtyRangeAlgorithmOptions,
		          },
		        ],
		      },
		      {
		        key: "dirty_data.group_consistency",
		        label: "一致性（Consistency）",
		        desc: "重复、矛盾、规则不一致等",
		        children: [
		          {
		            key: "dirty_data.duplicate",
		            label: "重复 / 近重复",
		            desc: "识别完全重复与近重复记录，输出去重建议。",
		            status: "ready",
		            module: "dirty_data",
		            algorithms: dirtyDuplicateAlgorithmOptions,
		          },
		        ],
		      },
		      {
		        key: "dirty_data.group_label",
		        label: "标注质量（Label）",
		        desc: "错标、弱标注、标签噪声",
		        children: [
		          {
		            key: "dirty_data.label_mismatch",
		            label: "疑似错标（Label Mismatch）",
		            desc: "识别“标签与特征不一致”的样本（如猫被标成狗）。",
		            badge: { text: "即将上线", type: "warning" },
		            status: "planned",
		            disabled: true,
		            module: "dirty_data",
		            algorithms: labelMismatchAlgorithmOptions,
		          },
		        ],
		      },
		    ],
		  },
		  {
		    key: "distribution",
		    label: "分布偏差体系",
		    desc: "训练/基线 vs 当前数据分布变化监控",
		    children: [
		      {
		        key: "distribution.group_feature",
		        label: "特征漂移（Feature Drift）",
		        desc: "数值/类别特征的分布变化",
		        children: [
		          {
		            key: "distribution.numeric_drift",
		            label: "数值特征漂移",
		            desc: "对连续特征分布做两样本检验，输出漂移结论与 p 值。",
		            badge: { text: "推荐", type: "success" },
		            status: "ready",
		            module: "distribution",
		            algorithms: distributionAlgorithmOptions,
		          },
		          {
		            key: "distribution.categorical_drift",
		            label: "类别特征漂移",
		            desc: "对离散特征做卡方等检验，定位漂移字段。",
		            status: "ready",
		            module: "distribution",
		            algorithms: distributionAlgorithmOptions,
		          },
		        ],
		      },
		      {
		        key: "distribution.group_label",
		        label: "标签漂移（Label Shift）",
		        desc: "标签分布变化与类别占比变化",
		        children: [
		          {
		            key: "distribution.label_shift",
		            label: "标签分布变化",
		            desc: "对标签列做分布对比，监控类占比突变与先验变化。",
		            status: "ready",
		            module: "distribution",
		            algorithms: distributionAlgorithmOptions,
		          },
		        ],
		      },
		      {
		        key: "distribution.group_unstructured",
		        label: "非结构化漂移",
		        desc: "文本/图像 embedding 的漂移监控",
		        children: [
		          {
		            key: "distribution.embedding_drift",
		            label: "Embedding 分布漂移（文本/图像）",
		            desc: "对非结构化数据先做 embedding，再做分布对比。",
		            badge: { text: "即将上线", type: "warning" },
		            status: "planned",
		            disabled: true,
		            module: "distribution",
		            algorithms: distributionAlgorithmOptions,
		          },
		        ],
		      },
		    ],
		  },
		  {
		    key: "adversarial",
		    label: "对抗性与鲁棒性体系",
		    desc: "黑盒/白盒攻击下模型脆弱性评估",
		    children: [
		      {
		        key: "adversarial.group_attack",
		        label: "攻击评估（Attack）",
		        desc: "攻击成功率、扰动预算与鲁棒性",
		        children: [
		          {
		            key: "adversarial.blackbox",
		            label: "黑盒攻击（ZOO/随机）",
		            desc: "在无梯度条件下进行黑盒攻击，评估模型易受攻击程度。",
		            badge: { text: "可用", type: "success" },
		            status: "ready",
		            module: "adversarial",
		            algorithms: adversarialAlgorithmOptions,
		          },
		          {
		            key: "adversarial.whitebox",
		            label: "白盒攻击（FGSM/PGD）",
		            desc: "基于梯度的白盒攻击评估（需要模型与梯度接口）。",
		            badge: { text: "即将上线", type: "warning" },
		            status: "planned",
		            disabled: true,
		            module: "adversarial",
		            algorithms: adversarialAlgorithmOptions,
		          },
		        ],
		      },
		      {
		        key: "adversarial.group_monitor",
		        label: "鲁棒性监控（Monitoring）",
		        desc: "敏感特征、鲁棒性分解与风险提示",
		        children: [
		          {
		            key: "adversarial.sensitivity",
		            label: "特征敏感性分析",
		            desc: "识别对扰动最敏感的特征与子群体风险。",
		            badge: { text: "即将上线", type: "warning" },
		            status: "planned",
		            disabled: true,
		            module: "adversarial",
		            algorithms: adversarialAlgorithmOptions,
		          },
		        ],
		      },
		    ],
		  },
		  {
		    key: "physics",
		    label: "物理保真度与规则体系",
		    desc: "规则/约束一致性与守恒校验",
		    children: [
		      {
		        key: "physics.group_schema",
		        label: "Schema 与字段约束",
		        desc: "类型/范围/枚举/依赖约束",
		        children: [
		          {
		            key: "physics.schema",
		            label: "Schema 校验（字段约束）",
		            desc: "字段类型、范围、枚举与必填约束检查。",
		            badge: { text: "推荐", type: "success" },
		            status: "ready",
		            module: "physics",
		            algorithms: physicsAlgorithmOptions,
		          },
		        ],
		      },
		      {
		        key: "physics.group_conservation",
		        label: "跨字段一致性",
		        desc: "守恒、平衡、逻辑一致性等",
		        children: [
		          {
		            key: "physics.conservation",
		            label: "守恒/一致性校验",
		            desc: "启用跨字段启发式规则与自定义 min/max 约束。",
		            status: "ready",
		            module: "physics",
		            algorithms: physicsAlgorithmOptions,
		          },
		        ],
		      },
		      {
		        key: "physics.group_future",
		        label: "高级规则（Advanced）",
		        desc: "因果/时序/结构化规则",
		        children: [
		          {
		            key: "physics.temporal",
		            label: "时序物理规律",
		            desc: "面向时序数据的物理规律校验（例如单调、周期、滞后）。",
		            badge: { text: "即将上线", type: "warning" },
		            status: "planned",
		            disabled: true,
		            module: "physics",
		            algorithms: physicsAlgorithmOptions,
		          },
		        ],
		      },
		    ],
		  },
		]);

		function buildDefectIndex(nodes: DefectTreeNode[]) {
		  const nodeByKey: Record<string, DefectTreeNode> = {};
		  const pathByKey: Record<string, string[]> = {};
		  const leafKeys: string[] = [];

		  const walk = (items: DefectTreeNode[], ancestors: string[]) => {
		    for (const n of items) {
		      nodeByKey[n.key] = n;
		      const path = [...ancestors, n.label];
		      pathByKey[n.key] = path;
		      if (n.children?.length) {
		        walk(n.children, path);
		      } else {
		        leafKeys.push(n.key);
		      }
		    }
		  };

		  walk(nodes, []);
		  return { nodeByKey, pathByKey, leafKeys };
		}

		const defectIndex = computed(() => buildDefectIndex(defectTreeData.value));

		const defaultExpandedDefectKeys = [
		  "dirty_data",
		  "dirty_data.group_integrity",
		  "dirty_data.group_noise",
		  "dirty_data.group_consistency",
		  "dirty_data.group_label",
		  "distribution",
		  "distribution.group_feature",
		  "distribution.group_label",
		  "distribution.group_unstructured",
		  "adversarial",
		  "adversarial.group_attack",
		  "adversarial.group_monitor",
		  "physics",
		  "physics.group_schema",
		  "physics.group_conservation",
		  "physics.group_future",
		];

		const defaultCheckedDefectKeys = [
		  "dirty_data.anomaly",
		  "dirty_data.missing",
		  "dirty_data.duplicate",
		  "dirty_data.range",
		  "distribution.numeric_drift",
		  "distribution.categorical_drift",
		  "adversarial.blackbox",
		  "physics.schema",
		  "physics.conservation",
		];

		const checkedDefectKeys = ref<string[]>([...defaultCheckedDefectKeys]);
		const activeDefectKey = ref<string>("dirty_data.anomaly");
		const activeDefectTab = ref<"algo" | "params" | "output">("algo");

		function createDefaultDefectAlgorithms(): Record<string, string[]> {
		  return {
		    "dirty_data.anomaly": ["ecod_3sigma"],
		    "dirty_data.missing": ["missing_stats_threshold"],
		    "dirty_data.duplicate": ["exact_duplicate"],
		    "dirty_data.range": ["sigma_rule"],
		    "dirty_data.label_mismatch": [],
		    "distribution.numeric_drift": ["mmd_ks_chi2"],
		    "distribution.categorical_drift": ["mmd_ks_chi2"],
		    "distribution.label_shift": ["mmd_ks_chi2"],
		    "distribution.embedding_drift": [],
		    "adversarial.blackbox": ["zoo_or_random"],
		    "adversarial.whitebox": [],
		    "adversarial.sensitivity": [],
		    "physics.schema": ["pandera_or_fallback"],
		    "physics.conservation": ["cross_constraints"],
		    "physics.temporal": [],
		  };
		}

		const defectAlgorithms = ref<Record<string, string[]>>(createDefaultDefectAlgorithms());

		const activeDefectMeta = computed<DefectTreeNode | null>(() => {
		  const node = defectIndex.value.nodeByKey[activeDefectKey.value];
		  if (!node || !node.algorithms) return null;
		  return node;
		});

		const activeDefectPathText = computed(() => {
		  const path = defectIndex.value.pathByKey[activeDefectKey.value];
		  return path?.length ? path.join(" / ") : "-";
		});

		function getCheckedLeafKeys(): string[] {
		  const tree = defectTreeRef.value;
		  if (tree?.getCheckedKeys) {
		    const keys = tree.getCheckedKeys(true) as string[];
		    return Array.from(new Set(keys.filter((k) => typeof k === "string")));
		  }
		  return Array.from(new Set(checkedDefectKeys.value));
		}

		function moduleKeyFromDefectKey(key: string): "dirty_data" | "distribution" | "adversarial" | "physics" | null {
		  const prefix = key.split(".")[0];
		  if (prefix === "dirty_data" || prefix === "distribution" || prefix === "adversarial" || prefix === "physics") return prefix;
		  return null;
		}

		function syncDerivedFromChecked(keys: string[]) {
		  const moduleSet = new Set<string>();
		  const dirtyChecks = new Set<string>();

		  for (const k of keys) {
		    const moduleKey = moduleKeyFromDefectKey(k);
		    if (moduleKey) moduleSet.add(moduleKey);
		    if (k === "dirty_data.anomaly") dirtyChecks.add("anomaly");
		    else if (k === "dirty_data.missing") dirtyChecks.add("missing");
		    else if (k === "dirty_data.duplicate") dirtyChecks.add("duplicate");
		    else if (k === "dirty_data.range") dirtyChecks.add("range");
		    else if (k === "dirty_data.label_mismatch") dirtyChecks.add("label_mismatch");
		  }

		  selectedModules.value = Array.from(moduleSet);
		  dirtyEnabledChecks.value = Array.from(dirtyChecks);
		}

		function setCheckedDefects(keys: string[]) {
		  const uniq = Array.from(new Set(keys));
		  const tree = defectTreeRef.value;
		  if (tree?.setCheckedKeys) {
		    tree.setCheckedKeys(uniq);
		    checkedDefectKeys.value = getCheckedLeafKeys();
		  } else {
		    checkedDefectKeys.value = uniq;
		  }
		  syncDerivedFromChecked(checkedDefectKeys.value);
		}

		const activeDefectAlgorithms = computed<string[]>({
		  get() {
		    if (!activeDefectKey.value) return [];
		    return defectAlgorithms.value[activeDefectKey.value] || [];
		  },
		  set(v) {
		    if (!activeDefectKey.value) return;
		    defectAlgorithms.value[activeDefectKey.value] = Array.from(new Set((v || []).filter((x) => !!x)));
		  },
		});

		const activeDefectEnabled = computed<boolean>({
		  get() {
		    if (!activeDefectKey.value) return false;
		    return checkedDefectKeys.value.includes(activeDefectKey.value);
		  },
		  set(v) {
		    const meta = activeDefectMeta.value;
		    if (!activeDefectKey.value || !meta) return;
		    if (meta.status !== "ready") return;
		    const tree = defectTreeRef.value;
		    if (tree?.setChecked) {
		      tree.setChecked(activeDefectKey.value, !!v, true);
		      checkedDefectKeys.value = getCheckedLeafKeys();
		    } else {
		      const set = new Set(checkedDefectKeys.value);
		      if (v) set.add(activeDefectKey.value);
		      else set.delete(activeDefectKey.value);
		      checkedDefectKeys.value = Array.from(set);
		    }
		    syncDerivedFromChecked(checkedDefectKeys.value);
		  },
		});

		const selectedLeafDefectCount = computed(() => checkedDefectKeys.value.length);
		const selectedDefectAlgorithmCount = computed(() => {
		  let total = 0;
		  for (const k of checkedDefectKeys.value) {
		    total += (defectAlgorithms.value[k] || []).length;
		  }
		  return total;
		});

		const selectedModulesDisplay = computed(() => {
		  if (!selectedModules.value.length) return "未选择";
		  const titleByKey = new Map(modules.map((m) => [m.key, m.title]));
		  return selectedModules.value.map((k) => titleByKey.get(k) || k).join("、");
		});

		const selectedDefectsDisplay = computed(() => {
		  const labels = checkedDefectKeys.value
		    .map((k) => defectIndex.value.nodeByKey[k]?.label)
		    .filter((x): x is string => !!x);
		  if (!labels.length) return "未选择";
		  if (labels.length <= 4) return labels.join("、");
		  return `${labels.slice(0, 4).join("、")} 等${labels.length}项`;
		});

		const selectedAlgorithmsDisplay = computed(() => {
		  const algoLabelMap: Record<string, string> = {};
		  for (const n of Object.values(defectIndex.value.nodeByKey)) {
		    for (const a of n.algorithms || []) {
		      if (!algoLabelMap[a.key]) algoLabelMap[a.key] = a.label;
		    }
		  }
		  const algoKeys = new Set<string>();
		  for (const defectKey of checkedDefectKeys.value) {
		    for (const a of defectAlgorithms.value[defectKey] || []) algoKeys.add(a);
		  }
		  const labels = Array.from(algoKeys)
		    .map((k) => algoLabelMap[k] || k)
		    .filter((x) => !!x);
		  if (!labels.length) return "未选择";
		  if (labels.length <= 3) return labels.join("、");
		  return `${labels.slice(0, 3).join("、")} 等${labels.length}项`;
		});

		function firstLeafKeyOf(node: DefectTreeNode): string | null {
		  if (!node.children?.length) return node.key;
		  for (const c of node.children) {
		    const leaf = firstLeafKeyOf(c);
		    if (leaf) return leaf;
		  }
		  return null;
		}

		function onDefectNodeClick(data: DefectTreeNode) {
		  const leafKey = firstLeafKeyOf(data);
		  if (!leafKey) return;
		  activeDefectKey.value = leafKey;
		}

		function onDefectCheck() {
		  checkedDefectKeys.value = getCheckedLeafKeys();
		  syncDerivedFromChecked(checkedDefectKeys.value);
		}

		function filterDefectNode(value: string, data: DefectTreeNode) {
		  if (!value) return true;
		  const v = value.trim().toLowerCase();
		  const hay = `${data.label || ""} ${data.desc || ""}`.toLowerCase();
		  return hay.includes(v);
		}

		function selectAllDefects() {
		  const keys = defectIndex.value.leafKeys.filter((k) => !defectIndex.value.nodeByKey[k]?.disabled);
		  setCheckedDefects(keys);
		}

		function selectRecommendedDefects() {
		  const keys = defaultCheckedDefectKeys.filter((k) => !defectIndex.value.nodeByKey[k]?.disabled);
		  setCheckedDefects(keys);
		}

		function clearDefects() {
		  setCheckedDefects([]);
		}

			watch(defectSearch, (v) => {
			  defectTreeRef.value?.filter?.(v);
			});

			const distributionAlgorithms = ref<string[]>(["mmd_ks_chi2"]);
			const dirtyDataAlgorithms = ref<string[]>(["ecod_3sigma"]);
			const adversarialAlgorithms = ref<string[]>(["zoo_or_random"]);
			const physicsAlgorithms = ref<string[]>(["pandera_or_fallback"]);

		// 脏数据模块参数（UI 侧）
		const dirtyContamination = ref(0.1);
			const dirtyMissingThreshold = ref(0.1);
			const dirtyDuplicateThreshold = ref(0.02);
			const dirtyEnabledChecks = ref<string[]>(["anomaly", "missing", "duplicate", "range"]);
			const dirtyMaxExamples = ref(50);
			const dirtyWhitelistColumns = ref<string[]>([]);
			const dirtyBlacklistColumns = ref<string[]>([]);
			syncDerivedFromChecked(checkedDefectKeys.value);
			const duplicateKeyColumns = ref<string[]>([]);
			const duplicateSimilarity = ref(0.92);
			const rangeMethod = ref<"sigma" | "iqr" | "rules">("sigma");
		const rangeSigma = ref(3);
		const rangeIqrFactor = ref(1.5);
		const rangeOnlyColumns = ref<string[]>([]);
		const labelMismatchLabelColumn = ref<string>("");
		const labelMismatchMaxSamples = ref(20000);
		const labelMismatchConfidence = ref(0.8);
		const labelMismatchFolds = ref(5);
		const labelMismatchMaxExamples = ref(50);

	// 对抗性模块参数（UI 侧）
	const adversarialEpsilon = ref(0.05);
	const adversarialMaxIter = ref(20);
	const adversarialRandomTrials = ref(40);
	const adversarialRandomFeatures = ref(3);
	const adversarialMaxSamples = ref(50);
	const adversarialSeed = ref(42);
	const adversarialLearningRate = ref(0.01);
	const adversarialConfidence = ref(0);
	const adversarialBatchSize = ref(1);

	// 物理保真度模块参数（UI 侧）
	const physicsCheckConservation = ref(false);
	const physicsAutoConstraints = ref(true);
	type PhysicsConstraintRow = { id: string; column: string; min?: number; max?: number };
	const physicsConstraints = ref<PhysicsConstraintRow[]>([]);

	function addPhysicsConstraint() {
	  physicsConstraints.value.push({
	    id: `${Date.now()}_${Math.random().toString(16).slice(2)}`,
	    column: "",
	    min: undefined,
	    max: undefined,
	  });
	}

	function removePhysicsConstraint(id: string) {
	  physicsConstraints.value = physicsConstraints.value.filter((x) => x.id !== id);
	}

		let ws: WebSocket | null = null;
		let pollTimer: number | null = null;

		const canStart = computed(
		  () =>
		    !!currentUploadedFile.value?.file_id &&
		    !!selectedAlgorithm.value &&
		    selectedLeafDefectCount.value > 0 &&
		    !starting.value
		);
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
			  defectSearch.value = "";
			  scanPreset.value = "balanced";
			  globalMaxSamples.value = 20000;
			  globalParallelism.value = 2;
			  globalSeed.value = 42;
			  reportOptions.docx = true;
			  reportOptions.summary = true;
			  reportOptions.max_examples = 50;
			  defectAlgorithms.value = createDefaultDefectAlgorithms();
			  checkedDefectKeys.value = [...defaultCheckedDefectKeys];
			  setCheckedDefects(checkedDefectKeys.value);
			  activeDefectKey.value = "dirty_data.anomaly";
			  activeDefectTab.value = "algo";
			  activeModuleTab.value = "distribution";
			  distributionAlgorithms.value = ["mmd_ks_chi2"];
			  dirtyDataAlgorithms.value = ["ecod_3sigma"];
			  adversarialAlgorithms.value = ["zoo_or_random"];
			  physicsAlgorithms.value = ["pandera_or_fallback"];
		  distributionCompareMode.value = "baseline_file";
		  distributionTrainTestSplit.value = 0.7;
		  distributionLabelColumn.value = "";
		  distributionPVal.value = 0.05;
		  distributionExcludeColumns.value = [];
		  dirtyContamination.value = 0.1;
		  dirtyMissingThreshold.value = 0.1;
			  dirtyDuplicateThreshold.value = 0.02;
			  dirtyEnabledChecks.value = ["anomaly", "missing", "duplicate", "range"];
			  dirtyMaxExamples.value = 50;
			  dirtyWhitelistColumns.value = [];
			  dirtyBlacklistColumns.value = [];
			  duplicateKeyColumns.value = [];
			  duplicateSimilarity.value = 0.92;
			  rangeMethod.value = "sigma";
			  rangeSigma.value = 3;
			  rangeIqrFactor.value = 1.5;
			  rangeOnlyColumns.value = [];
			  labelMismatchLabelColumn.value = "";
			  labelMismatchMaxSamples.value = 20000;
			  labelMismatchConfidence.value = 0.8;
			  labelMismatchFolds.value = 5;
			  labelMismatchMaxExamples.value = 50;
			  adversarialEpsilon.value = 0.05;
			  adversarialMaxIter.value = 20;
			  adversarialRandomTrials.value = 40;
			  adversarialRandomFeatures.value = 3;
		  adversarialMaxSamples.value = 50;
		  adversarialSeed.value = 42;
		  adversarialLearningRate.value = 0.01;
		  adversarialConfidence.value = 0;
		  adversarialBatchSize.value = 1;
		  physicsCheckConservation.value = false;
		  physicsAutoConstraints.value = true;
		  physicsConstraints.value = [];
		  columnOptions.value = [];
		  columnsLoading.value = false;
		  columnsError.value = null;
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
	    if (distributionLabelColumn.value && !cols.includes(distributionLabelColumn.value)) {
	      distributionLabelColumn.value = "";
		    }
		    dirtyWhitelistColumns.value = dirtyWhitelistColumns.value.filter((c) => cols.includes(c));
		    dirtyBlacklistColumns.value = dirtyBlacklistColumns.value.filter((c) => cols.includes(c));
		    duplicateKeyColumns.value = duplicateKeyColumns.value.filter((c) => cols.includes(c));
		    rangeOnlyColumns.value = rangeOnlyColumns.value.filter((c) => cols.includes(c));
		    if (labelMismatchLabelColumn.value && !cols.includes(labelMismatchLabelColumn.value)) {
		      labelMismatchLabelColumn.value = "";
		    }
		    physicsConstraints.value = physicsConstraints.value.map((x) => {
		      if (!x.column) return x;
		      if (cols.includes(x.column)) return x;
		      return { ...x, column: "" };
		    });
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
		    const enabledDefects = [...checkedDefectKeys.value];
		    const effectiveModules = selectedModules.value?.length
		      ? selectedModules.value
		      : Array.from(
		          new Set(enabledDefects.map((k) => moduleKeyFromDefectKey(k)).filter((x): x is string => !!x))
		        );

		    const moduleAlgorithms = (() => {
		      const out: Record<string, Set<string>> = {
		        distribution: new Set<string>(),
		        dirty_data: new Set<string>(),
		        adversarial: new Set<string>(),
		        physics: new Set<string>(),
		      };
		      for (const defectKey of enabledDefects) {
		        const moduleKey = moduleKeyFromDefectKey(defectKey);
		        if (!moduleKey) continue;
		        for (const a of defectAlgorithms.value[defectKey] || []) out[moduleKey].add(a);
		      }
		      const toList = (set: Set<string>, fallback: string[]) => (set.size ? Array.from(set) : fallback);
		      return {
		        distribution: toList(out.distribution, distributionAlgorithms.value),
		        dirty_data: toList(out.dirty_data, dirtyDataAlgorithms.value),
		        adversarial: toList(out.adversarial, adversarialAlgorithms.value),
		        physics: toList(out.physics, physicsAlgorithms.value),
		      };
		    })();

		    const params: Record<string, any> = {
		      modules: effectiveModules.length ? effectiveModules : undefined,
		      module_algorithms: moduleAlgorithms,
		      runtime: {
		        preset: scanPreset.value,
		        max_samples: globalMaxSamples.value,
		        parallelism: globalParallelism.value,
		        seed: globalSeed.value,
		      },
		      report: { ...reportOptions },
		    };

		    if (effectiveModules.includes("distribution")) {
		      params.distribution_compare_mode = distributionCompareMode.value;
		      params.p_val = distributionPVal.value;
		      params.train_test_split = distributionTrainTestSplit.value;
	      if (distributionLabelColumn.value) {
	        params.label_column = distributionLabelColumn.value;
	      }
	      if (distributionExcludeColumns.value.length) {
	        params.exclude_columns = distributionExcludeColumns.value;
	      }
	    }

		    if (effectiveModules.includes("dirty_data")) {
		      params.contamination = dirtyContamination.value;
		      params.dirty_data = {
		        enabled_checks: dirtyEnabledChecks.value,
		        missing_threshold: dirtyMissingThreshold.value,
		        duplicate_threshold: dirtyDuplicateThreshold.value,
		        duplicate_key_columns: duplicateKeyColumns.value,
		        duplicate_similarity: duplicateSimilarity.value,
		        max_examples: dirtyMaxExamples.value,
		        whitelist_columns: dirtyWhitelistColumns.value,
		        blacklist_columns: dirtyBlacklistColumns.value,
		        range: {
		          method: rangeMethod.value,
		          sigma: rangeSigma.value,
		          iqr_factor: rangeIqrFactor.value,
		          only_columns: rangeOnlyColumns.value,
		        },
		        label_mismatch: {
		          label_column: labelMismatchLabelColumn.value,
		          max_samples: labelMismatchMaxSamples.value,
		          confidence: labelMismatchConfidence.value,
		          folds: labelMismatchFolds.value,
		          max_examples: labelMismatchMaxExamples.value,
		        },
		      };
		    }

	    if (effectiveModules.includes("adversarial")) {
	      params.adversarial = {
	        epsilon: adversarialEpsilon.value,
	        max_iter: adversarialMaxIter.value,
	        random_trials: adversarialRandomTrials.value,
	        random_features: adversarialRandomFeatures.value,
	        max_samples: adversarialMaxSamples.value,
	        seed: adversarialSeed.value,
	        learning_rate: adversarialLearningRate.value,
	        confidence: adversarialConfidence.value,
	        batch_size: adversarialBatchSize.value,
	      };
	    }

		    if (effectiveModules.includes("physics")) {
		      const constraints: Record<string, any> = {};
		      for (const x of physicsConstraints.value) {
		        if (!x.column) continue;
	        const rule: Record<string, any> = {};
	        if (typeof x.min === "number") rule.min = x.min;
	        if (typeof x.max === "number") rule.max = x.max;
	        if (Object.keys(rule).length) constraints[x.column] = rule;
	      }
	      params.physics = {
	        check_conservation: physicsCheckConservation.value,
	        auto_constraints: physicsAutoConstraints.value,
		        constraints,
		      };
		    }

		    const defectsPayload: Record<string, any> = {};
		    for (const defectKey of enabledDefects) {
		      const meta = defectIndex.value.nodeByKey[defectKey];
		      const moduleKey = moduleKeyFromDefectKey(defectKey);
		      const buildParamsFor = () => {
		        if (defectKey === "dirty_data.anomaly") {
		          return { contamination: dirtyContamination.value, max_examples: dirtyMaxExamples.value, max_samples: globalMaxSamples.value };
		        }
		        if (defectKey === "dirty_data.missing") {
		          return {
		            missing_threshold: dirtyMissingThreshold.value,
		            whitelist_columns: dirtyWhitelistColumns.value,
		            blacklist_columns: dirtyBlacklistColumns.value,
		          };
		        }
		        if (defectKey === "dirty_data.duplicate") {
		          return {
		            duplicate_threshold: dirtyDuplicateThreshold.value,
		            key_columns: duplicateKeyColumns.value,
		            similarity: duplicateSimilarity.value,
		          };
		        }
		        if (defectKey === "dirty_data.range") {
		          return {
		            method: rangeMethod.value,
		            sigma: rangeSigma.value,
		            iqr_factor: rangeIqrFactor.value,
		            only_columns: rangeOnlyColumns.value,
		          };
		        }
		        if (defectKey === "dirty_data.label_mismatch") {
		          return {
		            label_column: labelMismatchLabelColumn.value,
		            max_samples: labelMismatchMaxSamples.value,
		            confidence: labelMismatchConfidence.value,
		            folds: labelMismatchFolds.value,
		            max_examples: labelMismatchMaxExamples.value,
		          };
		        }
		        if (defectKey === "distribution.numeric_drift" || defectKey === "distribution.categorical_drift") {
		          return {
		            compare_mode: distributionCompareMode.value,
		            p_val: distributionPVal.value,
		            train_test_split: distributionTrainTestSplit.value,
		            exclude_columns: distributionExcludeColumns.value,
		          };
		        }
		        if (defectKey === "distribution.label_shift") {
		          return { label_column: distributionLabelColumn.value, p_val: distributionPVal.value };
		        }
		        if (defectKey.startsWith("adversarial")) {
		          return {
		            epsilon: adversarialEpsilon.value,
		            max_iter: adversarialMaxIter.value,
		            random_trials: adversarialRandomTrials.value,
		            random_features: adversarialRandomFeatures.value,
		            max_samples: adversarialMaxSamples.value,
		            seed: adversarialSeed.value,
		            learning_rate: adversarialLearningRate.value,
		            confidence: adversarialConfidence.value,
		            batch_size: adversarialBatchSize.value,
		          };
		        }
		        if (defectKey.startsWith("physics")) {
		          const constraints: Record<string, any> = {};
		          for (const x of physicsConstraints.value) {
		            if (!x.column) continue;
		            const rule: Record<string, any> = {};
		            if (typeof x.min === "number") rule.min = x.min;
		            if (typeof x.max === "number") rule.max = x.max;
		            if (Object.keys(rule).length) constraints[x.column] = rule;
		          }
		          return {
		            check_conservation: physicsCheckConservation.value,
		            auto_constraints: physicsAutoConstraints.value,
		            constraints,
		          };
		        }
		        return {};
		      };
		      defectsPayload[defectKey] = {
		        enabled: true,
		        status: meta?.status || "ready",
		        module: moduleKey,
		        label: meta?.label,
		        path: defectIndex.value.pathByKey[defectKey]?.join(" / "),
		        algorithms: defectAlgorithms.value[defectKey] || [],
		        params: buildParamsFor(),
		      };
		    }

		    params.defects = {
		      preset: scanPreset.value,
		      global: {
		        max_samples: globalMaxSamples.value,
		        parallelism: globalParallelism.value,
		        seed: globalSeed.value,
		      },
		      report: { ...reportOptions },
		      selected: defectsPayload,
		    };

		    const baselineFileId =
		      effectiveModules.includes("distribution") && distributionCompareMode.value === "baseline_file"
		        ? baselineUploadedFile.value?.file_id
		        : undefined;
	    const res = await DQScanAPI.createTask({
	      file_id: currentUploadedFile.value.file_id,
	      baseline_file_id: baselineFileId,
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

	const resultModules = computed(() => {
  const r = result.value;
  if (!r?.modules) return [];
  return Object.keys(r.modules).map((k) => {
    const mr = r.modules[k] || {};
    const rep = r.reports?.[k]?.paths || {};
    const extra = (() => {
      if (k === "dirty_data") return { label: "异常率", value: mr.anomaly_rate };
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

.dqscan-module-pane {
  min-height: 680px;
}

.dqscan-ul {
  padding-left: 18px;
  margin: 0;
}
.dqscan-ul li {
  margin: 6px 0;
  color: var(--el-text-color-regular);
}

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

.dqscan-config-tabs :deep(.el-tabs__content) {
  padding-left: 8px;
}

.dqscan-config-tabs :deep(.el-tabs__item) {
  height: 44px;
  line-height: 44px;
}

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
</style>

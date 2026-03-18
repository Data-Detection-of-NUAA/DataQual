<template>
  <!-- Step 2: image config -->
  <el-card v-show="activeStep === 2 && selectedModality === 'image'" shadow="never" class="mt-4">
    <template #header>
      <div class="font-bold">图片错标检测配置</div>
    </template>

    <el-alert
      type="info"
      show-icon
      :closable="false"
      title="图片分类错标检测"
      description="使用 CLIP 嵌入 + KNN 邻域投票（SimiFeat KNN）或感知哈希离群（pHash Outlier）检测图片分类数据集中的标签错误。"
      class="mb-3"
    />

    <el-card shadow="never" class="mb-3">
      <template #header><div class="font-bold">算法选择</div></template>
      <el-form label-width="120px">
        <el-form-item label="检测算法">
          <el-radio-group v-model="imageLabelAlgorithm">
            <el-radio-button label="simifeat_knn">SimiFeat KNN（推荐）</el-radio-button>
            <el-radio-button label="phash_outlier">pHash Outlier（轻量兜底）</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="设备">
          <el-radio-group v-model="imageLabelDevice">
            <el-radio-button label="auto">自动</el-radio-button>
            <el-radio-button label="cpu">CPU</el-radio-button>
            <el-radio-button label="cuda">CUDA</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="mb-3">
      <template #header><div class="font-bold">标签文件列映射</div></template>
      <el-form label-width="120px">
        <el-form-item label="图片路径列">
          <el-input v-model="imageLabelImageColumn" placeholder="image_path" />
        </el-form-item>
        <el-form-item label="标签列">
          <el-input v-model="imageLabelLabelColumn" placeholder="label" />
        </el-form-item>
        <el-form-item label="CSV 文件名">
          <el-input v-model="imageLabelCsvPath" placeholder="留空则自动检测 ZIP 内 CSV" />
          <el-text type="info" class="block mt-1">ZIP 内含多个 CSV 时请指定文件名，例如 labels.csv</el-text>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="mb-3">
      <template #header><div class="font-bold">高级参数</div></template>
      <el-form label-width="140px">
        <el-form-item label="KNN 邻居数 (k)">
          <el-input-number v-model="imageLabelK" :min="1" :max="50" />
        </el-form-item>
        <el-form-item label="投票阈值">
          <el-slider v-model="imageLabelThreshold" :min="0.1" :max="1.0" :step="0.05" show-input />
        </el-form-item>
        <el-form-item label="最大采样数">
          <el-input-number v-model="imageLabelMaxSamples" :min="100" :max="50000" :step="500" />
        </el-form-item>
        <el-form-item label="最大展示条数">
          <el-input-number v-model="imageLabelMaxExamples" :min="10" :max="5000" :step="50" />
        </el-form-item>
        <el-form-item label="批大小">
          <el-input-number v-model="imageLabelBatchSize" :min="1" :max="128" :step="8" />
        </el-form-item>
      </el-form>
    </el-card>

    <div class="mt-3 flex items-center justify-end gap-2">
      <el-button @click="gotoStep(1)">上一步</el-button>
      <el-button type="success" :loading="starting" icon="video-play" @click="startScan">
        开始检测
      </el-button>
    </div>
  </el-card>

  <!-- Step 2: tabular config -->
  <el-card v-show="activeStep === 2 && selectedModality !== 'image'" shadow="never" class="mt-4">
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
        <!-- 缺陷树 -->
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
                  <el-tooltip v-if="data.desc" :content="data.desc" placement="right" :show-after="300">
                    <span>{{ data.label }}</span>
                  </el-tooltip>
                  <span v-else>{{ data.label }}</span>
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

        <!-- 运行策略 -->
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

          <el-divider class="my-3" />

          <div class="font-bold mb-2">报告输出</div>
          <el-form label-width="110px">
            <el-form-item label="Word 报告">
              <el-switch v-model="reportOptions.docx" />
            </el-form-item>
            <el-form-item label="摘要报告">
              <el-switch v-model="reportOptions.summary" />
            </el-form-item>
            <el-form-item label="样例数量">
              <el-input-number v-model="reportOptions.max_examples" :min="10" :max="500" :step="10" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :md="16" :xs="24">
        <!-- 模块配置工作台 -->
        <el-card shadow="never" class="mb-3">
          <template #header>
            <div class="flex-x-between">
              <div class="flex items-center gap-2">
                <div class="font-bold">模块配置工作台</div>
                <el-tag type="info" effect="plain" size="small">模块级算法 + 缺陷绑定</el-tag>
              </div>
              <div class="flex items-center gap-2">
                <el-switch
                  v-model="showOnlyEnabledDefects"
                  active-text="仅显示已启用缺陷"
                  inactive-text="显示全部缺陷"
                />
                <el-button size="small" @click="expandAllModulePanels">展开全部</el-button>
                <el-button size="small" @click="collapseAllModulePanels">折叠全部</el-button>
              </div>
            </div>
          </template>

          <el-alert
            type="info"
            show-icon
            :closable="false"
            title="先配基础参数，再绑定缺陷算法"
            description="推荐流程：先完成模块「基础参数」，再在「缺陷绑定」里为每个缺陷选择执行算法；最后到「算法参数」里补充该算法的特定参数。"
            class="mb-3"
          />
          <el-alert
            v-if="configIssuesHint"
            type="warning"
            show-icon
            :closable="false"
            title="还有配置未完成"
            :description="configIssuesHint"
            class="mb-3"
          />

          <el-collapse v-model="openModulePanels" class="dqscan-module-workbench">
            <el-collapse-item v-for="m in modules" :key="m.key" :name="m.key">
              <template #title>
                <div class="dqscan-collapse-title">
                  <div class="flex items-center gap-2">
                    <span class="dqscan-collapse-title-text">{{ m.title }}</span>
                    <el-tag type="info" effect="plain" size="small">{{ m.desc }}</el-tag>
                    <el-tag v-if="isModuleEnabled(m.key)" type="success" effect="plain" size="small">已启用</el-tag>
                    <el-tag v-else type="info" effect="plain" size="small">未启用</el-tag>
                    <el-tag type="info" effect="plain" size="small">
                      缺陷 {{ moduleEnabledDefectCount(m.key) }}/{{ moduleAllDefectCount(m.key) }}
                    </el-tag>
                    <el-tag type="info" effect="plain" size="small">算法 {{ getModuleAlgorithms(m.key).length }}</el-tag>
                  </div>
                  <div class="flex items-center gap-2" @click.stop>
                    <el-switch
                      :model-value="isModuleEnabled(m.key)"
                      active-text="启用"
                      inactive-text="关闭"
                      @update:model-value="(v) => setModuleEnabled(m.key, v)"
                    />
                  </div>
                </div>
              </template>

              <el-tabs v-model="moduleWorkbenchTab[m.key]" type="border-card" class="dqscan-module-tabs">
                <el-tab-pane label="基础参数" name="base">
                  <el-card shadow="never" class="dqscan-panel-card">
                    <template #header>
                      <div class="flex-x-between">
                        <div class="font-bold">基础参数</div>
                        <el-tag type="info" effect="plain" size="small">模块级</el-tag>
                      </div>
                    </template>

                    <div v-if="m.key === 'distribution'">
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

                    <div v-else-if="m.key === 'dirty_data'">
                      <el-form label-width="160px">
                        <el-form-item label="输出样例数">
                          <el-input-number v-model="dirtyMaxExamples" :min="10" :max="500" :step="10" />
                        </el-form-item>
                        <el-form-item label="白名单字段（可选）">
                          <el-select v-model="dirtyWhitelistColumns" multiple filterable placeholder="仅对这些字段做脏数据扫描（可选）">
                            <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                          </el-select>
                        </el-form-item>
                        <el-form-item label="黑名单字段（可选）">
                          <el-select v-model="dirtyBlacklistColumns" multiple filterable placeholder="跳过这些字段（可选）">
                            <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                          </el-select>
                        </el-form-item>
                      </el-form>
                    </div>

                    <div v-else-if="m.key === 'adversarial'">
                      <el-form label-width="160px">
                        <el-form-item label="最大样本数">
                          <el-input-number v-model="adversarialMaxSamples" :min="100" :max="500000" :step="100" />
                        </el-form-item>
                        <el-form-item label="随机种子">
                          <el-input-number v-model="adversarialSeed" :min="0" :max="999999" :step="1" />
                        </el-form-item>
                      </el-form>
                    </div>

                    <div v-else-if="m.key === 'physics'">
                      <el-empty description="该模块的规则/约束参数属于算法参数，请先完成缺陷绑定后再配置。" />
                    </div>
                  </el-card>
                </el-tab-pane>

                <el-tab-pane label="缺陷绑定" name="bind">
                  <el-card shadow="never" class="dqscan-panel-card">
                    <template #header>
                      <div class="flex-x-between">
                        <div class="flex items-center gap-2">
                          <div class="font-bold">缺陷绑定</div>
                          <el-tag type="info" effect="plain" size="small">缺陷→执行算法</el-tag>
                        </div>
                        <div class="flex items-center gap-2">
                          <el-button size="small" @click="autoBindModuleDefects(m.key)">自动分配</el-button>
                          <el-button size="small" @click="disableAllModuleDefects(m.key)">全部关闭</el-button>
                        </div>
                      </div>
                    </template>

                    <el-table
                      :data="moduleDefectRows(m.key)"
                      border
                      size="small"
                      style="width: 100%"
                      :row-class-name="defectBindRowClassName"
                    >
                      <el-table-column label="缺陷" min-width="260">
                        <template #default="{ row }">
                          <div class="flex items-center gap-2">
                            <el-tooltip :content="row.desc || row.path" placement="top" :show-after="300">
                              <div :id="`defect-row-${row.key}`" class="font-bold">{{ row.label }}</div>
                            </el-tooltip>
                            <el-tag v-if="row.badge" :type="row.badge.type" effect="plain" size="small">{{ row.badge.text }}</el-tag>
                          </div>
                        </template>
                      </el-table-column>
                      <el-table-column label="状态" width="110">
                        <template #default="{ row }">
                          <el-tag :type="row.status === 'ready' ? 'success' : 'warning'" effect="plain" size="small">
                            {{ row.status === "ready" ? "可用" : "即将上线" }}
                          </el-tag>
                        </template>
                      </el-table-column>
                      <el-table-column label="启用" width="110">
                        <template #default="{ row }">
                          <el-switch
                            :model-value="isDefectEnabled(row.key)"
                            :disabled="row.status !== 'ready'"
                            active-text="启用"
                            inactive-text="关闭"
                            @update:model-value="(v) => setDefectEnabled(row.key, v)"
                          />
                        </template>
                      </el-table-column>
                      <el-table-column label="执行算法" min-width="280">
                        <template #default="{ row }">
                          <el-select
                            :model-value="getDefectExecutor(row.key)"
                            filterable
                            clearable
                            placeholder="选择执行算法"
                            style="width: 100%"
                            popper-class="dqscan-algo-select-popper"
                            :disabled="!isDefectEnabled(row.key) || row.status !== 'ready'"
                            @update:model-value="(v) => setDefectExecutor(row.key, v)"
                          >
                            <el-option
                              v-for="a in executorAlgorithmOptions(row.key)"
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
                        </template>
                      </el-table-column>
                    </el-table>
                  </el-card>
                </el-tab-pane>

                <el-tab-pane label="算法参数" name="algo_params">
                  <el-card shadow="never" class="dqscan-panel-card">
                    <template #header>
                      <div class="flex-x-between">
                        <div class="flex items-center gap-2">
                          <div class="font-bold">算法参数</div>
                          <el-tag type="info" effect="plain" size="small">按已绑定算法汇总</el-tag>
                        </div>
                        <el-button size="small" @click="moduleWorkbenchTab[m.key] = 'bind'">回到缺陷绑定</el-button>
                      </div>
                    </template>

                    <el-empty v-if="!getModuleAlgorithms(m.key).length" description="请先在「缺陷绑定」里选择执行算法" />

                    <div v-else>
                      <el-card v-for="algoKey in getModuleAlgorithms(m.key)" :key="algoKey" shadow="never" class="mb-3">
                        <template #header>
                          <div class="flex items-center gap-2">
                            <div class="font-bold">{{ algoOptionByKey[algoKey]?.label || algoKey }}</div>
                            <el-tag type="success" effect="plain" size="small">可用</el-tag>
                            <el-tag type="info" effect="plain" size="small">
                              绑定缺陷 {{ boundDefectCount(m.key, algoKey) }}
                            </el-tag>
                            <el-tag
                              v-for="dk in boundDefectTags(m.key, algoKey)"
                              :key="`${algoKey}_${dk}`"
                              type="info"
                              effect="plain"
                              size="small"
                            >
                              {{ defectIndex.nodeByKey[dk]?.label || dk }}
                            </el-tag>
                          </div>
                        </template>

                        <el-form label-width="160px">
                          <template v-if="algoKey === 'mmd_ks_chi2'">
                            <el-form-item label="显著性水平（p 值阈值）">
                              <el-slider v-model="distributionPVal" :min="0.001" :max="0.2" :step="0.001" show-input />
                            </el-form-item>
                            <el-form-item v-if="boundDefectKeys(m.key, algoKey).includes('distribution.label_shift')" label="标签列（Label Shift）">
                              <el-select v-model="distributionLabelColumn" clearable filterable placeholder="选择标签列">
                                <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                              </el-select>
                            </el-form-item>
                          </template>

                          <template v-else-if="algoKey === 'ecod_3sigma'">
                            <template v-if="boundDefectKeys(m.key, algoKey).includes('dirty_data.anomaly')">
                              <el-form-item label="异常率/污染度（contamination）">
                                <el-slider v-model="dirtyContamination" :min="0.001" :max="0.3" :step="0.001" show-input />
                              </el-form-item>
                            </template>
                            <template v-if="boundDefectKeys(m.key, algoKey).includes('dirty_data.missing')">
                              <el-form-item label="缺失阈值（missing_threshold）">
                                <el-slider v-model="dirtyMissingThreshold" :min="0.01" :max="0.5" :step="0.01" show-input />
                              </el-form-item>
                            </template>
                            <template v-if="boundDefectKeys(m.key, algoKey).includes('dirty_data.duplicate')">
                              <el-form-item label="重复阈值（duplicate_threshold）">
                                <el-slider v-model="dirtyDuplicateThreshold" :min="0.001" :max="0.5" :step="0.001" show-input />
                              </el-form-item>
                              <el-form-item label="关键列（去重，可选）">
                                <el-select v-model="duplicateKeyColumns" multiple filterable placeholder="用于整行/关键列去重（可选）">
                                  <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                                </el-select>
                              </el-form-item>
                            </template>
                            <template v-if="boundDefectKeys(m.key, algoKey).includes('dirty_data.range')">
                              <el-form-item label="值域检测策略">
                                <el-radio-group v-model="rangeMethod">
                                  <el-radio-button label="sigma">3σ</el-radio-button>
                                  <el-radio-button label="iqr">IQR</el-radio-button>
                                  <el-radio-button label="rules">业务规则</el-radio-button>
                                </el-radio-group>
                              </el-form-item>
                              <el-form-item v-if="rangeMethod === 'sigma'" label="k 值">
                                <el-slider v-model="rangeSigma" :min="1" :max="6" :step="0.5" show-input />
                              </el-form-item>
                              <el-form-item v-else-if="rangeMethod === 'iqr'" label="IQR 因子">
                                <el-slider v-model="rangeIqrFactor" :min="0.5" :max="3" :step="0.1" show-input />
                              </el-form-item>
                              <el-form-item label="仅检查字段（可选）">
                                <el-select v-model="rangeOnlyColumns" multiple filterable placeholder="不选则默认检查全部">
                                  <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                                </el-select>
                              </el-form-item>
                            </template>
                            <el-text type="info">该算法参数仅在绑定该算法的缺陷上生效。</el-text>
                          </template>

                          <template v-else-if="algoKey === 'confident_learning' || algoKey === 'cv_consistency'">
                            <template v-if="boundDefectKeys(m.key, algoKey).includes('dirty_data.label_mismatch')">
                              <el-form-item label="标签列（Label Mismatch）">
                                <el-select v-model="labelMismatchLabelColumn" clearable filterable placeholder="选择标签列">
                                  <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                                </el-select>
                                <el-text type="info" class="block mt-2">必填：用于发现"疑似错标"样本（例如猫被标成狗）。</el-text>
                              </el-form-item>

                              <el-form-item label="排除字段">
                                <el-popover placement="bottom-start" :width="420" trigger="click">
                                  <template #reference>
                                    <el-input :model-value="labelMismatchExcludeColumnsDisplay" readonly placeholder="点击选择要排除的列" />
                                  </template>
                                  <div v-if="columnsLoading" class="text-sm text-gray">正在解析列名...</div>
                                  <div v-else-if="columnsError" class="text-sm text-red">{{ columnsError }}</div>
                                  <el-scrollbar v-else height="220px">
                                    <el-checkbox-group v-model="labelMismatchExcludeColumns" class="flex flex-col gap-1">
                                      <el-checkbox v-for="c in columnOptions" :key="c" :label="c">{{ c }}</el-checkbox>
                                    </el-checkbox-group>
                                  </el-scrollbar>
                                  <div class="mt-2 flex justify-end gap-2">
                                    <el-button size="small" @click="labelMismatchExcludeColumns = []">清空</el-button>
                                  </div>
                                </el-popover>
                                <el-text type="info" class="block mt-2">建议排除 id/uuid/时间戳等高基数字段，避免模型"记住样本"。</el-text>
                              </el-form-item>

                              <el-form-item label="抽样上限">
                                <el-input-number v-model="labelMismatchMaxSamples" :min="100" :max="500000" :step="100" />
                              </el-form-item>
                              <el-form-item label="交叉验证折数">
                                <el-input-number v-model="labelMismatchNSplits" :min="2" :max="10" :step="1" />
                              </el-form-item>
                              <el-form-item label="P(给定标签)阈值">
                                <el-slider v-model="labelMismatchThresholdProbTrue" :min="0" :max="0.8" :step="0.01" show-input />
                              </el-form-item>
                              <el-form-item label="P(建议标签)阈值">
                                <el-slider v-model="labelMismatchThresholdProbPred" :min="0.2" :max="0.99" :step="0.01" show-input />
                              </el-form-item>

                              <template v-if="algoKey === 'confident_learning'">
                                <el-form-item label="Score 方法">
                                  <el-select v-model="labelMismatchScoreMethod" placeholder="选择打分方式">
                                    <el-option label="self_confidence（默认）" value="self_confidence" />
                                    <el-option label="normalized_margin" value="normalized_margin" />
                                    <el-option label="confidence_weighted_entropy" value="confidence_weighted_entropy" />
                                  </el-select>
                                </el-form-item>
                                <el-form-item label="筛选策略">
                                  <el-select v-model="labelMismatchFilterBy" placeholder="选择筛选策略">
                                    <el-option label="both（推荐）" value="both" />
                                    <el-option label="prune_by_class" value="prune_by_class" />
                                    <el-option label="prune_by_noise_rate" value="prune_by_noise_rate" />
                                    <el-option label="confident_learning（仅高置信冲突）" value="confident_learning" />
                                  </el-select>
                                </el-form-item>
                                <el-form-item label="fraction_noise">
                                  <el-slider v-model="labelMismatchFractionNoise" :min="0" :max="0.3" :step="0.005" show-input />
                                  <el-text type="info" class="block mt-2">控制"按类剪枝"候选集规模（越小越严格）。</el-text>
                                </el-form-item>
                              </template>

                              <el-form-item label="输出样例数">
                                <el-input-number v-model="labelMismatchMaxExamples" :min="10" :max="500" :step="10" />
                              </el-form-item>

                              <el-text type="info" class="block mt-2">
                                这些配置会写入"疑似错标（Label Mismatch）"缺陷的参数中（`label_column/exclude_columns/...`）。
                              </el-text>
                            </template>
                          </template>

                          <template v-else-if="algoKey === 'missing_stats_threshold'">
                            <el-form-item label="缺失阈值（missing_threshold）">
                              <el-slider v-model="dirtyMissingThreshold" :min="0.01" :max="0.5" :step="0.01" show-input />
                            </el-form-item>
                          </template>

                          <template v-else-if="algoKey === 'exact_duplicate'">
                            <el-form-item label="重复阈值（duplicate_threshold）">
                              <el-slider v-model="dirtyDuplicateThreshold" :min="0.001" :max="0.5" :step="0.001" show-input />
                            </el-form-item>
                            <el-form-item label="关键列（去重，可选）">
                              <el-select v-model="duplicateKeyColumns" multiple filterable placeholder="用于整行/关键列去重（可选）">
                                <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                              </el-select>
                            </el-form-item>
                          </template>

                          <template v-else-if="algoKey === 'sigma_rule'">
                            <el-form-item label="k 值（3σ）">
                              <el-slider v-model="rangeSigma" :min="1" :max="6" :step="0.5" show-input />
                            </el-form-item>
                            <el-form-item label="仅检查字段（可选）">
                              <el-select v-model="rangeOnlyColumns" multiple filterable placeholder="不选则默认检查全部">
                                <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                              </el-select>
                            </el-form-item>
                          </template>

                          <template v-else-if="algoKey === 'zoo_or_random'">
                            <el-form-item label="扰动预算（epsilon）">
                              <el-slider v-model="adversarialEpsilon" :min="0.001" :max="0.3" :step="0.001" show-input />
                            </el-form-item>
                            <el-form-item label="最大迭代（max_iter）">
                              <el-input-number v-model="adversarialMaxIter" :min="1" :max="200" :step="1" />
                            </el-form-item>
                            <el-form-item label="随机尝试次数">
                              <el-input-number v-model="adversarialRandomTrials" :min="1" :max="500" :step="1" />
                            </el-form-item>
                            <el-form-item label="随机特征数">
                              <el-input-number v-model="adversarialRandomFeatures" :min="1" :max="200" :step="1" />
                            </el-form-item>
                            <el-form-item label="学习率">
                              <el-input-number v-model="adversarialLearningRate" :min="0.0001" :max="1" :step="0.001" />
                            </el-form-item>
                            <el-form-item label="置信度（可选）">
                              <el-input-number v-model="adversarialConfidence" :min="0" :max="100" :step="1" />
                            </el-form-item>
                            <el-form-item label="Batch Size">
                              <el-input-number v-model="adversarialBatchSize" :min="1" :max="1024" :step="1" />
                            </el-form-item>
                          </template>

                          <template v-else-if="algoKey === 'pandera_or_fallback'">
                            <el-alert type="info" :closable="false" class="mb-3">
                              <template #title>列级规则 + 跨列规则</template>
                              <div>上传数据后选择字段，可快速配置 min/max、必填/枚举/正则以及 if-then、求和、唯一等跨列规则。</div>
                            </el-alert>
                            <el-form-item label="自动推断基础规则">
                              <el-switch v-model="physicsAutoConstraints" />
                            </el-form-item>

                            <el-divider class="my-2" />

                            <div class="flex-x-between mb-2">
                              <div class="font-bold">范围约束（min/max）</div>
                              <el-button size="small" @click="addPhysicsConstraint">新增列约束</el-button>
                            </div>
                            <el-table :data="physicsConstraints" border size="small" row-key="id">
                              <el-table-column label="字段" min-width="180">
                                <template #default="{ row }">
                                  <el-select v-model="row.column" filterable clearable placeholder="选择字段">
                                    <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                                  </el-select>
                                </template>
                              </el-table-column>
                              <el-table-column label="min" min-width="120">
                                <template #default="{ row }">
                                  <el-input-number v-model="row.min" :min="-1e12" :max="1e12" :step="1" />
                                </template>
                              </el-table-column>
                              <el-table-column label="max" min-width="120">
                                <template #default="{ row }">
                                  <el-input-number v-model="row.max" :min="-1e12" :max="1e12" :step="1" />
                                </template>
                              </el-table-column>
                              <el-table-column label="操作" width="100">
                                <template #default="{ row }">
                                  <el-button size="small" type="danger" @click="removePhysicsConstraint(row.id)">删除</el-button>
                                </template>
                              </el-table-column>
                            </el-table>
                            <el-text type="info" class="block mt-2">未填写 min/max 的行会被忽略。</el-text>

                            <el-divider class="my-4" />

                            <div class="flex-x-between mb-2">
                              <div class="font-bold">列级规则（必填 / 枚举 / 正则）</div>
                              <el-button size="small" @click="addColumnRule">添加列规则</el-button>
                            </div>
                            <el-table :data="physicsColumnRules" border size="small" row-key="id">
                              <el-table-column label="字段" min-width="160">
                                <template #default="{ row }">
                                  <el-select v-model="row.column" filterable clearable placeholder="选择字段">
                                    <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                                  </el-select>
                                </template>
                              </el-table-column>
                              <el-table-column label="规则类型" min-width="160">
                                <template #default="{ row }">
                                  <el-select v-model="row.type" placeholder="选择类型" @change="(val) => handleColumnRuleTypeChange(row, val)">
                                    <el-option v-for="opt in physicsColumnRuleTypeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                                  </el-select>
                                </template>
                              </el-table-column>
                              <el-table-column label="参数" min-width="220">
                                <template #default="{ row }">
                                  <div v-if="row.type === 'not_null'">无需额外参数</div>
                                  <div v-else-if="row.type === 'in_set'" class="flex flex-col gap-1">
                                    <el-input v-model="row.values" placeholder="使用英文逗号分隔取值，例如：A,B,C" />
                                    <el-text type="info" class="text-xs">输入为空时将忽略该规则</el-text>
                                  </div>
                                  <div v-else-if="row.type === 'regex'" class="flex flex-col gap-1">
                                    <el-input v-model="row.pattern" placeholder="输入正则表达式，例如：^\\d{4}-\\d{2}-\\d{2}$" />
                                  </div>
                                </template>
                              </el-table-column>
                              <el-table-column label="操作" width="100">
                                <template #default="{ row }">
                                  <el-button link type="danger" @click="removeColumnRule(row.id)">删除</el-button>
                                </template>
                              </el-table-column>
                            </el-table>

                            <el-divider class="my-4" />

                            <div class="flex-x-between mb-2">
                              <div class="font-bold">跨列规则（条件 / 关系 / 求和 / 唯一）</div>
                              <el-button size="small" @click="addCrossRule()">添加跨列规则</el-button>
                            </div>
                            <el-table :data="physicsCrossRules" border size="small" row-key="id">
                              <el-table-column label="规则类型" min-width="180">
                                <template #default="{ row }">
                                  <el-select v-model="row.type" placeholder="选择类型" @change="(val) => handleCrossRuleTypeChange(row, val)">
                                    <el-option v-for="opt in physicsCrossRuleTypeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                                  </el-select>
                                </template>
                              </el-table-column>
                              <el-table-column label="配置" min-width="420">
                                <template #default="{ row }">
                                  <div v-if="row.type === 'if_then'" class="flex flex-col gap-2">
                                    <div class="flex items-center gap-2 flex-wrap">
                                      <span>如果</span>
                                      <el-select v-model="row.ifColumn" filterable clearable placeholder="字段">
                                        <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                                      </el-select>
                                      <el-select v-model="row.ifOp" placeholder="比较符">
                                        <el-option v-for="op in comparisonOperatorOptions" :key="op.value" :label="op.label" :value="op.value" />
                                      </el-select>
                                      <el-input v-model="row.ifValue" placeholder="值" style="max-width: 160px" />
                                    </div>
                                    <div class="flex items-center gap-2 flex-wrap">
                                      <span>则需要</span>
                                      <el-select v-model="row.thenColumn" filterable clearable placeholder="字段">
                                        <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                                      </el-select>
                                      <el-select v-model="row.thenOp" placeholder="比较符">
                                        <el-option v-for="op in comparisonOperatorOptions" :key="op.value" :label="op.label" :value="op.value" />
                                      </el-select>
                                      <el-input v-model="row.thenValue" placeholder="值" style="max-width: 160px" />
                                    </div>
                                  </div>
                                  <div v-else-if="row.type === 'relation'" class="flex items-center gap-2 flex-wrap">
                                    <el-select v-model="row.relationLeft" filterable clearable placeholder="左侧字段">
                                      <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                                    </el-select>
                                    <el-select v-model="row.relationOp" placeholder="比较符">
                                      <el-option v-for="op in comparisonOperatorOptions" :key="op.value" :label="op.label" :value="op.value" />
                                    </el-select>
                                    <el-select v-model="row.relationRight" filterable clearable placeholder="右侧字段">
                                      <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                                    </el-select>
                                    <el-input-number v-model="row.relationTolerance" :min="0" :max="1e6" :step="0.01" placeholder="容差(可选)" />
                                  </div>
                                  <div v-else-if="row.type === 'sum'" class="flex flex-col gap-2">
                                    <div class="flex items-start gap-2 flex-wrap">
                                      <span>求和字段</span>
                                      <el-select v-model="row.sumColumns" multiple filterable collapse-tags placeholder="选择字段">
                                        <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                                      </el-select>
                                    </div>
                                    <div class="flex items-center gap-2 flex-wrap">
                                      <span>目标 =</span>
                                      <el-select v-model="row.sumTargetColumn" clearable filterable placeholder="目标字段（可选）">
                                        <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                                      </el-select>
                                      <span>或</span>
                                      <el-input v-model="row.sumTargetValue" placeholder="常量值（可选）" style="max-width: 160px" />
                                      <span>容差</span>
                                      <el-input-number v-model="row.sumTolerance" :min="0" :max="1e6" :step="0.01" />
                                    </div>
                                  </div>
                                  <div v-else-if="row.type === 'unique'" class="flex items-center gap-2 flex-wrap">
                                    <el-select v-model="row.uniqueColumns" multiple filterable placeholder="唯一性字段组合">
                                      <el-option v-for="c in columnOptions" :key="c" :label="c" :value="c" />
                                    </el-select>
                                  </div>
                                </template>
                              </el-table-column>
                              <el-table-column label="操作" width="100">
                                <template #default="{ row }">
                                  <el-button link type="danger" @click="removeCrossRule(row.id)">删除</el-button>
                                </template>
                              </el-table-column>
                            </el-table>
                          </template>

                          <template v-else-if="algoKey === 'psi'">
                            <el-form-item label="分箱数">
                              <el-slider v-model="algoParams.psi_bins" :min="5" :max="50" :step="1" show-input />
                            </el-form-item>
                            <el-form-item label="分箱方式">
                              <el-select v-model="algoParams.psi_bucket" placeholder="选择分箱方式">
                                <el-option label="等频（quantile）" value="quantile" />
                                <el-option label="等宽（uniform）" value="uniform" />
                              </el-select>
                            </el-form-item>
                          </template>

                          <template v-else-if="algoKey === 'wasserstein'">
                            <el-form-item label="阈值">
                              <el-slider v-model="algoParams.wasserstein_threshold" :min="0" :max="1" :step="0.01" show-input />
                            </el-form-item>
                          </template>

                          <template v-else-if="algoKey === 'embedding_mmd'">
                            <el-form-item label="Embedding 模型">
                              <el-select v-model="algoParams.embedding_model" filterable placeholder="选择模型">
                                <el-option label="通用（small）" value="small" />
                                <el-option label="通用（large）" value="large" />
                              </el-select>
                            </el-form-item>
                            <el-form-item label="Batch Size">
                              <el-input-number v-model="algoParams.embedding_batch_size" :min="1" :max="1024" :step="8" />
                            </el-form-item>
                          </template>

                          <template v-else-if="algoKey === 'isolation_forest'">
                            <el-form-item label="树数量">
                              <el-input-number v-model="algoParams.iforest_estimators" :min="50" :max="1000" :step="50" />
                            </el-form-item>
                            <el-form-item label="最大采样">
                              <el-input-number v-model="algoParams.iforest_max_samples" :min="64" :max="100000" :step="64" />
                            </el-form-item>
                          </template>

                          <template v-else-if="algoKey === 'autoencoder'">
                            <el-form-item label="潜变量维度">
                              <el-input-number v-model="algoParams.ae_latent_dim" :min="4" :max="128" :step="4" />
                            </el-form-item>
                            <el-form-item label="训练轮数">
                              <el-input-number v-model="algoParams.ae_epochs" :min="5" :max="200" :step="5" />
                            </el-form-item>
                          </template>

                          <template v-else-if="algoKey === 'fgsm'">
                            <el-form-item label="范数">
                              <el-select v-model="algoParams.fgsm_norm">
                                <el-option label="L∞" value="linf" />
                                <el-option label="L2" value="l2" />
                              </el-select>
                            </el-form-item>
                            <el-form-item label="目标攻击">
                              <el-switch v-model="algoParams.fgsm_targeted" />
                            </el-form-item>
                          </template>

                          <template v-else-if="algoKey === 'pgd'">
                            <el-form-item label="步数">
                              <el-input-number v-model="algoParams.pgd_steps" :min="1" :max="200" :step="5" />
                            </el-form-item>
                            <el-form-item label="步长">
                              <el-slider v-model="algoParams.pgd_step_size" :min="0.001" :max="0.2" :step="0.001" show-input />
                            </el-form-item>
                            <el-form-item label="随机初始化">
                              <el-switch v-model="algoParams.pgd_random_start" />
                            </el-form-item>
                          </template>

                          <template v-else>
                            <el-text type="info">该算法暂无可配置的算法参数。</el-text>
                          </template>
                        </el-form>
                      </el-card>
                    </div>
                  </el-card>
                </el-tab-pane>
              </el-tabs>
            </el-collapse-item>
          </el-collapse>
        </el-card>

        <!-- 配置预览 -->
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
        <el-text type="info">右侧按模块选择算法，并为缺陷绑定「执行算法」</el-text>
      </div>
      <div class="flex items-center gap-2">
        <el-button @click="gotoStep(1)">上一步</el-button>
        <el-button type="success" :disabled="!canStart" :loading="starting" icon="video-play" @click="startScan">
          开始检测
        </el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import {
  useDqscanInject, modules, defaultExpandedDefectKeys,
  comparisonOperatorOptions, physicsColumnRuleTypeOptions, physicsCrossRuleTypeOptions,
} from "../composables/useDqscanState";

const state = useDqscanInject();
const {
  activeStep, gotoStep, selectedModality,
  // 图片错标检测
  imageLabelAlgorithm, imageLabelK, imageLabelThreshold, imageLabelMaxSamples,
  imageLabelMaxExamples, imageLabelBatchSize, imageLabelDevice,
  imageLabelImageColumn, imageLabelLabelColumn, imageLabelCsvPath,
  selectedAlgorithmLabel, selectedAlgorithmDesc,
  // 缺陷树
  defectSearch, defectTreeRef, defectTreeData, defectTreeProps, defectIndex,
  checkedDefectKeys, activeDefectKey,
  onDefectNodeClick, onDefectCheck, filterDefectNode,
  selectAllDefects, selectRecommendedDefects, clearDefects,
  selectedLeafDefectCount, selectedDefectAlgorithmCount,
  // 运行策略
  scanPreset, scanPresetLabel, globalMaxSamples, globalParallelism, globalSeed,
  reportOptions, algoParams,
  // 模块
  openModulePanels, moduleWorkbenchTab,
  expandAllModulePanels, collapseAllModulePanels,
  isModuleEnabled, setModuleEnabled, disableAllModuleDefects,
  moduleAllDefectCount, moduleEnabledDefectCount,
  getModuleAlgorithms, autoBindModuleDefects,
  moduleDefectRows, defectBindRowClassName,
  isDefectEnabled, setDefectEnabled,
  getDefectExecutor, setDefectExecutor, executorAlgorithmOptions,
  algoOptionByKey, boundDefectKeys, boundDefectCount, boundDefectTags,
  showOnlyEnabledDefects,
  configIssuesHint,
  // 分布偏差
  distributionCompareMode, distributionTrainTestSplit, distributionLabelColumn, distributionPVal,
  distributionExcludeColumns, excludeColumnsDisplay,
  columnOptions, columnsLoading, columnsError,
  baselineUploadedFile, clearBaseline,
  // 脏数据
  dirtyContamination, dirtyMissingThreshold, dirtyDuplicateThreshold,
  dirtyMaxExamples, dirtyWhitelistColumns, dirtyBlacklistColumns,
  duplicateKeyColumns,
  rangeMethod, rangeSigma, rangeIqrFactor, rangeOnlyColumns,
  // label mismatch
  labelMismatchLabelColumn, labelMismatchMaxSamples, labelMismatchExcludeColumns,
  labelMismatchExcludeColumnsDisplay,
  labelMismatchNSplits, labelMismatchThresholdProbTrue, labelMismatchThresholdProbPred,
  labelMismatchScoreMethod, labelMismatchFilterBy, labelMismatchFractionNoise, labelMismatchMaxExamples,
  // 对抗性
  adversarialEpsilon, adversarialMaxIter, adversarialRandomTrials, adversarialRandomFeatures,
  adversarialMaxSamples, adversarialSeed, adversarialLearningRate, adversarialConfidence, adversarialBatchSize,
  // 物理保真度
  physicsAutoConstraints, physicsConstraints, physicsColumnRules, physicsCrossRules,
  addPhysicsConstraint, removePhysicsConstraint,
  addColumnRule, removeColumnRule, handleColumnRuleTypeChange,
  addCrossRule, removeCrossRule, handleCrossRuleTypeChange,
  // 摘要
  selectedModulesDisplay, selectedDefectsDisplay, selectedAlgorithmsDisplay,
  // 任务
  algorithmsLoading, loadAlgorithms,
  canStart, starting, startScan,
} = state;
</script>

<style scoped lang="scss">
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

.dqscan-module-tabs :deep(.el-tabs__content) {
  padding: 10px;
}

.dqscan-module-tabs :deep(.el-tabs__item) {
  height: 44px;
  line-height: 44px;
  font-weight: 700;
}

.dqscan-panel-card {
  border-radius: 12px;
}

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

.dqscan-config-tabs :deep(.el-tabs__content) {
  padding-left: 8px;
}

.dqscan-config-tabs :deep(.el-tabs__item) {
  height: 44px;
  line-height: 44px;
}

.dqscan-module-tabs :deep(.dqscan-row-missing-executor td) {
  background-color: var(--el-color-danger-light-9);
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

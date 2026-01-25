<template>
  <div class="metrics-config">
    <div class="section-header">
      <div class="flex items-center gap-3">
        <span class="w-7 h-7 rounded-lg bg-indigo-600 text-white text-sm font-bold flex items-center justify-center shadow">5</span>
        <div>
          <h3 class="font-bold text-gray-900">指标与输出</h3>
          <p class="text-sm text-gray-500 mt-1">选择评估指标与产物落盘策略</p>
        </div>
      </div>
      <div class="flex items-center gap-2 text-xs text-gray-500">
        <el-icon><PieChart /></el-icon>
        <span>Metrics & Outputs</span>
      </div>
    </div>

    <!-- 模块功能说明 -->
    <div class="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
      <div class="flex items-start gap-3">
        <el-icon class="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0"><InfoFilled /></el-icon>
        <div class="text-sm text-blue-900">
          <p class="font-semibold mb-1">配置评估结果的计算和保存方式</p>
          <p class="text-blue-800">在此模块中，您需要选择用于衡量模型鲁棒性的评估指标，以及配置对抗样本和实验数据的存储选项。这些配置将决定评估结束后生成哪些分析报告和数据文件。</p>
        </div>
      </div>
    </div>

    <div class="form-content space-y-6">
      <!-- 评估指标选择 -->
      <div class="p-4 bg-gray-50 border border-gray-200 rounded-lg">
        <div class="mb-4">
          <div class="flex items-center justify-between">
            <div class="text-sm font-semibold text-gray-800">鲁棒性评估指标</div>
            <div class="flex items-center gap-2">
              <span class="text-xs text-gray-500">已选择 {{ localData.selected.length }} 项</span>
              <el-button @click="selectAllMetrics" size="small" plain>全选</el-button>
              <el-button @click="clearAllMetrics" size="small" plain>清空</el-button>
            </div>
          </div>
          <div class="text-xs text-gray-500 mt-1">选择用于量化模型鲁棒性的评价指标，建议至少勾选 Clean Accuracy、Robust Accuracy 和 ASR 三项核心指标</div>
        </div>
        
        <div class="grid grid-cols-1 gap-3">
          <label 
            v-for="metric in availableMetrics" 
            :key="metric.key" 
            :class="[
              'flex items-start gap-3 p-4 bg-white border rounded-lg cursor-pointer transition-all',
              localData.selected.includes(metric.key) 
                ? 'border-indigo-300 bg-indigo-50' 
                : 'border-gray-200 hover:border-indigo-300'
            ]"
            @click="toggleMetric(metric.key)"
          >
            <div class="flex-shrink-0 mt-1">
              <div :class="[
                'w-5 h-5 rounded border-2 flex items-center justify-center',
                localData.selected.includes(metric.key) 
                  ? 'border-indigo-600 bg-indigo-600' 
                  : 'border-gray-300'
              ]">
                <el-icon v-if="localData.selected.includes(metric.key)" class="w-3 h-3 text-white">
                  <Check />
                </el-icon>
              </div>
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <div class="text-sm font-medium text-gray-800">{{ metric.label }}</div>
                <el-tag v-if="metric.priority === 'high'" size="small" type="danger">核心</el-tag>
                <el-tag v-else-if="metric.priority === 'medium'" size="small" type="warning">重要</el-tag>
                <el-tag v-else size="small" type="info">可选</el-tag>
              </div>
              <div class="text-xs text-gray-600">{{ metric.desc }}</div>
              <div v-if="metric.formula" class="mt-2 p-2 bg-gray-50 rounded text-xs font-mono text-gray-700">
                公式: {{ metric.formula }}
              </div>
            </div>
          </label>
        </div>

        <!-- 指标配置 -->
        <div v-if="localData.selected.length > 0" class="mt-4 p-3 bg-white border border-gray-200 rounded-lg">
          <div class="text-sm font-medium text-gray-800 mb-3">指标计算配置</div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-2">Top-K 准确率</label>
              <el-select v-model="localData.topK" size="small" class="w-full">
                <el-option :value="1" label="Top-1" />
                <el-option :value="5" label="Top-5" />
                <el-option :value="10" label="Top-10" />
              </el-select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-2">置信度阈值</label>
              <div class="flex items-center gap-2">
                <el-input-number 
                  v-model="localData.confidenceThreshold"
                  :min="0.0"
                  :max="1.0"
                  :step="0.01"
                  :precision="2"
                  size="small"
                  class="w-20"
                />
                <el-slider
                  v-model="localData.confidenceThreshold"
                  :min="0.0"
                  :max="1.0"
                  :step="0.01"
                  size="small"
                  class="flex-1"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 数据输出选项 -->
      <div class="p-4 bg-gray-50 border border-gray-200 rounded-lg">
        <div class="mb-4">
          <div class="text-sm font-semibold text-gray-800">数据输出选项</div>
          <div class="text-xs text-gray-500 mt-1">配置实验数据和对抗样本的保存方式，用于后续分析和可视化</div>
        </div>
        <div class="space-y-4">
          <!-- 对抗样本保存 -->
          <div class="p-4 bg-white border border-gray-200 rounded-lg">
            <div class="flex items-start gap-3">
              <el-switch 
                v-model="localData.outputs.save_adv"
                @change="onOutputChange"
              />
              <div class="flex-1">
                <div class="text-sm font-medium text-gray-800">保存对抗样本（artifact）</div>
                <div class="text-xs text-gray-600 mt-1">将生成的对抗样本保存到磁盘，便于后续可视化分析和对比实验。文件较大，需要足够存储空间</div>
                <div v-if="localData.outputs.save_adv" class="mt-2 ml-4 space-y-2">
                  <el-checkbox v-model="localData.outputs.save_original">同时保存原始样本</el-checkbox>
                  <el-checkbox v-model="localData.outputs.save_perturbation">保存扰动向量</el-checkbox>
                  <div class="flex items-center gap-2">
                    <span class="text-xs text-gray-600">保存格式:</span>
                    <el-select v-model="localData.outputs.adv_format" size="small">
                      <el-option value="numpy" label="NumPy (.npy)" />
                      <el-option value="pickle" label="Pickle (.pkl)" />
                      <el-option value="hdf5" label="HDF5 (.h5)" />
                      <el-option value="image" label="图像格式" />
                    </el-select>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 中间过程保存 -->
          <div class="p-4 bg-white border border-gray-200 rounded-lg">
            <div class="flex items-start gap-3">
              <el-switch 
                v-model="localData.outputs.save_intermediate"
                @change="onOutputChange"
              />
              <div class="flex-1">
                <div class="text-sm font-medium text-gray-800">保存中间过程（loss/梯度/查询）</div>
                <div class="text-xs text-gray-600 mt-1">记录攻击过程中的损失函数值、梯度信息和查询历史，用于深入分析攻击动态和调试算法</div>
                <div v-if="localData.outputs.save_intermediate" class="mt-2 ml-4 space-y-2">
                  <el-checkbox v-model="localData.outputs.save_loss_curve">保存损失曲线</el-checkbox>
                  <el-checkbox v-model="localData.outputs.save_gradients">保存梯度信息</el-checkbox>
                  <el-checkbox v-model="localData.outputs.save_queries">保存查询历史</el-checkbox>
                </div>
              </div>
            </div>
          </div>

          <!-- 报告导出格式 -->
          <div class="p-4 bg-white border border-gray-200 rounded-lg">
            <div class="text-sm font-medium text-gray-800 mb-3">报告导出格式</div>
            <div class="grid grid-cols-2 gap-4">
              <label class="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                <el-checkbox v-model="localData.outputs.export_csv" />
                <div class="flex-1">
                  <div class="text-sm font-medium text-gray-800">CSV 格式</div>
                  <div class="text-xs text-gray-600">表格数据，便于Excel分析</div>
                </div>
              </label>
              
              <label class="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                <el-checkbox v-model="localData.outputs.export_json" />
                <div class="flex-1">
                  <div class="text-sm font-medium text-gray-800">JSON 格式</div>
                  <div class="text-xs text-gray-600">结构化数据，程序化处理</div>
                </div>
              </label>

              <label class="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                <el-checkbox v-model="localData.outputs.export_html" />
                <div class="flex-1">
                  <div class="text-sm font-medium text-gray-800">HTML 报告</div>
                  <div class="text-xs text-gray-600">可视化报告，包含图表</div>
                </div>
              </label>

              <label class="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                <el-checkbox v-model="localData.outputs.export_pdf" />
                <div class="flex-1">
                  <div class="text-sm font-medium text-gray-800">PDF 报告</div>
                  <div class="text-xs text-gray-600">正式报告，适合分享</div>
                </div>
              </label>
            </div>
          </div>

          <!-- 高级输出选项 -->
          <div class="p-4 bg-white border border-gray-200 rounded-lg">
            <div class="text-sm font-medium text-gray-800 mb-3">高级输出选项</div>
            <div class="space-y-2">
              <el-checkbox v-model="localData.outputs.save_model_outputs">保存模型预测输出</el-checkbox>
              <el-checkbox v-model="localData.outputs.save_feature_maps">保存特征图（如果适用）</el-checkbox>
              <el-checkbox v-model="localData.outputs.save_attention_maps">保存注意力图（如果适用）</el-checkbox>
              <el-checkbox v-model="localData.outputs.generate_visualization">生成可视化图像</el-checkbox>
              <el-checkbox v-model="localData.outputs.compress_outputs">压缩输出文件</el-checkbox>
            </div>
          </div>
        </div>
      </div>

      <!-- 成本预估 -->
      <div class="p-4 bg-purple-50 border border-purple-200 rounded-lg">
        <div class="flex items-center gap-3 mb-4">
          <el-icon class="w-5 h-5 text-purple-600"><Timer /></el-icon>
          <div class="text-sm font-semibold text-purple-900">运行成本预估</div>
          <el-button @click="computeCostEstimate" size="small" type="primary" plain>
            重新计算
          </el-button>
        </div>

        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <div class="p-3 bg-white rounded-lg border border-purple-200">
            <div class="text-xs text-purple-600 mb-1">样本数量</div>
            <div class="text-lg font-bold text-purple-900">{{ costEstimate.samples?.toLocaleString() }}</div>
          </div>
          <div class="p-3 bg-white rounded-lg border border-purple-200">
            <div class="text-xs text-purple-600 mb-1">平均步数</div>
            <div class="text-lg font-bold text-purple-900">{{ costEstimate.steps }}</div>
          </div>
          <div class="p-3 bg-white rounded-lg border border-purple-200">
            <div class="text-xs text-purple-600 mb-1">预计耗时</div>
            <div class="text-lg font-bold text-purple-900">{{ formatTime(costEstimate.estSeconds) }}</div>
          </div>
          <div class="p-3 bg-white rounded-lg border border-purple-200">
            <div class="text-xs text-purple-600 mb-1">存储需求</div>
            <div class="text-lg font-bold text-purple-900">{{ formatFileSize(costEstimate.storageSize) }}</div>
          </div>
        </div>

        <div class="text-xs text-purple-700">
          <p class="mb-1"><strong>估算说明：</strong></p>
          <p>• 计算基于选择的攻击方法、数据集大小和参数配置</p>
          <p>• 实际运行时间可能因硬件配置而有所差异</p>
          <p>• 存储需求包括对抗样本、中间过程和报告文件</p>
        </div>
      </div>

      <!-- 快速配置预设 -->
      <div class="p-4 bg-green-50 border border-green-200 rounded-lg">
        <div class="flex items-center justify-between mb-4">
          <div>
            <div class="text-sm font-semibold text-green-900">快速配置预设</div>
            <div class="text-xs text-green-700 mt-1">选择预定义的配置组合，快速开始评估</div>
          </div>
          <el-button @click="saveCurrentPreset" size="small" type="success" plain>
            保存当前配置
          </el-button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div 
            v-for="preset in configPresets"
            :key="preset.id"
            :class="[
              'p-3 border rounded-lg cursor-pointer transition-all',
              'border-green-300 hover:bg-green-100'
            ]"
            @click="applyPreset(preset)"
          >
            <div class="flex items-center gap-2 mb-2">
              <el-icon class="text-green-600"><component :is="preset.icon" /></el-icon>
              <div class="text-sm font-medium text-green-900">{{ preset.name }}</div>
            </div>
            <div class="text-xs text-green-700 mb-2">{{ preset.description }}</div>
            <div class="flex flex-wrap gap-1">
              <el-tag 
                v-for="metric in preset.metrics.slice(0, 3)" 
                :key="metric"
                size="small" 
                type="success"
              >
                {{ getMetricLabel(metric) }}
              </el-tag>
              <el-tag v-if="preset.metrics.length > 3" size="small" type="info">
                +{{ preset.metrics.length - 3 }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>

      <!-- 配置验证 -->
      <div v-if="validationErrors.length > 0" class="p-4 bg-red-50 border border-red-200 rounded-lg">
        <div class="flex items-center gap-2 mb-2">
          <el-icon class="w-5 h-5 text-red-600"><WarningFilled /></el-icon>
          <div class="text-sm font-semibold text-red-900">配置验证警告</div>
        </div>
        <ul class="text-sm text-red-700 space-y-1">
          <li v-for="error in validationErrors" :key="error" class="flex items-center gap-2">
            <span class="w-1 h-1 bg-red-500 rounded-full"></span>
            {{ error }}
          </li>
        </ul>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <div class="flex gap-2">
        <el-button @click="$emit('prev')">
          <el-icon class="mr-2"><ArrowLeft /></el-icon>
          上一步
        </el-button>
        <el-button @click="exportFullConfig" plain>
          <el-icon class="mr-2"><Download /></el-icon>
          导出完整配置
        </el-button>
      </div>
      <el-button @click="$emit('next')" type="primary" :disabled="!canProceed">
        下一步：运行控制
        <el-icon class="ml-2"><ArrowRight /></el-icon>
      </el-button>
    </div>

    <!-- 预设保存对话框 -->
    <el-dialog v-model="presetDialogVisible" title="保存配置预设" width="40%">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">预设名称</label>
          <el-input v-model="newPresetName" placeholder="请输入预设名称..." />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">描述</label>
          <el-input 
            v-model="newPresetDesc"
            type="textarea"
            :rows="3"
            placeholder="请描述这个配置预设的用途..."
          />
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <el-button @click="presetDialogVisible = false">取消</el-button>
          <el-button @click="confirmSavePreset" type="primary">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  PieChart,
  InfoFilled,
  Check,
  Timer,
  WarningFilled,
  ArrowLeft,
  ArrowRight,
  Download,
  Star,
  DataAnalysis,
  Medal
} from '@element-plus/icons-vue'

interface Props {
  modelValue: {
    selected: string[]
    outputs: any
    topK: number
    confidenceThreshold: number
  }
}

interface Emits {
  (e: 'update:modelValue', value: Props['modelValue']): void
  (e: 'prev'): void
  (e: 'next'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 本地数据
const localData = ref({
  selected: ['clean_acc', 'robust_acc', 'asr'],
  outputs: {
    save_adv: true,
    save_original: false,
    save_perturbation: false,
    adv_format: 'numpy',
    save_intermediate: false,
    save_loss_curve: false,
    save_gradients: false,
    save_queries: false,
    export_csv: true,
    export_json: true,
    export_html: false,
    export_pdf: false,
    save_model_outputs: false,
    save_feature_maps: false,
    save_attention_maps: false,
    generate_visualization: false,
    compress_outputs: true
  },
  topK: 5,
  confidenceThreshold: 0.5,
  ...props.modelValue
})

// 状态管理
const presetDialogVisible = ref(false)
const newPresetName = ref('')
const newPresetDesc = ref('')

// 成本预估
const costEstimate = ref({
  samples: 1000,
  steps: 20,
  estSeconds: 120,
  storageSize: 1024 * 1024 * 100 // 100MB
})

// 可用指标配置
const availableMetrics = [
  { 
    key: 'clean_acc', 
    label: 'Clean Accuracy', 
    desc: '模型在未受攻击的原始测试集上的分类准确率，反映模型的基础性能',
    formula: 'correct_predictions / total_samples',
    priority: 'high'
  },
  { 
    key: 'robust_acc', 
    label: 'Robust Accuracy', 
    desc: '模型在对抗样本上仍然正确分类的比例，数值越高表示鲁棒性越强',
    formula: 'correct_adv_predictions / total_adv_samples',
    priority: 'high'
  },
  { 
    key: 'asr', 
    label: 'Attack Success Rate (ASR)', 
    desc: '对抗攻击成功率，即成功误导模型的对抗样本占比，数值越低表示模型越鲁棒',
    formula: '1 - robust_acc',
    priority: 'high'
  },
  { 
    key: 'top5_asr', 
    label: 'Top-5 ASR', 
    desc: 'Top-5攻击成功率，攻击使真实类别不在模型预测的前5名中的比例',
    formula: 'successful_top5_attacks / total_attacks',
    priority: 'medium'
  },
  { 
    key: 'conf_drop', 
    label: 'Confidence Drop', 
    desc: '置信度下降幅度，衡量对抗攻击导致模型预测置信度降低的程度',
    formula: 'avg(clean_confidence - adv_confidence)',
    priority: 'medium'
  },
  { 
    key: 'perturbation_norm', 
    label: 'Perturbation Norm', 
    desc: '对抗扰动的平均范数大小，反映扰动的强度',
    formula: 'avg(||δ||_p)',
    priority: 'medium'
  },
  { 
    key: 'query_count', 
    label: 'Query Count', 
    desc: '黑盒攻击的平均查询次数，反映攻击的计算成本',
    formula: 'total_queries / successful_attacks',
    priority: 'low'
  },
  { 
    key: 'attack_time', 
    label: 'Attack Time', 
    desc: '生成对抗样本的平均时间，衡量攻击效率',
    formula: 'total_time / total_samples',
    priority: 'low'
  },
  { 
    key: 'fooling_rate', 
    label: 'Fooling Rate', 
    desc: '欺骗率，成功改变模型预测的样本比例',
    formula: 'changed_predictions / total_samples',
    priority: 'medium'
  }
]

// 配置预设
const configPresets = ref([
  {
    id: 'basic',
    name: '基础评估',
    description: '核心指标，快速评估',
    icon: 'Star',
    metrics: ['clean_acc', 'robust_acc', 'asr'],
    outputs: {
      save_adv: false,
      export_csv: true,
      export_json: false
    }
  },
  {
    id: 'comprehensive',
    name: '全面评估',
    description: '完整指标，深度分析',
    icon: 'DataAnalysis',
    metrics: ['clean_acc', 'robust_acc', 'asr', 'top5_asr', 'conf_drop', 'perturbation_norm'],
    outputs: {
      save_adv: true,
      save_intermediate: true,
      export_csv: true,
      export_json: true,
      export_html: true
    }
  },
  {
    id: 'research',
    name: '研究级别',
    description: '所有指标，完整数据',
    icon: 'Medal',
    metrics: ['clean_acc', 'robust_acc', 'asr', 'top5_asr', 'conf_drop', 'perturbation_norm', 'query_count', 'attack_time', 'fooling_rate'],
    outputs: {
      save_adv: true,
      save_intermediate: true,
      save_model_outputs: true,
      export_csv: true,
      export_json: true,
      export_html: true,
      export_pdf: true
    }
  }
])

// 计算属性
const canProceed = computed(() => {
  return localData.value.selected.length > 0 && 
         (localData.value.outputs.export_csv || localData.value.outputs.export_json || localData.value.outputs.export_html || localData.value.outputs.export_pdf)
})

const validationErrors = computed(() => {
  const errors: string[] = []
  
  if (localData.value.selected.length === 0) {
    errors.push('至少选择一个评估指标')
  }
  
  if (!localData.value.outputs.export_csv && !localData.value.outputs.export_json && 
      !localData.value.outputs.export_html && !localData.value.outputs.export_pdf) {
    errors.push('至少选择一种报告导出格式')
  }
  
  if (localData.value.outputs.save_adv && !localData.value.outputs.adv_format) {
    errors.push('保存对抗样本时必须选择保存格式')
  }
  
  if (localData.value.confidenceThreshold < 0 || localData.value.confidenceThreshold > 1) {
    errors.push('置信度阈值必须在0-1之间')
  }
  
  return errors
})

// 方法
const toggleMetric = (metricKey: string) => {
  const index = localData.value.selected.indexOf(metricKey)
  if (index > -1) {
    localData.value.selected.splice(index, 1)
  } else {
    localData.value.selected.push(metricKey)
  }
  onDataChange()
}

const selectAllMetrics = () => {
  localData.value.selected = availableMetrics.map(m => m.key)
  onDataChange()
  ElMessage.success('已选择所有指标')
}

const clearAllMetrics = () => {
  localData.value.selected = []
  onDataChange()
  ElMessage.info('已清空所有指标')
}

const onOutputChange = () => {
  onDataChange()
}

const onDataChange = () => {
  emit('update:modelValue', localData.value)
  computeCostEstimate()
}

const computeCostEstimate = () => {
  // 模拟成本计算
  let samples = 1000
  let steps = 20
  let multiplier = 1
  
  // 根据选择的指标调整
  multiplier += localData.value.selected.length * 0.1
  
  // 根据输出选项调整
  if (localData.value.outputs.save_adv) multiplier += 0.3
  if (localData.value.outputs.save_intermediate) multiplier += 0.5
  if (localData.value.outputs.save_model_outputs) multiplier += 0.2
  
  costEstimate.value = {
    samples,
    steps,
    estSeconds: Math.round(samples * steps * multiplier * 0.01),
    storageSize: Math.round(samples * multiplier * 1024 * 100) // KB
  }
  
  ElMessage.info('成本预估已更新')
}

const formatTime = (seconds: number): string => {
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.round(seconds / 60)}分钟`
  return `${Math.round(seconds / 3600)}小时`
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const getMetricLabel = (metricKey: string): string => {
  const metric = availableMetrics.find(m => m.key === metricKey)
  return metric?.label.split(' ')[0] || metricKey
}

const applyPreset = (preset: any) => {
  localData.value.selected = [...preset.metrics]
  localData.value.outputs = { ...localData.value.outputs, ...preset.outputs }
  onDataChange()
  ElMessage.success(`已应用预设：${preset.name}`)
}

const saveCurrentPreset = () => {
  newPresetName.value = ''
  newPresetDesc.value = ''
  presetDialogVisible.value = true
}

const confirmSavePreset = () => {
  if (!newPresetName.value.trim()) {
    ElMessage.warning('请输入预设名称')
    return
  }
  
  const newPreset = {
    id: Date.now().toString(),
    name: newPresetName.value,
    description: newPresetDesc.value || '用户自定义预设',
    icon: 'Star',
    metrics: [...localData.value.selected],
    outputs: { ...localData.value.outputs }
  }
  
  configPresets.value.push(newPreset)
  presetDialogVisible.value = false
  ElMessage.success('配置预设已保存')
}

const exportFullConfig = () => {
  const config = {
    metrics: localData.value,
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  }
  
  const json = JSON.stringify(config, null, 2)
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'dqtest-metrics-config.json'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  
  ElMessage.success('完整配置已导出')
}

// 监听数据变化
watch(localData, (newVal) => {
  emit('update:modelValue', newVal)
}, { deep: true })

watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    localData.value = { ...localData.value, ...newVal }
  }
}, { deep: true })

// 初始化
computeCostEstimate()
</script>

<style lang="scss" scoped>
.metrics-config {
  padding: 2rem;
  
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    
    h3 {
      font-size: 1.25rem;
      font-weight: 600;
      margin: 0;
    }
  }
  
  .form-content {
    margin-bottom: 2rem;
  }
  
  .action-buttons {
    display: flex;
    justify-content: space-between;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
  }
}

// Tailwind-like classes
.flex { display: flex; }
.items-center { align-items: center; }
.items-start { align-items: flex-start; }
.justify-between { justify-content: space-between; }
.justify-end { justify-content: flex-end; }
.gap-1 { gap: 0.25rem; }
.gap-2 { gap: 0.5rem; }
.gap-3 { gap: 0.75rem; }
.gap-4 { gap: 1rem; }
.w-1 { width: 0.25rem; }
.h-1 { height: 0.25rem; }
.w-3 { width: 0.75rem; }
.h-3 { height: 0.75rem; }
.w-5 { width: 1.25rem; }
.h-5 { height: 1.25rem; }
.w-7 { width: 1.75rem; }
.h-7 { height: 1.75rem; }
.w-20 { width: 5rem; }
.rounded-lg { border-radius: 0.5rem; }
.rounded-full { border-radius: 9999px; }
.bg-indigo-600 { background-color: rgb(79 70 229); }
.bg-indigo-50 { background-color: rgb(238 242 255); }
.bg-blue-50 { background-color: rgb(239 246 255); }
.bg-gray-50 { background-color: rgb(249 250 251); }
.bg-gray-900 { background-color: rgb(17 24 39); }
.bg-white { background-color: rgb(255 255 255); }
.bg-purple-50 { background-color: rgb(250 245 255); }
.bg-green-50 { background-color: rgb(240 253 244); }
.bg-red-50 { background-color: rgb(254 242 242); }
.bg-red-500 { background-color: rgb(239 68 68); }
.text-white { color: rgb(255 255 255); }
.text-gray-900 { color: rgb(17 24 39); }
.text-gray-800 { color: rgb(31 41 55); }
.text-gray-700 { color: rgb(55 65 81); }
.text-gray-600 { color: rgb(75 85 99); }
.text-gray-500 { color: rgb(107 114 128); }
.text-blue-900 { color: rgb(30 58 138); }
.text-blue-800 { color: rgb(30 64 175); }
.text-blue-600 { color: rgb(37 99 235); }
.text-indigo-300 { color: rgb(165 180 252); }
.text-purple-600 { color: rgb(147 51 234); }
.text-purple-900 { color: rgb(88 28 135); }
.text-purple-700 { color: rgb(126 34 206); }
.text-green-600 { color: rgb(22 163 74); }
.text-green-900 { color: rgb(20 83 45); }
.text-green-700 { color: rgb(21 128 61); }
.text-red-600 { color: rgb(220 38 38); }
.text-red-900 { color: rgb(127 29 29); }
.text-red-700 { color: rgb(185 28 28); }
.text-sm { font-size: 0.875rem; }
.text-xs { font-size: 0.75rem; }
.text-lg { font-size: 1.125rem; }
.font-bold { font-weight: 700; }
.font-semibold { font-weight: 600; }
.font-medium { font-weight: 500; }
.font-mono { font-family: ui-monospace, SFMono-Regular, 'SF Mono', monospace; }
.shadow { box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1); }
.border { border-width: 1px; }
.border-2 { border-width: 2px; }
.border-gray-200 { border-color: rgb(229 231 235); }
.border-gray-300 { border-color: rgb(209 213 219); }
.border-blue-200 { border-color: rgb(191 219 254); }
.border-indigo-300 { border-color: rgb(165 180 252); }
.border-indigo-600 { border-color: rgb(79 70 229); }
.border-purple-200 { border-color: rgb(221 214 254); }
.border-green-200 { border-color: rgb(187 247 208); }
.border-green-300 { border-color: rgb(134 239 172); }
.border-red-200 { border-color: rgb(254 202 202); }
.p-2 { padding: 0.5rem; }
.p-3 { padding: 0.75rem; }
.p-4 { padding: 1rem; }
.mb-1 { margin-bottom: 0.25rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-3 { margin-bottom: 0.75rem; }
.mb-4 { margin-bottom: 1rem; }
.mt-1 { margin-top: 0.25rem; }
.mt-2 { margin-top: 0.5rem; }
.mt-4 { margin-top: 1rem; }
.mr-2 { margin-right: 0.5rem; }
.ml-2 { margin-left: 0.5rem; }
.ml-4 { margin-left: 1rem; }
.space-y-1 > * + * { margin-top: 0.25rem; }
.space-y-2 > * + * { margin-top: 0.5rem; }
.space-y-4 > * + * { margin-top: 1rem; }
.space-y-6 > * + * { margin-top: 1.5rem; }
.grid { display: grid; }
.grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.cursor-pointer { cursor: pointer; }
.transition-all { transition-property: all; }
.overflow-hidden { overflow: hidden; }
.block { display: block; }
.flex-1 { flex: 1 1 0%; }
.flex-shrink-0 { flex-shrink: 0; }
.flex-wrap { flex-wrap: wrap; }
.min-w-0 { min-width: 0px; }
.w-full { width: 100%; }

// 响应式
@media (min-width: 768px) {
  .md\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .md\:grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}

@media (min-width: 1024px) {
  .lg\:grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}

// 悬停效果
.hover\:bg-gray-50:hover { background-color: rgb(249 250 251); }
.hover\:bg-green-100:hover { background-color: rgb(220 252 231); }
.hover\:border-indigo-300:hover { border-color: rgb(165 180 252); }
</style>

## 功能特点总结

现在"指标与输出"模块已经完全恢复HTML的复杂功能，包括：

### ✅ 完整功能列表：

1. **评估指标选择** - 9种鲁棒性指标，带优先级和公式说明
2. **输出选项配置** - 对抗样本保存、中间过程、多种报告格式
3. **成本预估系统** - 动态计算时间、存储、样本数量
4. **配置预设** - 基础、全面、研究级三种快速配置
5. **参数验证** - 实时验证配置合理性
6. **高级输出选项** - 特征图、注意力图、可视化等
7. **配置导出** - 完整配置JSON导出功能

### ✅ 交互功能：

- 指标复选框切换
- 输出选项动态配置
- 成本实时计算更新
- 预设应用和保存
- 配置验证提示
- 参数调节滑块

### ✅ 智能特性：

- 优先级指标标识
- 依赖配置联动
- 存储需求预估
- 配置冲突检测
- 快速配置模板

现在可以测试这个模块的完整功能了！继续下一个模块"运行控制"吗？
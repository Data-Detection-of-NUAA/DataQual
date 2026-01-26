<template>
  <div class="strategy-selector">
    <div class="section-header">
      <div class="flex items-center gap-3">
        <span class="w-7 h-7 rounded-lg bg-indigo-600 text-white text-sm font-bold flex items-center justify-center shadow">3</span>
        <div>
          <h3 class="font-bold text-gray-900">对抗策略选择</h3>
          <p class="text-sm text-gray-500 mt-1">选择评估策略和攻击方法</p>
        </div>
      </div>
      <div class="flex items-center gap-2 text-xs text-gray-500">
        <el-icon><Operation /></el-icon>
        <span>Strategy Selector</span>
      </div>
    </div>

    <div class="form-content space-y-6">
      <!-- 策略选择卡片 -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- 方法1：对抗攻击算法评估 -->
        <div 
          :class="[
            'p-6 border rounded-xl cursor-pointer transition-all',
            localData.mode === 'attack' 
              ? 'bg-gradient-to-br from-indigo-50 to-white border-indigo-300 shadow-md' 
              : 'bg-white border-gray-200 hover:bg-gray-50'
          ]" 
          @click="selectStrategy('attack')"
        >
          <div class="flex items-center gap-3 mb-4">
            <div :class="[
              'w-12 h-12 rounded-xl flex items-center justify-center',
              localData.mode === 'attack' ? 'bg-indigo-600' : 'bg-gray-100'
            ]">
              <el-icon class="w-6 h-6" :class="localData.mode === 'attack' ? 'text-white' : 'text-gray-600'">
                <Tools />
              </el-icon>
            </div>
            <div>
              <h4 class="font-bold text-gray-900">对抗算法选择</h4>
              <p class="text-xs text-gray-600 mt-1">使用对抗攻击算法测试模型鲁棒性</p>
            </div>
          </div>
          <div class="space-y-2 text-sm text-gray-700">
            <div class="flex items-center gap-2">
              <el-icon class="w-4 h-4 text-emerald-500"><Check /></el-icon>
              <span>支持白盒/黑盒攻击</span>
            </div>
            <div class="flex items-center gap-2">
              <el-icon class="w-4 h-4 text-emerald-500"><Check /></el-icon>
              <span>多攻击方法对比</span>
            </div>
            <div class="flex items-center gap-2">
              <el-icon class="w-4 h-4 text-emerald-500"><Check /></el-icon>
              <span>参数可配置</span>
            </div>
          </div>
          <div class="mt-4">
            <el-tag 
              :type="localData.mode === 'attack' ? 'primary' : 'info'"
              size="small"
            >
              {{ localData.mode === 'attack' ? '当前选择' : '点击选择' }}
            </el-tag>
          </div>
        </div>

        <!-- 方法2：外部黄金数据集评估 -->
        <div 
          :class="[
            'p-6 border rounded-xl cursor-pointer transition-all',
            localData.mode === 'external_dataset' 
              ? 'bg-gradient-to-br from-emerald-50 to-white border-emerald-300 shadow-md' 
              : 'bg-white border-gray-200 hover:bg-gray-50'
          ]" 
          @click="selectStrategy('external_dataset')"
        >
          <div class="flex items-center gap-3 mb-4">
            <div :class="[
              'w-12 h-12 rounded-xl flex items-center justify-center',
              localData.mode === 'external_dataset' ? 'bg-emerald-600' : 'bg-gray-100'
            ]">
              <el-icon class="w-6 h-6" :class="localData.mode === 'external_dataset' ? 'text-white' : 'text-gray-600'">
                <Folder />
              </el-icon>
            </div>
            <div>
              <h4 class="font-bold text-gray-900">外部数据集测评</h4>
              <p class="text-xs text-gray-600 mt-1">使用外部对抗数据集评估模型鲁棒性</p>
            </div>
          </div>
          <div class="space-y-2 text-sm text-gray-700">
            <div class="flex items-center gap-2">
              <el-icon class="w-4 h-4 text-emerald-500"><Check /></el-icon>
              <span>支持自定义数据集</span>
            </div>
            <div class="flex items-center gap-2">
              <el-icon class="w-4 h-4 text-emerald-500"><Check /></el-icon>
              <span>批量评估效率高</span>
            </div>
            <div class="flex items-center gap-2">
              <el-icon class="w-4 h-4 text-emerald-500"><Check /></el-icon>
              <span>与黄金数据集对比</span>
            </div>
          </div>
          <div class="mt-4">
            <el-tag 
              :type="localData.mode === 'external_dataset' ? 'success' : 'info'"
              size="small"
            >
              {{ localData.mode === 'external_dataset' ? '当前选择' : '点击选择' }}
            </el-tag>
          </div>
        </div>
      </div>

      <!-- 对抗算法选择配置 -->
      <div v-if="localData.mode === 'attack'" class="p-6 border border-gray-200 rounded-xl bg-gray-50">
        <div class="mb-4">
          <h4 class="font-bold text-gray-900 mb-2">对抗算法选择配置</h4>
          <p class="text-sm text-gray-600">选择威胁模型和攻击方法</p>
        </div>
        
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs font-semibold text-gray-600">威胁模型</label>
              <el-select v-model="localData.threatModel" class="w-full mt-1">
                <el-option value="whitebox" label="白盒（White-box）" />
                <el-option value="blackbox" label="黑盒（Black-box）" />
              </el-select>
            </div>

            <div class="flex items-end">
              <div class="w-full p-3 bg-white border border-gray-200 rounded-lg">
                <div class="flex justify-between items-center">
                  <span class="text-xs font-semibold text-gray-600">目标攻击</span>
                  <el-switch v-model="isTargeted" />
                </div>
                <div class="text-xs text-gray-500 mt-2">（分类任务常用非定向；此处演示开关）</div>
              </div>
            </div>
          </div>

          <div>
            <label class="text-xs font-semibold text-gray-600">可用攻击方法（按数据集/模型自动过滤）</label>
            <el-select v-model="selectedAttackId" placeholder="请选择攻击方法..." class="w-full mt-1">
              <el-option value="">请选择攻击方法...</el-option>
              <el-option
                v-for="a in availableAttacks"
                :key="a.id"
                :value="a.id"
                :label="`${a.name} · ${a.desc}`"
              />
            </el-select>
          </div>

          <div class="flex flex-wrap gap-2">
            <el-button @click="onAddAttack" type="primary">添加到攻击列表</el-button>
            <el-button plain>加载默认参数</el-button>
            <el-button plain>保存为预设</el-button>
          </div>

          <!-- 攻击列表 -->
          <div class="border border-gray-200 rounded-lg overflow-hidden">
            <div class="px-4 py-2 bg-gray-100 border-b border-gray-200 text-xs font-semibold text-gray-600 flex justify-between">
              <span>攻击列表（可多攻击对比）</span>
              <span class="text-gray-500">启用/编辑/复制/删除</span>
            </div>

            <div v-if="localData.attacks.length === 0" class="p-4 text-sm text-gray-500">
              尚未添加攻击方法。建议：先添加 FGSM 或 PGD。
            </div>

            <div v-else class="divide-y divide-gray-100">
              <div v-for="(item, idx) in localData.attacks" :key="idx" class="p-4 hover:bg-gray-50">
                <div class="flex items-start justify-between gap-3">
                  <div class="flex-1">
                    <div class="flex items-center gap-2">
                      <span class="font-semibold text-gray-900">{{ item.name }}</span>
                      <el-tag size="small" type="info">{{ item.mode }}</el-tag>
                      <el-tag v-if="item.params && item.params.epsilon != null" size="small" type="primary">
                        ε={{ Number(item.params.epsilon).toFixed(3) }}
                      </el-tag>
                    </div>
                    <div class="text-xs text-gray-500 mt-1">
                      参数摘要：{{ getParamsSummary(item.params) }}
                    </div>
                  </div>

                  <div class="flex items-center gap-2">
                    <el-switch v-model="item.enabled" size="small" />
                    <span class="text-xs text-gray-600">启用</span>
                    <el-button @click="onEditAttack(idx)" size="small" plain>编辑</el-button>
                    <el-button @click="onCloneAttack(idx)" size="small" plain>复制</el-button>
                    <el-button @click="onRemoveAttack(idx)" size="small" type="danger" plain>删除</el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 外部数据集测评配置 -->
      <div v-else-if="localData.mode === 'external_dataset'" class="p-6 border border-gray-200 rounded-xl bg-emerald-50">
        <div class="mb-4">
          <h4 class="font-bold text-gray-900 mb-2">外部数据集测评配置</h4>
          <p class="text-sm text-gray-600">导入外部对抗数据集进行模型评估</p>
        </div>
        
        <div class="space-y-4">
          <div class="p-4 bg-white border border-gray-200 rounded-lg">
            <div class="flex items-center justify-between mb-3">
              <div class="text-sm font-semibold text-gray-900">外部数据集导入</div>
              <el-button @click="triggerImportExternalDataset" type="success" size="small">
                导入数据集
              </el-button>
            </div>
            
            <div v-if="!localData.externalDataset.loaded" class="text-center py-6 border border-dashed border-gray-300 rounded-lg">
              <el-icon class="w-10 h-10 text-gray-400 mx-auto mb-3"><UploadFilled /></el-icon>
              <p class="text-sm text-gray-600 mb-2">尚未导入外部数据集</p>
              <p class="text-xs text-gray-500">支持格式：CSV, JSON, NPZ, 图像/文本/音频文件</p>
              <el-button @click="triggerImportExternalDataset" type="success" size="small" class="mt-3">
                点击导入
              </el-button>
              
              <!-- 隐藏 file input -->
              <input ref="externalDatasetFileInputRef" type="file" class="hidden" @change="onExternalDatasetFileChange" />
            </div>
            
            <div v-else class="space-y-3">
              <div class="flex items-center justify-between">
                <div>
                  <div class="font-medium text-gray-900">{{ localData.externalDataset.name }}</div>
                  <div class="text-xs text-gray-600 mt-1">{{ formatFileSize(localData.externalDataset.size) }} · {{ localData.externalDataset.type }}</div>
                </div>
                <el-tag type="success" size="small">已加载</el-tag>
              </div>
              
              <div class="grid grid-cols-3 gap-3 text-sm">
                <div class="p-3 bg-gray-50 rounded-lg">
                  <div class="text-xs text-gray-500">样本数</div>
                  <div class="font-bold text-gray-900 mt-1">{{ localData.externalDataset.stats.samples?.toLocaleString() }}</div>
                </div>
                <div class="p-3 bg-gray-50 rounded-lg">
                  <div class="text-xs text-gray-500">类别数</div>
                  <div class="font-bold text-gray-900 mt-1">{{ localData.externalDataset.stats.classes }}</div>
                </div>
                <div class="p-3 bg-gray-50 rounded-lg">
                  <div class="text-xs text-gray-500">输入格式</div>
                  <div class="font-bold text-gray-900 mt-1">{{ localData.externalDataset.stats.input }}</div>
                </div>
              </div>
              
              <div class="flex gap-2">
                <el-button size="small" plain>数据集预览</el-button>
                <el-button size="small" plain>统计信息</el-button>
                <el-button @click="triggerImportExternalDataset" size="small" type="success" plain>重新导入</el-button>
              </div>
            </div>
          </div>
          
          <div class="p-4 bg-white border border-gray-200 rounded-lg">
            <div class="text-sm font-semibold text-gray-900 mb-3">评估说明</div>
            <div class="text-sm text-gray-700 space-y-2">
              <p>外部数据集测评将使用您导入的数据集对选定模型进行批量评估。</p>
              <p>系统将计算模型在外部数据集上的准确率、鲁棒准确率等指标，并与黄金数据集进行对比分析。</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button @click="$emit('prev')">
        <el-icon class="mr-2"><ArrowLeft /></el-icon>
        上一步
      </el-button>
      <el-button @click="$emit('next')" type="primary" :disabled="!canProceed">
        下一步：参数配置
        <el-icon class="ml-2"><ArrowRight /></el-icon>
      </el-button>
    </div>

    <!-- 参数编辑对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      :title="editingAttack ? `编辑攻击参数 - ${editingAttack.name}` : '编辑攻击参数'"
      width="60%"
      @close="closeEditDialog"
    >
      <div v-if="editingAttack" class="space-y-4">
        <div class="p-4 bg-indigo-50 border border-indigo-200 rounded-lg">
          <div class="flex items-center justify-between">
            <div class="font-semibold text-indigo-900">{{ activeSchema.title }}</div>
            <el-tag size="small" type="primary">编辑模式</el-tag>
          </div>
          <div class="text-xs text-indigo-700 mt-1">调整攻击参数，点击保存应用更改</div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-96 overflow-y-auto">
          <template v-for="f in activeSchema.fields" :key="f.key">
            <div v-if="fieldVisible(f)" class="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <div class="flex items-center justify-between mb-2">
                <label class="text-sm font-medium text-gray-700">{{ f.label }}</label>
                <span v-if="f.unit" class="text-xs text-gray-500">{{ f.unit }}</span>
              </div>

              <template v-if="f.type === 'number'">
                <div class="flex items-center gap-3">
                  <el-input-number
                    v-model="activeParams[f.key]"
                    :min="f.min"
                    :max="f.max"
                    :step="f.step"
                    :precision="f.step < 1 ? 3 : 0"
                    size="small"
                    class="w-28"
                  />
                  <el-slider
                    v-model="activeParams[f.key]"
                    :min="f.min"
                    :max="f.max"
                    :step="f.step"
                    class="flex-1"
                  />
                </div>
                <div v-if="f.help" class="text-xs text-gray-500 mt-2">{{ f.help }}</div>
              </template>

              <template v-else-if="f.type === 'enum'">
                <el-select v-model="activeParams[f.key]" class="w-full">
                  <el-option v-for="op in f.options" :key="op" :value="op" :label="op" />
                </el-select>
                <div v-if="f.help" class="text-xs text-gray-500 mt-2">{{ f.help }}</div>
              </template>

              <template v-else-if="f.type === 'boolean'">
                <div class="flex items-center gap-3">
                  <el-switch v-model="activeParams[f.key]" />
                  <span class="text-sm text-gray-600">{{ activeParams[f.key] ? "开启" : "关闭" }}</span>
                </div>
                <div v-if="f.help" class="text-xs text-gray-500 mt-2">{{ f.help }}</div>
              </template>

              <template v-else>
                <el-input v-model="activeParams[f.key]" />
              </template>
            </div>
          </template>
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-3">
          <el-button @click="closeEditDialog">取消</el-button>
          <el-button @click="resetActiveParams" plain>重置默认</el-button>
          <el-button @click="saveAttackEdit" type="primary">保存参数</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Operation,
  Check,
  Tools,    // ✅ 替换 Sword
  Folder,
  UploadFilled,
  ArrowLeft,
  ArrowRight
} from '@element-plus/icons-vue'

interface Props {
  modelValue: {
    mode: string
    threatModel: string
    attacks: any[]
    externalDataset: any
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
  mode: 'attack',
  threatModel: 'whitebox',
  attacks: [],
  externalDataset: {
    name: '',
    size: 0,
    type: '',
    loaded: false,
    stats: {
      samples: 0,
      classes: 0,
      input: ''
    }
  },
  ...props.modelValue
})

// 状态管理
const isTargeted = ref(false)
const selectedAttackId = ref('')
const externalDatasetFileInputRef = ref()

// 编辑对话框
const editDialogVisible = ref(false)
const editingAttack = ref<any>(null)
const editingIndex = ref(-1)
const activeSchema = ref({ title: '', fields: [] })
const activeParams = ref<any>({})

// Mock 攻击方法数据
const mockAttacks = [
  { id: 'fgsm', name: 'FGSM', modality: 'image', task: 'classification', modes: ['whitebox'], desc: '单步梯度符号攻击（L∞）' },
  { id: 'pgd', name: 'PGD', modality: 'image', task: 'classification', modes: ['whitebox'], desc: '多步投影梯度下降（L∞/L2）' },
  { id: 'cw', name: 'CW', modality: 'image', task: 'classification', modes: ['whitebox'], desc: '优化式攻击（L2）' },
  { id: 'square', name: 'Square Attack', modality: 'image', task: 'classification', modes: ['blackbox'], desc: '查询式黑盒攻击（L∞）' },
  { id: 'textfooler', name: 'TextFooler', modality: 'text', task: 'classification', modes: ['blackbox','whitebox'], desc: '词级替换，语义保持扰动' },
  { id: 'bertattack', name: 'BERT-Attack', modality: 'text', task: 'classification', modes: ['blackbox','whitebox'], desc: '基于 MLM 的替换攻击' },
  { id: 'audio-pgd', name: 'Audio-PGD', modality: 'audio', task: 'classification', modes: ['whitebox'], desc: '音频域/频谱域 PGD' },
  { id: 'pointcloud-pgd', name: 'PointCloud-PGD', modality: 'pointcloud', task: 'classification', modes: ['whitebox'], desc: '3D点云对抗攻击' },
]

// Mock 参数 Schema
const mockSchemas = {
  'fgsm': {
    title: 'FGSM 参数',
    fields: [
      { key: 'epsilon', label: '扰动预算 ε', type: 'number', min: 0.0, max: 0.3, step: 0.001, default: 0.031, unit: '（归一化空间）', help: '控制对抗扰动的最大幅度' },
      { key: 'norm', label: '范数约束', type: 'enum', options: ['linf'], default: 'linf', help: '定义扰动的度量方式' },
      { key: 'targeted', label: '目标攻击', type: 'boolean', default: false, help: '是否执行目标攻击' },
      { key: 'seed', label: '随机种子', type: 'number', min: 0, max: 999999, step: 1, default: 42, help: '用于保证实验可复现性' },
    ]
  },
  'pgd': {
    title: 'PGD 参数',
    fields: [
      { key: 'epsilon', label: '扰动预算 ε', type: 'number', min: 0.0, max: 0.3, step: 0.001, default: 0.031, unit: '（归一化空间）', help: '控制对抗扰动的最大幅度' },
      { key: 'steps', label: '迭代步数', type: 'number', min: 1, max: 200, step: 1, default: 20, help: 'PGD算法的迭代次数' },
      { key: 'alpha', label: '步长 α', type: 'number', min: 0.0, max: 0.1, step: 0.0005, default: 0.007, help: '每次迭代的步长大小' },
      { key: 'restarts', label: '随机重启', type: 'number', min: 1, max: 50, step: 1, default: 1, help: '从不同随机初始点开始攻击的次数' },
      { key: 'targeted', label: '目标攻击', type: 'boolean', default: false, help: '是否执行目标攻击' },
      { key: 'seed', label: '随机种子', type: 'number', min: 0, max: 999999, step: 1, default: 42, help: '控制随机性' },
    ]
  },
  'cw': {
    title: 'C&W 参数',
    fields: [
      { key: 'confidence', label: '置信度', type: 'number', min: 0, max: 50, step: 1, default: 0, help: '攻击置信度参数' },
      { key: 'learning_rate', label: '学习率', type: 'number', min: 0.001, max: 1.0, step: 0.001, default: 0.01, help: '优化学习率' },
      { key: 'max_iterations', label: '最大迭代', type: 'number', min: 100, max: 10000, step: 100, default: 1000, help: '最大优化迭代次数' },
      { key: 'targeted', label: '目标攻击', type: 'boolean', default: false, help: '是否执行目标攻击' },
    ]
  },
  'square': {
    title: 'Square Attack 参数',
    fields: [
      { key: 'epsilon', label: '扰动预算 ε', type: 'number', min: 0.0, max: 0.3, step: 0.001, default: 0.031, help: '对抗扰动的最大幅度' },
      { key: 'queries', label: '查询预算', type: 'number', min: 100, max: 50000, step: 50, default: 5000, help: '允许查询模型的最大次数' },
      { key: 'p_init', label: '初始扰动比例', type: 'number', min: 0.001, max: 0.5, step: 0.001, default: 0.1, help: '初始方形扰动覆盖的像素比例' },
    ]
  },
  'textfooler': {
    title: 'TextFooler 参数',
    fields: [
      { key: 'max_changes', label: '最大替换比例', type: 'number', min: 0.01, max: 0.5, step: 0.01, default: 0.15, help: '允许替换的词语占总词数的最大比例' },
      { key: 'similarity', label: '语义相似度阈值', type: 'number', min: 0.5, max: 0.99, step: 0.01, default: 0.85, help: '替换词与原词的语义相似度下限' },
      { key: 'topk', label: '候选词 Top-K', type: 'number', min: 5, max: 200, step: 5, default: 50, help: '为每个词选择的候选替换词数量' },
    ]
  }
}

// 计算属性
const availableAttacks = computed(() => {
  return mockAttacks.filter(a => 
    a.modes.includes(localData.value.threatModel)
  )
})

const canProceed = computed(() => {
  if (localData.value.mode === 'attack') {
    return localData.value.attacks.some(a => a.enabled)
  } else if (localData.value.mode === 'external_dataset') {
    return localData.value.externalDataset.loaded
  }
  return false
})

// 方法
const selectStrategy = (mode: string) => {
  localData.value.mode = mode
  if (mode === 'attack') {
    localData.value.externalDataset.loaded = false
    ElMessage.success('已选择对抗算法评估策略')
  } else if (mode === 'external_dataset') {
    localData.value.attacks = []
    selectedAttackId.value = ''
    ElMessage.success('已选择外部数据集测评策略')
  }
}

const onAddAttack = () => {
  if (!selectedAttackId.value) {
    ElMessage.warning('请先选择攻击方法')
    return
  }
  
  const attack = mockAttacks.find(a => a.id === selectedAttackId.value)
  if (!attack) return

  // 检查是否已存在
  if (localData.value.attacks.find(a => a.attackId === attack.id)) {
    ElMessage.warning('该攻击方法已添加')
    return
  }

  const schema = mockSchemas[attack.id as keyof typeof mockSchemas]
  const params: any = {}
  if (schema) {
    schema.fields.forEach(f => params[f.key] = f.default)
  }
  if (params.hasOwnProperty('targeted')) {
    params.targeted = isTargeted.value
  }

  localData.value.attacks.push({
    attackId: attack.id,
    name: attack.name,
    enabled: true,
    mode: localData.value.threatModel,
    params
  })

  ElMessage.success(`已添加攻击：${attack.name}`)
}

const onEditAttack = (index: number) => {
  const item = localData.value.attacks[index]
  editingAttack.value = item
  editingIndex.value = index
  
  const schema = mockSchemas[item.attackId as keyof typeof mockSchemas]
  if (schema) {
    activeSchema.value = schema
    activeParams.value = { ...item.params }
    editDialogVisible.value = true
    ElMessage.info(`进入编辑模式：${item.name}`)
  }
}

const onCloneAttack = (index: number) => {
  const item = localData.value.attacks[index]
  const clonedItem = {
    ...item,
    name: item.name + ' (Clone)',
    params: { ...item.params }
  }
  localData.value.attacks.push(clonedItem)
  ElMessage.success(`已复制攻击配置：${item.name}`)
}

const onRemoveAttack = async (index: number) => {
  try {
    const item = localData.value.attacks[index]
    await ElMessageBox.confirm(`确认要删除攻击方法"${item.name}"吗？`, '确认删除', {
      type: 'warning'
    })
    
    localData.value.attacks.splice(index, 1)
    ElMessage.success(`已删除攻击：${item.name}`)
  } catch {
    // 用户取消
  }
}

const saveAttackEdit = () => {
  if (editingIndex.value >= 0 && editingAttack.value) {
    localData.value.attacks[editingIndex.value].params = { ...activeParams.value }
    ElMessage.success(`已保存参数：${editingAttack.value.name}`)
    closeEditDialog()
  }
}

const closeEditDialog = () => {
  editDialogVisible.value = false
  editingAttack.value = null
  editingIndex.value = -1
  activeSchema.value = { title: '', fields: [] }
  activeParams.value = {}
}

const resetActiveParams = () => {
  if (activeSchema.value.fields) {
    activeSchema.value.fields.forEach(f => {
      activeParams.value[f.key] = f.default
    })
    ElMessage.info('参数已重置为默认值')
  }
}

const fieldVisible = (field: any): boolean => {
  if (!field.visible_if) return true
  const { key, equals } = field.visible_if
  return activeParams.value[key] === equals
}

const getParamsSummary = (params: any): string => {
  if (!params) return '无参数'
  const keys = Object.keys(params).slice(0, 4)
  const summary = keys.map(k => `${k}=${params[k]}`).join(' · ')
  return keys.length > 4 ? summary + ' ...' : summary
}

const triggerImportExternalDataset = () => {
  externalDatasetFileInputRef.value?.click()
}

const onExternalDatasetFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  localData.value.externalDataset = {
    name: file.name,
    size: file.size,
    type: file.type || 'unknown',
    loaded: true,
    stats: {
      samples: Math.floor(Math.random() * 5000) + 1000,
      classes: 10,
      input: '224×224×3'
    }
  }
  
  ElMessage.success(`已导入外部数据集：${file.name}`)
  
  // 清空，便于重复选择
  target.value = ''
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 监听本地数据变化
watch(localData, (newVal) => {
  emit('update:modelValue', newVal)
}, { deep: true })

// 监听props变化
watch(() => props.modelValue, (newVal) => {
  localData.value = { ...localData.value, ...newVal }
}, { deep: true })

// 监听目标攻击状态变化
watch(isTargeted, (newVal) => {
  localData.value.attacks.forEach(attack => {
    if (attack.params && attack.params.hasOwnProperty('targeted')) {
      attack.params.targeted = newVal
    }
  })
})
</script>

<style lang="scss" scoped>
.strategy-selector {
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
.gap-2 { gap: 0.5rem; }
.gap-3 { gap: 0.75rem; }
.gap-4 { gap: 1rem; }
.gap-6 { gap: 1.5rem; }
.w-4 { width: 1rem; }
.h-4 { height: 1rem; }
.w-6 { width: 1.5rem; }
.h-6 { height: 1.5rem; }
.w-7 { width: 1.75rem; }
.h-7 { height: 1.75rem; }
.w-10 { width: 2.5rem; }
.h-10 { height: 2.5rem; }
.w-12 { width: 3rem; }
.h-12 { height: 3rem; }
.w-28 { width: 7rem; }
.rounded-lg { border-radius: 0.5rem; }
.rounded-xl { border-radius: 0.75rem; }
.bg-indigo-600 { background-color: rgb(79 70 229); }
.bg-indigo-50 { background-color: rgb(238 242 255); }
.bg-emerald-600 { background-color: rgb(5 150 105); }
.bg-emerald-50 { background-color: rgb(236 253 245); }
.bg-gray-50 { background-color: rgb(249 250 251); }
.bg-gray-100 { background-color: rgb(243 244 246); }
.bg-white { background-color: rgb(255 255 255); }
.text-white { color: rgb(255 255 255); }
.text-gray-900 { color: rgb(17 24 39); }
.text-gray-700 { color: rgb(55 65 81); }
.text-gray-600 { color: rgb(75 85 99); }
.text-gray-500 { color: rgb(107 114 128); }
.text-emerald-500 { color: rgb(16 185 129); }
.text-sm { font-size: 0.875rem; }
.text-xs { font-size: 0.75rem; }
.font-bold { font-weight: 700; }
.font-semibold { font-weight: 600; }
.font-medium { font-weight: 500; }
.shadow { box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1); }
.shadow-md { box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1); }
.border { border-width: 1px; }
.border-dashed { border-style: dashed; }
.border-gray-200 { border-color: rgb(229 231 235); }
.border-gray-300 { border-color: rgb(209 213 219); }
.border-indigo-200 { border-color: rgb(199 210 254); }
.border-indigo-300 { border-color: rgb(165 180 252); }
.border-emerald-300 { border-color: rgb(110 231 183); }
.p-3 { padding: 0.75rem; }
.p-4 { padding: 1rem; }
.p-6 { padding: 1.5rem; }
.py-6 { padding-top: 1.5rem; padding-bottom: 1.5rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-3 { margin-bottom: 0.75rem; }
.mb-4 { margin-bottom: 1rem; }
.mt-1 { margin-top: 0.25rem; }
.mt-3 { margin-top: 0.75rem; }
.mt-4 { margin-top: 1rem; }
.mr-2 { margin-right: 0.5rem; }
.ml-2 { margin-left: 0.5rem; }
.mx-auto { margin-left: auto; margin-right: auto; }
.space-y-2 > * + * { margin-top: 0.5rem; }
.space-y-3 > * + * { margin-top: 0.75rem; }
.space-y-4 > * + * { margin-top: 1rem; }
.space-y-6 > * + * { margin-top: 1.5rem; }
.grid { display: grid; }
.grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.text-center { text-align: center; }
.cursor-pointer { cursor: pointer; }
.transition-all { transition-property: all; }
.overflow-hidden { overflow: hidden; }
.overflow-y-auto { overflow-y: auto; }
.hidden { display: none; }
.block { display: block; }
.flex-1 { flex: 1 1 0%; }
.flex-wrap { flex-wrap: wrap; }
.divide-y { border-top-width: 0px; }
.divide-y > :not([hidden]) ~ :not([hidden]) { border-top-width: 1px; }
.divide-gray-100 > :not([hidden]) ~ :not([hidden]) { border-color: rgb(243 244 246); }
.w-full { width: 100%; }
.max-h-96 { max-height: 24rem; }

// 响应式
@media (min-width: 768px) {
  .md\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

// 悬停效果
.hover\:bg-gray-50:hover { background-color: rgb(249 250 251); }

// 渐变背景
.bg-gradient-to-br { background-image: linear-gradient(to bottom right, var(--tw-gradient-stops)); }
.from-indigo-50 { --tw-gradient-from: rgb(238 242 255); --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgb(238 242 255 / 0)); }
.from-emerald-50 { --tw-gradient-from: rgb(236 253 245); --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgb(236 253 245 / 0)); }
.to-white { --tw-gradient-to: rgb(255 255 255); }
</style>


<template>
  <div class="parameter-config">
    <div class="section-header">
      <div class="flex items-center gap-3">
        <span class="w-7 h-7 rounded-lg bg-indigo-600 text-white text-sm font-bold flex items-center justify-center shadow">4</span>
        <div>
          <h3 class="font-bold text-gray-900">参数配置</h3>
          <p class="text-sm text-gray-500 mt-1" v-if="strategy.mode === 'attack'">Schema 驱动动态表单（字段/默认值/校验/依赖显示）</p>
          <p class="text-sm text-gray-500 mt-1" v-else>外部数据集评估参数配置</p>
        </div>
      </div>
      <div class="flex items-center gap-2 text-xs text-gray-500">
        <el-icon><Setting /></el-icon>
        <span v-if="strategy.mode === 'attack'">Attack Config</span>
        <span v-else>External Dataset Config</span>
      </div>
    </div>

    <div class="form-content space-y-4">
      <!-- 对抗算法模式参数配置 -->
      <div v-if="strategy.mode === 'attack'">
        <!-- 当前策略概览 -->
        <div class="p-4 bg-indigo-50 border border-indigo-200 rounded-lg mb-6">
          <div class="flex items-center justify-between mb-3">
            <div class="font-semibold text-indigo-900">当前评估策略</div>
            <el-tag type="primary" size="small">对抗攻击模式</el-tag>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <div class="text-xs text-indigo-600 mb-1">威胁模型</div>
              <div class="font-medium text-indigo-900">{{ strategy.threatModel === 'whitebox' ? '白盒攻击' : '黑盒攻击' }}</div>
            </div>
            <div>
              <div class="text-xs text-indigo-600 mb-1">攻击方法数量</div>
              <div class="font-medium text-indigo-900">{{ enabledAttacks.length }} 个已启用</div>
            </div>
            <div>
              <div class="text-xs text-indigo-600 mb-1">参数总数</div>
              <div class="font-medium text-indigo-900">{{ totalParameterCount }} 个参数</div>
            </div>
          </div>
        </div>

        <!-- 攻击方法参数配置 -->
        <div v-if="enabledAttacks.length === 0" class="p-4 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-500">
          请先在"策略选择"中添加并启用攻击方法，以显示对应参数配置界面。
        </div>

        <div v-else class="space-y-6">
          <!-- 攻击方法标签页 -->
          <div class="border-b border-gray-200">
            <div class="flex space-x-8 overflow-x-auto">
              <button
                v-for="(attack, index) in enabledAttacks"
                :key="attack.attackId"
                @click="activeAttackIndex = index"
                :class="[
                  'py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap',
                  activeAttackIndex === index
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                ]"
              >
                {{ attack.name }}
                <el-tag v-if="attack.params && Object.keys(attack.params).length > 0" size="small" type="info" class="ml-2">
                  {{ Object.keys(attack.params).length }}参数
                </el-tag>
              </button>
            </div>
          </div>

          <!-- 当前攻击方法参数表单 -->
          <div v-if="currentAttack" class="space-y-4">
            <div class="p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <div class="flex items-center justify-between">
                <div class="font-semibold text-gray-900">{{ currentSchema.title }}</div>
                <div class="flex items-center gap-2">
                  <el-tag size="small" type="primary">{{ currentAttack.mode }}</el-tag>
                  <el-button @click="resetCurrentParams" size="small" plain>重置默认</el-button>
                  <el-button @click="validateCurrentParams" size="small" type="success" plain>参数校验</el-button>
                </div>
              </div>
              <div class="text-xs text-gray-600 mt-1">调整参数后将自动保存到攻击配置中</div>
            </div>

            <!-- 参数表单网格 -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <template v-for="field in currentSchema.fields" :key="field.key">
                <div v-if="isFieldVisible(field)" class="parameter-field">
                  <div class="p-4 bg-white rounded-lg border border-gray-200 hover:border-indigo-300 transition-colors">
                    <!-- 参数标题 -->
                    <div class="flex items-start justify-between mb-3">
                      <div class="flex-1">
                        <label class="text-sm font-medium text-gray-700">{{ field.label }}</label>
                        <span v-if="field.unit" class="text-xs text-gray-500 ml-2">{{ field.unit }}</span>
                      </div>
                      <div class="flex items-center gap-1">
                        <el-tooltip v-if="field.help" :content="field.help" placement="top" :width="300">
                          <el-icon class="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-help"><QuestionFilled /></el-icon>
                        </el-tooltip>
                        <span v-if="isFieldRequired(field)" class="text-red-500 text-xs">*</span>
                      </div>
                    </div>

                    <!-- 数字类型参数 -->
                    <template v-if="field.type === 'number'">
                      <div class="space-y-3">
                        <div class="flex items-center gap-3">
                          <el-input-number
                            v-model="localParameters[currentAttack.attackId][field.key]"
                            :min="field.min"
                            :max="field.max"
                            :step="field.step"
                            :precision="getNumberPrecision(field.step)"
                            size="default"
                            class="w-32"
                            @change="onParameterChange"
                          />
                          <div class="flex-1">
                            <el-slider
                              v-model="localParameters[currentAttack.attackId][field.key]"
                              :min="field.min"
                              :max="field.max"
                              :step="field.step"
                              :show-tooltip="true"
                              @change="onParameterChange"
                            />
                          </div>
                        </div>
                        <div class="flex justify-between text-xs text-gray-500">
                          <span>最小值: {{ field.min }}</span>
                          <span>默认值: {{ field.default }}</span>
                          <span>最大值: {{ field.max }}</span>
                        </div>
                      </div>
                    </template>

                    <!-- 枚举类型参数 -->
                    <template v-else-if="field.type === 'enum'">
                      <el-select 
                        v-model="localParameters[currentAttack.attackId][field.key]"
                        class="w-full"
                        @change="onParameterChange"
                      >
                        <el-option
                          v-for="option in field.options"
                          :key="option"
                          :value="option"
                          :label="option"
                        />
                      </el-select>
                      <div class="mt-2 text-xs text-gray-500">
                        可选值: {{ field.options.join(', ') }}
                      </div>
                    </template>

                    <!-- 布尔类型参数 -->
                    <template v-else-if="field.type === 'boolean'">
                      <div class="flex items-center justify-between">
                        <div class="flex items-center gap-3">
                          <el-switch 
                            v-model="localParameters[currentAttack.attackId][field.key]"
                            @change="onParameterChange"
                          />
                          <span class="text-sm text-gray-600">
                            {{ localParameters[currentAttack.attackId][field.key] ? '开启' : '关闭' }}
                          </span>
                        </div>
                        <div class="text-xs text-gray-500">
                          默认: {{ field.default ? '开启' : '关闭' }}
                        </div>
                      </div>
                    </template>

                    <!-- 字符串类型参数 -->
                    <template v-else>
                      <el-input 
                        v-model="localParameters[currentAttack.attackId][field.key]"
                        :placeholder="field.default?.toString() || '请输入' + field.label"
                        @input="onParameterChange"
                      />
                    </template>

                    <!-- 参数帮助信息 -->
                    <div v-if="field.help" class="mt-3 p-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-700">
                      <el-icon class="w-3 h-3 inline mr-1"><InfoFilled /></el-icon>
                      {{ field.help }}
                    </div>
                  </div>
                </div>
              </template>
            </div>

            <!-- 参数预览 -->
            <div class="p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <div class="flex items-center justify-between mb-3">
                <h4 class="font-semibold text-gray-900">参数预览</h4>
                <div class="flex gap-2">
                  <el-button @click="exportCurrentParams" size="small" plain>
                    <el-icon class="mr-1"><Download /></el-icon>
                    导出JSON
                  </el-button>
                  <el-button @click="importCurrentParams" size="small" plain>
                    <el-icon class="mr-1"><Upload /></el-icon>
                    导入JSON
                  </el-button>
                </div>
              </div>
              <div class="bg-gray-900 text-green-400 p-3 rounded font-mono text-sm overflow-x-auto">
                <pre>{{ JSON.stringify(localParameters[currentAttack.attackId] || {}, null, 2) }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 外部数据集模式参数配置 -->
      <div v-else>
        <div class="p-4 bg-emerald-50 border border-emerald-200 rounded-lg mb-6">
          <div class="flex items-center justify-between">
            <div class="font-semibold text-emerald-900">外部数据集评估参数</div>
            <el-tag type="success" size="small">外部数据集模式</el-tag>
          </div>
          <div class="text-xs text-emerald-700 mt-1">配置外部数据集的评估参数</div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- 评估配置 -->
          <div class="space-y-4">
            <div class="p-4 bg-white rounded-lg border border-gray-200">
              <h4 class="font-medium text-gray-900 mb-4">评估配置</h4>
              
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">批次大小</label>
                  <div class="flex items-center gap-3">
                    <el-input-number 
                      v-model="localParameters.external.batchSize"
                      :min="1" 
                      :max="512" 
                      :step="1"
                      class="w-32"
                    />
                    <el-slider
                      v-model="localParameters.external.batchSize"
                      :min="1"
                      :max="512"
                      :step="1"
                      class="flex-1"
                    />
                  </div>
                  <div class="text-xs text-gray-500 mt-2">较大的批次大小可提高评估效率，但会消耗更多内存</div>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">评估样本数</label>
                  <el-select v-model="localParameters.external.sampleCount" class="w-full">
                    <el-option value="all" label="全部样本" />
                    <el-option value="1000" label="1000个样本" />
                    <el-option value="500" label="500个样本" />
                    <el-option value="100" label="100个样本" />
                  </el-select>
                  <div class="text-xs text-gray-500 mt-2">选择用于评估的样本数量</div>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">置信度阈值</label>
                  <div class="flex items-center gap-3">
                    <el-input-number 
                      v-model="localParameters.external.confidenceThreshold"
                      :min="0.0" 
                      :max="1.0" 
                      :step="0.01"
                      :precision="2"
                      class="w-32"
                    />
                    <el-slider
                      v-model="localParameters.external.confidenceThreshold"
                      :min="0.0"
                      :max="1.0"
                      :step="0.01"
                      class="flex-1"
                    />
                  </div>
                  <div class="text-xs text-gray-500 mt-2">预测置信度低于此值视为不确定</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 数据处理配置 -->
          <div class="space-y-4">
            <div class="p-4 bg-white rounded-lg border border-gray-200">
              <h4 class="font-medium text-gray-900 mb-4">数据处理</h4>
              
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">数据预处理</label>
                  <el-select v-model="localParameters.external.preprocessing" class="w-full">
                    <el-option value="auto" label="自动匹配模型要求" />
                    <el-option value="normalize" label="归一化处理" />
                    <el-option value="resize" label="调整尺寸" />
                    <el-option value="none" label="不预处理" />
                  </el-select>
                  <div class="text-xs text-gray-500 mt-2">确保外部数据与模型输入格式兼容</div>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">数据增强</label>
                  <div class="space-y-2">
                    <el-checkbox v-model="localParameters.external.augmentation.enabled">启用数据增强</el-checkbox>
                    <div v-if="localParameters.external.augmentation.enabled" class="ml-6 space-y-2">
                      <el-checkbox v-model="localParameters.external.augmentation.rotation">旋转</el-checkbox>
                      <el-checkbox v-model="localParameters.external.augmentation.flip">翻转</el-checkbox>
                      <el-checkbox v-model="localParameters.external.augmentation.noise">噪声</el-checkbox>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="p-4 bg-white rounded-lg border border-gray-200">
              <h4 class="font-medium text-gray-900 mb-4">高级选项</h4>
              <div class="space-y-3 text-sm text-gray-700">
                <el-checkbox v-model="localParameters.external.saveErrorSamples">保存错误样本以供分析</el-checkbox>
                <el-checkbox v-model="localParameters.external.perClassMetrics">计算每个类别的指标</el-checkbox>
                <el-checkbox v-model="localParameters.external.confusionMatrix">生成混淆矩阵</el-checkbox>
                <el-checkbox v-model="localParameters.external.compareGolden">与黄金数据集自动对比</el-checkbox>
              </div>
            </div>
          </div>
        </div>

        <!-- 外部数据集参数预览 -->
        <div class="p-4 bg-gray-50 border border-gray-200 rounded-lg mt-6">
          <div class="flex items-center justify-between mb-3">
            <h4 class="font-semibold text-gray-900">配置预览</h4>
            <el-button @click="exportExternalParams" size="small" plain>
              <el-icon class="mr-1"><Download /></el-icon>
              导出配置
            </el-button>
          </div>
          <div class="bg-gray-900 text-green-400 p-3 rounded font-mono text-sm overflow-x-auto">
            <pre>{{ JSON.stringify(localParameters.external || {}, null, 2) }}</pre>
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
      <el-button @click="$emit('next')" type="primary" :disabled="!hasValidParameters">
        下一步：指标与输出
        <el-icon class="ml-2"><ArrowRight /></el-icon>
      </el-button>
    </div>

    <!-- 参数导入对话框 -->
    <el-dialog v-model="importDialogVisible" title="导入参数配置" width="50%">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">粘贴JSON配置</label>
          <el-input
            v-model="importJsonText"
            type="textarea"
            :rows="10"
            placeholder="请粘贴JSON格式的参数配置..."
            class="font-mono"
          />
        </div>
        <div v-if="importError" class="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
          <el-icon class="mr-1"><WarningFilled /></el-icon>
          {{ importError }}
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <el-button @click="importDialogVisible = false">取消</el-button>
          <el-button @click="confirmImportParams" type="primary">导入</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Setting,
  QuestionFilled,
  InfoFilled,
  Download,
  Upload,
  ArrowLeft,
  ArrowRight,
  WarningFilled
} from '@element-plus/icons-vue'

interface Props {
  modelValue: any
  strategy: {
    mode: string
    threatModel: string
    attacks: any[]
    externalDataset: any
  }
}

interface Emits {
  (e: 'update:modelValue', value: any): void
  (e: 'prev'): void
  (e: 'next'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 本地参数数据
const localParameters = ref<any>({
  external: {
    batchSize: 32,
    sampleCount: 'all',
    confidenceThreshold: 0.5,
    preprocessing: 'auto',
    augmentation: {
      enabled: false,
      rotation: false,
      flip: false,
      noise: false
    },
    saveErrorSamples: true,
    perClassMetrics: true,
    confusionMatrix: false,
    compareGolden: true
  },
  ...props.modelValue
})

// 状态管理
const activeAttackIndex = ref(0)
const importDialogVisible = ref(false)
const importJsonText = ref('')
const importError = ref('')

// Mock 参数 Schema（与策略选择模块一致）
const mockSchemas: Record<string, any> = {
  'fgsm': {
    title: 'FGSM 参数配置',
    fields: [
      { key: 'epsilon', label: '扰动预算 ε', type: 'number', min: 0.0, max: 0.3, step: 0.001, default: 0.031, unit: '（归一化空间）', help: '控制对抗扰动的最大幅度。较大的ε会产生更强的攻击效果，但扰动更明显。典型值：8/255≈0.031，适用于图像攻击', required: true },
      { key: 'norm', label: '范数约束', type: 'enum', options: ['linf'], default: 'linf', help: '定义扰动的度量方式。L∞范数限制每个像素的最大变化量，FGSM通常使用L∞范数' },
      { key: 'clamp', label: '输入裁剪', type: 'enum', options: ['[0,1]', '[-1,1]', 'none'], default: '[0,1]', help: '将对抗样本限制在有效范围内。[0,1]适用于归一化后的图像，[-1,1]适用于某些预处理方式，none表示不裁剪' },
      { key: 'targeted', label: '目标攻击', type: 'boolean', default: false, help: '是否执行目标攻击。开启时，攻击会尝试让模型将样本误分类为指定的目标类别；关闭时为无目标攻击，只要让模型分类错误即可' },
      { key: 'target_class', label: '目标类别', type: 'number', min: 0, max: 999, step: 1, default: 0, visible_if: { key: 'targeted', equals: true }, help: '目标攻击时要误导模型预测的类别ID。仅在开启目标攻击时生效' },
      { key: 'seed', label: '随机种子', type: 'number', min: 0, max: 999999, step: 1, default: 42, help: '用于保证实验可复现性。相同的种子会产生相同的随机初始化和攻击结果' },
    ]
  },
  'pgd': {
    title: 'PGD 参数配置',
    fields: [
      { key: 'epsilon', label: '扰动预算 ε', type: 'number', min: 0.0, max: 0.3, step: 0.001, default: 0.031, unit: '（归一化空间）', help: '控制对抗扰动的最大幅度。PGD会在ε约束的球内进行多步迭代优化。典型值：8/255≈0.031', required: true },
      { key: 'norm', label: '范数约束', type: 'enum', options: ['linf','l2'], default: 'linf', help: '定义扰动空间的约束方式。L∞限制每个特征的最大变化，L2限制扰动的欧氏距离' },
      { key: 'steps', label: '迭代步数', type: 'number', min: 1, max: 200, step: 1, default: 20, help: 'PGD算法的迭代次数。更多步数通常能找到更强的对抗样本，但计算时间也更长。典型值：10-50步' },
      { key: 'alpha', label: '步长 α', type: 'number', min: 0.0, max: 0.1, step: 0.0005, default: 0.007, help: '每次迭代的步长大小。过大可能导致震荡，过小则收敛慢。常用设置：α≈ε/steps 或 2/255≈0.007' },
      { key: 'restarts', label: '随机重启', type: 'number', min: 1, max: 50, step: 1, default: 1, help: '从不同随机初始点开始攻击的次数。多次重启可以提高找到最优对抗样本的概率，但会增加计算成本' },
      { key: 'early_stop', label: '成功早停', type: 'boolean', default: true, help: '是否在攻击成功后立即停止迭代。开启可节省计算时间，关闭则会完成所有迭代步数' },
      { key: 'clamp', label: '输入裁剪', type: 'enum', options: ['[0,1]', '[-1,1]', 'none'], default: '[0,1]', help: '将对抗样本限制在有效范围内。确保生成的样本在合理的数值区间内' },
      { key: 'seed', label: '随机种子', type: 'number', min: 0, max: 999999, step: 1, default: 42, help: '控制随机初始化和重启的随机性，确保实验可复现' },
    ]
  },
  'cw': {
    title: 'C&W 参数配置',
    fields: [
      { key: 'confidence', label: '置信度', type: 'number', min: 0, max: 50, step: 1, default: 0, help: '攻击置信度参数，影响对抗样本的强度' },
      { key: 'learning_rate', label: '学习率', type: 'number', min: 0.001, max: 1.0, step: 0.001, default: 0.01, help: '优化算法的学习率' },
      { key: 'max_iterations', label: '最大迭代次数', type: 'number', min: 100, max: 10000, step: 100, default: 1000, help: '最大优化迭代次数' },
      { key: 'targeted', label: '目标攻击', type: 'boolean', default: false, help: '是否执行目标攻击' },
    ]
  },
  'square': {
    title: 'Square Attack 参数配置',
    fields: [
      { key: 'epsilon', label: '扰动预算 ε', type: 'number', min: 0.0, max: 0.3, step: 0.001, default: 0.031, help: '对抗扰动的最大幅度。Square Attack是黑盒攻击，通过随机方形扰动搜索对抗样本' },
      { key: 'queries', label: '查询预算', type: 'number', min: 100, max: 50000, step: 50, default: 5000, help: '允许查询模型的最大次数。黑盒攻击通过多次查询来估计梯度，查询次数越多攻击越强，但耗时也越长' },
      { key: 'p_init', label: '初始扰动比例 p_init', type: 'number', min: 0.001, max: 0.5, step: 0.001, default: 0.1, help: '初始方形扰动覆盖的像素比例。算法会自适应调整该比例以平衡探索和利用' },
      { key: 'seed', label: '随机种子', type: 'number', min: 0, max: 999999, step: 1, default: 42, help: '控制随机扰动生成的随机性，确保实验可复现' },
    ]
  },
  'textfooler': {
    title: 'TextFooler 参数配置',
    fields: [
      { key: 'max_changes', label: '最大替换比例', type: 'number', min: 0.01, max: 0.5, step: 0.01, default: 0.15, unit: '（比例）', help: '允许替换的词语占总词数的最大比例。较小值保持文本语义，较大值攻击更强但可能影响语义。建议0.1-0.2' },
      { key: 'similarity', label: '语义相似度阈值', type: 'number', min: 0.5, max: 0.99, step: 0.01, default: 0.85, help: '替换词与原词的语义相似度下限。数值越高，替换词与原词越相似，对抗文本语义保持越好。建议0.8-0.9' },
      { key: 'topk', label: '候选词 Top-K', type: 'number', min: 5, max: 200, step: 5, default: 50, help: '为每个词选择的候选替换词数量。更多候选词能提高攻击成功率，但会增加计算时间' },
      { key: 'seed', label: '随机种子', type: 'number', min: 0, max: 999999, step: 1, default: 42, help: '控制词语选择和替换的随机性，确保实验可复现' },
    ]
  }
}

// 计算属性
const enabledAttacks = computed(() => {
  return props.strategy.attacks?.filter(attack => attack.enabled) || []
})

const currentAttack = computed(() => {
  return enabledAttacks.value[activeAttackIndex.value] || null
})

const currentSchema = computed(() => {
  if (!currentAttack.value) return { title: '', fields: [] }
  return mockSchemas[currentAttack.value.attackId] || { title: '', fields: [] }
})

const totalParameterCount = computed(() => {
  return enabledAttacks.value.reduce((total, attack) => {
    const schema = mockSchemas[attack.attackId]
    return total + (schema?.fields?.length || 0)
  }, 0)
})

const hasValidParameters = computed(() => {
  if (props.strategy.mode === 'attack') {
    return enabledAttacks.value.length > 0 && Object.keys(localParameters.value).some(key => key !== 'external')
  } else {
    return localParameters.value.external && Object.keys(localParameters.value.external).length > 0
  }
})

// 方法
const initializeAttackParameters = () => {
  enabledAttacks.value.forEach(attack => {
    if (!localParameters.value[attack.attackId]) {
      localParameters.value[attack.attackId] = {}
    }
    
    const schema = mockSchemas[attack.attackId]
    if (schema?.fields) {
      schema.fields.forEach((field: any) => {
        if (localParameters.value[attack.attackId][field.key] === undefined) {
          localParameters.value[attack.attackId][field.key] = field.default
        }
      })
    }
  })
}

const isFieldVisible = (field: any): boolean => {
  if (!field.visible_if || !currentAttack.value) return true
  const { key, equals } = field.visible_if
  return localParameters.value[currentAttack.value.attackId][key] === equals
}

const isFieldRequired = (field: any): boolean => {
  return field.required === true
}

const getNumberPrecision = (step: number): number => {
  if (step >= 1) return 0
  if (step >= 0.1) return 1
  if (step >= 0.01) return 2
  return 3
}

const onParameterChange = () => {
  // 触发父组件���新
  emit('update:modelValue', localParameters.value)
  
  // 同步更新到strategy中的attacks参数
  if (currentAttack.value) {
    const attackIndex = props.strategy.attacks.findIndex(a => a.attackId === currentAttack.value.attackId)
    if (attackIndex >= 0) {
      props.strategy.attacks[attackIndex].params = { ...localParameters.value[currentAttack.value.attackId] }
    }
  }
}

const resetCurrentParams = () => {
  if (!currentAttack.value) return
  
  const schema = currentSchema.value
  if (schema.fields) {
    const resetParams: any = {}
    schema.fields.forEach((field: any) => {
      resetParams[field.key] = field.default
    })
    localParameters.value[currentAttack.value.attackId] = resetParams
    onParameterChange()
    ElMessage.success(`已重置 ${currentAttack.value.name} 参数为默认值`)
  }
}

const validateCurrentParams = () => {
  if (!currentAttack.value) return
  
  const schema = currentSchema.value
  const params = localParameters.value[currentAttack.value.attackId]
  let errors: string[] = []
  
  schema.fields?.forEach((field: any) => {
    const value = params[field.key]
    
    if (field.required && (value === undefined || value === null || value === '')) {
      errors.push(`${field.label} 为必填项`)
    }
    
    if (field.type === 'number' && value !== undefined) {
      if (value < field.min || value > field.max) {
        errors.push(`${field.label} 应在 ${field.min} ~ ${field.max} 范围内`)
      }
    }
  })
  
  if (errors.length > 0) {
    ElMessage.error(`参数验证失败：${errors.join('；')}`)
  } else {
    ElMessage.success(`${currentAttack.value.name} 参数验证通过`)
  }
}

const exportCurrentParams = () => {
  if (!currentAttack.value) return
  
  const params = localParameters.value[currentAttack.value.attackId]
  const json = JSON.stringify(params, null, 2)
  
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${currentAttack.value.name}-params.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  
  ElMessage.success('参数已导出')
}

const importCurrentParams = () => {
  importJsonText.value = ''
  importError.value = ''
  importDialogVisible.value = true
}

const confirmImportParams = () => {
  try {
    const params = JSON.parse(importJsonText.value)
    if (!currentAttack.value) return
    
    localParameters.value[currentAttack.value.attackId] = { ...params }
    onParameterChange()
    
    importDialogVisible.value = false
    ElMessage.success('参数导入成功')
  } catch (error) {
    importError.value = '无效的JSON格式，请检查输入内容'
  }
}

const exportExternalParams = () => {
  const json = JSON.stringify(localParameters.value.external, null, 2)
  
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'external-dataset-params.json'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  
  ElMessage.success('外部数据集参数已导出')
}

// 监听数据变化
watch(localParameters, (newVal) => {
  emit('update:modelValue', newVal)
}, { deep: true })

watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    localParameters.value = { ...localParameters.value, ...newVal }
  }
}, { deep: true })

watch(() => props.strategy.attacks, () => {
  initializeAttackParameters()
}, { deep: true, immediate: true })

// 切换攻击方法时重置索引
watch(enabledAttacks, (newVal) => {
  if (activeAttackIndex.value >= newVal.length) {
    activeAttackIndex.value = Math.max(0, newVal.length - 1)
  }
}, { immediate: true })
</script>

<style lang="scss" scoped>
.parameter-config {
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

.parameter-field {
  .hover\:border-indigo-300:hover {
    border-color: rgb(165 180 252);
  }
}

// Tailwind-like classes (保持之前的样式)
.flex { display: flex; }
.items-center { align-items: center; }
.items-start { align-items: flex-start; }
.justify-between { justify-content: space-between; }
.justify-end { justify-content: flex-end; }
.gap-1 { gap: 0.25rem; }
.gap-2 { gap: 0.5rem; }
.gap-3 { gap: 0.75rem; }
.gap-4 { gap: 1rem; }
.gap-6 { gap: 1.5rem; }
.w-3 { width: 0.75rem; }
.h-3 { height: 0.75rem; }
.w-4 { width: 1rem; }
.h-4 { height: 1rem; }
.w-7 { width: 1.75rem; }
.h-7 { height: 1.75rem; }
.w-32 { width: 8rem; }
.rounded-lg { border-radius: 0.5rem; }
.bg-indigo-600 { background-color: rgb(79 70 229); }
.bg-indigo-50 { background-color: rgb(238 242 255); }
.bg-emerald-50 { background-color: rgb(236 253 245); }
.bg-gray-50 { background-color: rgb(249 250 251); }
.bg-gray-900 { background-color: rgb(17 24 39); }
.bg-white { background-color: rgb(255 255 255); }
.bg-blue-50 { background-color: rgb(239 246 255); }
.text-white { color: rgb(255 255 255); }
.text-gray-900 { color: rgb(17 24 39); }
.text-gray-700 { color: rgb(55 65 81); }
.text-gray-600 { color: rgb(75 85 99); }
.text-gray-500 { color: rgb(107 114 128); }
.text-gray-400 { color: rgb(156 163 175); }
.text-indigo-900 { color: rgb(49 46 129); }
.text-indigo-600 { color: rgb(79 70 229); }
.text-indigo-500 { color: rgb(99 102 241); }
.text-emerald-900 { color: rgb(6 78 59); }
.text-emerald-700 { color: rgb(4 120 87); }
.text-green-400 { color: rgb(74 222 128); }
.text-blue-700 { color: rgb(29 78 216); }
.text-red-500 { color: rgb(239 68 68); }
.text-red-700 { color: rgb(185 28 28); }
.text-sm { font-size: 0.875rem; }
.text-xs { font-size: 0.75rem; }
.font-bold { font-weight: 700; }
.font-semibold { font-weight: 600; }
.font-medium { font-weight: 500; }
.font-mono { font-family: ui-monospace, SFMono-Regular, 'SF Mono', monospace; }
.shadow { box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1); }
.border { border-width: 1px; }
.border-2 { border-width: 2px; }
.border-b { border-bottom-width: 1px; }
.border-b-2 { border-bottom-width: 2px; }
.border-transparent { border-color: transparent; }
.border-gray-200 { border-color: rgb(229 231 235); }
.border-gray-300 { border-color: rgb(209 213 219); }
.border-indigo-200 { border-color: rgb(199 210 254); }
.border-indigo-500 { border-color: rgb(99 102 241); }
.border-emerald-200 { border-color: rgb(187 247 208); }
.border-blue-200 { border-color: rgb(191 219 254); }
.border-red-200 { border-color: rgb(254 202 202); }
.p-2 { padding: 0.5rem; }
.p-3 { padding: 0.75rem; }
.p-4 { padding: 1rem; }
.px-1 { padding-left: 0.25rem; padding-right: 0.25rem; }
.py-2 { padding-top: 0.5rem; padding-bottom: 0.5rem; }
.mb-1 { margin-bottom: 0.25rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-3 { margin-bottom: 0.75rem; }
.mb-4 { margin-bottom: 1rem; }
.mb-6 { margin-bottom: 1.5rem; }
.mt-1 { margin-top: 0.25rem; }
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 0.75rem; }
.mt-6 { margin-top: 1.5rem; }
.mr-1 { margin-right: 0.25rem; }
.mr-2 { margin-right: 0.5rem; }
.ml-1 { margin-left: 0.25rem; }
.ml-2 { margin-left: 0.5rem; }
.ml-6 { margin-left: 1.5rem; }
.space-y-2 > * + * { margin-top: 0.5rem; }
.space-y-3 > * + * { margin-top: 0.75rem; }
.space-y-4 > * + * { margin-top: 1rem; }
.space-y-6 > * + * { margin-top: 1.5rem; }
.space-x-8 > * + * { margin-left: 2rem; }
.grid { display: grid; }
.grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.text-center { text-align: center; }
.cursor-help { cursor: help; }
.transition-colors { transition-property: color, background-color, border-color, text-decoration-color, fill, stroke; }
.overflow-hidden { overflow: hidden; }
.overflow-x-auto { overflow-x: auto; }
.block { display: block; }
.inline { display: inline; }
.flex-1 { flex: 1 1 0%; }
.whitespace-nowrap { white-space: nowrap; }
.w-full { width: 100%; }

// 响应式
@media (min-width: 768px) {
  .md\:grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}

@media (min-width: 1024px) {
  .lg\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

// 悬停效果
.hover\:text-gray-700:hover { color: rgb(55 65 81); }
.hover\:text-gray-600:hover { color: rgb(75 85 99); }
.hover\:border-gray-300:hover { border-color: rgb(209 213 219); }
</style>

## 功能特点总结

现在"参数配置"模块已经完全恢复HTML的复杂功能，包括：

### ✅ 完整功能列表：

1. **动态参数表单** - 根据攻击方法自动生成参数配置界面
2. **多攻击方法Tab** - 支持切换不同攻击方法的参数配置
3. **丰富的参数类型** - 数字滑块、枚举选择、布尔开关、文本输入
4. **智能参数验证** - 必填项检查、数值范围验证、依赖显示
5. **参数预览和导出** - JSON格式预览、导出导入功能
6. **外部数据集配置** - 完整的数据集评估参数界面
7. **实时同步** - 参数变化实时同步到策略配置

### ✅ 交互功能：

- 参数Tab页切换
- 数字参数滑块调节
- 参数重置和校验
- JSON导入导出
- 实时参数预览
- 帮助提示和说明

### ✅ Schema驱动：

- 动态表单生成
- 参数类型自适应
- 条件显示字段
- 参数依赖管理
- 默认值和约束

现在可以测试这个模块的完整功能了！继续下一个模块"指标与输出"吗？
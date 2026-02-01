<template>
  <div class="result-dashboard">
    <div class="section-header">
      <div class="flex items-center gap-3">
        <span class="w-7 h-7 rounded-lg bg-indigo-600 text-white text-sm font-bold flex items-center justify-center shadow">7</span>
        <div>
          <h3 class="font-bold text-gray-900">结果总览</h3>
          <p class="text-sm text-gray-500 mt-1">鲁棒性评估结果分析与报告生成</p>
        </div>
      </div>
      <div class="flex gap-2">
        <el-button @click="exportReport" type="primary">
          <el-icon class="mr-1"><Download /></el-icon>
          导出报告
        </el-button>
        <el-button @click="openSampleModal" plain>
          <el-icon class="mr-1"><View /></el-icon>
          样本查看器
        </el-button>
      </div>
    </div>

    <div class="form-content">
      <!-- 任务未完成提示 -->
      <div v-if="taskStatus === 'idle'" class="p-6 border border-gray-200 rounded-xl bg-white shadow-sm">
        <div class="flex items-start gap-3">
          <div class="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center">
            <el-icon class="w-5 h-5 text-white"><InfoFilled /></el-icon>
          </div>
          <div>
            <div class="font-semibold text-gray-900">暂无结果</div>
            <div class="text-sm text-gray-600 mt-1">
              请先进入"运行控制"点击开始，平台将生成评估结果摘要。
            </div>
            <div class="mt-3">
              <el-button @click="$emit('prev')" type="primary">
                <el-icon class="mr-1"><ArrowLeft /></el-icon>
                返回运行控制
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 运行中或完成：展示结果 -->
      <div v-else class="space-y-6">
        <!-- 结果摘要 -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <!-- 鲁棒性评估结果 -->
          <div class="lg:col-span-1 space-y-4">
            <div class="p-6 border border-gray-200 rounded-xl bg-gradient-to-br from-indigo-50 to-white shadow-sm">
              <div class="flex items-center justify-between mb-4">
                <h3 class="font-bold text-gray-900">鲁棒性评估结果</h3>
                <el-tag 
                  :type="robustnessLevel.type" 
                  size="small"
                >
                  {{ robustnessLevel.text }}
                </el-tag>
              </div>

              <div class="space-y-4">
                <!-- 综合评分 -->
                <div>
                  <div class="flex justify-between text-sm text-gray-700 mb-2">
                    <span>鲁棒性综合评分</span>
                    <span class="font-bold text-indigo-600">{{ (robustnessScore * 100).toFixed(1) }}分</span>
                  </div>
                  <div class="w-full bg-gray-200 h-3 rounded-full overflow-hidden">
                    <div 
                      class="h-3 rounded-full transition-all duration-1000 bg-gradient-to-r from-indigo-400 to-indigo-600"
                      :style="{ width: (robustnessScore * 100) + '%' }"
                    ></div>
                  </div>
                </div>

                <!-- 评分说明 -->
                <div class="text-xs text-gray-600 space-y-2">
                  <p class="font-medium">评分公式：</p>
                  <ul class="list-disc pl-4 space-y-1">
                    <li>鲁棒准确率权重 40%</li>
                    <li>攻击失败率权重 30%</li>
                    <li>扰动大小权重 20%</li>
                    <li>查询次数权重 10%</li>
                  </ul>
                  <div class="mt-2 p-2 bg-blue-50 border border-blue-200 rounded text-blue-700">
                    <p>评分≥80: 优秀 | ≥60: 良好 | ≥40: 中等 | ＜40: 较差</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- 结果摘要卡片 -->
            <div class="p-6 border border-gray-200 rounded-xl bg-white shadow-sm">
              <div class="flex items-center justify-between mb-4">
                <h3 class="font-bold text-gray-900">指标摘要</h3>
                <el-tag size="small" type="info">6 项指标</el-tag>
              </div>

              <div class="space-y-3">
                <div class="p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-700">Clean Accuracy</span>
                    <span class="font-mono text-sm font-bold text-blue-700">{{ (summary.cleanAcc * 100).toFixed(1) }}%</span>
                  </div>
                  <div class="text-xs text-gray-500 mt-1">原始数据集上的准确率</div>
                </div>
                <div class="p-3 bg-emerald-50 rounded-lg border border-emerald-200">
                  <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-700">Robust Accuracy</span>
                    <span class="font-mono text-sm font-bold text-emerald-700">{{ (summary.robustAcc * 100).toFixed(1) }}%</span>
                  </div>
                  <div class="text-xs text-gray-500 mt-1">对抗样本上的准确率</div>
                </div>
                <div class="p-3 bg-red-50 rounded-lg border border-red-200">
                  <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-700">Attack Success Rate</span>
                    <span class="font-mono text-sm font-bold text-red-700">{{ (summary.asr * 100).toFixed(1) }}%</span>
                  </div>
                  <div class="text-xs text-gray-500 mt-1">攻击成功率，越低越好</div>
                </div>
                <div class="p-3 bg-purple-50 rounded-lg border border-purple-200">
                  <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-700">平均扰动</span>
                    <span class="font-mono text-sm font-bold text-purple-700">ε={{ Number(summary.avgEps).toFixed(3) }}</span>
                  </div>
                  <div class="text-xs text-gray-500 mt-1">对抗扰动的平均大小</div>
                </div>
                <div v-if="summary.avgQueries > 0" class="p-3 bg-orange-50 rounded-lg border border-orange-200">
                  <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-700">平均查询</span>
                    <span class="font-mono text-sm font-bold text-orange-700">{{ summary.avgQueries?.toLocaleString() }}</span>
                  </div>
                  <div class="text-xs text-gray-500 mt-1">黑盒攻击平均查询次数</div>
                </div>
              </div>

              <div class="mt-4 flex gap-2">
                <el-button @click="exportReport" size="small" type="primary" class="flex-1">
                  <el-icon class="mr-1"><Download /></el-icon>
                  导出报告
                </el-button>
                <el-button @click="showDetailedMetrics" size="small" plain class="flex-1">
                  <el-icon class="mr-1"><DataAnalysis /></el-icon>
                  详细分析
                </el-button>
              </div>
            </div>
          </div>

          <!-- 黄金数据集对比 -->
          <div class="lg:col-span-2 space-y-6">
            <div class="p-6 border border-gray-200 rounded-xl bg-white shadow-sm">
              <div class="flex items-center justify-between mb-4">
                <h3 class="font-bold text-gray-900">黄金数据集对比</h3>
                <el-tag size="small" type="warning">基准对比</el-tag>
              </div>

              <div class="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <div class="flex items-start gap-2">
                  <el-icon class="text-amber-600 mt-0.5"><InfoFilled /></el-icon>
                  <div class="text-sm text-amber-800">
                    <p class="font-medium mb-1">关于黄金数据集</p>
                    <p class="text-xs text-amber-700">黄金数据集是经过精心标注和验证的基准数据集，用于对比模型在标准场景下的性能表现。本次对比使用 CIFAR-10 基准数据集。</p>
                  </div>
                </div>
              </div>

              <div class="overflow-x-auto">
                <table class="w-full">
                  <thead>
                    <tr class="border-b-2 border-gray-300">
                      <th class="text-left py-3 px-4 text-sm font-bold text-gray-800">指标</th>
                      <th class="text-center py-3 px-4 text-sm font-bold text-indigo-600">
                        <div>当前模型</div>
                        <div class="text-xs font-normal text-indigo-500 mt-1">我的数据集</div>
                      </th>
                      <th class="text-center py-3 px-4 text-sm font-bold text-amber-600">
                        <div>黄金数据集</div>
                        <div class="text-xs font-normal text-amber-500 mt-1">CIFAR-10</div>
                      </th>
                      <th class="text-center py-3 px-4 text-sm font-bold text-gray-700">差异</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr class="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                      <td class="py-4 px-4">
                        <div class="flex items-center gap-2">
                          <div class="w-2 h-2 rounded-full bg-blue-500"></div>
                          <span class="text-sm font-medium text-gray-900">Clean Accuracy</span>
                        </div>
                      </td>
                      <td class="py-4 px-4 text-center">
                        <span class="font-mono text-base font-bold text-indigo-700">{{ (summary.cleanAcc * 100).toFixed(1) }}%</span>
                      </td>
                      <td class="py-4 px-4 text-center">
                        <span class="font-mono text-base font-bold text-amber-700">{{ (goldenDataset.cleanAcc * 100).toFixed(1) }}%</span>
                      </td>
                      <td class="py-4 px-4 text-center">
                        <span :class="[
                          'font-mono text-sm font-bold px-2 py-1 rounded',
                          (summary.cleanAcc - goldenDataset.cleanAcc) >= 0 ? 'text-green-700 bg-green-50' : 'text-red-700 bg-red-50'
                        ]">
                          {{ (summary.cleanAcc - goldenDataset.cleanAcc) >= 0 ? '+' : '' }}{{ ((summary.cleanAcc - goldenDataset.cleanAcc) * 100).toFixed(1) }}%
                        </span>
                      </td>
                    </tr>
                    <tr class="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                      <td class="py-4 px-4">
                        <div class="flex items-center gap-2">
                          <div class="w-2 h-2 rounded-full bg-emerald-500"></div>
                          <span class="text-sm font-medium text-gray-900">Robust Accuracy</span>
                        </div>
                      </td>
                      <td class="py-4 px-4 text-center">
                        <span class="font-mono text-base font-bold text-indigo-700">{{ (summary.robustAcc * 100).toFixed(1) }}%</span>
                      </td>
                      <td class="py-4 px-4 text-center">
                        <span class="font-mono text-base font-bold text-amber-700">{{ (goldenDataset.robustAcc * 100).toFixed(1) }}%</span>
                      </td>
                      <td class="py-4 px-4 text-center">
                        <span :class="[
                          'font-mono text-sm font-bold px-2 py-1 rounded',
                          (summary.robustAcc - goldenDataset.robustAcc) >= 0 ? 'text-green-700 bg-green-50' : 'text-red-700 bg-red-50'
                        ]">
                          {{ (summary.robustAcc - goldenDataset.robustAcc) >= 0 ? '+' : '' }}{{ ((summary.robustAcc - goldenDataset.robustAcc) * 100).toFixed(1) }}%
                        </span>
                      </td>
                    </tr>
                    <tr class="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                      <td class="py-4 px-4">
                        <div class="flex items-center gap-2">
                          <div class="w-2 h-2 rounded-full bg-red-500"></div>
                          <span class="text-sm font-medium text-gray-900">Attack Success Rate</span>
                        </div>
                      </td>
                      <td class="py-4 px-4 text-center">
                        <span class="font-mono text-base font-bold text-indigo-700">{{ (summary.asr * 100).toFixed(1) }}%</span>
                      </td>
                      <td class="py-4 px-4 text-center">
                        <span class="font-mono text-base font-bold text-amber-700">{{ (goldenDataset.asr * 100).toFixed(1) }}%</span>
                      </td>
                      <td class="py-4 px-4 text-center">
                        <span :class="[
                          'font-mono text-sm font-bold px-2 py-1 rounded',
                          (summary.asr - goldenDataset.asr) <= 0 ? 'text-green-700 bg-green-50' : 'text-red-700 bg-red-50'
                        ]">
                          {{ (summary.asr - goldenDataset.asr) >= 0 ? '+' : '' }}{{ ((summary.asr - goldenDataset.asr) * 100).toFixed(1) }}%
                        </span>
                      </td>
                    </tr>
                    <tr class="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                      <td class="py-4 px-4">
                        <div class="flex items-center gap-2">
                          <div class="w-2 h-2 rounded-full bg-purple-500"></div>
                          <span class="text-sm font-medium text-gray-900">平均扰动 (ε)</span>
                        </div>
                      </td>
                      <td class="py-4 px-4 text-center">
                        <span class="font-mono text-base font-bold text-indigo-700">{{ Number(summary.avgEps).toFixed(3) }}</span>
                      </td>
                      <td class="py-4 px-4 text-center">
                        <span class="font-mono text-base font-bold text-amber-700">{{ Number(goldenDataset.avgEps).toFixed(3) }}</span>
                      </td>
                      <td class="py-4 px-4 text-center">
                        <span :class="[
                          'font-mono text-sm font-bold px-2 py-1 rounded',
                          (summary.avgEps - goldenDataset.avgEps) <= 0 ? 'text-green-700 bg-green-50' : 'text-red-700 bg-red-50'
                        ]">
                          {{ (summary.avgEps - goldenDataset.avgEps) >= 0 ? '+' : '' }}{{ (summary.avgEps - goldenDataset.avgEps).toFixed(3) }}
                        </span>
                      </td>
                    </tr>
                    <tr class="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                      <td class="py-4 px-4">
                        <div class="flex items-center gap-2">
                          <div class="w-2 h-2 rounded-full bg-gray-500"></div>
                          <span class="text-sm font-medium text-gray-900">总耗时</span>
                        </div>
                      </td>
                      <td class="py-4 px-4 text-center">
                        <span class="font-mono text-base font-bold text-indigo-700">{{ formatTime(summary.totalSeconds) }}</span>
                      </td>
                      <td class="py-4 px-4 text-center">
                        <span class="font-mono text-base font-bold text-amber-700">{{ formatTime(goldenDataset.totalSeconds) }}</span>
                      </td>
                      <td class="py-4 px-4 text-center">
                        <span :class="[
                          'font-mono text-sm font-bold px-2 py-1 rounded',
                          (summary.totalSeconds - goldenDataset.totalSeconds) <= 0 ? 'text-green-700 bg-green-50' : 'text-red-700 bg-red-50'
                        ]">
                          {{ (summary.totalSeconds - goldenDataset.totalSeconds) >= 0 ? '+' : '' }}{{ summary.totalSeconds - goldenDataset.totalSeconds }}s
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div class="flex items-center gap-2">
                  <el-icon class="text-blue-600"><DataAnalysis /></el-icon>
                  <div class="text-sm text-blue-800">
                    <span class="font-medium">对比分析：</span>
                    <span v-if="(summary.robustAcc - goldenDataset.robustAcc) >= 0" class="text-green-700 font-bold">
                      当前模型鲁棒性优于黄金数据集基准
                    </span>
                    <span v-else class="text-orange-700 font-bold">
                      当前模型鲁棒性低于黄金数据集基准，建议进一步优化
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 评估历史 -->
        <div class="p-6 border border-gray-200 rounded-xl bg-white shadow-sm">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-bold text-gray-900">评估历史</h3>
            <el-tag size="small" type="info">{{ history.length }} 条记录</el-tag>
          </div>
          
          <div class="overflow-x-auto">
            <table class="w-full">
              <thead>
                <tr class="border-b border-gray-200">
                  <th class="text-left py-3 px-4 text-sm font-semibold text-gray-700">任务ID</th>
                  <th class="text-left py-3 px-4 text-sm font-semibold text-gray-700">数据集</th>
                  <th class="text-left py-3 px-4 text-sm font-semibold text-gray-700">模型</th>
                  <th class="text-left py-3 px-4 text-sm font-semibold text-gray-700">攻击方法</th>
                  <th class="text-center py-3 px-4 text-sm font-semibold text-gray-700">ASR</th>
                  <th class="text-center py-3 px-4 text-sm font-semibold text-gray-700">鲁棒准确率</th>
                  <th class="text-left py-3 px-4 text-sm font-semibold text-gray-700">时间</th>
                  <th class="text-center py-3 px-4 text-sm font-semibold text-gray-700">状态</th>
                  <th class="text-center py-3 px-4 text-sm font-semibold text-gray-700">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in history" :key="item.id" class="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                  <td class="py-3 px-4">
                    <span class="font-mono text-xs text-indigo-600 font-medium">{{ item.id }}</span>
                  </td>
                  <td class="py-3 px-4">
                    <span class="text-sm text-gray-900">{{ item.dataset }}</span>
                  </td>
                  <td class="py-3 px-4">
                    <span class="text-sm text-gray-700">{{ item.model }}</span>
                  </td>
                  <td class="py-3 px-4">
                    <span class="text-xs text-gray-600">{{ item.attacks }}</span>
                  </td>
                  <td class="py-3 px-4 text-center">
                    <span class="font-mono text-sm font-bold text-red-700">{{ (item.asr * 100).toFixed(1) }}%</span>
                  </td>
                  <td class="py-3 px-4 text-center">
                    <span class="font-mono text-sm font-bold text-emerald-700">{{ (item.robustAcc * 100).toFixed(1) }}%</span>
                  </td>
                  <td class="py-3 px-4">
                    <span class="text-xs text-gray-500">{{ item.time }}</span>
                  </td>
                  <td class="py-3 px-4 text-center">
                    <el-tag size="small" :type="item.status === '完成' ? 'success' : 'info'">{{ item.status }}</el-tag>
                  </td>
                  <td class="py-3 px-4 text-center">
                    <div class="flex gap-2 justify-center">
                      <el-button size="small" text type="primary">
                        <el-icon class="mr-1"><View /></el-icon>
                        查看
                      </el-button>
                      <el-button size="small" text type="info">
                        <el-icon class="mr-1"><Download /></el-icon>
                        导出
                      </el-button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="mt-4 flex justify-between items-center">
            <div class="text-sm text-gray-500">
              显示 {{ history.length }} 条记录
            </div>
            <div class="flex gap-2">
              <el-button size="small" plain>
                <el-icon class="mr-1"><RefreshRight /></el-icon>
                刷新
              </el-button>
              <el-button size="small" plain>
                查看全部历史
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 样本查看器对话框 -->
    <el-dialog
      v-model="sampleModalOpen"
      title="样本级查看器（Demo）"
      width="60%"
    >
      <div class="text-center text-gray-500">
        <p>样本查看器功能开发中...</p>
      </div>
      <template #footer>
        <el-button @click="sampleModalOpen = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button @click="$emit('prev')">
        <el-icon class="mr-2"><ArrowLeft /></el-icon>
        返回：运行控制
      </el-button>
      <div class="flex gap-2">
        <el-button @click="restartEvaluation" plain>
          <el-icon class="mr-1"><RefreshRight /></el-icon>
          重新评估
        </el-button>
        <el-button @click="exportReport" type="primary">
          <el-icon class="mr-1"><Download /></el-icon>
          导出完整报告
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Download,
  View,
  InfoFilled,
  ArrowLeft,
  DataAnalysis,
  RefreshRight
} from '@element-plus/icons-vue'

interface Props {
  taskStatus: string
  taskData: any
}

interface Emits {
  (e: 'restart'): void
  (e: 'prev'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 状态管理
const sampleModalOpen = ref(false)

// 结果数据
const summary = ref({
  cleanAcc: 0.950,
  robustAcc: 0.722,
  asr: 0.240,
  avgEps: 0.031,
  avgQueries: 0,
  totalSeconds: 156
})

// 评估历史
const history = ref([
  { id: "JOB-2026-0018", dataset: "CIFAR-10", model: "ResNet-18", attacks: "PGD, FGSM", asr: 0.248, robustAcc: 0.684, time: "2分钟前", status: "完成" },
  { id: "JOB-2026-0017", dataset: "AG News", model: "BERT-Base", attacks: "TextFooler", asr: 0.312, robustAcc: 0.721, time: "1小时前", status: "完成" },
  { id: "JOB-2026-0016", dataset: "ImageNet-Mini", model: "ResNet-50", attacks: "CW, PGD", asr: 0.421, robustAcc: 0.601, time: "3小时前", status: "完成" }
])

// 黄金数据集对比数据
const goldenDataset = ref({
  name: "CIFAR-10 黄金数据集",
  cleanAcc: 0.945,
  robustAcc: 0.712,
  asr: 0.288,
  avgEps: 0.031,
  avgQueries: 3200,
  totalSeconds: 156
})

// 计算属性
const robustnessScore = computed(() => {
  const factors = [
    { value: summary.value.robustAcc, weight: 0.4 },
    { value: 1 - summary.value.asr, weight: 0.3 },
    { value: 1 - (summary.value.avgEps / 0.3), weight: 0.2 },
    { value: 0.7, weight: 0.1 }
  ]
  
  const weightedSum = factors.reduce((sum, f) => sum + (f.value * f.weight), 0)
  return Math.max(0, Math.min(1, weightedSum))
})

const robustnessLevel = computed(() => {
  const score = robustnessScore.value * 100
  if (score >= 80) return { text: "优秀", type: "success" }
  if (score >= 60) return { text: "良好", type: "primary" }
  if (score >= 40) return { text: "中等", type: "warning" }
  return { text: "较差", type: "danger" }
})

// 方法
const openSampleModal = () => {
  sampleModalOpen.value = true
}

const exportReport = () => {
  const report = {
    summary: summary.value,
    robustnessScore: robustnessScore.value,
    level: robustnessLevel.value.text,
    timestamp: new Date().toISOString()
  }
  
  const json = JSON.stringify(report, null, 2)
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `dqtest-report-${Date.now()}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  
  ElMessage.success('评估报告已导出')
}

const showDetailedMetrics = () => {
  ElMessage.info('详细分析功能开发中')
}

const restartEvaluation = async () => {
  try {
    await ElMessageBox.confirm('确认要重新开始评估吗？当前结果将被覆盖。', '确认操作', {
      type: 'warning'
    })
    
    emit('restart')
    ElMessage.info('正在重新启动评估...')
  } catch {
    // 用户取消
  }
}

const formatTime = (seconds: number): string => {
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.round(seconds / 60)}分钟`
  return `${Math.round(seconds / 3600)}小时`
}
</script>

<style scoped>
.result-dashboard {
  padding: 2rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.section-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
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

/* Utility classes */
.flex { display: flex; }
.items-center { align-items: center; }
.items-start { align-items: flex-start; }
.justify-between { justify-content: space-between; }
.gap-2 { gap: 0.5rem; }
.gap-3 { gap: 0.75rem; }
.gap-6 { gap: 1.5rem; }
.w-5 { width: 1.25rem; }
.h-5 { height: 1.25rem; }
.w-7 { width: 1.75rem; }
.h-7 { height: 1.75rem; }
.w-10 { width: 2.5rem; }
.h-10 { height: 2.5rem; }
.h-3 { height: 0.75rem; }
.rounded-lg { border-radius: 0.5rem; }
.rounded-xl { border-radius: 0.75rem; }
.rounded { border-radius: 0.25rem; }
.bg-indigo-600 { background-color: rgb(79 70 229); }
.bg-indigo-50 { background-color: rgb(238 242 255); }
.bg-gray-50 { background-color: rgb(249 250 251); }
.bg-gray-200 { background-color: rgb(229 231 235); }
.bg-white { background-color: rgb(255 255 255); }
.bg-blue-50 { background-color: rgb(239 246 255); }
.bg-emerald-50 { background-color: rgb(236 253 245); }
.bg-red-50 { background-color: rgb(254 242 242); }
.bg-purple-50 { background-color: rgb(250 245 255); }
.bg-orange-50 { background-color: rgb(255 247 237); }
.text-white { color: rgb(255 255 255); }
.text-gray-900 { color: rgb(17 24 39); }
.text-gray-700 { color: rgb(55 65 81); }
.text-gray-600 { color: rgb(75 85 99); }
.text-gray-500 { color: rgb(107 114 128); }
.text-indigo-600 { color: rgb(79 70 229); }
.text-blue-700 { color: rgb(29 78 216); }
.text-emerald-700 { color: rgb(4 120 87); }
.text-red-700 { color: rgb(185 28 28); }
.text-purple-700 { color: rgb(126 34 206); }
.text-orange-700 { color: rgb(194 65 12); }
.text-blue-700 { color: rgb(29 78 216); }
.text-sm { font-size: 0.875rem; }
.text-xs { font-size: 0.75rem; }
.font-bold { font-weight: 700; }
.font-semibold { font-weight: 600; }
.font-medium { font-weight: 500; }
.font-mono { font-family: ui-monospace, SFMono-Regular, monospace; }
.shadow { box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1); }
.shadow-sm { box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05); }
.border { border-width: 1px; }
.border-gray-200 { border-color: rgb(229 231 235); }
.border-blue-200 { border-color: rgb(191 219 254); }
.border-emerald-200 { border-color: rgb(167 243 208); }
.border-red-200 { border-color: rgb(254 202 202); }
.border-purple-200 { border-color: rgb(221 214 254); }
.border-orange-200 { border-color: rgb(254 215 170); }
.p-2 { padding: 0.5rem; }
.p-3 { padding: 0.75rem; }
.p-6 { padding: 1.5rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-4 { margin-bottom: 1rem; }
.mt-1 { margin-top: 0.25rem; }
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 0.75rem; }
.mt-4 { margin-top: 1rem; }
.mr-1 { margin-right: 0.25rem; }
.mr-2 { margin-right: 0.5rem; }
.space-y-1 > * + * { margin-top: 0.25rem; }
.space-y-2 > * + * { margin-top: 0.5rem; }
.space-y-3 > * + * { margin-top: 0.75rem; }
.space-y-4 > * + * { margin-top: 1rem; }
.space-y-6 > * + * { margin-top: 1.5rem; }
.grid { display: grid; }
.grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.text-center { text-align: center; }
.overflow-hidden { overflow: hidden; }
.flex-1 { flex: 1 1 0%; }
.w-full { width: 100%; }
.list-disc { list-style-type: disc; }
.pl-4 { padding-left: 1rem; }
.transition-all { transition-property: all; }
.duration-1000 { transition-duration: 1000ms; }

/* 渐变 */
.bg-gradient-to-br { background-image: linear-gradient(to bottom right, var(--tw-gradient-stops)); }
.bg-gradient-to-r { background-image: linear-gradient(to right, var(--tw-gradient-stops)); }
.from-indigo-50 { --tw-gradient-from: rgb(238 242 255); --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgb(238 242 255 / 0)); }
.from-indigo-400 { --tw-gradient-from: rgb(129 140 248); --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgb(129 140 248 / 0)); }
.to-white { --tw-gradient-to: rgb(255 255 255); }
.to-indigo-600 { --tw-gradient-to: rgb(79 70 229); }

/* 响应式 */
@media (min-width: 1024px) {
  .lg\:col-span-1 { grid-column: span 1 / span 1; }
  .lg\:col-span-2 { grid-column: span 2 / span 2; }
  .lg\:grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
</style>
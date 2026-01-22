<!-- 数据集管理主页面 -->
<template>
  <div class="app-container dataset-management">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #e1f5fe">
              <el-icon :size="32" color="#0288d1">
                <DataBoard />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">总数据集</div>
              <div class="stat-value">{{ statistics.total_count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #e8f5e9">
              <el-icon :size="32" color="#388e3c">
                <CircleCheck />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">上传完成</div>
              <div class="stat-value">{{ statistics.completed_count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #fff3e0">
              <el-icon :size="32" color="#f57c00">
                <Loading />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">上传中</div>
              <div class="stat-value">{{ statistics.uploading_count }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #fce4ec">
              <el-icon :size="32" color="#c2185b">
                <FolderOpened />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">总存储</div>
              <div class="stat-value">{{ formatFileSize(statistics.total_size) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Tab 切换 -->
    <el-card shadow="hover" class="main-card">
      <el-tabs v-model="activeTab" type="border-card" class="dataset-tabs">
        <!-- 数据集上传 -->
        <el-tab-pane label="数据集上传" name="upload">
          <template #label>
            <span class="tab-label">
              <el-icon><Upload /></el-icon>
              数据集上传
            </span>
          </template>

          <div class="tab-content">
            <DatasetUpload
              v-if="activeTab === 'upload'"
              @upload-success="handleUploadSuccess"
              @upload-cancel="handleUploadCancel"
            />
          </div>
        </el-tab-pane>

        <!-- 数据集列表 -->
        <el-tab-pane label="数据集列表" name="list">
          <template #label>
            <span class="tab-label">
              <el-icon><List /></el-icon>
              数据集列表
            </span>
          </template>

          <div class="tab-content">
            <!-- 搜索和操作区域 -->
            <div class="search-container">
              <el-form
                ref="queryFormRef"
                :model="queryFormData"
                :inline="true"
                label-suffix=":"
                @submit.prevent="handleQuery"
              >
                <el-form-item prop="name" label="数据集名称">
                  <el-input
                    v-model="queryFormData.name"
                    placeholder="请输入数据集名称"
                    clearable
                  />
                </el-form-item>
                <el-form-item prop="modality" label="模态类型">
                  <el-select v-model="queryFormData.modality" placeholder="请选择模态类型" clearable>
                    <el-option label="图像" value="image" />
                    <el-option label="音频" value="audio" />
                    <el-option label="视频" value="video" />
                    <el-option label="文本" value="text" />
                    <el-option label="传感器" value="sensor" />
                    <el-option label="多模态" value="multimodal" />
                  </el-select>
                </el-form-item>
                <el-form-item prop="upload_status" label="上传状态">
                  <el-select
                    v-model="queryFormData.upload_status"
                    placeholder="请选择上传状态"
                    clearable
                  >
                    <el-option label="初始化" value="init" />
                    <el-option label="上传中" value="uploading" />
                    <el-option label="已完成" value="completed" />
                    <el-option label="失败" value="failed" />
                  </el-select>
                </el-form-item>
                <el-form-item class="search-buttons">
                  <el-button type="primary" icon="search" native-type="submit"> 查询 </el-button>
                  <el-button icon="refresh" @click="handleResetQuery"> 重置 </el-button>
                </el-form-item>
              </el-form>
            </div>

            <!-- 数据集表格 -->
            <el-table
              v-loading="loading"
              :data="datasetList"
              stripe
              border
              style="width: 100%"
              class="dataset-table"
            >
              <el-table-column type="index" label="#" width="60" />
              <el-table-column prop="name" label="数据集名称" min-width="180" show-overflow-tooltip />
              <el-table-column prop="original_filename" label="文件名" min-width="200" show-overflow-tooltip />
              <el-table-column label="模态类型" width="100">
                <template #default="{ row }">
                  <el-tag :type="getModalityTagType(row.modality)" size="small">
                    {{ getModalityText(row.modality) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="文件大小" width="120">
                <template #default="{ row }">
                  {{ formatFileSize(row.file_size) }}
                </template>
              </el-table-column>
              <el-table-column label="样本数" width="100">
                <template #default="{ row }">
                  {{ row.sample_count || "-" }}
                </template>
              </el-table-column>
              <el-table-column label="上传状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="getStatusTagType(row.upload_status)" size="small">
                    {{ getStatusText(row.upload_status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="created_time" label="创建时间" width="160">
                <template #default="{ row }">
                  {{ formatDateTime(row.created_time) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="280" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" link @click="handleViewDataset(row)">
                    <el-icon><View /></el-icon>
                    查看
                  </el-button>
                  <el-button
                    v-if="row.upload_status === 'completed' && !row.analysis_result"
                    type="success"
                    link
                    @click="handleAnalyzeDataset(row)"
                  >
                    <el-icon><DataAnalysis /></el-icon>
                    分析
                  </el-button>
                  <el-button type="warning" link @click="handleEditDataset(row)">
                    <el-icon><Edit /></el-icon>
                    编辑
                  </el-button>
                  <el-button type="danger" link @click="handleDeleteDataset(row)">
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- 分页 -->
            <div class="pagination-container">
              <pagination
                v-model:total="total"
                v-model:page="queryFormData.page_no"
                v-model:limit="queryFormData.page_size"
                @pagination="loadDatasetList"
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- 数据集分析 -->
        <el-tab-pane v-if="currentDatasetId" label="数据集分析" name="analysis">
          <template #label>
            <span class="tab-label">
              <el-icon><DataAnalysis /></el-icon>
              数据集分析
            </span>
          </template>

          <div class="tab-content">
            <DatasetAnalysis
              v-if="activeTab === 'analysis' && currentDatasetId"
              :dataset-id="currentDatasetId"
              @analysis-complete="handleAnalysisComplete"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 数据集详情弹窗 -->
    <el-drawer
      v-model="detailDrawerVisible"
      title="数据集详情"
      :size="drawerSize"
      direction="rtl"
    >
      <div v-if="currentDataset" class="dataset-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="数据集名称">
            {{ currentDataset.name }}
          </el-descriptions-item>
          <el-descriptions-item label="原始文件名">
            {{ currentDataset.original_filename }}
          </el-descriptions-item>
          <el-descriptions-item label="模态类型">
            <el-tag :type="getModalityTagType(currentDataset.modality)" size="small">
              {{ getModalityText(currentDataset.modality) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="上传状态">
            <el-tag :type="getStatusTagType(currentDataset.upload_status)" size="small">
              {{ getStatusText(currentDataset.upload_status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="文件大小">
            {{ formatFileSize(currentDataset.file_size) }}
          </el-descriptions-item>
          <el-descriptions-item label="文件哈希">
            <el-text truncated>{{ currentDataset.file_hash }}</el-text>
          </el-descriptions-item>
          <el-descriptions-item label="样本数量">
            {{ currentDataset.sample_count || "未分析" }}
          </el-descriptions-item>
          <el-descriptions-item label="类别数量">
            {{ currentDataset.class_count || "未分析" }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">
            {{ formatDateTime(currentDataset.created_time) }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ currentDataset.description || "暂无描述" }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 分析结果 -->
        <div v-if="currentDataset.analysis_result" class="mt-6">
          <h3 class="text-lg font-semibold mb-4">分析结果</h3>
          <el-card shadow="never" class="analysis-result-card">
            <pre>{{ JSON.stringify(currentDataset.analysis_result, null, 2) }}</pre>
          </el-card>
        </div>
      </div>
    </el-drawer>

    <!-- 编辑弹窗 -->
    <el-drawer
      v-model="editDrawerVisible"
      title="编辑数据集"
      :size="drawerSize"
      direction="rtl"
      @close="handleCloseEditDrawer"
    >
      <el-form
        ref="editFormRef"
        :model="editFormData"
        :rules="editFormRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="数据集名称" prop="name">
          <el-input v-model="editFormData.name" placeholder="请输入数据集名称" />
        </el-form-item>
        <el-form-item label="模态类型" prop="modality">
          <el-select v-model="editFormData.modality" placeholder="请选择模态类型">
            <el-option label="图像" value="image" />
            <el-option label="音频" value="audio" />
            <el-option label="视频" value="video" />
            <el-option label="文本" value="text" />
            <el-option label="传感器" value="sensor" />
            <el-option label="多模态" value="multimodal" />
          </el-select>
        </el-form-item>
        <el-form-item label="样本数量" prop="sample_count">
          <el-input-number
            v-model="editFormData.sample_count"
            :min="0"
            :controls="true"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="类别数量" prop="class_count">
          <el-input-number
            v-model="editFormData.class_count"
            :min="0"
            :controls="true"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="editFormData.status">
            <el-radio value="0">启用</el-radio>
            <el-radio value="1">停用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="editFormData.description"
            type="textarea"
            :rows="4"
            placeholder="请输入数据集描述"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleCloseEditDrawer">取消</el-button>
          <el-button type="primary" @click="handleSubmitEdit">确定</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from "vue";
import {
  DataBoard,
  CircleCheck,
  Loading,
  FolderOpened,
  Upload,
  List,
  DataAnalysis,
  View,
  Edit,
  Delete,
} from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { formatToDateTime } from "@/utils/dateUtil";
import { useAppStore } from "@/store/modules/app.store";
import { DeviceEnum } from "@/enums/settings/device.enum";
import DatasetAPI, {
  type DatasetInfo,
  type DatasetPageQuery,
  type DatasetStatistics,
  type DatasetUpdateForm,
} from "@/api/module_application/dataset";
import DatasetUpload from "./components/DatasetUpload.vue";
import DatasetAnalysis from "./components/DatasetAnalysis.vue";

defineOptions({
  name: "DatasetManagement",
  inheritAttrs: false,
});

const appStore = useAppStore();

// Tab 切换
const activeTab = ref("upload");

// 统计数据
const statistics = ref<DatasetStatistics>({
  total_count: 0,
  completed_count: 0,
  uploading_count: 0,
  failed_count: 0,
  total_size: 0,
  modality_stats: {},
});

// 数据集列表相关
const queryFormRef = ref();
const loading = ref(false);
const total = ref(0);
const datasetList = ref<DatasetInfo[]>([]);
const queryFormData = reactive<DatasetPageQuery>({
  page_no: 1,
  page_size: 10,
  name: undefined,
  modality: undefined,
  upload_status: undefined,
});

// 当前数据集
const currentDatasetId = ref<number | null>(null);
const currentDataset = ref<DatasetInfo | null>(null);

// 详情弹窗
const detailDrawerVisible = ref(false);

// 编辑弹窗
const editDrawerVisible = ref(false);
const editFormRef = ref();
const editFormData = reactive<DatasetUpdateForm>({
  name: "",
  modality: "",
  sample_count: 0,
  class_count: 0,
  status: "0",
  description: "",
});

const editFormRules = reactive({
  name: [{ required: true, message: "请输入数据集名称", trigger: "blur" }],
  modality: [{ required: true, message: "请选择模态类型", trigger: "change" }],
});

// 计算属性
const drawerSize = computed(() => (appStore.device === DeviceEnum.DESKTOP ? "600px" : "90%"));

// 模态类型映射
const modalityMap: Record<string, string> = {
  image: "图像",
  audio: "音频",
  video: "视频",
  text: "文本",
  sensor: "传感器",
  multimodal: "多模态",
  unknown: "未知",
};

function getModalityText(modality: string): string {
  return modalityMap[modality] || modality;
}

function getModalityTagType(modality: string): "success" | "info" | "warning" | "danger" | "" {
  const typeMap: Record<string, "success" | "info" | "warning" | "danger"> = {
    image: "success",
    audio: "warning",
    video: "danger",
    text: "info",
  };
  return typeMap[modality] || "";
}

// 状态映射
function getStatusText(status: string): string {
  const textMap: Record<string, string> = {
    init: "初始化",
    uploading: "上传中",
    completed: "已完成",
    failed: "失败",
  };
  return textMap[status] || status;
}

function getStatusTagType(status: string): "success" | "info" | "warning" | "danger" | "" {
  const typeMap: Record<string, "success" | "info" | "warning" | "danger"> = {
    completed: "success",
    uploading: "info",
    init: "warning",
    failed: "danger",
  };
  return typeMap[status] || "";
}

// 格式化文件大小
function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

// 格式化日期时间
function formatDateTime(dateStr: string | undefined): string {
  if (!dateStr) return "-";
  try {
    return formatToDateTime(dateStr, "YYYY-MM-DD HH:mm:ss");
  } catch {
    return dateStr;
  }
}

// 加载统计数据
async function loadStatistics() {
  try {
    const response = await DatasetAPI.getStatistics();
    statistics.value = response.data.data;
  } catch (error: any) {
    console.error("加载统计数据失败:", error);
  }
}

// 加载数据集列表
async function loadDatasetList() {
  loading.value = true;
  try {
    const response = await DatasetAPI.getList(queryFormData);
    datasetList.value = response.data.data.items;
    total.value = response.data.data.total;
  } catch (error: any) {
    ElMessage.error("加载数据集列表失败: " + (error.message || "未知错误"));
  } finally {
    loading.value = false;
  }
}

// 查询
async function handleQuery() {
  queryFormData.page_no = 1;
  await loadDatasetList();
}

// 重置查询
async function handleResetQuery() {
  queryFormRef.value?.resetFields();
  queryFormData.page_no = 1;
  await loadDatasetList();
}

// 上传成功回调
function handleUploadSuccess(datasetId?: number) {
  ElMessage.success("数据集上传成功!");
  loadStatistics();
  loadDatasetList();

  if (datasetId) {
    currentDatasetId.value = datasetId;
    activeTab.value = "analysis";
  }
}

// 上传取消回调
function handleUploadCancel() {
  // 处理取消逻辑
}

// 查看数据集
async function handleViewDataset(row: DatasetInfo) {
  try {
    const response = await DatasetAPI.getDetail(row.id!);
    currentDataset.value = response.data.data;
    detailDrawerVisible.value = true;
  } catch (error: any) {
    ElMessage.error("加载数据集详情失败: " + (error.message || "未知错误"));
  }
}

// 分析数据集
function handleAnalyzeDataset(row: DatasetInfo) {
  currentDatasetId.value = row.id!;
  activeTab.value = "analysis";
}

// 编辑数据集
function handleEditDataset(row: DatasetInfo) {
  currentDataset.value = row;
  Object.assign(editFormData, {
    name: row.name,
    modality: row.modality,
    sample_count: row.sample_count,
    class_count: row.class_count,
    status: row.status || "0",
    description: row.description,
  });
  editDrawerVisible.value = true;
}

// 删除数据集
async function handleDeleteDataset(row: DatasetInfo) {
  try {
    const action = await ElMessageBox.confirm(
      "确认删除该数据集？是否同时删除存储文件？",
      "警告",
      {
        confirmButtonText: "删除(保留文件)",
        cancelButtonText: "取消",
        distinguishCancelAndClose: true,
        type: "warning",
        showClose: false,
        closeOnClickModal: false,
        closeOnPressEscape: false,
        customClass: "delete-confirm-box",
        buttonSize: "default",
        // 添加自定义按钮
        showCancelButton: true,
        showConfirmButton: true,
        beforeClose: (action, instance, done) => {
          if (action === "confirm") {
            // 保留文件
            done();
          } else if (action === "cancel") {
            done();
          } else {
            done();
          }
        },
      },
    );

    // 询问是否删除文件
    let deleteFile = false;
    if (action === "confirm") {
      try {
        await ElMessageBox.confirm(
          `数据集记录将被删除，是否同时删除存储文件？\n\n文件路径: ${row.storage_path || "未知"}`,
          "删除文件确认",
          {
            confirmButtonText: "同时删除文件",
            cancelButtonText: "仅删除记录",
            type: "warning",
            distinguishCancelAndClose: true,
          },
        );
        deleteFile = true;
      } catch (err) {
        if (err === "cancel") {
          deleteFile = false;
        } else {
          throw err;
        }
      }
    }

    await DatasetAPI.delete([row.id!], deleteFile);
    ElMessage.success(
      deleteFile ? "数据集及文件删除成功" : "数据集记录删除成功(文件已保留)",
    );
    await loadDatasetList();
    await loadStatistics();
  } catch (error: any) {
    if (error !== "cancel" && error !== "close") {
      ElMessage.error("删除失败: " + (error.message || "未知错误"));
    }
  }
}

// 提交编辑
async function handleSubmitEdit() {
  try {
    await editFormRef.value?.validate();

    await DatasetAPI.update(currentDataset.value!.id!, editFormData);

    ElMessage.success("更新成功");
    editDrawerVisible.value = false;
    await loadDatasetList();
  } catch (error: any) {
    if (error !== "cancel") {
      ElMessage.error("更新失败: " + (error.message || "未知错误"));
    }
  }
}

// 关闭编辑弹窗
function handleCloseEditDrawer() {
  editDrawerVisible.value = false;
  editFormRef.value?.resetFields();
}

// 分析完成回调
function handleAnalysisComplete() {
  loadDatasetList();
  loadStatistics();
  ElMessage.success("数据集分析完成!");
}

// 初始化
onMounted(async () => {
  await loadStatistics();
  await loadDatasetList();
});
</script>

<style lang="scss" scoped>
.dataset-management {
  .stats-row {
    margin-bottom: 20px;

    .stat-card {
      border-radius: 12px;
      overflow: hidden;
      transition: all 0.3s ease;

      &:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
      }

      .stat-content {
        display: flex;
        gap: 16px;
        align-items: center;

        .stat-icon {
          display: flex;
          flex-shrink: 0;
          align-items: center;
          justify-content: center;
          width: 64px;
          height: 64px;
          border-radius: 12px;
        }

        .stat-info {
          flex: 1;

          .stat-label {
            margin-bottom: 8px;
            font-size: 14px;
            color: var(--el-text-color-secondary);
          }

          .stat-value {
            font-size: 28px;
            font-weight: 700;
            color: var(--el-text-color-primary);
          }
        }
      }
    }
  }

  .main-card {
    border-radius: 16px;
    overflow: hidden;

    .dataset-tabs {
      :deep(.el-tabs__header) {
        margin: 0;
        background: var(--el-fill-color-light);
      }

      .tab-label {
        display: flex;
        gap: 6px;
        align-items: center;
      }

      .tab-content {
        padding: 24px;
        min-height: 500px;
      }
    }
  }

  .dataset-table {
    margin-top: 16px;
  }

  .pagination-container {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
  }

  .dataset-detail {
    .analysis-result-card {
      pre {
        margin: 0;
        overflow-x: auto;
        font-family: "Courier New", monospace;
        font-size: 13px;
        line-height: 1.6;
        color: var(--el-text-color-regular);
      }
    }
  }
}
</style>

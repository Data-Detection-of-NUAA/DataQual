<template>
  <div class="app-container">
    <div class="search-container">
      <el-form :inline="true" :model="queryFormData" @submit.prevent="handleSearch">
        <el-form-item prop="keyword" label="名称/文件">
          <el-input
            v-model="queryFormData.keyword"
            placeholder="请输入法规名称或文件名"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item class="search-buttons">
          <el-button type="primary" native-type="submit">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-card class="data-table" shadow="never">
      <template #header>
        <div class="card-header">
          <span>法规记录列表</span>
        </div>
      </template>
      <div class="data-table__toolbar">
        <el-button type="success" icon="plus" @click="openUploadDialog">上传法规</el-button>
        <el-button
          type="danger"
          icon="delete"
          :disabled="!selectedIds.length"
          @click="() => handleBatchDelete()"
        >
          批量删除
        </el-button>
      </div>
      <el-table
        v-loading="loading"
        :data="tableData"
        border
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="regulation_name" label="法规名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="file_name" label="文件名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="file_type" label="类型" width="120" />
        <el-table-column label="大小" width="120">
          <template #default="{ row }">
            {{ formatSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="updated_time" label="最后更新" min-width="160" />
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="handleDetail(row)">详情</el-button>
            <el-button
              type="danger"
              size="small"
              link
              @click="() => row.id !== undefined && handleBatchDelete([row.id])"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <pagination
          v-model:total="total"
          v-model:page="queryFormData.page_no"
          v-model:limit="queryFormData.page_size"
          @pagination="loadTableData"
        />
      </template>
    </el-card>

    <el-dialog v-model="uploadDialog.visible" title="上传法规" width="520px" @close="resetUploadForm">
      <el-form :model="uploadForm" label-width="90px">
        <el-form-item label="法规名称">
          <el-input v-model="uploadForm.regulation_name" placeholder="可为空，用于区分业务场景" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="uploadForm.description" type="textarea" :rows="2" placeholder="可描述法规文件用途" />
        </el-form-item>
        <el-form-item label="法规文件" required>
          <el-upload
            drag
            :auto-upload="false"
            :limit="1"
            accept=".txt,.pdf,.docx,.json,.xml"
            :on-change="handleUploadFileChange"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<span class="primary">点击上传</span>
            </div>
            <template #tip>
              <div class="el-upload__tip">仅支持上传一个文件</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUploadSubmit">确认上传</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailDialog.visible" title="法规详情" width="520px" @close="detailDialog.data = null">
      <el-descriptions v-if="detailDialog.data" :column="1" border>
        <el-descriptions-item label="法规名称">{{ detailDialog.data.regulation_name }}</el-descriptions-item>
        <el-descriptions-item label="文件名称">{{ detailDialog.data.file_name }}</el-descriptions-item>
        <el-descriptions-item label="文件类型">{{ detailDialog.data.file_type }}</el-descriptions-item>
        <el-descriptions-item label="文件大小">{{ formatSize(detailDialog.data.file_size) }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ detailDialog.data.description || "-" }}</el-descriptions-item>
        <el-descriptions-item label="最后更新">{{ detailDialog.data.updated_time || "-" }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button type="primary" @click="detailDialog.visible = false">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue";
import { ElMessage, ElMessageBox, UploadFile } from "element-plus";
import { UploadFilled } from "@element-plus/icons-vue";
import AuditRegulationAPI, {
  AuditRegulationTable,
  AuditRegulationPageQuery,
  AuditRegulationUploadForm,
} from "@/api/module_audit/regulation";

defineOptions({
  name: "AuditRegulation",
});

const loading = ref(false);
const uploading = ref(false);
const tableData = ref<AuditRegulationTable[]>([]);
const total = ref(0);
const selectedIds = ref<number[]>([]);

const queryFormData = reactive<AuditRegulationPageQuery>({
  page_no: 1,
  page_size: 10,
  keyword: "",
});

const uploadDialog = reactive({
  visible: false,
});
const uploadForm = reactive<{
  regulation_name: string;
  description: string;
  file: File | null;
}>({
  regulation_name: "",
  description: "",
  file: null,
});

const detailDialog = reactive<{
  visible: boolean;
  data: AuditRegulationTable | null;
}>({
  visible: false,
  data: null,
});

async function loadTableData() {
  loading.value = true;
  try {
    const { data } = await AuditRegulationAPI.listRegulation(queryFormData);
    tableData.value = data.data?.items || [];
    total.value = data.data?.total || 0;
  } catch (error) {
    console.error(error);
  } finally {
    loading.value = false;
  }
}

function handleSearch() {
  queryFormData.page_no = 1;
  loadTableData();
}

function handleReset() {
  queryFormData.keyword = "";
  queryFormData.page_no = 1;
  loadTableData();
}

function handleSelectionChange(selection: AuditRegulationTable[]) {
  selectedIds.value = selection
    .map((item) => item.id)
    .filter((id): id is number => typeof id === "number");
}

function openUploadDialog() {
  resetUploadForm();
  uploadDialog.visible = true;
}

function resetUploadForm() {
  uploadForm.regulation_name = "";
  uploadForm.description = "";
  uploadForm.file = null;
}

function handleUploadFileChange(file: UploadFile) {
  uploadForm.file = (file.raw as File) || null;
}

async function handleUploadSubmit() {
  if (!uploadForm.file) {
    ElMessage.warning("请先选择要上传的法规文件");
    return;
  }
  uploading.value = true;
  try {
    const payload: AuditRegulationUploadForm = {
      regulation_name: uploadForm.regulation_name,
      description: uploadForm.description,
      file: uploadForm.file as File,
    };
    await AuditRegulationAPI.uploadRegulation(payload);
    ElMessage.success("法规上传成功");
    uploadDialog.visible = false;
    resetUploadForm();
    loadTableData();
  } catch (error) {
    console.error(error);
  } finally {
    uploading.value = false;
  }
}

async function handleBatchDelete(ids?: number[]) {
  const targetIds = ids || selectedIds.value;
  if (!targetIds.length) return;
  try {
    await ElMessageBox.confirm("确认要删除选中的法规文件吗？", "提示", {
      type: "warning",
    });
    loading.value = true;
    await AuditRegulationAPI.deleteRegulation(targetIds);
    ElMessage.success("删除成功");
    selectedIds.value = [];
    loadTableData();
  } catch (error) {
    if (error !== "cancel") {
      console.error(error);
    }
  } finally {
    loading.value = false;
  }
}

async function handleDetail(row: AuditRegulationTable) {
  if (typeof row.id !== "number") return;
  try {
    const { data } = await AuditRegulationAPI.detailRegulation(row.id);
    detailDialog.data = data.data;
    detailDialog.visible = true;
  } catch (error) {
    console.error(error);
  }
}

function formatSize(size?: number) {
  if (!size && size !== 0) return "-";
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

loadTableData();
</script>

<style scoped>
.search-container {
  margin-bottom: 16px;
}

.data-table__toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

</style>

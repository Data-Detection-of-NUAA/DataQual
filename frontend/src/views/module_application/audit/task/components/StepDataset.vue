<template>
  <div class="step-panel">
    <el-alert
      title="上传待审计的数据集，支持 30+ 种文件格式（CSV/Excel/JSON/XML/ZIP/TXT/HTML/PDF/DOC等）"
      type="info"
      :closable="false"
      show-icon
    />
    <el-upload class="mt-4" drag :auto-upload="false" :limit="1" accept=".csv,.xlsx,.xls,.json,.xml,.zip,.rar,.7z,.tar,.gz,.txt,.log,.md,.html,.htm,.pdf,.doc,.docx,.rtf,.tsv,.yaml,.yml,.toml,.ini,.conf,.cfg" :on-change="handleFileChange">
      <el-icon class="el-icon--upload">
        <UploadFilled />
      </el-icon>
      <div class="el-upload__text">将文件拖到此处，或<span class="primary">点击上传</span></div>
      <template #tip>
        <div class="el-upload__tip">支持结构化数据（CSV/Excel）、压缩包（ZIP/RAR）、文档（PDF/DOC）、网页（HTML）等多种格式</div>
      </template>
    </el-upload>
    <div class="action-area">
      <el-button type="primary" :loading="loading" @click="handleUpload">
        上传数据集
      </el-button>
      <div v-if="datasetFileName" class="mt-2 text-secondary">
        当前文件：{{ datasetFileName }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { ElMessage, UploadFile } from "element-plus";
import { UploadFilled } from "@element-plus/icons-vue";

const props = defineProps({
  loading: { type: Boolean, default: false },
  datasetFileName: { type: String, default: "" },
});

const emit = defineEmits<{
  upload: [file: File];
}>();

const selectedFile = ref<File | null>(null);

function handleFileChange(file: UploadFile) {
  selectedFile.value = file.raw || null;
}

function handleUpload() {
  if (!selectedFile.value) {
    ElMessage.warning("请先选择数据集文件");
    return;
  }
  emit("upload", selectedFile.value);
}
</script>

<style scoped>
.step-panel {
  padding: 12px 0;
}

.action-area {
  margin-top: 20px;
  text-align: center;
}

.text-secondary {
  color: var(--el-text-color-secondary);
}
</style>

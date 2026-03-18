<template>
  <div class="step-panel">
    <el-alert
      title="请上传与 GDPR 相关的法规文件，支持 30+ 种文件格式（TXT/PDF/DOC/JSON/XML/HTML/ZIP等）"
      type="info"
      :closable="false"
      show-icon
    />
    <div class="regulation-layout">
      <div class="regulation-block select-block">
        <div class="block-header">
          <span>选择已发布的法规文件</span>
          <el-tag size="small" type="info">
            当前：{{ regulationFileName || "暂无选择" }}
          </el-tag>
        </div>
        <el-select
          v-model="selectedRegulation"
          filterable
          placeholder="请选择法规文件"
          class="regulation-select"
        >
          <el-option
            v-for="item in regulations"
            :key="item.id"
            :label="`${item.regulation_name}（${item.file_name}）`"
            :value="item.id"
          />
        </el-select>
        <el-button
          type="primary"
          class="use-button"
          :loading="selecting"
          :disabled="!selectedRegulation"
          @click="handleUseRegulation"
        >
          使用所选法规
        </el-button>
      </div>
      <div class="vertical-divider" />
      <div class="regulation-block upload-block">
        <div class="block-header">
          <span>上传新的法规文件</span>
        </div>
        <el-upload
          class="upload-area"
          drag
          :auto-upload="false"
          :limit="1"
          accept=".txt,.pdf,.doc,.docx,.json,.xml,.html,.htm,.md,.rtf,.csv,.xlsx,.zip,.rar,.7z"
          :on-change="handleFileChange"
        >
          <el-icon class="el-icon--upload">
            <UploadFilled />
          </el-icon>
          <div class="el-upload__text">
            将文件拖到此处，或<span class="primary">点击上传</span>
          </div>
          <template #tip>
            <div class="el-upload__tip">支持文档（PDF/DOC）、网页（HTML）、压缩包（ZIP）等多种格式</div>
          </template>
        </el-upload>
        <div class="action-area">
          <el-button type="primary" :loading="loading" @click="handleUpload">
            上传法规
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { ElMessage, UploadFile } from "element-plus";
import { UploadFilled } from "@element-plus/icons-vue";
import type { PropType } from "vue";
import type { AuditRegulationOption } from "@/api/module_application/audit/regulation";

const props = defineProps({
  loading: { type: Boolean, default: false },
  selecting: { type: Boolean, default: false },
  regulationFileName: { type: String, default: "" },
  regulationId: { type: Number, default: undefined },
  regulations: {
    type: Array as PropType<AuditRegulationOption[]>,
    default: () => [],
  },
});

const emit = defineEmits<{
  upload: [file: File];
  use: [regulationId: number];
}>();

const selectedFile = ref<File | null>(null);
const selectedRegulation = ref<number | null>(null);

watch(
  () => props.regulationId,
  (val) => {
    selectedRegulation.value = typeof val === "number" ? val : null;
  },
  { immediate: true }
);

function handleFileChange(file: UploadFile) {
  selectedFile.value = file.raw || null;
}

function handleUpload() {
  if (!selectedFile.value) {
    ElMessage.warning("请先选择法规文件");
    return;
  }
  emit("upload", selectedFile.value);
  selectedFile.value = null;
}

function handleUseRegulation() {
  if (!selectedRegulation.value) {
    ElMessage.warning("请选择法规文件");
    return;
  }
  emit("use", selectedRegulation.value);
}
</script>

<style scoped>
.step-panel {
  padding: 12px 0;
}

.regulation-layout {
  display: flex;
  gap: 24px;
  margin-top: 20px;
  flex-wrap: wrap;
}

.regulation-block {
  flex: 1;
  min-width: 280px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.block-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.regulation-select {
  width: 100%;
}

.use-button {
  align-self: flex-start;
}

.vertical-divider {
  width: 1px;
  background-color: var(--el-border-color-lighter);
  min-height: 220px;
}

.action-area {
  text-align: left;
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
}

@media screen and (max-width: 900px) {
  .regulation-layout {
    flex-direction: column;
  }

  .vertical-divider {
    width: 100%;
    height: 1px;
    min-height: 1px;
  }
}
</style>

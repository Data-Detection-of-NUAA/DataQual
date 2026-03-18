<template>
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
          <el-tag v-else-if="selectedModality === m.value" type="success" effect="plain" size="small">已选择</el-tag>
          <el-tag v-else type="info" effect="plain" size="small">可用</el-tag>
        </el-card>
      </el-col>
    </el-row>
    <div class="mt-2 flex justify-end">
      <el-button type="primary" :disabled="!selectedModality" @click="gotoStep(1)">下一步</el-button>
    </div>
  </el-card>

  <!-- Step 1: upload (tabular) -->
  <el-card v-show="activeStep === 1 && selectedModality !== 'image'" shadow="never" class="mt-4">
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
        免基线模式会按"切分比例"将同一文件分成两段进行漂移对比。
      </el-text>
    </el-card>

    <el-card v-if="distributionCompareMode === 'baseline_file'" shadow="never" class="mb-3">
      <template #header>
        <div class="flex-x-between">
          <div class="font-bold">基线文件（必填）</div>
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

  <!-- Step 1: upload (image) -->
  <el-card v-show="activeStep === 1 && selectedModality === 'image'" shadow="never" class="mt-4">
    <template #header>
      <div class="font-bold">上传图片数据集（ZIP，最大2GB）</div>
    </template>

    <el-alert
      type="info"
      show-icon
      :closable="false"
      title="ZIP 文件要求"
      description="ZIP 包内需包含：① 图片文件（支持 jpg/png/bmp/gif/webp）；② 标签 CSV 文件（含 image_path 和 label 列）。图片路径为相对于 ZIP 根目录的路径。"
      class="mb-3"
    />

    <el-card shadow="never">
      <template #header>
        <div class="flex-x-between">
          <div class="font-bold">图片数据集 ZIP</div>
          <el-tag type="success" effect="plain" size="small">扫描对象</el-tag>
        </div>
      </template>

      <el-upload
        ref="currentUploadRef"
        drag
        :auto-upload="false"
        :limit="1"
        :file-list="currentFileList"
        accept=".zip"
        @change="onCurrentFileChange"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">将 ZIP 文件拖到此处，或 <em>点击选择</em></div>
      </el-upload>

      <div class="mt-3 flex items-center gap-2">
        <el-button type="primary" :loading="currentUploading" :disabled="!currentSelectedFile" @click="doUploadCurrent">
          上传并继续
        </el-button>
        <el-text v-if="currentUploadedFile" type="info">
          已上传：{{ currentUploadedFile.filename }}（{{ formatBytes(currentUploadedFile.file_size) }}）
        </el-text>
      </div>
    </el-card>
  </el-card>
</template>

<script setup lang="ts">
import { UploadFilled } from "@element-plus/icons-vue";
import { useDqscanInject, modalities, formatBytes } from "../composables/useDqscanState";

const {
  activeStep, gotoStep, selectedModality,
  baselineUploadRef, currentUploadRef,
  baselineFileList, baselineSelectedFile, baselineUploading, baselineUploadedFile,
  currentFileList, currentSelectedFile, currentUploading, currentUploadedFile,
  distributionCompareMode,
  onBaselineFileChange, onCurrentFileChange, clearBaseline, doUploadBaseline, doUploadCurrent,
} = useDqscanInject();
</script>

<style scoped>
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
</style>

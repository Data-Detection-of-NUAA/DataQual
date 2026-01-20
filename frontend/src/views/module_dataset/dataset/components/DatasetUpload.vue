<!-- 数据集上传组件 - 支持大文件分片上传和断点续传 -->
<template>
  <div class="dataset-upload-container">
    <!-- 上传区域 -->
    <div
      v-if="!uploadedFile"
      class="upload-zone"
      :class="{ 'upload-zone-dragover': dragover }"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
      @click="triggerFileInput"
    >
      <input
        ref="fileInputRef"
        type="file"
        accept=".zip,.tar,.gz,.rar,.7z,.tar.gz,.tar.bz2"
        style="display: none"
        @change="handleFileChange"
      />

      <div class="upload-icon">
        <el-icon :size="64" color="#409eff">
          <UploadFilled />
        </el-icon>
      </div>

      <div class="upload-text">
        <p class="upload-title">点击或拖拽文件到此处上传</p>
        <p class="upload-hint">支持格式: ZIP, TAR, GZ, RAR, 7Z</p>
        <p class="upload-hint">支持 10GB+ 大文件、断点续传</p>
      </div>

      <el-button type="primary" size="large" class="mt-4">
        <el-icon class="mr-2"><Upload /></el-icon>
        选择文件
      </el-button>
    </div>

    <!-- 上传进度显示 -->
    <div v-else class="upload-progress-container">
      <!-- 文件信息卡片 -->
      <el-card shadow="hover" class="file-info-card">
        <template #header>
          <div class="card-header">
            <span class="font-semibold">文件信息</span>
            <el-button
              v-if="!uploading && uploadProgress < 100"
              type="danger"
              link
              @click="cancelUpload"
            >
              <el-icon><Close /></el-icon>
              取消上传
            </el-button>
          </div>
        </template>

        <div class="file-info">
          <div class="file-icon">
            <el-icon :size="48" color="#409eff">
              <Document />
            </el-icon>
          </div>
          <div class="file-details">
            <div class="file-name">{{ uploadedFile.name }}</div>
            <div class="file-size">{{ formatFileSize(uploadedFile.size) }}</div>
          </div>
        </div>

        <!-- 数据集名称和描述 -->
        <el-divider />
        <el-form :model="datasetForm" label-width="100px" label-position="left">
          <el-form-item label="数据集名称">
            <el-input
              v-model="datasetForm.name"
              placeholder="请输入数据集名称"
              :disabled="uploading || uploadProgress >= 100"
            />
          </el-form-item>
          <el-form-item label="任务类型" required>
            <el-select
              v-model="datasetForm.taskType"
              placeholder="请选择任务类型"
              :disabled="uploading || uploadProgress >= 100"
              style="width: 100%"
              filterable
            >
              <el-option
                v-for="task in taskTypes"
                :key="task.value"
                :label="task.label"
                :value="task.value"
              />
            </el-select>
          </el-form-item>
        </el-form>

        <!-- 上传进度条 -->
        <div v-if="uploadProgress > 0" class="progress-section">
          <div class="progress-header">
            <span class="progress-label">上传进度</span>
            <span class="progress-value">{{ uploadProgress.toFixed(1) }}%</span>
          </div>

          <el-progress
            :percentage="uploadProgress"
            :status="uploadStatus"
            :stroke-width="18"
            :striped="uploading"
            :striped-flow="uploading"
          />

          <div class="progress-stats">
            <div class="stat-item">
              <el-icon><Clock /></el-icon>
              <span>剩余时间: {{ remainingTime }}</span>
            </div>
            <div class="stat-item">
              <el-icon><Odometer /></el-icon>
              <span>速度: {{ uploadSpeed }} MB/s</span>
            </div>
            <div class="stat-item">
              <el-icon><Checked /></el-icon>
              <span>已上传: {{ uploadedChunks }} / {{ totalChunks }} 分片</span>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="action-buttons">
          <el-button
            v-if="!uploading && uploadProgress === 0"
            type="primary"
            size="large"
            @click="startUpload"
          >
            <el-icon class="mr-2"><Upload /></el-icon>
            开始上传
          </el-button>

          <template v-else-if="uploading && uploadProgress < 100">
            <el-button type="warning" size="large" @click="pauseUpload">
              <el-icon class="mr-2"><VideoPause /></el-icon>
              暂停
            </el-button>
          </template>

          <template v-else-if="uploadPaused && uploadProgress < 100">
            <el-button type="success" size="large" @click="resumeUpload">
              <el-icon class="mr-2"><VideoPlay /></el-icon>
              继续上传
            </el-button>
            <el-button type="danger" size="large" @click="cancelUpload">
              <el-icon class="mr-2"><Close /></el-icon>
              取消
            </el-button>
          </template>

          <template v-else-if="uploadProgress >= 100">
            <el-button type="success" size="large" disabled>
              <el-icon class="mr-2"><CircleCheck /></el-icon>
              上传完成
            </el-button>
            <el-button type="primary" size="large" @click="proceedToAnalysis">
              下一步：数据集分析
              <el-icon class="ml-2"><ArrowRight /></el-icon>
            </el-button>
          </template>
        </div>
      </el-card>

      <!-- 上传日志 -->
      <el-card v-if="uploadLogs.length > 0" shadow="hover" class="log-card mt-4">
        <template #header>
          <div class="card-header">
            <span class="font-semibold">上传日志</span>
            <el-button type="primary" link @click="uploadLogs = []">
              <el-icon><Delete /></el-icon>
              清空
            </el-button>
          </div>
        </template>

        <div class="log-container">
          <div
            v-for="(log, index) in uploadLogs"
            :key="index"
            class="log-item"
            :class="`log-${log.type}`"
          >
            <span class="log-time">{{ log.time }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from "vue";
import {
  UploadFilled,
  Upload,
  Document,
  Close,
  Clock,
  Odometer,
  Checked,
  VideoPause,
  VideoPlay,
  CircleCheck,
  ArrowRight,
  Delete,
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import DatasetAPI, { type UploadInitRequest } from "@/api/module_dataset/dataset";
import SparkMD5 from "spark-md5";

// Emits
const emit = defineEmits(["upload-success", "upload-cancel"]);

// 文件上传相关
const fileInputRef = ref<HTMLInputElement>();
const dragover = ref(false);
const uploadedFile = ref<File | null>(null);
const uploading = ref(false);
const uploadPaused = ref(false);
const uploadProgress = ref(0);
const uploadSpeed = ref("0");
const remainingTime = ref("--:--");
const uploadedChunks = ref(0);
const totalChunks = ref(0);

// 上传会话信息
const uploadId = ref("");
const fileHash = ref("");

// 数据集表单
const datasetForm = reactive({
  name: "",
  taskType: "classification", // 默认任务类型：分类
  description: "",
});

// 任务类型列表
const taskTypes = [
  { value: "classification", label: "分类" },
  { value: "object_detection", label: "目标检测" },
  { value: "speech_recognition", label: "语音识别" },
  { value: "regression", label: "回归" },
  { value: "generation", label: "生成" },
  { value: "anomaly_detection", label: "异常检测" },
  { value: "segmentation", label: "分割" },
  { value: "recommendation", label: "推荐" },
];

// 上传日志
const uploadLogs = ref<Array<{ time: string; message: string; type: string }>>([]);

// 上传状态
const uploadStatus = computed(() => {
  if (uploadProgress.value >= 100) return "success";
  if (uploadPaused.value) return "warning";
  return undefined;
});

// 拖拽处理
function handleDragOver() {
  dragover.value = true;
}

function handleDragLeave() {
  dragover.value = false;
}

function handleDrop(event: DragEvent) {
  dragover.value = false;
  const file = event.dataTransfer?.files[0];
  if (file) {
    selectFile(file);
  }
}

function triggerFileInput() {
  fileInputRef.value?.click();
}

function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (file) {
    selectFile(file);
  }
  // 清空 input，允许重新选择同一文件
  target.value = "";
}

function selectFile(file: File) {
  // 验证文件类型
  const validExtensions = [".zip", ".tar", ".gz", ".rar", ".7z", ".tar.gz", ".tar.bz2"];
  const fileName = file.name.toLowerCase();
  const isValid = validExtensions.some((ext) => fileName.endsWith(ext));

  if (!isValid) {
    ElMessage.error("不支持的文件格式，请上传 ZIP、TAR、GZ、RAR 或 7Z 格式文件");
    return;
  }

  // 验证文件大小
  const maxSize = 100 * 1024 * 1024 * 1024; // 100GB
  if (file.size > maxSize) {
    ElMessage.error("文件大小超过 100GB 限制");
    return;
  }

  uploadedFile.value = file;
  extractDatasetName(file.name);
  addLog("INFO", `已选择文件: ${file.name} (${formatFileSize(file.size)})`);
}

function extractDatasetName(fileName: string) {
  // 移除文件扩展名
  let name = fileName.replace(/\.[^/.]+$/, "");
  // 移除常见后缀
  name = name.replace(/(_dataset|_data|_train|_test|_val)$/i, "");
  // 将下划线和连字符替换为空格
  name = name.replace(/[_-]/g, " ");
  // 首字母大写
  name = name.replace(/\b\w/g, (char) => char.toUpperCase());

  datasetForm.name = name || "未命名数据集";
  datasetForm.description = `基于 ${name} 数据集构建的多模态鲁棒性评估模型`;
}

// 计算文件哈希值
async function calculateFileHash(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const chunkSize = 2 * 1024 * 1024; // 2MB per chunk for hash calculation
    const chunks = Math.ceil(file.size / chunkSize);
    let currentChunk = 0;
    const spark = new SparkMD5.ArrayBuffer();
    const fileReader = new FileReader();

    fileReader.onload = (e) => {
      if (e.target?.result) {
        spark.append(e.target.result as ArrayBuffer);
        currentChunk++;

        if (currentChunk < chunks) {
          loadNext();
        } else {
          resolve(spark.end());
        }
      }
    };

    fileReader.onerror = () => {
      reject(new Error("文件读取失败"));
    };

    function loadNext() {
      const start = currentChunk * chunkSize;
      const end = Math.min(start + chunkSize, file.size);
      fileReader.readAsArrayBuffer(file.slice(start, end));
    }

    loadNext();
  });
}

// 开始上传
async function startUpload() {
  if (!uploadedFile.value) return;

  uploading.value = true;
  uploadPaused.value = false;
  uploadProgress.value = 0;
  addLog("INFO", "开始计算文件哈希值...");

  try {
    // 计算文件哈希值
    fileHash.value = await calculateFileHash(uploadedFile.value);
    addLog("INFO", `文件哈希值: ${fileHash.value}`);

    // 检查是否可以断点续传
    const resumeResponse = await DatasetAPI.resumeUpload({ file_hash: fileHash.value });

    if (resumeResponse.data.data.file_exists) {
      ElMessage.success("文件已存在,秒传成功!");
      uploadProgress.value = 100;
      addLog("SUCCESS", "文件秒传成功");
      emit("upload-success", resumeResponse.data.data.dataset_id);
      return;
    }

    // 上传初始化
    const initRequest: UploadInitRequest = {
      filename: uploadedFile.value.name,
      file_size: uploadedFile.value.size,
      file_hash: fileHash.value,
      chunk_size: 5 * 1024 * 1024, // 5MB per chunk
      name: datasetForm.name,
      task_type: datasetForm.taskType, // 添加任务类型
    };

    const initResponse = await DatasetAPI.uploadInit(initRequest);
    const initData = initResponse.data.data;

    uploadId.value = initData.upload_id;
    totalChunks.value = initData.total_chunks;
    uploadedChunks.value = initData.uploaded_chunks.length;

    addLog("INFO", `上传初始化成功, 共 ${totalChunks.value} 个分片`);

    if (initData.uploaded_chunks.length > 0) {
      addLog(
        "INFO",
        `检测到已上传 ${initData.uploaded_chunks.length} 个分片,将继续上传`,
      );
    }

    // 开始分片上传
    await uploadChunks(initData.uploaded_chunks);
  } catch (error: any) {
    ElMessage.error("上传失败: " + (error.message || "未知错误"));
    addLog("ERROR", "上传失败: " + (error.message || "未知错误"));
    uploading.value = false;
  }
}

// 分片上传
async function uploadChunks(uploadedChunkList: number[]) {
  if (!uploadedFile.value) return;

  const chunkSize = 5 * 1024 * 1024; // 5MB
  const totalChunksCount = Math.ceil(uploadedFile.value.size / chunkSize);
  const startTime = Date.now();

  for (let i = 0; i < totalChunksCount; i++) {
    if (uploadPaused.value) {
      addLog("WARN", "上传已暂停");
      return;
    }

    // 跳过已上传的分片
    if (uploadedChunkList.includes(i)) {
      uploadedChunks.value++;
      uploadProgress.value = (uploadedChunks.value / totalChunksCount) * 100;
      continue;
    }

    const start = i * chunkSize;
    const end = Math.min(start + chunkSize, uploadedFile.value.size);
    const chunk = uploadedFile.value.slice(start, end);

    // 计算分片哈希值
    const chunkHash = SparkMD5.ArrayBuffer.hash(await chunk.arrayBuffer());

    // 创建 FormData
    const formData = new FormData();
    formData.append("upload_id", uploadId.value);
    formData.append("chunk_index", i.toString());
    formData.append("chunk_hash", chunkHash);
    formData.append("file", chunk);

    try {
      const response = await DatasetAPI.uploadChunk(formData);
      const data = response.data.data;

      uploadedChunks.value = data.uploaded_chunks;
      uploadProgress.value = data.progress * 100;

      // 计算上传速度和剩余时间
      const elapsedSeconds = (Date.now() - startTime) / 1000;
      const uploadedBytes = uploadedChunks.value * chunkSize;
      const speed = uploadedBytes / elapsedSeconds / (1024 * 1024); // MB/s
      uploadSpeed.value = speed.toFixed(2);

      const remainingBytes = uploadedFile.value.size - uploadedBytes;
      const remainingSeconds = Math.ceil(remainingBytes / (speed * 1024 * 1024));
      const minutes = Math.floor(remainingSeconds / 60);
      const seconds = remainingSeconds % 60;
      remainingTime.value = `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;

      if (i % 10 === 0) {
        addLog("INFO", `已上传 ${uploadedChunks.value}/${totalChunksCount} 分片`);
      }
    } catch (error: any) {
      ElMessage.error(`分片 ${i} 上传失败: ${error.message}`);
      addLog("ERROR", `分片 ${i} 上传失败: ${error.message}`);
      uploading.value = false;
      return;
    }
  }

  // 所有分片上传完成,合并文件
  await completeUpload();
}

// 完成上传
async function completeUpload() {
  try {
    addLog("INFO", "所有分片上传完成,正在合并文件...");

    const response = await DatasetAPI.uploadComplete({
      upload_id: uploadId.value,
      verify_hash: true,
    });

    const data = response.data.data;

    if (data.merge_success && data.hash_verified) {
      uploadProgress.value = 100;
      uploading.value = false;
      ElMessage.success("文件上传成功!");
      addLog("SUCCESS", `文件上传并验证成功: ${data.storage_path}`);
      emit("upload-success", data.dataset_id);
    } else {
      ElMessage.error("文件合并或验证失败");
      addLog("ERROR", "文件合并或验证失败");
      uploading.value = false;
    }
  } catch (error: any) {
    ElMessage.error("上传完成失败: " + (error.message || "未知错误"));
    addLog("ERROR", "上传完成失败: " + (error.message || "未知错误"));
    uploading.value = false;
  }
}

// 暂停上传
function pauseUpload() {
  uploadPaused.value = true;
  uploading.value = false;
  addLog("WARN", "上传已暂停");
}

// 恢复上传
async function resumeUpload() {
  if (!uploadedFile.value) return;

  uploadPaused.value = false;
  uploading.value = true;
  addLog("INFO", "继续上传...");

  try {
    // 查询已上传的分片
    const resumeResponse = await DatasetAPI.resumeUpload({ file_hash: fileHash.value });
    const uploadedChunkList = resumeResponse.data.data.uploaded_chunks;

    await uploadChunks(uploadedChunkList);
  } catch (error: any) {
    ElMessage.error("恢复上传失败: " + (error.message || "未知错误"));
    addLog("ERROR", "恢复上传失败: " + (error.message || "未知错误"));
    uploading.value = false;
  }
}

// 取消上传
function cancelUpload() {
  uploadedFile.value = null;
  uploading.value = false;
  uploadPaused.value = false;
  uploadProgress.value = 0;
  uploadedChunks.value = 0;
  totalChunks.value = 0;
  uploadId.value = "";
  fileHash.value = "";
  datasetForm.name = "";
  datasetForm.taskType = "classification"; // 重置为默认值
  datasetForm.description = "";
  uploadLogs.value = [];
  emit("upload-cancel");
  ElMessage.info("已取消上传");
}

// 继续到分析步骤
function proceedToAnalysis() {
  // 由父组件处理
  emit("upload-success");
}

// 格式化文件大小
function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

// 添加日志
function addLog(type: string, message: string) {
  const now = new Date();
  const time = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}:${now.getSeconds().toString().padStart(2, "0")}`;
  uploadLogs.value.push({ time, message, type: type.toLowerCase() });

  // 保持最多 50 条日志
  if (uploadLogs.value.length > 50) {
    uploadLogs.value.shift();
  }
}

// 暴露方法给父组件
defineExpose({
  cancelUpload,
});
</script>

<script lang="ts">
export default {
  name: "DatasetUpload",
};
</script>

<style lang="scss" scoped>
.dataset-upload-container {
  width: 100%;
  max-width: 900px;
  margin: 0 auto;
}

.upload-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 48px 24px;
  background: linear-gradient(145deg, var(--el-bg-color) 0%, var(--el-bg-color-page) 100%);
  border: 2px dashed var(--el-border-color);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover,
  &.upload-zone-dragover {
    border-color: var(--el-color-primary);
    background: linear-gradient(
      145deg,
      rgba(var(--el-color-primary-rgb), 0.05) 0%,
      rgba(var(--el-color-primary-rgb), 0.02) 100%
    );
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(var(--el-color-primary-rgb), 0.15);
  }
}

.upload-icon {
  margin-bottom: 24px;
  animation: bounce 2s ease-in-out infinite;
}

@keyframes bounce {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.upload-text {
  text-align: center;

  .upload-title {
    margin: 0 0 12px;
    font-size: 20px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }

  .upload-hint {
    margin: 6px 0;
    font-size: 14px;
    color: var(--el-text-color-secondary);
  }
}

.upload-progress-container {
  .file-info-card {
    border-radius: 16px;
    overflow: hidden;
  }

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .file-info {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 12px;
    background: var(--el-fill-color-light);
    border-radius: 12px;

    .file-icon {
      flex-shrink: 0;
    }

    .file-details {
      flex: 1;
      min-width: 0;

      .file-name {
        margin-bottom: 4px;
        overflow: hidden;
        text-overflow: ellipsis;
        font-size: 16px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        white-space: nowrap;
      }

      .file-size {
        font-size: 14px;
        color: var(--el-text-color-secondary);
      }
    }
  }

  .progress-section {
    margin-top: 24px;

    .progress-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;

      .progress-label {
        font-size: 14px;
        font-weight: 600;
        color: var(--el-text-color-primary);
      }

      .progress-value {
        font-size: 16px;
        font-weight: 700;
        color: var(--el-color-primary);
      }
    }

    .progress-stats {
      display: flex;
      gap: 24px;
      align-items: center;
      justify-content: space-around;
      margin-top: 16px;
      padding: 12px;
      background: var(--el-fill-color-light);
      border-radius: 8px;

      .stat-item {
        display: flex;
        gap: 6px;
        align-items: center;
        font-size: 13px;
        color: var(--el-text-color-regular);

        .el-icon {
          color: var(--el-color-primary);
        }
      }
    }
  }

  .action-buttons {
    display: flex;
    gap: 12px;
    align-items: center;
    justify-content: center;
    margin-top: 24px;
  }

  .log-card {
    border-radius: 16px;
    overflow: hidden;

    .log-container {
      max-height: 300px;
      overflow-y: auto;
      font-family: "Courier New", monospace;
      font-size: 13px;
      line-height: 1.6;
      background: var(--el-fill-color-darker);
      border-radius: 8px;

      .log-item {
        display: flex;
        gap: 12px;
        padding: 8px 12px;
        border-bottom: 1px solid var(--el-border-color-lighter);

        &:last-child {
          border-bottom: none;
        }

        .log-time {
          flex-shrink: 0;
          color: var(--el-text-color-secondary);
        }

        .log-message {
          flex: 1;
          color: var(--el-text-color-regular);
        }

        &.log-info .log-message {
          color: var(--el-color-info);
        }

        &.log-success .log-message {
          color: var(--el-color-success);
        }

        &.log-warn .log-message {
          color: var(--el-color-warning);
        }

        &.log-error .log-message {
          color: var(--el-color-danger);
        }
      }
    }
  }
}
</style>

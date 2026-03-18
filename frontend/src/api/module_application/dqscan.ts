import request from "@/utils/request";

// dqscan 前端 API 封装：与后端 `backend/app/plugin/module_application/dqscan/controller.py` 一一对应
// - 上传文件 → 返回 file_id
// - 创建任务 → 返回 task_id
// - 查询任务/获取结果/下载产物
const API_PATH = "/application/dqscan";

export interface DQScanUploadOut {
  file_id: string;
  filename: string;
  file_size: number;
}

export interface DQScanAlgorithmOut {
  name: string;
  label: string;
  description: string;
  params_schema: Record<string, any>;
}

export interface DQScanDefectCatalogOut {
  modality: string;
  engine: string;
  tree: any[];
}

export interface DQScanCreateTaskIn {
  file_id: string;
  baseline_file_id?: string;
  algorithm: string;
  params?: Record<string, any>;
  data_type?: string;
}

export type DQScanTaskStatus = "PENDING" | "RUNNING" | "SUCCESS" | "FAILED";

export interface DQScanTaskOut {
  task_id: string;
  status: DQScanTaskStatus;
  progress: number;
  started_at?: number | null;
  ended_at?: number | null;
  error?: string | null;
  baseline_file_id?: string | null;
  result_file_id?: string | null;
}

export interface DQScanResult {
  summary: Record<string, any>;
  modules?: Record<string, any>;
  defects?: Record<string, any>;
  reports?: Record<string, any>;
}

export interface DQScanReportPayload {
  metadata?: Record<string, any>;
  scoring?: Record<string, any>;
  results?: Record<string, any>;
  error?: string;
}

export interface DQScanReportsOut {
  reports: Record<string, DQScanReportPayload>;
}

const DQScanAPI = {
  listAlgorithms() {
    return request<ApiResponse<DQScanAlgorithmOut[]>>({
      url: `${API_PATH}/algorithms`,
      method: "get",
    });
  },

  getDefectsCatalog(opts?: { modality?: string; engine?: string }) {
    return request<ApiResponse<DQScanDefectCatalogOut>>({
      url: `${API_PATH}/defects`,
      method: "get",
      params: { modality: opts?.modality ?? "tabular", engine: opts?.engine },
    });
  },

  uploadFile(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    return request<ApiResponse<DQScanUploadOut>>({
      url: `${API_PATH}/upload`,
      method: "post",
      data: formData,
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  createTask(body: DQScanCreateTaskIn) {
    return request<ApiResponse<{ task_id: string }>>({
      url: `${API_PATH}/tasks`,
      method: "post",
      data: body,
    });
  },

  getTask(taskId: string) {
    return request<ApiResponse<DQScanTaskOut>>({
      url: `${API_PATH}/tasks/${taskId}`,
      method: "get",
    });
  },

  getResult(taskId: string) {
    return request<ApiResponse<DQScanResult>>({
      url: `${API_PATH}/tasks/${taskId}/result`,
      method: "get",
    });
  },

  downloadResult(taskId: string) {
    return request<Blob>({
      url: `${API_PATH}/tasks/${taskId}/download`,
      method: "get",
      responseType: "blob",
    });
  },

  downloadArtifact(taskId: string, path: string) {
    return request<Blob>({
      url: `${API_PATH}/tasks/${taskId}/artifact`,
      method: "get",
      params: { path },
      responseType: "blob",
    });
  },

  getReports(taskId: string, opts?: { module?: string; report_type?: "json" | "summary" }) {
    return request<ApiResponse<DQScanReportsOut>>({
      url: `${API_PATH}/tasks/${taskId}/report`,
      method: "get",
      params: { module: opts?.module, report_type: opts?.report_type ?? "json" },
    });
  },
};

export default DQScanAPI;

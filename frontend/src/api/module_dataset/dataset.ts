import request from "@/utils/request";

const API_PATH = "/dataset/data";

export const DatasetAPI = {
  /**
   * 上传初始化
   * @param data 上传初始化请求数据
   */
  uploadInit(data: UploadInitRequest) {
    return request<ApiResponse<UploadInitResponse>>({
      url: `${API_PATH}/upload/init`,
      method: "post",
      data,
    });
  },

  /**
   * 分片上传
   * @param data 分片上传数据
   */
  uploadChunk(data: FormData) {
    return request<ApiResponse<ChunkUploadResponse>>({
      url: `${API_PATH}/upload/chunk`,
      method: "post",
      data,
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },

  /**
   * 上传完成
   * @param data 上传完成请求数据
   */
  uploadComplete(data: UploadCompleteRequest) {
    return request<ApiResponse<UploadCompleteResponse>>({
      url: `${API_PATH}/upload/complete`,
      method: "post",
      data,
    });
  },

  /**
   * 断点续传查询
   * @param data 断点续传请求数据
   */
  resumeUpload(data: ResumeUploadRequest) {
    return request<ApiResponse<ResumeUploadResponse>>({
      url: `${API_PATH}/upload/resume`,
      method: "post",
      data,
    });
  },

  /**
   * 获取数据集详情
   * @param id 数据集ID
   */
  getDetail(id: number) {
    return request<ApiResponse<DatasetInfo>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
    });
  },

  /**
   * 查询数据集列表
   * @param query 查询参数
   */
  getList(query: DatasetPageQuery) {
    return request<ApiResponse<PageResult<DatasetInfo[]>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  /**
   * 更新数据集
   * @param id 数据集ID
   * @param data 更新数据
   */
  update(id: number, data: DatasetUpdateForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data,
    });
  },

  /**
   * 删除数据集
   * @param ids 数据集ID列表
   * @param deleteFile 是否删除存储文件
   */
  delete(ids: number[], deleteFile: boolean = false) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: { ids, delete_file: deleteFile },
    });
  },

  /**
   * 获取数据集统计信息
   */
  getStatistics() {
    return request<ApiResponse<DatasetStatistics>>({
      url: `${API_PATH}/statistics`,
      method: "get",
    });
  },

  /**
   * 启动数据集分析
   * @param id 数据集ID
   */
  analyze(id: number) {
    return request<ApiResponse<any>>({
      url: `${API_PATH}/analyze/${id}`,
      method: "post",
    });
  },

  /**
   * 查询分析状态
   * @param id 数据集ID
   */
  getAnalyzeStatus(id: number) {
    return request<ApiResponse<DatasetAnalysisStatus>>({
      url: `${API_PATH}/analyze/status/${id}`,
      method: "get",
    });
  },

  /**
   * 数据集预览
   * @param id 数据集ID
   * @param limit 预览数量
   */
  preview(id: number, limit: number = 5) {
    return request<ApiResponse<DatasetPreviewResponse>>({
      url: `${API_PATH}/preview/${id}`,
      method: "get",
      params: { limit },
    });
  },
};

export default DatasetAPI;

// ==================== 类型定义 ====================

/**
 * 上传初始化请求
 */
export interface UploadInitRequest {
  filename: string;
  file_size: number;
  file_hash: string;
  chunk_size?: number;
  name?: string;
  task_type?: string;
}

/**
 * 分片信息
 */
export interface ChunkInfo {
  chunk_index: number;
  chunk_size: number;
  is_uploaded: boolean;
}

/**
 * 上传初始化响应
 */
export interface UploadInitResponse {
  upload_id: string;
  dataset_id?: number;
  storage_path: string;
  total_chunks: number;
  chunk_size: number;
  chunks: ChunkInfo[];
  file_exists: boolean;
  uploaded_chunks: number[];
}

/**
 * 分片上传响应
 */
export interface ChunkUploadResponse {
  upload_id: string;
  chunk_index: number;
  chunk_uploaded: boolean;
  progress: number;
  uploaded_chunks: number;
  total_chunks: number;
}

/**
 * 上传完成请求
 */
export interface UploadCompleteRequest {
  upload_id: string;
  verify_hash?: boolean;
}

/**
 * 上传完成响应
 */
export interface UploadCompleteResponse {
  dataset_id: number;
  upload_id: string;
  storage_path: string;
  file_size: number;
  file_hash: string;
  hash_verified: boolean;
  merge_success: boolean;
  message: string;
}

/**
 * 断点续传请求
 */
export interface ResumeUploadRequest {
  file_hash: string;
}

/**
 * 断点续传响应
 */
export interface ResumeUploadResponse {
  can_resume: boolean;
  upload_id?: string;
  uploaded_chunks: number[];
  total_chunks?: number;
  progress: number;
  file_exists: boolean;
  dataset_id?: number;
}

/**
 * 数据集分页查询参数
 */
export interface DatasetPageQuery extends PageQuery {
  name?: string;
  original_filename?: string;
  upload_status?: string;
  modality?: string;
  status?: string;
  created_time?: string[];
  file_size_min?: number;
  file_size_max?: number;
}

/**
 * 数据集信息
 */
export interface DatasetInfo extends BaseType {
  name: string;
  original_filename: string;
  file_size: number;
  storage_path: string;
  file_hash: string;
  upload_id?: string;
  upload_status: string;
  modality: string;
  task_type?: string;
  sample_count?: number;
  class_count?: number;
  dataset_metadata?: Record<string, any>;
  analysis_result?: Record<string, any>;
  created_by?: CommonType;
  updated_by?: CommonType;
}

/**
 * 数据集更新表单
 */
export interface DatasetUpdateForm {
  name?: string;
  status?: string;
  description?: string;
  modality?: string;
  sample_count?: number;
  class_count?: number;
  dataset_metadata?: Record<string, any>;
  analysis_result?: Record<string, any>;
}

/**
 * 数据集统计信息
 */
export interface DatasetStatistics {
  total_count: number;
  completed_count: number;
  uploading_count: number;
  failed_count: number;
  total_size: number;
  modality_stats: Record<
    string,
    {
      count: number;
      total_size: number;
    }
  >;
}

/**
 * 数据集分析状态
 */
export interface DatasetAnalysisStatus {
  dataset_id: number;
  modality: string;
  sample_count?: number;
  class_count?: number;
  analysis_result?: Record<string, any>;
  status: string;
}

/**
 * 数据集预览响应
 */
export interface DatasetPreviewResponse {
  dataset_id: number;
  total_previewed: number;
  items: Array<{
    filename: string;
    size: number;
    compressed_size: number;
    extension: string;
  }>;
}

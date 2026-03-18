import request from "@/utils/request";

const API_PATH = "/train";

const ModelAPI = {
  /**
   * 模型推荐
   * @param data 推荐请求数据
   */
  recommend(data: ModelRecommendationRequest) {
    return request<ApiResponse<ModelRecommendationResponse>>({
      url: `${API_PATH}/recommend`,
      method: "post",
      data,
    });
  },

  /**
   * 获取模型详情
   * @param id 模型ID
   */
  getDetail(id: number) {
    return request<ApiResponse<ModelDetailInfo>>({
      url: `${API_PATH}/model/detail/${id}`,
      method: "get",
    });
  },

  /**
   * 查询模型列表
   * @param query 查询参数
   */
  getList(query: ModelPageQuery) {
    return request<ApiResponse<PageResult<ModelInfo[]>>>({
      url: `${API_PATH}/model/list`,
      method: "get",
      params: query,
    });
  },

  /**
   * 创建模型配置
   * @param data 模型配置数据
   */
  create(data: ModelCreateForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/model/create`,
      method: "post",
      data,
    });
  },

  /**
   * 更新模型配置
   * @param id 模型ID
   * @param data 更新数据
   */
  update(id: number, data: ModelUpdateForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/model/update/${id}`,
      method: "put",
      data,
    });
  },

  /**
   * 删除模型配置
   * @param ids 模型ID列表
   */
  delete(ids: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/model/delete`,
      method: "delete",
      data: { ids },
    });
  },

  /**
   * 获取模型统计信息
   */
  getStatistics() {
    return request<ApiResponse<ModelStatistics>>({
      url: `${API_PATH}/model/statistics`,
      method: "get",
    });
  },

  /**
   * 获取热门模型
   * @param limit 返回数量
   */
  getPopular(limit: number = 10) {
    return request<ApiResponse<ModelInfo[]>>({
      url: `${API_PATH}/model/popular`,
      method: "get",
      params: { limit },
    });
  },

  /**
   * 按模态查询模型
   * @param modality 模态类型
   */
  getByModality(modality: string) {
    return request<ApiResponse<ModelInfo[]>>({
      url: `${API_PATH}/model/by-modality`,
      method: "get",
      params: { modality },
    });
  },

  /**
   * 按任务类型查询模型
   * @param taskType 任务类型
   */
  getByTask(taskType: string) {
    return request<ApiResponse<ModelInfo[]>>({
      url: `${API_PATH}/model/by-task`,
      method: "get",
      params: { task_type: taskType },
    });
  },

  /**
   * 按框架查询模型
   * @param framework 框架名称
   */
  getByFramework(framework: string) {
    return request<ApiResponse<ModelInfo[]>>({
      url: `${API_PATH}/model/by-framework`,
      method: "get",
      params: { framework },
    });
  },

  /**
   * 按标签搜索模型
   * @param tag 标签
   */
  searchByTag(tag: string) {
    return request<ApiResponse<ModelInfo[]>>({
      url: `${API_PATH}/model/search-by-tag`,
      method: "get",
      params: { tag },
    });
  },

  /**
   * 增加模型使用次数
   * @param id 模型ID
   */
  incrementUsage(id: number) {
    return request<ApiResponse>({
      url: `${API_PATH}/model/increment-usage/${id}`,
      method: "post",
    });
  },

  /**
   * 更新模型状态
   * @param id 模型ID
   * @param status 状态
   */
  updateStatus(id: number, status: string) {
    return request<ApiResponse>({
      url: `${API_PATH}/model/status/${id}`,
      method: "put",
      data: { status },
    });
  },
};

/**
 * 训练任务API
 */
const TrainTaskAPI = {
  /**
   * 创建训练任务
   * @param data 训练任务数据
   */
  create(data: TrainTaskCreateForm) {
    return request<ApiResponse<TrainTaskCreateResponse>>({
      url: `${API_PATH}/tasks`,
      method: "post",
      data,
    });
  },

  /**
   * 查询训练任务列表
   * @param query 查询参数
   */
  getList(query: TrainTaskPageQuery) {
    return request<ApiResponse<PageResult<TrainTaskInfo[]>>>({
      url: `${API_PATH}/tasks`,
      method: "get",
      params: query,
    });
  },

  /**
   * 获取训练任务详情
   * @param taskId 任务ID
   */
  getDetail(taskId: string) {
    return request<ApiResponse<TrainTaskDetailInfo>>({
      url: `${API_PATH}/tasks/${taskId}`,
      method: "get",
    });
  },

  /**
   * 获取训练任务状态
   * @param taskId 任务ID
   */
  getStatus(taskId: string) {
    return request<ApiResponse<TrainTaskStatusInfo>>({
      url: `${API_PATH}/tasks/${taskId}`,
      method: "get",
    });
  },

  /**
   * 更新训练任务
   * @param taskId 任务ID
   * @param data 更新数据
   */
  update(taskId: string, data: TrainTaskUpdateForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/tasks/${taskId}/status`,
      method: "put",
      data,
    });
  },

  /**
   * 删除训练任务
   * @param taskIds 任务ID列表
   */
  delete(taskIds: string[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/tasks/${taskIds[0]}`,
      method: "delete",
    });
  },

  /**
   * 取消训练任务
   * @param taskId 任务ID
   */
  cancel(taskId: string) {
    return request<ApiResponse>({
      url: `${API_PATH}/tasks/${taskId}/status`,
      method: "put",
      data: { status: 'cancelled' },
    });
  },

  /**
   * 暂停训练任务
   * @param taskId 任务ID
   */
  pause(taskId: string) {
    return request<ApiResponse>({
      url: `${API_PATH}/tasks/${taskId}/status`,
      method: "put",
      data: { status: 'paused' },
    });
  },

  /**
   * 恢复训练任务
   * @param taskId 任务ID
   */
  resume(taskId: string) {
    return request<ApiResponse>({
      url: `${API_PATH}/tasks/${taskId}/status`,
      method: "put",
      data: { status: 'running' },
    });
  },

  /**
   * 获取训练进度曲线
   * @param taskId 任务ID
   */
  getProgressCurve(taskId: string) {
    return request<ApiResponse<TrainProgressCurveResponse>>({
      url: `${API_PATH}/tasks/${taskId}/progress/curve`,
      method: "get",
    });
  },

  /**
   * 获取最新训练进度
   * @param taskId 任务ID
   */
  getLatestProgress(taskId: string) {
    return request<ApiResponse<TrainProgressInfo>>({
      url: `${API_PATH}/tasks/${taskId}/progress`,
      method: "get",
    });
  },

  /**
   * 获取训练进度历史
   * @param taskId 任务ID
   * @param query 查询参数
   */
  getProgressHistory(taskId: string, query?: TrainProgressQuery) {
    return request<ApiResponse<PageResult<TrainProgressInfo[]>>>({
      url: `${API_PATH}/tasks/${taskId}/progress/history`,
      method: "get",
      params: query,
    });
  },

  /**
   * 获取训练任务统计
   */
  getStatistics() {
    return request<ApiResponse<TrainTaskStatistics>>({
      url: `${API_PATH}/tasks/statistics`,
      method: "get",
    });
  },

  /**
   * 获取训练任务日志
   * @param taskId 任务ID
   * @param lines 返回最后N行日志
   */
  getLogs(taskId: string, lines: number = 100) {
    return request<ApiResponse<TrainTaskLogsResponse>>({
      url: `${API_PATH}/tasks/${taskId}/logs`,
      method: "get",
      params: { lines },
    });
  },

  /**
   * 获取用户的训练任务
   * @param query 查询参数
   */
  getMyTasks(query: TrainTaskPageQuery) {
    return request<ApiResponse<PageResult<TrainTaskInfo[]>>>({
      url: `${API_PATH}/tasks/my-tasks`,
      method: "get",
      params: query,
    });
  },

  /**
   * 下载训练产物（模型文件）
   * 使用 axios 携带 token 请求文件流，再由 Blob 触发浏览器下载
   * @param taskId 任务ID
   * @param filePath 文件相对路径（相对于任务目录）
   */
  async downloadModel(taskId: string, filePath: string): Promise<void> {
    // model_save_path 存的可能是绝对路径，artifact 接口只接受相对于任务目录的文件名
    // 统一将反斜杠转为正斜杠后取最后一段作为文件名传给接口
    const fileName = filePath.replace(/\\/g, "/").split("/").pop() || "model_file";
    // responseType=blob 时拦截器直接返回 AxiosResponse，response.data 就是 Blob
    const response = await request({
      url: `${API_PATH}/tasks/${taskId}/artifact`,
      method: "get",
      params: { path: fileName },
      responseType: "blob",
    }) as any;
    const blob: Blob = response.data;
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  },
};

// ==================== 类型定义 ====================

/**
 * 模型推荐请求
 */
export interface ModelRecommendationRequest {
  dataset_id: number;
  modality?: string;
  task_type?: string;
  top_k?: number;
  only_active?: boolean;
}

/**
 * 数据集信息（用于推荐响应）
 */
export interface DatasetInfoForRecommendation {
  dataset_id: number;
  name: string;
  modality: string;
  task_type?: string;
  sample_count?: number;
  class_count?: number;
  file_size: number;
}

/**
 * 模型推荐项
 */
export interface ModelRecommendationItem {
  model_id: number;
  model_name: string;
  display_name: string;
  model_version: string;
  description: string;
  framework: string;
  tags: string[];
  priority: number;
  match_score: number;
  recommendation_reason: string;
  key_metrics?: Record<string, any>;
  hardware_summary?: string;
  default_config_preview?: Record<string, any>;
}

/**
 * 模型推荐响应
 */
export interface ModelRecommendationResponse {
  dataset_info: DatasetInfoForRecommendation;
  total_recommended: number;
  recommendations: ModelRecommendationItem[];
  recommendation_metadata?: Record<string, any>;
}

/**
 * 模型分页查询参数
 */
export interface ModelPageQuery extends PageQuery {
  model_name?: string;
  display_name?: string;
  modality?: string;
  task_type?: string;
  framework?: string;
  status?: string;
  tags?: string;
}

/**
 * 模型基本信息
 */
export interface ModelInfo extends BaseType {
  model_name: string;
  display_name: string;
  model_version: string;
  supported_modalities: string;
  supported_task_types: string;
  description: string;
  architecture_summary?: string;
  framework: string;
  framework_version?: string;
  priority: number;
  status: string;
  usage_count: number;
  tags?: string;
  reference_url?: string;
  created_by?: CommonType;
  updated_by?: CommonType;
}

/**
 * 模型详细信息
 */
export interface ModelDetailInfo extends ModelInfo {
  pretrained_weights?: Record<string, any>;
  default_train_config: Record<string, any>;
  performance_metrics?: Record<string, any>;
  hardware_requirements?: Record<string, any>;
  model_code_path?: string;
  config_template_path?: string;
  remarks?: string;
}

/**
 * 模型创建表单
 */
export interface ModelCreateForm {
  model_name: string;
  display_name: string;
  model_version?: string;
  supported_modalities: string;
  supported_task_types: string;
  description: string;
  architecture_summary?: string;
  pretrained_weights?: Record<string, any>;
  default_train_config: Record<string, any>;
  performance_metrics?: Record<string, any>;
  hardware_requirements?: Record<string, any>;
  framework: string;
  framework_version?: string;
  model_code_path?: string;
  config_template_path?: string;
  priority?: number;
  status?: string;
  tags?: string;
  reference_url?: string;
  remarks?: string;
}

/**
 * 模型更新表单
 */
export interface ModelUpdateForm {
  display_name?: string;
  model_version?: string;
  supported_modalities?: string;
  supported_task_types?: string;
  description?: string;
  architecture_summary?: string;
  pretrained_weights?: Record<string, any>;
  default_train_config?: Record<string, any>;
  performance_metrics?: Record<string, any>;
  hardware_requirements?: Record<string, any>;
  framework?: string;
  framework_version?: string;
  model_code_path?: string;
  config_template_path?: string;
  priority?: number;
  status?: string;
  tags?: string;
  reference_url?: string;
  remarks?: string;
}

/**
 * 模型统计信息
 */
export interface ModelStatistics {
  total_count: number;
  active_count: number;
  inactive_count: number;
  deprecated_count: number;
  framework_stats: Record<string, number>;
  modality_stats: Record<string, number>;
  task_type_stats: Record<string, number>;
  most_used_models: Array<{
    model_id: number;
    model_name: string;
    display_name: string;
    usage_count: number;
  }>;
}

// ==================== 训练任务类型定义 ====================

/**
 * 训练任务创建表单
 */
export interface TrainTaskCreateForm {
  dataset_id: number;
  model_config_id: number;
  train_config: TrainConfig;
  task_name?: string;
  description?: string;
}

/**
 * 训练配置
 */
export interface TrainConfig {
  epochs: number;
  batch_size: number;
  learning_rate: number;
  optimizer: string;
  loss_function: string;
  scheduler?: string;
  weight_decay?: number;
  momentum?: number;
  device?: string;
  num_workers?: number;
  save_best_only?: boolean;
  early_stopping?: boolean;
  early_stopping_patience?: number;
  [key: string]: any;
}

/**
 * 训练任务创建响应
 */
export interface TrainTaskCreateResponse {
  task_id: string;
  status: string;
  message: string;
}

/**
 * 训练任务分页查询参数
 */
export interface TrainTaskPageQuery extends PageQuery {
  task_id?: string;
  status?: string;
  dataset_id?: number;
  model_config_id?: number;
  created_id?: number;
  start_time?: string;
  end_time?: string;
}

/**
 * 训练任务基本信息
 */
export interface TrainTaskInfo extends BaseType {
  task_id: string;
  status: string;
  dataset_id: number;
  dataset_name?: string;
  model_config_id: number;
  model_name?: string;
  model_save_path?: string;
  current_epoch: number;
  total_epochs: number;
  progress_percentage: number;
  actual_start_time?: string;
  actual_completion_time?: string;
  estimated_completion_time?: string;
  created_by?: CommonType;
  updated_by?: CommonType;
}

/**
 * 训练任务详细信息
 */
export interface TrainTaskDetailInfo extends TrainTaskInfo {
  dataset_info: Record<string, any>;
  model_config: Record<string, any>;
  train_config: TrainConfig;
  model_save_path?: string;
  log_file_path?: string;
  result_file_path?: string;
  final_metrics?: Record<string, any>;
  error_message?: string;
  remarks?: string;
}

/**
 * 训练任务状态信息
 */
export interface TrainTaskStatusInfo {
  task_id: string;
  status: string;
  current_epoch: number;
  total_epochs: number;
  progress_percentage: number;
  estimated_completion_time?: string;
  error_message?: string;
}

/**
 * 训练任务更新表单
 */
export interface TrainTaskUpdateForm {
  status?: string;
  remarks?: string;
}

/**
 * 训练进度信息
 */
export interface TrainProgressInfo {
  id: number;
  task_id: string;
  epoch: number;
  batch?: number;
  total_batches?: number;
  train_loss?: number;
  train_accuracy?: number;
  val_loss?: number;
  val_accuracy?: number;
  learning_rate?: number;
  epoch_progress?: number;
  overall_progress?: number;
  resource_metrics?: Record<string, any>;
  timestamp: string;
  additional_metrics?: Record<string, any>;
}

/**
 * 训练进度曲线响应
 */
export interface TrainProgressCurveResponse {
  task_id: string;
  total_epochs: number;
  current_epoch: number;
  data_points: Array<{
    epoch: number;
    train_loss?: number;
    train_accuracy?: number;
    val_loss?: number;
    val_accuracy?: number;
    learning_rate?: number;
    timestamp: string;
  }>;
}

/**
 * 训练进度查询参数
 */
export interface TrainProgressQuery extends PageQuery {
  epoch?: number;
  start_epoch?: number;
  end_epoch?: number;
}

/**
 * 训练任务统计信息
 */
export interface TrainTaskStatistics {
  total_count: number;
  created_count: number;
  pending_count: number;
  running_count: number;
  completed_count: number;
  failed_count: number;
  cancelled_count: number;
  status_distribution: Record<string, number>;
  recent_tasks: TrainTaskInfo[];
  average_duration?: number;
  success_rate?: number;
}

export interface TrainTaskLogItem {
  time: string;
  level: string;
  message: string;
}

export interface TrainTaskLogsResponse {
  task_id: string;
  logs: TrainTaskLogItem[];
  total_lines: number;
  returned_lines?: number;
  message?: string;
}



export { ModelAPI, TrainTaskAPI };
export default { ModelAPI, TrainTaskAPI };


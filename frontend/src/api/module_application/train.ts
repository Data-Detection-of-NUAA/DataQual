import request from "@/utils/request";

const API_PATH = "/train";

export const ModelAPI = {
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

export default ModelAPI;

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

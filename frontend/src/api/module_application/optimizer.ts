import request from "@/utils/request";

const API_PATH = "/application/optimizer";

const OptimizerAPI = {
  // ==================== 优化器任务管理接口 ====================

  listTask(query: OptimizerTaskPageQuery) {
    return request<ApiResponse<PageResult<OptimizerTaskTable[]>>>({
      url: `${API_PATH}/task/list`,
      method: "get",
      params: query,
    });
  },

  detailTask(query: number) {
    return request<ApiResponse<OptimizerTaskTable>>({
      url: `${API_PATH}/task/detail/${query}`,
      method: "get",
    });
  },

  createTask(body: OptimizerTaskForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/task/create`,
      method: "post",
      data: body,
    });
  },

  updateTask(id: number, body: OptimizerTaskForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/task/update/${id}`,
      method: "put",
      data: body,
    });
  },

  deleteTask(body: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/task/delete`,
      method: "delete",
      data: body,
    });
  },

  exportTask(body: OptimizerTaskPageQuery) {
    return request<Blob>({
      url: `${API_PATH}/task/export`,
      method: "post",
      data: body,
      responseType: "blob",
    });
  },

  clearTask() {
    return request<ApiResponse>({
      url: `${API_PATH}/task/clear`,
      method: "delete",
    });
  },

  runTask(id: number, body?: OptimizerTaskRunParams) {
    return request<ApiResponse<OptimizerTaskRunResult>>({
      url: `${API_PATH}/task/run/${id}`,
      method: "post",
      data: body,
    });
  },

  cancelTask(id: number) {
    return request<ApiResponse>({
      url: `${API_PATH}/task/cancel/${id}`,
      method: "put",
    });
  },

  // ==================== 优化器结果管理接口 ====================

  listResult(query: OptimizerResultPageQuery) {
    return request<ApiResponse<PageResult<OptimizerResultTable[]>>>({
      url: `${API_PATH}/result/list`,
      method: "get",
      params: query,
    });
  },

  detailResult(query: number) {
    return request<ApiResponse<OptimizerResultTable>>({
      url: `${API_PATH}/result/detail/${query}`,
      method: "get",
    });
  },

  createResult(body: OptimizerResultForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/result/create`,
      method: "post",
      data: body,
    });
  },

  updateResult(id: number, body: OptimizerResultForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/result/update/${id}`,
      method: "put",
      data: body,
    });
  },

  deleteResult(body: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/result/delete`,
      method: "delete",
      data: body,
    });
  },

  exportResult(body: OptimizerResultPageQuery) {
    return request<Blob>({
      url: `${API_PATH}/result/export`,
      method: "post",
      data: body,
      responseType: "blob",
    });
  },

  clearResult() {
    return request<ApiResponse>({
      url: `${API_PATH}/result/clear`,
      method: "delete",
    });
  },

  applyResult(id: number, body: OptimizerResultApplyParams) {
    return request<ApiResponse<OptimizerResultApplyResult>>({
      url: `${API_PATH}/result/apply/${id}`,
      method: "post",
      data: body,
    });
  },

  // ==================== 优化器执行日志管理接口 ====================

  listLog(query: OptimizerLogPageQuery) {
    return request<ApiResponse<PageResult<OptimizerLogTable[]>>>({
      url: `${API_PATH}/log/list`,
      method: "get",
      params: query,
    });
  },

  detailLog(query: number) {
    return request<ApiResponse<OptimizerLogTable>>({
      url: `${API_PATH}/log/detail/${query}`,
      method: "get",
    });
  },

  deleteLog(body: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/log/delete`,
      method: "delete",
      data: body,
    });
  },

  exportLog(body: OptimizerLogPageQuery) {
    return request<Blob>({
      url: `${API_PATH}/log/export`,
      method: "post",
      data: body,
      responseType: "blob",
    });
  },

  clearLog() {
    return request<ApiResponse>({
      url: `${API_PATH}/log/clear`,
      method: "delete",
    });
  },
};

export default OptimizerAPI;

// ==================== 优化器任务相关类型定义 ====================

export interface OptimizerTaskPageQuery extends PageQuery {
  name?: string;
  task_type?: string;
  status?: string;
  priority?: number;
  created_id?: number;
  updated_id?: number;
  created_time?: string[];
  updated_time?: string[];
}

export interface OptimizerTaskTable extends BaseType {
  name: string;
  description?: string;
  task_type: string;
  config: any;
  priority: number;
  created_by?: CommonType;
  updated_by?: CommonType;
}

export interface OptimizerTaskForm extends BaseFormType {
  name?: string;
  description?: string;
  task_type?: string;
  config?: any;
  priority?: number;
}

export interface OptimizerTaskRunParams {
  override_config?: any;
}

export interface OptimizerTaskRunResult {
  task_id: number;
  task_name: string;
  status: string;
  message: string;
}

// ==================== 优化器结果相关类型定义 ====================

export interface OptimizerResultPageQuery extends PageQuery {
  task_id?: number;
  result_type?: string;
  status?: string;
  min_score?: number;
  created_id?: number;
  updated_id?: number;
  created_time?: string[];
  updated_time?: string[];
}

export interface OptimizerResultTable extends BaseType {
  task_id: number;
  result_type: string;
  result_data: any;
  score?: number;
  improvement?: number;
  created_by?: CommonType;
  updated_by?: CommonType;
}

export interface OptimizerResultForm extends BaseFormType {
  task_id?: number;
  result_type?: string;
  result_data?: any;
  score?: number;
  improvement?: number;
}

export interface OptimizerResultApplyParams {
  apply_mode?: string;
  confirm?: boolean;
}

export interface OptimizerResultApplyResult {
  result_id: number;
  mode: string;
  status: string;
  message: string;
  preview_data?: any;
}

// ==================== 优化器执行日志相关类型定义 ====================

export interface OptimizerLogPageQuery extends PageQuery {
  task_id?: number;
  status?: string;
  created_time?: string[];
}

export interface OptimizerLogTable extends BaseType {
  task_id: number;
  execution_time: number;
  error_message?: string;
  log_data?: any;
}

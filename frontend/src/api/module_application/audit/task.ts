import request from "@/utils/request";

const API_PATH = "/application/audit/task";

const EXECUTE_AUDIT_TIMEOUT = 60000;

const AuditTaskAPI = {
  // 获取任务列表
  listTask(query: AuditTaskPageQuery) {
    return request<ApiResponse<PageResult<AuditTaskTable[]>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  // 获取任务详情
  detailTask(id: number) {
    return request<ApiResponse<AuditTaskTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
    });
  },

  // 创建任务
  createTask(body: FormData) {
    return request<ApiResponse>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },

  // 更新任务
  updateTask(id: number, body: AuditTaskForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },

  // 删除任务
  deleteTask(ids: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: { ids },
    });
  },

  // 上传合规文件
  uploadRegulation(taskId: number, file: File) {
    const formData = new FormData();
    formData.append("file", file);
    // 从文件名提取文件类型
    const fileExtension = file.name.split('.').pop()?.toLowerCase() || 'txt';
    formData.append("file_type", fileExtension);
    return request<ApiResponse>({
      url: `${API_PATH}/${taskId}/upload-regulation`,
      method: "post",
      data: formData,
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },

  // 閫夋嫨宸插崟渚垮彂甯冪殑娉曡鏂囦欢
  useRegulation(taskId: number, regulationId: number) {
    return request<ApiResponse>({
      url: `${API_PATH}/${taskId}/use-regulation/${regulationId}`,
      method: "post",
    });
  },

  // AI 匹配规则
  aiMatchRules(taskId: number) {
    return request<ApiResponse<{ matched_rule_ids: number[]; matched_rules: MatchedRuleSummary[] }>>({
      url: `${API_PATH}/${taskId}/match-rules`,
      method: "post",
    });
  },

  // 确认规则
  confirmRules(taskId: number, ruleIds: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/${taskId}/confirm-rules`,
      method: "post",
      data: { selected_rules: ruleIds },
    });
  },

  // 上传数据集
  uploadDataset(taskId: number, file: File) {
    const formData = new FormData();
    formData.append("file", file);
    // 从文件名提取文件类型
    const fileExtension = file.name.split('.').pop()?.toLowerCase() || 'csv';
    formData.append("file_type", fileExtension);
    return request<ApiResponse>({
      url: `${API_PATH}/${taskId}/upload-dataset`,
      method: "post",
      data: formData,
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },

  // 执行审计
  executeAudit(taskId: number) {
    return request<ApiResponse>({
      url: `${API_PATH}/${taskId}/execute`,
      method: "post",
      timeout: EXECUTE_AUDIT_TIMEOUT,
    });
  },

  // 下载审计报告
  downloadReport(taskId: number) {
    return request<Blob>({
      url: `${API_PATH}/${taskId}/download-report`,
      method: "get",
      responseType: "blob",
    });
  },

  // 获取任务错误列表
  getTaskErrors(taskId: number, query: AuditErrorPageQuery) {
    return request<ApiResponse<PageResult<AuditErrorTable[]>>>({
      url: `${API_PATH}/${taskId}/errors`,
      method: "get",
      params: query,
    });
  },
};

export default AuditTaskAPI;

// 查询参数
export interface AuditTaskPageQuery extends PageQuery {
  task_name?: string;
  task_status?: string;
  created_time?: string[];
}

export interface AuditErrorPageQuery extends PageQuery {
  error_type?: string;
  severity?: string;
}

// 表格数据
export interface AuditTaskTable extends BaseType {
  task_name: string;
  task_status: string;
  description?: string;
  regulation_file_type?: string;
  regulation_file_path?: string;
  regulation_file_name?: string;
  regulation_id?: number;
  dataset_file_type?: string;
  dataset_file_path?: string;
  dataset_file_name?: string;
  matched_rule_ids?: number[];
  selected_rule_ids?: number[];
  total_records?: number;
  error_records?: number;
  audit_report_path?: string;
  created_by?: string;
}

export interface AuditErrorTable extends BaseType {
  task_id?: number;
  row_number?: number;
  column_name?: string;
  field_name?: string;
  original_value?: string;
  error_type: string;
  error_message: string;
  severity?: string;
  rule_id?: number;
}

// 表单数据
export interface AuditTaskForm extends BaseFormType {
  task_name: string;
  task_status?: string;
  selected_rules?: number[];
}

export interface MatchedRuleSummary {
  id: number;
  rule_code: string;
  rule_name: string;
  rule_type: string;
  rule_description?: string;
  severity?: string;
  ai_matched?: boolean;
}

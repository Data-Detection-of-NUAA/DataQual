import request from "@/utils/request";

const API_PATH = "/audit/rule";

const AuditRuleAPI = {
  // 获取规则列表
  listRule(query: AuditRulePageQuery) {
    return request<ApiResponse<PageResult<AuditRuleTable[]>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  // 获取规则详情
  detailRule(id: number) {
    return request<ApiResponse<AuditRuleTable>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
    });
  },

  // 创建规则
  createRule(body: AuditRuleForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  // 更新规则
  updateRule(id: number, body: AuditRuleForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/update`,
      method: "put",
      params: { id },
      data: body,
    });
  },

  // 删除规则
  deleteRule(ids: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: { ids },
    });
  },

  // 批量启用/禁用规则
  batchRule(body: BatchType) {
    return request<ApiResponse>({
      url: `${API_PATH}/batch`,
      method: "patch",
      data: body,
    });
  },

  // 获取所有规则选项（用于任务中选择规则）
  optionRule() {
    return request<ApiResponse<AuditRuleTable[]>>({
      url: `${API_PATH}/options`,
      method: "get",
    });
  },
};

export default AuditRuleAPI;

// 查询参数
export interface AuditRulePageQuery extends PageQuery {
  rule_code?: string;
  rule_name?: string;
  rule_type?: string;
  field_name?: string;
  is_active?: number;
  created_time?: string[];
}

// 表格数据
export interface AuditRuleTable extends BaseType {
  rule_code: string;
  rule_name: string;
  rule_type: string;
  field_name?: string;
  validation_rule?: string;
  error_message?: string;
  is_active: number;
  rule_description?: string;
  rule_expression?: string;
  severity?: string;
  remark?: string;
}

// 表单数据
export interface AuditRuleForm extends BaseFormType {
  rule_code: string;
  rule_name: string;
  rule_type: string;
  field_name?: string;
  validation_rule?: string;
  error_message?: string;
  is_active: number;
  rule_description?: string;
  rule_expression?: string;
  severity?: string;
  remark?: string;
}

import request from "@/utils/request";

const API_PATH = "/optimizer/diagnosis";

const OptimizerAPI = {
  // ==================== 数据集管理 ====================

  /**
   * 获取多模态数据集列表
   */
  getDatasetList(params?: any) {
    return request({
      url: `/optimizer/datasets`,
      method: "get",
      params,
    });
  },

  /**
   * 获取数据集详情
   */
  getDatasetDetail(datasetId: string) {
    return request({
      url: `/optimizer/datasets/${datasetId}`,
      method: "get",
    });
  },

  // ==================== Step 1: 诊断概览 ====================

  /**
   * 获取诊断概览数据
   */
  getDiagnosisOverview() {
    return request({
      url: `${API_PATH}/overview`,
      method: "get",
    });
  },

  /**
   * 获取优化建议
   */
  getSuggestions() {
    return request({
      url: `${API_PATH}/suggestions`,
      method: "get",
    });
  },

  /**
   * 获取数据集模型评估结果（包含各类别 AP）
   */
  getModelEvaluation(datasetId: string) {
    return request({
      url: `/optimizer/diagnosis/${datasetId}/evaluation`,
      method: "get",
    });
  },

  /**
   * 获取有问题的样本 ID 列表
   */
  getProblematicSamples(datasetId: string) {
    return request({
      url: `/optimizer/diagnosis/${datasetId}/problematic-samples`,
      method: "get",
    });
  },

  // ==================== Step 2: 策略配置 ====================

  /**
   * 保存策略配置
   */
  saveStrategyConfig(data: any) {
    return request({
      url: `/optimizer/strategy/config`,
      method: "post",
      data: data,
    });
  },

  /**
   * 获取策略配置
   */
  getStrategyConfig() {
    return request({
      url: `/optimizer/strategy/config`,
      method: "get",
    });
  },

  /**
   * 生成候选数据集
   */
  generateCandidates(data: any) {
    return request({
      url: `/optimizer/strategy/generate`,
      method: "post",
      data: data,
    });
  },

  /**
   * 获取优化估算
   */
  getEstimation(data: any) {
    return request({
      url: `/optimizer/strategy/estimate`,
      method: "post",
      data: data,
    });
  },

  /**
   * 获取缺陷特征分析
   */
  getDefectAnalysis(datasetId: string) {
    return request({
      url: `/optimizer/strategy/${datasetId}/defect-analysis`,
      method: "get",
    });
  },

  /**
   * 生成补数方案
   */
  generateAugmentationPlan(datasetId: string, strategies: any) {
    return request({
      url: `/optimizer/strategy/${datasetId}/generate-plan`,
      method: "post",
      data: strategies,
    });
  },

  // ==================== Step 3: 补数审核 ====================

  /**
   * 获取候选数据列表
   */
  getCandidates(params?: any) {
    return request({
      url: `/optimizer/review/candidates`,
      method: "get",
      params,
    });
  },

  /**
   * 批量采纳
   */
  batchAccept(candidateIds: string[]) {
    return request({
      url: `/optimizer/review/batch-accept`,
      method: "post",
      data: candidateIds,
    });
  },

  /**
   * 批量拒绝
   */
  batchReject(candidateIds: string[]) {
    return request({
      url: `/optimizer/review/batch-reject`,
      method: "post",
      data: candidateIds,
    });
  },

  /**
   * 采纳单条数据
   */
  acceptCandidate(candidateId: string) {
    return request({
      url: `/optimizer/review/${candidateId}/accept`,
      method: "post",
    });
  },

  /**
   * 拒绝单条数据
   */
  rejectCandidate(candidateId: string) {
    return request({
      url: `/optimizer/review/${candidateId}/reject`,
      method: "post",
    });
  },

  /**
   * 获取补数方案列表
   */
  getAugmentationPlans(datasetId: string) {
    return request({
      url: `/optimizer/review/${datasetId}/plans`,
      method: "get",
    });
  },

  /**
   * 采纳方案
   */
  acceptPlan(datasetId: string, planId: string) {
    return request({
      url: `/optimizer/review/${datasetId}/plans/${planId}/accept`,
      method: "post",
    });
  },

  /**
   * 拒绝方案
   */
  rejectPlan(datasetId: string, planId: string) {
    return request({
      url: `/optimizer/review/${datasetId}/plans/${planId}/reject`,
      method: "post",
    });
  },

  // ==================== Step 4: 执行确认 ====================

  /**
   * 执行优化任务
   */
  executeOptimization(data: any) {
    return request({
      url: `/optimizer/execution/execute`,
      method: "post",
      data: data,
    });
  },

  /**
   * 获取执行进度
   */
  getProgress() {
    return request({
      url: `/optimizer/execution/progress`,
      method: "get",
    });
  },

  /**
   * 获取执行结果（包含 mAP 对比）
   */
  getExecutionResult(datasetId: string) {
    return request({
      url: `/optimizer/execution/${datasetId}/result`,
      method: "get",
    });
  },

  /**
   * 导出优化方案
   */
  exportPlan(data: any, format: string = "json") {
    return request({
      url: `/optimizer/execution/export`,
      method: "post",
      params: { format },
      data,
    });
  },

  /**
   * 导出优化报告
   */
  exportReport(datasetId: string, format: 'pdf' | 'json') {
    return request({
      url: `/optimizer/execution/${datasetId}/export-report`,
      method: "get",
      params: { format },
      responseType: 'blob',
    });
  },

  /**
   * 下载新增样本包
   */
  downloadDataset(data: any) {
    return request({
      url: `/optimizer/execution/download`,
      method: "post",
      data,
      responseType: "blob",
    });
  },

  /**
   * 下载优化后数据集
   */
  downloadOptimizedDataset(datasetId: string) {
    return request({
      url: `/optimizer/execution/${datasetId}/download-dataset`,
      method: "get",
      responseType: 'blob',
    });
  },

  /**
   * 触发训练
   */
  triggerTraining(data: any) {
    return request({
      url: `/optimizer/execution/trigger-training`,
      method: "post",
      data,
    });
  },
};

export default OptimizerAPI;

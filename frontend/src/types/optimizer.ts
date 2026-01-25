/** 诊断概览相关类型 */

/** 质量探测问题 */
export interface QualityDetectionIssue {
  type: string;
  count: number;
  severity: 'low' | 'medium' | 'high';
  confidence: number;
}

/** 鲁棒性问题 */
export interface RobustnessIssue {
  attack_type: string;
  count: number;
  vulnerability_score: number;
}

/** 合规问题 */
export interface ComplianceIssue {
  issue_type: string;
  count: number;
  severity: 'info' | 'warning' | 'error';
}

/** 模型评估结果 */
export interface ModelEvaluation {
  metric_name: string;
  current_value: number;
  low_ap_categories: string[];
}

/** 诊断概览响应 */
export interface DiagnosisOverviewResponse {
  code: number;
  msg: string;
  data: {
    quality_issues: QualityDetectionIssue[];
    robustness_issues: RobustnessIssue[];
    compliance_issues: ComplianceIssue[];
    model_evaluation?: ModelEvaluation;
  };
}

/** 优化建议 */
export interface SuggestionsResponse {
  code: number;
  msg: string;
  data: {
    suggestions: Array<{
      type: 'info' | 'warning' | 'error';
      message: string;
      recommended_action: string;
    }>;
  };
}

// ==================== 策略配置相关类型 ====================

/** 增强策略配置 */
export interface AugmentationStrategy {
  noise_level: number;
  blur_radius: number;
  enable_adversarial: boolean;
}

/** 检索策略配置 */
export interface RetrievalStrategy {
  data_source: string;
  target_count: number;
}

/** GenAI策略配置 */
export interface GenAIStrategy {
  model: string;
  scenario: string;
  batch_size: number;
}

/** 策略配置 */
export interface StrategyConfig {
  augmentation: AugmentationStrategy;
  retrieval: RetrievalStrategy;
  genai: GenAIStrategy;
}

/** 策略配置响应 */
export interface StrategyConfigResponse {
  code: number;
  msg: string;
  data: StrategyConfig;
}

/** 估算响应 */
export interface EstimationResponse {
  code: number;
  msg: string;
  data: {
    retrieval_count: number;
    genai_count: number;
    augmentation_count: number;
    total_new_count: number;
    predicted_map: number;
    map_improvement: number;
    gpu_time_hours: number;
    storage_gb: number;
    estimated_cost_usd: number;
  };
}

// ==================== 候选数据相关类型 ====================

/** 候选数据 */
export interface CandidateData {
  id: string;
  source: 'augmentation' | 'retrieval' | 'genai';
  category: string;
  confidence: number;
  thumbnail: string;
  description: string;
}

/** 候选数据列表响应 */
export interface CandidateListResponse {
  code: number;
  msg: string;
  data: {
    total: number;
    items: CandidateData[];
    page: number;
    page_size: number;
  };
}

// ==================== 执行确认相关类型 ====================

/** 任务摘要 */
export interface ExecutionTaskSummary {
  retrieval_count: number;
  genai_count: number;
  augmentation_count: number;
  total_new_count: number;
}

/** 资源预测 */
export interface ResourceForecast {
  gpu_time_hours: number;
  storage_gb: number;
  estimated_cost_usd: number;
}

/** 流程进度 */
export interface ProcessProgress {
  task_name: string;
  progress: number;
  status: 'pending' | 'in_progress' | 'completed';
  log_url?: string;
}

/** 执行结果响应 */
export interface ExecutionResultResponse {
  code: number;
  msg: string;
  data: {
    task_summary: ExecutionTaskSummary;
    resource_forecast: ResourceForecast;
    progress: ProcessProgress[];
    predicted_map: number;
    map_improvement: number;
  };
}

/** 进度查询响应 */
export interface ProgressResponse {
  code: number;
  msg: string;
  data: {
    current_stage: string;
    overall_progress: number;
    stages: ProcessProgress[];
  };
}

// ==================== 新增类型定义 ====================

/** 数据集信息 */
export interface DatasetInfo {
  id: string;
  name: string;
  dataType: 'image' | 'text' | 'audio' | 'multimodal';
  sampleCount: number;
  currentMap: number;
  status: 'pending' | 'in_progress' | 'completed';
  createdAt: string;
  updatedAt: string;
}

/** 数据集列表响应 */
export interface DatasetListResponse {
  code: number;
  msg: string;
  data: {
    total: number;
    items: DatasetInfo[];
    page: number;
    page_size: number;
  };
}

/** 类别 AP 信息 */
export interface CategoryAP {
  name: string;
  ap: number;
  dataTypes: string[];
}

/** 模型评估详情 */
export interface ModelEvaluationDetail {
  currentMap: number;
  categories: CategoryAP[];
  lowAPCategories: CategoryAP[];
}

/** 模型评估响应 */
export interface ModelEvaluationResponse {
  code: number;
  msg: string;
  data: ModelEvaluationDetail;
}

/** 有问题的样本列表响应 */
export interface ProblematicSamplesResponse {
  code: number;
  msg: string;
  data: {
    sampleIds: string[];
    totalCount: number;
  };
}

/** 缺陷特征 */
export interface DefectFeature {
  id: string;
  label: string;
  type: 'annotation_error' | 'distribution_shift' | 'adversarial_vulnerability';
  typeName: string;
  affectedCategories: string[];
  sampleCount: number;
  ap: number;
  dataTypes: string[];
  augmentationStrategy: any;
  retrievalStrategy: any;
}

/** 缺陷分析响应 */
export interface DefectAnalysisResponse {
  code: number;
  msg: string;
  data: {
    defectFeatures: DefectFeature[];
  };
}

/** 补数方案 */
export interface AugmentationPlan {
  id: string;
  title: string;
  strategyType: 'augmentation' | 'retrieval';
  defectTypeName: string;
  targetCategories: string[];
  dataTypes: string[];
  candidateCount: number;
  candidates: CandidateData[];
  status: 'pending' | 'accepted' | 'rejected';
}

/** 补数方案列表响应 */
export interface AugmentationPlansResponse {
  code: number;
  msg: string;
  data: {
    plans: AugmentationPlan[];
  };
}

/** 执行结果对比 */
export interface ExecutionResultComparison {
  originalMap: number;
  finalMap: number;
  improvement: number;
  categoryComparison: Array<{
    name: string;
    originalAP: number;
    finalAP: number;
  }>;
}

/** 执行结果对比响应 */
export interface ExecutionResultComparisonResponse {
  code: number;
  msg: string;
  data: ExecutionResultComparison;
}


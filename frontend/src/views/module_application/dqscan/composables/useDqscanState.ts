/**
 * useDqscanState - 共享状态管理（provide/inject 模式）
 * 所有跨步骤共享的 ref/reactive/computed/方法 都集中在这里。
 */
import { type InjectionKey, type Ref } from "vue";
import type { UploadFile } from "element-plus";
import DQScanAPI, { type DQScanAlgorithmOut, type DQScanUploadOut } from "@/api/module_application/dqscan";

// ───────────────────────── 类型 ─────────────────────────
export type TaskStatus = "IDLE" | "PENDING" | "RUNNING" | "SUCCESS" | "FAILED";
export type ModuleKey = "distribution" | "dirty_data" | "adversarial" | "physics";
export type DistributionCompareMode = "baseline_file" | "in_file_split";
export type AlgoOptionStatus = "ready" | "planned";
export type AlgoOption = { key: string; label: string; desc: string; status: AlgoOptionStatus };
export type DefectStatus = AlgoOptionStatus;
export type DefectBadge = { text: string; type: "success" | "warning" | "info" | "danger" };
export type DefectTreeNode = {
  key: string;
  label: string;
  desc?: string;
  badge?: DefectBadge;
  status?: DefectStatus;
  disabled?: boolean;
  module?: ModuleKey;
  algorithms?: AlgoOption[];
  children?: DefectTreeNode[];
};
export type ComparisonOperator = "==" | "!=" | ">" | ">=" | "<" | "<=";
export type PhysicsConstraintRow = { id: string; column: string; min?: number; max?: number };
export type PhysicsColumnRuleType = "not_null" | "in_set" | "regex";
export type PhysicsColumnRule = {
  id: string;
  column: string;
  type: PhysicsColumnRuleType;
  values?: string;
  pattern?: string;
};
export type PhysicsCrossRuleType = "if_then" | "relation" | "sum" | "unique";
export type PhysicsCrossRule = {
  id: string;
  type: PhysicsCrossRuleType;
  ifColumn?: string;
  ifOp?: ComparisonOperator;
  ifValue?: string;
  thenColumn?: string;
  thenOp?: ComparisonOperator;
  thenValue?: string;
  relationLeft?: string;
  relationOp?: ComparisonOperator;
  relationRight?: string;
  relationTolerance?: number;
  sumColumns?: string[];
  sumTargetColumn?: string;
  sumTargetValue?: string;
  sumTolerance?: number;
  uniqueColumns?: string[];
};
export type ModuleAlgoSelection = Record<ModuleKey, string[]>;
export type ModuleDefectRow = {
  key: string;
  label: string;
  desc?: string;
  status: DefectStatus;
  path: string;
  badge?: DefectBadge;
};
export type IssueKind = "anomaly" | "missing" | "duplicate" | "label_mismatch" | "other";

// ───────────────────────── InjectionKey ─────────────────────────
export const DqscanStateKey: InjectionKey<ReturnType<typeof useDqscanState>> = Symbol("DqscanState");

// ───────────────────────── 静态数据 ─────────────────────────
export const modalities = [
  { value: "tabular", label: "表格数据", icon: "table", desc: "CSV/TXT", disabled: false },
  { value: "timeseries", label: "时序数据", icon: "monitor", desc: "后续接入", disabled: true },
  { value: "image", label: "图像数据", icon: "browser", desc: "ZIP(图片+标签CSV)", disabled: false },
  { value: "text", label: "文本数据", icon: "document", desc: "后续接入", disabled: true },
];

export const modules: { key: ModuleKey; title: string; desc: string }[] = [
  { key: "distribution", title: "分布偏差检测", desc: "基线对比 / 免基线切分模拟" },
  { key: "dirty_data", title: "脏数据扫描", desc: "异常/缺失/重复/值域违规/疑似错标" },
  { key: "adversarial", title: "对抗性检测", desc: "扰动攻击下模型脆弱性评估" },
  { key: "physics", title: "物理保真度扫描", desc: "规则/约束一致性校验" },
];

export const comparisonOperatorOptions: { label: string; value: ComparisonOperator }[] = [
  { label: "=", value: "==" },
  { label: "≠", value: "!=" },
  { label: ">", value: ">" },
  { label: "≥", value: ">=" },
  { label: "<", value: "<" },
  { label: "≤", value: "<=" },
];

export const physicsColumnRuleTypeOptions: { label: string; value: PhysicsColumnRuleType }[] = [
  { label: "必填（Not Null）", value: "not_null" },
  { label: "枚举集合（In Set）", value: "in_set" },
  { label: "正则匹配（Regex）", value: "regex" },
];

export const physicsCrossRuleTypeOptions: { label: string; value: PhysicsCrossRuleType }[] = [
  { label: "条件规则（If-Then）", value: "if_then" },
  { label: "列间比较（Relation）", value: "relation" },
  { label: "求和校验（Sum）", value: "sum" },
  { label: "唯一约束（Unique）", value: "unique" },
];

export const ISSUE_COLORS: Record<IssueKind, string> = {
  anomaly: "#DC3545",
  missing: "#FFC107",
  duplicate: "#17A2B8",
  label_mismatch: "#6F42C1",
  other: "#909399",
};

// ───────────────────────── 算法选项 ─────────────────────────
export const distributionAlgorithmOptions: AlgoOption[] = [
  { key: "mmd_ks_chi2", label: "MMD + KS + 卡方（两样本）", desc: "对数值列做 MMD/KS，对类别列做卡方检验，输出 drift_detected 与 p_value。", status: "ready" },
  { key: "psi", label: "PSI（Population Stability Index）", desc: "更适合离散/分箱场景，输出稳定性指数。", status: "planned" },
  { key: "wasserstein", label: "Wasserstein 距离", desc: "对连续分布的距离度量，可用于分布差异排序。", status: "planned" },
  { key: "embedding_mmd", label: "Embedding 分布漂移（文本/图像）", desc: "对非结构化数据先做 embedding，再做分布对比。", status: "planned" },
];

export const dirtyDataAlgorithmOptions: AlgoOption[] = [
  { key: "ecod_3sigma", label: "通用脏数据扫描器（ECOD + 3σ）", desc: "一次扫描输出异常/缺失/重复/值域四类信号；有 pyod 则 ECOD，无依赖时降级为 3σ 规则。", status: "ready" },
  { key: "isolation_forest", label: "IsolationForest", desc: "对高维数值更稳定的异常检测。", status: "planned" },
  { key: "ruleset", label: "可配置规则引擎", desc: "按字段类型/业务规则进行检查。", status: "planned" },
  { key: "autoencoder", label: "AutoEncoder 异常检测", desc: "适合大规模/非线性异常。", status: "planned" },
];

export const adversarialAlgorithmOptions: AlgoOption[] = [
  { key: "zoo_or_random", label: "ZOO（ART）/ 随机扰动", desc: "有 ART 则用 ZOO 黑盒攻击；无 ART 则使用随机扰动搜索降级。", status: "ready" },
  { key: "fgsm", label: "FGSM（白盒）", desc: "快速白盒攻击，需要梯度支持。", status: "planned" },
  { key: "pgd", label: "PGD（白盒）", desc: "更强的迭代攻击，需要梯度支持。", status: "planned" },
  { key: "cw", label: "C&W（白盒）", desc: "优化式攻击，需要梯度支持。", status: "planned" },
];

export const physicsAlgorithmOptions: AlgoOption[] = [
  { key: "pandera_or_fallback", label: "Pandera Schema / 基础校验", desc: "有 pandera 则 schema 校验，否则使用基本 min/max 规则验证。", status: "ready" },
  { key: "cross_constraints", label: "跨字段约束（守恒/一致性）", desc: "启用输入输出守恒等跨字段启发式规则（已接入）。", status: "ready" },
  { key: "causal_graph", label: "因果图一致性", desc: "基于因果图做一致性检查。", status: "planned" },
  { key: "temporal_rules", label: "时序物理规律", desc: "适用于时序数据的物理规律校验。", status: "planned" },
];

export const dirtyMissingAlgorithmOptions: AlgoOption[] = [
  ...dirtyDataAlgorithmOptions,
  { key: "missing_stats_threshold", label: "缺失统计 + 阈值", desc: "统计每列缺失率，超过阈值则告警，并输出影响字段与缺失分布。", status: "ready" },
  { key: "missing_pattern_mcar", label: "缺失模式分析（MCAR/MAR）", desc: "分析缺失是否与其他字段相关，定位系统性缺失与采集偏差。", status: "planned" },
  { key: "auto_imputation_suggest", label: "自动补全建议（KNN/Iterative）", desc: "给出补全策略与风险提示，辅助数据修复。", status: "planned" },
  { key: "missing_correlation_heatmap", label: "缺失相关性热力图", desc: "以可视化方式呈现缺失相关结构，便于快速排查。", status: "planned" },
];

export const dirtyDuplicateAlgorithmOptions: AlgoOption[] = [
  ...dirtyDataAlgorithmOptions,
  { key: "exact_duplicate", label: "完全重复检测", desc: "按整行或关键字段判断重复，输出重复率与示例行。", status: "ready" },
  { key: "near_duplicate_similarity", label: "近重复（相似度）", desc: "支持「近重复/模糊重复」识别（例如文本字段轻微差异）。", status: "planned" },
  { key: "minhash_lsh", label: "MinHash + LSH", desc: "适合大规模去重的近似方法。", status: "planned" },
  { key: "record_linkage", label: "Record Linkage（实体对齐）", desc: "针对多字段拼接的「同一实体多条记录」识别。", status: "planned" },
];

export const dirtyRangeAlgorithmOptions: AlgoOption[] = [
  ...dirtyDataAlgorithmOptions,
  { key: "sigma_rule", label: "3σ 规则", desc: "用均值±kσ 的启发式方式发现可疑极值。", status: "ready" },
  { key: "iqr_rule", label: "IQR 规则", desc: "对长尾分布更稳健的四分位距方法。", status: "planned" },
  { key: "domain_rules", label: "业务规则（min/max/枚举）", desc: "按字段业务约束检查取值范围。", status: "planned" },
  { key: "schema_constraints", label: "Schema 约束联动", desc: "与 Pandera/规则库联动，统一落地字段约束。", status: "planned" },
];

export const labelMismatchAlgorithmOptions: AlgoOption[] = [
  { key: "confident_learning", label: "Confident Learning（错标候选集）", desc: "基于 out-of-fold 概率的 label quality score + 按类剪枝，输出疑似错标候选集与混淆方向。", status: "ready" },
  { key: "cv_consistency", label: "交叉验证一致性", desc: "通过交叉验证训练并找出「模型强烈不认可的标签」样本。", status: "ready" },
  { key: "embedding_knn", label: "Embedding + KNN 近邻一致性", desc: "在特征/embedding 空间中检查近邻标签一致性，发现疑似错标。", status: "planned" },
  { key: "confidence_margin", label: "置信度边界样本", desc: "识别高不确定样本与置信度异常样本，辅助人工复核。", status: "planned" },
];

// ───────────────────────── 缺陷树默认数据 ─────────────────────────
export function createDefaultDefectTreeData(): DefectTreeNode[] {
  return [
    {
      key: "dirty_data",
      label: "脏数据体系",
      desc: "完整性 / 一致性 / 异常与噪声 / 标注质量",
      children: [
        {
          key: "dirty_data.group_integrity",
          label: "完整性（Completeness）",
          desc: "缺失、空值、字段缺失等",
          children: [
            { key: "dirty_data.missing", label: "缺失值异常", desc: "统计缺失率与缺失模式，定位缺失严重字段。", badge: { text: "推荐", type: "success" }, status: "ready", module: "dirty_data", algorithms: dirtyMissingAlgorithmOptions },
          ],
        },
        {
          key: "dirty_data.group_noise",
          label: "异常与噪声（Outliers）",
          desc: "异常点、极值、噪声样本",
          children: [
            { key: "dirty_data.anomaly", label: "异常样本（Outlier）", desc: "无监督异常检测，定位疑似异常行与可疑字段。", badge: { text: "推荐", type: "success" }, status: "ready", module: "dirty_data", algorithms: dirtyDataAlgorithmOptions },
            { key: "dirty_data.range", label: "值域违规", desc: "用统计规则或业务规则识别异常取值范围。", status: "ready", module: "dirty_data", algorithms: dirtyRangeAlgorithmOptions },
          ],
        },
        {
          key: "dirty_data.group_consistency",
          label: "一致性（Consistency）",
          desc: "重复、矛盾、规则不一致等",
          children: [
            { key: "dirty_data.duplicate", label: "重复 / 近重复", desc: "识别完全重复与近重复记录，输出去重建议。", status: "ready", module: "dirty_data", algorithms: dirtyDuplicateAlgorithmOptions },
          ],
        },
        {
          key: "dirty_data.group_label",
          label: "标注质量（Label）",
          desc: "错标、弱标注、标签噪声",
          children: [
            { key: "dirty_data.label_mismatch", label: "疑似错标（Label Mismatch）", desc: "识别「标签与特征不一致」的样本（如猫被标成狗）。", badge: { text: "可用", type: "success" }, status: "ready", module: "dirty_data", algorithms: labelMismatchAlgorithmOptions },
          ],
        },
      ],
    },
    {
      key: "distribution",
      label: "分布偏差体系",
      desc: "训练/基线 vs 当前数据分布变化监控",
      children: [
        {
          key: "distribution.group_feature",
          label: "特征漂移（Feature Drift）",
          desc: "数值/类别特征的分布变化",
          children: [
            { key: "distribution.numeric_drift", label: "数值特征漂移", desc: "对连续特征分布做两样本检验，输出漂移结论与 p 值。", badge: { text: "推荐", type: "success" }, status: "ready", module: "distribution", algorithms: distributionAlgorithmOptions },
            { key: "distribution.categorical_drift", label: "类别特征漂移", desc: "对离散特征做卡方等检验，定位漂移字段。", status: "ready", module: "distribution", algorithms: distributionAlgorithmOptions },
          ],
        },
        {
          key: "distribution.group_label",
          label: "标签漂移（Label Shift）",
          desc: "标签分布变化与类别占比变化",
          children: [
            { key: "distribution.label_shift", label: "标签分布变化", desc: "对标签列做分布对比，监控类占比突变与先验变化。", status: "ready", module: "distribution", algorithms: distributionAlgorithmOptions },
          ],
        },
        {
          key: "distribution.group_unstructured",
          label: "非结构化漂移",
          desc: "文本/图像 embedding 的漂移监控",
          children: [
            { key: "distribution.embedding_drift", label: "Embedding 分布漂移（文本/图像）", desc: "对非结构化数据先做 embedding，再做分布对比。", badge: { text: "即将上线", type: "warning" }, status: "planned", disabled: true, module: "distribution", algorithms: distributionAlgorithmOptions },
          ],
        },
      ],
    },
    {
      key: "adversarial",
      label: "对抗性与鲁棒性体系",
      desc: "黑盒/白盒攻击下模型脆弱性评估",
      children: [
        {
          key: "adversarial.group_attack",
          label: "攻击评估（Attack）",
          desc: "攻击成功率、扰动预算与鲁棒性",
          children: [
            { key: "adversarial.blackbox", label: "黑盒攻击（ZOO/随机）", desc: "在无梯度条件下进行黑盒攻击，评估模型易受攻击程度。", badge: { text: "可用", type: "success" }, status: "ready", module: "adversarial", algorithms: adversarialAlgorithmOptions },
            { key: "adversarial.whitebox", label: "白盒攻击（FGSM/PGD）", desc: "基于梯度的白盒攻击评估（需要模型与梯度接口）。", badge: { text: "即将上线", type: "warning" }, status: "planned", disabled: true, module: "adversarial", algorithms: adversarialAlgorithmOptions },
          ],
        },
        {
          key: "adversarial.group_monitor",
          label: "鲁棒性监控（Monitoring）",
          desc: "敏感特征、鲁棒性分解与风险提示",
          children: [
            { key: "adversarial.sensitivity", label: "特征敏感性分析", desc: "识别对扰动最敏感的特征与子群体风险。", badge: { text: "即将上线", type: "warning" }, status: "planned", disabled: true, module: "adversarial", algorithms: adversarialAlgorithmOptions },
          ],
        },
      ],
    },
    {
      key: "physics",
      label: "物理保真度与规则体系",
      desc: "按列配置约束与业务规则，扫描数据质量",
      children: [
        { key: "physics.rules", label: "规则扫描", desc: "对每列设置约束规则，支持跨列关系/条件/求和/唯一性规则。", badge: { text: "推荐", type: "success" }, status: "ready", module: "physics", algorithms: physicsAlgorithmOptions.map((a) => ({ ...a })) },
      ],
    },
  ];
}

export const defaultExpandedDefectKeys = [
  "dirty_data", "dirty_data.group_integrity", "dirty_data.group_noise", "dirty_data.group_consistency", "dirty_data.group_label",
  "distribution", "distribution.group_feature", "distribution.group_label", "distribution.group_unstructured",
  "adversarial", "adversarial.group_attack", "adversarial.group_monitor",
  "physics",
];

export const defaultCheckedDefectKeys = [
  "dirty_data.anomaly", "dirty_data.missing", "dirty_data.duplicate", "dirty_data.range",
  "distribution.numeric_drift", "distribution.categorical_drift",
  "adversarial.blackbox",
  "physics.rules",
];

const recommendedDefectsByModule: Record<ModuleKey, string[]> = {
  dirty_data: ["dirty_data.anomaly", "dirty_data.missing", "dirty_data.duplicate", "dirty_data.range"],
  distribution: ["distribution.numeric_drift", "distribution.categorical_drift"],
  adversarial: ["adversarial.blackbox"],
  physics: ["physics.rules"],
};

const executorPreferenceByDefect: Record<string, string[]> = {
  "dirty_data.anomaly": ["ecod_3sigma"],
  "dirty_data.missing": ["missing_stats_threshold", "ecod_3sigma"],
  "dirty_data.duplicate": ["exact_duplicate", "ecod_3sigma"],
  "dirty_data.range": ["sigma_rule", "ecod_3sigma"],
  "dirty_data.label_mismatch": ["confident_learning", "cv_consistency"],
  "distribution.numeric_drift": ["mmd_ks_chi2", "psi", "wasserstein"],
  "distribution.categorical_drift": ["mmd_ks_chi2", "psi"],
  "distribution.label_shift": ["mmd_ks_chi2", "psi"],
  "adversarial.blackbox": ["zoo_or_random"],
  "adversarial.whitebox": ["fgsm", "pgd", "cw"],
  "physics.rules": ["pandera_or_fallback"],
};

// ───────────────────────── 工具函数 ─────────────────────────
export function makeTempId(prefix: string) {
  return `${prefix}_${Date.now()}_${Math.random().toString(16).slice(2, 8)}`;
}

export function formatBytes(bytes: number) {
  const units = ["B", "KB", "MB", "GB"];
  let v = bytes;
  let i = 0;
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i += 1; }
  return `${v.toFixed(i === 0 ? 0 : 2)} ${units[i]}`;
}

export function scoreColor(score: number): string {
  if (score >= 90) return "#28A745";
  if (score >= 80) return "#17A2B8";
  if (score >= 70) return "#FFC107";
  return "#DC3545";
}

export function gradeFull(score: number): string {
  if (score >= 90) return "S (优秀)";
  if (score >= 80) return "A (良好)";
  if (score >= 70) return "B (中等)";
  if (score >= 60) return "C (及格)";
  return "D (不及格)";
}

export function statusFromScore(score: number): { statusTag: "success" | "warning" | "danger"; statusText: string } {
  if (score >= 90) return { statusTag: "success", statusText: "[OK]" };
  if (score >= 70) return { statusTag: "warning", statusText: "[!]" };
  return { statusTag: "danger", statusText: "[X]" };
}

export function dataTypeLabel(dt: string): string {
  const map: Record<string, string> = { tabular: "表格数据", timeseries: "时序数据", image: "图像数据", text: "文本数据" };
  return map[dt] || dt;
}

export function issueKindFromType(issueType: any): IssueKind {
  const t = String(issueType || "");
  if (t.includes("异常")) return "anomaly";
  if (t.includes("缺失")) return "missing";
  if (t.includes("重复")) return "duplicate";
  if (t.includes("错标")) return "label_mismatch";
  const lower = t.toLowerCase();
  if (lower.includes("label") && lower.includes("mismatch")) return "label_mismatch";
  return "other";
}

export function issueTagStyle(issueType: any): Record<string, string> {
  const kind = issueKindFromType(issueType);
  const c = ISSUE_COLORS[kind];
  const bg =
    kind === "anomaly" ? "rgba(220, 53, 69, 0.08)"
    : kind === "missing" ? "rgba(255, 193, 7, 0.12)"
    : kind === "duplicate" ? "rgba(23, 162, 184, 0.08)"
    : kind === "label_mismatch" ? "rgba(111, 66, 193, 0.08)"
    : "rgba(144, 147, 153, 0.08)";
  const text = kind === "missing" ? "#6B4F00" : c;
  return { color: text, borderColor: c, backgroundColor: bg };
}

export function issueRowClassName({ row }: { row: any }): string {
  const kind = issueKindFromType(row?.issue_type);
  return kind === "other" ? "" : `dqscan-issue dqscan-issue-${kind}`;
}

export function severityTagType(sev: any): "info" | "success" | "warning" | "danger" {
  const s = String(sev || "").toLowerCase();
  if (s.includes("severe") || s.includes("high")) return "danger";
  if (s.includes("moderate") || s.includes("medium")) return "warning";
  if (s.includes("light") || s.includes("low")) return "info";
  return "info";
}

export function issueDetailsText(details: any): string {
  if (!details) return "";
  if (typeof details === "string") return details;
  try {
    if (typeof details === "object") {
      const pairs = Object.entries(details).slice(0, 6).map(([k, v]) => `${k}=${typeof v === "object" ? JSON.stringify(v) : String(v)}`);
      return pairs.join("; ");
    }
    return String(details);
  } catch { return String(details); }
}

function detectDelimiter(line: string): string {
  const candidates = [",", "\t", ";", "|"];
  let best = ",";
  let bestCount = -1;
  for (const d of candidates) {
    const count = line.split(d).length - 1;
    if (count > bestCount) { bestCount = count; best = d; }
  }
  return best;
}

function parseDelimitedHeader(line: string, delimiter: string): string[] {
  const out: string[] = [];
  let cur = "";
  let inQuotes = false;
  const s = line.replace(/^\ufeff/, "");
  for (let i = 0; i < s.length; i += 1) {
    const ch = s[i];
    if (ch === '"') {
      if (inQuotes && s[i + 1] === '"') { cur += '"'; i += 1; } else { inQuotes = !inQuotes; }
      continue;
    }
    if (ch === delimiter && !inQuotes) { out.push(cur); cur = ""; continue; }
    cur += ch;
  }
  out.push(cur);
  return out.map((x) => x.trim().replace(/^"|"$/g, "").trim()).filter((x) => !!x);
}

async function extractColumnsFromFile(file: File): Promise<string[]> {
  const text = await file.slice(0, 64 * 1024).text();
  const firstLine = text.split(/\r?\n/).find((l) => l.trim().length > 0) || "";
  if (!firstLine) return [];
  const delimiter = detectDelimiter(firstLine);
  const cols = parseDelimitedHeader(firstLine.replace(/\r$/, ""), delimiter);
  const seen = new Set<string>();
  const uniq: string[] = [];
  for (const c of cols) { if (!seen.has(c)) { seen.add(c); uniq.push(c); } }
  return uniq;
}

function buildDefectIndex(nodes: DefectTreeNode[]) {
  const nodeByKey: Record<string, DefectTreeNode> = {};
  const pathByKey: Record<string, string[]> = {};
  const leafKeys: string[] = [];
  const walk = (items: DefectTreeNode[], ancestors: string[]) => {
    for (const n of items) {
      nodeByKey[n.key] = n;
      const path = [...ancestors, n.label];
      pathByKey[n.key] = path;
      if (n.children?.length) { walk(n.children, path); } else { leafKeys.push(n.key); }
    }
  };
  walk(nodes, []);
  return { nodeByKey, pathByKey, leafKeys };
}

function createDefaultDefectAlgorithms(): Record<string, string[]> {
  return {
    "dirty_data.anomaly": ["ecod_3sigma"],
    "dirty_data.missing": ["ecod_3sigma"],
    "dirty_data.duplicate": ["ecod_3sigma"],
    "dirty_data.range": ["ecod_3sigma"],
    "dirty_data.label_mismatch": [],
    "distribution.numeric_drift": ["mmd_ks_chi2"],
    "distribution.categorical_drift": ["mmd_ks_chi2"],
    "distribution.label_shift": ["mmd_ks_chi2"],
    "distribution.embedding_drift": [],
    "adversarial.blackbox": ["zoo_or_random"],
    "adversarial.whitebox": [],
    "adversarial.sensitivity": [],
    "physics.rules": ["pandera_or_fallback"],
  };
}

function createDefaultDefectExecutors(): Record<string, string | null> {
  return {
    "dirty_data.anomaly": "ecod_3sigma",
    "dirty_data.missing": "ecod_3sigma",
    "dirty_data.duplicate": "ecod_3sigma",
    "dirty_data.range": "ecod_3sigma",
    "dirty_data.label_mismatch": "confident_learning",
    "distribution.numeric_drift": "mmd_ks_chi2",
    "distribution.categorical_drift": "mmd_ks_chi2",
    "distribution.label_shift": "mmd_ks_chi2",
    "distribution.embedding_drift": null,
    "adversarial.blackbox": "zoo_or_random",
    "adversarial.whitebox": null,
    "adversarial.sensitivity": null,
    "physics.rules": "pandera_or_fallback",
  };
}

function createDefaultModuleAlgorithms(): ModuleAlgoSelection {
  return {
    dirty_data: ["ecod_3sigma"],
    distribution: ["mmd_ks_chi2"],
    adversarial: ["zoo_or_random"],
    physics: ["pandera_or_fallback"],
  };
}

export function normalizeRuleValue(val?: string | number | null) {
  if (val === null || val === undefined) return undefined;
  if (typeof val === "number") return Number.isFinite(val) ? val : undefined;
  const trimmed = val.trim();
  if (!trimmed) return undefined;
  const num = Number(trimmed);
  return Number.isFinite(num) ? num : trimmed;
}

export function splitCsvValues(text?: string) {
  if (!text) return [];
  return text.split(",").map((v) => v.trim()).filter((v) => v.length > 0);
}

// ───────────────────────── Composable ─────────────────────────
export function useDqscanState() {
  // === 步骤 ===
  const activeStep = ref(0);

  // === 模态 ===
  const selectedModality = ref<string>("tabular");

  // === 文件上传 ===
  const baselineUploadRef = ref();
  const currentUploadRef = ref();
  const baselineFileList = ref<UploadFile[]>([]);
  const baselineSelectedFile = ref<File | null>(null);
  const baselineUploading = ref(false);
  const baselineUploadedFile = ref<DQScanUploadOut | null>(null);
  const currentFileList = ref<UploadFile[]>([]);
  const currentSelectedFile = ref<File | null>(null);
  const currentUploading = ref(false);
  const currentUploadedFile = ref<DQScanUploadOut | null>(null);

  // === 算法 ===
  const algorithmsLoading = ref(false);
  const algorithms = ref<DQScanAlgorithmOut[]>([]);
  const selectedAlgorithm = ref<string>("tabular_quality_engine");

  // === 模块选择 ===
  const selectedModules = ref<string[]>(["dirty_data", "distribution", "adversarial", "physics"]);
  const openModulePanels = ref<string[]>(modules.map((m) => m.key));
  const moduleWorkbenchTab = reactive<Record<ModuleKey, "base" | "bind" | "algo_params">>({
    dirty_data: "base", distribution: "base", adversarial: "base", physics: "base",
  });

  // === 任务 ===
  const starting = ref(false);
  const taskId = ref<string | null>(null);
  const progress = ref(0);
  const logs = ref<string[]>([]);
  const taskStatus = ref<TaskStatus>("IDLE");
  const taskError = ref<string | null>(null);
  const result = ref<any | null>(null);

  // === 报告 ===
  const reportsLoading = ref(false);
  const reports = ref<Record<string, any>>({});
  const activeReportModule = ref<string>("");

  // === 分布偏差 ===
  const distributionCompareMode = ref<DistributionCompareMode>("baseline_file");
  const distributionTrainTestSplit = ref(0.7);
  const distributionLabelColumn = ref<string>("");
  const distributionPVal = ref(0.05);
  const distributionExcludeColumns = ref<string[]>([]);
  const columnOptions = ref<string[]>([]);
  const columnsLoading = ref(false);
  const columnsError = ref<string | null>(null);

  const excludeColumnsDisplay = computed(() => {
    const n = distributionExcludeColumns.value.length;
    if (n === 0) return "未选择（默认不排除）";
    if (n <= 3) return distributionExcludeColumns.value.join(", ");
    return `${distributionExcludeColumns.value.slice(0, 3).join(", ")} 等${n}项`;
  });

  const labelMismatchExcludeColumnsDisplay = computed(() => {
    const n = labelMismatchExcludeColumns.value.length;
    if (n === 0) return "未选择（建议排除 id/uuid 等高基数字段）";
    if (n <= 3) return labelMismatchExcludeColumns.value.join(", ");
    return `${labelMismatchExcludeColumns.value.slice(0, 3).join(", ")} 等${n}项`;
  });

  // === 缺陷树 ===
  const defectSearch = ref("");
  const defectTreeRef = ref<any>();
  const defectTreeProps = { label: "label", children: "children", disabled: "disabled" } as const;
  const defectsCatalogLoading = ref(false);
  const defectsCatalogError = ref<string | null>(null);
  const defectTreeData = ref<DefectTreeNode[]>(createDefaultDefectTreeData());
  const defectIndex = computed(() => buildDefectIndex(defectTreeData.value));
  const checkedDefectKeys = ref<string[]>([...defaultCheckedDefectKeys]);
  const activeDefectKey = ref<string>("dirty_data.anomaly");
  const activeDefectTab = ref<"algo" | "params" | "output">("algo");
  const defectAlgorithms = ref<Record<string, string[]>>(createDefaultDefectAlgorithms());
  const defectExecutor = ref<Record<string, string | null>>(createDefaultDefectExecutors());
  const moduleAlgorithmsSelected = ref<ModuleAlgoSelection>(createDefaultModuleAlgorithms());
  const activeModuleTab = ref<string>("distribution");
  const showOnlyEnabledDefects = ref(false);
  const openDefectPanels = ref<string[]>([...defaultCheckedDefectKeys]);

  // === 扫描参数 ===
  const scanPreset = ref<"fast" | "balanced" | "thorough">("balanced");
  const globalMaxSamples = ref(20000);
  const globalParallelism = ref(2);
  const globalSeed = ref(42);
  const reportOptions = reactive({ docx: true, summary: true, max_examples: 50 });
  const algoParams = reactive({
    psi_bins: 10, psi_bucket: "quantile",
    wasserstein_threshold: 0.1,
    embedding_model: "small", embedding_batch_size: 64,
    iforest_estimators: 200, iforest_max_samples: 256,
    ae_latent_dim: 16, ae_epochs: 20,
    fgsm_norm: "linf", fgsm_targeted: false,
    pgd_steps: 20, pgd_step_size: 0.01, pgd_random_start: true,
  });

  const scanPresetLabel = computed(() => {
    const map: Record<string, string> = { fast: "快速", balanced: "均衡", thorough: "深度" };
    return map[scanPreset.value] || scanPreset.value;
  });

  // === 脏数据参数 ===
  const dirtyContamination = ref(0.1);
  const dirtyMissingThreshold = ref(0.1);
  const dirtyDuplicateThreshold = ref(0.02);
  const dirtyEnabledChecks = ref<string[]>(["anomaly", "missing", "duplicate", "range"]);
  const dirtyMaxExamples = ref(50);
  const dirtyWhitelistColumns = ref<string[]>([]);
  const dirtyBlacklistColumns = ref<string[]>([]);
  const duplicateKeyColumns = ref<string[]>([]);
  const duplicateSimilarity = ref(0.92);
  const rangeMethod = ref<"sigma" | "iqr" | "rules">("sigma");
  const rangeSigma = ref(3);
  const rangeIqrFactor = ref(1.5);
  const rangeOnlyColumns = ref<string[]>([]);
  const labelMismatchLabelColumn = ref<string>("");
  const labelMismatchMaxSamples = ref(20000);
  const labelMismatchExcludeColumns = ref<string[]>([]);
  const labelMismatchNSplits = ref(5);
  const labelMismatchThresholdProbTrue = ref(0.2);
  const labelMismatchThresholdProbPred = ref(0.6);
  const labelMismatchScoreMethod = ref<"self_confidence" | "normalized_margin" | "confidence_weighted_entropy">("self_confidence");
  const labelMismatchFilterBy = ref<"both" | "prune_by_class" | "prune_by_noise_rate" | "confident_learning">("both");
  const labelMismatchFractionNoise = ref(0.05);
  const labelMismatchMaxExamples = ref(500);

  // === 图片错标检测参数 ===
  const imageLabelAlgorithm = ref<"simifeat_knn" | "phash_outlier">("simifeat_knn");
  const imageLabelK = ref(10);
  const imageLabelThreshold = ref(0.5);
  const imageLabelMaxSamples = ref(5000);
  const imageLabelMaxExamples = ref(500);
  const imageLabelBatchSize = ref(32);
  const imageLabelDevice = ref<"auto" | "cpu" | "cuda">("auto");
  const imageLabelImageColumn = ref("image_path");
  const imageLabelLabelColumn = ref("label");
  const imageLabelCsvPath = ref("");

  // === 对抗性参数 ===
  const adversarialEpsilon = ref(0.05);
  const adversarialMaxIter = ref(20);
  const adversarialRandomTrials = ref(40);
  const adversarialRandomFeatures = ref(3);
  const adversarialMaxSamples = ref(50);
  const adversarialSeed = ref(42);
  const adversarialLearningRate = ref(0.01);
  const adversarialConfidence = ref(0);
  const adversarialBatchSize = ref(1);

  // === 物理保真度参数 ===
  const physicsAutoConstraints = ref(true);
  const physicsConstraints = ref<PhysicsConstraintRow[]>([]);
  const physicsColumnRules = ref<PhysicsColumnRule[]>([]);
  const physicsCrossRules = ref<PhysicsCrossRule[]>([]);

  // === 分布相关算法 ===
  const distributionAlgorithms = ref<string[]>(["mmd_ks_chi2"]);
  const dirtyDataAlgorithms = ref<string[]>(["ecod_3sigma"]);
  const adversarialAlgorithms = ref<string[]>(["zoo_or_random"]);
  const physicsAlgorithmsRef = ref<string[]>(["pandera_or_fallback"]);

  // === WebSocket ===
  let ws: WebSocket | null = null;
  let pollTimer: number | null = null;

  // ─── 辅助函数 ───

  function pushLog(line: string) {
    if (!line) return;
    logs.value.push(line);
    if (logs.value.length > 800) logs.value.splice(0, logs.value.length - 800);
  }

  function resetWs() {
    try { ws?.close(1000, "reset"); } catch {}
    ws = null;
  }

  function clearPoll() {
    if (pollTimer) { window.clearInterval(pollTimer); pollTimer = null; }
  }

  function gotoStep(step: number) { activeStep.value = step; }

  function stepClass(idx: number) {
    if (activeStep.value === idx) return "active";
    if (activeStep.value > idx) return "completed";
    return "";
  }

  // ─── 缺陷树操作 ───

  function moduleKeyFromDefectKey(key: string): ModuleKey | null {
    const prefix = key.split(".")[0];
    if (prefix === "dirty_data" || prefix === "distribution" || prefix === "adversarial" || prefix === "physics") return prefix;
    return null;
  }

  function getCheckedLeafKeys(): string[] {
    const tree = defectTreeRef.value;
    if (tree?.getCheckedKeys) {
      const keys = tree.getCheckedKeys(true) as string[];
      return Array.from(new Set(keys.filter((k) => typeof k === "string")));
    }
    return Array.from(new Set(checkedDefectKeys.value));
  }

  function syncDerivedFromChecked(keys: string[]) {
    const moduleSet = new Set<string>();
    const dirtyChecks = new Set<string>();
    for (const k of keys) {
      const moduleKey = moduleKeyFromDefectKey(k);
      if (moduleKey) moduleSet.add(moduleKey);
      if (k === "dirty_data.anomaly") dirtyChecks.add("anomaly");
      else if (k === "dirty_data.missing") dirtyChecks.add("missing");
      else if (k === "dirty_data.duplicate") dirtyChecks.add("duplicate");
      else if (k === "dirty_data.range") dirtyChecks.add("range");
      else if (k === "dirty_data.label_mismatch") dirtyChecks.add("label_mismatch");
    }
    selectedModules.value = Array.from(moduleSet);
    dirtyEnabledChecks.value = Array.from(dirtyChecks);
  }

  function moduleLeafDefectKeys(moduleKey: ModuleKey): string[] {
    return defectIndex.value.leafKeys.filter((k) => moduleKeyFromDefectKey(k) === moduleKey);
  }

  function executorAlgorithmOptions(defectKey: string): AlgoOption[] {
    const meta = defectIndex.value.nodeByKey[defectKey];
    if (!meta?.algorithms?.length) return [];
    const map = new Map<string, AlgoOption>();
    for (const a of meta.algorithms) {
      const existing = map.get(a.key);
      if (!existing) map.set(a.key, a);
      else if (existing.status === "planned" && a.status === "ready") map.set(a.key, a);
    }
    return Array.from(map.values()).sort((a, b) => {
      if (a.status !== b.status) return a.status === "ready" ? -1 : 1;
      return a.label.localeCompare(b.label);
    });
  }

  const algoOptionByKey = computed<Record<string, AlgoOption>>(() => {
    const out: Record<string, AlgoOption> = {};
    for (const n of Object.values(defectIndex.value.nodeByKey)) {
      for (const a of n.algorithms || []) {
        const existing = out[a.key];
        if (!existing) { out[a.key] = a; continue; }
        if (existing.status === "planned" && a.status === "ready") out[a.key] = a;
      }
    }
    return out;
  });

  const algoMetaByKey = computed(() => {
    const out: Record<string, { label: string; status: AlgoOptionStatus }> = {};
    for (const n of Object.values(defectIndex.value.nodeByKey)) {
      for (const a of n.algorithms || []) {
        if (!out[a.key]) out[a.key] = { label: a.label, status: a.status };
      }
    }
    return out;
  });

  function chooseExecutorForDefect(defectKey: string): string | null {
    const opts = executorAlgorithmOptions(defectKey);
    if (!opts.length) return null;
    const statusByKey = new Map(opts.map((x) => [x.key, x.status] as const));
    const pref = executorPreferenceByDefect[defectKey] || [];
    for (const k of pref) { if (statusByKey.get(k) === "ready") return k; }
    return opts.find((x) => x.status === "ready")?.key || null;
  }

  function autoBindModuleDefects(moduleKey: ModuleKey) {
    const defectKeys = moduleLeafDefectKeys(moduleKey);
    for (const dk of defectKeys) {
      const meta = defectIndex.value.nodeByKey[dk];
      if (!meta || meta.status !== "ready") continue;
      const current = defectExecutor.value[dk];
      const allowed = new Set(executorAlgorithmOptions(dk).map((a) => a.key));
      if (current && allowed.has(current)) continue;
      defectExecutor.value[dk] = chooseExecutorForDefect(dk);
    }
  }

  function setCheckedDefects(keys: string[]) {
    const uniq = Array.from(new Set(keys));
    const tree = defectTreeRef.value;
    if (tree?.setCheckedKeys) {
      tree.setCheckedKeys(uniq);
      checkedDefectKeys.value = getCheckedLeafKeys();
    } else {
      checkedDefectKeys.value = uniq;
    }
    syncDerivedFromChecked(checkedDefectKeys.value);
    for (const mk of selectedModules.value) {
      if (mk !== "dirty_data" && mk !== "distribution" && mk !== "adversarial" && mk !== "physics") continue;
      autoBindModuleDefects(mk);
    }
  }

  function getModuleAlgorithms(moduleKey: ModuleKey): string[] {
    const enabled = new Set(checkedDefectKeys.value);
    const algoKeys = new Set<string>();
    for (const defectKey of moduleLeafDefectKeys(moduleKey)) {
      if (!enabled.has(defectKey)) continue;
      const meta = defectIndex.value.nodeByKey[defectKey];
      if (!meta || meta.status !== "ready") continue;
      const executor = defectExecutor.value[defectKey];
      if (!executor) continue;
      if (algoOptionByKey.value[executor]?.status === "planned") continue;
      algoKeys.add(executor);
    }
    const labelOf = (k: string) => algoOptionByKey.value[k]?.label || k;
    return Array.from(algoKeys).sort((a, b) => labelOf(a).localeCompare(labelOf(b)));
  }

  function boundDefectKeys(moduleKey: ModuleKey, algoKey: string): string[] {
    const enabled = new Set(checkedDefectKeys.value);
    const out: string[] = [];
    for (const defectKey of moduleLeafDefectKeys(moduleKey)) {
      if (!enabled.has(defectKey)) continue;
      const meta = defectIndex.value.nodeByKey[defectKey];
      if (!meta || meta.status !== "ready") continue;
      if (defectExecutor.value[defectKey] === algoKey) out.push(defectKey);
    }
    return out;
  }

  function boundDefectCount(moduleKey: ModuleKey, algoKey: string): number {
    return boundDefectKeys(moduleKey, algoKey).length;
  }

  function boundDefectTags(moduleKey: ModuleKey, algoKey: string): string[] {
    return boundDefectKeys(moduleKey, algoKey).slice(0, 4);
  }

  function moduleAlgorithmOptions(moduleKey: ModuleKey): AlgoOption[] {
    const out = new Map<string, AlgoOption>();
    for (const defectKey of defectIndex.value.leafKeys) {
      const meta = defectIndex.value.nodeByKey[defectKey];
      const mk = meta?.module || moduleKeyFromDefectKey(defectKey);
      if (mk !== moduleKey || !meta?.algorithms?.length) continue;
      for (const a of meta.algorithms) {
        const existing = out.get(a.key);
        if (!existing) out.set(a.key, a);
        else if (existing.status === "planned" && a.status === "ready") out.set(a.key, a);
      }
    }
    return Array.from(out.values()).sort((a, b) => {
      if (a.status !== b.status) return a.status === "ready" ? -1 : 1;
      return a.label.localeCompare(b.label);
    });
  }

  function setModuleAlgorithms(moduleKey: ModuleKey, v: string[]) {
    const allowedReady = new Set(moduleAlgorithmOptions(moduleKey).filter((a) => a.status === "ready").map((a) => a.key));
    const filtered = (v || []).filter((x) => allowedReady.has(x));
    moduleAlgorithmsSelected.value[moduleKey] = Array.from(new Set(filtered));
    autoBindModuleDefects(moduleKey);
  }

  function moduleAllDefectCount(moduleKey: ModuleKey): number {
    return moduleLeafDefectKeys(moduleKey).length;
  }

  function moduleEnabledDefectCount(moduleKey: ModuleKey): number {
    const keys = new Set(moduleLeafDefectKeys(moduleKey));
    return checkedDefectKeys.value.filter((k) => keys.has(k)).length;
  }

  function isModuleEnabled(moduleKey: ModuleKey): boolean {
    return selectedModules.value.includes(moduleKey);
  }

  function setModuleEnabled(moduleKey: ModuleKey, enabled: boolean) {
    if (!enabled) {
      const toRemove = new Set(moduleLeafDefectKeys(moduleKey));
      setCheckedDefects(checkedDefectKeys.value.filter((k) => !toRemove.has(k)));
      return;
    }
    const metaReady = (k: string) => defectIndex.value.nodeByKey[k]?.status === "ready";
    const defaults = (recommendedDefectsByModule[moduleKey] || []).filter((k) => metaReady(k));
    setCheckedDefects(Array.from(new Set([...checkedDefectKeys.value, ...defaults])));
    autoBindModuleDefects(moduleKey);
  }

  function disableAllModuleDefects(moduleKey: ModuleKey) {
    setModuleEnabled(moduleKey, false);
  }

  function getDefectExecutor(defectKey: string): string {
    return defectExecutor.value[defectKey] || "";
  }

  function setDefectExecutor(defectKey: string, algoKey: string | null | undefined) {
    const meta = defectIndex.value.nodeByKey[defectKey];
    if (!meta || meta.status !== "ready") return;
    if (!algoKey) { defectExecutor.value[defectKey] = null; return; }
    const allowed = new Set(executorAlgorithmOptions(defectKey).map((a) => a.key));
    if (!allowed.has(algoKey)) return;
    if (algoOptionByKey.value[algoKey]?.status === "planned") return;
    defectExecutor.value[defectKey] = algoKey;
  }

  function isDefectEnabled(defectKey: string): boolean {
    return checkedDefectKeys.value.includes(defectKey);
  }

  function setDefectEnabled(defectKey: string, enabled: boolean) {
    const meta = defectMeta(defectKey);
    if (!meta || meta.status !== "ready") return;
    const tree = defectTreeRef.value;
    if (tree?.setChecked) {
      tree.setChecked(defectKey, !!enabled, true);
      checkedDefectKeys.value = getCheckedLeafKeys();
    } else {
      const set = new Set(checkedDefectKeys.value);
      if (enabled) set.add(defectKey); else set.delete(defectKey);
      checkedDefectKeys.value = Array.from(set);
    }
    syncDerivedFromChecked(checkedDefectKeys.value);
    if (enabled) {
      const mk = moduleKeyFromDefectKey(defectKey);
      if (mk) autoBindModuleDefects(mk);
    }
    if (enabled && !openDefectPanels.value.includes(defectKey)) {
      openDefectPanels.value.push(defectKey);
    }
  }

  function defectMeta(defectKey: string): DefectTreeNode | null {
    const node = defectIndex.value.nodeByKey[defectKey];
    if (!node || !node.algorithms) return null;
    return node;
  }

  function defectPathText(defectKey: string): string {
    const path = defectIndex.value.pathByKey[defectKey];
    return path?.length ? path.join(" / ") : "-";
  }

  function getDefectAlgorithms(defectKey: string): string[] {
    return defectAlgorithms.value[defectKey] || [];
  }

  function setDefectAlgorithms(defectKey: string, v: string[]) {
    const allowed = new Set((defectMeta(defectKey)?.algorithms || []).map((a) => a.key));
    const filtered = (v || []).filter((x) => allowed.has(x));
    defectAlgorithms.value[defectKey] = Array.from(new Set(filtered));
  }

  function clearDefectAlgorithms(defectKey: string) {
    setDefectAlgorithms(defectKey, []);
  }

  function applyAlgorithmsToModule(sourceDefectKey: string) {
    const moduleKey = moduleKeyFromDefectKey(sourceDefectKey);
    if (!moduleKey) return;
    const source = getDefectAlgorithms(sourceDefectKey);
    const targets = defectIndex.value.leafKeys.filter((k) => moduleKeyFromDefectKey(k) === moduleKey);
    for (const k of targets) {
      if (!checkedDefectKeys.value.includes(k)) continue;
      const allowed = new Set((defectMeta(k)?.algorithms || []).map((a) => a.key));
      const filtered = source.filter((x) => allowed.has(x));
      defectAlgorithms.value[k] = Array.from(new Set(filtered));
    }
  }

  function firstLeafKeyOf(node: DefectTreeNode): string | null {
    if (!node.children?.length) return node.key;
    for (const c of node.children) {
      const leaf = firstLeafKeyOf(c);
      if (leaf) return leaf;
    }
    return null;
  }

  function onDefectNodeClick(data: DefectTreeNode) {
    const leafKey = firstLeafKeyOf(data);
    if (!leafKey) return;
    activeDefectKey.value = leafKey;
    if (showOnlyEnabledDefects.value && !checkedDefectKeys.value.includes(leafKey)) {
      showOnlyEnabledDefects.value = false;
    }
    const moduleKey = moduleKeyFromDefectKey(leafKey);
    if (moduleKey && !openModulePanels.value.includes(moduleKey)) {
      openModulePanels.value.push(moduleKey);
    }
    if (moduleKey) {
      moduleWorkbenchTab[moduleKey] = "bind";
    }
    nextTick(() => {
      const el = document.getElementById(`defect-row-${leafKey}`);
      el?.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  }

  function onDefectCheck() {
    checkedDefectKeys.value = getCheckedLeafKeys();
    syncDerivedFromChecked(checkedDefectKeys.value);
    for (const mk of selectedModules.value) {
      if (mk !== "dirty_data" && mk !== "distribution" && mk !== "adversarial" && mk !== "physics") continue;
      autoBindModuleDefects(mk);
    }
  }

  function filterDefectNode(value: string, data: DefectTreeNode) {
    if (!value) return true;
    const v = value.trim().toLowerCase();
    const hay = `${data.label || ""} ${data.desc || ""}`.toLowerCase();
    return hay.includes(v);
  }

  function selectAllDefects() {
    const keys = defectIndex.value.leafKeys.filter((k) => !defectIndex.value.nodeByKey[k]?.disabled);
    setCheckedDefects(keys);
  }

  function selectRecommendedDefects() {
    const keys = defaultCheckedDefectKeys.filter((k) => !defectIndex.value.nodeByKey[k]?.disabled);
    setCheckedDefects(keys);
  }

  function clearDefects() {
    setCheckedDefects([]);
  }

  function moduleDefectRows(moduleKey: ModuleKey): ModuleDefectRow[] {
    const rows = moduleLeafDefectKeys(moduleKey)
      .map((k) => {
        const meta = defectIndex.value.nodeByKey[k];
        return { key: k, label: meta?.label || k, desc: meta?.desc, status: meta?.status || "ready", path: defectIndex.value.pathByKey[k]?.join(" / ") || "", badge: meta?.badge } as ModuleDefectRow;
      })
      .filter((r) => !!r.key);
    const enabledSet = new Set(checkedDefectKeys.value);
    const filtered = showOnlyEnabledDefects.value ? rows.filter((r) => enabledSet.has(r.key)) : rows;
    return filtered.sort((a, b) => {
      const ae = enabledSet.has(a.key);
      const be = enabledSet.has(b.key);
      if (ae !== be) return ae ? -1 : 1;
      if (a.status !== b.status) return a.status === "ready" ? -1 : 1;
      return a.label.localeCompare(b.label);
    });
  }

  // ─── Computed ───

  const visibleDefectKeys = computed(() => {
    const all = defectIndex.value.leafKeys.filter((k) => !!defectIndex.value.nodeByKey[k]?.algorithms);
    const q = defectSearch.value.trim().toLowerCase();
    let keys = all;
    if (showOnlyEnabledDefects.value) keys = keys.filter((k) => checkedDefectKeys.value.includes(k));
    if (q) {
      keys = keys.filter((k) => {
        const node = defectIndex.value.nodeByKey[k];
        const hay = `${node?.label || ""} ${node?.desc || ""}`.toLowerCase();
        return hay.includes(q);
      });
    }
    return keys;
  });

  const activeDefectMeta = computed<DefectTreeNode | null>(() => {
    const node = defectIndex.value.nodeByKey[activeDefectKey.value];
    if (!node || !node.algorithms) return null;
    return node;
  });

  const activeDefectPathText = computed(() => {
    const path = defectIndex.value.pathByKey[activeDefectKey.value];
    return path?.length ? path.join(" / ") : "-";
  });

  const activeDefectAlgorithms = computed<string[]>({
    get() { return activeDefectKey.value ? (defectAlgorithms.value[activeDefectKey.value] || []) : []; },
    set(v) { if (!activeDefectKey.value) return; defectAlgorithms.value[activeDefectKey.value] = Array.from(new Set((v || []).filter((x) => !!x))); },
  });

  const activeDefectEnabled = computed<boolean>({
    get() { return activeDefectKey.value ? checkedDefectKeys.value.includes(activeDefectKey.value) : false; },
    set(v) {
      const meta = activeDefectMeta.value;
      if (!activeDefectKey.value || !meta) return;
      if (meta.status !== "ready") return;
      const tree = defectTreeRef.value;
      if (tree?.setChecked) {
        tree.setChecked(activeDefectKey.value, !!v, true);
        checkedDefectKeys.value = getCheckedLeafKeys();
      } else {
        const set = new Set(checkedDefectKeys.value);
        if (v) set.add(activeDefectKey.value); else set.delete(activeDefectKey.value);
        checkedDefectKeys.value = Array.from(set);
      }
      syncDerivedFromChecked(checkedDefectKeys.value);
    },
  });

  const selectedLeafDefectCount = computed(() => checkedDefectKeys.value.length);

  const selectedDefectAlgorithmCount = computed(() => {
    const set = new Set<string>();
    for (const mk of selectedModules.value) {
      if (mk !== "dirty_data" && mk !== "distribution" && mk !== "adversarial" && mk !== "physics") continue;
      for (const a of getModuleAlgorithms(mk)) set.add(a);
    }
    return set.size;
  });

  const missingExecutorDefects = computed(() => {
    const out: string[] = [];
    for (const defectKey of checkedDefectKeys.value) {
      const meta = defectIndex.value.nodeByKey[defectKey];
      if (!meta || meta.status !== "ready") continue;
      if (!defectExecutor.value[defectKey]) out.push(defectKey);
    }
    return out;
  });

  const baselineMissing = computed(() => {
    if (!selectedModules.value.includes("distribution")) return false;
    if (distributionCompareMode.value !== "baseline_file") return false;
    return !baselineUploadedFile.value?.file_id;
  });

  const labelShiftMissingColumn = computed(() => {
    if (!checkedDefectKeys.value.includes("distribution.label_shift")) return false;
    const executor = defectExecutor.value["distribution.label_shift"];
    if (!executor || executor !== "mmd_ks_chi2") return false;
    return !distributionLabelColumn.value;
  });

  const labelMismatchMissingColumn = computed(() => {
    if (!checkedDefectKeys.value.includes("dirty_data.label_mismatch")) return false;
    return !labelMismatchLabelColumn.value;
  });

  const configIssuesHint = computed(() => {
    const issues: string[] = [];
    if (baselineMissing.value) issues.push("分布偏差选择了「基线文件对比」，但基线文件未上传（可回到上传步骤补齐，或切换到免基线模式）。");
    if (missingExecutorDefects.value.length) {
      const labels = missingExecutorDefects.value.map((k) => defectIndex.value.nodeByKey[k]?.label || k);
      const short = labels.length <= 3 ? labels.join("、") : `${labels.slice(0, 3).join("、")} 等`;
      issues.push(`有 ${labels.length} 个已启用缺陷未绑定执行算法：${short}`);
    }
    if (labelShiftMissingColumn.value) issues.push("已启用「标签分布变化」，请在「分布偏差 → 算法参数」中选择标签列。");
    if (labelMismatchMissingColumn.value) issues.push("已启用「疑似错标检测」，请在「脏数据 → 算法参数」中选择标签列。");
    return issues.join("；");
  });

  function defectBindRowClassName({ row }: { row: ModuleDefectRow }): string {
    if (!isDefectEnabled(row.key)) return "";
    if (!getDefectExecutor(row.key)) return "dqscan-row-missing-executor";
    return "";
  }

  const plannedAlgorithmsSelected = computed(() => {
    const planned = new Set<string>();
    for (const defectKey of checkedDefectKeys.value) {
      for (const a of defectAlgorithms.value[defectKey] || []) {
        if (algoMetaByKey.value[a]?.status === "planned") planned.add(a);
      }
    }
    return Array.from(planned);
  });

  const plannedAlgorithmsSelectedHint = computed(() => {
    const labels = plannedAlgorithmsSelected.value.map((k) => algoMetaByKey.value[k]?.label || k);
    if (!labels.length) return "";
    const short = labels.length <= 4 ? labels.join("、") : `${labels.slice(0, 4).join("、")} 等`;
    return `已选择 ${labels.length} 个即将上线算法，本次运行将自动跳过：${short}`;
  });

  const selectedModulesDisplay = computed(() => {
    if (!selectedModules.value.length) return "未选择";
    const titleByKey = new Map(modules.map((m) => [m.key, m.title]));
    return selectedModules.value.map((k) => titleByKey.get(k) || k).join("、");
  });

  const selectedDefectsDisplay = computed(() => {
    const labels = checkedDefectKeys.value.map((k) => defectIndex.value.nodeByKey[k]?.label).filter((x): x is string => !!x);
    if (!labels.length) return "未选择";
    if (labels.length <= 4) return labels.join("、");
    return `${labels.slice(0, 4).join("、")} 等${labels.length}项`;
  });

  const selectedAlgorithmsDisplay = computed(() => {
    const algoLabelMap: Record<string, string> = {};
    for (const a of Object.values(algoOptionByKey.value)) { if (!algoLabelMap[a.key]) algoLabelMap[a.key] = a.label; }
    const algoKeys = new Set<string>();
    for (const mk of selectedModules.value) {
      if (mk !== "dirty_data" && mk !== "distribution" && mk !== "adversarial" && mk !== "physics") continue;
      for (const a of getModuleAlgorithms(mk)) algoKeys.add(a);
    }
    const labels = Array.from(algoKeys).map((k) => algoLabelMap[k] || k).filter((x) => !!x);
    if (!labels.length) return "未选择";
    if (labels.length <= 3) return labels.join("、");
    return `${labels.slice(0, 3).join("、")} 等${labels.length}项`;
  });

  const canStart = computed(() =>
    !!currentUploadedFile.value?.file_id &&
    !!selectedAlgorithm.value &&
    selectedLeafDefectCount.value > 0 &&
    !baselineMissing.value &&
    !labelShiftMissingColumn.value &&
    !labelMismatchMissingColumn.value &&
    missingExecutorDefects.value.length === 0 &&
    !starting.value
  );

  const resultReady = computed(() => taskStatus.value === "SUCCESS" && !!result.value);

  const selectedAlgorithmLabel = computed(() => {
    const alg = algorithms.value.find((a) => a.name === selectedAlgorithm.value);
    return alg?.label || "表格数据质量探测引擎";
  });

  const selectedAlgorithmDesc = computed(() => {
    const alg = algorithms.value.find((a) => a.name === selectedAlgorithm.value);
    return alg?.description || "脏数据扫描 / 分布偏差 / 对抗性 / 物理保真度，并生成报告";
  });

  const statusText = computed(() => {
    const map: Record<TaskStatus, string> = { IDLE: "未开始", PENDING: "排队中", RUNNING: "运行中", SUCCESS: "已完成", FAILED: "失败" };
    return map[taskStatus.value] || "未知";
  });

  const statusTagType = computed(() => {
    switch (taskStatus.value) {
      case "SUCCESS": return "success";
      case "FAILED": return "danger";
      case "RUNNING": return "primary";
      case "PENDING": return "warning";
      default: return "info";
    }
  });

  const progressStatus = computed(() => {
    if (taskStatus.value === "FAILED") return "exception";
    if (taskStatus.value === "SUCCESS") return "success";
    return undefined;
  });

  // ─── 文件操作 ───

  function onBaselineFileChange(file: UploadFile, files: UploadFile[]) {
    baselineFileList.value = (files || []).slice(-1);
    const raw = (baselineFileList.value[0]?.raw || file.raw) as File | undefined;
    baselineSelectedFile.value = raw || null;
  }

  function onCurrentFileChange(file: UploadFile, files: UploadFile[]) {
    currentFileList.value = (files || []).slice(-1);
    const raw = (currentFileList.value[0]?.raw || file.raw) as File | undefined;
    currentSelectedFile.value = raw || null;
    void refreshColumnsFromCurrentFile();
  }

  async function refreshColumnsFromCurrentFile() {
    if (!currentSelectedFile.value) { columnOptions.value = []; columnsError.value = null; return; }
    columnsLoading.value = true;
    columnsError.value = null;
    try {
      const cols = await extractColumnsFromFile(currentSelectedFile.value);
      columnOptions.value = cols;
      distributionExcludeColumns.value = distributionExcludeColumns.value.filter((c) => cols.includes(c));
      if (distributionLabelColumn.value && !cols.includes(distributionLabelColumn.value)) distributionLabelColumn.value = "";
      dirtyWhitelistColumns.value = dirtyWhitelistColumns.value.filter((c) => cols.includes(c));
      dirtyBlacklistColumns.value = dirtyBlacklistColumns.value.filter((c) => cols.includes(c));
      duplicateKeyColumns.value = duplicateKeyColumns.value.filter((c) => cols.includes(c));
      rangeOnlyColumns.value = rangeOnlyColumns.value.filter((c) => cols.includes(c));
      if (labelMismatchLabelColumn.value && !cols.includes(labelMismatchLabelColumn.value)) labelMismatchLabelColumn.value = "";
      labelMismatchExcludeColumns.value = labelMismatchExcludeColumns.value.filter((c) => cols.includes(c));
      physicsConstraints.value = physicsConstraints.value.map((x) => {
        if (!x.column) return x;
        if (cols.includes(x.column)) return x;
        return { ...x, column: "" };
      });
      physicsColumnRules.value.forEach((rule) => { if (rule.column && !cols.includes(rule.column)) rule.column = ""; });
      physicsCrossRules.value.forEach((rule) => {
        if (rule.ifColumn && !cols.includes(rule.ifColumn)) rule.ifColumn = "";
        if (rule.thenColumn && !cols.includes(rule.thenColumn)) rule.thenColumn = "";
        if (rule.relationLeft && !cols.includes(rule.relationLeft)) rule.relationLeft = "";
        if (rule.relationRight && !cols.includes(rule.relationRight)) rule.relationRight = "";
        if (rule.sumTargetColumn && !cols.includes(rule.sumTargetColumn)) rule.sumTargetColumn = "";
        rule.sumColumns = (rule.sumColumns || []).filter((c) => cols.includes(c));
        rule.uniqueColumns = (rule.uniqueColumns || []).filter((c) => cols.includes(c));
      });
    } catch (e: any) {
      columnOptions.value = [];
      columnsError.value = e?.message ? String(e.message) : "解析列名失败";
    } finally {
      columnsLoading.value = false;
    }
  }

  function clearBaseline() {
    baselineFileList.value = [];
    baselineSelectedFile.value = null;
    baselineUploading.value = false;
    baselineUploadedFile.value = null;
  }

  async function doUploadBaseline() {
    if (!baselineSelectedFile.value) return;
    baselineUploading.value = true;
    try {
      const res = await DQScanAPI.uploadFile(baselineSelectedFile.value);
      baselineUploadedFile.value = res.data.data;
      pushLog(`基线文件上传成功：${baselineUploadedFile.value?.filename}`);
    } finally {
      baselineUploading.value = false;
    }
  }

  async function doUploadCurrent() {
    if (!currentSelectedFile.value) return;
    currentUploading.value = true;
    try {
      const res = await DQScanAPI.uploadFile(currentSelectedFile.value);
      currentUploadedFile.value = res.data.data;
      gotoStep(2);
      pushLog(`当前文件上传成功：${currentUploadedFile.value?.filename}`);
    } finally {
      currentUploading.value = false;
    }
  }

  // ─── 算法加载 ───

  async function loadAlgorithms() {
    algorithmsLoading.value = true;
    try {
      const res = await DQScanAPI.listAlgorithms();
      algorithms.value = res.data.data || [];
      const defaultEngine = selectedModality.value === "image" ? "image_quality_engine" : "tabular_quality_engine";
      if (algorithms.value.some((a) => a.name === defaultEngine)) {
        selectedAlgorithm.value = defaultEngine;
      } else if (algorithms.value.length > 0) {
        selectedAlgorithm.value = algorithms.value[0].name;
      }
    } finally {
      algorithmsLoading.value = false;
    }
  }

  async function loadDefectsCatalog() {
    defectsCatalogLoading.value = true;
    defectsCatalogError.value = null;
    try {
      const modality = selectedModality.value || "tabular";
      const res = await DQScanAPI.getDefectsCatalog({ modality });
      const catalog = res?.data?.data;
      const tree = catalog?.tree;
      if (Array.isArray(tree) && tree.length) {
        defectTreeData.value = tree as any;
        await nextTick();
        const allowed = new Set(defectIndex.value.leafKeys);
        setCheckedDefects(checkedDefectKeys.value.filter((k) => allowed.has(k)));
        if (!defectIndex.value.nodeByKey[activeDefectKey.value]) {
          activeDefectKey.value = defectIndex.value.leafKeys[0] || "dirty_data.anomaly";
        }
        for (const mk of selectedModules.value) {
          if (mk !== "dirty_data" && mk !== "distribution" && mk !== "adversarial" && mk !== "physics") continue;
          autoBindModuleDefects(mk);
        }
        pushLog("缺陷树已从后端加载（/defects）");
      }
    } catch (e: any) {
      defectsCatalogError.value = e?.message ? String(e.message) : "加载缺陷树失败";
      pushLog(`加载缺陷树失败，将使用内置配置：${defectsCatalogError.value}`);
    } finally {
      defectsCatalogLoading.value = false;
    }
  }

  // ─── 物理规则操作 ───

  function addPhysicsConstraint() {
    physicsConstraints.value.push({ id: makeTempId("constraint"), column: "", min: undefined, max: undefined });
  }

  function removePhysicsConstraint(id: string) {
    physicsConstraints.value = physicsConstraints.value.filter((x) => x.id !== id);
  }

  function addColumnRule() {
    physicsColumnRules.value.push({ id: makeTempId("column_rule"), column: "", type: "not_null", values: "", pattern: "" });
  }

  function removeColumnRule(id: string) {
    physicsColumnRules.value = physicsColumnRules.value.filter((x) => x.id !== id);
  }

  function handleColumnRuleTypeChange(rule: PhysicsColumnRule, next: PhysicsColumnRuleType) {
    rule.type = next;
    if (next === "not_null") { rule.values = ""; rule.pattern = ""; }
    else if (next === "in_set") { rule.pattern = ""; }
    else if (next === "regex") { rule.values = ""; }
  }

  function resetCrossRuleFields(rule: PhysicsCrossRule) {
    rule.ifColumn = ""; rule.ifOp = "=="; rule.ifValue = "";
    rule.thenColumn = ""; rule.thenOp = "=="; rule.thenValue = "";
    rule.relationLeft = ""; rule.relationOp = "=="; rule.relationRight = ""; rule.relationTolerance = undefined;
    rule.sumColumns = []; rule.sumTargetColumn = ""; rule.sumTargetValue = ""; rule.sumTolerance = undefined;
    rule.uniqueColumns = [];
  }

  function addCrossRule(type: PhysicsCrossRuleType = "if_then") {
    const base: PhysicsCrossRule = { id: makeTempId("cross_rule"), type, ifOp: "==", thenOp: "==", relationOp: "==", sumColumns: [], uniqueColumns: [] };
    resetCrossRuleFields(base);
    base.type = type;
    physicsCrossRules.value.push(base);
  }

  function removeCrossRule(id: string) {
    physicsCrossRules.value = physicsCrossRules.value.filter((x) => x.id !== id);
  }

  function handleCrossRuleTypeChange(rule: PhysicsCrossRule, next: PhysicsCrossRuleType) {
    resetCrossRuleFields(rule);
    rule.type = next;
  }

  // ─── 模块面板 ───

  function expandAllModulePanels() { openModulePanels.value = modules.map((m) => m.key); }
  function collapseAllModulePanels() { openModulePanels.value = []; }
  function expandAllDefectPanels() { openDefectPanels.value = [...visibleDefectKeys.value]; }
  function collapseAllDefectPanels() { openDefectPanels.value = []; }

  // ─── WebSocket / 任务 ───

  function connectWs(id: string) {
    resetWs();
    const base = import.meta.env.VITE_APP_WS_ENDPOINT || "";
    const url = `${base}/api/v1/application/dqscan/ws/${id}`;
    ws = new WebSocket(url);
    ws.onopen = () => { pushLog("WebSocket 已连接"); };
    ws.onmessage = async (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        if (msg.type === "snapshot") {
          pushLog(`任务快照：${msg.status}，progress=${msg.progress}`);
          progress.value = Number(msg.progress ?? progress.value);
          taskStatus.value = (msg.status as TaskStatus) ?? taskStatus.value;
          if (msg.error) taskError.value = String(msg.error);
          return;
        }
        if (msg.type === "log") { pushLog(msg.message); }
        else if (msg.type === "progress") { progress.value = Number(msg.value ?? progress.value); }
        else if (msg.type === "done") {
          pushLog(msg.message || "完成");
          taskStatus.value = "SUCCESS";
          progress.value = 100;
          clearPoll();
          await fetchResult();
          gotoStep(4);
        } else if (msg.type === "error") {
          pushLog(`错误：${msg.message}`);
          taskStatus.value = "FAILED";
          taskError.value = msg.message;
          clearPoll();
        }
      } catch { pushLog(String(evt.data)); }
    };
    ws.onclose = () => { pushLog("WebSocket 已断开"); };
    ws.onerror = () => { pushLog("WebSocket 错误"); };
  }

  async function refreshTask() {
    if (!taskId.value) return;
    const res = await DQScanAPI.getTask(taskId.value);
    const data = res.data.data;
    taskStatus.value = (data.status as TaskStatus) ?? taskStatus.value;
    progress.value = Number(data.progress ?? progress.value);
    taskError.value = data.error || null;
  }

  async function fetchResult() {
    if (!taskId.value) return;
    try {
      const res = await DQScanAPI.getResult(taskId.value);
      result.value = res.data.data;
      await fetchReports();
    } catch (e: any) { pushLog(`获取结果失败：${e?.message || e}`); }
  }

  async function fetchReports() {
    if (!taskId.value) return;
    reportsLoading.value = true;
    try {
      const res = await DQScanAPI.getReports(taskId.value, { report_type: "json" });
      reports.value = res.data.data.reports || {};
      if (!activeReportModule.value) {
        activeReportModule.value = Object.keys(reports.value)[0] || Object.keys(result.value?.modules || {})[0] || "";
      }
    } catch (e: any) {
      pushLog(`获取报告失败：${e?.message || e}`);
      reports.value = {};
    } finally {
      reportsLoading.value = false;
    }
  }

  // ─── payload builders ───

  function buildPhysicsConstraintsPayload() {
    const constraints: Record<string, any> = {};
    for (const x of physicsConstraints.value) {
      if (!x.column) continue;
      const rule: Record<string, any> = {};
      if (typeof x.min === "number") rule.min = x.min;
      if (typeof x.max === "number") rule.max = x.max;
      if (Object.keys(rule).length) constraints[x.column] = rule;
    }
    return constraints;
  }

  function buildPhysicsRulesPayload() {
    const rules: any[] = [];
    for (const r of physicsColumnRules.value) {
      if (!r.column) continue;
      if (r.type === "not_null") { rules.push({ id: r.id, type: "not_null", col: r.column }); }
      else if (r.type === "in_set") { const values = splitCsvValues(r.values); if (values.length) rules.push({ id: r.id, type: "in_set", col: r.column, values }); }
      else if (r.type === "regex") { const pattern = r.pattern?.trim(); if (pattern) rules.push({ id: r.id, type: "regex", col: r.column, pattern }); }
    }
    for (const r of physicsCrossRules.value) {
      if (r.type === "if_then") {
        if (!(r.ifColumn && r.thenColumn && r.ifOp && r.thenOp)) continue;
        const condValue = normalizeRuleValue(r.ifValue);
        const thenValue = normalizeRuleValue(r.thenValue);
        if (condValue === undefined || thenValue === undefined) continue;
        rules.push({ id: r.id, type: "if_then", condition: { col: r.ifColumn, op: r.ifOp, value: condValue }, then: { col: r.thenColumn, op: r.thenOp, value: thenValue } });
      } else if (r.type === "relation") {
        if (!(r.relationLeft && r.relationOp && r.relationRight)) continue;
        rules.push({ id: r.id, type: "relation", left: { col: r.relationLeft }, op: r.relationOp, right: { col: r.relationRight }, tolerance: typeof r.relationTolerance === "number" ? r.relationTolerance : undefined });
      } else if (r.type === "sum") {
        const cols = (r.sumColumns || []).filter((c) => !!c);
        if (!cols.length) continue;
        const payload: any = { id: r.id, type: "sum", columns: cols };
        if (r.sumTargetColumn) payload.target_column = r.sumTargetColumn;
        else { const targetValue = normalizeRuleValue(r.sumTargetValue); if (targetValue !== undefined) payload.target_value = targetValue; }
        if (typeof r.sumTolerance === "number") payload.tolerance = r.sumTolerance;
        rules.push(payload);
      } else if (r.type === "unique") {
        const cols = (r.uniqueColumns || []).filter((c) => !!c);
        if (!cols.length) continue;
        rules.push({ id: r.id, type: "unique", columns: cols });
      }
    }
    return rules;
  }

  // ─── startScan ───

  async function startScan() {
    if (!currentUploadedFile.value?.file_id) return;
    const isImage = selectedModality.value === "image";
    if (!isImage && baselineMissing.value) {
      ElMessage.warning("已选择「基线文件对比」，但基线文件未上传。请回到上传步骤补齐，或切换到「免基线」模式。");
      gotoStep(1); return;
    }
    if (!isImage && labelShiftMissingColumn.value) { ElMessage.warning("已启用「标签分布变化」，请先在「分布偏差 → 算法参数」中选择标签列。"); return; }
    if (!isImage && labelMismatchMissingColumn.value) { ElMessage.warning("已启用「疑似错标检测」，请先在「脏数据 → 算法参数」中选择标签列。"); return; }
    if (!isImage && missingExecutorDefects.value.length) { ElMessage.warning("还有已启用缺陷未绑定执行算法，请在「缺陷绑定」中完成选择。"); return; }
    starting.value = true;
    result.value = null;
    reports.value = {};
    activeReportModule.value = "";
    taskError.value = null;
    logs.value = [];
    progress.value = 0;
    taskStatus.value = "PENDING";
    gotoStep(3);

    try {
      // ── 图片模态快速路径 ──
      if (isImage) {
        const imageParams: Record<string, any> = {
          defects: {
            selected: {
              "dirty_data.image_label_mismatch": {
                enabled: true,
                module: "dirty_data",
                label: "图片错标检测",
                params: {
                  algorithm: imageLabelAlgorithm.value,
                  k: imageLabelK.value,
                  threshold: imageLabelThreshold.value,
                  max_samples: imageLabelMaxSamples.value,
                  max_examples: imageLabelMaxExamples.value,
                  batch_size: imageLabelBatchSize.value,
                  device: imageLabelDevice.value,
                  image_column: imageLabelImageColumn.value,
                  label_column: imageLabelLabelColumn.value,
                  label_csv_path: imageLabelCsvPath.value || undefined,
                },
              },
            },
          },
        };
        const res = await DQScanAPI.createTask({
          file_id: currentUploadedFile.value.file_id,
          algorithm: "image_quality_engine",
          params: imageParams,
          data_type: "image",
        });
        taskId.value = res.data.data.task_id;
        pushLog(`图片检测任务已创建：${taskId.value}`);
        taskStatus.value = "RUNNING";
        connectWs(taskId.value);
        clearPoll();
        pollTimer = window.setInterval(async () => {
          try {
            await refreshTask();
            if (taskStatus.value === "SUCCESS") { clearPoll(); await fetchResult(); }
            else if (taskStatus.value === "FAILED") { clearPoll(); }
          } catch {}
        }, 2000);
        return;
      }

      const enabledDefects = [...checkedDefectKeys.value];
      const effectiveModules = selectedModules.value?.length
        ? selectedModules.value
        : Array.from(new Set(enabledDefects.map((k) => moduleKeyFromDefectKey(k)).filter((x): x is string => !!x)));

      const effectiveModuleSet = new Set(effectiveModules as string[]);
      const moduleAlgorithmsAll: Record<ModuleKey, string[]> = {
        dirty_data: effectiveModuleSet.has("dirty_data") ? getModuleAlgorithms("dirty_data") : [],
        distribution: effectiveModuleSet.has("distribution") ? getModuleAlgorithms("distribution") : [],
        adversarial: effectiveModuleSet.has("adversarial") ? getModuleAlgorithms("adversarial") : [],
        physics: effectiveModuleSet.has("physics") ? getModuleAlgorithms("physics") : [],
      };

      const isPlannedAlgo = (algoKey: string) => algoOptionByKey.value[algoKey]?.status === "planned";
      const runtimeList = (list: string[]) => list.filter((a) => !isPlannedAlgo(a));
      const skippedList = (list: string[]) => list.filter((a) => isPlannedAlgo(a));

      const moduleAlgorithmsRuntime: Record<ModuleKey, string[]> = {
        dirty_data: runtimeList(moduleAlgorithmsAll.dirty_data),
        distribution: runtimeList(moduleAlgorithmsAll.distribution),
        adversarial: runtimeList(moduleAlgorithmsAll.adversarial),
        physics: runtimeList(moduleAlgorithmsAll.physics),
      };

      const moduleAlgorithmsSkipped: Record<ModuleKey, string[]> = {
        dirty_data: skippedList(moduleAlgorithmsAll.dirty_data),
        distribution: skippedList(moduleAlgorithmsAll.distribution),
        adversarial: skippedList(moduleAlgorithmsAll.adversarial),
        physics: skippedList(moduleAlgorithmsAll.physics),
      };

      const params: Record<string, any> = {
        modules: effectiveModules.length ? effectiveModules : undefined,
        module_algorithms: moduleAlgorithmsAll,
        module_algorithms_runtime: moduleAlgorithmsRuntime,
        module_algorithms_skipped: moduleAlgorithmsSkipped,
        runtime: { preset: scanPreset.value, max_samples: globalMaxSamples.value, parallelism: globalParallelism.value, seed: globalSeed.value },
        report: { ...reportOptions },
        algorithms_config: { ...toRaw(algoParams) },
      };

      if (effectiveModules.includes("distribution")) {
        params.distribution_compare_mode = distributionCompareMode.value;
        params.p_val = distributionPVal.value;
        params.train_test_split = distributionTrainTestSplit.value;
        if (distributionLabelColumn.value) params.label_column = distributionLabelColumn.value;
        if (distributionExcludeColumns.value.length) params.exclude_columns = distributionExcludeColumns.value;
      }

      if (effectiveModules.includes("dirty_data")) {
        params.contamination = dirtyContamination.value;
        params.dirty_data = {
          enabled_checks: dirtyEnabledChecks.value,
          missing_threshold: dirtyMissingThreshold.value,
          duplicate_threshold: dirtyDuplicateThreshold.value,
          duplicate_key_columns: duplicateKeyColumns.value,
          duplicate_similarity: duplicateSimilarity.value,
          max_examples: dirtyMaxExamples.value,
          whitelist_columns: dirtyWhitelistColumns.value,
          blacklist_columns: dirtyBlacklistColumns.value,
          range: { method: rangeMethod.value, sigma: rangeSigma.value, iqr_factor: rangeIqrFactor.value, only_columns: rangeOnlyColumns.value },
          label_mismatch: {
            label_column: labelMismatchLabelColumn.value,
            max_samples: labelMismatchMaxSamples.value,
            exclude_columns: labelMismatchExcludeColumns.value,
            n_splits: labelMismatchNSplits.value,
            threshold_prob_true: labelMismatchThresholdProbTrue.value,
            threshold_prob_pred: labelMismatchThresholdProbPred.value,
            score_method: labelMismatchScoreMethod.value,
            filter_by: labelMismatchFilterBy.value,
            fraction_noise: labelMismatchFractionNoise.value,
            max_examples: labelMismatchMaxExamples.value,
          },
        };
      }

      if (effectiveModules.includes("adversarial")) {
        params.adversarial = {
          epsilon: adversarialEpsilon.value, max_iter: adversarialMaxIter.value,
          random_trials: adversarialRandomTrials.value, random_features: adversarialRandomFeatures.value,
          max_samples: adversarialMaxSamples.value, seed: adversarialSeed.value,
          learning_rate: adversarialLearningRate.value, confidence: adversarialConfidence.value,
          batch_size: adversarialBatchSize.value,
        };
      }

      if (effectiveModules.includes("physics")) {
        const constraints = buildPhysicsConstraintsPayload();
        const rulesPayload = buildPhysicsRulesPayload();
        params.physics = { auto_constraints: physicsAutoConstraints.value, constraints, rules: rulesPayload.length ? rulesPayload : undefined };
      }

      const defectsPayload: Record<string, any> = {};
      for (const defectKey of enabledDefects) {
        const meta = defectIndex.value.nodeByKey[defectKey];
        const moduleKey = moduleKeyFromDefectKey(defectKey);
        if (!moduleKey) continue;
        const executorSelected = defectExecutor.value[defectKey] || null;
        const algorithmsSelected = executorSelected ? [executorSelected] : [];
        const algorithmsRuntime = executorSelected && !isPlannedAlgo(executorSelected) ? [executorSelected] : [];
        const algorithmsSkipped = executorSelected && isPlannedAlgo(executorSelected) ? [executorSelected] : [];
        const executorRuntime = executorSelected && !isPlannedAlgo(executorSelected) ? executorSelected : null;
        const buildParamsFor = () => {
          if (defectKey === "dirty_data.anomaly") return { contamination: dirtyContamination.value, max_examples: dirtyMaxExamples.value, max_samples: globalMaxSamples.value };
          if (defectKey === "dirty_data.missing") return { missing_threshold: dirtyMissingThreshold.value, whitelist_columns: dirtyWhitelistColumns.value, blacklist_columns: dirtyBlacklistColumns.value };
          if (defectKey === "dirty_data.duplicate") return { duplicate_threshold: dirtyDuplicateThreshold.value, key_columns: duplicateKeyColumns.value, similarity: duplicateSimilarity.value };
          if (defectKey === "dirty_data.range") return { method: rangeMethod.value, sigma: rangeSigma.value, iqr_factor: rangeIqrFactor.value, only_columns: rangeOnlyColumns.value };
          if (defectKey === "dirty_data.label_mismatch") return {
            label_column: labelMismatchLabelColumn.value, max_samples: labelMismatchMaxSamples.value, exclude_columns: labelMismatchExcludeColumns.value,
            n_splits: labelMismatchNSplits.value, threshold_prob_true: labelMismatchThresholdProbTrue.value, threshold_prob_pred: labelMismatchThresholdProbPred.value,
            score_method: labelMismatchScoreMethod.value, filter_by: labelMismatchFilterBy.value, fraction_noise: labelMismatchFractionNoise.value, max_examples: labelMismatchMaxExamples.value,
          };
          if (defectKey === "distribution.numeric_drift" || defectKey === "distribution.categorical_drift") return { compare_mode: distributionCompareMode.value, p_val: distributionPVal.value, train_test_split: distributionTrainTestSplit.value, exclude_columns: distributionExcludeColumns.value };
          if (defectKey === "distribution.label_shift") return { label_column: distributionLabelColumn.value, p_val: distributionPVal.value };
          if (defectKey.startsWith("adversarial")) return {
            epsilon: adversarialEpsilon.value, max_iter: adversarialMaxIter.value, random_trials: adversarialRandomTrials.value,
            random_features: adversarialRandomFeatures.value, max_samples: adversarialMaxSamples.value, seed: adversarialSeed.value,
            learning_rate: adversarialLearningRate.value, confidence: adversarialConfidence.value, batch_size: adversarialBatchSize.value,
          };
          if (defectKey === "physics.rules") {
            const constraints = buildPhysicsConstraintsPayload();
            const rulesPayload = buildPhysicsRulesPayload();
            return { auto_constraints: physicsAutoConstraints.value, constraints, rules: rulesPayload.length ? rulesPayload : undefined };
          }
          return {};
        };
        defectsPayload[defectKey] = {
          enabled: true, status: meta?.status || "ready", module: moduleKey, label: meta?.label,
          path: defectIndex.value.pathByKey[defectKey]?.join(" / "),
          algorithms: algorithmsSelected, algorithms_runtime: algorithmsRuntime, algorithms_skipped: algorithmsSkipped,
          executor_algorithm: executorSelected, executor_runtime: executorRuntime, params: buildParamsFor(),
        };
      }

      params.defects = {
        preset: scanPreset.value,
        global: { max_samples: globalMaxSamples.value, parallelism: globalParallelism.value, seed: globalSeed.value },
        report: { ...reportOptions },
        algorithms_config: { ...toRaw(algoParams) },
        selected: defectsPayload,
      };

      const baselineFileId =
        effectiveModules.includes("distribution") && distributionCompareMode.value === "baseline_file"
          ? baselineUploadedFile.value?.file_id
          : undefined;
      const res = await DQScanAPI.createTask({
        file_id: currentUploadedFile.value.file_id,
        baseline_file_id: baselineFileId,
        algorithm: selectedAlgorithm.value,
        params,
        data_type: selectedModality.value || "tabular",
      });
      taskId.value = res.data.data.task_id;
      pushLog(`任务已创建：${taskId.value}`);
      taskStatus.value = "RUNNING";
      connectWs(taskId.value);

      clearPoll();
      pollTimer = window.setInterval(async () => {
        try {
          await refreshTask();
          if (taskStatus.value === "SUCCESS") { clearPoll(); await fetchResult(); }
          else if (taskStatus.value === "FAILED") { clearPoll(); }
        } catch {}
      }, 2000);
    } finally {
      starting.value = false;
    }
  }

  // ─── 下载 ───

  async function downloadResultJson() {
    if (!taskId.value) return;
    const { saveAs } = await import("file-saver");
    const res = await DQScanAPI.downloadResult(taskId.value);
    const blob = (res as any).data as Blob;
    saveAs(blob, "result.json");
  }

  async function downloadArtifact(path: string, filename: string) {
    if (!taskId.value) return;
    const { saveAs } = await import("file-saver");
    const res = await DQScanAPI.downloadArtifact(taskId.value, path);
    const blob = (res as any).data as Blob;
    saveAs(blob, filename);
  }

  // ─── 重置 ───

  function resetAll() {
    resetWs();
    clearPoll();
    activeStep.value = 0;
    baselineFileList.value = [];
    baselineSelectedFile.value = null;
    baselineUploading.value = false;
    baselineUploadedFile.value = null;
    currentFileList.value = [];
    currentSelectedFile.value = null;
    currentUploading.value = false;
    currentUploadedFile.value = null;
    defectSearch.value = "";
    showOnlyEnabledDefects.value = false;
    openDefectPanels.value = [...defaultCheckedDefectKeys];
    scanPreset.value = "balanced";
    globalMaxSamples.value = 20000;
    globalParallelism.value = 2;
    globalSeed.value = 42;
    reportOptions.docx = true;
    reportOptions.summary = true;
    reportOptions.max_examples = 50;
    algoParams.psi_bins = 10;
    algoParams.psi_bucket = "quantile";
    algoParams.wasserstein_threshold = 0.1;
    algoParams.embedding_model = "small";
    algoParams.embedding_batch_size = 64;
    algoParams.iforest_estimators = 200;
    algoParams.iforest_max_samples = 256;
    algoParams.ae_latent_dim = 16;
    algoParams.ae_epochs = 20;
    algoParams.fgsm_norm = "linf";
    algoParams.fgsm_targeted = false;
    algoParams.pgd_steps = 20;
    algoParams.pgd_step_size = 0.01;
    algoParams.pgd_random_start = true;
    defectAlgorithms.value = createDefaultDefectAlgorithms();
    checkedDefectKeys.value = [...defaultCheckedDefectKeys];
    setCheckedDefects(checkedDefectKeys.value);
    activeDefectKey.value = "dirty_data.anomaly";
    activeDefectTab.value = "algo";
    activeModuleTab.value = "distribution";
    distributionAlgorithms.value = ["mmd_ks_chi2"];
    dirtyDataAlgorithms.value = ["ecod_3sigma"];
    adversarialAlgorithms.value = ["zoo_or_random"];
    physicsAlgorithmsRef.value = ["pandera_or_fallback"];
    distributionCompareMode.value = "baseline_file";
    distributionTrainTestSplit.value = 0.7;
    distributionLabelColumn.value = "";
    distributionPVal.value = 0.05;
    distributionExcludeColumns.value = [];
    dirtyContamination.value = 0.1;
    dirtyMissingThreshold.value = 0.1;
    dirtyDuplicateThreshold.value = 0.02;
    dirtyEnabledChecks.value = ["anomaly", "missing", "duplicate", "range"];
    dirtyMaxExamples.value = 50;
    dirtyWhitelistColumns.value = [];
    dirtyBlacklistColumns.value = [];
    duplicateKeyColumns.value = [];
    duplicateSimilarity.value = 0.92;
    rangeMethod.value = "sigma";
    rangeSigma.value = 3;
    rangeIqrFactor.value = 1.5;
    rangeOnlyColumns.value = [];
    labelMismatchLabelColumn.value = "";
    labelMismatchMaxSamples.value = 20000;
    labelMismatchExcludeColumns.value = [];
    labelMismatchNSplits.value = 5;
    labelMismatchThresholdProbTrue.value = 0.2;
    labelMismatchThresholdProbPred.value = 0.6;
    labelMismatchScoreMethod.value = "self_confidence";
    labelMismatchFilterBy.value = "both";
    labelMismatchFractionNoise.value = 0.05;
    labelMismatchMaxExamples.value = 500;
    adversarialEpsilon.value = 0.05;
    adversarialMaxIter.value = 20;
    adversarialRandomTrials.value = 40;
    adversarialRandomFeatures.value = 3;
    adversarialMaxSamples.value = 50;
    adversarialSeed.value = 42;
    adversarialLearningRate.value = 0.01;
    adversarialConfidence.value = 0;
    adversarialBatchSize.value = 1;
    physicsAutoConstraints.value = true;
    physicsConstraints.value = [];
    physicsColumnRules.value = [];
    physicsCrossRules.value = [];
    columnOptions.value = [];
    columnsLoading.value = false;
    columnsError.value = null;
    starting.value = false;
    taskId.value = null;
    progress.value = 0;
    logs.value = [];
    taskStatus.value = "IDLE";
    taskError.value = null;
    result.value = null;
    reportsLoading.value = false;
    reports.value = {};
    activeReportModule.value = "";
  }

  // ─── 初始化辅助 ───
  function initDerivedState() {
    syncDerivedFromChecked(checkedDefectKeys.value);
    for (const mk of selectedModules.value) {
      if (mk !== "dirty_data" && mk !== "distribution" && mk !== "adversarial" && mk !== "physics") continue;
      autoBindModuleDefects(mk);
    }
  }

  function moduleTitle(key: string) {
    return modules.find((m) => m.key === key)?.title || key;
  }

  // ─── Watchers (注意：需在 setup 中调用) ───
  function setupWatchers() {
    watch(defectSearch, (v) => { defectTreeRef.value?.filter?.(v); });
    watch(visibleDefectKeys, (keys) => {
      const set = new Set(keys);
      openDefectPanels.value = openDefectPanels.value.filter((k) => set.has(k));
    }, { immediate: true });
    watch(selectedModality, async () => {
      await loadAlgorithms();
      await loadDefectsCatalog();
    });
  }

  function setupLifecycle() {
    onMounted(async () => {
      await loadAlgorithms();
      await loadDefectsCatalog();
    });
    onBeforeUnmount(() => {
      resetWs();
      clearPoll();
    });
  }

  // ─── 返回所有状态和方法 ───
  return {
    // 步骤
    activeStep, gotoStep, stepClass,
    // 模态
    selectedModality,
    // 文件上传
    baselineUploadRef, currentUploadRef,
    baselineFileList, baselineSelectedFile, baselineUploading, baselineUploadedFile,
    currentFileList, currentSelectedFile, currentUploading, currentUploadedFile,
    onBaselineFileChange, onCurrentFileChange, clearBaseline, doUploadBaseline, doUploadCurrent,
    // 算法
    algorithmsLoading, algorithms, selectedAlgorithm, loadAlgorithms,
    selectedAlgorithmLabel, selectedAlgorithmDesc,
    // 模块
    selectedModules, openModulePanels, moduleWorkbenchTab,
    expandAllModulePanels, collapseAllModulePanels,
    isModuleEnabled, setModuleEnabled, disableAllModuleDefects,
    moduleAllDefectCount, moduleEnabledDefectCount,
    moduleAlgorithmOptions, getModuleAlgorithms,
    moduleAlgorithmsSelected, setModuleAlgorithms,
    moduleDefectRows, moduleLeafDefectKeys, moduleKeyFromDefectKey,
    autoBindModuleDefects,
    boundDefectKeys, boundDefectCount, boundDefectTags,
    // 缺陷树
    defectSearch, defectTreeRef, defectTreeProps, defectTreeData, defectIndex,
    defectsCatalogLoading, defectsCatalogError, loadDefectsCatalog,
    checkedDefectKeys, setCheckedDefects,
    activeDefectKey, activeDefectTab, activeDefectMeta, activeDefectPathText,
    activeDefectAlgorithms, activeDefectEnabled,
    defectAlgorithms, defectExecutor,
    isDefectEnabled, setDefectEnabled,
    getDefectExecutor, setDefectExecutor,
    executorAlgorithmOptions,
    getDefectAlgorithms, setDefectAlgorithms, clearDefectAlgorithms, applyAlgorithmsToModule,
    defectMeta, defectPathText,
    onDefectNodeClick, onDefectCheck, filterDefectNode,
    selectAllDefects, selectRecommendedDefects, clearDefects,
    showOnlyEnabledDefects, openDefectPanels, visibleDefectKeys,
    expandAllDefectPanels, collapseAllDefectPanels,
    defectBindRowClassName,
    algoOptionByKey, algoMetaByKey,
    plannedAlgorithmsSelected, plannedAlgorithmsSelectedHint,
    activeModuleTab,
    // 扫描参数
    scanPreset, scanPresetLabel, globalMaxSamples, globalParallelism, globalSeed,
    reportOptions, algoParams,
    // 分布偏差
    distributionCompareMode, distributionTrainTestSplit, distributionLabelColumn, distributionPVal,
    distributionExcludeColumns, excludeColumnsDisplay,
    columnOptions, columnsLoading, columnsError,
    // 脏数据
    dirtyContamination, dirtyMissingThreshold, dirtyDuplicateThreshold,
    dirtyEnabledChecks, dirtyMaxExamples, dirtyWhitelistColumns, dirtyBlacklistColumns,
    duplicateKeyColumns, duplicateSimilarity,
    rangeMethod, rangeSigma, rangeIqrFactor, rangeOnlyColumns,
    // label mismatch
    labelMismatchLabelColumn, labelMismatchMaxSamples, labelMismatchExcludeColumns,
    labelMismatchExcludeColumnsDisplay,
    labelMismatchNSplits, labelMismatchThresholdProbTrue, labelMismatchThresholdProbPred,
    labelMismatchScoreMethod, labelMismatchFilterBy, labelMismatchFractionNoise, labelMismatchMaxExamples,
    // 图片错标检测
    imageLabelAlgorithm, imageLabelK, imageLabelThreshold, imageLabelMaxSamples,
    imageLabelMaxExamples, imageLabelBatchSize, imageLabelDevice,
    imageLabelImageColumn, imageLabelLabelColumn, imageLabelCsvPath,
    // 对抗性
    adversarialEpsilon, adversarialMaxIter, adversarialRandomTrials, adversarialRandomFeatures,
    adversarialMaxSamples, adversarialSeed, adversarialLearningRate, adversarialConfidence, adversarialBatchSize,
    // 物理保真度
    physicsAutoConstraints, physicsConstraints, physicsColumnRules, physicsCrossRules,
    addPhysicsConstraint, removePhysicsConstraint,
    addColumnRule, removeColumnRule, handleColumnRuleTypeChange,
    addCrossRule, removeCrossRule, handleCrossRuleTypeChange,
    // 任务
    starting, taskId, progress, logs, taskStatus, taskError, result,
    canStart, resultReady, startScan, refreshTask,
    statusText, statusTagType, progressStatus,
    pushLog,
    // 报告
    reportsLoading, reports, activeReportModule,
    fetchResult, fetchReports,
    // 下载
    downloadResultJson, downloadArtifact,
    // 结果展示
    selectedModulesDisplay, selectedDefectsDisplay, selectedAlgorithmsDisplay,
    selectedLeafDefectCount, selectedDefectAlgorithmCount,
    missingExecutorDefects, baselineMissing, labelShiftMissingColumn, labelMismatchMissingColumn,
    configIssuesHint,
    // 重置
    resetAll,
    // 初始化
    initDerivedState, setupWatchers, setupLifecycle,
    moduleTitle,
  };
}

export function useDqscanInject() {
  const state = inject(DqscanStateKey);
  if (!state) throw new Error("useDqscanInject must be used within a component that provides DqscanStateKey");
  return state;
}

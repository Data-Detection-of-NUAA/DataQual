---
marp: true
paginate: true
---
# 数据合规审计系统
## 技术实现方案

---

# 第1页：系统架构与核心流程

## 一、系统架构（五层设计）

```
┌─────────────────────────────────────────────────┐
│          前端交互层 (Vue3 + Element Plus)        │
│    4步向导：法规上传 → AI匹配 → 规则选择 → 审计 │
├─────────────────────────────────────────────────┤
│           API路由层 (FastAPI Controller)        │
│  TaskRouter / RuleRouter / RegulationRouter     │
├─────────────────────────────────────────────────┤
│           业务逻辑层 (Service Layer)             │
│  AuditTaskService / AuditRuleService / ...      │
├─────────────────────────────────────────────────┤
│        核心引擎层 (7个独立引擎模块)              │
│ ┌──────────────┬──────────────┬─────────────┐  │
│ │ FileParser   │ AIMatcher    │AuditEngine  │  │
│ │ 文件解析引擎  │ AI匹配引擎   │ 审计引擎    │  │
│ ├──────────────┼──────────────┼─────────────┤  │
│ │ContentDetector│RuleInstantiator│ReportGen │  │
│ │ 内容检测引擎  │ 规则实例化   │ 报告生成    │  │
│ └──────────────┴──────────────┴─────────────┘  │
├─────────────────────────────────────────────────┤
│          数据持久层 (SQLAlchemy ORM)            │
│  Task/Rule/RuleTemplate/Regulation/Error        │
└─────────────────────────────────────────────────┘
```

## 二、核心业务流程

```mermaid
graph LR
    A[步骤1: 上传法规文件] -->|FileParser解析| B[步骤2: AI智能匹配规则]
    B -->|AIMatcher调用大模型| C[步骤3: 用户确认规则]
    C -->|选择审计规则| D[步骤4: 上传数据集]
    D -->|AuditEngine验证| E[生成审计报告]
    E --> F[Excel报告 + 错误详情]
```

**流程说明**：
- **Step 1**：上传GDPR法规（支持30+种格式：PDF/Word/HTML/ZIP等）
- **Step 2**：AI大模型分析法规内容，从规则池智能匹配相关规则
- **Step 3**：展示AI推荐规则（含匹配原因+法规条款引用），用户确认
- **Step 4**：上传数据集（CSV/Excel/JSON），执行审计，生成报告

---

# 第2页：关键算法与数据结构

## 一、核心算法

### 1. AI智能匹配算法（AIMatcher）

```python
# 算法流程
def match_rules(regulation_content, all_rules):
    # ① 构建Prompt：法规内容 + 规则池描述
    prompt = f"""
    分析法规文件，识别数据类型，匹配审计规则。
    返回JSON: {{"matches": [
        {{"rule_id": 1, "reason": "原因", "regulation_ref": "条款"}}
    ]}}

    规则池: {rules_desc}
    法规内容: {regulation_content[:3000]}
    """

    # ② 调用OpenAI API（支持Qwen/GPT系列）
    response = client.chat.completions.create(
        model="Qwen/Qwen3-4B",
        messages=[{"role": "system", "content": "数据合规审计专家"},
                  {"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        extra_body={"enable_thinking": False}  # Qwen3专用
    )

    # ③ 解析返回的规则ID + 匹配原因 + 法规引用
    return {"rule_ids": [...], "matches": [...]}
```

**优势**：
- 自动理解法规语义，无需人工配置映射关系
- 返回可解释的匹配原因，提升用户信任度
- 失败时自动降级：返回所有规则（保证系统可用性）

### 2. 规则验证算法（AuditEngine）

```python
# 支持12种验证类型
def _validate_record(record, rule, row_number):
    if rule.rule_type == 'email':
        # 邮箱正则：^\w+@[a-zA-Z0-9]+\.[a-zA-Z]{2,}$
        return _validate_email(record, rule)

    elif rule.rule_type == 'phone':
        # 手机号正则：1[3-9]\d{9}
        return _validate_phone(record, rule)

    elif rule.rule_type == 'idcard':
        # 身份证算法：17位数字 + 校验位（X或数字）
        # 校验算法：GB11643-1999标准
        return _validate_idcard(record, rule)

    elif rule.rule_type == 'custom':
        # 自定义规则：支持JSON表达式
        # - field_required（必填）
        # - regex_match（正则）
        # - enum_validation（枚举）
        # - length_limit（长度）
        # - numeric_range（数值范围）
        # - date_validation（日期）
        # - uniqueness_check（唯一性）
        # - field_dependency（字段依赖）
        return _validate_custom(record, rule, rule_config)
```

**特色功能**：
- **上下文验证**：跨记录唯一性检查、字段依赖关系
- **精确定位**：记录错误的行号、列名、起止位置（前端波浪线标注）
- **统计分析**：每条规则的命中率、错误分布

### 3. 内容检测算法（ContentDetector）

```python
# 6大类40+种敏感数据检测
DETECTION_PATTERNS = {
    "个人数据PII": {
        "身份证": r'\d{17}[\dXx]',           # 高风险
        "手机号": r'1[3-9]\d{9}',            # 中风险
        "邮箱": r'\w+@[\w.]+\.\w{2,}',       # 中风险
    },
    "特殊类别": {
        "健康数据": ["病历","诊断","HIV","癌症"],  # 严重
        "生物识别": ["指纹","虹膜","人脸","DNA"]   # 严重
    },
    "安全敏感": {
        "密码": r'password\s*[:=]\s*\S+',     # 严重（脱敏）
        "API密钥": r'(api[_-]?key|apikey)\s*[:=]\s*[\w-]+' # 严重
    }
}

# 输出：检测类型 + 风险等级 + 位置 + 置信度 + 处置建议
```

**防护机制**：
- 密码/密钥自动脱敏，不记录明文
- 防Zip Bomb：大小/文件数/递归深度三重限制

## 二、关键数据结构

### 1. 审计任务模型（AuditTask）

```python
class AuditTask:
    # 基本信息
    task_name: str              # 任务名称
    task_status: str            # 状态：pending → processing → completed

    # 步骤1：法规
    regulation_id: int          # 引用法规ID（可选）
    regulation_file_path: str   # 上传的法规文件路径

    # 步骤2：规则匹配
    matched_rules: dict         # AI匹配的规则：
                                # {"rule_ids": [1,2], "matches": [
                                #   {"rule_id": 1, "reason": "...",
                                #    "regulation_ref": "第X条"}
                                # ]}
    selected_rules: dict        # 用户最终选择的规则ID列表

    # 步骤3：审计结果
    dataset_file_path: str      # 数据集文件路径
    total_records: int          # 总记录数
    error_records: int          # 错误记录数
    audit_report_path: str      # Excel报告路径
```

### 2. 审计错误模型（AuditError）

```python
class AuditError:
    task_id: int                # 关联任务
    error_type: str             # 类型：data/label

    # 位置信息（前端精确定位）
    row_number: int             # 行号
    column_name: str            # 列名
    start_position: int         # 错误开始位置
    end_position: int           # 错误结束位置

    # 错误详情
    original_value: str         # 原始值
    error_message: str          # 错误信息
    rule_id: int                # 违反的规则
    severity: str               # 严重等级：error/warning/info
```

### 3. 规则模板系统（二层结构）

```
规则模板层 (Template)
    ↓ 实例化
规则实例层 (Rule Instance)
    ↓ 应用
审计任务
```

**10个内置模板**：
1. `FIELD_REQUIRED` - 字段必填验证
2. `FIELD_FORMAT_REGEX` - 格式正则验证
3. `FIELD_ENUM_VALUES` - 枚举值限制
4. `FIELD_LENGTH_LIMIT` - 长度限制
5. `FIELD_NUMERIC_RANGE` - 数值范围
6. `FIELD_DATE_VALIDATION` - 日期验证
7. `FIELD_NO_PII_KEYWORDS` - 不含敏感词
8. `FIELD_DEPENDENCY_CHECK` - 字段依赖
9. `FIELD_UNIQUE_CHECK` - 唯一性验证
10. `FIELD_CROSS_DATASET_REFERENCE` - 跨数据集引用

---

# 第3页：案例演示与技术亮点

## 一、实际案例：GDPR合规审计

### 案例场景
某公司需要审计用户数据集（`users.csv`），确保符合GDPR第6条（合法基础）和第9条（特殊类别数据）要求。

### 操作流程

**Step 1：上传GDPR法规文件**
```
输入：GDPR_Article_6_9.pdf（欧盟GDPR法规第6-9条）
输出：FileParser解析为3000字符文本
```

**Step 2：AI智能匹配**
```
输入：法规内容 + 10条规则池
AI分析：识别关键词"个人数据"、"合法基础"、"特殊类别"
输出：推荐5条规则
  ✓ 规则1：邮箱格式验证
    匹配原因："法规要求验证邮箱有效性"
    法规引用："第6条第1款"
  ✓ 规则2：手机号格式验证
    匹配原因："个人数据需符合格式标准"
    法规引用："第6条第1款"
  ✓ 规则3：敏感健康数据检测
    匹配原因："特殊类别数据需明确标识"
    法规引用："第9条第1款"
```

**Step 3：用户确认规则**
```
用户界面展示：
[AI推荐] 规则1：邮箱格式验证
  📄 匹配原因：法规要求验证邮箱有效性
  📖 法规条款：第6条第1款
  [✓] 确认使用

用户选择：保留5条规则
```

**Step 4：审计数据集**
```
输入：users.csv（1000行，包含姓名/邮箱/手机/健康状态）

审计结果：
- 总记录数：1000
- 错误记录数：127
- 错误详情：
  • 第23行，邮箱列：无效格式"test@"（规则1违反）
  • 第45行，手机列：号段错误"12345678901"（规则2违反）
  • 第67行，健康状态列：包含"HIV"敏感词（规则3违反）

生成报告：audit_report_20261103_143022.xlsx
```

### 审计报告示例

| 行号 | 列名 | 原始值 | 错误信息 | 规则 | 严重等级 |
|------|------|--------|----------|------|----------|
| 23 | email | test@ | 邮箱格式不符合标准 | 邮箱格式验证 | error |
| 45 | phone | 12345678901 | 手机号段不正确 | 手机号验证 | error |
| 67 | health_status | HIV阳性 | 特殊类别数据需脱敏 | 敏感数据检测 | warning |

**统计数据**：
- 邮箱格式错误：34条（3.4%）
- 手机号格式错误：58条（5.8%）
- 敏感数据检测：35条（3.5%）

---

## 二、技术亮点

### 1. 文件格式全覆盖（30+种）
```
文档类：txt, md, log, doc, docx, pdf, rtf
数据类：csv, json, xml, yaml, ini, toml
表格类：xls, xlsx
演示类：ppt, pptx
图片类：png, jpg, bmp, tiff（支持OCR）
压缩类：zip, rar, 7z, tar, gz（递归解压）
网页类：html, htm
```

**技术实现**：
- PDF智能识别：区分文本型/扫描型，标记需OCR
- 压缩包递归：防Zip Bomb攻击（大小/文件数/深度限制）
- 编码兼容：自动识别UTF-8/GBK/GB2312

### 2. AI驱动的可解释性
```
传统方式：人工配置规则与法规的映射关系
本系统 ：AI自动分析法规内容，生成匹配理由
```

**用户价值**：
- 前端显示"为什么推荐这条规则"
- 法规条款引用（如"第6条第1款"）
- 降低用户学习成本，提升信任度

### 3. 规则模板 + 实例化架构
```
手动创建10条规则 → 繁琐
AI自动实例化  → 一次法规解析生成数十条规则
```

**工作流**：
```
用户上传法规
    ↓
AI识别：需要验证"邮箱"、"手机号"
    ↓
从模板 FIELD_FORMAT_REGEX 实例化2条规则
    ↓
自动添加到规则池
```

### 4. 精确错误定位（前端波浪线）
```javascript
// 错误数据结构包含位置信息
{
  row_number: 23,
  column_name: "email",
  original_value: "test@invalid",
  start_position: 5,  // 错误开始位置
  end_position: 12,   // 错误结束位置
  error_message: "无效域名"
}

// 前端渲染：在"invalid"下方显示红色波浪线
```

### 5. 多层安全防护
- **密码脱敏**：检测到密码时不记录明文，显示 `***REDACTED***`
- **防Zip Bomb**：限制压缩包大小（500MB）、文件数（1万个）、递归深度（5层）
- **超时保护**：大文件审计设置超时（默认2分钟）

---

## 三、系统性能

| 操作 | 数据规模 | 耗时 |
|------|---------|------|
| 文件解析（CSV） | 10MB / 5万行 | 3-5秒 |
| AI规则匹配 | 3000字法规 + 10条规则 | 2-4秒 |
| 数据审计 | 5万行 × 5条规则 | 8-12秒 |
| 报告生成（Excel） | 1000条错误 | 1-2秒 |

**总体流程**（5万行数据集）：**15-23秒**

---

## 四、技术栈总结

| 层次 | 技术选型 |
|------|---------|
| 前端 | Vue3 + TypeScript + Element Plus |
| 后端 | FastAPI + Python 3.8+ |
| AI模型 | OpenAI API（兼容 Qwen/GPT/ModelScope） |
| 数据库 | SQLAlchemy ORM（支持MySQL/PostgreSQL） |
| 文件解析 | pandas, openpyxl, python-docx, pdfplumber |
| 数据检测 | 正则表达式 + 关键词匹配 + AI语义分析 |

---

## 联系信息

项目路径：`backend/app/plugin/module_application/audit`
详细文档：`audit/README.md`、`audit/GDPR_AUDIT_SYSTEM.md`
技术支持：见项目文档

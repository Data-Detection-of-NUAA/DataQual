# 规则模板与法规解析系统

## 📖 系统概述

本系统实现了**规则模板 + 法规解析 + 自动生成**的完整工作流，让用户可以：

1. 上传法规文件或输入法规要求
2. AI自动解析法规，提取审计要求
3. 将要求映射到通用规则模板
4. 自动实例化生成具体的审计规则
5. 在数据审计任务中使用这些规则

## 🎯 核心概念

### 规则模板（Rule Template）

**规则模板**是可参数化的通用规则，定义了一类验证逻辑。

**示例**：
- 模板：`FIELD_REQUIRED`（字段必填验证）
- 参数：`field_name`, `field_display_name`, `error_message`
- 用途：可以实例化为"邮箱必填"、"手机号必填"等具体规则

### 规则实例（Rule Instance）

**规则实例**是从模板实例化出的具体规则，包含实际的参数值。

**示例**：
- 从模板 `FIELD_REQUIRED` 实例化
- 参数：`{"field_name": "email", "field_display_name": "用户邮箱"}`
- 结果：一条具体的"用户邮箱必填"规则

### 法规解析（Regulation Parsing）

**法规解析**是使用AI从法规文本中提取审计要求的过程。

**流程**：
```
法规文本
  → AI解析
  → 提取要求
  → 匹配模板
  → 生成参数
  → 实例化规则
```

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端/API层                            │
├─────────────────────────────────────────────────────────────┤
│  规则模板管理   │  法规解析   │  规则生成   │  审计执行    │
├─────────────────────────────────────────────────────────────┤
│                        业务逻辑层                            │
├──────────────────┬──────────────────┬──────────────────────┤
│ RegulationParser │ RuleInstantiator │   AuditEngine        │
│  (法规解析器)     │  (规则实例化器)   │   (审计引擎)          │
├──────────────────┴──────────────────┴──────────────────────┤
│                        数据模型层                            │
├─────────────────────────────────────────────────────────────┤
│ AuditRuleTemplate │ AuditRule │ AuditRegulation │ AuditTask │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 文件结构

```
backend/app/plugin/module_application/audit/
├── rule_template/                      # 规则模板模块
│   ├── model.py                        # 数据模型：AuditRuleTemplate
│   ├── schema.py                       # Pydantic Schema
│   ├── crud.py                         # 数据库操作
│   ├── service.py                      # 业务逻辑
│   ├── controller.py                   # API路由
│   ├── default_templates.py            # 默认模板定义（10个）
│   ├── seeder.py                       # 数据初始化
│   └── __init__.py
│
├── engine/                             # 审计引擎
│   ├── regulation_parser.py            # 法规解析器（AI）
│   ├── rule_instantiator.py            # 规则实例化引擎
│   ├── audit_engine.py                 # 审计引擎（已更新）
│   ├── content_extractor.py            # 文件内容提取器
│   └── ...
│
├── regulation/
│   ├── parse_controller.py             # 法规解析API
│   └── ...
│
├── rule/
│   ├── model.py                        # 更新：添加模板关联字段
│   ├── crud.py                         # 更新：添加get_rule_by_code
│   └── ...
│
├── RULE_TEMPLATE_SYSTEM.md             # 本文档
└── REGULATION_INPUT_GUIDE.md           # 用户输入指南
```

---

## 🔧 核心组件详解

### 1. 规则模板（AuditRuleTemplate）

**数据模型**：
```python
class AuditRuleTemplate:
    template_code: str              # 模板编码（唯一）
    template_name: str              # 模板名称
    template_category: str          # 分类
    template_description: str       # 描述
    parameters_schema: dict         # 参数定义（JSON Schema）
    validation_template: dict       # 验证逻辑配置
    default_severity: str           # 默认严重等级
    tags: dict                      # 标签
    is_active: int                  # 是否启用
```

**默认模板**（10个）：
1. `FIELD_REQUIRED` - 字段必填验证
2. `FIELD_FORMAT_REGEX` - 字段格式正则验证
3. `FIELD_ENUM_VALUES` - 字段枚举值限制
4. `FIELD_LENGTH_LIMIT` - 字段长度限制
5. `FIELD_NUMERIC_RANGE` - 数值范围验证
6. `FIELD_DATE_VALIDATION` - 日期字段验证
7. `FIELD_NO_PII_KEYWORDS` - 字段不含敏感词
8. `FIELD_DEPENDENCY_CHECK` - 字段依赖关系验证
9. `FIELD_UNIQUE_CHECK` - 字段唯一性验证
10. `FIELD_CROSS_DATASET_REFERENCE` - 跨数据集引用验证

### 2. 法规解析器（RegulationParser）

**核心方法**：

```python
# 自动解析法规文本
async def parse_regulation(
    regulation_content: str,
    available_templates: List
) -> List[Dict]:
    """使用AI解析法规，返回审计要求列表"""

# 解析结构化输入
async def parse_structured_regulation(
    regulation_dict: Dict,
    available_templates: List
) -> List[Dict]:
    """解析用户手动填写的结构化数据"""
```

**AI Prompt设计**：
- 输入：法规文本 + 规则模板池
- 输出：结构化的审计要求（JSON）
- 包含：模板ID、实例化参数、置信度、规则信息等

### 3. 规则实例化器（RuleInstantiator）

**核心方法**：

```python
def instantiate_rule(
    template: AuditRuleTemplate,
    instance_parameters: Dict,
    rule_code: str,
    rule_name: str,
    ...
) -> Dict:
    """从模板实例化一个具体规则"""

def batch_instantiate_rules(
    parsed_requirements: List[Dict],
    templates_map: Dict,
    regulation_id: int
) -> List[Dict]:
    """批量实例化规则"""
```

**实例化逻辑**：
- 根据模板类型生成 `rule_type` 和 `rule_expression`
- 智能推断：如field_name包含"email"，自动使用email类型
- 生成JSON配置：包含validation_type和所有参数

### 4. 审计引擎（AuditEngine）

**更新内容**：

新增9个验证方法，支持模板实例化的规则：
- `_validate_field_required` - 必填验证
- `_validate_regex_match` - 正则匹配
- `_validate_enum_validation` - 枚举验证
- `_validate_length_limit` - 长度限制
- `_validate_numeric_range` - 数值范围
- `_validate_date_validation` - 日期验证
- `_validate_no_pii_keywords` - 敏感词检测
- `_validate_field_dependency` - 依赖关系
- `_validate_uniqueness_check` - 唯一性检查

**兼容性**：
- 支持新的 `validation_type` 字段
- 保持对旧的 `custom_type` 字段的兼容

---

## 🚀 使用流程

### 流程A：完全自动化

```
1. 上传法规文件
   ↓
2. 调用 /audit/regulation/{id}/parse-and-generate
   ↓
3. AI自动解析 + 生成规则
   ↓
4. 规则可用于审计任务
```

**API调用**：
```bash
POST /audit/regulation/123/parse-and-generate
{
  "parse_mode": "auto"
}
```

### 流程B：分步操作

```
1. 上传法规文件
   ↓
2. 解析法规：/audit/regulation/{id}/parse
   ↓
3. 查看解析结果，确认或调整
   ↓
4. 生成规则：/audit/regulation/{id}/generate-rules
   ↓
5. 规则可用于审计任务
```

### 流程C：结构化输入

```
1. 准备结构化JSON数据（见REGULATION_INPUT_GUIDE.md）
   ↓
2. 调用解析API，传入structured_input
   ↓
3. 生成规则
```

**API调用**：
```bash
POST /audit/regulation/123/parse
{
  "parse_mode": "manual",
  "structured_input": {
    "regulation_name": "...",
    "requirements": [...]
  }
}
```

---

## 📡 API接口

### 规则模板管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/audit/rule-template/list` | 获取模板列表 |
| GET | `/audit/rule-template/all` | 获取所有启用模板 |
| GET | `/audit/rule-template/options` | 获取模板选项（下拉框） |
| GET | `/audit/rule-template/detail/{id}` | 获取模板详情 |
| POST | `/audit/rule-template/create` | 创建模板 |
| PUT | `/audit/rule-template/update` | 更新模板 |
| DELETE | `/audit/rule-template/delete/{id}` | 删除模板 |

### 法规解析与规则生成

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/audit/regulation/{id}/parse` | 解析法规，返回审计要求 |
| POST | `/audit/regulation/{id}/generate-rules` | 根据解析结果生成规则 |
| POST | `/audit/regulation/{id}/parse-and-generate` | 一键解析并生成规则 |

---

## 💾 数据库变更

### 新增表：audit_rule_template

```sql
CREATE TABLE audit_rule_template (
    id INT PRIMARY KEY AUTO_INCREMENT,
    template_code VARCHAR(100) NOT NULL UNIQUE,
    template_name VARCHAR(200) NOT NULL,
    template_category VARCHAR(50) NOT NULL,
    template_description TEXT,
    parameters_schema JSON NOT NULL,
    validation_template JSON NOT NULL,
    default_severity VARCHAR(20) DEFAULT 'warning',
    tags JSON,
    is_active INT DEFAULT 1,
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 修改表：audit_rule

新增字段：
```sql
ALTER TABLE audit_rule ADD COLUMN template_id INT;
ALTER TABLE audit_rule ADD COLUMN instance_parameters JSON;
ALTER TABLE audit_rule ADD COLUMN regulation_id INT;
ALTER TABLE audit_rule ADD COLUMN auto_generated INT DEFAULT 0;
```

---

## 🎨 实例化示例

### 示例1：必填字段

**模板**：FIELD_REQUIRED

**输入参数**：
```json
{
  "field_name": "email",
  "field_display_name": "用户邮箱",
  "error_message": "用户邮箱不能为空"
}
```

**生成的规则**：
```json
{
  "rule_code": "REG-EMAIL-REQUIRED",
  "rule_name": "用户邮箱必填",
  "rule_type": "custom",
  "rule_expression": {
    "validation_type": "field_required",
    "field_name": "email",
    "error_message": "用户邮箱不能为空"
  },
  "severity": "error",
  "template_id": 1,
  "instance_parameters": {...},
  "auto_generated": 1
}
```

### 示例2：枚举验证

**模板**：FIELD_ENUM_VALUES

**输入参数**：
```json
{
  "field_name": "consent_flag",
  "field_display_name": "用户同意标识",
  "allowed_values": ["Y", "N"],
  "case_sensitive": true
}
```

**生成的规则**：
```json
{
  "rule_code": "REG-CONSENT_FLAG-ENUM",
  "rule_name": "用户同意标识 - 枚举",
  "rule_type": "custom",
  "rule_expression": {
    "validation_type": "enum_validation",
    "field_name": "consent_flag",
    "allowed_values": ["Y", "N"],
    "case_sensitive": true
  },
  "severity": "error"
}
```

### 示例3：格式验证（智能推断）

**模板**：FIELD_FORMAT_REGEX

**输入参数**：
```json
{
  "field_name": "email",
  "field_display_name": "用户邮箱",
  "regex_pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
  "format_description": "有效的邮箱地址"
}
```

**生成的规则**：
```json
{
  "rule_code": "REG-EMAIL-FORMAT",
  "rule_name": "用户邮箱格式验证",
  "rule_type": "email",  // ← 智能推断为email类型
  "rule_expression": null,  // 使用内置验证
  "severity": "error"
}
```

---

## 🔐 权限要求

建议在 `module_system` 的权限系统中添加以下权限：

```python
permissions = [
    "module_application:audit:rule_template:query",     # 查询模板
    "module_application:audit:rule_template:create",    # 创建模板
    "module_application:audit:rule_template:update",    # 更新模板
    "module_application:audit:rule_template:delete",    # 删除模板
    "module_application:audit:regulation:parse",        # 解析法规
    "module_application:audit:regulation:generate_rules", # 生成规则
]
```

---

## 🧪 测试步骤

### 1. 初始化规则模板

```python
# 在应用启动时或通过管理命令执行
from app.plugin.module_application.audit.rule_template.seeder import seed_default_templates

# 初始化10个默认模板
await seed_default_templates(db)
```

### 2. 测试法规解析（自动模式）

```bash
# 1. 上传法规文件
POST /audit/regulation/upload
Content-Type: multipart/form-data
file: gdpr_regulation.pdf

# 2. 解析法规
POST /audit/regulation/1/parse
{
  "parse_mode": "auto"
}

# 响应示例
{
  "success": true,
  "requirements_count": 5,
  "requirements": [
    {
      "template_id": 1,
      "template_code": "FIELD_REQUIRED",
      "instance_parameters": {
        "field_name": "email",
        "field_display_name": "用户邮箱"
      },
      "rule_code": "REG-EMAIL-REQUIRED",
      "confidence": 0.95,
      ...
    }
  ]
}
```

### 3. 测试规则生成

```bash
POST /audit/regulation/1/generate-rules
{
  "parsed_requirements": [...],  # 从解析结果复制
  "auto_activate": true
}

# 响应
{
  "success": true,
  "generated_count": 5,
  "failed_count": 0,
  "rule_ids": [10, 11, 12, 13, 14]
}
```

### 4. 测试规则应用

```bash
# 创建审计任务并选择生成的规则
POST /audit/task/{id}/confirm-rules
{
  "selected_rules": [10, 11, 12, 13, 14]
}

# 上传数据集并执行审计
POST /audit/task/{id}/upload-dataset
POST /audit/task/{id}/execute
```

---

## 🐛 常见问题

### Q1: AI解析不准确怎么办？

**解决方案**：
1. 使用结构化输入模式（100%准确）
2. 在解析后手动调整结果
3. 优化法规文本格式（清晰的条款结构）

### Q2: 如何添加新的规则模板？

**步骤**：
1. 在 `default_templates.py` 中定义模板
2. 在 `RuleInstantiator` 中添加实例化逻辑
3. 在 `AuditEngine` 中添加验证方法
4. 运行 `seed_default_templates` 初始化

### Q3: 生成的规则编码重复怎么办？

**解决方案**：
- 系统会自动检测重复并跳过
- 可以在解析时调整 `rule_code` 参数
- 使用更具描述性的编码格式

### Q4: 如何删除模板？

**注意**：
- 删除模板前应检查是否有规则使用
- 建议使用"禁用"而不是"删除"
- 可以实现级联删除或标记为不可用

---

## 📈 扩展建议

### 1. 模板市场

创建模板市场，允许用户分享和下载模板：
- 行业专用模板（金融、医疗、教育等）
- 法规专用模板（GDPR、HIPAA、CCPA等）
- 社区贡献模板

### 2. 智能推荐

基于历史数据推荐模板：
- 分析常用字段名
- 学习用户偏好
- 自动建议模板组合

### 3. 可视化编辑器

提供图形化界面创建和编辑模板：
- 拖拽式参数配置
- 实时预览验证逻辑
- 测试数据验证

### 4. 多语言支持

支持多种语言的法规解析：
- 英文、中文、日文等
- 自动翻译参数
- 本地化错误消息

---

## 📚 相关文档

- [法规输入指南](./REGULATION_INPUT_GUIDE.md) - 用户如何输入法规
- [GDPR审计系统](./GDPR_AUDIT_SYSTEM.md) - 整体系统设计
- [集成完成报告](./INTEGRATION_COMPLETE.md) - 系统集成文档

---

## ✅ 功能清单

- [x] 规则模板数据模型
- [x] 10个默认规则模板
- [x] AI法规解析器
- [x] 规则实例化引擎
- [x] 规则模板CRUD
- [x] 法规解析API
- [x] 规则生成API
- [x] AuditEngine验证方法
- [x] 结构化输入支持
- [x] 用户输入指南
- [x] 系统文档

---

## 🤝 贡献

欢迎提交Issue和Pull Request来改进本系统。

---

最后更新：2026-03-11
版本：1.0.0

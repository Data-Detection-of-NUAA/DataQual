# 法规输入指南

本指南帮助你正确输入法规内容，以便AI能够准确解析并生成审计规则。

## 📋 输入方式

系统支持两种输入方式：

### 1. 自动解析模式（推荐）

直接上传或粘贴法规文本，AI会自动识别和提取审计要求。

**适用场景**：
- 已有完整的法规文档（PDF、Word、TXT等）
- 法规内容结构清晰，包含明确的数据要求

**优点**：
- 无需手动整理
- 快速便捷
- 支持多种文件格式

### 2. 结构化输入模式

按照统一的格式手动填写审计要求，确保解析准确率。

**适用场景**：
- 法规内容分散或不规范
- 需要精确控制每条规则
- 法规文档不可用，只有口头要求

**优点**：
- 100%准确率
- 完全可控
- 适合定制化需求

---

## 📝 结构化输入模板

如果选择结构化输入模式，请按照以下JSON格式填写：

```json
{
  "regulation_name": "GDPR用户数据保护条例",
  "description": "欧盟通用数据保护条例对用户数据的管理要求",
  "requirements": [
    {
      "field_name": "email",
      "field_display_name": "用户邮箱",
      "rule_type": "必填",
      "validation_condition": "不能为空",
      "severity": "error"
    },
    {
      "field_name": "phone",
      "field_display_name": "手机号",
      "rule_type": "格式验证",
      "validation_condition": "必须是11位数字，1开头",
      "regex_pattern": "^1[3-9]\\d{9}$",
      "format_description": "中国大陆手机号格式",
      "severity": "error"
    },
    {
      "field_name": "consent_flag",
      "field_display_name": "用户同意标识",
      "rule_type": "枚举",
      "validation_condition": "只能是Y或N",
      "allowed_values": ["Y", "N"],
      "severity": "error"
    },
    {
      "field_name": "age",
      "field_display_name": "用户年龄",
      "rule_type": "数值范围",
      "validation_condition": "必须在0-150之间",
      "min_value": 0,
      "max_value": 150,
      "severity": "warning"
    }
  ]
}
```

---

## 🔧 字段说明

### 基本信息

| 字段 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `regulation_name` | ✅ | 法规名称 | "GDPR用户数据保护条例" |
| `description` | ❌ | 法规描述 | "欧盟通用数据保护条例..." |
| `requirements` | ✅ | 审计要求列表 | 见下方 |

### 审计要求字段（requirements数组中的每个对象）

#### 通用字段（所有规则类型都需要）

| 字段 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `field_name` | ✅ | 字段名称（数据库列名或JSON键名） | "email", "phone" |
| `field_display_name` | ✅ | 字段显示名称（用于错误消息） | "用户邮箱", "手机号" |
| `rule_type` | ✅ | 规则类型（见下方类型列表） | "必填", "格式验证" |
| `validation_condition` | ✅ | 验证条件描述 | "不能为空", "必须是有效邮箱" |
| `severity` | ❌ | 严重等级（默认warning） | "error", "warning", "info" |

#### 规则类型及其特定字段

##### 1. 必填（FIELD_REQUIRED）

验证字段不能为空。

```json
{
  "field_name": "email",
  "field_display_name": "用户邮箱",
  "rule_type": "必填",
  "validation_condition": "不能为空",
  "severity": "error"
}
```

##### 2. 格式验证（FIELD_FORMAT_REGEX）

使用正则表达式验证字段格式。

```json
{
  "field_name": "email",
  "field_display_name": "用户邮箱",
  "rule_type": "格式验证",
  "validation_condition": "必须是有效的邮箱格式",
  "regex_pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
  "format_description": "有效的邮箱地址",
  "severity": "error"
}
```

**特定字段**：
- `regex_pattern`（必填）：正则表达式
- `format_description`（可选）：格式描述

**常用正则表达式**：
- 邮箱：`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- 手机号：`^1[3-9]\d{9}$`
- 身份证：`^\d{17}[\dXx]$`

##### 3. 枚举（FIELD_ENUM_VALUES）

验证字段值必须在指定列表中。

```json
{
  "field_name": "consent_flag",
  "field_display_name": "用户同意标识",
  "rule_type": "枚举",
  "validation_condition": "只能是Y或N",
  "allowed_values": ["Y", "N"],
  "case_sensitive": true,
  "severity": "error"
}
```

**特定字段**：
- `allowed_values`（必填）：允许的值列表
- `case_sensitive`（可选）：是否区分大小写，默认true

##### 4. 长度限制（FIELD_LENGTH_LIMIT）

验证字段长度。

```json
{
  "field_name": "username",
  "field_display_name": "用户名",
  "rule_type": "长度限制",
  "validation_condition": "长度在3-20个字符之间",
  "min_length": 3,
  "max_length": 20,
  "severity": "warning"
}
```

**特定字段**：
- `min_length`（可选）：最小长度
- `max_length`（可选）：最大长度

##### 5. 数值范围（FIELD_NUMERIC_RANGE）

验证数值字段的范围。

```json
{
  "field_name": "age",
  "field_display_name": "年龄",
  "rule_type": "数值范围",
  "validation_condition": "必须在0-150之间",
  "min_value": 0,
  "max_value": 150,
  "allow_decimal": false,
  "severity": "warning"
}
```

**特定字段**：
- `min_value`（可选）：最小值
- `max_value`（可选）：最大值
- `allow_decimal`（可选）：是否允许小数，默认false

##### 6. 日期验证（FIELD_DATE_VALIDATION）

验证日期字段格式。

```json
{
  "field_name": "birth_date",
  "field_display_name": "出生日期",
  "rule_type": "日期",
  "validation_condition": "必须是YYYY-MM-DD格式",
  "date_format": "YYYY-MM-DD",
  "severity": "error"
}
```

**特定字段**：
- `date_format`（可选）：日期格式，默认YYYY-MM-DD
  - 支持：YYYY-MM-DD, YYYY/MM/DD, DD-MM-YYYY, DD/MM/YYYY

##### 7. 唯一性验证（FIELD_UNIQUE_CHECK）

验证字段值在数据集中唯一。

```json
{
  "field_name": "user_id",
  "field_display_name": "用户ID",
  "rule_type": "唯一性",
  "validation_condition": "不能重复",
  "ignore_empty": true,
  "severity": "error"
}
```

**特定字段**：
- `ignore_empty`（可选）：是否忽略空值，默认true

##### 8. 依赖关系验证（FIELD_DEPENDENCY_CHECK）

验证字段间的依赖关系。

```json
{
  "source_field": "lawful_basis",
  "source_field_display": "合法性基础",
  "dependent_field": "consent_flag",
  "dependent_field_display": "同意标识",
  "rule_type": "依赖关系",
  "validation_condition": "当合法性基础有值时，同意标识也必须有值",
  "condition": "not_empty",
  "severity": "error"
}
```

**特定字段**：
- `source_field`（必填）：源字段名称
- `source_field_display`（必填）：源字段显示名称
- `dependent_field`（必填）：依赖字段名称
- `dependent_field_display`（必填）：依赖字段显示名称
- `condition`（可选）：触发条件，默认not_empty
  - `not_empty`：源字段不为空
  - `equals`：源字段等于指定值
  - `contains`：源字段包含指定值
- `condition_value`（可选）：条件值（condition为equals或contains时）

##### 9. 不含敏感词（FIELD_NO_PII_KEYWORDS）

验证字段不包含敏感关键词。

```json
{
  "field_name": "comments",
  "field_display_name": "备注",
  "rule_type": "不含敏感词",
  "validation_condition": "不能包含密码、身份证等敏感信息",
  "blocked_keywords": ["密码", "password", "身份证", "idcard"],
  "case_sensitive": false,
  "severity": "warning"
}
```

**特定字段**：
- `blocked_keywords`（必填）：禁止的关键词列表
- `case_sensitive`（可选）：是否区分大小写，默认false

---

## 💡 最佳实践

### 1. 字段命名规范

**推荐**：
- 使用英文字段名：`email`, `phone`, `user_id`
- 使用下划线分隔：`consent_flag`, `birth_date`
- 保持一致性：统一使用驼峰或下划线

**不推荐**：
- 中文字段名：`用户邮箱`（除非数据库确实如此）
- 混合命名：`userEmail` 和 `user_id` 混用

### 2. 显示名称要清晰

```json
{
  "field_name": "email",
  "field_display_name": "用户邮箱",  // ✅ 清晰易懂
  // 而不是：
  "field_display_name": "email"      // ❌ 对用户不友好
}
```

### 3. 合理设置严重等级

- `error`：强制要求，不符合则审计失败（如：必填字段、关键格式）
- `warning`：建议遵守，但不强制（如：长度建议、数据质量）
- `info`：提示性信息，仅供参考

### 4. 正则表达式要转义

在JSON中，反斜杠需要双重转义：

```json
{
  "regex_pattern": "^\\d{11}$"  // ✅ 正确
  // 而不是：
  "regex_pattern": "^\d{11}$"   // ❌ 错误，\d会被解析错误
}
```

### 5. 枚举值要完整

```json
{
  "allowed_values": ["Y", "N", "UNKNOWN"]  // ✅ 包含所有可能的值
  // 而不是：
  "allowed_values": ["Y", "N"]              // ❌ 遗漏了UNKNOWN
}
```

---

## 📖 完整示例

以下是一个完整的GDPR合规法规输入示例：

```json
{
  "regulation_name": "GDPR用户数据保护条例",
  "description": "欧盟通用数据保护条例对个人数据收集和处理的要求",
  "requirements": [
    {
      "field_name": "email",
      "field_display_name": "用户邮箱",
      "rule_type": "必填",
      "validation_condition": "用户邮箱为必填项，用于联系和告知",
      "severity": "error"
    },
    {
      "field_name": "email",
      "field_display_name": "用户邮箱",
      "rule_type": "格式验证",
      "validation_condition": "必须是有效的邮箱格式",
      "regex_pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
      "format_description": "有效的邮箱地址",
      "severity": "error"
    },
    {
      "field_name": "phone",
      "field_display_name": "手机号",
      "rule_type": "格式验证",
      "validation_condition": "必须是11位中国大陆手机号",
      "regex_pattern": "^1[3-9]\\d{9}$",
      "format_description": "11位中国大陆手机号",
      "severity": "warning"
    },
    {
      "field_name": "consent_flag",
      "field_display_name": "用户同意标识",
      "rule_type": "枚举",
      "validation_condition": "必须显式标识用户是否同意",
      "allowed_values": ["Y", "N"],
      "case_sensitive": true,
      "severity": "error"
    },
    {
      "field_name": "age",
      "field_display_name": "年龄",
      "rule_type": "数值范围",
      "validation_condition": "年龄必须在0-150之间",
      "min_value": 0,
      "max_value": 150,
      "allow_decimal": false,
      "severity": "warning"
    },
    {
      "field_name": "user_id",
      "field_display_name": "用户ID",
      "rule_type": "唯一性",
      "validation_condition": "用户ID不能重复",
      "ignore_empty": true,
      "severity": "error"
    }
  ]
}
```

---

## 🚀 使用流程

### 方式A：自动解析

1. 上传或选择已有的法规文件
2. 点击"解析法规"按钮
3. 系统自动提取审计要求
4. 确认或调整解析结果
5. 生成审计规则

### 方式B：结构化输入

1. 选择"结构化输入"模式
2. 按照模板填写JSON数据
3. 点击"解析法规"按钮
4. 系统根据输入生成审计要求
5. 生成审计规则

---

## ❓ 常见问题

### Q1: 同一个字段可以应用多个规则吗？

**A**: 可以！例如email字段可以同时有"必填"和"格式验证"两条规则。

### Q2: 如果字段名不确定怎么办？

**A**: 使用自动解析模式，AI会尝试推断字段名。或者先创建规则，后续可以修改。

### Q3: 支持自定义验证逻辑吗？

**A**: 对于复杂逻辑，可以联系管理员添加新的规则模板，或使用正则表达式实现大部分验证需求。

### Q4: 解析结果不准确怎么办？

**A**: 可以在解析后手动调整，或改用结构化输入模式获得100%准确率。

---

## 📞 技术支持

如有疑问或需要帮助，请联系系统管理员。

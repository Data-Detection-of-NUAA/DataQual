# 部署指南：规则模板与法规解析系统

## 📋 部署步骤

### 步骤1: 执行数据库迁移

使用MySQL客户端执行迁移脚本：

```bash
mysql -u your_username -p your_database < backend/migrations/add_rule_template_system.sql
```

或者在MySQL命令行中：

```sql
USE your_database;
SOURCE backend/migrations/add_rule_template_system.sql;
```

**迁移内容**：
- ✅ 创建 `audit_rule_template` 表
- ✅ 在 `audit_rule` 表中添加4个新字段
- ✅ 创建必要的索引

---

### 步骤2: 初始化规则模板

**方法A: 使用Python脚本（推荐）**

在已安装项目依赖的环境中运行：

```bash
cd backend
python init_rule_templates.py
```

**方法B: 使用API接口**

启动应用后，调用初始化接口：

```bash
POST http://localhost:8000/audit/rule-template/init
```

**方法C: 手动执行SQL**

运行以下SQL脚本初始化模板（见下方完整脚本）

---

### 步骤3: 验证安装

**1. 检查表是否创建成功**

```sql
-- 查看表结构
DESCRIBE audit_rule_template;
DESCRIBE audit_rule;

-- 查看模板数量
SELECT COUNT(*) FROM audit_rule_template;
-- 应该返回 10

-- 查看所有模板
SELECT template_code, template_name, template_category, is_active
FROM audit_rule_template
ORDER BY template_category, template_code;
```

**2. 通过API验证**

```bash
# 获取模板列表
GET http://localhost:8000/audit/rule-template/list

# 获取所有启用的模板
GET http://localhost:8000/audit/rule-template/all
```

**3. 检查日志**

启动应用，查看是否有加载错误。

---

### 步骤4: 配置AI服务（可选）

如果要使用自动解析功能，需要配置OpenAI API。

在 `.env` 或配置文件中添加：

```env
# OpenAI API配置
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# 或者使用其他兼容的API
# OPENAI_BASE_URL=https://api.deepseek.com/v1
# OPENAI_MODEL=deepseek-chat
```

**注意**：
- 不配置AI服务也可以使用结构化输入模式
- 结构化输入模式不依赖AI，准确率100%

---

## 📝 手动初始化SQL脚本

如果无法使用Python脚本，可以执行以下SQL：

```sql
-- =====================================================
-- 插入10个默认规则模板
-- =====================================================

-- 1. 字段必填验证
INSERT INTO audit_rule_template (
    template_code, template_name, template_category, template_description,
    parameters_schema, validation_template, default_severity, tags, is_active, remark
) VALUES (
    'FIELD_REQUIRED',
    '字段必填验证',
    'field_validation',
    '验证指定字段不能为空、null或仅包含空格。适用于必填字段的合规要求。',
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'field_name', JSON_OBJECT('type', 'string', 'description', '要验证的字段名称'),
            'field_display_name', JSON_OBJECT('type', 'string', 'description', '字段的显示名称'),
            'error_message', JSON_OBJECT('type', 'string', 'description', '自定义错误消息', 'default', '{field_display_name}不能为空')
        ),
        'required', JSON_ARRAY('field_name', 'field_display_name')
    ),
    JSON_OBJECT('type', 'field_required', 'logic', 'check_not_empty_and_not_null'),
    'error',
    JSON_OBJECT('category', '基础验证', 'gdpr', true, 'common', true),
    1,
    '最常用的模板，用于验证必填字段'
);

-- 2. 字段格式正则验证
INSERT INTO audit_rule_template (
    template_code, template_name, template_category, template_description,
    parameters_schema, validation_template, default_severity, tags, is_active, remark
) VALUES (
    'FIELD_FORMAT_REGEX',
    '字段格式正则验证',
    'format_check',
    '使用正则表达式验证字段格式。适用于各种格式要求（邮箱、手机号、身份证等）。',
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'field_name', JSON_OBJECT('type', 'string', 'description', '要验证的字段名称'),
            'field_display_name', JSON_OBJECT('type', 'string', 'description', '字段的显示名称'),
            'regex_pattern', JSON_OBJECT('type', 'string', 'description', '正则表达式'),
            'format_description', JSON_OBJECT('type', 'string', 'description', '格式说明')
        ),
        'required', JSON_ARRAY('field_name', 'field_display_name', 'regex_pattern', 'format_description')
    ),
    JSON_OBJECT('type', 'regex_match', 'logic', 'validate_field_against_regex'),
    'error',
    JSON_OBJECT('category', '格式验证', 'gdpr', true, 'flexible', true),
    1,
    '通用格式验证模板，支持任意正则表达式'
);

-- 3. 字段枚举值限制
INSERT INTO audit_rule_template (
    template_code, template_name, template_category, template_description,
    parameters_schema, validation_template, default_severity, tags, is_active, remark
) VALUES (
    'FIELD_ENUM_VALUES',
    '字段枚举值限制',
    'field_validation',
    '验证字段值必须在指定的枚举列表中。适用于状态、类型等有限选项的字段。',
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'field_name', JSON_OBJECT('type', 'string', 'description', '要验证的字段名称'),
            'field_display_name', JSON_OBJECT('type', 'string', 'description', '字段的显示名称'),
            'allowed_values', JSON_OBJECT('type', 'array', 'description', '允许的值列表'),
            'case_sensitive', JSON_OBJECT('type', 'boolean', 'description', '是否区分大小写', 'default', true)
        ),
        'required', JSON_ARRAY('field_name', 'field_display_name', 'allowed_values')
    ),
    JSON_OBJECT('type', 'enum_validation', 'logic', 'check_value_in_allowed_list'),
    'error',
    JSON_OBJECT('category', '业务验证', 'gdpr', true),
    1,
    '用于验证枚举字段，如同意标识、用途标签等'
);

-- 4. 字段长度限制
INSERT INTO audit_rule_template (
    template_code, template_name, template_category, template_description,
    parameters_schema, validation_template, default_severity, tags, is_active, remark
) VALUES (
    'FIELD_LENGTH_LIMIT',
    '字段长度限制',
    'field_validation',
    '验证字段长度在指定范围内。适用于姓名、地址等有长度要求的文本字段。',
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'field_name', JSON_OBJECT('type', 'string', 'description', '要验证的字段名称'),
            'field_display_name', JSON_OBJECT('type', 'string', 'description', '字段的显示名称'),
            'min_length', JSON_OBJECT('type', 'integer', 'description', '最小长度'),
            'max_length', JSON_OBJECT('type', 'integer', 'description', '最大长度')
        ),
        'required', JSON_ARRAY('field_name', 'field_display_name')
    ),
    JSON_OBJECT('type', 'length_check', 'logic', 'validate_string_length'),
    'warning',
    JSON_OBJECT('category', '数据质量', 'gdpr', false),
    1,
    '用于验证文本长度，如姓名2-50字符'
);

-- 5. 数值范围验证
INSERT INTO audit_rule_template (
    template_code, template_name, template_category, template_description,
    parameters_schema, validation_template, default_severity, tags, is_active, remark
) VALUES (
    'FIELD_NUMERIC_RANGE',
    '数值范围验证',
    'field_validation',
    '验证数值字段在指定范围内。适用于年龄、保留期限等数值型合规要求。',
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'field_name', JSON_OBJECT('type', 'string', 'description', '要验证的字段名称'),
            'field_display_name', JSON_OBJECT('type', 'string', 'description', '字段的显示名称'),
            'min_value', JSON_OBJECT('type', 'number', 'description', '最小值'),
            'max_value', JSON_OBJECT('type', 'number', 'description', '最大值'),
            'allow_decimal', JSON_OBJECT('type', 'boolean', 'description', '是否允许小数', 'default', false)
        ),
        'required', JSON_ARRAY('field_name', 'field_display_name')
    ),
    JSON_OBJECT('type', 'numeric_range', 'logic', 'validate_number_in_range'),
    'warning',
    JSON_OBJECT('category', '业务验证', 'gdpr', true),
    1,
    '用于数值范围验证，如保留期限0-24个月'
);

-- 6. 日期字段验证
INSERT INTO audit_rule_template (
    template_code, template_name, template_category, template_description,
    parameters_schema, validation_template, default_severity, tags, is_active, remark
) VALUES (
    'FIELD_DATE_VALIDATION',
    '日期字段验证',
    'format_check',
    '验证日期字段格式和有效性。适用于出生日期、同意日期等时间相关字段。',
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'field_name', JSON_OBJECT('type', 'string', 'description', '要验证的字段名称'),
            'field_display_name', JSON_OBJECT('type', 'string', 'description', '字段的显示名称'),
            'date_format', JSON_OBJECT('type', 'string', 'description', '日期格式', 'default', 'YYYY-MM-DD'),
            'min_date', JSON_OBJECT('type', 'string', 'description', '最早日期'),
            'max_date', JSON_OBJECT('type', 'string', 'description', '最晚日期')
        ),
        'required', JSON_ARRAY('field_name', 'field_display_name')
    ),
    JSON_OBJECT('type', 'date_validation', 'logic', 'validate_date_format_and_range'),
    'error',
    JSON_OBJECT('category', '格式验证', 'gdpr', true),
    1,
    '用于日期格式和范围验证'
);

-- 7. 字段不含敏感词
INSERT INTO audit_rule_template (
    template_code, template_name, template_category, template_description,
    parameters_schema, validation_template, default_severity, tags, is_active, remark
) VALUES (
    'FIELD_NO_PII_KEYWORDS',
    '字段不含敏感词',
    'data_quality',
    '验证字段不包含指定的敏感关键词。适用于数据最小化和隐私保护。',
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'field_name', JSON_OBJECT('type', 'string', 'description', '要验证的字段名称'),
            'field_display_name', JSON_OBJECT('type', 'string', 'description', '字段的显示名称'),
            'blocked_keywords', JSON_OBJECT('type', 'array', 'description', '禁止出现的关键词列表'),
            'case_sensitive', JSON_OBJECT('type', 'boolean', 'description', '是否区分大小写', 'default', false)
        ),
        'required', JSON_ARRAY('field_name', 'field_display_name', 'blocked_keywords')
    ),
    JSON_OBJECT('type', 'keyword_block', 'logic', 'check_no_sensitive_keywords'),
    'warning',
    JSON_OBJECT('category', '隐私保护', 'gdpr', true),
    1,
    '用于检测字段中不应出现的敏感信息'
);

-- 8. 字段依赖关系验证
INSERT INTO audit_rule_template (
    template_code, template_name, template_category, template_description,
    parameters_schema, validation_template, default_severity, tags, is_active, remark
) VALUES (
    'FIELD_DEPENDENCY_CHECK',
    '字段依赖关系验证',
    'business_rule',
    '验证字段间的依赖关系。例如：如果字段A有值，则字段B也必须有值。',
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'source_field', JSON_OBJECT('type', 'string', 'description', '源字段名称'),
            'source_field_display', JSON_OBJECT('type', 'string', 'description', '源字段显示名称'),
            'dependent_field', JSON_OBJECT('type', 'string', 'description', '依赖字段名称'),
            'dependent_field_display', JSON_OBJECT('type', 'string', 'description', '依赖字段显示名称'),
            'condition', JSON_OBJECT('type', 'string', 'description', '触发条件', 'default', 'not_empty')
        ),
        'required', JSON_ARRAY('source_field', 'source_field_display', 'dependent_field', 'dependent_field_display')
    ),
    JSON_OBJECT('type', 'field_dependency', 'logic', 'validate_field_dependency'),
    'error',
    JSON_OBJECT('category', '业务规则', 'gdpr', true),
    1,
    '用于验证字段间的业务依赖关系，如合法性基础与用途的一致性'
);

-- 9. 字段唯一性验证
INSERT INTO audit_rule_template (
    template_code, template_name, template_category, template_description,
    parameters_schema, validation_template, default_severity, tags, is_active, remark
) VALUES (
    'FIELD_UNIQUE_CHECK',
    '字段唯一性验证',
    'data_quality',
    '验证字段值在数据集中唯一（无重复）。适用于用户ID、订单号等唯一标识。',
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'field_name', JSON_OBJECT('type', 'string', 'description', '要验证的字段名称'),
            'field_display_name', JSON_OBJECT('type', 'string', 'description', '字段的显示名称'),
            'ignore_empty', JSON_OBJECT('type', 'boolean', 'description', '是否忽略空值', 'default', true)
        ),
        'required', JSON_ARRAY('field_name', 'field_display_name')
    ),
    JSON_OBJECT('type', 'uniqueness_check', 'logic', 'validate_no_duplicates'),
    'error',
    JSON_OBJECT('category', '数据质量', 'gdpr', false),
    1,
    '用于验证唯一性字段不重复'
);

-- 10. 跨数据集引用验证
INSERT INTO audit_rule_template (
    template_code, template_name, template_category, template_description,
    parameters_schema, validation_template, default_severity, tags, is_active, remark
) VALUES (
    'FIELD_CROSS_DATASET_REFERENCE',
    '跨数据集引用验证',
    'business_rule',
    '验证字段值必须在另一个数据集/字典中存在。适用于外键、参照完整性等场景。',
    JSON_OBJECT(
        'type', 'object',
        'properties', JSON_OBJECT(
            'field_name', JSON_OBJECT('type', 'string', 'description', '要验证的字段名称'),
            'field_display_name', JSON_OBJECT('type', 'string', 'description', '字段的显示名称'),
            'reference_dataset', JSON_OBJECT('type', 'string', 'description', '参考数据集/表名称'),
            'reference_field', JSON_OBJECT('type', 'string', 'description', '参考字段名称'),
            'allow_empty', JSON_OBJECT('type', 'boolean', 'description', '是否允许空值', 'default', false)
        ),
        'required', JSON_ARRAY('field_name', 'field_display_name', 'reference_dataset', 'reference_field')
    ),
    JSON_OBJECT('type', 'reference_check', 'logic', 'validate_reference_exists'),
    'error',
    JSON_OBJECT('category', '参照完整性', 'gdpr', false),
    1,
    '用于验证外键引用完整性'
);

-- 验证插入结果
SELECT
    template_code,
    template_name,
    template_category,
    is_active
FROM audit_rule_template
ORDER BY template_category, template_code;

-- 统计
SELECT
    template_category,
    COUNT(*) as count
FROM audit_rule_template
GROUP BY template_category;
```

---

## ✅ 验证清单

完成部署后，请检查以下项目：

- [ ] `audit_rule_template` 表已创建
- [ ] `audit_rule` 表新增了4个字段
- [ ] 数据库中有10个规则模板记录
- [ ] 所有模板的 `is_active = 1`
- [ ] API接口 `/audit/rule-template/list` 可以访问
- [ ] API接口 `/audit/rule-template/all` 返回10个模板
- [ ] 查看 `QUICKSTART.md` 完成第一次测试

---

## 🐛 故障排查

### 问题1: 表创建失败

**错误**: Table already exists

**解决**:
```sql
DROP TABLE IF EXISTS audit_rule_template;
-- 然后重新执行创建语句
```

### 问题2: JSON列不支持

**错误**: Unknown column type 'JSON'

**解决**: MySQL版本过低，需要5.7.8+版本

### 问题3: 模板插入失败

**错误**: Duplicate entry for key 'template_code'

**解决**: 模板已存在，先清空再插入
```sql
TRUNCATE TABLE audit_rule_template;
-- 然后重新执行插入语句
```

### 问题4: 外键约束错误

**解决**: 注释掉SQL脚本中的外键约束部分

---

## 📞 获取帮助

如果遇到问题，请查看：
1. [完整系统文档](./RULE_TEMPLATE_SYSTEM.md)
2. [快速开始指南](./QUICKSTART.md)
3. 项目Issue页面

---

部署完成后，请参考 [QUICKSTART.md](./QUICKSTART.md) 进行第一次测试！

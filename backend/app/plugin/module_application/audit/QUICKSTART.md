# 快速开始：规则模板与法规解析系统

这是一个5分钟快速上手指南，帮助你快速测试和使用法规解析与规则自动生成功能。

## 🚀 快速开始

### 步骤1：初始化规则模板

首先需要初始化10个默认规则模板。

**方法A：通过Python脚本**

创建文件 `init_templates.py`：

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config.setting import settings
from app.plugin.module_application.audit.rule_template.seeder import seed_default_templates

async def init():
    # 创建数据库连接
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        await seed_default_templates(session)
        print("规则模板初始化完成！")

if __name__ == "__main__":
    asyncio.run(init())
```

运行：
```bash
python init_templates.py
```

**方法B：通过SQL直接插入**

查看 `default_templates.py` 中的模板定义，手动插入到 `audit_rule_template` 表中。

---

### 步骤2：测试结构化输入（最简单）

使用Postman或curl测试结构化输入模式。

**创建测试法规**：
```bash
POST http://localhost:8000/audit/regulation/upload
Content-Type: multipart/form-data

# 上传一个空文件即可，我们使用结构化输入
file: test_regulation.txt
regulation_name: "测试GDPR法规"
```

获取法规ID（假设返回 `regulation_id: 1`）

**解析法规（结构化输入）**：
```bash
POST http://localhost:8000/audit/regulation/1/parse
Content-Type: application/json

{
  "parse_mode": "manual",
  "structured_input": {
    "regulation_name": "GDPR用户数据保护条例",
    "requirements": [
      {
        "field_name": "email",
        "field_display_name": "用户邮箱",
        "rule_type": "必填",
        "validation_condition": "不能为空",
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
        "field_name": "consent_flag",
        "field_display_name": "用户同意标识",
        "rule_type": "枚举",
        "validation_condition": "只能是Y或N",
        "allowed_values": ["Y", "N"],
        "severity": "error"
      }
    ]
  }
}
```

**期望响应**：
```json
{
  "code": 200,
  "message": "解析成功，提取到 3 个审计要求",
  "data": {
    "success": true,
    "requirements_count": 3,
    "requirements": [
      {
        "template_id": 1,
        "template_code": "FIELD_REQUIRED",
        "instance_parameters": {
          "field_name": "email",
          "field_display_name": "用户邮箱"
        },
        "rule_code": "REG-EMAIL-REQUIRED",
        "rule_name": "用户邮箱 - 必填",
        "confidence": 1.0,
        "severity": "error"
      },
      ...
    ]
  }
}
```

---

### 步骤3：生成规则

使用上一步解析的结果生成规则。

```bash
POST http://localhost:8000/audit/regulation/1/generate-rules
Content-Type: application/json

{
  "parsed_requirements": [
    // 复制步骤2返回的 requirements 数组
  ],
  "auto_activate": true
}
```

**期望响应**：
```json
{
  "code": 200,
  "message": "成功生成 3 个规则",
  "data": {
    "success": true,
    "generated_count": 3,
    "failed_count": 0,
    "rule_ids": [10, 11, 12],
    "errors": []
  }
}
```

---

### 步骤4：验证规则

查看生成的规则：

```bash
GET http://localhost:8000/audit/rule/detail/10
GET http://localhost:8000/audit/rule/detail/11
GET http://localhost:8000/audit/rule/detail/12
```

检查规则是否包含：
- `template_id`：关联的模板ID
- `instance_parameters`：实例化参数
- `regulation_id`：关联的法规ID
- `auto_generated: 1`：标记为自动生成

---

### 步骤5：在审计任务中使用规则

创建审计任务并使用生成的规则：

```bash
# 1. 创建任务
POST http://localhost:8000/audit/task/create
{
  "task_name": "测试GDPR审计",
  "description": "使用自动生成的规则"
}

# 2. 上传或选择法规
POST http://localhost:8000/audit/task/1/use-regulation/1

# 3. 确认规则（选择自动生成的规则）
POST http://localhost:8000/audit/task/1/confirm-rules
{
  "selected_rules": [10, 11, 12]
}

# 4. 上传测试数据集
POST http://localhost:8000/audit/task/1/upload-dataset
Content-Type: multipart/form-data
file: test_data.csv

# 5. 执行审计
POST http://localhost:8000/audit/task/1/execute
```

---

## 🧪 测试数据

### 测试CSV文件（test_data.csv）

```csv
user_id,email,consent_flag,age
1,user1@example.com,Y,25
2,invalid-email,N,30
3,user3@example.com,Y,150
4,,Y,20
5,user5@example.com,INVALID,35
```

**预期审计结果**：
- 第2行：email格式错误
- 第3行：age超出范围（如果有范围规则）
- 第4行：email为空（必填规则）
- 第5行：consent_flag不是Y或N（枚举规则）

---

## 🎯 一键测试（所有步骤合并）

使用一键API完成所有操作：

```bash
POST http://localhost:8000/audit/regulation/1/parse-and-generate
Content-Type: application/json

{
  "parse_mode": "manual",
  "structured_input": {
    "regulation_name": "GDPR用户数据保护条例",
    "requirements": [
      {
        "field_name": "email",
        "field_display_name": "用户邮箱",
        "rule_type": "必填",
        "validation_condition": "不能为空",
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
        "field_name": "consent_flag",
        "field_display_name": "用户同意标识",
        "rule_type": "枚举",
        "validation_condition": "只能是Y或N",
        "allowed_values": ["Y", "N"],
        "severity": "error"
      },
      {
        "field_name": "age",
        "field_display_name": "年龄",
        "rule_type": "数值范围",
        "validation_condition": "必须在0-120之间",
        "min_value": 0,
        "max_value": 120,
        "severity": "warning"
      }
    ]
  }
}
```

**一步完成**：解析 + 生成规则！

---

## 🔧 配置AI服务（可选）

如果要使用自动解析模式（AI解析法规文本），需要配置OpenAI API。

在 `.env` 文件中添加：

```env
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
```

然后可以使用自动解析：

```bash
POST http://localhost:8000/audit/regulation/1/parse
{
  "parse_mode": "auto"  # 使用AI自动解析
}
```

---

## 📋 检查清单

完成以下检查确保系统正常工作：

- [ ] 数据库表 `audit_rule_template` 已创建
- [ ] 已运行 `seed_default_templates` 初始化10个模板
- [ ] 可以查询模板列表：`GET /audit/rule-template/list`
- [ ] 可以上传或创建法规
- [ ] 可以解析法规（结构化输入模式）
- [ ] 可以生成规则
- [ ] 生成的规则包含 `template_id` 和 `instance_parameters`
- [ ] 可以在审计任务中使用生成的规则
- [ ] 审计引擎能正确验证数据

---

## 🐛 常见问题排查

### 问题1：模板列表为空

**原因**：未初始化模板
**解决**：运行 `seed_default_templates`

### 问题2：解析返回空数组

**原因**：
- 结构化输入格式错误
- rule_type 不在支持列表中

**解决**：
- 检查JSON格式
- 参考 `REGULATION_INPUT_GUIDE.md` 中的规则类型

### 问题3：生成规则失败

**原因**：
- 规则编码重复
- 参数缺失

**解决**：
- 使用唯一的rule_code
- 确保必需参数都存在

### 问题4：规则验证不生效

**原因**：
- rule_expression 格式错误
- validation_type 不匹配

**解决**：
- 检查生成的rule_expression
- 确认AuditEngine已更新

---

## 📞 获取帮助

如遇问题，请查看：
1. [完整系统文档](./RULE_TEMPLATE_SYSTEM.md)
2. [法规输入指南](./REGULATION_INPUT_GUIDE.md)
3. 项目Issue页面

---

**祝测试顺利！** 🎉

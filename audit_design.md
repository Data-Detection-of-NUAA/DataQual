# 数据集合规审计系统 - 设计文档

## 1. 功能流程

```
步骤1: 上传法规文件
   ↓
步骤2: AI智能匹配规则 + 用户确认/调整
   ↓
步骤3: 上传数据集
   ↓
步骤4: 审计结果展示 + 错误报告下载
```

## 2. 数据库表设计

### 2.1 规则池表 (audit_rule)
```sql
CREATE TABLE audit_rule (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    rule_code VARCHAR(100) NOT NULL COMMENT '规则编码',
    rule_name VARCHAR(200) NOT NULL COMMENT '规则名称',
    rule_type VARCHAR(50) NOT NULL COMMENT '规则类型：email/phone/idcard/custom等',
    rule_description TEXT COMMENT '规则描述',
    rule_expression TEXT COMMENT '规则表达式(正则/JSON)',
    severity VARCHAR(20) DEFAULT 'warning' COMMENT '严重级别：error/warning/info',
    is_active TINYINT DEFAULT 1 COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_id BIGINT,
    updated_id BIGINT,
    remark VARCHAR(500)
);
```

### 2.2 审计任务表 (audit_task)
```sql
CREATE TABLE audit_task (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_name VARCHAR(200) NOT NULL COMMENT '任务名称',
    task_status VARCHAR(20) DEFAULT 'pending' COMMENT '任务状态：pending/processing/completed/failed',

    -- 步骤1: 法规文件
    regulation_file_type VARCHAR(50) COMMENT '法规文件类型：txt/xml/docx/pdf',
    regulation_file_path VARCHAR(500) COMMENT '法规文件路径',
    regulation_file_name VARCHAR(200) COMMENT '法规文件名',

    -- 步骤2: AI匹配的规则
    matched_rules JSON COMMENT 'AI匹配的规则ID列表',
    selected_rules JSON COMMENT '用户最终选择的规则ID列表',

    -- 步骤3: 数据集文件
    dataset_file_type VARCHAR(50) COMMENT '数据集文件类型',
    dataset_file_path VARCHAR(500) COMMENT '数据集文件路径',
    dataset_file_name VARCHAR(200) COMMENT '数据集文件名',

    -- 审计结果
    total_records INT DEFAULT 0 COMMENT '总记录数',
    error_records INT DEFAULT 0 COMMENT '错误记录数',
    data_errors JSON COMMENT '数据错误详情',
    label_errors JSON COMMENT '标签错误详情',
    audit_report_path VARCHAR(500) COMMENT '审计报告路径',

    -- 元信息
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_id BIGINT,
    updated_id BIGINT,
    remark VARCHAR(500)
);
```

### 2.3 审计错误详情表 (audit_error)
```sql
CREATE TABLE audit_error (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id BIGINT NOT NULL COMMENT '任务ID',
    error_type VARCHAR(20) NOT NULL COMMENT '错误类型：data/label',

    -- 错误位置
    row_number INT COMMENT '行号',
    column_name VARCHAR(100) COMMENT '列名',
    field_name VARCHAR(100) COMMENT '字段名',

    -- 错误内容
    original_value TEXT COMMENT '原始值',
    error_message TEXT COMMENT '错误描述',
    rule_id BIGINT COMMENT '违反的规则ID',
    severity VARCHAR(20) COMMENT '严重级别',

    -- 错误标记位置（用于前端波浪线标记）
    start_position INT COMMENT '错误开始位置',
    end_position INT COMMENT '错误结束位置',

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_task_id (task_id),
    INDEX idx_error_type (error_type)
);
```

## 3. 后端API接口设计

### 3.1 规则管理接口
```
GET    /api/v1/audit/rule/list          # 获取规则列表
POST   /api/v1/audit/rule/create        # 创建规则
PUT    /api/v1/audit/rule/update        # 更新规则
DELETE /api/v1/audit/rule/delete/{id}   # 删除规则
GET    /api/v1/audit/rule/detail/{id}   # 获取规则详情
```

### 3.2 审计任务接口
```
POST   /api/v1/audit/task/create                    # 创建审计任务
GET    /api/v1/audit/task/detail/{id}               # 获取任务详情
GET    /api/v1/audit/task/list                      # 获取任务列表

# 步骤1: 上传法规文件
POST   /api/v1/audit/task/{id}/upload-regulation    # 上传法规文件

# 步骤2: AI匹配规则
POST   /api/v1/audit/task/{id}/match-rules          # AI智能匹配规则
POST   /api/v1/audit/task/{id}/confirm-rules        # 用户确认规则

# 步骤3: 上传数据集
POST   /api/v1/audit/task/{id}/upload-dataset       # 上传数据集

# 步骤4: 执行审计 & 获取结果
POST   /api/v1/audit/task/{id}/execute              # 执行审计
GET    /api/v1/audit/task/{id}/result               # 获取审计结果
GET    /api/v1/audit/task/{id}/download-report      # 下载审计报告
GET    /api/v1/audit/task/{id}/errors               # 获取错误详情列表
```

### 3.3 文件上传接口
```
POST   /api/v1/audit/file/upload                    # 通用文件上传
GET    /api/v1/audit/file/download/{filename}       # 文件下载
```

## 4. 前端页面结构

### 4.1 路由配置
```
/audit/task/list         # 任务列表页
/audit/task/create       # 创建任务 & 执行审计流程
/audit/rule/list         # 规则管理页
```

### 4.2 审计流程页面组件结构
```vue
<template>
  <div class="audit-workflow">
    <!-- 步骤导航条 (始终显示) -->
    <el-steps :active="currentStep" align-center>
      <el-step title="上传法规文件" />
      <el-step title="选择审计规则" />
      <el-step title="上传数据集" />
      <el-step title="审计结果" />
    </el-steps>

    <!-- 步骤内容 -->
    <div class="step-content">
      <!-- 步骤1: 上传法规文件 -->
      <StepRegulation v-if="currentStep === 1" />

      <!-- 步骤2: 选择规则 -->
      <StepRuleSelect v-if="currentStep === 2" />

      <!-- 步骤3: 上传数据集 -->
      <StepDataset v-if="currentStep === 3" />

      <!-- 步骤4: 审计结果 -->
      <StepResult v-if="currentStep === 4" />
    </div>

    <!-- 操作按钮 -->
    <div class="step-actions">
      <el-button v-if="currentStep > 1" @click="prevStep">上一步</el-button>
      <el-button v-if="currentStep < 4" type="primary" @click="nextStep">下一步</el-button>
      <el-button v-if="currentStep === 4" type="success" @click="downloadReport">下载报告</el-button>
    </div>
  </div>
</template>
```

### 4.3 各步骤组件详细设计

#### 步骤1: 上传法规文件 (StepRegulation.vue)
```vue
<template>
  <div class="step-regulation">
    <el-alert type="info" :closable="false" show-icon>
      <template #title>
        <strong>合规审计流程说明</strong>
      </template>
      <p>1️⃣ 上传法规文件（支持txt/xml/docx/pdf格式）</p>
      <p>2️⃣ AI智能匹配审计规则，您可以调整</p>
      <p>3️⃣ 上传待审计的数据集</p>
      <p>4️⃣ 查看审计结果并下载报告</p>
    </el-alert>

    <el-form :model="form" label-width="120px" style="margin-top: 20px">
      <el-form-item label="法规文件类型">
        <el-select v-model="form.fileType" placeholder="请选择文件类型">
          <el-option label="文本文件 (.txt)" value="txt" />
          <el-option label="XML文件 (.xml)" value="xml" />
          <el-option label="Word文档 (.docx)" value="docx" />
          <el-option label="PDF文档 (.pdf)" value="pdf" />
        </el-select>
      </el-form-item>

      <el-form-item label="上传法规文件">
        <el-upload
          :action="uploadUrl"
          :accept="acceptTypes"
          :before-upload="beforeUpload"
          :on-success="handleSuccess"
          :limit="1"
        >
          <el-button type="primary">点击上传</el-button>
          <template #tip>
            <div class="el-upload__tip">
              只能上传{{ form.fileType }}文件，且不超过10MB
            </div>
          </template>
        </el-upload>
      </el-form-item>
    </el-form>
  </div>
</template>
```

#### 步骤2: 选择规则 (StepRuleSelect.vue)
```vue
<template>
  <div class="step-rule-select">
    <el-alert type="success" :closable="false" show-icon>
      AI已根据您上传的法规文件智能匹配以下审计规则，请确认或调整：
    </el-alert>

    <div style="margin-top: 20px">
      <el-transfer
        v-model="selectedRules"
        :data="allRules"
        :titles="['可用规则', '已选规则']"
        :props="{
          key: 'id',
          label: 'rule_name'
        }"
        filterable
      >
        <template #default="{ option }">
          <div>
            <span>{{ option.rule_name }}</span>
            <el-tag v-if="option.ai_matched" type="success" size="small" style="margin-left: 10px">
              AI推荐
            </el-tag>
          </div>
          <div style="font-size: 12px; color: #999">
            {{ option.rule_description }}
          </div>
        </template>
      </el-transfer>
    </div>

    <el-divider />

    <el-table :data="selectedRuleDetails" border>
      <el-table-column prop="rule_code" label="规则编码" width="120" />
      <el-table-column prop="rule_name" label="规则名称" />
      <el-table-column prop="rule_type" label="规则类型" width="120" />
      <el-table-column prop="severity" label="严重级别" width="100">
        <template #default="{ row }">
          <el-tag :type="getSeverityType(row.severity)">
            {{ row.severity }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="rule_description" label="规则描述" />
    </el-table>
  </div>
</template>
```

#### 步骤3: 上传数据集 (StepDataset.vue)
```vue
<template>
  <div class="step-dataset">
    <el-form :model="form" label-width="120px">
      <el-form-item label="数据集类型">
        <el-select v-model="form.datasetType" placeholder="请选择数据集类型">
          <el-option label="CSV文件 (.csv)" value="csv" />
          <el-option label="Excel文件 (.xlsx)" value="xlsx" />
          <el-option label="JSON文件 (.json)" value="json" />
          <el-option label="XML文件 (.xml)" value="xml" />
          <el-option label="文本文件 (.txt)" value="txt" />
        </el-select>
      </el-form-item>

      <el-form-item label="上传数据集">
        <el-upload
          :action="uploadUrl"
          :accept="acceptTypes"
          :before-upload="beforeUpload"
          :on-success="handleSuccess"
          :on-progress="handleProgress"
          :limit="1"
        >
          <el-button type="primary">点击上传</el-button>
          <template #tip>
            <div class="el-upload__tip">
              只能上传{{ form.datasetType }}文件，且不超过100MB
            </div>
          </template>
        </el-upload>

        <el-progress v-if="uploadProgress > 0" :percentage="uploadProgress" />
      </el-form-item>
    </el-form>

    <el-alert v-if="uploadSuccess" type="success" :closable="false">
      数据集上传成功！点击"下一步"开始执行审计
    </el-alert>
  </div>
</template>
```

#### 步骤4: 审计结果 (StepResult.vue)
```vue
<template>
  <div class="step-result">
    <!-- 审计概览 -->
    <el-row :gutter="20">
      <el-col :span="6">
        <el-statistic title="总记录数" :value="result.total_records" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="错误记录数" :value="result.error_records" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="数据错误" :value="result.data_errors?.length || 0" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="标签错误" :value="result.label_errors?.length || 0" />
      </el-col>
    </el-row>

    <el-divider />

    <!-- 错误详情 -->
    <el-row :gutter="20">
      <!-- 左侧：数据错误 -->
      <el-col :span="12">
        <el-card header="数据错误">
          <el-table :data="dataErrors" border max-height="500">
            <el-table-column prop="row_number" label="行号" width="80" />
            <el-table-column prop="column_name" label="列名" width="120" />
            <el-table-column prop="original_value" label="错误值">
              <template #default="{ row }">
                <span class="error-text">
                  {{ highlightError(row.original_value, row.start_position, row.end_position) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="error_message" label="错误描述" />
            <el-table-column prop="severity" label="级别" width="80">
              <template #default="{ row }">
                <el-tag :type="getSeverityType(row.severity)" size="small">
                  {{ row.severity }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 右侧：标签错误 -->
      <el-col :span="12">
        <el-card header="标签错误">
          <el-table :data="labelErrors" border max-height="500">
            <el-table-column prop="row_number" label="行号" width="80" />
            <el-table-column prop="field_name" label="字段名" width="120" />
            <el-table-column prop="original_value" label="错误值">
              <template #default="{ row }">
                <span class="error-text">
                  {{ highlightError(row.original_value, row.start_position, row.end_position) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="error_message" label="错误描述" />
            <el-table-column prop="severity" label="级别" width="80">
              <template #default="{ row }">
                <el-tag :type="getSeverityType(row.severity)" size="small">
                  {{ row.severity }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <div style="margin-top: 20px; text-align: center">
      <el-button type="success" size="large" @click="downloadReport">
        <el-icon><Download /></el-icon>
        下载完整审计报告
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.error-text {
  position: relative;
}

.error-text::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: -2px;
  width: 100%;
  height: 2px;
  background-image: repeating-linear-gradient(
    45deg,
    #f56c6c,
    #f56c6c 2px,
    transparent 2px,
    transparent 4px
  );
}
</style>
```

## 5. 技术实现要点

### 5.1 文件上传处理
- 使用FastAPI的`UploadFile`处理文件上传
- 按日期分目录存储：`/upload/audit/{year}/{month}/{day}/`
- 生成唯一文件名避免冲突：`{uuid}_{original_name}`

### 5.2 AI规则匹配
- 使用OpenAI API解析法规文件内容
- Prompt设计：
  ```
  分析以下法规文件内容，识别需要审计的数据类型（如邮箱、手机号、身份证等），
  从规则池中匹配相关规则，返回规则ID列表。

  规则池：{rules}

  法规内容：{regulation_content}
  ```

### 5.3 数据集审计引擎
- 根据文件类型选择解析器（CSV/Excel/JSON/XML）
- 逐行应用选定的规则进行校验
- 记录错误位置（行号、列名、起止位置）
- 生成审计报告（Excel格式）

### 5.4 错误标记实现
- 在前端使用CSS实现波浪线效果
- 根据`start_position`和`end_position`精确定位错误

## 6. 项目文件结构

```
backend/app/plugin/module_audit/
├── __init__.py
├── rule/                          # 规则管理
│   ├── controller.py
│   ├── service.py
│   ├── crud.py
│   ├── model.py
│   └── schema.py
├── task/                          # 审计任务
│   ├── controller.py
│   ├── service.py
│   ├── crud.py
│   ├── model.py
│   └── schema.py
├── file/                          # 文件处理
│   ├── controller.py
│   └── service.py
└── engine/                        # 审计引擎
    ├── parser.py                  # 文件解析器
    ├── validator.py               # 规则验证器
    ├── ai_matcher.py              # AI规则匹配
    └── report_generator.py        # 报告生成器

frontend/src/
├── api/module_audit/
│   ├── rule.ts
│   ├── task.ts
│   └── file.ts
└── views/module_audit/
    ├── rule/
    │   └── index.vue              # 规则管理页面
    ├── task/
    │   ├── list.vue               # 任务列表
    │   └── workflow.vue           # 审计流程页面
    └── components/
        ├── StepRegulation.vue     # 步骤1组件
        ├── StepRuleSelect.vue     # 步骤2组件
        ├── StepDataset.vue        # 步骤3组件
        └── StepResult.vue         # 步骤4组件
```

## 7. 开发步骤建议

1. ✅ **创建数据库表** - 执行SQL创建表结构
2. ✅ **开发规则管理** - 先实现规则的CRUD功能（可使用代码生成器）
3. ✅ **实现文件上传** - 开发文件上传接口和服务
4. ✅ **集成AI服务** - 实现AI规则匹配功能
5. ✅ **开发审计引擎** - 实现数据解析和校验逻辑
6. ✅ **开发任务管理** - 实现任务创建、执行、结果查询
7. ✅ **开发前端页面** - 实现4个步骤组件和整体流程
8. ✅ **联调测试** - 端到端测试整个审计流程

## 8. 注意事项

- **权限控制**：所有API需要添加权限装饰器
- **异常处理**：文件解析、AI调用等环节需要完善的异常处理
- **性能优化**：大文件审计考虑使用异步任务队列（Celery）
- **安全性**：文件上传需要校验文件类型和大小，防止恶意文件
- **日志记录**：关键操作使用OperationLogRoute记录日志

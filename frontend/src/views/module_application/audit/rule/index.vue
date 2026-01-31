<!-- 审计规则管理 -->
<template>
  <div class="app-container">
    <!-- 搜索区域 -->
    <div class="search-container">
      <el-form
        ref="queryFormRef"
        :model="queryFormData"
        :inline="true"
        label-suffix=":"
        @submit.prevent="handleQuery"
      >
        <el-form-item prop="rule_code" label="规则编码">
          <el-input v-model="queryFormData.rule_code" placeholder="请输入规则编码" clearable />
        </el-form-item>
        <el-form-item prop="rule_name" label="规则名称">
          <el-input v-model="queryFormData.rule_name" placeholder="请输入规则名称" clearable />
        </el-form-item>
        <el-form-item prop="rule_type" label="规则类型">
          <el-select
            v-model="queryFormData.rule_type"
            placeholder="请选择规则类型"
            style="width: 167.5px"
            clearable
          >
            <el-option value="data_validation" label="数据验证" />
            <el-option value="label_validation" label="标签验证" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="isExpand" prop="is_active" label="状态">
          <el-select
            v-model="queryFormData.is_active"
            placeholder="请选择状态"
            style="width: 167.5px"
            clearable
          >
            <el-option :value="1" label="启用" />
            <el-option :value="0" label="禁用" />
          </el-select>
        </el-form-item>
        <!-- 查询、重置、展开/收起按钮 -->
        <el-form-item class="search-buttons">
          <el-button type="primary" icon="search" native-type="submit">查询</el-button>
          <el-button icon="refresh" @click="handleResetQuery">重置</el-button>
          <!-- 展开/收起 -->
          <template v-if="isExpandable">
            <el-link class="ml-3" type="primary" underline="never" @click="isExpand = !isExpand">
              {{ isExpand ? "收起" : "展开" }}
              <el-icon>
                <template v-if="isExpand">
                  <ArrowUp />
                </template>
                <template v-else>
                  <ArrowDown />
                </template>
              </el-icon>
            </el-link>
          </template>
        </el-form-item>
      </el-form>
    </div>

    <!-- 内容区域 -->
    <el-card class="data-table">
      <template #header>
        <div class="card-header">
          <span>
            <el-tooltip content="审计规则管理，用于配置数据合规性审计的验证规则。">
              <QuestionFilled class="w-4 h-4 mx-1" />
            </el-tooltip>
            审计规则列表
          </span>
        </div>
      </template>

      <!-- 功能区域 -->
      <div class="data-table__toolbar">
        <div class="data-table__toolbar--left">
          <el-row :gutter="10">
            <el-col :span="1.5">
              <el-button type="success" icon="plus" @click="handleOpenDialog('create')">
                新增规则
              </el-button>
            </el-col>
            <el-col :span="1.5">
              <el-button
                type="danger"
                icon="delete"
                :disabled="selectIds.length === 0"
                @click="handleDelete(selectIds)"
              >
                批量删除
              </el-button>
            </el-col>
            <el-col :span="1.5">
              <el-dropdown trigger="click">
                <el-button type="default" :disabled="selectIds.length === 0" icon="ArrowDown">
                  更多
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item icon="Check" @click="handleMoreClick(1)">
                      批量启用
                    </el-dropdown-item>
                    <el-dropdown-item icon="CircleClose" @click="handleMoreClick(0)">
                      批量禁用
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </el-col>
          </el-row>
        </div>
        <div class="data-table__toolbar--right">
          <el-row :gutter="10">
            <el-col :span="1.5">
              <el-tooltip content="刷新">
                <el-button type="primary" icon="refresh" circle @click="handleRefresh" />
              </el-tooltip>
            </el-col>
          </el-row>
        </div>
      </div>

      <!-- 表格区域 -->
      <el-table
        ref="dataTableRef"
        v-loading="loading"
        :data="pageTableData"
        highlight-current-row
        class="data-table__content"
        height="450"
        max-height="450"
        border
        stripe
        @selection-change="handleSelectionChange"
      >
        <template #empty>
          <el-empty :image-size="80" description="暂无数据" />
        </template>
        <el-table-column type="selection" min-width="55" align="center" />
        <el-table-column type="index" fixed label="序号" min-width="60">
          <template #default="scope">
            {{ (queryFormData.page_no - 1) * queryFormData.page_size + scope.$index + 1 }}
          </template>
        </el-table-column>
        <el-table-column label="规则编码" prop="rule_code" min-width="140" show-overflow-tooltip />
        <el-table-column label="规则名称" prop="rule_name" min-width="180" show-overflow-tooltip />
        <el-table-column label="规则类型" prop="rule_type" min-width="120">
          <template #default="scope">
            <el-tag v-if="scope.row.rule_type === 'data_validation'" type="primary">
              数据验证
            </el-tag>
            <el-tag v-else-if="scope.row.rule_type === 'label_validation'" type="success">
              标签验证
            </el-tag>
            <el-tag v-else>{{ scope.row.rule_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column
          label="字段名称"
          prop="field_name"
          min-width="120"
          show-overflow-tooltip
        />
        <el-table-column
          label="验证规则"
          prop="validation_rule"
          min-width="150"
          show-overflow-tooltip
        />
        <el-table-column label="状态" prop="is_active" min-width="80">
          <template #default="scope">
            <el-tag :type="scope.row.is_active === 1 ? 'success' : 'danger'">
              {{ scope.row.is_active === 1 ? "启用" : "禁用" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" prop="created_time" min-width="180" sortable />
        <el-table-column fixed="right" label="操作" align="center" min-width="220">
          <template #default="scope">
            <el-button
              type="info"
              size="small"
              link
              icon="document"
              @click="handleOpenDialog('detail', scope.row.id)"
            >
              详情
            </el-button>
            <el-button
              type="primary"
              size="small"
              link
              icon="edit"
              @click="handleOpenDialog('update', scope.row.id)"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              size="small"
              link
              icon="delete"
              @click="handleDelete([scope.row.id])"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页区域 -->
      <template #footer>
        <pagination
          v-model:total="total"
          v-model:page="queryFormData.page_no"
          v-model:limit="queryFormData.page_size"
          @pagination="loadingData"
        />
      </template>
    </el-card>

    <!-- 弹窗区域 -->
    <el-dialog
      v-model="dialogVisible.visible"
      :title="dialogVisible.title"
      width="600px"
      @close="handleCloseDialog"
    >
      <!-- 详情 -->
      <template v-if="dialogVisible.type === 'detail'">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="规则编码" :span="2">
            {{ detailFormData.rule_code }}
          </el-descriptions-item>
          <el-descriptions-item label="规则名称" :span="2">
            {{ detailFormData.rule_name }}
          </el-descriptions-item>
          <el-descriptions-item label="规则类型" :span="2">
            <el-tag v-if="detailFormData.rule_type === 'data_validation'" type="primary">
              数据验证
            </el-tag>
            <el-tag v-else-if="detailFormData.rule_type === 'label_validation'" type="success">
              标签验证
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="字段名称" :span="2">
            {{ detailFormData.field_name || "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="验证规则" :span="2">
            {{ detailFormData.validation_rule || "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="错误消息" :span="2">
            {{ detailFormData.error_message || "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="状态" :span="2">
            <el-tag v-if="detailFormData.is_active === 1" type="success">启用</el-tag>
            <el-tag v-else type="danger">禁用</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">
            {{ detailFormData.created_time }}
          </el-descriptions-item>
        </el-descriptions>
      </template>
      <!-- 新增、编辑表单 -->
      <template v-else>
        <el-form
          ref="dataFormRef"
          :model="formData"
          :rules="rules"
          label-suffix=":"
          label-width="auto"
          label-position="right"
        >
          <el-form-item label="规则编码" prop="rule_code">
            <el-input v-model="formData.rule_code" placeholder="请输入规则编码" :maxlength="50" />
          </el-form-item>
          <el-form-item label="规则名称" prop="rule_name">
            <el-input v-model="formData.rule_name" placeholder="请输入规则名称" :maxlength="100" />
          </el-form-item>
          <el-form-item label="规则类型" prop="rule_type">
            <el-select
              v-model="formData.rule_type"
              placeholder="请选择规则类型"
              style="width: 100%"
            >
              <el-option value="data_validation" label="数据验证" />
              <el-option value="label_validation" label="标签验证" />
            </el-select>
          </el-form-item>
          <el-form-item label="字段名称" prop="field_name">
            <el-input
              v-model="formData.field_name"
              placeholder="请输入字段名称（如：email, phone）"
              :maxlength="50"
            />
          </el-form-item>
          <el-form-item label="验证规则" prop="validation_rule">
            <el-input
              v-model="formData.validation_rule"
              :rows="3"
              type="textarea"
              placeholder="请输入验证规则（如：email, phone, idcard, address, name）"
            />
          </el-form-item>
          <el-form-item label="错误消息" prop="error_message">
            <el-input
              v-model="formData.error_message"
              :rows="2"
              type="textarea"
              placeholder="请输入错误消息"
              :maxlength="200"
            />
          </el-form-item>
          <el-form-item label="状态" prop="is_active">
            <el-radio-group v-model="formData.is_active">
              <el-radio :value="1">启用</el-radio>
              <el-radio :value="0">禁用</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>
      </template>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleCloseDialog">取消</el-button>
          <el-button v-if="dialogVisible.type !== 'detail'" type="primary" @click="handleSubmit">
            确定
          </el-button>
          <el-button v-else type="primary" @click="handleCloseDialog">确定</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
defineOptions({
  name: "AuditRule",
  inheritAttrs: false,
});

import AuditRuleAPI, {
  AuditRuleTable,
  AuditRuleForm,
  AuditRulePageQuery,
} from "@/api/module_application/audit/rule";

const queryFormRef = ref();
const dataFormRef = ref();
const total = ref(0);
const selectIds = ref<number[]>([]);
const loading = ref(false);

const isExpand = ref(false);
const isExpandable = ref(true);

// 分页表单
const pageTableData = ref<AuditRuleTable[]>([]);

// 详情表单
const detailFormData = ref<AuditRuleTable>({} as AuditRuleTable);

// 分页查询参数
const queryFormData = reactive<AuditRulePageQuery>({
  page_no: 1,
  page_size: 10,
  rule_code: undefined,
  rule_name: undefined,
  rule_type: undefined,
  is_active: undefined,
});

// 编辑表单
const formData = reactive<AuditRuleForm>({
  id: undefined,
  rule_code: "",
  rule_name: "",
  rule_type: "data_validation",
  field_name: "",
  validation_rule: "",
  error_message: "",
  is_active: 1,
});

// 弹窗状态
const dialogVisible = reactive({
  title: "",
  visible: false,
  type: "create" as "create" | "update" | "detail",
});

// 表单验证规则
const rules = reactive({
  rule_code: [{ required: true, message: "请输入规则编码", trigger: "blur" }],
  rule_name: [{ required: true, message: "请输入规则名称", trigger: "blur" }],
  rule_type: [{ required: true, message: "请选择规则类型", trigger: "change" }],
});

// 列表刷新
async function handleRefresh() {
  await loadingData();
}

// 加载表格数据
async function loadingData() {
  loading.value = true;
  try {
    const response = await AuditRuleAPI.listRule(queryFormData);
    pageTableData.value = response.data.data.items;
    total.value = response.data.data.total;
  } catch (error: any) {
    console.error(error);
  } finally {
    loading.value = false;
  }
}

// 查询（重置页码后获取数据）
async function handleQuery() {
  queryFormData.page_no = 1;
  loadingData();
}

// 重置查询
async function handleResetQuery() {
  queryFormRef.value.resetFields();
  queryFormData.page_no = 1;
  loadingData();
}

// 定义初始表单数据常量
const initialFormData: AuditRuleForm = {
  id: undefined,
  rule_code: "",
  rule_name: "",
  rule_type: "data_validation",
  field_name: "",
  validation_rule: "",
  error_message: "",
  is_active: 1,
};

// 重置表单
async function resetForm() {
  if (dataFormRef.value) {
    dataFormRef.value.resetFields();
    dataFormRef.value.clearValidate();
  }
  Object.assign(formData, initialFormData);
}

// 行复选框选中项变化
async function handleSelectionChange(selection: any) {
  selectIds.value = selection.map((item: any) => item.id);
}

// 关闭弹窗
async function handleCloseDialog() {
  dialogVisible.visible = false;
  resetForm();
}

// 打开弹窗
async function handleOpenDialog(type: "create" | "update" | "detail", id?: number) {
  dialogVisible.type = type;
  if (id) {
    const response = await AuditRuleAPI.detailRule(id);
    if (type === "detail") {
      dialogVisible.title = "规则详情";
      Object.assign(detailFormData.value, response.data.data);
    } else if (type === "update") {
      dialogVisible.title = "修改规则";
      Object.assign(formData, response.data.data);
    }
  } else {
    dialogVisible.title = "新增规则";
    formData.id = undefined;
  }
  dialogVisible.visible = true;
}

// 新增、编辑弹窗处理
async function handleSubmit() {
  dataFormRef.value.validate(async (valid: any) => {
    if (valid) {
      loading.value = true;
      const id = formData.id;
      if (id) {
        try {
          await AuditRuleAPI.updateRule(id, { id, ...formData });
          dialogVisible.visible = false;
          resetForm();
          handleResetQuery();
        } catch (error: any) {
          console.error(error);
        } finally {
          loading.value = false;
        }
      } else {
        try {
          await AuditRuleAPI.createRule(formData);
          dialogVisible.visible = false;
          resetForm();
          handleResetQuery();
        } catch (error: any) {
          console.error(error);
        } finally {
          loading.value = false;
        }
      }
    }
  });
}

// 删除、批量删除
async function handleDelete(ids: number[]) {
  ElMessageBox.confirm("确认删除该项数据?", "警告", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning",
  })
    .then(async () => {
      try {
        loading.value = true;
        await AuditRuleAPI.deleteRule(ids);
        handleResetQuery();
      } catch (error: any) {
        console.error(error);
      } finally {
        loading.value = false;
      }
    })
    .catch(() => {
      ElMessageBox.close();
    });
}

// 批量启用/禁用
async function handleMoreClick(is_active: number) {
  if (selectIds.value.length) {
    ElMessageBox.confirm(`确认${is_active === 1 ? "启用" : "禁用"}该项数据?`, "警告", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    })
      .then(async () => {
        try {
          loading.value = true;
          await AuditRuleAPI.batchRule({ ids: selectIds.value, is_active });
          handleResetQuery();
        } catch (error: any) {
          console.error(error);
        } finally {
          loading.value = false;
        }
      })
      .catch(() => {
        ElMessageBox.close();
      });
  }
}

onMounted(() => {
  loadingData();
});
</script>

<style lang="scss" scoped></style>

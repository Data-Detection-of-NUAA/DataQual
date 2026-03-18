<template>
  <div class="step-panel">
    <el-alert
      title="使用 AI 自动匹配 GDPR 默认规则，可在右侧进行人工调整"
      type="info"
      :closable="false"
      show-icon
    />
    <div class="action-row">
      <el-button type="primary" :loading="matching" @click="$emit('match')">
        AI 智能匹配
      </el-button>
      <span v-if="matchedRuleIds.length" class="matched-hint">
        已推荐 {{ matchedRuleIds.length }} 条
      </span>
    </div>
    <el-transfer
      class="rule-transfer"
      v-model="innerSelected"
      :data="transferData"
      filterable
      :titles="['可用规则', '已选择规则']"
      :props="{
        key: 'id',
        label: 'label',
        disabled: 'disabled',
      }"
    >
      <template #default="{ option }">
        <div class="rule-option">
          <div class="rule-main">
            <span>{{ option.label }}</span>
            <el-tag
              v-if="option.ai_matched"
              size="small"
              type="success"
              effect="plain"
              >AI推荐</el-tag
            >
          </div>
          <div v-if="option.match_reason || option.regulation_ref" class="rule-detail">
            <div v-if="option.match_reason" class="match-reason">
              <el-icon><InfoFilled /></el-icon>
              <span>{{ option.match_reason }}</span>
            </div>
            <div v-if="option.regulation_ref" class="regulation-ref">
              <el-icon><Document /></el-icon>
              <span>{{ option.regulation_ref }}</span>
            </div>
          </div>
        </div>
      </template>
    </el-transfer>
    <div class="action-area">
      <el-button type="primary" :loading="confirming" @click="$emit('confirm')">
        确认规则
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { PropType } from "vue";
import type { MatchedRuleSummary } from "@/api/module_application/audit/task";
import { InfoFilled, Document } from "@element-plus/icons-vue";

const props = defineProps({
  matching: { type: Boolean, default: false },
  confirming: { type: Boolean, default: false },
  allRules: {
    type: Array as PropType<MatchedRuleSummary[]>,
    default: () => [],
  },
  matchedRuleIds: {
    type: Array as PropType<number[]>,
    default: () => [],
  },
  selectedRuleIds: {
    type: Array as PropType<number[]>,
    default: () => [],
  },
});

const emit = defineEmits<{
  (e: "match"): void;
  (e: "confirm"): void;
  (e: "update:selectedRuleIds", value: number[]): void;
}>();

const innerSelected = ref<number[]>([]);

watch(
  () => props.selectedRuleIds,
  (val) => {
    innerSelected.value = Array.isArray(val) ? [...val] : [];
  },
  { immediate: true }
);

watch(innerSelected, (val) => {
  emit("update:selectedRuleIds", val);
});

const transferData = computed(() =>
  props.allRules.map((rule) => ({
    id: rule.id,
    label: `${rule.rule_name} (${rule.rule_code})`,
    ai_matched: props.matchedRuleIds.includes(rule.id),
    match_reason: rule.match_reason || '',
    regulation_ref: rule.regulation_ref || '',
  }))
);
</script>

<style scoped>
.step-panel {
  padding: 12px 0;
}

.action-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 16px 0;
}

.matched-hint {
  color: var(--el-color-success);
}

.rule-option {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  width: 100%;
}

.rule-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.rule-detail {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
  padding-left: 8px;
  border-left: 2px solid var(--el-color-success-light-5);
}

.match-reason,
.regulation-ref {
  display: flex;
  align-items: center;
  gap: 4px;
  margin: 2px 0;
}

.match-reason .el-icon,
.regulation-ref .el-icon {
  font-size: 14px;
}

.rule-transfer {
  width: 100%;
}

.rule-transfer :deep(.el-transfer-panel) {
  width: 320px;
  height: 420px;
}

.rule-transfer :deep(.el-transfer-panel__body) {
  height: calc(100% - 52px);
}

.action-area {
  margin-top: 20px;
  text-align: center;
}
</style>

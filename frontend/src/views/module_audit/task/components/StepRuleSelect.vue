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
          <span>{{ option.label }}</span>
          <el-tag
            v-if="option.ai_matched"
            size="small"
            type="success"
            effect="plain"
            >AI推荐</el-tag
          >
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
import type { MatchedRuleSummary } from "@/api/module_audit/task";

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
  align-items: center;
  justify-content: space-between;
  width: 100%;
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

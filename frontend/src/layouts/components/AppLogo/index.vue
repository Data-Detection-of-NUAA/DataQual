<template>
  <div class="logo">
    <transition enter-active-class="animate__animated animate__fadeInLeft">
      <router-link :key="+collapse" class="wh-full flex-center" to="/">
        <span v-if="!collapse" class="title">数据集质量测评系统</span>
      </router-link>
    </transition>
  </div>
</template>

<script lang="ts" setup>
import { useConfigStore } from "@/store";
const configStore = useConfigStore();

defineProps({
  collapse: {
    type: Boolean,
    required: true,
  },
});
</script>

<style lang="scss" scoped>
.logo {
  width: auto;
  height: calc(#{$navbar-height} + 12px);
  background-color: transparent;
  display: flex;
  align-items: center;
  justify-content: center;

  :deep(.wh-full) {
    width: auto;
    height: 100%;
    justify-content: center;
  }

  .title {
    max-width: 320px;
    margin-left: 0;
    font-size: 20px;
    font-weight: bold;
    color: $sidebar-logo-text-color;
    line-height: 1;
    text-align: left;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}
</style>

<style lang="scss">
// 顶部布局和混合布局的特殊处理
.layout-top,
.layout-mix {
  .logo {
    background-color: transparent !important;

    .title {
      color: var(--menu-text);
    }
  }
}

// 宽屏时：openSidebar 状态下显示完整Logo+文字
.openSidebar {
  &.layout-top .layout__header-left .logo,
  &.layout-mix .layout__header-logo .logo {
    width: $sidebar-width; // 210px，显示logo+文字
  }
}

// 窄屏时：hideSidebar 状态下只显示Logo图标
.hideSidebar {
  &.layout-top .layout__header-left .logo,
  &.layout-mix .layout__header-logo .logo {
    width: $sidebar-width-collapsed; // 54px，只显示logo
  }

  // 隐藏文字，只显示图标
  .logo .title {
    display: none;
  }
}
</style>

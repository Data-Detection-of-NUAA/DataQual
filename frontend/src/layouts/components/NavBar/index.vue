<template>
  <div ref="navbar" class="navbar">
    <div class="navbar__left">
      <!-- 面包屑导航 -->
      <Breadcrumb class="navbar__breadcrumb" />
    </div>
    <!-- 导航栏操作区域 -->
    <div class="navbar__actions">
      <NavbarActions />
    </div>
  </div>
</template>

<script setup lang="ts">
import Breadcrumb from "@/components/Breadcrumb/index.vue";
import NavbarActions from "./components/NavbarActions.vue";

// 侧栏折叠功能已按需求注释
</script>

<style lang="scss" scoped>
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: $navbar-height;
  padding: 0 16px;
  background-color: var(--el-bg-color);

  &__left {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  &__breadcrumb {
    margin-left: 12px;
  }

  &__actions {
    display: flex;
    align-items: center;
    height: 100%;
  }
}
</style>

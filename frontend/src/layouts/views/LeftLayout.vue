<template>
  <BaseLayout>
    <!-- 顶栏 -->
    <NavBar class="layout__topbar" />

    <!-- 左侧菜单栏 -->
    <div class="layout__sidebar">
      <div class="layout-sidebar">
        <!-- 侧栏标题 -->
        <AppLogo :collapse="isLogoCollapsed" />
        <!-- 主菜单内容 -->
        <el-scrollbar ref="sidebarScrollbarRef" wrap-class="sidebar-scroll-wrap">
          <BasicMenu :data="routes" base-path="" />
        </el-scrollbar>

        <!-- 侧栏底部用户信息 -->
        <div class="sidebar-footer">
          <el-dropdown trigger="click">
            <div class="sidebar-user">
              <div class="sidebar-user__avatar">
                <el-avatar v-if="userAvatar" :size="36" :src="userAvatar" />
                <el-avatar v-else :size="36" icon="UserFilled" />
              </div>
              <div class="sidebar-user__info">
                <div class="sidebar-user__name">{{ userName }}</div>
                <div class="sidebar-user__role">{{ userRole }}</div>
              </div>
              <el-icon class="sidebar-user__arrow">
                <ArrowRight />
              </el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleProfileClick">
                  <el-icon>
                    <User />
                  </el-icon>
                  {{ t("navbar.profile") }}
                </el-dropdown-item>
                <el-dropdown-item @click="handleDocumentClick">
                  <el-icon>
                    <Document />
                  </el-icon>
                  {{ t("navbar.document") }}
                </el-dropdown-item>
                <el-dropdown-item @click="handleGiteeClick">
                  <el-icon>
                    <Reading />
                  </el-icon>
                  {{ t("navbar.gitee") }}
                </el-dropdown-item>
                <el-dropdown-item @click="handleTourClick">
                  <el-icon>
                    <Position />
                  </el-icon>
                  {{ t("navbar.tour") }}
                </el-dropdown-item>
                <el-dropdown-item divided @click="handlelockScreen">
                  <el-icon>
                    <Lock />
                  </el-icon>
                  {{ t("navbar.lock") }}
                </el-dropdown-item>
                <el-dropdown-item @click="logout">
                  <el-icon>
                    <SwitchButton />
                  </el-icon>
                  {{ t("navbar.logout") }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>

    <!-- 标签栏 -->
    <TagsView v-if="isShowTagsView" class="layout__tagsview" />

    <!-- 主内容区 -->
    <div :class="{
      hasTagsView: isShowTagsView,
    }" class="layout__main">
      <AppMain />
    </div>

    <!-- 引导 -->
    <Guide v-if="guideVisible" v-model="guideVisible" @skip="handleGuideExit" />

    <!-- 锁屏弹窗 -->
    <LockDialog v-if="dialogVisible" v-model="dialogVisible" />
    <teleport to="body">
      <transition name="fade-bottom" mode="out-in">
        <LockPage v-if="getIsLock" />
      </transition>
    </teleport>
  </BaseLayout>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { useLayout } from "../composables/useLayout";
import { useLayoutMenu } from "../composables/useLayoutMenu";
import BaseLayout from "./BaseLayout.vue";
import NavBar from "../components/NavBar/index.vue";
import AppLogo from "../components/AppLogo/index.vue";
import TagsView from "../components/TagsView/index.vue";
import AppMain from "../components/AppMain/index.vue";
import BasicMenu from "../components/Menu/BasicMenu.vue";
import { useUserStore, useLockStore, useSettingsStore, useAppStore } from "@/store";
import { DeviceEnum } from "@/enums/settings/device.enum";
import Guide from "@/components/Guide/index.vue";
import LockDialog from "../components/NavBar/components/LockDialog.vue";
import LockPage from "../components/NavBar/components/LockPage.vue";
import {
  ArrowRight,
  User,
  Document,
  Reading,
  Position,
  Lock,
  SwitchButton,
} from "@element-plus/icons-vue";

// 布局相关参数
const { t } = useI18n();
const router = useRouter();
const { isShowTagsView, isSidebarOpen, isShowLogo } = useLayout();
const userStore = useUserStore();
const lockStore = useLockStore();
const settingStore = useSettingsStore();
const appStore = useAppStore();
const isLogoCollapsed = computed(() => !appStore.sidebar.opened);

const userName = computed(() => userStore.basicInfo.name || "超级管理员");
const userRole = computed(
  () => userStore.basicInfo.roles?.[0]?.name || userStore.basicInfo.description || "系统管理员"
);
const userAvatar = computed(() => userStore.basicInfo.avatar || "");

const sidebarScrollbarRef = ref();
let sidebarScrollTimer: ReturnType<typeof setTimeout> | null = null;
let sidebarScrollRaf = 0;

watch(
  () => appStore.sidebar.opened,
  () => {
    const scrollbar = sidebarScrollbarRef.value;
    const wrap = scrollbar?.wrapRef as HTMLElement | undefined;
    const scrollTop = wrap ? wrap.scrollTop : 0;

    if (sidebarScrollTimer) {
      clearTimeout(sidebarScrollTimer);
    }

    sidebarScrollTimer = setTimeout(() => {
      const nextWrap = scrollbar?.wrapRef as HTMLElement | undefined;
      if (!nextWrap) return;

      let frameCount = 0;
      const restore = () => {
        nextWrap.scrollTop = scrollTop;
        frameCount += 1;
        if (frameCount < 10) {
          sidebarScrollRaf = requestAnimationFrame(restore);
        }
      };

      sidebarScrollRaf = requestAnimationFrame(restore);
    }, 320);
  }
);

onUnmounted(() => {
  if (sidebarScrollTimer) {
    clearTimeout(sidebarScrollTimer);
  }
  if (sidebarScrollRaf) {
    cancelAnimationFrame(sidebarScrollRaf);
  }
});

const guideVisible = computed({
  get: () => appStore.guideVisible,
  set: (newValue) => appStore.showGuide(newValue),
});

const dialogVisible = ref<boolean>(false);
const getIsLock = computed(() => lockStore.getLockInfo?.isLock ?? false);

function handleProfileClick() {
  router.push({ name: "Profile" });
}

function handleDocumentClick() {
  window.open("https://service.fastapiadmin.com", "_blank");
}

function handleGiteeClick() {
  window.open("https://gitee.com/tao__tao/FastapiAdmin");
}

function handleTourClick() {
  if (appStore.device === DeviceEnum.MOBILE) {
    router.push({ name: "Guide" });
  } else {
    guideVisible.value = true;
  }
}

function handleGuideExit() {
  settingStore.updateSetting("showGuide", false);
}

watch(
  () => guideVisible.value,
  (val, oldVal) => {
    if (oldVal && !val) {
      settingStore.updateSetting("showGuide", false);
    }
  }
);

const handlelockScreen = () => {
  dialogVisible.value = true;
};

function logout() {
  ElMessageBox.confirm("确定注销并退出系统吗？", "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning",
    lockScroll: false,
  })
    .then(() => {
      userStore.logout().then(() => {
        router.push(`/login`);
      });
    })
    .catch(() => {
      ElMessageBox.close();
    });
}

// 菜单相关
const { routes } = useLayoutMenu();
</script>

<style lang="scss" scoped>
.layout {
  &__sidebar {
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
    z-index: 999;
    width: $sidebar-width;
    background-color: $menu-background;
    transition: transform 0.28s ease;
    will-change: transform;

    .layout-sidebar {
      position: relative;
      display: flex;
      flex-direction: column;
      height: 100%;
      background-color: var(--menu-background);
      transition: none;

      :deep(.el-scrollbar) {
        flex: 1;
      }

      :deep(.sidebar-scroll-wrap) {
        overflow-anchor: none;
      }

      :deep(.el-scrollbar__view),
      :deep(.el-scrollbar__wrap),
      :deep(.el-menu) {
        overflow-anchor: none;
      }

      :deep(.el-menu) {
        border: none;
      }
    }
  }

  &__topbar {
    position: fixed;
    top: 0;
    right: 0;
    left: $sidebar-width;
    z-index: 1000;
    background-color: var(--el-bg-color);
    border-bottom: 1px solid var(--el-border-color-light);
    transition: left 0.28s ease;
  }

  &__tagsview {
    position: fixed;
    top: $navbar-height;
    right: 0;
    left: $sidebar-width;
    z-index: 999;
    height: $tags-view-height;
    overflow: visible;
    transition: left 0.28s ease;
  }

  &__main {
    position: relative;
    height: 100%;
    margin-left: $sidebar-width;
    margin-top: $navbar-height;
    overflow-y: auto;
    transition: margin-left 0.28s ease;

    &.hasTagsView {
      margin-top: calc($navbar-height + $tags-view-height);
    }

    .fixed-header {
      position: sticky;
      top: 0;
      z-index: 9;
      transition: width 0.28s;
    }
  }
}

.sidebar-footer {
  padding: 12px 18px;
  border-top: 1px solid #eceff5;
}

.sidebar-user {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 2px;
  background: transparent;
  border: none;
  border-radius: 0;
  box-shadow: none;
  cursor: pointer;

  &__avatar {
    flex-shrink: 0;
  }

  &__info {
    flex: 1;
    overflow: hidden;
  }

  &__name {
    font-size: 15px;
    font-weight: 600;
    color: #1f2430;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__role {
    margin-top: 2px;
    font-size: 12px;
    color: #9aa0ad;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__arrow {
    color: #b8becb;
    font-size: 16px;
  }
}

/* 移动端样式 */
.mobile {
  .layout__sidebar {
    width: $sidebar-width !important;
    transition:
      transform 0.28s,
      width 0s;
  }

  &.hideSidebar {
    .layout__sidebar {
      transform: translateX(-$sidebar-width);
    }
  }

  &.openSidebar {
    .layout__sidebar {
      transform: translateX(0);
    }
  }

  .layout__main {
    margin-left: 0 !important;
  }

  .layout__topbar {
    left: 0;
  }

  .layout__tagsview {
    left: 0;
  }
}
</style>

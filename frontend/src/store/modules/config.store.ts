import { store } from "@/store";
import ParamsAPI, { ConfigTable } from "@/api/module_system/params";

interface ConfigState {
  // 网站信息
  sys_web_title: ConfigTable;
  sys_web_version: ConfigTable;
  sys_web_description: ConfigTable;
  // 网站图标
  sys_login_background: ConfigTable;
  sys_web_favicon: ConfigTable;
  sys_web_logo: ConfigTable;
  // 安全隐私配置
  sys_keep_record: ConfigTable;
  sys_web_clause: ConfigTable;
  sys_web_copyright: ConfigTable;
  sys_web_privacy: ConfigTable;
  sys_git_code: ConfigTable;
  sys_help_doc: ConfigTable;
  // 接口安全配置
  white_api_list_path: ConfigTable;
  ip_black_list: ConfigTable;
  // 演示环境配置
  demo_enable: ConfigTable;
  ip_white_list: ConfigTable;
}

export const useConfigStore = defineStore("config", {
  state: () => ({
    configData: {} as ConfigState, // 存储系统配置
    isConfigLoaded: false, // 标记配置是否已加载
  }),

  actions: {
    async getConfig() {
      try {
        const response = await ParamsAPI.getInitConfig();
        // 检查响应数据是否存在且为数组
        if (response?.data?.data && Array.isArray(response.data.data)) {
          response.data.data.forEach((item: ConfigTable) => {
            // 确保所有配置项都正确映射到 configData
            if (item.config_value !== undefined) {
              this.configData[item.config_key as keyof ConfigState] = item;
            }
          });
        }
        this.isConfigLoaded = true;
      } catch (error) {
        console.error("获取系统配置失败:", error);
        // 即使失败也标记为已加载，避免阻塞应用启动
        this.isConfigLoaded = true;
      }
    },
  },
  persist: true,
});

export function useConfigStoreHook() {
  return useConfigStore(store);
}

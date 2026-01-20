# 数据集管理模块 - 安装说明

本模块实现了鲁棒性评估系统使用手册中的数据集管理部分功能，包括大文件分片上传、断点续传和数据集分析等功能。

## 已创建文件

### 1. API 文件
- `frontend/src/api/module_dataset/dataset.ts` - 数据集管理 API 接口定义

### 2. 页面和组件
- `frontend/src/views/module_dataset/dataset/index.vue` - 数据集管理主页面
- `frontend/src/views/module_dataset/dataset/components/DatasetUpload.vue` - 数据集上传组件
- `frontend/src/views/module_dataset/dataset/components/DatasetAnalysis.vue` - 数据集分析组件

## 安装步骤

### 1. 安装依赖

在 `frontend` 目录下运行以下命令安装 spark-md5 库(用于计算文件哈希值):

```bash
cd frontend
pnpm install spark-md5
pnpm install @types/spark-md5 -D
```

### 2. 配置路由

需要在路由配置中添加数据集管理路由。这通常由后端动态返回菜单路由,但如果需要手动添加,可以参考以下配置:

```typescript
{
  path: '/dataset',
  component: Layout,
  redirect: '/dataset/index',
  meta: { title: '数据集管理', icon: 'database' },
  children: [
    {
      path: 'index',
      name: 'DatasetManagement',
      component: () => import('@/views/module_dataset/dataset/index.vue'),
      meta: { title: '数据集管理', icon: 'database', keepAlive: true }
    }
  ]
}
```

### 3. 权限配置

确保后端已配置以下权限:

- `module_dataset:upload:init` - 上传初始化
- `module_dataset:upload:chunk` - 分片上传
- `module_dataset:upload:complete` - 上传完成
- `module_dataset:upload:resume` - 断点续传
- `module_dataset:dataset:query` - 查询数据集列表
- `module_dataset:dataset:detail` - 获取数据集详情
- `module_dataset:dataset:update` - 更新数据集
- `module_dataset:dataset:delete` - 删除数据集
- `module_dataset:dataset:analyze` - 数据集分析
- `module_dataset:dataset:preview` - 数据集预览
- `module_dataset:dataset:statistics` - 数据集统计

## 功能说明

### 1. 数据集上传 (DatasetUpload.vue)

**功能特性:**
- ✅ 支持大文件(最大 100GB)分片上传
- ✅ 支持拖拽上传和点击选择
- ✅ 自动计算文件 MD5 哈希值
- ✅ 支持断点续传(网络中断后可继续上传)
- ✅ 支持秒传(文件已存在时直接跳过上传)
- ✅ 实时显示上传进度、速度和剩余时间
- ✅ 上传暂停/继续/取消功能
- ✅ 详细的上传日志

**使用流程:**
1. 用户选择或拖拽文件
2. 自动提取数据集名称(可编辑)
3. 系统计算文件哈希值
4. 初始化上传会话
5. 分片上传(每片 5MB)
6. 上传完成后自动合并和验证
7. 跳转到数据集分析页面

### 2. 数据集分析 (DatasetAnalysis.vue)

**功能特性:**
- ✅ 自动分析数据集模态类型(图像/音频/视频/文本等)
- ✅ 统计样本数量和类别数量
- ✅ 显示分析进度动画
- ✅ 数据集预览(前 5 个样本)
- ✅ 分析结果可视化展示

**分析结果包括:**
- 模态类型识别
- 样本数量统计
- 类别数量统计
- 文件格式信息
- 样本预览列表

### 3. 数据集管理主页面 (index.vue)

**功能特性:**
- ✅ 统计卡片展示(总数据集、已完成、上传中、总存储)
- ✅ Tab 切换(数据集上传、数据集列表、数据集分析)
- ✅ 数据集列表查询(支持名称、模态类型、上传状态筛选)
- ✅ 数据集详情查看
- ✅ 数据集编辑
- ✅ 数据集删除(可选择是否删除存储文件)
- ✅ 快速跳转到分析页面

## 样式参考

界面样式参考了 `鲁棒性评估8.html` 中的设计:
- 采用渐变色背景和卡片阴影
- 统一的圆角和间距设计
- 响应式布局
- 现代化的动画效果
- Element Plus 组件库风格

## 后端 API 对接

所有 API 接口已在 `dataset.ts` 中定义,对应后端路由:
- POST `/dataset/data/upload/init` - 上传初始化
- POST `/dataset/data/upload/chunk` - 分片上传
- POST `/dataset/data/upload/complete` - 上传完成
- POST `/dataset/data/upload/resume` - 断点续传查询
- GET `/dataset/data/list` - 数据集列表
- GET `/dataset/data/detail/{id}` - 数据集详情
- PUT `/dataset/data/update/{id}` - 更新数据集
- DELETE `/dataset/data/delete` - 删除数据集
- POST `/dataset/data/analyze/{id}` - 启动分析
- GET `/dataset/data/analyze/status/{id}` - 查询分析状态
- GET `/dataset/data/preview/{id}` - 数据集预览
- GET `/dataset/data/statistics` - 统计信息

## 注意事项

1. **文件大小限制:** 前端限制最大 100GB,需确保后端和 Nginx 配置也支持大文件上传
2. **分片大小:** 默认 5MB 每片,可根据实际情况调整
3. **哈希计算:** 大文件哈希计算可能耗时较长,已添加进度提示
4. **断点续传:** 依赖后端保存上传状态,确保后端正确实现
5. **权限控制:** 所有接口都需要相应权限,确保权限配置正确

## 技术栈

- Vue 3 Composition API
- TypeScript
- Element Plus
- Spark-MD5 (文件哈希计算)
- Axios (HTTP 请求)
- Pinia (状态管理)

## 后续优化建议

1. 添加文件加密上传支持
2. 支持多文件同时上传
3. 添加上传队列管理
4. 完善数据集预览功能(图像缩略图、音频波形等)
5. 添加数据集版本管理
6. 支持数据集导出和下载
7. 添加数据集质量评估报告生成

## 问题排查

如遇到问题,请检查:
1. 是否正确安装了 spark-md5 依赖
2. 后端 API 是否正常运行
3. 权限配置是否正确
4. 浏览器控制台是否有错误信息
5. 网络请求是否成功(查看 Network 面板)

## 联系方式

如有问题,请联系开发团队或提交 Issue。

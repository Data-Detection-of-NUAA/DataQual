frontend/src/views/module_application/dqtest/
├── index.vue                 # 主页面（基于HTML转换）
├── components/               # 子组件
│   ├── DatasetSelector.vue   # 数据集选择
│   ├── ModelTrainer.vue      # 模型训练  
│   ├── StrategySelector.vue  # 策略选择
│   ├── ParameterConfig.vue   # 参数配置
│   ├── MetricsConfig.vue     # 指标配置
│   ├── RunControl.vue        # 运行控制
│   └── ResultDashboard.vue   # 结果展示
└── hooks/                    # 组合式API钩子
    ├── useWebSocket.ts       # WebSocket连接
    └── useRobustnessTask.ts  # 任务管理
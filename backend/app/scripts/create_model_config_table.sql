-- 模型配置表 SQL 创建语句
-- 数据库: MySQL 8.0+

CREATE TABLE IF NOT EXISTS `model_config` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `model_name` VARCHAR(100) NOT NULL UNIQUE COMMENT '模型名称(唯一标识)',
    `display_name` VARCHAR(100) NOT NULL COMMENT '显示名称',
    `model_version` VARCHAR(50) NOT NULL DEFAULT '1.0.0' COMMENT '模型版本号',
    `supported_modalities` VARCHAR(255) NOT NULL COMMENT '适用模态列表(逗号分隔)',
    `supported_task_types` VARCHAR(512) NOT NULL COMMENT '适用任务类型列表(逗号分隔)',
    `description` TEXT NOT NULL COMMENT '模型简介',
    `architecture_summary` VARCHAR(500) DEFAULT NULL COMMENT '架构简要说明',
    `pretrained_weights` JSON DEFAULT NULL COMMENT '预训练权重信息(JSON格式)',
    `default_train_config` JSON NOT NULL COMMENT '默认训练配置(JSON格式)',
    `performance_metrics` JSON DEFAULT NULL COMMENT '性能指标参考(JSON格式)',
    `hardware_requirements` JSON DEFAULT NULL COMMENT '硬件要求(JSON格式)',
    `framework` VARCHAR(50) NOT NULL DEFAULT 'PyTorch' COMMENT '深度学习框架',
    `framework_version` VARCHAR(50) DEFAULT NULL COMMENT '框架版本要求',
    `model_code_path` VARCHAR(512) DEFAULT NULL COMMENT '模型代码路径',
    `config_template_path` VARCHAR(512) DEFAULT NULL COMMENT '配置模板文件路径',
    `priority` INT NOT NULL DEFAULT 0 COMMENT '推荐优先级(数值越大优先级越高)',
    `status` VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '模型状态(active/inactive/deprecated)',
    `usage_count` INT NOT NULL DEFAULT 0 COMMENT '使用次数统计',
    `tags` VARCHAR(255) DEFAULT NULL COMMENT '标签(逗号分隔)',
    `reference_url` VARCHAR(512) DEFAULT NULL COMMENT '参考文档或论文链接',
    `remarks` TEXT DEFAULT NULL COMMENT '备注信息',
    `created_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `created_by` INT DEFAULT NULL COMMENT '创建人ID',
    `updated_by` INT DEFAULT NULL COMMENT '更新人ID',
    INDEX `idx_model_status` (`status`),
    INDEX `idx_model_name` (`model_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模型配置表';

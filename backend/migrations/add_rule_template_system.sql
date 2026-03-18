-- =====================================================
-- 规则模板与法规解析系统 - 数据库迁移脚本
-- 版本: 1.0.0
-- 日期: 2026-03-11
-- =====================================================

-- 1. 创建规则模板表
CREATE TABLE IF NOT EXISTS `audit_rule_template` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `template_code` VARCHAR(100) NOT NULL UNIQUE COMMENT '模板编码（唯一）',
    `template_name` VARCHAR(200) NOT NULL COMMENT '模板名称',
    `template_category` VARCHAR(50) NOT NULL COMMENT '模板分类：field_validation/format_check/business_rule/data_quality等',
    `template_description` TEXT COMMENT '模板描述（详细说明该模板的用途）',
    `parameters_schema` JSON NOT NULL COMMENT '参数定义（JSON Schema格式），定义实例化时需要哪些参数',
    `validation_template` JSON NOT NULL COMMENT '验证逻辑模板配置',
    `default_severity` VARCHAR(20) DEFAULT 'warning' COMMENT '默认严重级别：error/warning/info',
    `tags` JSON COMMENT '模板标签（用于分类和搜索）',
    `is_active` INT DEFAULT 1 COMMENT '是否启用：1-启用，0-禁用',
    `remark` TEXT COMMENT '备注',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_template_code` (`template_code`),
    INDEX `idx_template_category` (`template_category`),
    INDEX `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审计规则模板表 - 用于规则实例化';

-- 2. 修改审计规则表，添加模板关联字段
ALTER TABLE `audit_rule`
ADD COLUMN `template_id` INT NULL COMMENT '关联的规则模板ID（如果是从模板实例化而来）' AFTER `remark`,
ADD COLUMN `instance_parameters` JSON NULL COMMENT '实例化参数（如果是从模板实例化，存储具体的参数值）' AFTER `template_id`,
ADD COLUMN `regulation_id` INT NULL COMMENT '关联的法规ID（如果是从法规解析生成）' AFTER `instance_parameters`,
ADD COLUMN `auto_generated` INT DEFAULT 0 COMMENT '是否自动生成：1-AI自动生成，0-手动创建' AFTER `regulation_id`;

-- 添加外键约束（可选，根据实际需求）
-- ALTER TABLE `audit_rule`
-- ADD CONSTRAINT `fk_rule_template` FOREIGN KEY (`template_id`) REFERENCES `audit_rule_template`(`id`) ON DELETE SET NULL,
-- ADD CONSTRAINT `fk_rule_regulation` FOREIGN KEY (`regulation_id`) REFERENCES `audit_regulation`(`id`) ON DELETE SET NULL;

-- 添加索引
ALTER TABLE `audit_rule`
ADD INDEX `idx_template_id` (`template_id`),
ADD INDEX `idx_regulation_id` (`regulation_id`),
ADD INDEX `idx_auto_generated` (`auto_generated`);

-- 3. 完成
SELECT '数据库迁移完成！' AS status;

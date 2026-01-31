-- 添加审计管理菜单的SQL脚本
-- 使用前请先查询当前sys_menu表的最大ID,并根据实际情况调整下面的ID值

-- 1. 添加审计管理父菜单 (假设父菜单ID从1000开始,请根据实际情况调整)
INSERT INTO sys_menu (
    id, name, type, `order`, permission, icon, route_name, route_path, component_path,
    redirect, hidden, keep_alive, always_show, title, params, affix, parent_id, status, description,
    created_time, updated_time
) VALUES (
    1000, '审计管理', 1, 8, NULL, 'el-icon-DocumentChecked', 'Audit', '/audit', NULL,
    '/application/audit/rule', 0, 1, 0, '审计管理', NULL, 0, NULL, '0', '数据合规审计系统',
    NOW(), NOW()
);

-- 2. 添加审计规则子菜单
INSERT INTO sys_menu (
    id, name, type, `order`, permission, icon, route_name, route_path, component_path,
    redirect, hidden, keep_alive, always_show, title, params, affix, parent_id, status, description,
    created_time, updated_time
) VALUES (
    1001, '审计规则', 2, 1, 'module_application:audit:rule:query', 'el-icon-Notebook', 'AuditRule', '/application/audit/rule', 'module_application/audit/rule/index',
    NULL, 0, 1, 0, '审计规则', NULL, 0, 1000, '0', '审计规则管理',
    NOW(), NOW()
);

-- 3. 添加审计规则的权限按钮
INSERT INTO sys_menu (id, name, type, `order`, permission, route_name, route_path, component_path, status, keep_alive, hidden, always_show, title, affix, parent_id, description, created_time, updated_time)
VALUES
(1002, '创建审计规则', 3, 1, 'module_application:audit:rule:create', NULL, NULL, NULL, '0', 1, 0, 0, '创建审计规则', 0, 1001, '创建审计规则', NOW(), NOW()),
(1003, '更新审计规则', 3, 2, 'module_application:audit:rule:update', NULL, NULL, NULL, '0', 1, 0, 0, '更新审计规则', 0, 1001, '更新审计规则', NOW(), NOW()),
(1004, '删除审计规则', 3, 3, 'module_application:audit:rule:delete', NULL, NULL, NULL, '0', 1, 0, 0, '删除审计规则', 0, 1001, '删除审计规则', NOW(), NOW()),
(1005, '批量修改审计规则状态', 3, 4, 'module_application:audit:rule:patch', NULL, NULL, NULL, '0', 1, 0, 0, '批量修改审计规则状态', 0, 1001, '批量修改审计规则状态', NOW(), NOW()),
(1006, '审计规则详情', 3, 5, 'module_application:audit:rule:detail', NULL, NULL, NULL, '0', 1, 0, 0, '审计规则详情', 0, 1001, '审计规则详情', NOW(), NOW()),
(1007, '查询审计规则', 3, 6, 'module_application:audit:rule:query', NULL, NULL, NULL, '0', 1, 0, 0, '查询审计规则', 0, 1001, '查询审计规则', NOW(), NOW());

-- 4. 添加审计任务子菜单
INSERT INTO sys_menu (
    id, name, type, `order`, permission, icon, route_name, route_path, component_path,
    redirect, hidden, keep_alive, always_show, title, params, affix, parent_id, status, description,
    created_time, updated_time
) VALUES (
    1010, '审计任务', 2, 2, 'module_application:audit:task:query', 'el-icon-Operation', 'AuditTask', '/application/audit/task', 'module_application/audit/task/index',
    NULL, 0, 1, 0, '审计任务', NULL, 0, 1000, '0', '审计任务管理',
    NOW(), NOW()
);

-- 5. 添加审计任务的权限按钮
INSERT INTO sys_menu (id, name, type, `order`, permission, route_name, route_path, component_path, status, keep_alive, hidden, always_show, title, affix, parent_id, description, created_time, updated_time)
VALUES
(1011, '创建审计任务', 3, 1, 'module_application:audit:task:create', NULL, NULL, NULL, '0', 1, 0, 0, '创建审计任务', 0, 1010, '创建审计任务', NOW(), NOW()),
(1012, '更新审计任务', 3, 2, 'module_application:audit:task:update', NULL, NULL, NULL, '0', 1, 0, 0, '更新审计任务', 0, 1010, '更新审计任务', NOW(), NOW()),
(1013, '删除审计任务', 3, 3, 'module_application:audit:task:delete', NULL, NULL, NULL, '0', 1, 0, 0, '删除审计任务', 0, 1010, '删除审计任务', NOW(), NOW()),
(1014, '上传法规文件', 3, 4, 'module_application:audit:task:upload', NULL, NULL, NULL, '0', 1, 0, 0, '上传法规文件', 0, 1010, '上传法规文件', NOW(), NOW()),
(1015, 'AI匹配规则', 3, 5, 'module_application:audit:task:ai_match', NULL, NULL, NULL, '0', 1, 0, 0, 'AI匹配规则', 0, 1010, 'AI匹配规则', NOW(), NOW()),
(1016, '确认规则', 3, 6, 'module_application:audit:task:confirm', NULL, NULL, NULL, '0', 1, 0, 0, '确认规则', 0, 1010, '确认规则', NOW(), NOW()),
(1017, '执行审计', 3, 7, 'module_application:audit:task:execute', NULL, NULL, NULL, '0', 1, 0, 0, '执行审计', 0, 1010, '执行审计', NOW(), NOW()),
(1018, '下载报告', 3, 8, 'module_application:audit:task:download', NULL, NULL, NULL, '0', 1, 0, 0, '下载报告', 0, 1010, '下载报告', NOW(), NOW()),
(1019, '审计任务详情', 3, 9, 'module_application:audit:task:detail', NULL, NULL, NULL, '0', 1, 0, 0, '审计任务详情', 0, 1010, '审计任务详情', NOW(), NOW()),
(1020, '查询审计任务', 3, 10, 'module_application:audit:task:query', NULL, NULL, NULL, '0', 1, 0, 0, '查询审计任务', 0, 1010, '查询审计任务', NOW(), NOW());

-- 6. 为超级管理员角色分配审计管理权限
-- 注意:请根据实际的角色ID调整下面的role_id(通常超级管理员的ID为1)
INSERT INTO sys_role_menus (role_id, menu_id)
SELECT 1, id FROM sys_menu WHERE id BETWEEN 1000 AND 1020;

-- 查询插入结果
SELECT COUNT(*) as '插入的菜单数量' FROM sys_menu WHERE id BETWEEN 1000 AND 1020;

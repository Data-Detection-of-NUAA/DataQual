-- 更新审计模块的菜单路径
-- 将 module_audit 更新为 module_application/audit

-- 更新权限字符串
UPDATE sys_menu
SET permission = REPLACE(permission, 'module_audit:', 'module_application:audit:')
WHERE permission LIKE 'module_audit:%';

-- 更新组件路径
UPDATE sys_menu
SET component_path = REPLACE(component_path, 'module_audit/', 'module_application/audit/')
WHERE component_path LIKE 'module_audit/%';

-- 更新路由路径
UPDATE sys_menu
SET route_path = REPLACE(route_path, '/audit/', '/application/audit/')
WHERE route_path LIKE '/audit/%';

-- 查看更新结果
SELECT id, menu_name, route_path, component_path, permission
FROM sys_menu
WHERE permission LIKE '%audit%'
   OR component_path LIKE '%audit%'
   OR route_path LIKE '%audit%';

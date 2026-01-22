#!/bin/bash
# MySQL数据库备份脚本
# 用于架构调整前备份数据库

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}   数据库备份工具 - 批次0${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# 生成备份文件名（时间戳）
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="database_backup_${BACKUP_DATE}.sql"

# 数据库配置（从.env文件读取或手动设置）
DB_HOST="localhost"
DB_PORT="3306"
DB_USER="root"
DB_NAME="fastapiadmin"

echo -e "${YELLOW}备份配置：${NC}"
echo "  数据库主机: ${DB_HOST}:${DB_PORT}"
echo "  数据库名称: ${DB_NAME}"
echo "  数据库用户: ${DB_USER}"
echo "  备份文件名: ${BACKUP_FILE}"
echo ""

# 提示输入密码
echo -e "${YELLOW}请输入数据库密码：${NC}"
read -s DB_PASSWORD
echo ""

# 执行备份
echo -e "${YELLOW}正在备份数据库...${NC}"
mysqldump -h "${DB_HOST}" -P "${DB_PORT}" -u "${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}" > "${BACKUP_FILE}" 2>&1

# 检查备份是否成功
if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo -e "${GREEN}✅ 数据库备份成功！${NC}"
    echo -e "${GREEN}   文件: ${BACKUP_FILE}${NC}"
    echo -e "${GREEN}   大小: ${BACKUP_SIZE}${NC}"
    echo ""
    echo -e "${YELLOW}备份文件路径：${NC}"
    echo -e "${GREEN}   $(pwd)/${BACKUP_FILE}${NC}"
    echo ""
    echo -e "${YELLOW}恢复命令（如需回滚）：${NC}"
    echo -e "${GREEN}   mysql -h ${DB_HOST} -P ${DB_PORT} -u ${DB_USER} -p ${DB_NAME} < ${BACKUP_FILE}${NC}"
else
    echo -e "${RED}❌ 数据库备份失败！${NC}"
    echo -e "${RED}   请检查数据库连接配置${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${GREEN}   备份完成！${NC}"
echo -e "${YELLOW}========================================${NC}"

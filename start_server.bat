@echo off
REM FastAPI Admin 启动脚本
REM 使用 Conda base 环境（Python 3.11）

echo ========================================
echo FastAPI Admin 启动脚本
echo ========================================
echo.

cd /d "%~dp0backend"

echo 当前目录: %CD%
echo Python 环境: Conda base (Python 3.11)
echo.

echo 正在启动服务...
echo.

REM 设置环境变量
set ENVIRONMENT=dev

REM 使用 conda run 启动服务
conda run -n base --no-capture-output python main.py run --env=dev

pause

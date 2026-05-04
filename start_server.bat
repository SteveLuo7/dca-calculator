@echo off
chcp 65001 > nul
echo ========================================
echo 定投收益计算器 - 本地开发服务器
echo ========================================
echo.

REM 检查Python是否可用
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] 找到Python环境
    set PYTHON_CMD=python
    goto :check_dependencies
)

REM 检查py命令是否可用
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] 找到Python环境 (py命令)
    set PYTHON_CMD=py
    goto :check_dependencies
)

REM 检查Conda是否可用
where conda >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [INFO] 找到Conda环境
    echo [提示] 请先激活你的Conda环境
    echo.
    conda env list
    echo.
    echo 使用方法: conda activate your_env_name
    pause
    exit /b 1
)

echo [ERROR] 未找到Python环境
echo 请安装Python或激活Conda环境
pause
exit /b 1

:check_dependencies
echo.
echo [检查] 检查依赖包...
%PYTHON_CMD% -c "import fastapi" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 未安装FastAPI
    echo 正在安装依赖...
    cd backend
    pip install -r requirements.txt
    cd ..
)

echo [OK] 依赖检查完成
echo.
echo [启动] 正在启动后端服务器...
echo 后端地址: http://localhost:8000
echo 前端地址: http://localhost:8000
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

cd backend
%PYTHON_CMD% -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause

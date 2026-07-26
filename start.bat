@echo off
chcp 65001 >nul
title 个人数据管家

echo ================================
echo    个人数据管家 v1.0
echo ================================
echo.
echo 访问地址：http://localhost:5000
echo 默认账号：admin / admin123
echo.

cd /d "%~dp0backend"

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

REM 检查依赖
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装依赖...
    python -m pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
    if errorlevel 1 (
        echo [错误] 依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
)

echo [启动] 服务启动中...
start http://localhost:5000
python app.py
pause

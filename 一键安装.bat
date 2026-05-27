@echo off
chcp 65001 >nul
title NebulaCraft 一键安装

echo.
echo ========================================
echo      NebulaCraft v7.0 一键安装
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python
    echo       正在打开 Python 下载页面...
    start https://www.python.org/downloads/
    echo       请安装 Python 3.10+ 后重新运行本脚本
    pause
    exit /b 1
)
echo [OK] Python 已就绪

:: 安装依赖
echo [安装] 正在安装依赖...
pip install requests Pillow PyPDF2 python-docx pandas openpyxl edge-tts cryptography -q
echo [OK] 依赖安装完成

:: 检查 Ollama
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [提示] 未检测到 Ollama
    echo       Ollama 是运行 AI 模型必需的
    echo       正在打开 Ollama 下载页面...
    start https://ollama.com/download/windows
    echo       请安装 Ollama 后重新运行本脚本
    pause
    exit /b 1
)
echo [OK] Ollama 已就绪

:: 下载模型
echo [下载] 正在下载 AI 模型（约 1GB，请耐心等待）...
ollama pull qwen2.5:1.5b
echo [OK] 模型下载完成

:: 创建必要目录
mkdir data\output 2>nul
mkdir data\shares 2>nul
mkdir data\notes 2>nul
mkdir data\more 2>nul

echo.
echo ========================================
echo       安装完成！
echo ========================================
echo.
echo   启动方式：
echo   1. 双击「启动.bat」
echo   2. 或运行 python server/main.py
echo.
echo   访问: http://localhost:8889
echo ========================================
echo.
pause
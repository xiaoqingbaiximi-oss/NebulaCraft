@echo off
cd /d E:\NebulaCraft
:loop
echo [%time%] 启动 NebulaCraft...
python server/main.py
echo [%time%] 服务器已停止，3秒后重启...
timeout /t 3 >nul
goto loop
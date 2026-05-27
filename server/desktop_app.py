"""
NebulaCraft 桌面应用包装
系统托盘 + 打包支持
"""
import os
import sys
import threading
import webbrowser
import subprocess
import time

# 启动服务器
def start_server():
    from server.main import run_server
    run_server()

# 尝试创建托盘图标
def create_tray():
    try:
        import pystray
        from PIL import Image, ImageDraw
        
        # 创建一个简单的图标
        icon = Image.new('RGB', (64, 64), color=(108, 92, 231))
        draw = ImageDraw.Draw(icon)
        draw.text((16, 20), "NC", fill='white')
        
        menu = pystray.Menu(
            pystray.MenuItem("打开 NebulaCraft", lambda: webbrowser.open("http://localhost:8889")),
            pystray.MenuItem("查看状态", lambda: os.system("start http://localhost:8889/health")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", lambda: on_exit(icon)),
        )
        
        icon = pystray.Icon("NebulaCraft", icon, "NebulaCraft", menu)
        icon.run()
    except ImportError:
        print("[Desktop] pystray 未安装，跳过托盘图标")
        print("[Desktop] 服务器运行中，访问 http://localhost:8889")
        print("[Desktop] 按 Ctrl+C 停止")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

def on_exit(icon):
    icon.stop()
    os._exit(0)

if __name__ == "__main__":
    print("🌌 NebulaCraft Desktop Starting...")
    
    # 启动服务器线程
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # 等服务器启动
    time.sleep(2)
    
    # 自动打开浏览器
    webbrowser.open("http://localhost:8889")
    
    # 创建托盘
    create_tray()
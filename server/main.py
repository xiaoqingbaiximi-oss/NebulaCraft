# server/main.py
import sys
import os
import webbrowser
from http.server import HTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.config import HOST, PORT, VERSION, DATA_DIR
from server.handler import Handler
from server.utils.helpers import get_local_ip
from server.services.database import init_db


def _start_http_server():
    """启动 HTTP 服务器的核心逻辑"""
    os.makedirs(DATA_DIR, exist_ok=True)
    init_db()

    print(f"""
╔══════════════════════════════════════════╗
║   🌌 NebulaCraft v{VERSION}                 ║
║   本地全能AI工作站                        ║
║   📡 http://localhost:{PORT}              ║
║   📡 http://{get_local_ip()}:{PORT}      ║
╚══════════════════════════════════════════╝
""")

    try:
        webbrowser.open(f"http://localhost:{PORT}")
    except:
        pass

    server = HTTPServer((HOST, PORT), Handler)
    return server


def run_server():
    """桌面应用入口：启动服务器并保持运行"""
    server = _start_http_server()
    print("🚀 服务器已启动，按 Ctrl+C 停止\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 已停止")
        server.shutdown()


def main():
    """命令行入口（功能与 run_server 相同）"""
    run_server()


# 启动热文件夹监控
try:
    from server.services.watcher import Watcher
    watcher = Watcher()
    watcher.start()
except Exception as e:
    print(f"⚠️ 热文件夹监控启动失败: {e}")


if __name__ == "__main__":
    main()
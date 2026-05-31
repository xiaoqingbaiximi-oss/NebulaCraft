# server/services/watcher.py

class Watcher:
    """热文件夹监控服务"""
    def __init__(self):
        self._running = False

    def start(self):
        """启动监控"""
        self._running = True
        print("[Watcher] 热文件夹监控已启动（占位）")

    def stop(self):
        """停止监控"""
        self._running = False
        print("[Watcher] 热文件夹监控已停止")

    def is_running(self):
        return self._running
"""远程访问隧道服务"""
import os
import json
import subprocess
import threading


class TunnelService:
    def __init__(self):
        self.active = False
        self.url = ""
        self.type = ""

    def start_ngrok(self, port=8889):
        """启动 ngrok 隧道"""
        try:
            # 检测 ngrok
            result = subprocess.run(["ngrok", "version"], capture_output=True, text=True)
            if result.returncode != 0:
                return {"ok": False, "error": "ngrok 未安装。下载: https://ngrok.com"}

            # 启动 ngrok
            self.active = True
            self.type = "ngrok"

            def run():
                process = subprocess.Popen(
                    ["ngrok", "http", str(port), "--log=stdout"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                # 读取公网 URL
                import re
                for line in process.stdout:
                    match = re.search(r"url=(\S+\.ngrok\S+)", line)
                    if match:
                        self.url = match.group(1)
                        print(f"🌐 公网访问: {self.url}")
                        break

            thread = threading.Thread(target=run, daemon=True)
            thread.start()

            return {"ok": True, "message": "ngrok 启动中，请稍候...", "type": "ngrok"}

        except FileNotFoundError:
            return {"ok": False, "error": "ngrok 未安装"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def status(self):
        return {
            "ok": True,
            "active": self.active,
            "url": self.url,
            "type": self.type,
            "tips": "安装 ngrok 后可使用公网访问: https://ngrok.com/download",
        }


tunnel = TunnelService()
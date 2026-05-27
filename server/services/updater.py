"""自动更新检测服务"""
import json
import time
import threading
import requests

# GitHub Release API
GITHUB_API = "https://api.github.com/repos/yourusername/NebulaCraft/releases/latest"
CURRENT_VERSION = "7.0.0"


class Updater:
    def __init__(self):
        self.latest_version = CURRENT_VERSION
        self.update_available = False
        self.update_url = ""
        self.update_notes = ""
        self.last_check = 0

    def check(self):
        """检查更新"""
        if time.time() - self.last_check < 3600:  # 1小时内不重复检查
            return self._status()

        self.last_check = time.time()
        try:
            resp = requests.get(GITHUB_API, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                self.latest_version = data.get("tag_name", CURRENT_VERSION).lstrip("v")
                self.update_url = data.get("html_url", "")
                self.update_notes = data.get("body", "")[:500]

                # 比较版本
                if self._compare_versions(self.latest_version, CURRENT_VERSION) > 0:
                    self.update_available = True
                    print(f"🆕 发现新版本: v{self.latest_version}")
                else:
                    print(f"✅ 已是最新版本: v{CURRENT_VERSION}")
        except:
            pass

        return self._status()

    def _status(self):
        return {
            "ok": True,
            "current": CURRENT_VERSION,
            "latest": self.latest_version,
            "update_available": self.update_available,
            "update_url": self.update_url,
            "update_notes": self.update_notes[:200],
        }

    def _compare_versions(self, v1, v2):
        """比较版本号"""
        try:
            parts1 = [int(x) for x in v1.split(".")]
            parts2 = [int(x) for x in v2.split(".")]
            for i in range(max(len(parts1), len(parts2))):
                a = parts1[i] if i < len(parts1) else 0
                b = parts2[i] if i < len(parts2) else 0
                if a > b:
                    return 1
                if a < b:
                    return -1
            return 0
        except:
            return 0


updater = Updater()
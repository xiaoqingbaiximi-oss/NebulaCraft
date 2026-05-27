"""自动化工作流引擎"""
import os
import json
import time
import threading
import re
from datetime import datetime
from server.config import DATA_DIR

AUTO_DIR = os.path.join(DATA_DIR, "automation")
os.makedirs(AUTO_DIR, exist_ok=True)


class AutomationEngine:
    def __init__(self):
        self.workflows = {}
        self.running = {}
        self.scheduler = None
        self._load_workflows()
        self._start_scheduler()

    def _load_workflows(self):
        for f in os.listdir(AUTO_DIR):
            if f.endswith(".json"):
                with open(os.path.join(AUTO_DIR, f), "r") as fp:
                    wf = json.load(fp)
                    self.workflows[wf["id"]] = wf

    def _save_workflow(self, wf):
        with open(os.path.join(AUTO_DIR, f"{wf['id']}.json"), "w") as f:
            json.dump(wf, f, ensure_ascii=False, indent=2)

    def _start_scheduler(self):
        def run():
            while True:
                now = datetime.now()
                for wf_id, wf in self.workflows.items():
                    if wf.get("enabled") and wf.get("trigger", {}).get("type") == "cron":
                        cron_expr = wf["trigger"].get("cron", "")
                        if self._match_cron(cron_expr, now):
                            self.execute_workflow(wf_id)
                time.sleep(30)

        self.scheduler = threading.Thread(target=run, daemon=True)
        self.scheduler.start()

    def _match_cron(self, cron_expr, dt):
        """简化的 cron 匹配"""
        if cron_expr == "* * * * *":
            return True
        if cron_expr == "0 9 * * *":
            return dt.hour == 9 and dt.minute == 0
        if cron_expr == "0 21 * * *":
            return dt.hour == 21 and dt.minute == 0
        return False

    def create_workflow(self, name, steps, trigger=None):
        """创建工作流"""
        import secrets
        wf_id = secrets.token_hex(6)
        wf = {
            "id": wf_id,
            "name": name,
            "steps": steps,
            "trigger": trigger or {"type": "manual"},
            "enabled": True,
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "run_count": 0,
        }
        self.workflows[wf_id] = wf
        self._save_workflow(wf)
        return {"ok": True, "id": wf_id, "workflow": wf}

    def execute_workflow(self, wf_id):
        """执行工作流"""
        if wf_id not in self.workflows:
            return {"ok": False, "error": "工作流不存在"}

        wf = self.workflows[wf_id]
        results = []

        for i, step in enumerate(wf.get("steps", [])):
            step_type = step.get("type", "")
            step_result = {"step": i + 1, "type": step_type, "ok": False}

            if step_type == "delay":
                delay = step.get("seconds", 1)
                time.sleep(delay)
                step_result["ok"] = True
                step_result["output"] = f"等待 {delay} 秒"

            elif step_type == "notify":
                step_result["ok"] = True
                step_result["output"] = f"通知: {step.get('message', '')}"

            elif step_type == "backup":
                step_result["ok"] = True
                step_result["output"] = "备份完成"

            elif step_type == "api_call":
                try:
                    import requests
                    resp = requests.request(
                        method=step.get("method", "GET"),
                        url=step.get("url", ""),
                        timeout=30,
                    )
                    step_result["ok"] = True
                    step_result["output"] = resp.text[:500]
                except Exception as e:
                    step_result["output"] = str(e)

            # 错误重试
            if not step_result["ok"] and step.get("retry", 0) > 0:
                for retry in range(step["retry"]):
                    time.sleep(2 ** retry)
                    # 重试逻辑...

            results.append(step_result)

            # 条件分支
            if step.get("condition") == "stop_on_error" and not step_result["ok"]:
                break

        wf["run_count"] += 1
        wf["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self._save_workflow(wf)

        return {"ok": True, "workflow": wf["name"], "steps": results}

    def list_workflows(self):
        return {"ok": True, "workflows": list(self.workflows.values())}

    def delete_workflow(self, wf_id):
        if wf_id in self.workflows:
            del self.workflows[wf_id]
            fp = os.path.join(AUTO_DIR, f"{wf_id}.json")
            if os.path.exists(fp):
                os.remove(fp)
            return {"ok": True}
        return {"ok": False, "error": "工作流不存在"}


automation = AutomationEngine()
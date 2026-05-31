# -*- coding: utf-8 -*-
"""
NebulaCraft 电脑管家核心引擎 v2
完全自主的电脑管家：监控、优化、清理、安全、维护
所有危险操作需用户确认后才执行
"""
import os
import re
import json
import time
import shutil
import threading
import traceback
import requests
import subprocess
from datetime import datetime, timedelta
from collections import deque

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5:1.5b"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
BUTLER_DIR = os.path.join(BASE_DIR, "data", "butler")
os.makedirs(BUTLER_DIR, exist_ok=True)

STATUS_FILE = os.path.join(BUTLER_DIR, "status.json")
HEALTH_SCORE_FILE = os.path.join(BUTLER_DIR, "health_score.json")
PENDING_ACTIONS_FILE = os.path.join(BUTLER_DIR, "pending_actions.json")
EXECUTED_LOG_FILE = os.path.join(BUTLER_DIR, "executed_log.json")

REQUIRE_CONFIRMATION = [
    "kill_process", "kill_high_cpu", "clear_memory",
    "clean_disk", "clean_temp", "delete_file",
    "modify_startup", "modify_registry", "install_software",
    "uninstall_software", "enable_defender", "enable_firewall",
    "fix_network", "install_updates", "restart_service"
]

SAFE_ACTIONS = [
    "check_cpu", "check_memory", "check_disk",
    "check_startup", "check_temp_files", "check_network",
    "security_scan", "check_updates", "health_score"
]


class PCButlerV2:
    """电脑管家核心引擎 v2 - 安全版"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.status = self._load_json(STATUS_FILE, {
            "mode": "idle",
            "last_scan": None,
            "issues_found": 0,
            "issues_fixed": 0,
            "protection_enabled": False
        })
        self.pending_actions = self._load_json(PENDING_ACTIONS_FILE, [])
        self.executed_log = self._load_json(EXECUTED_LOG_FILE, [])
        self.health_history = deque(self._load_json(HEALTH_SCORE_FILE, []), maxlen=200)
        self._init_services()
    
    def _load_json(self, path, default):
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except:
            pass
        return default
    
    def _save_json(self, path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_status(self):
        self._save_json(STATUS_FILE, self.status)
    
    def _log_executed(self, action, target, result):
        log = {
            "time": datetime.now().isoformat(),
            "action": action,
            "target": target,
            "result": result,
            "confirmed": True
        }
        self.executed_log.append(log)
        self.executed_log = self.executed_log[-200:]
        self._save_json(EXECUTED_LOG_FILE, self.executed_log)
    
    def _llm_think(self, prompt, max_tokens=500, temperature=0.3):
        try:
            resp = requests.post(OLLAMA_URL, json={
                "model": MODEL, "prompt": prompt, "stream": False,
                "options": {"num_predict": max_tokens, "temperature": temperature}
            }, timeout=30)
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
        except:
            pass
        return None
    
    def _init_services(self):
        print("[Butler] 🏠 电脑管家 v2 初始化中...")
        try:
            import psutil
            self.has_psutil = True
        except ImportError:
            self.has_psutil = False
            print("[Butler] ⚠️ psutil 未安装")
        print("[Butler] ✅ 电脑管家就绪（所有操作需确认后执行）")
    
    # ===== 安全确认机制 =====
    
    def _needs_confirmation(self, action):
        return action in REQUIRE_CONFIRMATION
    
    def _create_confirmation(self, action, title, description, details=None):
        confirm_id = f"confirm_{int(time.time())}_{len(self.pending_actions)}"
        pending = {
            "id": confirm_id,
            "action": action,
            "title": title,
            "description": description,
            "details": details,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        }
        self.pending_actions.append(pending)
        self._save_json(PENDING_ACTIONS_FILE, self.pending_actions)
        return pending
    
    def get_pending_confirmations(self):
        now = datetime.now()
        self.pending_actions = [
            a for a in self.pending_actions
            if a["status"] == "pending" and datetime.fromisoformat(a["expires_at"]) > now
        ]
        self._save_json(PENDING_ACTIONS_FILE, self.pending_actions)
        return self.pending_actions
    
    def confirm_action(self, confirm_id):
        for action in self.pending_actions:
            if action["id"] == confirm_id:
                action["status"] = "confirmed"
                self._save_json(PENDING_ACTIONS_FILE, self.pending_actions)
                result = self._execute_confirmed_action(action)
                return result
        return {"ok": False, "error": "确认ID不存在或已过期"}
    
    def reject_action(self, confirm_id):
        for action in self.pending_actions:
            if action["id"] == confirm_id:
                action["status"] = "rejected"
                self._save_json(PENDING_ACTIONS_FILE, self.pending_actions)
                return {"ok": True, "message": f"已拒绝: {action['title']}"}
        return {"ok": False, "error": "确认ID不存在"}
    
    def confirm_all(self):
        results = []
        for action in self.pending_actions:
            if action["status"] == "pending":
                action["status"] = "confirmed"
                result = self._execute_confirmed_action(action)
                results.append(result)
        self._save_json(PENDING_ACTIONS_FILE, self.pending_actions)
        return {"ok": True, "results": results}
    
    def reject_all(self):
        count = 0
        for action in self.pending_actions:
            if action["status"] == "pending":
                action["status"] = "rejected"
                count += 1
        self._save_json(PENDING_ACTIONS_FILE, self.pending_actions)
        return {"ok": True, "message": f"已拒绝 {count} 个操作"}
    
    def _execute_confirmed_action(self, action):
        action_type = action["action"]
        details = action.get("details", {})
        result = self._execute_fix(action_type, details)
        self._log_executed(action_type, action.get("title", ""), result)
        return result
    
    # ===== 全面系统扫描 =====
    
    def full_scan(self):
        print("[Butler] 🔍 开始全面系统扫描...")
        self.status["mode"] = "scanning"
        self._save_status()
        
        issues = []
        all_checks = {}
        
        checks = [
            ("cpu", self._check_cpu),
            ("memory", self._check_memory),
            ("disk", self._check_disk),
            ("startup", self._check_startup),
            ("temp_files", self._check_temp_files),
            ("network", self._check_network),
            ("security", self._security_scan),
            ("updates", self._check_updates),
        ]
        
        for name, check_func in checks:
            result = check_func()
            all_checks[name] = result
            if result.get("issues"):
                issues.extend(result["issues"])
        
        self.status["last_scan"] = datetime.now().isoformat()
        self.status["issues_found"] = len(issues)
        self.status["mode"] = "idle"
        self._save_status()
        
        health_score = self._calculate_health_score(issues)
        self.health_history.append({
            "time": datetime.now().isoformat(),
            "score": health_score,
            "issues": len(issues)
        })
        self._save_json(HEALTH_SCORE_FILE, list(self.health_history))
        
        print(f"[Butler] ✅ 扫描完成: {len(issues)} 个问题, 健康评分: {health_score}/100")
        
        pending_list = []
        for issue in issues:
            if issue.get("fix_action") and self._needs_confirmation(issue.get("fix_action", "")):
                confirm = self._create_confirmation(
                    action=issue["fix_action"],
                    title=issue["title"],
                    description=issue.get("suggestion", issue["description"]),
                    details=issue
                )
                pending_list.append(confirm)
        
        return {
            "ok": True,
            "issues": issues,
            "total_issues": len(issues),
            "health_score": health_score,
            "pending_confirmations": pending_list,
            "pending_count": len(pending_list),
            "message": f"扫描完成，发现 {len(issues)} 个问题。{len(pending_list)} 个修复操作等待确认。输入'确认修复'执行，或'拒绝'跳过。",
            "checks": all_checks
        }
    
    def _check_cpu(self):
        issues = []
        cpu_percent = None
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 80:
                top = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                    try:
                        if proc.info['cpu_percent'] > 5:
                            top.append(proc.info)
                    except:
                        pass
                top.sort(key=lambda x: x['cpu_percent'], reverse=True)
                issues.append({
                    "type": "cpu_high", "severity": "high",
                    "title": f"CPU 使用率过高 ({cpu_percent}%)",
                    "description": f"当前 CPU {cpu_percent}%，可能影响电脑速度",
                    "suggestion": f"建议结束以下高占用进程: {', '.join(p['name'] for p in top[:3])}",
                    "fix_action": "kill_high_cpu",
                    "top_processes": top[:5]
                })
        except:
            pass
        return {"issues": issues, "cpu_percent": cpu_percent}
    
    def _check_memory(self):
        issues = []
        mem = None
        try:
            import psutil
            mem = psutil.virtual_memory()
            if mem.percent > 85:
                issues.append({
                    "type": "memory_high", "severity": "high",
                    "title": f"内存使用率过高 ({mem.percent}%)",
                    "description": f"已用 {mem.used/1024**3:.1f}GB / 共 {mem.total/1024**3:.1f}GB",
                    "suggestion": "建议关闭不需要的程序",
                    "fix_action": "clear_memory"
                })
        except:
            pass
        return {"issues": issues, "memory_percent": mem.percent if mem else None}
    
    def _check_disk(self):
        issues = []
        try:
            import psutil
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    if usage.percent > 85:
                        issues.append({
                            "type": "disk_full", "severity": "critical" if usage.percent > 95 else "high",
                            "title": f"磁盘 {part.device} 空间不足 ({usage.percent}%)",
                            "description": f"剩余 {usage.free/1024**3:.1f}GB",
                            "suggestion": "建议清理临时文件和回收站",
                            "fix_action": "clean_disk",
                            "drive": part.device
                        })
                except:
                    pass
        except:
            pass
        return {"issues": issues}
    
    def _check_startup(self):
        issues = []
        paths = [
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"),
            os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs\Startup"),
        ]
        count = 0
        for p in paths:
            if os.path.exists(p):
                try:
                    count += len(os.listdir(p))
                except:
                    pass
        if count > 15:
            issues.append({
                "type": "startup_too_many", "severity": "medium",
                "title": f"启动项过多 ({count} 个)",
                "description": "拖慢开机速度",
                "suggestion": "建议禁用不必要的启动项",
                "fix_action": "modify_startup"
            })
        return {"issues": issues, "startup_count": count}
    
    def _check_temp_files(self):
        issues = []
        temp_dirs = [os.path.expandvars(r"%TEMP%"), os.path.expandvars(r"%WINDIR%\Temp")]
        total = 0
        for d in temp_dirs:
            if os.path.exists(d):
                try:
                    for root, dirs, files in os.walk(d):
                        for f in files:
                            try:
                                total += os.path.getsize(os.path.join(root, f))
                            except:
                                pass
                except:
                    pass
        mb = total / 1024**2
        if mb > 500:
            issues.append({
                "type": "temp_files_large", "severity": "medium",
                "title": f"临时文件 {mb:.0f}MB",
                "description": "可以安全清理释放空间",
                "suggestion": f"清理可释放约 {mb:.0f}MB 空间",
                "fix_action": "clean_temp",
                "size_mb": mb
            })
        return {"issues": issues, "temp_size_mb": mb}
    
    def _check_network(self):
        issues = []
        try:
            result = subprocess.run(["ping", "-n", "1", "-w", "2000", "8.8.8.8"],
                                   capture_output=True, text=True, timeout=3)
            if "TTL=" not in result.stdout:
                issues.append({
                    "type": "network_issue", "severity": "high",
                    "title": "网络连接异常",
                    "description": "无法连接到互联网",
                    "suggestion": "尝试修复网络或重启路由器",
                    "fix_action": "fix_network"
                })
        except:
            pass
        return {"issues": issues}
    
    def _security_scan(self):
        issues = []
        try:
            result = subprocess.run(["powershell", "-Command", "Get-MpComputerStatus | Select-Object -ExpandProperty AntivirusEnabled"],
                                   capture_output=True, text=True, timeout=5)
            if "False" in result.stdout:
                issues.append({
                    "type": "antivirus_off", "severity": "critical",
                    "title": "杀毒软件未启用",
                    "description": "Windows Defender 未运行，电脑面临安全风险",
                    "suggestion": "建议立即启用 Windows Defender",
                    "fix_action": "enable_defender"
                })
        except:
            pass
        try:
            result = subprocess.run(["netsh", "advfirewall", "show", "allprofiles"],
                                   capture_output=True, text=True, timeout=5)
            if "State" in result.stdout and "OFF" in result.stdout:
                issues.append({
                    "type": "firewall_off", "severity": "critical",
                    "title": "防火墙已关闭",
                    "description": "系统防火墙未启用",
                    "suggestion": "建议启用防火墙保护网络安全",
                    "fix_action": "enable_firewall"
                })
        except:
            pass
        return {"issues": issues}
    
    def _check_updates(self):
        issues = []
        try:
            result = subprocess.run(["powershell", "-Command",
                "(New-Object -ComObject Microsoft.Update.Session).CreateUpdateSearcher().Search('IsInstalled=0').Updates.Count"],
                capture_output=True, text=True, timeout=10)
            count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
            if count > 3:
                issues.append({
                    "type": "updates_pending", "severity": "medium",
                    "title": f"有 {count} 个更新待安装",
                    "description": "包含安全补丁和性能改进",
                    "suggestion": "建议安装系统更新",
                    "fix_action": "install_updates"
                })
        except:
            pass
        return {"issues": issues}
    
    def _calculate_health_score(self, issues):
        base = 100
        deductions = {"critical": 20, "high": 10, "medium": 5, "low": 2}
        for i in issues:
            base -= deductions.get(i.get("severity", "low"), 2)
        return max(0, min(100, base))
    
    # ===== 执行修复 =====
    
    def _execute_fix(self, action, details):
        try:
            if action == "kill_high_cpu":
                return self._fix_kill_high_cpu(details)
            elif action == "clear_memory":
                return self._fix_clear_memory()
            elif action == "clean_disk":
                return self._fix_clean_disk()
            elif action == "clean_temp":
                return self._fix_clean_temp()
            elif action == "enable_defender":
                return self._fix_enable_defender()
            elif action == "enable_firewall":
                return self._fix_enable_firewall()
            elif action == "fix_network":
                return self._fix_network()
            elif action == "modify_startup":
                return {"ok": True, "message": "请在启动文件夹中手动清理"}
            elif action == "install_updates":
                return {"ok": True, "message": "请通过 Windows 更新手动安装"}
            else:
                return {"ok": False, "error": f"未知操作: {action}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def _fix_kill_high_cpu(self, details):
        try:
            import psutil
            killed = []
            for p in details.get("top_processes", [])[:3]:
                try:
                    proc = psutil.Process(p['pid'])
                    if proc.name() not in ["System", "svchost.exe", "explorer.exe"]:
                        proc.terminate()
                        killed.append(p['name'])
                except:
                    pass
            return {"ok": True, "killed": killed} if killed else {"ok": False, "error": "没有可安全结束的进程"}
        except:
            return {"ok": False, "error": "psutil 未安装"}
    
    def _fix_clear_memory(self):
        try:
            subprocess.run(["taskkill", "/F", "/IM", "explorer.exe"], capture_output=True)
            time.sleep(1)
            subprocess.run(["explorer.exe"])
            return {"ok": True, "message": "已刷新资源管理器"}
        except:
            return {"ok": False, "error": "清理失败"}
    
    def _fix_clean_disk(self):
        try:
            subprocess.run(["cleanmgr", "/sagerun:1"], capture_output=True, timeout=60)
            return {"ok": True, "message": "磁盘清理已启动"}
        except:
            return {"ok": False, "error": "磁盘清理启动失败"}
    
    def _fix_clean_temp(self):
        cleaned = 0
        for d in [os.path.expandvars(r"%TEMP%"), os.path.expandvars(r"%WINDIR%\Temp")]:
            if os.path.exists(d):
                try:
                    for item in os.listdir(d):
                        try:
                            p = os.path.join(d, item)
                            if os.path.isfile(p):
                                cleaned += os.path.getsize(p)
                                os.remove(p)
                            elif os.path.isdir(p):
                                shutil.rmtree(p, ignore_errors=True)
                        except:
                            pass
                except:
                    pass
        return {"ok": True, "cleaned_mb": round(cleaned/1024**2, 1)}
    
    def _fix_enable_defender(self):
        try:
            subprocess.run(["powershell", "-Command", "Set-MpPreference -DisableRealtimeMonitoring $false"],
                         capture_output=True, timeout=10)
            return {"ok": True, "message": "已启用 Windows Defender"}
        except:
            return {"ok": False, "error": "启用失败"}
    
    def _fix_enable_firewall(self):
        try:
            subprocess.run(["netsh", "advfirewall", "set", "allprofiles", "state", "on"],
                         capture_output=True, timeout=5)
            return {"ok": True, "message": "已启用防火墙"}
        except:
            return {"ok": False, "error": "启用失败"}
    
    def _fix_network(self):
        try:
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True, timeout=5)
            subprocess.run(["ipconfig", "/renew"], capture_output=True, timeout=10)
            return {"ok": True, "message": "已重置网络"}
        except:
            return {"ok": False, "error": "修复失败"}
    
    # ===== 实时保护 =====
    
    def start_protection(self):
        if self.running:
            return {"ok": False, "error": "保护已在运行"}
        self.running = True
        self.status["protection_enabled"] = True
        self._save_status()
        self.thread = threading.Thread(target=self._protection_loop, daemon=True)
        self.thread.start()
        return {"ok": True, "message": "实时保护已启动"}
    
    def stop_protection(self):
        self.running = False
        self.status["protection_enabled"] = False
        self._save_status()
        return {"ok": True, "message": "实时保护已停止"}
    
    def _protection_loop(self):
        print("[Butler] 🛡️ 实时保护已启动")
        while self.running:
            try:
                import psutil
                cpu = psutil.cpu_percent(interval=1)
                mem = psutil.virtual_memory().percent
                if cpu > 90:
                    print(f"[Butler] ⚠️ CPU {cpu}% - 等待用户确认处理")
                    self._create_confirmation("kill_high_cpu", f"CPU 过高 ({cpu}%)",
                        "是否结束高占用进程？", {"top_processes": []})
                if mem > 95:
                    print(f"[Butler] ⚠️ 内存 {mem}% - 等待用户确认处理")
                    self._create_confirmation("clear_memory", f"内存不足 ({mem}%)",
                        "是否刷新资源管理器释放内存？")
            except:
                pass
            time.sleep(30)
    
    def get_status(self):
        return {
            "ok": True,
            "status": self.status,
            "pending_count": len([a for a in self.pending_actions if a["status"] == "pending"]),
            "health_history": list(self.health_history)[-10:]
        }


# 全局单例
butler = PCButlerV2()
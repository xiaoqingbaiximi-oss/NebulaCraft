# -*- coding: utf-8 -*-
"""
NebulaCraft 自主运行核心引擎
OpenCLAW 级别核心能力：
- 持续环境感知
- 自主决策与规划
- 自动纠错与重试
- 目标驱动执行
- 自我迭代优化
"""
import os
import re
import json
import time
import threading
import traceback
import requests
from datetime import datetime
from collections import deque

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5:1.5b"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CORE_DIR = os.path.join(BASE_DIR, "data", "autonomous")
os.makedirs(CORE_DIR, exist_ok=True)

GOALS_FILE = os.path.join(CORE_DIR, "active_goals.json")
DECISIONS_FILE = os.path.join(CORE_DIR, "decisions.json")
OBSERVATIONS_FILE = os.path.join(CORE_DIR, "observations.json")
ERROR_LOG_FILE = os.path.join(CORE_DIR, "error_patterns.json")
STRATEGIES_FILE = os.path.join(CORE_DIR, "strategies.json")


class AutonomousCore:
    """自主运行核心引擎"""
    
    def __init__(self):
        self.active_goals = self._load_json(GOALS_FILE, [])
        self.decisions = self._load_json(DECISIONS_FILE, [])
        self.observations = deque(self._load_json(OBSERVATIONS_FILE, []), maxlen=100)
        self.error_patterns = self._load_json(ERROR_LOG_FILE, {})
        self.strategies = self._load_json(STRATEGIES_FILE, {})
        self.running = False
        self.thread = None
        self.last_action_time = None
        self.idle_counter = 0
    
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
    
    def _llm_think(self, prompt, max_tokens=500, temperature=0.3):
        """调用 LLM 进行思考"""
        try:
            resp = requests.post(OLLAMA_URL, json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": temperature}
            }, timeout=30)
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
        except:
            pass
        return None
    
    # ===== 1. 环境感知 =====
    
    def observe(self):
        """感知当前环境状态"""
        observation = {
            "time": datetime.now().isoformat(),
            "system": self._observe_system(),
            "files": self._observe_files(),
            "errors": self._observe_errors(),
            "user_activity": self._observe_user_activity()
        }
        self.observations.append(observation)
        self._save_json(OBSERVATIONS_FILE, list(self.observations))
        return observation
    
    def _observe_system(self):
        """观察系统状态"""
        try:
            import psutil
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.3),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "running_processes": len(psutil.pids())
            }
        except:
            return {"error": "psutil 未安装"}
    
    def _observe_files(self):
        """观察文件变化"""
        desktop = os.path.expanduser("~/Desktop")
        try:
            files = os.listdir(desktop)
            return {
                "desktop_files": len(files),
                "recent_changes": self._get_recent_file_changes(desktop)
            }
        except:
            return {}
    
    def _get_recent_file_changes(self, path, minutes=10):
        """获取最近修改的文件"""
        recent = []
        cutoff = time.time() - minutes * 60
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.getmtime(item_path) > cutoff:
                    recent.append(item)
        except:
            pass
        return recent[-10:]
    
    def _observe_errors(self):
        """观察最近的错误"""
        return dict(list(self.error_patterns.items())[-5:])
    
    def _observe_user_activity(self):
        """感知用户活动"""
        idle_time = time.time() - self.last_action_time if self.last_action_time else 0
        return {
            "idle_seconds": int(idle_time),
            "is_idle": idle_time > 300,
            "idle_counter": self.idle_counter
        }
    
    # ===== 2. 自主决策 =====
    
    def decide(self, observation):
        """基于环境感知做出自主决策"""
        decisions = []
        
        # 检查系统健康
        sys_info = observation.get("system", {})
        if sys_info.get("cpu_percent", 0) > 80:
            decisions.append({
                "priority": "high",
                "type": "system_health",
                "action": "cpu_high",
                "message": f"CPU 使用率 {sys_info['cpu_percent']}%，需要检查",
                "suggested_tool": "shell_exec",
                "suggested_command": "tasklist | sort /R /+58"
            })
        
        if sys_info.get("memory_percent", 0) > 85:
            decisions.append({
                "priority": "high",
                "type": "system_health",
                "action": "memory_high",
                "message": f"内存使用率 {sys_info['memory_percent']}%，建议清理",
                "suggested_tool": "shell_exec",
                "suggested_command": "taskkill /F /IM chrome.exe"
            })
        
        if sys_info.get("disk_percent", 0) > 90:
            decisions.append({
                "priority": "critical",
                "type": "system_health",
                "action": "disk_full",
                "message": f"磁盘使用率 {sys_info['disk_percent']}%！需要立即清理",
                "suggested_tool": "agent",
                "suggested_action": "清理临时文件和不必要的下载"
            })
        
        # 检查文件整理
        files_info = observation.get("files", {})
        if files_info.get("desktop_files", 0) > 30:
            decisions.append({
                "priority": "low",
                "type": "file_organization",
                "action": "desktop_cluttered",
                "message": f"桌面有 {files_info['desktop_files']} 个文件，建议整理",
                "suggested_tool": "agent",
                "suggested_action": "按类型整理桌面文件到对应文件夹"
            })
        
        # 用户长时间空闲
        user_activity = observation.get("user_activity", {})
        if user_activity.get("is_idle") and user_activity.get("idle_counter", 0) == 0:
            decisions.append({
                "priority": "low",
                "type": "idle_optimization",
                "action": "user_idle",
                "message": "用户已离开，可以执行优化任务",
                "suggested_tool": "agent",
                "suggested_action": "运行系统优化和维护任务"
            })
        
        return decisions
    
    # ===== 3. 目标驱动规划 =====
    
    def plan_for_goal(self, goal):
        """为目标制定执行计划"""
        prompt = f"""你是一个任务规划器。为以下目标制定详细的执行计划。

目标：{goal}

可用工具：file_list, file_read, file_write, file_delete, shell_exec, screen_capture, browser_search, browser_open, image_gen, code_generate

输出 JSON 格式的步骤数组：
[
  {{"step": 1, "tool": "工具名", "params": {{}}, "description": "描述", "expected_result": "预期结果", "fallback": "失败时的备选方案"}},
  ...
]

如果目标不明确或无法执行，输出：{{"error": "原因"}}

JSON:"""

        response = self._llm_think(prompt, max_tokens=1000, temperature=0.2)
        if response:
            try:
                response = re.sub(r'^```(?:json)?\s*\n?', '', response)
                response = re.sub(r'\n?```\s*$', '', response)
                match = re.search(r'\[[\s\S]*\]', response)
                if match:
                    plan = json.loads(match.group())
                    if isinstance(plan, list):
                        return plan
            except:
                pass
        return None
    
    # ===== 4. 执行与纠错 =====
    
    def execute_step(self, step):
        """执行单个步骤"""
        tool = step.get("tool", "")
        params = step.get("params", {})
        
        try:
            if tool == "file_list":
                from server.services.file_operator import list_directory
                return list_directory(params.get("path", "桌面"))
            elif tool == "file_read":
                from server.services.file_operator import read_file
                return read_file(params.get("path", ""))
            elif tool == "file_write":
                from server.services.file_operator import write_file
                return write_file(params.get("path", ""), params.get("content", ""))
            elif tool == "file_delete":
                from server.services.file_operator import delete_file
                return delete_file(params.get("path", ""))
            elif tool == "shell_exec":
                from server.services.shell_executor import execute_shell
                return execute_shell(params.get("command", ""))
            elif tool == "screen_capture":
                from server.services.screen_analyzer import capture_screen
                return capture_screen()
            elif tool == "browser_search":
                from server.services.browser_controller import search_web
                return search_web(params.get("query", ""))
            elif tool == "browser_open":
                from server.services.browser_controller import open_website
                return open_website(params.get("url", ""))
            elif tool == "image_gen":
                from server.services.cloud_image import generate_image
                return generate_image(params.get("prompt", ""))
            elif tool == "code_generate":
                from server.routes.code_routes import handle as code_handle
                return code_handle({"prompt": params.get("prompt", ""), "action": "generate"})
            else:
                return {"ok": False, "error": f"未知工具: {tool}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def execute_with_retry(self, step, max_retries=3):
        """执行步骤，失败自动重试"""
        for attempt in range(max_retries):
            result = self.execute_step(step)
            
            if result.get("ok"):
                return result
            
            # 分析失败原因
            error_msg = result.get("error", "未知错误")
            step_desc = step.get("description", "")
            
            # 记录错误模式
            error_key = f"{step.get('tool')}:{type(result.get('error', '')).__name__}"
            self.error_patterns[error_key] = self.error_patterns.get(error_key, 0) + 1
            self._save_json(ERROR_LOG_FILE, self.error_patterns)
            
            print(f"[Core] 步骤失败 (尝试 {attempt+1}/{max_retries}): {step_desc} - {error_msg}")
            
            if attempt < max_retries - 1:
                # 调整策略
                fallback = step.get("fallback", "")
                if fallback:
                    print(f"[Core] 使用备选方案: {fallback}")
                    step = self._generate_fallback_step(step, error_msg)
                time.sleep(1)
        
        return {"ok": False, "error": f"重试 {max_retries} 次后仍失败"}
    
    def _generate_fallback_step(self, failed_step, error_msg):
        """生成备选步骤"""
        prompt = f"""原步骤失败：
工具：{failed_step.get('tool')}
参数：{json.dumps(failed_step.get('params', {}))}
错误：{error_msg}

请生成一个替代方案，用不同的工具或参数达到相同目的。输出 JSON：
{{"tool": "工具名", "params": {{}}, "description": "描述"}}

JSON:"""
        
        response = self._llm_think(prompt, max_tokens=300, temperature=0.3)
        if response:
            try:
                response = re.sub(r'^```(?:json)?\s*\n?', '', response)
                response = re.sub(r'\n?```\s*$', '', response)
                match = re.search(r'\{[^{}]*\}', response)
                if match:
                    new_step = json.loads(match.group())
                    new_step["description"] = f"[备选] {new_step.get('description', '')}"
                    return new_step
            except:
                pass
        return failed_step
    
    # ===== 5. 连续执行循环 =====
    
    def execute_goal(self, goal):
        """执行一个目标（计划 + 执行 + 验证 + 纠错）"""
        print(f"[Core] 🎯 开始执行目标: {goal}")
        
        # 制定计划
        plan = self.plan_for_goal(goal)
        if not plan:
            # 计划失败，尝试直接执行
            plan = [{"step": 1, "tool": "shell_exec", "params": {"command": goal}, "description": goal}]
        
        results = []
        
        for step in plan:
            step_num = step.get("step", len(results) + 1)
            desc = step.get("description", f"步骤 {step_num}")
            
            print(f"[Core] 执行步骤 {step_num}/{len(plan)}: {desc}")
            
            result = self.execute_with_retry(step)
            results.append({
                "step": step_num,
                "description": desc,
                "result": result
            })
            
            if not result.get("ok"):
                # 检查是否需要跳过继续
                if step.get("critical"):
                    print(f"[Core] 关键步骤失败，中止执行")
                    break
        
        # 验证结果
        success_count = sum(1 for r in results if r["result"].get("ok"))
        summary = self._summarize_results(goal, results)
        
        print(f"[Core] ✅ 目标完成: {success_count}/{len(plan)} 步骤成功")
        
        return {
            "ok": True,
            "goal": goal,
            "total_steps": len(plan),
            "success_steps": success_count,
            "results": results,
            "summary": summary
        }
    
    def _summarize_results(self, goal, results):
        """总结执行结果"""
        prompt = f"""目标：{goal}
执行结果：{json.dumps(results, ensure_ascii=False, indent=2)[:2000]}

请用中文简洁总结执行情况，并给出后续建议。"""
        
        summary = self._llm_think(prompt, max_tokens=200, temperature=0.5)
        return summary or f"完成 {sum(1 for r in results if r['result'].get('ok'))}/{len(results)} 步骤"
    
    # ===== 6. 自主运行循环 =====
    
    def autonomous_loop(self):
        """自主运行主循环"""
        print("[Core] 🧠 自主运行核心已启动")
        self.running = True
        observation_interval = 10  # 每 10 秒观察一次
        last_observation_time = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # 定期观察环境
                if current_time - last_observation_time > observation_interval:
                    observation = self.observe()
                    last_observation_time = current_time
                    
                    # 基于观察做决策
                    decisions = self.decide(observation)
                    
                    for decision in decisions:
                        if decision["priority"] in ["critical", "high"]:
                            print(f"[Core] ⚠️ 自主决策: {decision['message']}")
                            
                            # 自动执行高优先级决策
                            if decision.get("suggested_action"):
                                self.execute_goal(decision["suggested_action"])
                
                # 检查是否有待执行的目标
                if self.active_goals:
                    goal = self.active_goals.pop(0)
                    self._save_json(GOALS_FILE, self.active_goals)
                    self.execute_goal(goal)
                
                time.sleep(1)
                
            except Exception as e:
                print(f"[Core] 自主循环异常: {e}")
                traceback.print_exc()
                time.sleep(5)
    
    def start(self):
        """启动自主运行"""
        if self.running:
            return {"ok": False, "error": "已在运行中"}
        
        self.thread = threading.Thread(target=self.autonomous_loop, daemon=True)
        self.thread.start()
        return {"ok": True, "message": "自主运行核心已启动"}
    
    def stop(self):
        """停止自主运行"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        return {"ok": True, "message": "自主运行核心已停止"}
    
    def add_goal(self, goal):
        """添加目标"""
        self.active_goals.append(goal)
        self._save_json(GOALS_FILE, self.active_goals)
        
        # 如果目标看起来像高层次目标，先分解
        if len(goal) > 10 and not goal.startswith("执行"):
            plan = self.plan_for_goal(goal)
            if plan and len(plan) > 1:
                return {
                    "ok": True,
                    "message": f"目标已分解为 {len(plan)} 个步骤",
                    "plan": plan
                }
        
        return {"ok": True, "message": "目标已添加"}
    
    def get_status(self):
        """获取运行状态"""
        return {
            "ok": True,
            "running": self.running,
            "active_goals": self.active_goals,
            "observations_count": len(self.observations),
            "error_patterns": dict(list(self.error_patterns.items())[-10:]),
            "last_action": self.last_action_time
        }


# 全局单例
core = AutonomousCore()
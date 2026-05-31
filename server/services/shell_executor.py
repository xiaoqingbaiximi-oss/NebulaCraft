# -*- coding: utf-8 -*-
"""
Shell 命令执行引擎
AI 直接执行系统命令
"""
import os
import re
import json
import subprocess
import time as _time
import requests
from datetime import datetime

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5:1.5b"

# 危险命令黑名单
BLACKLIST = [
    "format", "del /f /s", "rm -rf /", "shutdown", "restart",
    "diskpart", "fdisk", "mkfs", "dd if=", ":(){ :|:& };:",
    "chmod 777 /", "wget", "curl.*|.*sh", "> /dev/sda",
]

# 命令历史
HISTORY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
HISTORY_FILE = os.path.join(HISTORY_DIR, "shell_history.json")


def _log_command(command, result):
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        else:
            history = []
        history.append({
            "command": command,
            "result": result,
            "time": datetime.now().isoformat()
        })
        history = history[-200:]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except:
        pass


def _is_dangerous(command):
    cmd_lower = command.lower()
    for pattern in BLACKLIST:
        if pattern.lower() in cmd_lower:
            return pattern
    return None


def execute_shell(command, timeout=30):
    """执行 Shell 命令"""
    if not command or not command.strip():
        return {"ok": False, "error": "命令为空"}
    
    # 安全检查
    dangerous = _is_dangerous(command)
    if dangerous:
        return {
            "ok": False,
            "error": f"危险命令被拦截: {dangerous}",
            "blocked": True,
            "command": command
        }
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="ignore"
        )
        
        output = result.stdout.strip()
        error = result.stderr.strip()
        
        response = {
            "ok": True,
            "command": command,
            "stdout": output[:5000] if output else "",
            "stderr": error[:1000] if error else "",
            "returncode": result.returncode,
            "success": result.returncode == 0
        }
        
        _log_command(command, "success" if result.returncode == 0 else f"exit code: {result.returncode}")
        return response
        
    except subprocess.TimeoutExpired:
        _log_command(command, "timeout")
        return {"ok": False, "error": f"命令执行超时 ({timeout}s): {command}"}
    except Exception as e:
        _log_command(command, f"error: {e}")
        return {"ok": False, "error": str(e)}


def execute_python(code, timeout=10):
    """执行 Python 代码"""
    try:
        # 在受限的命名空间中执行
        restricted_globals = {
            "__builtins__": {
                "print": print,
                "len": len,
                "range": range,
                "int": int,
                "str": str,
                "float": float,
                "list": list,
                "dict": dict,
                "bool": bool,
                "sum": sum,
                "min": min,
                "max": max,
                "sorted": sorted,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "abs": abs,
                "round": round,
                "type": type,
                "isinstance": isinstance,
                "json": json,
                "os": None,  # 禁止 os
                "subprocess": None,  # 禁止 subprocess
                "eval": None,  # 禁止 eval
                "exec": None,  # 禁止 exec
                "open": None,  # 禁止 open
            }
        }
        
        # 捕获输出
        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            exec(code, restricted_globals)
            output = sys.stdout.getvalue()
            return {
                "ok": True,
                "code": code,
                "output": output[:5000] if output else "代码执行完毕（无输出）"
            }
        finally:
            sys.stdout = old_stdout
            
    except Exception as e:
        return {"ok": False, "error": str(e), "code": code}


def ai_shell_operation(user_message):
    """AI 理解用户的 Shell 操作意图"""
    
    # 先检查是否是 Python 代码执行
    python_patterns = [
        r'(?:执行|运行|跑)\s*(?:python|代码|这段)\s*(?:代码)?[：:]*\s*(.+)',
        r'(?:用python|python)\s*(?:执行|运行)?[：:]*\s*(.+)',
    ]
    for pattern in python_patterns:
        match = re.search(pattern, user_message, re.IGNORECASE)
        if match:
            code = match.group(1).strip()
            return execute_python(code)
    
    # 快速匹配常见命令
    quick_patterns = [
        (r'(?:打开|启动|运行)\s*(?:应用|程序|软件)?\s*(.+)', 'start {}'),
        (r'(?:查看|显示)\s*(?:IP|ip|网络|地址)', 'ipconfig'),
        (r'(?:查看|显示)\s*(?:进程|任务)', 'tasklist'),
        (r'(?:查看|显示)\s*(?:端口)', 'netstat -an'),
        (r'(?:查看|显示)\s*(?:系统信息)', 'systeminfo'),
        (r'(?:ping|测试连接)\s*(.+)', 'ping {}'),
        (r'(?:创建文件夹|新建目录|mkdir)\s*(.+)', 'mkdir {}'),
        (r'(?:删除文件夹|删除目录|rmdir)\s*(.+)', 'rmdir /s {}'),
        (r'(?:复制文件|拷贝|copy)\s*(.+?)\s*(?:到|to)\s*(.+)', 'copy {} {}'),
        (r'(?:移动文件|移动|move)\s*(.+?)\s*(?:到|to)\s*(.+)', 'move {} {}'),
        (r'(?:环境变量|path)', 'echo %PATH%'),
        (r'(?:关机)', 'shutdown /s /t 60'),
        (r'(?:取消关机)', 'shutdown /a'),
        (r'(?:重启)', 'shutdown /r /t 60'),
    ]
    
    for pattern, cmd_template in quick_patterns:
        match = re.search(pattern, user_message, re.IGNORECASE)
        if match:
            groups = match.groups()
            try:
                command = cmd_template.format(*groups)
            except:
                command = cmd_template
            print(f"[Shell] 快速匹配: {command}")
            return execute_shell(command)
    
    # 用 LLM 生成命令
    prompt = f"""你是一个命令行助手。根据用户需求，生成对应的 Windows CMD 命令。

用户需求：{user_message}

规则：
1. 只输出命令本身，不要解释
2. 不要用 rm -rf, format, shutdown 等危险命令
3. 如果是搜索文件用 dir，查看内容用 type
4. 如果无法生成合适命令，回复 NONE

命令："""

    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL, "prompt": prompt, "stream": False,
            "options": {"num_predict": 200, "temperature": 0}
        }, timeout=10)
        if resp.status_code == 200:
            command = resp.json().get("response", "").strip()
            command = re.sub(r'^```[\w]*\n?', '', command)
            command = re.sub(r'\n?```$', '', command)
            command = command.strip()
            if command and command.upper() != "NONE":
                print(f"[Shell] LLM 生成: {command}")
                return execute_shell(command)
    except Exception as e:
        print(f"[Shell] LLM 失败: {e}")
    
    return {"ok": False, "error": "无法理解命令意图"}


def get_shell_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return {"ok": True, "history": json.load(f)[-30:]}
    except:
        pass
    return {"ok": True, "history": []}
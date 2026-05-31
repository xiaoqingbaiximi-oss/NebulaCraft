# -*- coding: utf-8 -*-
"""
Agent 任务编排引擎 v2
流式进度反馈 + 记忆系统 + 自学习
"""
import json
import re
import requests
import threading
from datetime import datetime

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5:1.5b"

TASK_HISTORY = []


def _plan_task(user_message):
    prompt = f"""你是一个任务规划器。将用户需求分解为可执行的步骤。

可用工具：
- file_list: 列出目录 {{"path": "路径"}}
- file_read: 读取文件 {{"path": "路径"}}
- file_write: 创建文件 {{"path": "路径", "content": "内容"}}
- file_delete: 删除文件 {{"path": "路径"}}
- shell_exec: 执行命令 {{"command": "命令"}}
- screen_capture: 截图 {{}}
- browser_search: 搜索 {{"query": "关键词"}}
- browser_open: 打开网址 {{"url": "网址"}}
- image_gen: AI生图 {{"prompt": "描述"}}
- code_generate: 生成代码 {{"prompt": "需求"}}
- ai_chat: 对话 {{"message": "内容"}}

用户需求：{user_message}

输出 JSON 数组（如果只需一步也输出数组）：
[{{"step": 1, "tool": "工具名", "params": {{参数}}, "description": "步骤描述"}}]

如果无法执行，输出：{{"error": "原因"}}
JSON:"""

    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL, "prompt": prompt, "stream": False,
            "options": {"num_predict": 800, "temperature": 0.2}
        }, timeout=20)
        if resp.status_code == 200:
            raw = resp.json().get("response", "").strip()
            raw = re.sub(r'^```(?:json)?\s*\n?', '', raw)
            raw = re.sub(r'\n?```\s*$', '', raw)
            match = re.search(r'\[[\s\S]*\]', raw)
            if match:
                return json.loads(match.group())
            match = re.search(r'\{[\s\S]*\}', raw)
            if match:
                obj = json.loads(match.group())
                if "error" in obj:
                    return obj
    except Exception as e:
        print(f"[Agent] 规划失败: {e}")
    return None


def _execute_step(step):
    tool = step.get("tool", "")
    params = step.get("params", {})
    description = step.get("description", "")
    
    print(f"[Agent] 执行步骤 {step.get('step')}: {description}")
    
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
            return search_web(params.get("query", ""), params.get("engine", "google"))
        elif tool == "browser_open":
            from server.services.browser_controller import open_website
            return open_website(params.get("url", ""))
        elif tool == "image_gen":
            from server.services.cloud_image import generate_image
            return generate_image(params.get("prompt", ""))
        elif tool == "code_generate":
            from server.routes.code_routes import handle as code_handle
            return code_handle({"prompt": params.get("prompt", ""), "action": "generate"})
        elif tool == "ai_chat":
            messages = [{"role": "user", "content": params.get("message", "")}]
            from server.services.ollama import chat
            reply = chat(messages, timeout=60)
            return {"ok": True, "reply": reply}
        else:
            return {"ok": False, "error": f"未知工具: {tool}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def execute_agent_task(user_message):
    """执行 Agent 任务（非流式）"""
    from server.services.memory import memory
    
    plan = _plan_task(user_message)
    
    if not plan:
        memory.learn_from_failure(user_message, "无法规划任务")
        return {"ok": False, "error": "无法规划任务"}
    
    if isinstance(plan, dict) and "error" in plan:
        memory.learn_from_failure(user_message, plan["error"])
        return {"ok": False, "error": plan["error"]}
    
    if not isinstance(plan, list):
        return {"ok": False, "error": "规划结果格式错误"}
    
    results = []
    success_count = 0
    
    for step in plan:
        result = _execute_step(step)
        result["_step"] = step.get("step")
        result["_description"] = step.get("description", "")
        results.append(result)
        if result.get("ok"):
            success_count += 1
            memory.learn_from_success(step.get("description", ""), "成功")
        else:
            memory.learn_from_failure(step.get("description", ""), result.get("error", ""))
    
    # 记录习惯
    memory.record_habit(user_message)
    memory.update_context(topic=user_message)
    
    # 生成总结
    summary_prompt = f"""用户需求：{user_message}
执行结果：
{json.dumps(results, ensure_ascii=False, indent=2)[:2000]}

请用自然语言总结执行结果。"""

    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL, "prompt": summary_prompt, "stream": False,
            "options": {"num_predict": 300, "temperature": 0.5}
        }, timeout=15)
        summary = resp.json().get("response", "").strip() if resp.status_code == 200 else f"完成: {success_count}/{len(plan)}"
    except:
        summary = f"完成: {success_count}/{len(plan)}"
    
    # 获取主动建议
    suggestions = memory.get_suggestions(user_message)
    if suggestions:
        summary += "\n\n💡 建议：" + "\n".join(suggestions)
    
    task_record = {
        "task": user_message, "steps": len(plan), "success": success_count,
        "results": results, "summary": summary, "time": datetime.now().isoformat()
    }
    TASK_HISTORY.append(task_record)
    if len(TASK_HISTORY) > 50:
        TASK_HISTORY.pop(0)
    
    return {
        "ok": True,
        "task": user_message,
        "steps_total": len(plan),
        "steps_success": success_count,
        "results": results,
        "summary": summary
    }


def execute_agent_task_stream(user_message):
    """执行 Agent 任务（流式，逐步返回进度）"""
    from server.services.memory import memory
    
    plan = _plan_task(user_message)
    
    if not plan:
        memory.learn_from_failure(user_message, "无法规划任务")
        yield {"type": "error", "message": "无法规划任务"}
        return
    
    if isinstance(plan, dict) and "error" in plan:
        memory.learn_from_failure(user_message, plan["error"])
        yield {"type": "error", "message": plan["error"]}
        return
    
    if not isinstance(plan, list):
        yield {"type": "error", "message": "规划结果格式错误"}
        return
    
    total = len(plan)
    yield {"type": "plan", "steps": total, "description": f"规划了 {total} 个步骤"}
    
    results = []
    success_count = 0
    
    for i, step in enumerate(plan):
        step_num = step.get("step", i + 1)
        desc = step.get("description", f"步骤 {step_num}")
        
        yield {"type": "step_start", "step": step_num, "total": total, "description": desc}
        
        result = _execute_step(step)
        result["_step"] = step_num
        result["_description"] = desc
        results.append(result)
        
        if result.get("ok"):
            success_count += 1
            memory.learn_from_success(desc, "成功")
            yield {"type": "step_done", "step": step_num, "total": total, "success": True, "description": desc}
        else:
            memory.learn_from_failure(desc, result.get("error", ""))
            yield {"type": "step_done", "step": step_num, "total": total, "success": False, 
                   "description": desc, "error": result.get("error", "")}
    
    # 记录习惯
    memory.record_habit(user_message)
    memory.update_context(topic=user_message)
    
    # 生成总结
    summary_prompt = f"""用户需求：{user_message}
执行结果：{json.dumps(results, ensure_ascii=False, indent=2)[:2000]}
请用一句话总结。"""

    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL, "prompt": summary_prompt, "stream": False,
            "options": {"num_predict": 200, "temperature": 0.5}
        }, timeout=15)
        summary = resp.json().get("response", "").strip() if resp.status_code == 200 else f"完成: {success_count}/{total}"
    except:
        summary = f"完成: {success_count}/{total}"
    
    suggestions = memory.get_suggestions(user_message)
    if suggestions:
        summary += "\n\n💡 " + " | ".join(suggestions)
    
    yield {"type": "done", "steps_total": total, "steps_success": success_count, 
           "summary": summary, "results": results}


def get_task_history():
    return {"ok": True, "history": TASK_HISTORY[-20:]}


def get_memory_status():
    from server.services.memory import memory
    return {"ok": True, "memory": memory.summarize_user()}
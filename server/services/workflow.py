"""
工作流引擎
支持: 触发器 → 条件 → 动作 → 结果
"""
import json
import time
import threading
import os
from datetime import datetime
from server.config import DATA_DIR

WORKFLOW_DIR = os.path.join(DATA_DIR, "workflows")
WORKFLOW_FILE = os.path.join(WORKFLOW_DIR, "workflows.json")
os.makedirs(WORKFLOW_DIR, exist_ok=True)

_workflows = []
_running = False
_lock = threading.Lock()


def _load():
    global _workflows
    try:
        if os.path.exists(WORKFLOW_FILE):
            with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
                _workflows = json.load(f)
    except:
        _workflows = []


def _save():
    with open(WORKFLOW_FILE, "w", encoding="utf-8") as f:
        json.dump(_workflows, f, ensure_ascii=False, indent=2)


def _execute_node(node, context):
    """执行单个节点"""
    node_type = node.get("type", "")
    config = node.get("config", {})

    if node_type == "ai_chat":
        from server.services.ollama import chat
        prompt = config.get("prompt", "").format(**context)
        model = config.get("model", "")
        try:
            result = chat([{"role": "user", "content": prompt}], model=model, timeout=120)
            context[node.get("id", "result")] = result
            return {"ok": True, "output": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    elif node_type == "web_search":
        from server.services.search_web import search
        query = config.get("query", "").format(**context)
        try:
            results = search(query)
            context[node.get("id", "result")] = results
            return {"ok": True, "output": results}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    elif node_type == "save_file":
        path = config.get("path", "").format(**context)
        content = config.get("content", "").format(**context)
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"ok": True, "output": f"Saved to {path}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    elif node_type == "send_email":
        # 预留邮件发送
        return {"ok": True, "output": "Email sent (simulated)"}

    elif node_type == "delay":
        seconds = config.get("seconds", 1)
        time.sleep(seconds)
        return {"ok": True, "output": f"Waited {seconds}s"}

    elif node_type == "condition":
        field = config.get("field", "")
        operator = config.get("operator", "equals")
        value = config.get("value", "")
        actual = context.get(field, "")
        if operator == "equals":
            return {"ok": actual == value, "output": str(actual == value)}
        elif operator == "contains":
            return {"ok": value in str(actual), "output": str(value in str(actual))}
        else:
            return {"ok": True, "output": "true"}

    elif node_type == "generate_image":
        from server.services.image_gen import image_gen
        prompt = config.get("prompt", "").format(**context)
        try:
            result = image_gen.generate(prompt, width=512, height=512)
            context[node.get("id", "result")] = result
            return {"ok": True, "output": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    elif node_type == "knowledge_search":
        from server.services.knowledge import kb
        query = config.get("query", "").format(**context)
        collection = config.get("collection", "default")
        try:
            result = kb.search(collection, query)
            context[node.get("id", "result")] = result
            return {"ok": True, "output": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    return {"ok": False, "error": f"未知节点类型: {node_type}"}


def execute_workflow(workflow, context=None):
    """执行完整工作流"""
    if context is None:
        context = {}
    nodes = workflow.get("nodes", [])
    results = []

    for i, node in enumerate(nodes):
        result = _execute_node(node, context)
        results.append({"step": i + 1, "node": node.get("name", ""), "type": node.get("type", ""), "result": result})

        # 条件节点失败则跳过下一个
        if node.get("type") == "condition" and not result.get("ok"):
            break

    return {"ok": True, "workflow": workflow.get("name", ""), "steps": len(results), "results": results, "context": context}


def _checker():
    """定时检查触发器"""
    global _running
    while _running:
        now = datetime.now()
        with _lock:
            for wf in _workflows:
                if not wf.get("enabled", True):
                    continue
                trigger = wf.get("trigger", {})
                trigger_type = trigger.get("type", "")

                if trigger_type == "schedule":
                    schedule_time = trigger.get("time", "")
                    if schedule_time:
                        try:
                            h, m = map(int, schedule_time.split(":"))
                            if now.hour == h and now.minute == m:
                                last_run = wf.get("last_run", "")
                                if last_run:
                                    last_dt = datetime.fromisoformat(last_run)
                                    if (now - last_dt).total_seconds() < 60:
                                        continue
                                threading.Thread(target=_run_workflow, args=(wf,), daemon=True).start()
                        except:
                            pass

                elif trigger_type == "interval":
                    interval = trigger.get("minutes", 60)
                    last_run = wf.get("last_run", "")
                    if last_run:
                        last_dt = datetime.fromisoformat(last_run)
                        if (now - last_dt).total_seconds() >= interval * 60:
                            threading.Thread(target=_run_workflow, args=(wf,), daemon=True).start()
        time.sleep(30)


def _run_workflow(wf):
    """后台执行工作流"""
    with _lock:
        wf["last_run"] = datetime.now().isoformat()
    result = execute_workflow(wf)
    with _lock:
        wf["last_result"] = result.get("results", [])
    _save()
    print(f"[Workflow] '{wf.get('name', '')}' executed")


def start_workflow_engine():
    global _running
    _load()
    if not _running:
        _running = True
        t = threading.Thread(target=_checker, daemon=True)
        t.start()


def add_workflow(name, trigger, nodes):
    with _lock:
        wf = {
            "id": str(int(time.time() * 1000)),
            "name": name,
            "trigger": trigger,
            "nodes": nodes,
            "enabled": True,
            "created": datetime.now().isoformat(),
            "last_run": None,
            "last_result": None,
        }
        _workflows.append(wf)
        _save()
    return {"ok": True, "workflow": wf}


def list_workflows():
    return {"ok": True, "workflows": _workflows}


def delete_workflow(wf_id):
    global _workflows
    with _lock:
        _workflows = [w for w in _workflows if w.get("id") != wf_id]
        _save()
    return {"ok": True}


def run_workflow_now(wf_id):
    for wf in _workflows:
        if wf.get("id") == wf_id:
            result = execute_workflow(wf)
            wf["last_run"] = datetime.now().isoformat()
            wf["last_result"] = result.get("results", [])
            _save()
            return result
    return {"ok": False, "error": "工作流不存在"}
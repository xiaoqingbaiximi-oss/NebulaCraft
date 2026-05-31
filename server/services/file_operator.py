# -*- coding: utf-8 -*-
"""
NebulaCraft 文件操作引擎
AI 直接读写本地文件系统
"""
import os
import re
import json
import shutil
import time as _time
import requests
from datetime import datetime

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5:1.5b"

ALLOWED_BASES = [
    os.path.expanduser("~/Desktop"),
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Pictures"),
    os.path.expanduser("~/Music"),
    os.path.expanduser("~/Videos"),
    os.path.expanduser("~/NebulaCraft"),
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
]

HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "file_ops_history.json")


def _is_path_allowed(path):
    abs_path = os.path.abspath(path)
    for base in ALLOWED_BASES:
        if abs_path.startswith(os.path.abspath(base)):
            return True
    return False


def _log_operation(op_type, path, result):
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        else:
            history = []
        history.append({"type": op_type, "path": path, "result": result, "time": datetime.now().isoformat()})
        history = history[-500:]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except:
        pass


def read_file(path):
    if not _is_path_allowed(path):
        return {"ok": False, "error": f"路径不允许: {path}"}
    if not os.path.exists(path):
        return {"ok": False, "error": f"文件不存在: {path}"}
    try:
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.py', '.js', '.html', '.css', '.txt', '.md', '.json', '.xml', '.csv', '.yaml', '.yml', '.env', '.gitignore', '.bat', '.sh']:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            _log_operation("read", path, "success")
            return {"ok": True, "path": path, "content": content, "size": len(content), "lines": content.count('\n') + 1, "type": ext}
        else:
            size = os.path.getsize(path)
            _log_operation("read", path, "success")
            return {"ok": True, "path": path, "binary": True, "size": size, "type": ext, "content": f"[二进制文件，大小: {size} bytes]"}
    except Exception as e:
        _log_operation("read", path, f"error: {e}")
        return {"ok": False, "error": str(e)}


def write_file(path, content, create_dirs=True):
    if not _is_path_allowed(path):
        return {"ok": False, "error": f"路径不允许: {path}"}
    try:
        if create_dirs:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        existed = os.path.exists(path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        _log_operation("write", path, "success")
        return {"ok": True, "path": path, "size": len(content), "action": "updated" if existed else "created"}
    except Exception as e:
        _log_operation("write", path, f"error: {e}")
        return {"ok": False, "error": str(e)}


def modify_file(path, instruction, context=""):
    if not _is_path_allowed(path):
        return {"ok": False, "error": f"路径不允许: {path}"}
    if not os.path.exists(path):
        return {"ok": False, "error": f"文件不存在: {path}"}
    read_result = read_file(path)
    if not read_result.get("ok"):
        return read_result
    original_content = read_result.get("content", "")
    file_type = read_result.get("type", "")
    prompt = f"""你是一个文件编辑器。根据修改指令，输出修改后的完整文件内容。

文件路径：{path}
文件类型：{file_type}
当前内容：{original_content[:3000]}

修改指令：{instruction}

请输出修改后的完整文件内容（不是 diff），保持原有风格和缩进："""

    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL, "prompt": prompt, "stream": False,
            "options": {"num_predict": max(len(original_content) * 2, 1000), "temperature": 0.3}
        }, timeout=60)
        if resp.status_code == 200:
            new_content = resp.json().get("response", "")
            new_content = re.sub(r'^```[\w]*\n', '', new_content)
            new_content = re.sub(r'\n```$', '', new_content)
            return write_file(path, new_content)
    except Exception as e:
        return {"ok": False, "error": f"修改失败: {e}"}


def list_directory(path=".", filter_pattern=None):
    if not _is_path_allowed(path):
        return {"ok": False, "error": f"路径不允许: {path}"}
    if not os.path.exists(path):
        return {"ok": False, "error": f"路径不存在: {path}"}
    try:
        items = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            item_info = {
                "name": item, "path": item_path,
                "type": "directory" if os.path.isdir(item_path) else "file",
                "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
                "modified": datetime.fromtimestamp(os.path.getmtime(item_path)).isoformat()
            }
            if filter_pattern:
                if re.search(filter_pattern, item):
                    items.append(item_info)
            else:
                items.append(item_info)
        items.sort(key=lambda x: (0 if x["type"] == "directory" else 1, x["name"]))
        return {"ok": True, "path": path, "items": items, "total": len(items),
                "directories": sum(1 for i in items if i["type"] == "directory"),
                "files": sum(1 for i in items if i["type"] == "file")}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def delete_file(path, safe_mode=True):
    if not _is_path_allowed(path):
        return {"ok": False, "error": f"路径不允许: {path}"}
    if not os.path.exists(path):
        return {"ok": False, "error": f"文件不存在: {path}"}
    if safe_mode:
        trash_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "trash")
        os.makedirs(trash_dir, exist_ok=True)
        dest = os.path.join(trash_dir, f"{int(_time.time())}_{os.path.basename(path)}")
        try:
            shutil.move(path, dest)
            _log_operation("delete", path, f"moved to trash: {dest}")
            return {"ok": True, "action": "trashed", "path": dest}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    else:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            _log_operation("delete", path, "permanently deleted")
            return {"ok": True, "action": "deleted", "path": path}
        except Exception as e:
            return {"ok": False, "error": str(e)}


def search_files(directory, query, recursive=True):
    if not _is_path_allowed(directory):
        return {"ok": False, "error": f"路径不允许: {directory}"}
    results = []
    try:
        if recursive:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    filepath = os.path.join(root, file)
                    result = _search_in_file(filepath, query)
                    if result:
                        results.append(result)
                    if len(results) >= 20:
                        break
        else:
            for item in os.listdir(directory):
                filepath = os.path.join(directory, item)
                if os.path.isfile(filepath):
                    result = _search_in_file(filepath, query)
                    if result:
                        results.append(result)
        return {"ok": True, "query": query, "directory": directory, "results": results, "total": len(results)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _search_in_file(filepath, query):
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in ['.py', '.js', '.html', '.css', '.txt', '.md', '.json', '.xml', '.csv', '.yaml', '.yml']:
        return None
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if query.lower() in content.lower():
            lines = content.split('\n')
            matches = []
            for i, line in enumerate(lines):
                if query.lower() in line.lower():
                    matches.append({"line": i + 1, "content": line.strip()[:200]})
            return {"path": filepath, "name": os.path.basename(filepath), "matches": matches[:5]}
    except:
        pass
    return None


def _quick_file_match(user_message):
    """快速规则匹配，不依赖 LLM"""
    msg = user_message.strip()

    # 列出目录
    list_patterns = [
        r'(?:列出|显示|查看|看看|打开)\s*(?:桌面|下载|文档|文件夹|目录)',
        r'(?:桌面|下载|文档|文件夹|目录)\s*(?:有|里)\s*(?:什么|哪些|啥)',
        r'^(?:桌面|下载|文档)$',
        r'^(?:ls|dir|list)\b',
    ]
    for pattern in list_patterns:
        if re.search(pattern, msg):
            path = _extract_path(msg) or os.path.expanduser("~/Desktop")
            print(f"[FileOp] 规则匹配: list -> {path}")
            return list_directory(path)

    # 读取文件
    read_patterns = [
        r'(?:读取|查看|打开|看看|显示|读|看)\s*(?:文件\s*)?(.+\.\w+)',
        r'^(?:cat|type)\s+(.+)',
    ]
    for pattern in read_patterns:
        match = re.search(pattern, msg)
        if match:
            path = _resolve_path(match.group(1).strip())
            print(f"[FileOp] 规则匹配: read -> {path}")
            return read_file(path)

    # 创建文件
    write_patterns = [
        r'(?:创建|新建|写|生成|写入|保存)\s*(?:文件\s*)?(.+?)\s*(?:内容|写入|数据)\s*(?:是|为|：|:)\s*(.+)',
        r'(?:创建|新建|写|生成)\s*(?:文件\s*)?(.+\.\w+)',
        r'(?:在|到)\s*(.+?)\s*(?:创建|写|保存)\s*(.+)?',
    ]
    for pattern in write_patterns:
        match = re.search(pattern, msg)
        if match:
            path = _resolve_path(match.group(1).strip())
            content = match.group(2).strip() if match.lastindex >= 2 else ""
            print(f"[FileOp] 规则匹配: write -> {path}")
            return write_file(path, content)

    # 删除文件
    delete_patterns = [
        r'(?:删除|删掉|移除|去除)\s*(?:文件\s*)?(.+\.\w+)',
        r'^(?:rm|del|delete)\s+(.+)',
    ]
    for pattern in delete_patterns:
        match = re.search(pattern, msg)
        if match:
            path = _resolve_path(match.group(1).strip())
            print(f"[FileOp] 规则匹配: delete -> {path}")
            return delete_file(path)

    # 搜索文件
    search_patterns = [
        r'(?:搜索|查找|找|grep)\s*(.+?)\s*(?:在|于|从)\s*(.+)',
        r'(.+?)\s*(?:里|中|里面)\s*(?:有没有|有)\s*(.+)',
    ]
    for pattern in search_patterns:
        match = re.search(pattern, msg)
        if match:
            query = match.group(1).strip()
            directory = _resolve_path(match.group(2).strip()) if match.lastindex >= 2 else os.path.expanduser("~/Desktop")
            print(f"[FileOp] 规则匹配: search -> {query} in {directory}")
            return search_files(directory, query)

    # 修改文件
    modify_patterns = [
        r'(?:修改|编辑|改|更新)\s*(?:文件\s*)?(.+?)\s*(?:把|将|内容)?\s*(.+)',
    ]
    for pattern in modify_patterns:
        match = re.search(pattern, msg)
        if match:
            path = _resolve_path(match.group(1).strip())
            instruction = match.group(2).strip()
            print(f"[FileOp] 规则匹配: modify -> {path}")
            return modify_file(path, instruction)

    return None


def ai_file_operation(user_message):
    """AI 理解用户的文件操作意图并执行"""

    # 先用规则快速匹配
    result = _quick_file_match(user_message)
    if result:
        return result

    # 规则匹配失败，再用 LLM
    prompt = f"""分析用户消息，只输出一个 JSON 对象。

用户消息：{user_message}

操作类型：read, write, modify, list, search, delete

输出格式：
{{"action":"list","path":"桌面"}}
{{"action":"read","path":"桌面/test.txt"}}
{{"action":"write","path":"桌面/test.txt","content":"内容"}}
{{"action":"modify","path":"桌面/test.txt","instruction":"修改说明"}}
{{"action":"delete","path":"桌面/test.txt"}}
{{"action":"search","query":"关键词","directory":"桌面"}}

直接输出JSON："""

    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL, "prompt": prompt, "stream": False,
            "options": {"num_predict": 300, "temperature": 0, "top_p": 0.1}
        }, timeout=15)
        if resp.status_code == 200:
            raw = resp.json().get("response", "").strip()
            print(f"[FileOp] LLM 返回: {raw[:200]}")
            raw = re.sub(r'^```(?:json)?\s*\n?', '', raw)
            raw = re.sub(r'\n?```\s*$', '', raw)
            raw = raw.strip()
            json_match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
            if json_match:
                try:
                    action_data = json.loads(json_match.group())
                    print(f"[FileOp] 解析成功: {action_data}")
                    return execute_action(action_data)
                except json.JSONDecodeError as e:
                    print(f"[FileOp] JSON解析失败: {e}")
    except Exception as e:
        print(f"[FileOp] LLM失败: {e}")

    return {"ok": False, "error": f"无法理解操作: {user_message}"}


def execute_action(action_data):
    action = action_data.get("action", "none")
    path = action_data.get("path", "")
    path = _resolve_path(path)
    if action == "none":
        return {"ok": False, "error": "不涉及文件操作"}
    elif action == "read":
        return read_file(path)
    elif action == "write":
        return write_file(path, action_data.get("content", ""))
    elif action == "modify":
        return modify_file(path, action_data.get("instruction", ""))
    elif action == "list":
        return list_directory(path)
    elif action == "search":
        return search_files(action_data.get("directory", path), action_data.get("query", ""))
    elif action == "delete":
        return delete_file(path)
    return {"ok": False, "error": f"未知操作: {action}"}


def _resolve_path(path):
    path_map = {
        "桌面": os.path.expanduser("~/Desktop"),
        "下载": os.path.expanduser("~/Downloads"),
        "文档": os.path.expanduser("~/Documents"),
        "图片": os.path.expanduser("~/Pictures"),
        "音乐": os.path.expanduser("~/Music"),
        "视频": os.path.expanduser("~/Videos"),
    }
    for cn, actual in path_map.items():
        if path.startswith(cn):
            path = path.replace(cn, actual, 1)
            break
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    return path


def _extract_path(msg):
    path_map = {
        "桌面": os.path.expanduser("~/Desktop"),
        "下载": os.path.expanduser("~/Downloads"),
        "文档": os.path.expanduser("~/Documents"),
        "图片": os.path.expanduser("~/Pictures"),
        "音乐": os.path.expanduser("~/Music"),
        "视频": os.path.expanduser("~/Videos"),
    }
    for cn, actual in path_map.items():
        if cn in msg:
            return actual
    return None


def get_operation_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return {"ok": True, "history": json.load(f)[-50:]}
    except:
        pass
    return {"ok": True, "history": []}
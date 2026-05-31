# -*- coding: utf-8 -*-
"""
NebulaCraft 自升级引擎
AI 修改自身代码，自动进化
"""
import os
import re
import json
import shutil
import time
import requests
from datetime import datetime

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5:1.5b"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
BACKUP_DIR = os.path.join(BASE_DIR, "data", "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)
HISTORY_FILE = os.path.join(BASE_DIR, "data", "self_update_history.json")

ALLOWED_FILES = [
    "server/config.py",
    "server/main.py",
    "server/handler.py",
    "server/routes/chat.py",
    "server/services/intent_router.py",
    "server/services/cloud_image.py",
    "server/services/file_operator.py",
    "server/services/shell_executor.py",
    "server/services/browser_controller.py",
    "server/services/screen_analyzer.py",
    "server/services/agent_executor.py",
    "server/services/memory.py",
    "index.html",
    "css/style.css",
    "js/app.js",
]


def _log_history(action, path, description):
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        else:
            history = []
        history.append({
            "action": action,
            "path": path,
            "description": description,
            "time": datetime.now().isoformat()
        })
        history = history[-200:]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except:
        pass


def _is_allowed(path):
    rel_path = os.path.relpath(path, BASE_DIR).replace("\\", "/")
    for allowed in ALLOWED_FILES:
        if rel_path == allowed or rel_path.startswith(allowed):
            return True
    return False


def _backup_file(path):
    if not os.path.exists(path):
        return None
    backup_name = f"{os.path.basename(path)}.{int(time.time())}.bak"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    shutil.copy2(path, backup_path)
    print(f"[Updater] 备份: {backup_path}")
    return backup_path


def _simple_modify(full_path, original, instruction, display_path):
    """简单直接的文本替换"""
    changes = []
    new_content = original

    # 端口修改
    port_match = re.search(r'(?:PORT|port)\s*[=:]\s*(\d+)', original)
    new_port_match = re.search(r'(\d{3,5})', instruction)
    if port_match and new_port_match:
        old_port = port_match.group(1)
        new_port = new_port_match.group(1)
        # 替换 PORT = 数字（支持多种格式）
        new_content = re.sub(r'(PORT\s*=\s*)\d+', rf'\g<1>{new_port}', original)
        new_content = re.sub(r'("PORT",\s*)\d+', rf'\g<1>{new_port}', new_content)
        changes.append(f"端口: {old_port} → {new_port}")

    if not changes:
        return {"ok": False, "error": "无法自动修改，请更具体地说明要改什么"}

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    _log_history("modify", display_path, instruction)

    return {
        "ok": True, "path": display_path, "action": "modified",
        "instruction": instruction, "changes": changes
    }

    # 模型修改：只替换 DEFAULT_MODEL = 'xxx' 这一行
    model_match = re.search(r'(?:DEFAULT_MODEL)\s*[=:]\s*["\']([^"\']+)["\']', original)
    new_model_match = re.search(r'["\']?([a-zA-Z0-9.:_-]{3,30})["\']?', instruction)
    if model_match and new_model_match:
        old_model = model_match.group(1)
        new_model = new_model_match.group(1)
        if new_model not in ['改成', '改为', '修改', '端口', '模型']:
            new_content = re.sub(
                r"(DEFAULT_MODEL\s*=\s*)'[^']*'",
                rf"\g<1>'{new_model}'",
                new_content
            )
            changes.append(f"模型: {old_model} → {new_model}")

    if not changes:
        return {"ok": False, "error": "无法自动修改，请更具体地说明要改什么（如：把端口改成 9999）"}

    # 验证修改后的内容包含关键结构
    if 'PORT' in original and 'PORT' not in new_content:
        return {"ok": False, "error": "修改失败：端口配置丢失，已自动回滚"}
    if 'DEFAULT_MODEL' in original and 'DEFAULT_MODEL' not in new_content:
        return {"ok": False, "error": "修改失败：模型配置丢失，已自动回滚"}

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    _log_history("modify", display_path, instruction)

    return {
        "ok": True, "path": display_path, "action": "modified",
        "instruction": instruction, "changes": changes
    }


def read_project_file(path):
    full_path = os.path.join(BASE_DIR, path) if not os.path.isabs(path) else path
    if not _is_allowed(full_path):
        return {"ok": False, "error": f"文件不在白名单中: {path}"}
    if not os.path.exists(full_path):
        return {"ok": False, "error": f"文件不存在: {path}"}
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"ok": True, "path": path, "content": content, "size": len(content), "lines": content.count('\n') + 1}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def modify_project_file(path, instruction):
    full_path = os.path.join(BASE_DIR, path) if not os.path.isabs(path) else path
    if not _is_allowed(full_path):
        return {"ok": False, "error": f"文件不在白名单中: {path}"}
    if not os.path.exists(full_path):
        return {"ok": False, "error": f"文件不存在: {path}"}

    _backup_file(full_path)

    with open(full_path, "r", encoding="utf-8") as f:
        original = f.read()

    # 先尝试简单替换
    simple_result = _simple_modify(full_path, original, instruction, path)
    if simple_result.get("ok"):
        return simple_result

    # 简单替换失败，用 LLM
    file_type = os.path.splitext(path)[1]
    prompt = f"""你是一个代码编辑器。根据修改指令输出修改后的完整文件内容。

文件：{path}
类型：{file_type}
当前内容：{original[:4000]}

修改指令：{instruction}

规则：
1. 输出完整文件内容，不是 diff
2. 保持原有编码风格和缩进
3. 只修改用户要求的部分
4. 不要输出任何解释

修改后的内容："""

    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL, "prompt": prompt, "stream": False,
            "options": {"num_predict": max(len(original) * 2, 2000), "temperature": 0.2}
        }, timeout=60)

        if resp.status_code == 200:
            new_content = resp.json().get("response", "")

            if not new_content or len(new_content) < 50:
                return {"ok": False, "error": "AI 返回内容为空，请重试或更具体说明修改内容"}

            new_content = re.sub(r'^```[\w]*\n', '', new_content)
            new_content = re.sub(r'\n```$', '', new_content)

            if len(new_content) < len(original) * 0.5:
                return {"ok": False, "error": "AI 生成内容不完整，请重试"}

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            _log_history("modify", path, instruction)

            return {
                "ok": True, "path": path, "action": "modified",
                "instruction": instruction,
                "original_size": len(original), "new_size": len(new_content),
                "backup": os.path.join(BACKUP_DIR, f"{os.path.basename(path)}.*.bak")
            }
        else:
            return {"ok": False, "error": f"AI 服务返回错误: HTTP {resp.status_code}"}
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "AI 服务响应超时，请重试"}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "error": "无法连接 AI 服务，请确认 Ollama 正在运行"}
    except Exception as e:
        return {"ok": False, "error": f"修改失败: {str(e)}"}


def create_project_file(path, content=None, instruction=None):
    full_path = os.path.join(BASE_DIR, path) if not os.path.isabs(path) else path
    parent = os.path.dirname(os.path.relpath(full_path, BASE_DIR))
    if not any(parent.startswith(os.path.dirname(a)) for a in ALLOWED_FILES):
        if not _is_allowed(full_path):
            return {"ok": False, "error": f"路径不在白名单中: {path}"}
    if os.path.exists(full_path):
        return {"ok": False, "error": f"文件已存在: {path}，请用修改指令"}

    if instruction and not content:
        prompt = f"""你是一个程序员。创建一个新文件。

文件路径：{path}
创建说明：{instruction}

请输出完整的文件内容（代码），不要输出任何解释。"""
        try:
            resp = requests.post(OLLAMA_URL, json={
                "model": MODEL, "prompt": prompt, "stream": False,
                "options": {"num_predict": 2000, "temperature": 0.3}
            }, timeout=60)
            if resp.status_code == 200:
                content = resp.json().get("response", "")
                content = re.sub(r'^```[\w]*\n', '', content)
                content = re.sub(r'\n```$', '', content)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    if not content:
        return {"ok": False, "error": "需要提供文件内容或创建说明"}

    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        _log_history("create", path, instruction or "创建新文件")
        return {"ok": True, "path": path, "action": "created", "size": len(content)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def ai_self_update(user_message):
    """AI 理解自升级意图"""
    msg = user_message.strip()

    # 修改端口
    if re.search(r'(?:修改|改|设置|更改|把|将)\s*(?:端口|port)', msg, re.IGNORECASE):
        port_match = re.search(r'(\d{3,5})', msg)
        if port_match:
            new_port = port_match.group(1)
            return modify_project_file(
                "server/config.py",
                f"把 PORT 的值改成 {new_port}，其他所有代码保持不变"
            )
        else:
            return {"ok": False, "error": "请指定端口号，如：把端口改成 9999"}

    # 修改模型
    if re.search(r'(?:修改|改|设置|更改|把|将)\s*(?:模型|model)', msg, re.IGNORECASE):
        model_match = re.search(r'(?:改成|改为|设置为|换成|用)\s*["\']?([a-zA-Z0-9.:_-]+)["\']?', msg)
        if model_match:
            new_model = model_match.group(1)
            return modify_project_file(
                "server/config.py",
                f"把 DEFAULT_MODEL 的值改成 '{new_model}'，其他所有代码保持不变"
            )
        else:
            return {"ok": False, "error": "请指定模型名，如：把模型改成 qwen2.5:7b"}

    # 修改特定功能
    feature_targets = [
        (r'(?:修改|改|优化|升级)\s*(?:生图|图片生成|画图)', "server/services/cloud_image.py"),
        (r'(?:修改|改|优化|升级)\s*(?:对话|聊天|chat)', "server/routes/chat.py"),
        (r'(?:修改|改|优化|升级)\s*(?:文件操作|文件)', "server/services/file_operator.py"),
        (r'(?:修改|改|优化|升级)\s*(?:命令|shell)', "server/services/shell_executor.py"),
        (r'(?:修改|改|优化|升级)\s*(?:路由|意图|intent)', "server/services/intent_router.py"),
        (r'(?:修改|改|优化|升级)\s*(?:Agent|自动化)', "server/services/agent_executor.py"),
        (r'(?:修改|改|优化|升级)\s*(?:界面|前端|UI|样式)', "index.html"),
        (r'(?:修改|改|优化|升级)\s*(?:主页|首页)', "index.html"),
        (r'(?:修改|改|优化|升级)\s*(?:浏览器)', "server/services/browser_controller.py"),
        (r'(?:修改|改|优化|升级)\s*(?:屏幕|截图)', "server/services/screen_analyzer.py"),
        (r'(?:修改|改|优化|升级)\s*(?:记忆)', "server/services/memory.py"),
    ]
    for pattern, filepath in feature_targets:
        if re.search(pattern, msg, re.IGNORECASE):
            return modify_project_file(filepath, msg)

    # 新增功能/模块
    create_match = re.search(r'(?:创建|新增|添加|新建)\s*(?:功能|插件|模块|文件|路由)?\s*(.+)', msg, re.IGNORECASE)
    if create_match:
        name = create_match.group(1).strip()
        safe_name = re.sub(r'[^\w]', '_', name).lower()
        filepath = f"server/routes/{safe_name}.py"
        return create_project_file(filepath, instruction=f"创建一个 {name} 的 API 路由模块")

    # 通用修改：让 LLM 决定
    if re.search(r'(?:修改|改|优化|升级|更新|调整)', msg):
        return _llm_decide_update(msg)

    return {"ok": False, "error": "无法确定修改目标，请具体说明（如：修改端口、优化生图、新增功能等）"}


def _llm_decide_update(user_message):
    """让 LLM 决定修改什么"""
    file_list = "\n".join(ALLOWED_FILES)
    prompt = f"""你是一个系统管理员。根据用户需求，决定修改哪个文件。

用户需求：{user_message}

可选文件：
{file_list}

输出 JSON：
{{"file": "文件路径", "instruction": "具体的修改说明"}}
如果无法确定，输出：{{"error": "原因"}}

JSON:"""

    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL, "prompt": prompt, "stream": False,
            "options": {"num_predict": 300, "temperature": 0.2}
        }, timeout=15)
        if resp.status_code == 200:
            raw = resp.json().get("response", "").strip()
            match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
                if "error" in data:
                    return {"ok": False, "error": data["error"]}
                return modify_project_file(data["file"], data["instruction"])
    except:
        pass
    return {"ok": False, "error": "无法确定修改目标，请具体说明要修改什么"}


def restart_server():
    return {"ok": True, "message": "代码已修改，请手动重启 NebulaCraft 使修改生效", "need_restart": True}


def get_update_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return {"ok": True, "history": json.load(f)[-30:]}
    except:
        pass
    return {"ok": True, "history": []}


def rollback_last():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
            if history:
                last = history[-1]
                backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith(os.path.basename(last["path"]))])
                if backups:
                    backup_path = os.path.join(BACKUP_DIR, backups[-1])
                    original_path = os.path.join(BASE_DIR, last["path"])
                    shutil.copy2(backup_path, original_path)
                    return {"ok": True, "message": f"已回滚: {last['path']}"}
        return {"ok": False, "error": "没有可回滚的修改"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
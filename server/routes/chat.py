# -*- coding: utf-8 -*-
"""
对话 API - 完整版
支持：意图识别 + 生图 + 思维导图 + 代码 + 文件 + Shell + 屏幕 + 浏览器
     + Agent + 自升级 + 系统监控 + 打包 + 电脑管家 + 自主核心
"""
import json
import re
import traceback
import threading
from server.services.ollama import chat, chat_stream, is_available
from server.services.search_web import search as web_search
from server.services.intent_router import route_intent, learn
from server.config import DEFAULT_MODEL

_sessions = {}
MAX_HISTORY = 20


def _get_history(session_id: str) -> list:
    if session_id not in _sessions:
        _sessions[session_id] = []
    return _sessions[session_id]


def _add_to_history(session_id: str, role: str, content: str):
    history = _get_history(session_id)
    history.append({"role": role, "content": content})
    if len(history) > MAX_HISTORY * 2:
        _sessions[session_id] = history[-MAX_HISTORY * 2:]


def _is_browser_intent(text):
    patterns = [
        r'打开\s*(?:网址|网站|网页)?\s*(https?://[^\s]+)',
        r'打开\s*(?:网址|网站|网页)?\s*([a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,})',
        r'(?:搜索|搜|查)\s*',
    ]
    for p in patterns:
        if re.search(p, text):
            return True
    return False


def _handle_intent(intent, cleaned_text, prompt, model, session_id):
    """根据意图自动路由到对应功能"""

    # ===== 电脑管家 =====
    if intent == "butler" or any(w in cleaned_text for w in ["管家", "优化电脑", "清理系统", "系统扫描", "电脑体检", "扫描电脑", "电脑管家"]):
        try:
            from server.services.pc_butler import butler

            if any(w in cleaned_text for w in ["启动管家", "开启管家", "打开管家", "运行管家", "开启保护"]):
                result = butler.start_protection()
            elif any(w in cleaned_text for w in ["停止管家", "关闭管家", "暂停管家", "关闭保护"]):
                result = butler.stop_protection()
            elif any(w in cleaned_text for w in ["确认修复", "确认", "同意", "执行修复", "全部确认"]):
                result = butler.confirm_all()
            elif any(w in cleaned_text for w in ["拒绝", "取消", "全部拒绝", "不修复"]):
                result = butler.reject_all()
            elif any(w in cleaned_text for w in ["一键优化", "优化", "加速"]):
                scan = butler.full_scan()
                if scan.get("pending_count", 0) > 0:
                    return {
                        "ok": True,
                        "reply": f"🔍 扫描完成，健康评分: {scan['health_score']}/100\n\n发现 {scan['total_issues']} 个问题。\n\n{scan['message']}\n\n⚠️ 需要您确认后才会执行修复。",
                        "source": "butler",
                        "data": scan,
                        "session_id": session_id,
                        "intent": "butler"
                    }
                result = scan
            elif any(w in cleaned_text for w in ["扫描", "体检", "检查"]):
                result = butler.full_scan()
            elif any(w in cleaned_text for w in ["状态", "健康", "评分"]):
                result = butler.get_status()
            elif any(w in cleaned_text for w in ["待确认", "待处理", "有什么要确认"]):
                pending = butler.get_pending_confirmations()
                if pending:
                    items = "\n".join([f"- [{p['action']}] {p['title']}: {p['description']}" for p in pending])
                    return {
                        "ok": True,
                        "reply": f"📋 待确认操作 ({len(pending)} 个):\n\n{items}\n\n输入'确认修复'执行，或'拒绝'跳过。",
                        "source": "butler",
                        "session_id": session_id,
                        "intent": "butler"
                    }
                result = {"ok": True, "message": "没有待确认的操作"}
            else:
                result = butler.full_scan()

            if result and result.get("ok"):
                if result.get("pending_count", 0) > 0:
                    return {
                        "ok": True,
                        "reply": f"🔍 扫描完成，健康评分: {result['health_score']}/100\n\n发现 {result['total_issues']} 个问题。\n\n{result.get('message', '')}",
                        "source": "butler",
                        "data": result,
                        "session_id": session_id,
                        "intent": "butler"
                    }
                return {
                    "ok": True,
                    "reply": json.dumps(result, ensure_ascii=False, indent=2),
                    "source": "butler",
                    "session_id": session_id,
                    "intent": "butler"
                }
        except Exception as e:
            print(f"[Intent] 管家失败: {e}")
            traceback.print_exc()

    # ===== AI 生图 =====
    if intent == "image_gen":
        try:
            from server.services.cloud_image import generate_image
            result = generate_image(cleaned_text)
            if result and result.get("ok"):
                return {"ok": True, "reply": f"✅ 已生成图片: {cleaned_text}", "source": "image_gen",
                        "image_url": result.get("url"), "session_id": session_id, "intent": "image_gen"}
        except Exception as e:
            print(f"[Intent] 生图失败: {e}")

    # ===== 思维导图 =====
    if intent == "mindmap":
        try:
            from server.routes.extra import handle as extra_handle
            result = extra_handle({"prompt": cleaned_text, "type": "mindmap"})
            if result and result.get("ok"):
                return {"ok": True, "reply": f"✅ 已生成思维导图: {cleaned_text}", "source": "mindmap",
                        "data": result, "session_id": session_id, "intent": "mindmap"}
        except Exception as e:
            print(f"[Intent] 思维导图失败: {e}")

    # ===== 流程图 =====
    if intent == "flowchart":
        try:
            from server.routes.extra import handle as extra_handle
            result = extra_handle({"prompt": cleaned_text, "type": "flowchart"})
            if result and result.get("ok"):
                return {"ok": True, "reply": f"✅ 已生成流程图: {cleaned_text}", "source": "flowchart",
                        "data": result, "session_id": session_id, "intent": "flowchart"}
        except Exception as e:
            print(f"[Intent] 流程图失败: {e}")

    # ===== 代码生成 =====
    if intent == "code_gen":
        try:
            from server.routes.code_routes import handle as code_handle
            result = code_handle({"prompt": cleaned_text, "action": "generate"})
            if result and result.get("ok"):
                return {"ok": True, "reply": result.get("reply", f"✅ 代码已生成"), "source": "code_gen",
                        "code": result.get("code", ""), "session_id": session_id, "intent": "code_gen"}
        except Exception as e:
            print(f"[Intent] 代码生成失败: {e}")

    # ===== 代码审查 =====
    if intent == "code_review":
        try:
            from server.routes.code_routes import handle as code_handle
            result = code_handle({"prompt": cleaned_text, "action": "review"})
            if result and result.get("ok"):
                return {"ok": True, "reply": result.get("reply", ""), "source": "code_review",
                        "session_id": session_id, "intent": "code_review"}
        except Exception as e:
            print(f"[Intent] 代码审查失败: {e}")

    # ===== 翻译 =====
    if intent == "translate":
        try:
            from server.routes.translate import handle as translate_handle
            result = translate_handle({"text": cleaned_text})
            if result and result.get("ok"):
                return {"ok": True, "reply": result.get("reply", result.get("result", "")),
                        "source": "translate", "session_id": session_id, "intent": "translate"}
        except Exception as e:
            print(f"[Intent] 翻译失败: {e}")

    # ===== 知识库 =====
    if intent == "knowledge":
        try:
            from server.routes.knowledge import handle as kb_handle
            result = kb_handle({"action": "search", "query": cleaned_text})
            if result and result.get("ok"):
                return {"ok": True, "reply": result.get("reply", str(result)), "source": "knowledge",
                        "session_id": session_id, "intent": "knowledge"}
        except Exception as e:
            print(f"[Intent] 知识库失败: {e}")

    # ===== 文件操作 =====
    if intent == "file_operation":
        try:
            from server.services.file_operator import ai_file_operation
            result = ai_file_operation(cleaned_text)
            if result and result.get("ok"):
                return {"ok": True, "reply": json.dumps(result, ensure_ascii=False, indent=2),
                        "source": "file_operation", "data": result, "session_id": session_id, "intent": "file_operation"}
            else:
                return {"ok": True, "reply": f"文件操作失败: {result.get('error', '未知错误') if result else '无结果'}",
                        "source": "file_operation", "session_id": session_id, "intent": "file_operation"}
        except Exception as e:
            print(f"[Intent] 文件操作失败: {e}")

    # ===== Shell 命令 =====
    if intent == "shell_operation":
        try:
            from server.services.shell_executor import ai_shell_operation
            result = ai_shell_operation(cleaned_text)
            if result and result.get("ok"):
                reply_text = f"✅ 命令执行成功:\n```\n{result.get('stdout', result.get('output', ''))}\n```"
                if result.get("stderr"):
                    reply_text += f"\n⚠️ 错误:\n```\n{result['stderr']}\n```"
                return {"ok": True, "reply": reply_text, "source": "shell",
                        "data": result, "session_id": session_id, "intent": "shell_operation"}
            else:
                return {"ok": True, "reply": f"命令执行失败: {result.get('error', '未知错误') if result else '无结果'}",
                        "source": "shell", "session_id": session_id, "intent": "shell_operation"}
        except Exception as e:
            print(f"[Intent] Shell 失败: {e}")

    # ===== 屏幕操作 =====
    if intent == "screen_operation":
        try:
            from server.services.screen_analyzer import ai_screen_operation
            result = ai_screen_operation(cleaned_text)
            if result and result.get("ok"):
                return {"ok": True,
                        "reply": result.get("analysis", result.get("reply", "截图完成")),
                        "source": "screen", "data": result,
                        "session_id": session_id, "intent": "screen_operation"}
        except Exception as e:
            print(f"[Intent] 屏幕失败: {e}")

    # ===== 浏览器操作 =====
    if intent == "browser_operation" or _is_browser_intent(prompt):
        try:
            from server.services.browser_controller import ai_browser_operation
            result = ai_browser_operation(cleaned_text)
            if result and result.get("ok"):
                return {"ok": True,
                        "reply": f"✅ {result.get('action', '操作完成')}: {result.get('url', result.get('query', ''))}",
                        "source": "browser", "data": result,
                        "session_id": session_id, "intent": "browser_operation"}
        except Exception as e:
            print(f"[Intent] 浏览器失败: {e}")

    # ===== Agent 多步骤 =====
    agent_keywords = ["帮我", "自动", "然后", "接着", "并且", "同时", "先.*再", "打包", "批量", "压缩"]
    is_complex = any(re.search(kw, cleaned_text) for kw in agent_keywords) if cleaned_text else False

    if is_complex or intent == "agent":
        try:
            from server.services.agent_executor import execute_agent_task
            result = execute_agent_task(cleaned_text)
            if result and result.get("ok"):
                return {"ok": True,
                        "reply": f"🤖 Agent 完成 ({result['steps_success']}/{result['steps_total']}):\n\n{result['summary']}",
                        "source": "agent", "data": result,
                        "session_id": session_id, "intent": "agent"}
        except Exception as e:
            print(f"[Intent] Agent 失败: {e}")

    # ===== 自升级 =====
    if intent == "self_update":
        try:
            print(f"[Intent] 开始自升级: {cleaned_text}")
            from server.services.self_updater import ai_self_update, restart_server
            result = ai_self_update(cleaned_text)
            print(f"[Intent] 自升级结果: {result}")
            if result and result.get("ok"):
                restart_msg = restart_server()
                return {"ok": True,
                        "reply": f"✅ 代码已修改: {result.get('path', '')}\n📝 {result.get('instruction', result.get('action', ''))}\n\n⚠️ {restart_msg.get('message', '请重启')}",
                        "source": "self_update", "data": result,
                        "session_id": session_id, "intent": "self_update"}
            else:
                error_msg = result.get('error', '未知错误') if result else '无结果'
                return {"ok": True,
                        "reply": f"自升级失败: {error_msg}",
                        "source": "self_update",
                        "session_id": session_id, "intent": "self_update"}
        except Exception as e:
            print(f"[Intent] 自升级异常: {e}")
            traceback.print_exc()

    # ===== 系统监控 =====
    if intent == "system_monitor":
        try:
            from server.services.system_monitor import ai_system_operation
            result = ai_system_operation(cleaned_text)
            if result and result.get("ok"):
                return {"ok": True,
                        "reply": json.dumps(result.get("info", result), ensure_ascii=False, indent=2),
                        "source": "system", "session_id": session_id, "intent": "system_monitor"}
        except Exception as e:
            print(f"[Intent] 系统监控失败: {e}")

    # ===== 打包发布 =====
    if intent == "publish":
        try:
            from server.services.publisher import auto_publish
            result = auto_publish()
            if result and result.get("ok"):
                return {"ok": True,
                        "reply": f"📦 打包完成 v{result['version']}\n\n" + "\n".join(f"- {s['step']}: {s['result']}" for s in result['steps']),
                        "source": "publish", "session_id": session_id, "intent": "publish"}
        except Exception as e:
            print(f"[Intent] 打包失败: {e}")

    # ===== 自主运行核心 =====
    if intent == "autonomous":
        try:
            from server.services.autonomous_core import core
            if any(w in cleaned_text for w in ["启动", "开始", "开启", "运行"]):
                result = core.start()
            elif any(w in cleaned_text for w in ["停止", "关闭", "暂停"]):
                result = core.stop()
            elif any(w in cleaned_text for w in ["状态", "查看"]):
                result = core.get_status()
            else:
                result = core.add_goal(cleaned_text)
            if result and result.get("ok"):
                return {"ok": True,
                        "reply": json.dumps(result, ensure_ascii=False, indent=2),
                        "source": "autonomous", "session_id": session_id, "intent": "autonomous"}
        except Exception as e:
            print(f"[Intent] 自主核心失败: {e}")

    # ===== 工具：二维码 =====
    if intent == "tool_qrcode":
        try:
            from server.routes.generator import handle as gen_handle
            result = gen_handle({"type": "qrcode", "text": cleaned_text})
            if result and result.get("ok"):
                return {"ok": True, "reply": f"✅ 已生成二维码: {cleaned_text}", "source": "qrcode",
                        "image_url": result.get("url"), "session_id": session_id, "intent": "tool_qrcode"}
        except Exception as e:
            print(f"[Intent] 二维码失败: {e}")

    # ===== 工具：密码生成 =====
    if intent == "tool_password":
        try:
            from server.routes.security import handle as sec_handle
            result = sec_handle({"action": "generate_password"})
            if result and result.get("ok"):
                return {"ok": True, "reply": f"🔐 生成的密码: {result.get('password', '')}",
                        "source": "password_gen", "session_id": session_id, "intent": "tool_password"}
        except Exception as e:
            print(f"[Intent] 密码生成失败: {e}")

    # ===== 工具：计算器 =====
    if intent == "tool_calc":
        try:
            from server.routes.calculator import handle as calc_handle
            result = calc_handle({"expression": cleaned_text})
            if result and result.get("ok"):
                return {"ok": True, "reply": f"计算结果: {result.get('result', '')}",
                        "source": "calculator", "session_id": session_id, "intent": "tool_calc"}
        except Exception as e:
            print(f"[Intent] 计算失败: {e}")

    return None


def handle(body: dict) -> dict:
    prompt = body.get("message", "").strip()
    model = body.get("model", DEFAULT_MODEL)
    session_id = body.get("session_id", "default")

    if not prompt:
        return {"ok": False, "error": "消息不能为空"}

    # 意图自动识别
    if not prompt.startswith("@"):
        intent_result = route_intent(prompt)
        intent = intent_result["intent"]
        cleaned_text = intent_result["cleaned_text"]
        print(f"[Chat] 意图: {intent} | 方法: {intent_result['method']} | 原文: '{prompt}' | 清理: '{cleaned_text}'")

        complex_keywords = ["帮我", "自动", "然后", "打包", "批量", "压缩", "修改", "升级", "优化", "创建", "新增",
                           "管家", "扫描", "优化", "清理", "体检", "加速", "修复", "确认", "拒绝"]
        is_complex = any(re.search(kw, prompt) for kw in complex_keywords)

        if intent != "chat" or is_complex:
            intent_response = _handle_intent(intent, cleaned_text, prompt, model, session_id)
            if intent_response:
                try:
                    from server.services.memory import memory
                    memory.update_context(topic=prompt)
                except:
                    pass
                try:
                    from server.services.feedback_learner import record_feedback
                    record_feedback(prompt, intent, intent_response)
                except:
                    pass
                return intent_response

    messages = [{"role": "user", "content": prompt}]
    reply = chat(messages, model, timeout=120)

    try:
        from server.services.memory import memory
        memory.update_context(topic=prompt)
    except:
        pass

    return {"ok": True, "reply": reply, "source": "ai", "references": [], "session_id": session_id}


def handle_search(body: dict) -> dict:
    prompt = body.get("message", "").strip()
    if not prompt:
        return {"ok": False, "error": "请输入搜索内容"}
    results = web_search(prompt)
    return {"ok": True, "reply": str(results)[:500], "source": "search", "references": results[:5] if results else []}


def handle_stream(body: dict):
    prompt = body.get("message", "").strip()
    model = body.get("model", DEFAULT_MODEL)

    if not prompt:
        return lambda: iter(["data: " + json.dumps({"error": "消息不能为空"}) + "\n\n"])

    if not prompt.startswith("@"):
        intent_result = route_intent(prompt)
        intent = intent_result["intent"]
        cleaned_text = intent_result["cleaned_text"]

        complex_keywords = ["帮我", "自动", "然后", "打包", "批量", "压缩", "修改", "升级", "优化", "创建", "新增",
                           "管家", "扫描", "优化", "清理", "体检", "加速", "修复", "确认", "拒绝"]
        is_complex = any(re.search(kw, prompt) for kw in complex_keywords)

        if intent != "chat" or is_complex:
            intent_response = _handle_intent(intent, cleaned_text, prompt, model, "default")
            if intent_response:
                def gen_wrapper():
                    yield f"data: {json.dumps({'chunk': intent_response.get('reply', '')})}\n\n"
                    yield f"data: {json.dumps({'done': True, 'intent': intent})}\n\n"
                return gen_wrapper

    def gen():
        full_reply = ""
        try:
            for chunk in chat_stream([{"role": "user", "content": prompt}], model):
                full_reply += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return gen
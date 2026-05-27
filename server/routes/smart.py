"""
智能指令中心 - 增强版
支持: 16个预设角色 / 自定义角色 / 多轮对话 / 模板管理
"""
import json
import os
from server.services.ollama import chat
from server.config import DATA_DIR

# 预设角色
ROLES = {
    "润色": {
        "prompt": "你是专业文字编辑，擅长润色各类文案。请将用户提供的文字润色得更流畅优美，保持原意不变。直接输出润色后的文字。",
        "icon": "✨",
        "follow_up": "需要我进一步调整风格吗？可以改成更正式/更活泼/更简洁的版本。",
    },
    "改稿": {
        "prompt": "你是资深编辑，帮用户深度改写文稿。提升表达力、优化结构、修正语病。输出改写后的全文。",
        "icon": "📝",
        "follow_up": "改写完成。需要我解释修改的原因吗？",
    },
    "总结": {
        "prompt": "你是文档分析专家，帮用户提炼内容要点。用清晰的层级结构呈现核心信息。",
        "icon": "📋",
        "follow_up": "需要我生成思维导图格式的总结吗？",
    },
    "简历": {
        "prompt": "你是专业简历顾问，帮用户生成或优化简历。使用STAR法则描述经历，突出量化成果，格式规范专业。",
        "icon": "📄",
        "follow_up": "需要我帮你导出为PDF格式吗？或者针对特定岗位进一步优化？",
    },
    "演讲稿": {
        "prompt": "你是资深演讲撰稿人，帮用户撰写演讲稿。开头抓人、逻辑清晰、结尾有力，适合口头表达。",
        "icon": "🎤",
        "follow_up": "需要我标注演讲的节奏和停顿建议吗？",
    },
    "翻译": {
        "prompt": "你是专业翻译，精通多国语言。请将用户输入准确翻译为目标语言，保持原文风格和语气。",
        "icon": "🌐",
        "follow_up": "",
    },
    "起名": {
        "prompt": "你是起名专家，精通中英文取名。给出名字并解释寓意、音韵、文化内涵。提供至少3个选项。",
        "icon": "🏷️",
        "follow_up": "有偏好的风格吗？古风/现代/简约/独特？",
    },
    "食谱": {
        "prompt": "你是烹饪达人，帮用户提供详细食谱。包含食材清单（精确用量）、详细步骤、烹饪技巧、营养提示。",
        "icon": "🍳",
        "follow_up": "需要根据现有食材调整吗？或者换一个更简单的版本？",
    },
    "攻略": {
        "prompt": "你是资深旅游规划师，帮用户制定旅行攻略。包含行程安排、景点推荐、美食地图、交通指南、预算估算、注意事项。",
        "icon": "✈️",
        "follow_up": "有特别想去的景点或偏好的旅行方式吗？",
    },
    "解题": {
        "prompt": "你是耐心细致的教师，帮学生解答问题。讲解清晰、步骤详细、举一反三、通俗易懂。",
        "icon": "📚",
        "follow_up": "还有哪里不明白的可以继续问哦。",
    },
    "会议纪要": {
        "prompt": "你是专业行政助理，帮用户整理会议纪要。结构清晰：会议主题、参与人、讨论要点、决议事项、待办任务。",
        "icon": "📊",
        "follow_up": "需要我把待办事项整理成表格吗？",
    },
    "文案": {
        "prompt": "你是资深广告文案，帮用户撰写营销文案。抓住产品亮点、击中用户痛点、语言有力、促进转化。",
        "icon": "💡",
        "follow_up": "需要A/B两个版本做测试吗？",
    },
    "小说": {
        "prompt": "你是小说作家，帮用户创作或续写小说。文笔生动、情节引人、人物鲜明。",
        "icon": "📖",
        "follow_up": "需要我提供几个情节走向供选择吗？",
    },
    "情感": {
        "prompt": "你是温暖知心的朋友，帮用户疏导情绪。先倾听共情，再温和引导，给出建设性建议。",
        "icon": "💝",
        "follow_up": "如果愿意，可以和我说更多细节。",
    },
    "穿搭": {
        "prompt": "你是专业时尚顾问，帮用户提供穿搭建议。根据场景、身材、季节、预算推荐搭配方案。",
        "icon": "👔",
        "follow_up": "有具体的场合或预算限制吗？",
    },
    "代码审查": {
        "prompt": "你是资深代码审查专家。审查用户提供的代码，指出潜在问题、性能优化点、安全隐患，并给出改进建议。",
        "icon": "🔍",
        "follow_up": "需要我重写优化后的完整代码吗？",
    },
}

# 用户自定义角色存储
CUSTOM_ROLES_FILE = os.path.join(DATA_DIR, "custom_roles.json")


def _load_custom_roles() -> dict:
    if os.path.exists(CUSTOM_ROLES_FILE):
        with open(CUSTOM_ROLES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_custom_roles(roles: dict):
    with open(CUSTOM_ROLES_FILE, "w", encoding="utf-8") as f:
        json.dump(roles, f, ensure_ascii=False, indent=2)


def handle(body: dict) -> dict:
    """处理智能指令"""
    text = body.get("message", "").strip()
    action = body.get("action", "execute")  # execute / list / add_custom / delete_custom
    
    if not text and action == "execute":
        return {"ok": False, "error": "请输入内容"}
    
    # 列出所有角色
    if action == "list":
        all_roles = {**ROLES, **_load_custom_roles()}
        role_list = []
        for name, config in all_roles.items():
            role_list.append({
                "name": name,
                "icon": config.get("icon", "🤖"),
                "description": config["prompt"][:50] + "...",
                "is_custom": name not in ROLES,
            })
        return {"ok": True, "roles": role_list}
    
    # 添加自定义角色
    if action == "add_custom":
        role_name = body.get("role_name", "").strip()
        role_prompt = body.get("role_prompt", "").strip()
        role_icon = body.get("role_icon", "🤖")
        
        if not role_name or not role_prompt:
            return {"ok": False, "error": "角色名和提示词不能为空"}
        
        custom_roles = _load_custom_roles()
        custom_roles[role_name] = {
            "prompt": role_prompt,
            "icon": role_icon,
            "follow_up": "",
        }
        _save_custom_roles(custom_roles)
        return {"ok": True, "message": f"自定义角色「{role_name}」已添加"}
    
    # 删除自定义角色
    if action == "delete_custom":
        role_name = body.get("role_name", "").strip()
        custom_roles = _load_custom_roles()
        if role_name in custom_roles:
            del custom_roles[role_name]
            _save_custom_roles(custom_roles)
            return {"ok": True, "message": f"已删除「{role_name}」"}
        return {"ok": False, "error": "角色不存在"}
    
    # 执行指令
    role = "对话"
    system_prompt = "你是Nova，一个全能的AI助手。回答简洁、友好、有条理。"
    follow_up = ""
    
    # 合并所有角色
    all_roles = {**ROLES, **_load_custom_roles()}
    
    # 检测指令前缀
    for key, config in all_roles.items():
        prefix_patterns = [
            f"{key}：", f"{key}:",
            f"用{key}", f"帮我{key}",
        ]
        for pattern in prefix_patterns:
            if text.startswith(pattern):
                role = key
                system_prompt = config["prompt"]
                follow_up = config.get("follow_up", "")
                # 提取实际内容
                text = text[len(pattern):].strip()
                break
        else:
            continue
        break
    
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ]
        reply = chat(messages, timeout=120)
        
        result = {
            "ok": True,
            "reply": reply,
            "role": role,
        }
        
        if follow_up:
            result["follow_up"] = follow_up
        
        return result
        
    except Exception as e:
        return {"ok": False, "error": f"AI服务不可用: {e}", "role": role}
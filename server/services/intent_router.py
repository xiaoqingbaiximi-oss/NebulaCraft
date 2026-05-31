# -*- coding: utf-8 -*-
"""
意图路由器 - 自动识别用户想做什么
支持：生图、思维导图、代码、文件操作、Shell、屏幕、浏览器、Agent、自升级
"""
import json
import re
import requests
import os
import time as _time

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5:1.5b"

MEMORY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "intent_memory.json")

INTENTS = {
    "image_gen": {
        "keywords": ["画", "生成图", "生成一张", "画一张", "图片", "画个", "图", "生成图片",
                     "draw", "generate image", "生成一个图", "做一张图", "来张图", "画个图"],
        "description": "AI 生图",
        "extract_prompt": True,
        "remove_prefixes": ["画", "生成图", "生成一张", "画一张", "图片", "画个", "图", "生成图片",
                           "生成一个图", "做一张图", "来张图", "画个图"]
    },
    "mindmap": {
        "keywords": ["思维导图", "脑图", "整理思路", "梳理", "mindmap", "结构图",
                     "知识图谱", "思维整理", "帮我整理", "做个导图", "画个导图"],
        "description": "生成思维导图",
        "extract_prompt": True,
        "remove_prefixes": ["思维导图", "脑图", "生成思维导图", "做个思维导图", "画个思维导图",
                           "帮我整理", "梳理一下", "整理一下"]
    },
    "flowchart": {
        "keywords": ["流程图", "流程", "步骤图", "flowchart", "框图", "架构图",
                     "工作流", "画流程", "做个流程", "生成流程"],
        "description": "生成流程图",
        "extract_prompt": True,
        "remove_prefixes": ["流程图", "流程", "生成流程图", "画个流程图", "做个流程图", "做个流程"]
    },
    "code_gen": {
        "keywords": ["写代码", "生成代码", "写个", "写一个程序", "编写", "代码生成",
                     "写个游戏", "写个脚本", "帮我写", "实现一个", "编程",
                     "code", "写一个", "创建函数", "函数实现", "写段代码"],
        "description": "代码生成",
        "extract_prompt": True,
        "remove_prefixes": ["写代码", "生成代码", "写个", "写一个", "帮我写", "编写", "写段"]
    },
    "code_review": {
        "keywords": ["审查代码", "检查代码", "review", "代码审查", "检查这段代码",
                     "看看这段代码", "代码有问题", "bug", "优化代码", "重构", "这段代码"],
        "description": "代码审查/优化",
        "extract_prompt": False
    },
    "knowledge": {
        "keywords": ["知识库", "查一下", "搜索文档", "我的文档", "知识库查询",
                     "查文档", "search knowledge", "找一下文档", "文档里"],
        "description": "知识库查询",
        "extract_prompt": True,
        "remove_prefixes": ["知识库", "查一下", "搜索文档", "查文档", "找一下文档", "从知识库"]
    },
    "translate": {
        "keywords": ["翻译", "translate", "翻译成", "译成", "用英文", "用中文",
                     "翻一下", "翻译一下"],
        "description": "翻译",
        "extract_prompt": True,
        "remove_prefixes": ["翻译", "翻译一下", "翻一下", "翻译成"]
    },
    "file_operation": {
        "keywords": [
            "列出桌面", "桌面文件", "桌面上的", "桌面有什么", "桌面里有",
            "下载里的", "文档里的", "图片里的",
            "读取", "打开文件", "创建文件", "修改文件", "删除文件", "列出目录",
            "搜索文件", "查看文件", "写文件", "新建文件", "编辑文件", "改文件",
            "看文件", "读文件", "显示文件", "找文件", "文件内容",
            "保存到", "存到", "写到", "列出", "文件夹", "目录",
            "创建", "删除文件", "写一个文件", "新建", "生成文件",
            "桌面", "下载", "文档"
        ],
        "description": "文件操作",
        "extract_prompt": False,
        "remove_prefixes": []
    },
    "shell_operation": {
        "keywords": [
            "执行命令", "运行命令", "cmd", "命令行", "终端", "shell",
            "ping", "ipconfig", "tasklist", "systeminfo", "netstat",
            "打开应用", "启动程序", "运行软件", "打开软件",
            "执行python", "运行代码", "跑代码", "执行代码",
            "创建文件夹", "删除文件夹", "复制文件", "移动文件",
            "查看ip", "查看进程", "查看端口", "查看系统",
            "环境变量", "关机", "重启", "取消关机",
            "命令", "执行", "跑一下", "运行"
        ],
        "description": "Shell 命令执行",
        "extract_prompt": False,
        "remove_prefixes": []
    },
    "screen_operation": {
        "keywords": [
            "截图", "截屏", "屏幕截图", "screenshot",
            "屏幕分析", "看看屏幕", "分析屏幕", "屏幕有什么",
            "截个图", "屏幕", "截屏分析"
        ],
        "description": "屏幕截图分析",
        "extract_prompt": False,
        "remove_prefixes": []
    },
    "browser_operation": {
        "keywords": [
            "打开网址", "打开网站", "访问网站", "浏览网页",
            "搜索", "搜一下", "帮我搜", "百度一下", "google",
            "打开网页", "上网", "查一下", "搜搜",
            "bing", "百度", "搜索", "打开", "访问", "浏览"
        ],
        "description": "浏览器操作",
        "extract_prompt": False,
        "remove_prefixes": []
    },
    "agent": {
        "keywords": ["帮我", "自动", "批量", "打包", "然后", "接着做"],
        "description": "多步骤自动化任务",
        "extract_prompt": False,
        "remove_prefixes": []
    },
    "self_update": {
        "keywords": [
            "修改配置", "改端口", "改设置", "升级功能", "优化代码",
            "修改功能", "新增功能", "创建模块", "添加功能",
            "修改文件", "更新代码", "改代码", "自我升级",
            "修改", "升级", "优化", "添加", "创建"
        ],
        "description": "自我升级/修改代码",
        "extract_prompt": False,
        "remove_prefixes": []
    },
    "tool_calc": {
        "keywords": ["计算", "算一下", "等于多少", "计算器", "算算"],
        "description": "计算器",
        "extract_prompt": False
    },
    "tool_password": {
        "keywords": ["生成密码", "密码生成", "随机密码", "创建密码"],
        "description": "密码生成",
        "extract_prompt": False
    },
    "tool_qrcode": {
        "keywords": ["二维码", "生成二维码", "qr code", "做个二维码"],
        "description": "二维码生成",
        "extract_prompt": True,
        "remove_prefixes": ["生成二维码", "二维码", "做个二维码"]
    },
    "chat": {
        "keywords": [],
        "description": "普通对话",
        "extract_prompt": False
    }
}


def _load_memory():
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {"learned_keywords": {}, "corrections": []}


def _save_memory(memory):
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def learn(user_input, correct_intent):
    memory = _load_memory()
    words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', user_input.lower())
    for word in words:
        if len(word) < 2:
            continue
        if word not in memory["learned_keywords"]:
            memory["learned_keywords"][word] = {"intent": correct_intent, "weight": 1, "last_used": _time.time()}
        else:
            memory["learned_keywords"][word]["weight"] += 1
            memory["learned_keywords"][word]["last_used"] = _time.time()
    memory["corrections"].append({"input": user_input, "correct_intent": correct_intent, "time": _time.time()})
    memory["corrections"] = memory["corrections"][-100:]
    _save_memory(memory)
    print(f"[Router] 学习完成: '{user_input}' → {correct_intent}")


def quick_match(text):
    text_lower = text.lower()
    if text_lower.startswith("@"):
        return None


    # === 最高优先级：自升级 ===
    if re.search(r'(?:修改|改|升级|优化|新增|添加|创建)\s*(?:端口|配置|功能|代码|文件|模块|路由)', text_lower):
        return "self_update"
    if re.search(r'(?:把|将)\s*(?:端口|配置).*(?:改成|改为|改成|设置为)\s*\d+', text_lower):
        return "self_update"

    # === 电脑管家（在 Agent 之前） ===
    if re.search(r'(?:扫描|体检|检查|优化|清理|加速|修复).*(?:电脑|系统|磁盘|内存)', text_lower):
        return "butler"
    if re.search(r'(?:电脑|系统).*(?:扫描|体检|检查|优化|清理|加速)', text_lower):
        return "butler"
    if re.search(r'(?:一键优化|一键加速|深度清理|系统修复)', text_lower):
        return "butler"
    if re.search(r'(?:管家|健康评分|系统状态)', text_lower):
        return "butler"
    if re.search(r'^(?:扫描电脑|电脑体检|系统体检|优化电脑|清理系统)$', text_lower):
        return "butler"
    if re.search(r'(?:确认修复|确认|同意|执行修复|全部确认|拒绝|全部拒绝)', text_lower):
        return "butler"

    # === 第零优先级：Agent 多步骤任务 ===
    if re.search(r'(?:然后|接着|再|并且|同时|之后|完了|最后|先.*再|先.*然后)', text_lower):
        return "agent"
    if re.search(r'(?:帮我|自动|批量).*(?:然后|再|接着|并且|同时)', text_lower):
        return "agent"

    # === 第一优先级：文件操作 ===
    file_keywords = [
        "列出桌面", "桌面文件", "桌面上的", "桌面有什么", "桌面里有",
        "桌面", "下载里的", "文档里的", "图片里的",
        "创建文件", "写文件", "新建文件", "读取文件", "修改文件",
        "删除文件", "搜索文件", "列出目录", "文件夹", "目录",
        "列出", "看文件", "读文件", "找文件", "打开文件",
        "保存到", "存到", "写到"
    ]
    for kw in sorted(file_keywords, key=len, reverse=True):
        if kw in text_lower:
            return "file_operation"

    # === 第二优先级：Shell 操作 ===
    shell_keywords = [
        "执行命令", "运行命令", "命令行", "终端",
        "ping", "ipconfig", "tasklist", "systeminfo", "netstat",
        "执行python", "运行代码", "跑代码", "执行代码",
        "查看ip", "查看进程", "查看端口", "查看系统",
        "环境变量", "关机", "重启", "取消关机",
        "打开应用", "启动程序", "运行软件"
    ]
    for kw in sorted(shell_keywords, key=len, reverse=True):
        if kw in text_lower:
            return "shell_operation"

    # === 第三优先级：屏幕操作 ===
    screen_keywords = ["截图", "截屏", "屏幕分析", "看看屏幕", "分析屏幕", "截个图"]
    for kw in sorted(screen_keywords, key=len, reverse=True):
        if kw in text_lower:
            return "screen_operation"

    # === 第四优先级：浏览器操作 ===
    if re.search(r'打开\s*(?:网址|网站|网页)?\s*(https?://|[a-zA-Z0-9][-a-zA-Z0-9]*\.(?:com|cn|org|net|io|ai|dev|app|xyz|me|top|cc))', text_lower):
        return "browser_operation"
    if re.search(r'(?:搜索|搜一下|帮我搜|百度一下|google|bing)\s*', text_lower):
        return "browser_operation"

    # 检查学习到的关键词
    memory = _load_memory()
    for word, info in sorted(memory.get("learned_keywords", {}).items(), key=lambda x: -x[1]["weight"]):
        if word in text_lower:
            return info["intent"]

    # 检查内置关键词（跳过已处理的意图）
    _KEYWORD_CACHE = {}
    skip_intents = ["file_operation", "shell_operation", "screen_operation", "browser_operation", "agent", "self_update"]
    for intent_name, intent_data in INTENTS.items():
        if intent_name in skip_intents:
            continue
        for kw in intent_data.get("keywords", []):
            _KEYWORD_CACHE[kw] = intent_name

    for kw, intent in sorted(_KEYWORD_CACHE.items(), key=lambda x: -len(x[0])):
        if kw in text_lower:
            return intent

    return None


def llm_classify(text):
    intent_list = "\n".join([f"- {k}: {v['description']}" for k, v in INTENTS.items()])
    prompt = f"""你是一个意图分类器。分析用户输入，判断他们想做什么。

可选意图：
{intent_list}

用户输入："{text}"

请只回复一个意图名称，不要回复其他内容。"""

    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL, "prompt": prompt, "stream": False,
            "options": {"num_predict": 10, "temperature": 0}
        }, timeout=5)
        if resp.status_code == 200:
            result = resp.json().get("response", "").strip().lower()
            for intent in INTENTS:
                if intent in result:
                    return intent
    except:
        pass
    return None


def extract_prompt(text, intent_name):
    intent_data = INTENTS.get(intent_name, {})
    if not intent_data.get("extract_prompt"):
        return text
    prefixes = intent_data.get("remove_prefixes", [])
    cleaned = text
    for prefix in sorted(prefixes, key=len, reverse=True):
        pattern = re.compile(rf"^{re.escape(prefix)}\s*", re.IGNORECASE)
        cleaned = pattern.sub("", cleaned)
    return cleaned.strip() or text


def route_intent(text):
    intent = quick_match(text)
    method = "keyword"
    if not intent:
        intent = llm_classify(text)
        method = "llm"
    if not intent:
        intent = "chat"
        method = "default"
    cleaned = extract_prompt(text, intent)
    return {"intent": intent, "cleaned_text": cleaned, "method": method}
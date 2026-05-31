# -*- coding: utf-8 -*-
"""
浏览器控制引擎
打开网页、搜索、基础自动化
"""
import os
import re
import webbrowser
import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5:1.5b"


def open_website(url):
    """打开网址"""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        webbrowser.open(url)
        return {"ok": True, "url": url, "action": "opened"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def search_web(query, engine="google"):
    """搜索网页"""
    search_engines = {
        "google": "https://www.google.com/search?q={}",
        "bing": "https://www.bing.com/search?q={}",
        "baidu": "https://www.baidu.com/s?wd={}",
        "github": "https://github.com/search?q={}",
    }
    
    url_template = search_engines.get(engine, search_engines["google"])
    url = url_template.format(requests.utils.quote(query))
    
    try:
        webbrowser.open(url)
        return {"ok": True, "url": url, "query": query, "engine": engine, "action": "searched"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def ai_browser_operation(user_message):
    """AI 处理浏览器操作"""
    msg = user_message.strip()
    
    # 打开网址
    url_patterns = [
        r'(?:打开|访问|浏览|goto|open)\s*(?:网址|网站|网页)?\s*(https?://[^\s]+)',
        r'(?:打开|访问|浏览|goto|open)\s*(?:网址|网站|网页)?\s*([a-zA-Z0-9]+\.[a-zA-Z]{2,}[^\s]*)',
    ]
    for pattern in url_patterns:
        match = re.search(pattern, msg)
        if match:
            url = match.group(1).strip()
            return open_website(url)
    
    # 搜索
    search_patterns = [
        r'(?:搜索|查询|搜一下|帮我搜|百度|google|bing)\s*(.+)',
    ]
    for pattern in search_patterns:
        match = re.search(pattern, msg)
        if match:
            query = match.group(1).strip()
            engine = "google"
            if "百度" in msg or "baidu" in msg.lower():
                engine = "baidu"
            elif "bing" in msg.lower():
                engine = "bing"
            return search_web(query, engine)
    
    # 用 LLM 理解
    prompt = f"""分析用户消息，判断他们想要的操作，输出一个 JSON。

用户消息：{user_message}

操作类型：
- search: 搜索网页 → {{"action":"search","query":"关键词","engine":"google"}}
- open: 打开网址 → {{"action":"open","url":"https://..."}}
- none: 不相关 → {{"action":"none"}}

JSON:"""

    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL, "prompt": prompt, "stream": False,
            "options": {"num_predict": 200, "temperature": 0}
        }, timeout=10)
        if resp.status_code == 200:
            raw = resp.json().get("response", "").strip()
            import json
            json_match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                if data.get("action") == "search":
                    return search_web(data.get("query", ""), data.get("engine", "google"))
                elif data.get("action") == "open":
                    return open_website(data.get("url", ""))
    except:
        pass
    
    return {"ok": False, "error": "无法理解浏览器操作意图"}
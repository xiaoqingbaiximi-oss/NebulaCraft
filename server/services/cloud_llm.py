"""
云端 LLM 服务 - 多平台支持
支持: 通义千问 / DeepSeek / OpenAI / 自定义 OpenAI 兼容接口
"""
import os
import json
import requests

API_CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "api_config.json")
API_CONFIG = {}


def _load_config():
    global API_CONFIG
    try:
        if os.path.exists(API_CONFIG_FILE):
            with open(API_CONFIG_FILE, "r", encoding="utf-8") as f:
                API_CONFIG = json.load(f)
    except:
        API_CONFIG = {}


def _save_config():
    os.makedirs(os.path.dirname(API_CONFIG_FILE), exist_ok=True)
    with open(API_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(API_CONFIG, f, ensure_ascii=False, indent=2)


_load_config()


# ===== 平台配置 =====
PLATFORMS = {
    "qwen": {
        "name": "通义千问",
        "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "api_key": API_CONFIG.get("qwen_api_key", ""),
        "models": ["qwen-plus", "qwen-turbo", "qwen-max"],
        "default_model": "qwen-plus",
        "headers": lambda key: {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    },
    "deepseek": {
        "name": "DeepSeek",
        "api_url": "https://api.deepseek.com/v1/chat/completions",
        "api_key": API_CONFIG.get("deepseek_api_key", ""),
        "models": ["deepseek-chat", "deepseek-coder"],
        "default_model": "deepseek-chat",
        "headers": lambda key: {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    },
    "openai": {
        "name": "OpenAI",
        "api_url": "https://api.openai.com/v1/chat/completions",
        "api_key": API_CONFIG.get("openai_api_key", ""),
        "models": ["gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"],
        "default_model": "gpt-3.5-turbo",
        "headers": lambda key: {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    },
    "custom": {
        "name": "自定义",
        "api_url": API_CONFIG.get("custom_api_url", ""),
        "api_key": API_CONFIG.get("custom_api_key", ""),
        "models": API_CONFIG.get("custom_models", []),
        "default_model": API_CONFIG.get("custom_default_model", ""),
        "headers": lambda key: {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    },
}

# 当前激活的平台
ACTIVE_PLATFORM = API_CONFIG.get("active_platform", "")


def get_active_platform():
    """获取当前激活的平台"""
    global ACTIVE_PLATFORM
    ACTIVE_PLATFORM = API_CONFIG.get("active_platform", "")
    if ACTIVE_PLATFORM and ACTIVE_PLATFORM in PLATFORMS:
        p = PLATFORMS[ACTIVE_PLATFORM]
        if p["api_key"]:
            return p
    # 自动检测第一个有 key 的平台
    for name, p in PLATFORMS.items():
        if p["api_key"]:
            ACTIVE_PLATFORM = name
            return p
    return None


def chat(messages, model=None, timeout=120):
    """调用云端 API"""
    platform = get_active_platform()
    if not platform:
        raise Exception("请先设置 API Key")

    model = model or platform["default_model"]
    api_url = platform["api_url"]
    api_key = platform["api_key"]
    headers = platform["headers"](api_key) if callable(platform["headers"]) else platform["headers"]

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 4096,
    }

    try:
        resp = requests.post(api_url, json=payload, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        else:
            raise Exception(f"API 错误 ({resp.status_code}): {resp.text[:200]}")
    except requests.exceptions.Timeout:
        raise Exception("API 请求超时")
    except Exception as e:
        raise Exception(f"请求失败: {str(e)}")


def chat_stream(messages, model=None):
    """流式调用云端 API"""
    platform = get_active_platform()
    if not platform:
        yield "请先设置 API Key"
        return

    model = model or platform["default_model"]
    api_url = platform["api_url"]
    api_key = platform["api_key"]
    headers = platform["headers"](api_key) if callable(platform["headers"]) else platform["headers"]

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 4096,
        "stream": True,
    }

    try:
        resp = requests.post(api_url, json=payload, headers=headers, timeout=300, stream=True)
        if resp.status_code != 200:
            yield f"API 错误 ({resp.status_code})"
            return
        for line in resp.iter_lines():
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        return
                    try:
                        data = json.loads(data_str)
                        content = data["choices"][0].get("delta", {}).get("content", "")
                        if content:
                            yield content
                    except:
                        continue
    except Exception as e:
        yield f"请求失败: {str(e)}"


# ===== 设置方法 =====
def set_api_key(platform, key):
    """设置指定平台的 API Key"""
    global ACTIVE_PLATFORM
    key_map = {
        "qwen": "qwen_api_key",
        "deepseek": "deepseek_api_key",
        "openai": "openai_api_key",
        "custom": "custom_api_key",
    }
    config_key = key_map.get(platform, f"{platform}_api_key")
    API_CONFIG[config_key] = key
    API_CONFIG["active_platform"] = platform
    PLATFORMS[platform]["api_key"] = key
    ACTIVE_PLATFORM = platform
    _save_config()
    return True


def set_custom_api(url, key, models="", default_model=""):
    """设置自定义 API"""
    API_CONFIG["custom_api_url"] = url
    API_CONFIG["custom_api_key"] = key
    API_CONFIG["custom_models"] = [m.strip() for m in models.split(",") if m.strip()]
    API_CONFIG["custom_default_model"] = default_model or (API_CONFIG["custom_models"][0] if API_CONFIG["custom_models"] else "")
    API_CONFIG["active_platform"] = "custom"
    PLATFORMS["custom"]["api_url"] = url
    PLATFORMS["custom"]["api_key"] = key
    PLATFORMS["custom"]["models"] = API_CONFIG["custom_models"]
    PLATFORMS["custom"]["default_model"] = API_CONFIG["custom_default_model"]
    global ACTIVE_PLATFORM
    ACTIVE_PLATFORM = "custom"
    _save_config()
    return True


def get_all_status():
    """获取所有平台状态"""
    result = {"active": ACTIVE_PLATFORM, "platforms": {}}
    for name, p in PLATFORMS.items():
        key = p["api_key"]
        result["platforms"][name] = {
            "name": p["name"],
            "has_key": bool(key),
            "masked_key": (key[:8] + "****" + key[-4:]) if len(key) > 12 else "未设置",
            "models": p["models"],
            "default_model": p["default_model"],
        }
    return result
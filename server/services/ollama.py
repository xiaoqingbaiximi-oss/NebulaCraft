"""
Ollama 服务接口 - 支持本地和云端切换
"""
import os
import json
import requests
from server.config import DEFAULT_MODEL

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")


def is_available():
    """检查 Ollama 是否可用"""
    try:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        return resp.status_code == 200
    except:
        return False


def list_models():
    """列出本地模型"""
    try:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            models = [{"name": m["name"], "size": str(m.get("size", ""))} for m in data.get("models", [])]
            return {"ok": True, "models": models}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, "models": []}


def chat(messages, model=None, timeout=120):
    """发送对话请求 - 优先云端 API"""
    model = model or DEFAULT_MODEL

    # 检查是否启用了云端 API
    try:
        from server.services.cloud_llm import get_active_platform
        platform = get_active_platform()
        if platform:
            from server.services.cloud_llm import chat as cloud_chat
            cloud_model = platform["default_model"]
            # DeepSeek 模型映射
            if platform.get("name") == "DeepSeek":
                cloud_model = "deepseek-chat"
            return cloud_chat(messages, model=cloud_model, timeout=timeout)
    except ImportError:
        pass
    except Exception as e:
        raise Exception(f"云端 API 错误: {str(e)}")

    # 回退到本地 Ollama
    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={"model": model, "messages": messages, "stream": False},
            timeout=timeout,
        )
        if resp.status_code == 200:
            return resp.json().get("message", {}).get("content", "")
        else:
            raise Exception(f"Ollama 返回错误: {resp.status_code}")
    except requests.exceptions.ConnectionError:
        raise Exception("Ollama 服务未连接，请确保已启动")
    except Exception as e:
        raise Exception(f"对话失败: {str(e)}")


def chat_stream(messages, model=None):
    """流式对话 - 优先云端 API"""
    model = model or DEFAULT_MODEL

    # 检查是否启用了云端 API
    try:
        from server.services.cloud_llm import get_active_platform
        platform = get_active_platform()
        if platform:
            from server.services.cloud_llm import chat_stream as cloud_stream
            cloud_model = platform["default_model"]
            if platform.get("name") == "DeepSeek":
                cloud_model = "deepseek-chat"
            for chunk in cloud_stream(messages, model=cloud_model):
                yield chunk
            return
    except ImportError:
        pass
    except Exception:
        pass

    # 回退到本地 Ollama 流式
    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={"model": model, "messages": messages, "stream": True},
            timeout=300,
            stream=True,
        )
        for line in resp.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    chunk = data.get("message", {}).get("content", "")
                    if chunk:
                        yield chunk
                except:
                    continue
    except requests.exceptions.ConnectionError:
        yield "Ollama 服务未连接，请确保已启动"
    except Exception as e:
        yield f"对话失败: {str(e)}"
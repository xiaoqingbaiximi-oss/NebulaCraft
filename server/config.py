"""全局配置"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")

for d in [DATA_DIR, OUTPUT_DIR]:
    os.makedirs(d, exist_ok=True)

PORT = int(os.environ.get("PORT", 8889))
HOST = "0.0.0.0"
VERSION = "7.0.0"

# 调试模式（命令行加 --debug 启用）
DEBUG = "--debug" in sys.argv

# Ollama
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_GENERATE = f"{OLLAMA_URL}/api/generate"
OLLAMA_CHAT = f"{OLLAMA_URL}/api/chat"
DEFAULT_MODEL = os.environ.get("MODEL", "qwen2.5:1.5b")

# 速率限制
RATE_LIMIT_ENABLED = not DEBUG
RATE_LIMIT_MAX_REQUESTS = 120
RATE_LIMIT_WINDOW = 60

# 文件上传限制（字节）
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
MAX_BODY_SIZE = 10 * 1024 * 1024    # 10MB
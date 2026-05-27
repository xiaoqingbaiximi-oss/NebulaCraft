"""使用量统计与配额管理"""
import os
import json
import time
from server.config import DATA_DIR

QUOTA_DIR = os.path.join(DATA_DIR, "quota")
os.makedirs(QUOTA_DIR, exist_ok=True)

# 默认配额
DEFAULT_QUOTA = {
    "daily_chat": 500,       # 每日对话次数
    "daily_images": 50,      # 每日图像生成
    "daily_searches": 100,   # 每日搜索
    "knowledge_docs": 1000,  # 知识库文档数
    "storage_mb": 500,       # 存储空间(MB)
}


def get_usage(user="default"):
    """获取使用量"""
    today = time.strftime("%Y-%m-%d")
    usage_file = os.path.join(QUOTA_DIR, f"{user}.json")

    if os.path.exists(usage_file):
        with open(usage_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"daily": {}, "total": {"chat": 0, "images": 0, "searches": 0}}

    if today not in data["daily"]:
        data["daily"][today] = {"chat": 0, "images": 0, "searches": 0}

    return data


def save_usage(user, data):
    """保存使用量"""
    usage_file = os.path.join(QUOTA_DIR, f"{user}.json")
    with open(usage_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def track(user, action, count=1):
    """记录使用"""
    data = get_usage(user)
    today = time.strftime("%Y-%m-%d")

    if today not in data["daily"]:
        data["daily"][today] = {"chat": 0, "images": 0, "searches": 0}

    if action in ("chat", "images", "searches"):
        data["daily"][today][action] += count
        data["total"][action] = data["total"].get(action, 0) + count

    save_usage(user, data)


def check_quota(user="default"):
    """检查配额"""
    usage = get_usage(user)
    today = time.strftime("%Y-%m-%d")
    daily = usage["daily"].get(today, {"chat": 0, "images": 0, "searches": 0})
    total = usage["total"]

    return {
        "daily": {
            "chat": {"used": daily.get("chat", 0), "limit": DEFAULT_QUOTA["daily_chat"]},
            "images": {"used": daily.get("images", 0), "limit": DEFAULT_QUOTA["daily_images"]},
            "searches": {"used": daily.get("searches", 0), "limit": DEFAULT_QUOTA["daily_searches"]},
        },
        "total": {
            "chat": total.get("chat", 0),
            "images": total.get("images", 0),
            "searches": total.get("searches", 0),
        },
        "quota_ok": (
            daily.get("chat", 0) < DEFAULT_QUOTA["daily_chat"]
            and daily.get("images", 0) < DEFAULT_QUOTA["daily_images"]
            and daily.get("searches", 0) < DEFAULT_QUOTA["daily_searches"]
        ),
    }
"""审计日志服务"""
import os
import json
import time
from server.config import DATA_DIR

AUDIT_DIR = os.path.join(DATA_DIR, "audit")
os.makedirs(AUDIT_DIR, exist_ok=True)


def log(action, user="anonymous", details=None, ip=""):
    """记录审计日志"""
    entry = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": time.time(),
        "user": user,
        "action": action,
        "ip": ip,
        "details": details or {},
    }

    # 按日期分文件
    date_str = time.strftime("%Y-%m-%d")
    log_file = os.path.join(AUDIT_DIR, f"{date_str}.jsonl")

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def query(date=None, action=None, user=None, limit=100):
    """查询审计日志"""
    results = []

    if date:
        log_file = os.path.join(AUDIT_DIR, f"{date}.jsonl")
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if action and entry.get("action") != action:
                            continue
                        if user and entry.get("user") != user:
                            continue
                        results.append(entry)
                    except:
                        continue
    else:
        # 读取所有日志文件
        for filename in sorted(os.listdir(AUDIT_DIR), reverse=True):
            if not filename.endswith(".jsonl"):
                continue
            log_file = os.path.join(AUDIT_DIR, filename)
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if action and entry.get("action") != action:
                            continue
                        if user and entry.get("user") != user:
                            continue
                        results.append(entry)
                    except:
                        continue
            if len(results) >= limit:
                break

    results.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return results[:limit]


def get_stats():
    """获取审计统计"""
    total = 0
    today = time.strftime("%Y-%m-%d")
    today_count = 0

    for filename in os.listdir(AUDIT_DIR):
        if not filename.endswith(".jsonl"):
            continue
        log_file = os.path.join(AUDIT_DIR, filename)
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                total += 1
                if filename.startswith(today):
                    today_count += 1

    # 按动作统计
    actions = {}
    for filename in os.listdir(AUDIT_DIR)[-7:]:
        if not filename.endswith(".jsonl"):
            continue
        log_file = os.path.join(AUDIT_DIR, filename)
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    act = entry.get("action", "unknown")
                    actions[act] = actions.get(act, 0) + 1
                except:
                    continue

    return {
        "total": total,
        "today": today_count,
        "top_actions": sorted(actions.items(), key=lambda x: x[1], reverse=True)[:10],
    }
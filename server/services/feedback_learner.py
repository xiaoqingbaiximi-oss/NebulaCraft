# -*- coding: utf-8 -*-
"""
反馈学习引擎
从用户反馈中自动优化
"""
import os
import json
import time
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
FEEDBACK_FILE = os.path.join(DATA_DIR, "feedback.json")


def record_feedback(user_input, intent, result, rating=None):
    """记录用户反馈"""
    try:
        if os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
                feedbacks = json.load(f)
        else:
            feedbacks = []
        
        feedbacks.append({
            "input": user_input,
            "intent": intent,
            "success": result.get("ok", False),
            "rating": rating,
            "time": datetime.now().isoformat()
        })
        
        feedbacks = feedbacks[-500:]
        with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
            json.dump(feedbacks, f, ensure_ascii=False, indent=2)
        
        # 分析失败模式
        if not result.get("ok"):
            analyze_failures()
    except:
        pass


def analyze_failures():
    """分析失败模式，找出问题"""
    try:
        if not os.path.exists(FEEDBACK_FILE):
            return
        
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            feedbacks = json.load(f)
        
        failures = [f for f in feedbacks if not f.get("success")]
        if len(failures) >= 3:
            # 找出最常见的失败意图
            from collections import Counter
            intent_counts = Counter(f["intent"] for f in failures)
            most_failed = intent_counts.most_common(3)
            print(f"[Feedback] 常见失败意图: {most_failed}")
    except:
        pass


def get_feedback_stats():
    """获取反馈统计"""
    try:
        if os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
                feedbacks = json.load(f)
            
            total = len(feedbacks)
            successes = sum(1 for f in feedbacks if f.get("success"))
            
            return {
                "ok": True,
                "total": total,
                "successes": successes,
                "failures": total - successes,
                "success_rate": round(successes / max(total, 1) * 100, 1),
                "recent": feedbacks[-10:]
            }
    except:
        pass
    return {"ok": True, "total": 0, "successes": 0, "failures": 0, "success_rate": 0, "recent": []}
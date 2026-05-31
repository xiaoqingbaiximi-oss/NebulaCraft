# -*- coding: utf-8 -*-
"""
主动建议引擎
根据时间、习惯、上下文主动推荐操作
"""
import os
import json
import time
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
SUGGESTIONS_FILE = os.path.join(DATA_DIR, "proactive_suggestions.json")


class ProactiveEngine:
    def __init__(self):
        self.rules = self._load_rules()
    
    def _load_rules(self):
        default_rules = [
            {"time": "09:00", "action": "总结今天的新闻", "intent": "shell", "days": ["Monday","Tuesday","Wednesday","Thursday","Friday"]},
            {"time": "12:00", "action": "截图分析上午的工作", "intent": "screen", "days": ["Monday","Tuesday","Wednesday","Thursday","Friday"]},
            {"time": "17:00", "action": "备份桌面文件", "intent": "agent", "days": ["Monday","Tuesday","Wednesday","Thursday","Friday"]},
            {"idle_minutes": 10, "action": "需要我帮你做点什么吗？", "intent": "chat"},
        ]
        try:
            if os.path.exists(SUGGESTIONS_FILE):
                with open(SUGGESTIONS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except:
            pass
        return default_rules
    
    def get_suggestions(self, context=None):
        """获取当前时刻的建议"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_day = now.strftime("%A")
        
        suggestions = []
        for rule in self.rules:
            # 时间匹配
            if rule.get("time") == current_time:
                if "days" in rule and current_day not in rule["days"]:
                    continue
                suggestions.append({
                    "action": rule["action"],
                    "intent": rule.get("intent", "chat"),
                    "type": "time_based",
                    "priority": "high"
                })
        
        # 基于上下文
        if context:
            if "错误" in str(context) or "失败" in str(context):
                suggestions.append({
                    "action": "需要我帮你排查这个错误吗？",
                    "intent": "chat",
                    "type": "context_based",
                    "priority": "high"
                })
        
        return suggestions
    
    def add_rule(self, time_str, action, intent="chat", days=None):
        """添加新规则"""
        rule = {"time": time_str, "action": action, "intent": intent}
        if days:
            rule["days"] = days
        self.rules.append(rule)
        self._save()
    
    def _save(self):
        os.makedirs(os.path.dirname(SUGGESTIONS_FILE), exist_ok=True)
        with open(SUGGESTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.rules, f, ensure_ascii=False, indent=2)


proactive = ProactiveEngine()
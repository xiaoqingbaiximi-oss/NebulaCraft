# -*- coding: utf-8 -*-
"""
NebulaCraft 记忆系统
记住用户偏好、习惯、上下文
"""
import os
import json
import time
from datetime import datetime

MEMORY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "memory")
os.makedirs(MEMORY_DIR, exist_ok=True)

USER_PROFILE_FILE = os.path.join(MEMORY_DIR, "user_profile.json")
PREFERENCES_FILE = os.path.join(MEMORY_DIR, "preferences.json")
HABITS_FILE = os.path.join(MEMORY_DIR, "habits.json")
CONTEXT_FILE = os.path.join(MEMORY_DIR, "context.json")
LEARNINGS_FILE = os.path.join(MEMORY_DIR, "learnings.json")


class MemorySystem:
    def __init__(self):
        self.profile = self._load(USER_PROFILE_FILE, {})
        self.preferences = self._load(PREFERENCES_FILE, {})
        self.habits = self._load(HABITS_FILE, [])
        self.context = self._load(CONTEXT_FILE, {"recent_topics": [], "current_task": None})
        self.learnings = self._load(LEARNINGS_FILE, {"successes": [], "failures": []})
    
    def _load(self, path, default):
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except:
            pass
        return default
    
    def _save(self, path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_all(self):
        self._save(USER_PROFILE_FILE, self.profile)
        self._save(PREFERENCES_FILE, self.preferences)
        self._save(HABITS_FILE, self.habits)
        self._save(CONTEXT_FILE, self.context)
        self._save(LEARNINGS_FILE, self.learnings)
    
    def remember_preference(self, key, value):
        """记住用户偏好"""
        self.preferences[key] = {"value": value, "time": time.time()}
        self._save(PREFERENCES_FILE, self.preferences)
        print(f"[Memory] 记住偏好: {key} = {value}")
    
    def get_preference(self, key, default=None):
        """获取用户偏好"""
        pref = self.preferences.get(key, {})
        return pref.get("value", default)
    
    def record_habit(self, action, time_of_day=None):
        """记录用户习惯"""
        habit = {
            "action": action,
            "time": time_of_day or datetime.now().strftime("%H:%M"),
            "day": datetime.now().strftime("%A"),
            "count": 1
        }
        # 检查是否已存在相似习惯
        for h in self.habits:
            if h["action"] == action and h["time"] == habit["time"]:
                h["count"] += 1
                self._save(HABITS_FILE, self.habits)
                return
        self.habits.append(habit)
        self.habits = self.habits[-200:]
        self._save(HABITS_FILE, self.habits)
    
    def get_current_habits(self):
        """获取当前时间段的习惯"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_day = now.strftime("%A")
        suggestions = []
        for h in self.habits:
            if h["time"] == current_time and h["count"] >= 2:
                suggestions.append(h["action"])
        return suggestions
    
    def update_context(self, topic=None, task=None):
        """更新当前上下文"""
        if topic:
            self.context["recent_topics"].insert(0, topic)
            self.context["recent_topics"] = self.context["recent_topics"][:10]
        if task:
            self.context["current_task"] = task
        self._save(CONTEXT_FILE, self.context)
    
    def get_context(self):
        """获取当前上下文"""
        return self.context
    
    def learn_from_success(self, input_text, result):
        """从成功操作中学习"""
        self.learnings["successes"].append({
            "input": input_text,
            "result": str(result)[:200],
            "time": time.time()
        })
        self.learnings["successes"] = self.learnings["successes"][-50:]
        self._save(LEARNINGS_FILE, self.learnings)
    
    def learn_from_failure(self, input_text, error):
        """从失败中学习"""
        # 记录失败模式，下次避免
        self.learnings["failures"].append({
            "input": input_text,
            "error": str(error)[:200],
            "time": time.time()
        })
        self.learnings["failures"] = self.learnings["failures"][-50:]
        self._save(LEARNINGS_FILE, self.learnings)
        
        # 分析失败模式
        similar_failures = [f for f in self.learnings["failures"] 
                          if f["input"] == input_text]
        if len(similar_failures) >= 3:
            print(f"[Memory] 检测到重复失败模式: '{input_text}'，将避免此操作")
    
    def get_suggestions(self, current_input):
        """根据历史和习惯主动建议"""
        suggestions = []
        
        # 基于当前时间段的习惯
        habit_suggestions = self.get_current_habits()
        for h in habit_suggestions:
            if h not in suggestions:
                suggestions.append(f"这个时间你通常会：{h}")
        
        # 基于最近话题的相关建议
        recent = self.context.get("recent_topics", [])
        if recent:
            suggestions.append(f"继续之前的话题：{recent[0]}")
        
        return suggestions
    
    def summarize_user(self):
        """生成用户画像摘要"""
        return {
            "preferences": dict(list(self.preferences.items())[-10:]),
            "habits_count": len(self.habits),
            "recent_topics": self.context.get("recent_topics", [])[:5],
            "success_rate": len(self.learnings["successes"]) / max(len(self.learnings["successes"]) + len(self.learnings["failures"]), 1)
        }


memory = MemorySystem()
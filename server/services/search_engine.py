"""全文搜索引擎"""
import os
import json
import re
from server.services import database as db


class SearchEngine:
    def __init__(self):
        self.index = {}

    def search_all(self, query, limit=20):
        """跨所有数据源搜索"""
        results = []
        q = query.lower()

        # 搜索对话历史
        try:
            msgs = db.search_messages(query)
            for m in msgs:
                results.append({
                    "type": "对话",
                    "title": m.get("session", ""),
                    "snippet": self._highlight(m.get("content", ""), q)[:200],
                    "time": m.get("time", ""),
                })
        except:
            pass

        # 搜索笔记
        try:
            notes = db.get_notes()
            for n in notes:
                if q in (n.get("title", "") + n.get("content", "")).lower():
                    results.append({
                        "type": "笔记",
                        "title": n.get("title", ""),
                        "snippet": self._highlight(n.get("content", ""), q)[:200],
                        "time": n.get("updated", ""),
                    })
        except:
            pass

        # 去重排序
        results.sort(key=lambda x: x.get("time", ""), reverse=True)
        return results[:limit]

    def _highlight(self, text, query):
        """高亮搜索词"""
        if not text:
            return ""
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        return pattern.sub(f"**{query}**", text)

    def get_stats(self):
        """获取索引统计"""
        total_msgs = 0
        total_notes = 0
        try:
            msgs = db.search_messages("")
            total_msgs = len(msgs) if msgs else 0
        except:
            pass
        try:
            notes = db.get_notes()
            total_notes = len(notes) if notes else 0
        except:
            pass

        return {
            "total_messages": total_msgs,
            "total_notes": total_notes,
            "indexed": True,
        }


search_engine = SearchEngine()
"""全文搜索 API"""
from server.services.search_engine import search_engine


def handle(body):
    query = body.get("query", "").strip()
    if not query:
        return {"ok": False, "error": "请输入搜索词"}

    results = search_engine.search_all(query)
    return {"ok": True, "query": query, "total": len(results), "results": results}
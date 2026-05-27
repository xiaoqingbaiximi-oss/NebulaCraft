"""知识库 API 路由"""
from server.services.knowledge import kb


def handle(body):
    action = body.get("action", "search")
    collection = body.get("collection", "default")

    if action == "create_collection":
        return kb.create_collection(body.get("name", ""), body.get("description", ""))
    if action == "delete_collection":
        return kb.delete_collection(body.get("name", ""))
    if action == "list_collections":
        return kb.list_collections()
    if action == "add_document":
        return kb.add_document(collection, body.get("text", ""), body.get("title", ""), body.get("source", ""), body.get("metadata"))
    if action == "import_pdf":
        return kb.import_pdf(collection, body.get("file_data", b""), body.get("filename", "document.pdf"))
    if action == "import_url":
        return kb.import_url(collection, body.get("url", ""))
    if action == "search":
        return kb.search(collection, body.get("query", ""), body.get("top_k", 5))
    if action == "delete_document":
        return kb.delete_document(collection, body.get("doc_id", ""))
    if action == "get_stats":
        return kb.get_stats()

    return {"ok": False, "error": f"未知操作: {action}"}
"""数据库查询 API"""
from server.services.database import get_db


def handle(body):
    sql = body.get("sql", "").strip()
    if not sql:
        return {"ok": False, "error": "请输入 SQL"}

    # 安全检查：只允许 SELECT
    if not sql.upper().strip().startswith("SELECT"):
        return {"ok": False, "error": "仅支持 SELECT 查询"}

    # 禁止危险操作
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE"]
    for word in forbidden:
        if word in sql.upper():
            return {"ok": False, "error": f"不允许 {word} 操作"}

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            result.append({k: row[k] for k in row.keys()})

        return {"ok": True, "rows": result, "count": len(result)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
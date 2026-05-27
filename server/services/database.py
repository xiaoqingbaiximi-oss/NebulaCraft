"""
数据库服务 - SQLite
支持: 对话历史 / 用户数据隔离 / 笔记 / 知识库元数据
"""
import os
import sqlite3
import time
import json
from server.config import DATA_DIR

DB_PATH = os.path.join(DATA_DIR, "nebulacraft.db")


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 用户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            last_login TEXT
        )
    """)
    
    # 会话表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            title TEXT DEFAULT '新对话',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # 消息表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
    """)
    
    # 笔记表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            title TEXT DEFAULT '无标题',
            content TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # 知识库文档表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kb_documents (
            id TEXT PRIMARY KEY,
            collection_name TEXT NOT NULL,
            title TEXT DEFAULT '',
            source TEXT DEFAULT '',
            chunk_count INTEGER DEFAULT 0,
            text_length INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    
    # 习惯打卡表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habit_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
            UNIQUE(habit_id, date)
        )
    """)
    
    # 密码本表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vault (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            site TEXT NOT NULL,
            username TEXT DEFAULT '',
            password_encrypted TEXT NOT NULL,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, site)
        )
    """)
    
    conn.commit()
    conn.close()


# ==================== 消息操作 ====================

def save_message(session_id, role, content, user_id=None):
    """保存单条消息"""
    conn = get_db()
    conn.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content)
    )
    conn.execute(
        "UPDATE sessions SET updated_at = datetime('now','localtime') WHERE id = ?",
        (session_id,)
    )
    conn.commit()
    conn.close()


def get_messages(session_id, limit=100):
    """获取会话消息"""
    conn = get_db()
    rows = conn.execute(
        "SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY id ASC LIMIT ?",
        (session_id, limit)
    ).fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"], "time": r["created_at"]} for r in rows]


def create_session(user_id=None, title="新对话"):
    """创建新会话"""
    import secrets
    sid = "sess_" + secrets.token_hex(8)
    conn = get_db()
    conn.execute(
        "INSERT INTO sessions (id, user_id, title) VALUES (?, ?, ?)",
        (sid, user_id, title)
    )
    conn.commit()
    conn.close()
    return sid


def list_sessions(user_id=None, limit=50):
    """列出会话"""
    conn = get_db()
    if user_id:
        rows = conn.execute(
            "SELECT id, title, created_at, updated_at FROM sessions WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    conn.close()
    return [{"id": r["id"], "title": r["title"], "created": r["created_at"], "updated": r["updated_at"]} for r in rows]


def delete_session(session_id):
    """删除会话"""
    conn = get_db()
    conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


def search_messages(query, user_id=None, limit=20):
    """搜索消息"""
    conn = get_db()
    if user_id:
        rows = conn.execute(
            "SELECT m.role, m.content, m.created_at, s.title FROM messages m JOIN sessions s ON m.session_id = s.id WHERE s.user_id = ? AND m.content LIKE ? ORDER BY m.id DESC LIMIT ?",
            (user_id, f"%{query}%", limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT m.role, m.content, m.created_at, s.title FROM messages m JOIN sessions s ON m.session_id = s.id WHERE m.content LIKE ? ORDER BY m.id DESC LIMIT ?",
            (f"%{query}%", limit)
        ).fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"][:200], "time": r["created_at"], "session": r["title"]} for r in rows]


# ==================== 笔记操作 ====================

def save_note(note_id, title, content, user_id=None):
    """保存笔记"""
    conn = get_db()
    existing = conn.execute("SELECT id FROM notes WHERE id = ?", (note_id,)).fetchone()
    if existing:
        conn.execute(
            "UPDATE notes SET title = ?, content = ?, updated_at = datetime('now','localtime') WHERE id = ?",
            (title, content, note_id)
        )
    else:
        conn.execute(
            "INSERT INTO notes (id, user_id, title, content) VALUES (?, ?, ?, ?)",
            (note_id, user_id, title, content)
        )
    conn.commit()
    conn.close()


def get_notes(user_id=None):
    """获取笔记列表"""
    conn = get_db()
    if user_id:
        rows = conn.execute(
            "SELECT id, title, content, created_at, updated_at FROM notes WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, title, content, created_at, updated_at FROM notes ORDER BY updated_at DESC"
        ).fetchall()
    conn.close()
    return [{"id": r["id"], "title": r["title"], "content": r["content"], "created": r["created_at"], "updated": r["updated_at"]} for r in rows]


def delete_note(note_id):
    """删除笔记"""
    conn = get_db()
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()


# ==================== 习惯打卡 ====================

def get_habits(user_id=None):
    """获取习惯列表"""
    conn = get_db()
    if user_id:
        rows = conn.execute("SELECT id, name FROM habits WHERE user_id = ?", (user_id,)).fetchall()
    else:
        rows = conn.execute("SELECT id, name FROM habits").fetchall()
    
    habits = []
    for r in rows:
        records = conn.execute("SELECT date FROM habit_records WHERE habit_id = ? ORDER BY date DESC", (r["id"],)).fetchall()
        habits.append({
            "id": r["id"],
            "name": r["name"],
            "dates": [rec["date"] for rec in records]
        })
    conn.close()
    return habits


def add_habit(name, user_id=None):
    """添加习惯"""
    conn = get_db()
    conn.execute("INSERT INTO habits (user_id, name) VALUES (?, ?)", (user_id, name))
    conn.commit()
    conn.close()


def toggle_habit_record(habit_id, date):
    """切换打卡状态"""
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM habit_records WHERE habit_id = ? AND date = ?",
        (habit_id, date)
    ).fetchone()
    if existing:
        conn.execute("DELETE FROM habit_records WHERE id = ?", (existing["id"],))
    else:
        conn.execute("INSERT INTO habit_records (habit_id, date) VALUES (?, ?)", (habit_id, date))
    conn.commit()
    conn.close()


def delete_habit(habit_id):
    """删除习惯"""
    conn = get_db()
    conn.execute("DELETE FROM habit_records WHERE habit_id = ?", (habit_id,))
    conn.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
    conn.commit()
    conn.close()


# ==================== 密码本 ====================

def get_vault(user_id=None):
    """获取密码本"""
    conn = get_db()
    if user_id:
        rows = conn.execute("SELECT site, username, password_encrypted, notes FROM vault WHERE user_id = ?", (user_id,)).fetchall()
    else:
        rows = conn.execute("SELECT site, username, password_encrypted, notes FROM vault").fetchall()
    conn.close()
    result = {}
    for r in rows:
        result[r["site"]] = {"u": r["username"], "p": r["password_encrypted"], "notes": r["notes"]}
    return result


def save_vault_entry(user_id, site, username, password_encrypted):
    """保存密码条目"""
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO vault (user_id, site, username, password_encrypted, updated_at) VALUES (?, ?, ?, ?, datetime('now','localtime'))",
        (user_id, site, username, password_encrypted)
    )
    conn.commit()
    conn.close()


def delete_vault_entry(user_id, site):
    """删除密码条目"""
    conn = get_db()
    conn.execute("DELETE FROM vault WHERE user_id = ? AND site = ?", (user_id, site))
    conn.commit()
    conn.close()


# 初始化
init_db()
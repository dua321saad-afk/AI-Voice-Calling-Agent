"""
SQLite database for user accounts, conversation sessions, and messages.

Two separate identity systems:
  - "accounts": real signup/login users who start conversations
  - the single admin (username/password from .env, not stored in DB)

A "call" row represents one browser-based conversation session, tied to
the account that started it, with domain_key starting NULL until the
agent (via the LLM) figures out which of the three business domains the
caller wants.
"""

import sqlite3
from datetime import datetime
from config import Config


def get_connection():
    conn = sqlite3.connect(Config.DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def _add_column_if_missing(conn, table, column, coltype):
    existing_cols = [row["name"] for row in conn.execute(f"PRAGMA table_info({table})")]
    if column not in existing_cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")


def init_db():
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER,
            account_username TEXT,
            domain_key TEXT,
            domain_label TEXT,
            call_sid TEXT UNIQUE,
            status TEXT DEFAULT 'in_progress',
            message_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            ended_at TEXT,
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT,
            confidence REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (call_id) REFERENCES calls (id)
        );
        """
    )
    # Backwards-compatible migrations for older database.db files
    _add_column_if_missing(conn, "calls", "domain_key", "TEXT")
    _add_column_if_missing(conn, "calls", "account_id", "INTEGER")
    _add_column_if_missing(conn, "calls", "account_username", "TEXT")
    conn.commit()
    conn.close()


# ---- Accounts (user signup/login) ----

def create_account(username: str, password_hash: str) -> int:
    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM accounts WHERE username = ?", (username,)
    ).fetchone()
    if existing:
        conn.close()
        raise ValueError("Username already taken")

    cursor = conn.execute(
        "INSERT INTO accounts (username, password_hash, created_at) VALUES (?, ?, ?)",
        (username, password_hash, datetime.utcnow().isoformat()),
    )
    conn.commit()
    account_id = cursor.lastrowid
    conn.close()
    return account_id


def get_account_by_username(username: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM accounts WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_account_by_id(account_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_accounts(limit=100):
    """Admin view: every registered user, with their session count."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT a.id, a.username, a.created_at, "
        "COUNT(c.id) as session_count, MAX(c.created_at) as last_session_at "
        "FROM accounts a LEFT JOIN calls c ON c.account_id = a.id "
        "GROUP BY a.id ORDER BY a.created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---- Sessions ("calls") ----

def start_session(session_id: str, account_id: int, account_username: str) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO calls (account_id, account_username, domain_key, domain_label, "
        "call_sid, status, created_at) VALUES (?, ?, NULL, NULL, ?, 'in_progress', ?)",
        (account_id, account_username, session_id, datetime.utcnow().isoformat()),
    )
    conn.commit()
    call_id = cursor.lastrowid
    conn.close()
    return call_id


def set_session_domain(call_id: int, domain_key: str, domain_label: str):
    conn = get_connection()
    conn.execute(
        "UPDATE calls SET domain_key = ?, domain_label = ? WHERE id = ?",
        (domain_key, domain_label, call_id),
    )
    conn.commit()
    conn.close()


def end_session(call_id: int):
    conn = get_connection()
    conn.execute(
        "UPDATE calls SET status = 'completed', ended_at = ? WHERE id = ?",
        (datetime.utcnow().isoformat(), call_id),
    )
    conn.commit()
    conn.close()


def get_call_by_id(call_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM calls WHERE id = ?", (call_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_calls_by_domain(domain_key, limit=50):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM calls WHERE domain_key = ? ORDER BY id DESC LIMIT ?",
        (domain_key, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_calls(limit=50):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM calls ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def increment_message_count(call_id):
    conn = get_connection()
    conn.execute(
        "UPDATE calls SET message_count = message_count + 1 WHERE id = ?",
        (call_id,),
    )
    conn.commit()
    conn.close()


# ---- Messages ----

def log_message(call_id, role, content, source=None, confidence=None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO messages (call_id, role, content, source, confidence, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (call_id, role, content, source, confidence, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    increment_message_count(call_id)


def get_messages_for_call(call_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM messages WHERE call_id = ? ORDER BY id ASC",
        (call_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_conversation_history(call_id):
    messages = get_messages_for_call(call_id)
    return [{"role": m["role"], "content": m["content"]} for m in messages]


# ---- Admin delete authority ----

def delete_call(call_id: int) -> bool:
    """Deletes a single conversation session and all its messages."""
    conn = get_connection()
    existing = conn.execute("SELECT id FROM calls WHERE id = ?", (call_id,)).fetchone()
    if not existing:
        conn.close()
        return False
    conn.execute("DELETE FROM messages WHERE call_id = ?", (call_id,))
    conn.execute("DELETE FROM calls WHERE id = ?", (call_id,))
    conn.commit()
    conn.close()
    return True


def delete_all_calls(domain_key: str | None = None) -> int:
    """Deletes all conversation sessions (optionally scoped to one domain).
    Returns the number of sessions deleted."""
    conn = get_connection()
    if domain_key:
        ids = [r["id"] for r in conn.execute(
            "SELECT id FROM calls WHERE domain_key = ?", (domain_key,)
        ).fetchall()]
    else:
        ids = [r["id"] for r in conn.execute("SELECT id FROM calls").fetchall()]

    for call_id in ids:
        conn.execute("DELETE FROM messages WHERE call_id = ?", (call_id,))
        conn.execute("DELETE FROM calls WHERE id = ?", (call_id,))

    conn.commit()
    conn.close()
    return len(ids)


# ---- Stats ----

def get_domain_stats():
    conn = get_connection()
    rows = conn.execute(
        "SELECT domain_key, domain_label, COUNT(*) as total_calls, "
        "SUM(message_count) as total_messages "
        "FROM calls WHERE domain_key IS NOT NULL GROUP BY domain_key"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

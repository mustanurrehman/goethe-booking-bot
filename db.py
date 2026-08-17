"""
Database persistence layer (SQLite).        [DEPRECATED]
Stores students, results, logs persistently.

⚠️ WARNING: This module is deprecated. Use `database.py` (SQLAlchemy)
   for all new code. It supports both SQLite and PostgreSQL and is
   the production database layer. This file is kept for backward
   compatibility and will be removed in a future release.
"""

from __future__ import annotations

import json
import secrets
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).parent / "bot_data.db"
_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
    return _local.conn


def _init_migrations(conn):
    """Add missing columns for backward compatibility."""
    existing = {r["name"] for r in conn.execute("PRAGMA table_info(students)").fetchall()}
    migs = {
        "password": "ALTER TABLE students ADD COLUMN password TEXT DEFAULT ''",
        "first_name": "ALTER TABLE students ADD COLUMN first_name TEXT DEFAULT ''",
        "surname": "ALTER TABLE students ADD COLUMN surname TEXT DEFAULT ''",
        "dob": "ALTER TABLE students ADD COLUMN dob TEXT DEFAULT ''",
        "contact_number": "ALTER TABLE students ADD COLUMN contact_number TEXT DEFAULT ''",
        "country": "ALTER TABLE students ADD COLUMN country TEXT DEFAULT ''",
        "postal_code": "ALTER TABLE students ADD COLUMN postal_code TEXT DEFAULT ''",
        "street": "ALTER TABLE students ADD COLUMN street TEXT DEFAULT ''",
        "house_number": "ALTER TABLE students ADD COLUMN house_number TEXT DEFAULT ''",
        "additional_address": "ALTER TABLE students ADD COLUMN additional_address TEXT DEFAULT ''",
        "location_city": "ALTER TABLE students ADD COLUMN location_city TEXT DEFAULT ''",
        "phone_prefix": "ALTER TABLE students ADD COLUMN phone_prefix TEXT DEFAULT ''",
        "phone": "ALTER TABLE students ADD COLUMN phone TEXT DEFAULT ''",
        "place_of_birth": "ALTER TABLE students ADD COLUMN place_of_birth TEXT DEFAULT ''",
        "motivation": "ALTER TABLE students ADD COLUMN motivation TEXT DEFAULT ''",
        "promo_code": "ALTER TABLE students ADD COLUMN promo_code TEXT DEFAULT ''",
    }
    for col, sql in migs.items():
        if col not in existing:
            conn.execute(sql)


def init_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            password TEXT DEFAULT '',
            level TEXT,
            city TEXT,
            booking_datetime TEXT,
            status TEXT DEFAULT 'pending',
            result_json TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_key TEXT,
            level TEXT,
            message TEXT,
            time TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS bot_state (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            expires_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS queue_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            level TEXT,
            city TEXT,
            status TEXT DEFAULT 'pending',
            priority INTEGER DEFAULT 0,
            queued_at TEXT DEFAULT (datetime('now')),
            started_at TEXT,
            finished_at TEXT,
            result_json TEXT
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            email TEXT,
            details TEXT,
            ip TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    _init_migrations(conn)
    conn.commit()


def add_student(student: Dict[str, str]) -> int:
    conn = _get_conn()
    conn.execute("DELETE FROM students")
    for s in students:
        conn.execute(
            "INSERT INTO students (name, email, password, level, city, booking_datetime, status, first_name, surname, dob, contact_number, country, postal_code, street, house_number, additional_address, location_city, phone_prefix, phone, place_of_birth, motivation, promo_code) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (s.get("name", ""), s.get("email", ""), s.get("password", ""), s.get("level", s.get("exam_level", "")), s.get("city", ""), s.get("booking_datetime", ""), "pending",
             s.get("first_name", ""), s.get("surname", ""), s.get("dob", ""), s.get("contact_number", ""), s.get("country", ""), s.get("postal_code", ""), s.get("street", ""), s.get("house_number", ""), s.get("additional_address", ""), s.get("location_city", ""), s.get("phone_prefix", ""), s.get("phone", ""), s.get("place_of_birth", ""), s.get("motivation", ""), s.get("promo_code", "")),
        )
    conn.commit()


def add_student(student: Dict[str, str]) -> int:
    conn = _get_conn()
    cur = conn.execute(
        "INSERT INTO students (name, email, password, level, city, booking_datetime, status, first_name, surname, dob, contact_number, country, postal_code, street, house_number, additional_address, location_city, phone_prefix, phone, place_of_birth, motivation, promo_code) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (student.get("name", ""), student.get("email", ""), student.get("password", ""),
         student.get("level", student.get("exam_level", "")), student.get("city", ""),
         student.get("booking_datetime", ""),
         student.get("first_name", ""), student.get("surname", ""), student.get("dob", ""),
         student.get("contact_number", ""), student.get("country", ""), student.get("postal_code", ""),
         student.get("street", ""), student.get("house_number", ""), student.get("additional_address", ""),
         student.get("location_city", ""), student.get("phone_prefix", ""), student.get("phone", ""),
         student.get("place_of_birth", ""), student.get("motivation", ""), student.get("promo_code", "")),
    )
    conn.commit()
    return cur.lastrowid


def delete_student(student_id: int) -> bool:
    conn = _get_conn()
    cur = conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    return cur.rowcount > 0


def get_students() -> List[Dict[str, Any]]:
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM students ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def update_student_status(student_key: str, status: str, result: Optional[Dict] = None):
    conn = _get_conn()
    conn.execute(
        "UPDATE students SET status = ?, result_json = ?, updated_at = datetime('now') WHERE name || '|' || level || '|' || city = ?",
        (status, json.dumps(result) if result else None, student_key),
    )
    conn.commit()


def save_students(students: List[Dict]):
    import crypto_utils, os
    _fernet_key = os.environ.get("FERNET_KEY", "")
    conn = _get_conn()
    conn.execute("DELETE FROM students")
    for s in students:
        raw = s.get("password", "")
        try:
            crypto_utils.decrypt_password(raw, _fernet_key)
            pw_enc = raw
        except Exception:
            pw_enc = crypto_utils.encrypt_password(raw, _fernet_key)
        conn.execute(
            "INSERT INTO students (name, email, password, level, city, booking_datetime, status, first_name, surname, dob, contact_number, country, postal_code, street, house_number, additional_address, location_city, phone_prefix, phone, place_of_birth, motivation, promo_code, result_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                s.get("name", ""), s.get("email", ""), pw_enc,
                s.get("level", ""), s.get("city", ""), s.get("booking_datetime", ""),
                s.get("status", "pending"),
                s.get("first_name", ""), s.get("surname", ""),
                s.get("dob", ""), s.get("contact_number", ""),
                s.get("country", ""), s.get("postal_code", ""),
                s.get("street", ""), s.get("house_number", ""),
                s.get("additional_address", ""), s.get("location_city", ""),
                s.get("phone_prefix", ""), s.get("phone", ""),
                s.get("place_of_birth", ""), s.get("motivation", ""),
                s.get("promo_code", ""),
                json.dumps(s.get("result", {})),
            ),
        )
    conn.commit()


def add_log(student_key: str, level: str, message: str):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO logs (student_key, level, message) VALUES (?, ?, ?)",
        (student_key, level, message),
    )
    conn.commit()


def get_logs(student_key: Optional[str] = None, limit: int = 200, date_filter: Optional[str] = None) -> List[Dict]:
    conn = _get_conn()
    if date_filter:
        from datetime import datetime, timedelta
        try:
            day = datetime.strptime(date_filter, "%Y-%m-%d")
            next_day = day + timedelta(days=1)
            rows = conn.execute(
                "SELECT * FROM logs WHERE time >= ? AND time < ? ORDER BY id DESC LIMIT ?",
                (day.isoformat(), next_day.isoformat(), limit),
            ).fetchall()
        except ValueError:
            rows = []
    elif student_key:
        rows = conn.execute("SELECT * FROM logs WHERE student_key = ? ORDER BY id DESC LIMIT ?", (student_key, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def search_logs(query: str, limit: int = 100) -> List[Dict]:
    conn = _get_conn()
    like = f"%{query}%"
    rows = conn.execute(
        "SELECT * FROM logs WHERE student_key LIKE ? OR message LIKE ? ORDER BY id DESC LIMIT ?",
        (like, like, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def get_booking_history(limit: int = 100) -> List[Dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM queue_history ORDER BY finished_at DESC NULLS LAST, id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def set_state(key: str, value: str):
    conn = _get_conn()
    conn.execute("INSERT OR REPLACE INTO bot_state (key, value) VALUES (?, ?)", (key, value))
    conn.commit()


def get_state(key: str, default: str = "") -> str:
    conn = _get_conn()
    row = conn.execute("SELECT value FROM bot_state WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def delete_state(key: str):
    conn = _get_conn()
    conn.execute("DELETE FROM bot_state WHERE key = ?", (key,))
    conn.commit()


def save_checkpoint(student_key: str, step: int):
    set_state(f"checkpoint_{student_key}", str(step))


def get_checkpoint(student_key: str) -> int:
    val = get_state(f"checkpoint_{student_key}", "0")
    try:
        return int(val)
    except ValueError:
        return 0


def clear_checkpoint(student_key: str):
    delete_state(f"checkpoint_{student_key}")


def clear_all_checkpoints():
    conn = _get_conn()
    conn.execute("DELETE FROM bot_state WHERE key LIKE 'checkpoint_%'")
    conn.commit()


def add_to_queue(name: str, email: str, level: str, city: str, priority: int = 0):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO queue_history (name, email, level, city, status, priority) VALUES (?, ?, ?, ?, 'pending', ?)",
        (name, email, level, city, priority),
    )
    conn.commit()


def get_queue(status: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = _get_conn()
    if status:
        rows = conn.execute("SELECT * FROM queue_history WHERE status = ? ORDER BY priority DESC, id ASC", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM queue_history ORDER BY priority DESC, id ASC").fetchall()
    return [dict(r) for r in rows]


def update_queue_item(item_id: int, status: str, result: Optional[Dict] = None):
    conn = _get_conn()
    if status == "in_progress":
        conn.execute("UPDATE queue_history SET status = ?, started_at = datetime('now') WHERE id = ?", (status, item_id))
    elif status in ("completed", "failed"):
        conn.execute(
            "UPDATE queue_history SET status = ?, finished_at = datetime('now'), result_json = ? WHERE id = ?",
            (status, json.dumps(result) if result else None, item_id),
        )
    else:
        conn.execute("UPDATE queue_history SET status = ? WHERE id = ?", (status, item_id))
    conn.commit()


def delete_queue_item(item_id: int):
    conn = _get_conn()
    conn.execute("DELETE FROM queue_history WHERE id = ?", (item_id,))
    conn.commit()


def clear_queue():
    conn = _get_conn()
    conn.execute("DELETE FROM queue_history")
    conn.commit()


def create_session(email: str, expiry_hours: int = 24) -> str:
    conn = _get_conn()
    conn.execute("DELETE FROM sessions WHERE expires_at < datetime('now')")
    session_id = secrets.token_urlsafe(48)
    conn.execute(
        "INSERT INTO sessions (session_id, email, expires_at) VALUES (?, ?, datetime('now', '+{} hours'))".format(expiry_hours),
        (session_id, email),
    )
    conn.commit()
    return session_id


def validate_session(session_id: str) -> Optional[str]:
    conn = _get_conn()
    conn.execute("DELETE FROM sessions WHERE expires_at < datetime('now')")
    conn.commit()
    row = conn.execute(
        "SELECT email FROM sessions WHERE session_id = ? AND expires_at >= datetime('now')",
        (session_id,),
    ).fetchone()
    return row["email"] if row else None


def delete_session(session_id: str):
    conn = _get_conn()
    conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    conn.commit()


def clean_expired_sessions():
    conn = _get_conn()
    conn.execute("DELETE FROM sessions WHERE expires_at < datetime('now')")
    conn.commit()


def add_audit_log(action: str, email: str = "", details: str = "", ip: str = ""):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO audit_log (action, email, details, ip) VALUES (?, ?, ?, ?)",
        (action, email, details, ip),
    )
    conn.commit()


def get_audit_logs(limit: int = 100) -> List[Dict]:
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


init_db()

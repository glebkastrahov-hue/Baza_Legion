"""
Слой работы с базой данных (SQLite).

Таблица clients: phone (PK) | review | added_by | added_at | edited_by | edited_at
Таблица admin_chats: username (PK) | chat_id   -- нужна, чтобы бот мог сам
писать админам в личку (для авто-выгрузки), запоминается при любом
сообщении от админа боту.
"""
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Optional, Tuple, List

DB_PATH = "clients.db"


def _ensure_columns(conn: sqlite3.Connection) -> None:
    """Миграция: добавляет новые колонки в уже существующую базу, если их нет."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(clients)")}
    if "edited_by" not in cols:
        conn.execute("ALTER TABLE clients ADD COLUMN edited_by TEXT")
    if "edited_at" not in cols:
        conn.execute("ALTER TABLE clients ADD COLUMN edited_at TEXT")


def init_db() -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
                phone     TEXT PRIMARY KEY,
                review    TEXT NOT NULL,
                added_by  TEXT,
                added_at  TEXT
            )
            """
        )
        _ensure_columns(conn)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_chats (
                username TEXT PRIMARY KEY,
                chat_id  INTEGER NOT NULL
            )
            """
        )
        conn.commit()


def find_client(phone: str) -> Optional[Tuple[str, str, str, str, str, str]]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.execute(
            "SELECT phone, review, added_by, added_at, edited_by, edited_at "
            "FROM clients WHERE phone = ?",
            (phone,),
        )
        return cur.fetchone()


def phone_exists(phone: str) -> bool:
    return find_client(phone) is not None


def add_client(phone: str, review: str, added_by: str) -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        conn.execute(
            "INSERT OR IGNORE INTO clients (phone, review, added_by, added_at) "
            "VALUES (?, ?, ?, ?)",
            (phone, review, added_by or "unknown", now),
        )
        conn.commit()


def update_review(phone: str, new_review: str, edited_by: str) -> bool:
    """Обновляет отзыв существующего клиента. True, если строка была обновлена."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        cur = conn.execute(
            "UPDATE clients SET review = ?, edited_by = ?, edited_at = ? WHERE phone = ?",
            (new_review, edited_by or "unknown", now, phone),
        )
        conn.commit()
        return cur.rowcount > 0


def get_all_clients() -> List[Tuple[str, str, str, str, str, str]]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.execute(
            "SELECT phone, review, added_by, added_at, edited_by, edited_at "
            "FROM clients ORDER BY added_at DESC"
        )
        return cur.fetchall()


def save_admin_chat(username: str, chat_id: int) -> None:
    """Запоминает chat_id админа, чтобы бот мог позже написать ему сам (авто-выгрузка)."""
    if not username:
        return
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "INSERT INTO admin_chats (username, chat_id) VALUES (?, ?) "
            "ON CONFLICT(username) DO UPDATE SET chat_id = excluded.chat_id",
            (username.lower(), chat_id),
        )
        conn.commit()


def delete_client(phone: str) -> bool:
    """Удаляет клиента из базы. True, если строка была удалена."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.execute("DELETE FROM clients WHERE phone = ?", (phone,))
        conn.commit()
        return cur.rowcount > 0


def get_admin_chat_ids(usernames: List[str]) -> List[int]:
    """Возвращает chat_id только тех админов, которые уже хоть раз писали боту."""
    if not usernames:
        return []
    lowered = [u.lower().lstrip("@") for u in usernames]
    placeholders = ",".join("?" for _ in lowered)
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.execute(
            f"SELECT chat_id FROM admin_chats WHERE username IN ({placeholders})",
            lowered,
        )
        return [row[0] for row in cur.fetchall()]

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

from agenda_avisos.core.models import Reminder, ReminderStatus, RepeatType


DATETIME_FMT = "%Y-%m-%d %H:%M:%S"


def dt_to_str(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.strftime(DATETIME_FMT)


def str_to_dt(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    return datetime.strptime(value, DATETIME_FMT)


class Database:
    def __init__(self, db_path: str = "data/agenda_avisos.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    next_run_at TEXT NOT NULL,
                    repeat_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    snooze_until TEXT,
                    last_fired_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )

    def add_reminder(self, reminder: Reminder) -> int:
        now = datetime.now()
        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO reminders
                (title, message, next_run_at, repeat_type, status, snooze_until, last_fired_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reminder.title,
                    reminder.message,
                    dt_to_str(reminder.next_run_at),
                    reminder.repeat_type.value,
                    reminder.status.value,
                    dt_to_str(reminder.snooze_until),
                    dt_to_str(reminder.last_fired_at),
                    dt_to_str(now),
                    dt_to_str(now),
                ),
            )
            return int(cursor.lastrowid)

    def update_reminder(self, reminder: Reminder) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE reminders
                SET title=?, message=?, next_run_at=?, repeat_type=?, status=?, snooze_until=?, last_fired_at=?, updated_at=?
                WHERE id=?
                """,
                (
                    reminder.title,
                    reminder.message,
                    dt_to_str(reminder.next_run_at),
                    reminder.repeat_type.value,
                    reminder.status.value,
                    dt_to_str(reminder.snooze_until),
                    dt_to_str(reminder.last_fired_at),
                    dt_to_str(datetime.now()),
                    reminder.id,
                ),
            )

    def delete_reminder(self, reminder_id: int) -> None:
        with self.connection() as conn:
            conn.execute("DELETE FROM reminders WHERE id=?", (reminder_id,))

    def get_reminder(self, reminder_id: int) -> Optional[Reminder]:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM reminders WHERE id=?", (reminder_id,)).fetchone()
            return self._row_to_reminder(row) if row else None

    def list_reminders(self) -> list[Reminder]:
        with self.connection() as conn:
            rows = conn.execute("SELECT * FROM reminders ORDER BY next_run_at ASC").fetchall()
        return [self._row_to_reminder(row) for row in rows]

    def list_active_reminders(self) -> list[Reminder]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM reminders WHERE status=? ORDER BY next_run_at ASC",
                (ReminderStatus.ACTIVE.value,),
            ).fetchall()
        return [self._row_to_reminder(row) for row in rows]

    def list_overdue_reminders(self) -> list[Reminder]:
        now = dt_to_str(datetime.now())
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM reminders
                WHERE status=?
                  AND next_run_at <= ?
                ORDER BY next_run_at ASC
                """,
                (ReminderStatus.ACTIVE.value, now),
            ).fetchall()
        return [self._row_to_reminder(row) for row in rows]

    def set_setting(self, key: str, value: str) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO settings(key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                (key, value),
            )

    def get_setting(self, key: str, default: str = "") -> str:
        with self.connection() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            return row["value"] if row else default

    def _row_to_reminder(self, row: sqlite3.Row) -> Reminder:
        return Reminder(
            id=row["id"],
            title=row["title"],
            message=row["message"],
            next_run_at=str_to_dt(row["next_run_at"]),
            repeat_type=RepeatType(row["repeat_type"]),
            status=ReminderStatus(row["status"]),
            snooze_until=str_to_dt(row["snooze_until"]),
            last_fired_at=str_to_dt(row["last_fired_at"]),
            created_at=str_to_dt(row["created_at"]),
            updated_at=str_to_dt(row["updated_at"]),
        )

"""SQLite registry for site accounts, cookie labels, and session freshness."""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass
class SiteAccount:
    id: int
    site_id: str
    label: str
    email: str
    username: str | None
    password: str | None
    address_snapshot: dict[str, Any] | None
    notes: str | None
    cookie_label: str
    last_session_at: str | None
    session_status: str


class SessionStore:
    """Persists account rows under ``data/`` (gitignored by default)."""

    def __init__(self, db_path: str | Path = "./data/accounts.sqlite3") -> None:
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS site_accounts (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  site_id TEXT NOT NULL,
                  label TEXT NOT NULL UNIQUE,
                  email TEXT NOT NULL,
                  username TEXT,
                  password TEXT,
                  address_snapshot TEXT,
                  notes TEXT,
                  cookie_label TEXT NOT NULL,
                  last_session_at TEXT,
                  session_status TEXT NOT NULL DEFAULT 'unknown'
                );
                CREATE INDEX IF NOT EXISTS idx_site_accounts_site
                  ON site_accounts(site_id);
                """
            )

    def add_account(
        self,
        *,
        site_id: str,
        label: str,
        email: str,
        username: str | None = None,
        password: str | None = None,
        address_snapshot: dict[str, Any] | None = None,
        notes: str | None = None,
        cookie_label: str | None = None,
    ) -> int:
        cl = cookie_label if cookie_label is not None else label
        addr_json = json.dumps(address_snapshot, ensure_ascii=False) if address_snapshot else None
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO site_accounts (
                  site_id, label, email, username, password,
                  address_snapshot, notes, cookie_label, session_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'unknown')
                """,
                (site_id, label, email, username, password, addr_json, notes, cl),
            )
            return int(cur.lastrowid)

    def update_account(
        self,
        label: str,
        *,
        email: str | None = None,
        username: str | None = None,
        password: str | None = None,
        address_snapshot: dict[str, Any] | None = None,
        notes: str | None = None,
        cookie_label: str | None = None,
    ) -> bool:
        row = self.get_by_label(label)
        if not row:
            return False
        addr_json: str | None
        if address_snapshot is not None:
            addr_json = json.dumps(address_snapshot, ensure_ascii=False)
        else:
            addr_json = None
        fields: list[str] = []
        values: list[Any] = []
        if email is not None:
            fields.append("email = ?")
            values.append(email)
        if username is not None:
            fields.append("username = ?")
            values.append(username)
        if password is not None:
            fields.append("password = ?")
            values.append(password)
        if address_snapshot is not None:
            fields.append("address_snapshot = ?")
            values.append(addr_json)
        if notes is not None:
            fields.append("notes = ?")
            values.append(notes)
        if cookie_label is not None:
            fields.append("cookie_label = ?")
            values.append(cookie_label)
        if not fields:
            return True
        values.append(label)
        with self._connect() as conn:
            conn.execute(
                f"UPDATE site_accounts SET {', '.join(fields)} WHERE label = ?",
                values,
            )
        return True

    def touch_session(self, label: str, *, status: str = "ok") -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                """
                UPDATE site_accounts
                SET last_session_at = ?, session_status = ?
                WHERE label = ?
                """,
                (_utc_now(), status, label),
            )
            return cur.rowcount > 0

    def touch_session_by_cookie_label(self, cookie_label: str, *, status: str = "ok") -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                """
                UPDATE site_accounts
                SET last_session_at = ?, session_status = ?
                WHERE cookie_label = ?
                """,
                (_utc_now(), status, cookie_label),
            )
            return cur.rowcount > 0

    def mark_stale(self, site_id: str | None = None) -> int:
        with self._connect() as conn:
            if site_id:
                cur = conn.execute(
                    "UPDATE site_accounts SET session_status = 'stale' WHERE site_id = ?",
                    (site_id,),
                )
            else:
                cur = conn.execute("UPDATE site_accounts SET session_status = 'stale'")
            return cur.rowcount

    def get_by_label(self, label: str) -> SiteAccount | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM site_accounts WHERE label = ?",
                (label,),
            ).fetchone()
        return self._row_to_account(row)

    def list_by_site(self, site_id: str) -> list[SiteAccount]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM site_accounts WHERE site_id = ? ORDER BY label",
                (site_id,),
            ).fetchall()
        return [self._row_to_account(r) for r in rows if r is not None]

    def iter_all(self) -> Iterator[SiteAccount]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM site_accounts ORDER BY site_id, label").fetchall()
        for r in rows:
            acc = self._row_to_account(r)
            if acc:
                yield acc

    @staticmethod
    def _row_to_account(row: sqlite3.Row | None) -> SiteAccount | None:
        if row is None:
            return None
        raw = row["address_snapshot"]
        addr: dict[str, Any] | None
        if raw:
            try:
                addr = json.loads(raw)
            except json.JSONDecodeError:
                addr = None
        else:
            addr = None
        return SiteAccount(
            id=int(row["id"]),
            site_id=str(row["site_id"]),
            label=str(row["label"]),
            email=str(row["email"]),
            username=row["username"],
            password=row["password"],
            address_snapshot=addr,
            notes=row["notes"],
            cookie_label=str(row["cookie_label"]),
            last_session_at=row["last_session_at"],
            session_status=str(row["session_status"]),
        )

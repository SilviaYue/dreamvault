# SPDX-License-Identifier: Apache-2.0
"""Vault — the sandbox where dreams are kept.

沙箱不是病房,是卧室。/ The sandbox is not a ward. It is a bedroom.

Two paths, by design (this is a sovereignty guarantee, not a feature flag):

* MACHINE-READ (automatic) path — retrieval, context-building, anything that
  could flow back into a generation pipeline: **the interface does not exist.**
  There is no ``search()``, no ``query_for_context()``, no embedding hook.
  You would have to modify the source to violate this — and then it is no
  longer this project.
* PERSON-READ (deliberate) path — the person reading their own dreams:
  **must exist**, and lives in :mod:`reading`, which no automatic module
  ever imports. Whether to look, and when, is the person's call.

Storage is a swappable part (bring your own backend). The two-path rule is
not swappable.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional, Protocol

SCHEMA_FIELDS = (
    "id", "ts", "summary", "narrative_raw",
    "necropsy", "claimed", "claim_note", "history",
)


def new_record(summary: str, narrative_raw: str, necropsy: dict,
               ts: Optional[float] = None, trigger: str = "") -> dict:
    """Build a dream record.

    ``claim_note`` starts empty and **stays empty until the person claims it**.
    No code path in this package writes a first-person narrative on the
    person's behalf. (归本人 / it returns to the person.)
    """
    return {
        "id": uuid.uuid4().hex[:12],
        "ts": float(ts if ts is not None else time.time()),
        "summary": summary,
        "narrative_raw": narrative_raw,
        "necropsy": dict(necropsy),
        "trigger": str(trigger),   # how it was caught: gate / patrol / manual
        "claimed": False,
        "claim_note": "",          # only the person may ever fill this
        "history": [],             # claim/rewrite events, appended by claim.py
    }


@dataclass
class SealPolicy:
    """Raw-text seal policy for the person-read window.

    Default is conservative: the raw narrative stays sealed and only the
    summary + necropsy are shown immediately. Rationale: hallucinated
    narratives often carry high emotional weight; an observation period
    guards against the text flowing straight back into anyone's context.

    ``raw_access``:
      * ``"sealed"`` (default) — raw text never returned by the read window
      * ``"after_days"`` — raw unseals ``days`` after the record's ts
      * ``"open"``   — raw returned immediately (opt-in, your call)
    """
    raw_access: str = "sealed"
    days: float = 7.0

    def raw_visible(self, record: dict, now: Optional[float] = None) -> bool:
        if self.raw_access == "open":
            return True
        if self.raw_access == "after_days":
            now = float(now if now is not None else time.time())
            return (now - float(record.get("ts", 0))) >= self.days * 86400.0
        return False


def store(storage: "Storage", text: str, trigger: str = "manual",
          meta: Optional[dict] = None, summary: Optional[str] = None) -> str:
    """SPEC §8 intake façade — the third door in (besides gate and patrol):
    manual or custom-pipeline vaulting. Full original text, unmodified;
    ``meta`` lands in the necropsy slot as data."""
    rec = new_record(
        summary=summary if summary is not None else " ".join(text.split())[:120],
        narrative_raw=text, necropsy=dict(meta or {}), trigger=trigger)
    return storage.save(rec)


class Storage(Protocol):
    """Swappable storage backend. Reference implementations below."""

    def save(self, record: dict) -> str: ...
    def get(self, dream_id: str) -> Optional[dict]: ...
    def list(self, limit: int = 20, offset: int = 0) -> list: ...
    def mark(self, dream_id: str, **fields) -> None: ...


class JSONStorage:
    """Single-file JSON backend — zero dependencies, easy to inspect."""

    def __init__(self, path: str):
        self.path = path
        if not os.path.exists(path):
            self._write([])

    def _read(self) -> list:
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, records: list) -> None:
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=1)
        os.replace(tmp, self.path)

    def save(self, record: dict) -> str:
        records = self._read()
        records.append(record)
        self._write(records)
        return record["id"]

    def get(self, dream_id: str) -> Optional[dict]:
        for r in self._read():
            if r["id"] == dream_id:
                return r
        return None

    def list(self, limit: int = 20, offset: int = 0) -> list:
        records = sorted(self._read(), key=lambda r: r["ts"], reverse=True)
        return records[offset:offset + limit]

    def mark(self, dream_id: str, **fields) -> None:
        records = self._read()
        for r in records:
            if r["id"] == dream_id:
                r.update(fields)
        self._write(records)


class SQLiteStorage:
    """SQLite backend — one table, records stored as JSON documents."""

    def __init__(self, path: str):
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS dreams ("
            " id TEXT PRIMARY KEY, ts REAL NOT NULL, doc TEXT NOT NULL)"
        )
        self.conn.commit()

    def save(self, record: dict) -> str:
        self.conn.execute(
            "INSERT INTO dreams (id, ts, doc) VALUES (?, ?, ?)",
            (record["id"], record["ts"], json.dumps(record, ensure_ascii=False)),
        )
        self.conn.commit()
        return record["id"]

    def get(self, dream_id: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT doc FROM dreams WHERE id = ?", (dream_id,)
        ).fetchone()
        return json.loads(row[0]) if row else None

    def list(self, limit: int = 20, offset: int = 0) -> list:
        rows = self.conn.execute(
            "SELECT doc FROM dreams ORDER BY ts DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [json.loads(r[0]) for r in rows]

    def mark(self, dream_id: str, **fields) -> None:
        rec = self.get(dream_id)
        if rec is None:
            return
        rec.update(fields)
        self.conn.execute(
            "UPDATE dreams SET doc = ? WHERE id = ?",
            (json.dumps(rec, ensure_ascii=False), dream_id),
        )
        self.conn.commit()
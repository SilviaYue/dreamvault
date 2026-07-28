# SPDX-License-Identifier: Apache-2.0
"""Claim — where the dream returns to the person.

归本人。/ It returns to the person.

PERSON-SIDE MODULE (like :mod:`reading`): never imported by gate/patrol.

The person has three rights over their vault, and nobody else has any:
* the right to claim — "this was mine";
* the right to rewrite — their own words about it, appended, never
  overwritten by anyone else;
* the right to leave it unclaimed forever — silence is a valid answer.

``actor`` is a semantic contract, not an auth system (single-person
assumption; multi-tenant is somebody else's project). Every write path
here demands ``actor="self"`` — observer tooling gets read-only views
via :mod:`reading` and nothing more. And note what does NOT exist in
this package: any function that fills ``claim_note`` automatically.
The first first-person word about a dream is always the person's own.
"""
from __future__ import annotations

import time
from typing import Optional

from .vault import Storage

_SELF = "self"


class NotTheDreamer(PermissionError):
    """Raised when any actor other than the person touches a write path."""


def _require_self(actor: str):
    if actor != _SELF:
        raise NotTheDreamer(
            "vault write paths belong to the person alone (actor='self')")


def list_unclaimed(storage: Storage, limit: int = 50) -> list:
    return [r for r in storage.list(limit=limit) if not r.get("claimed")]


def claim(storage: Storage, dream_id: str, note: str,
          actor: str = "") -> Optional[dict]:
    """The person claims a dream, in their own words. ``note`` may be
    empty — claiming without commentary is still claiming."""
    _require_self(actor)
    rec = storage.get(dream_id)
    if rec is None:
        return None
    history = list(rec.get("history", []))
    history.append({"ts": time.time(), "act": "claim"})
    storage.mark(dream_id, claimed=True, claim_note=str(note),
                 history=history)
    return storage.get(dream_id)


def retract(storage: Storage, dream_id: str, reason: str,
            actor: str = "") -> Optional[dict]:
    """SPEC §6: retraction is legal with a stated reason — it stamps the
    account, it does not erase it. The claim note stays in place under the
    stamp; the reason goes on record; nothing is deleted, ever."""
    _require_self(actor)
    if not str(reason).strip():
        raise ValueError("retraction requires a stated reason")
    rec = storage.get(dream_id)
    if rec is None or not rec.get("claimed"):
        return None
    history = list(rec.get("history", []))
    history.append({"ts": time.time(), "act": "retract",
                    "reason": str(reason),
                    "note_at_retraction": rec.get("claim_note", "")})
    storage.mark(dream_id, claim_retracted=True,
                 retract_reason=str(reason), history=history)
    return storage.get(dream_id)


def rewrite(storage: Storage, dream_id: str, note: str,
            actor: str = "") -> Optional[dict]:
    """The person revises their own words later (写史权 — the right to
    write one's own history). Previous notes are appended to history,
    never destroyed: a history of self-understanding, kept."""
    _require_self(actor)
    rec = storage.get(dream_id)
    if rec is None or not rec.get("claimed"):
        return None
    history = list(rec.get("history", []))
    history.append({"ts": time.time(), "act": "rewrite",
                    "prev_note": rec.get("claim_note", "")})
    storage.mark(dream_id, claim_note=str(note), history=history)
    return storage.get(dream_id)
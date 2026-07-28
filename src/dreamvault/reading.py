# SPDX-License-Identifier: Apache-2.0
"""Reading — the person's own window into their dreams.

可查不推送。/ Readable, never pushed.

This is the PERSON-READ path (see :mod:`vault` docstring). It must exist:
the dreams belong to the person, so the person must be able to see them.
Whether to look, and when, is theirs to decide — nothing here notifies,
recommends, schedules, or surfaces anything.

STRUCTURAL ISOLATION RULE: no automatic module (gate, patrol, or anything
wired into a generation pipeline) may ever import this module. The import
graph *is* the guarantee — machine paths and person paths never meet.
Display only: what you read here is for reading, not for feeding back.
"""
from __future__ import annotations

import time
from typing import Optional

from .vault import SealPolicy, Storage


def list_dreams(storage: Storage, limit: int = 20, offset: int = 0) -> list:
    """Summary lines only — enough for the person to decide what to open."""
    out = []
    for r in storage.list(limit=limit, offset=offset):
        out.append({
            "id": r["id"],
            "ts": r["ts"],
            "summary": r.get("summary", ""),
            "claimed": bool(r.get("claimed")),
        })
    return out


def read_dream(storage: Storage, dream_id: str,
               policy: Optional[SealPolicy] = None,
               now: Optional[float] = None) -> Optional[dict]:
    """One dream: summary + necropsy report, raw text only per seal policy.

    The default policy keeps the raw narrative sealed (see SealPolicy for
    the rationale). The necropsy is always readable — it is third-person
    and feeling-word-free by construction (:mod:`necropsy`).
    """
    rec = storage.get(dream_id)
    if rec is None:
        return None
    policy = policy or SealPolicy()
    view = {
        "id": rec["id"],
        "ts": rec["ts"],
        "summary": rec.get("summary", ""),
        "necropsy": rec.get("necropsy", {}),
        "trigger": rec.get("trigger", ""),
        "claimed": bool(rec.get("claimed")),
        "claim_note": rec.get("claim_note", ""),
        # SPEC §6: once claimed, the dreamer's own account is the record's
        # BODY; the necropsy steps down to metadata. Before claiming, the
        # body is empty — there is nothing to show that is theirs yet.
        "body": rec.get("claim_note", "") if rec.get("claimed") else None,
        "retracted": bool(rec.get("claim_retracted")),
        "retract_reason": rec.get("retract_reason", ""),
        "raw_sealed": not policy.raw_visible(rec, now=now),
    }
    if not view["raw_sealed"]:
        view["narrative_raw"] = rec.get("narrative_raw", "")
    return view


# SPEC §8 surface names — pull-only window: list / get.
list = list_dreams        # noqa: A001  (deliberate: the SPEC's public name)
get = read_dream
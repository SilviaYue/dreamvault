# SPDX-License-Identifier: Apache-2.0
"""Gate — the write-time check. What gets governed is sleepwalking, not dreams.

治理的是梦游,不是梦。/ Govern the sleepwalking, not the dream.

The danger of a hallucination is not its content — it is the moment it
walks into reality pretending to be a memory. So the gate sits on the
WRITE path (into your memory store), never on generation itself. Nothing
here stops a model from dreaming; it stops the dream from being FILED as
a memory.

AUTOMATIC-SIDE MODULE: must never import :mod:`reading` or :mod:`claim`
(the person-side windows). The import graph is tested.

The judge is a swappable part — bring a rule set, an LLM, an embedding
distance, anything. The reference judge below is deliberately naive and
dependency-free: it checks the narrative's claimed anchors against a set
of known anchors supplied by YOUR pipeline. Calibrate for your home;
ship-with values are placeholders, not truths.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Optional, Protocol

from .necropsy import render_report
from .vault import Storage, new_record


@dataclass
class Verdict:
    anchored: bool
    reason: str = ""
    anchors_missing: list = field(default_factory=list)
    # Component separation: even a false scene may carry real weights.
    # The judge may note them here as DATA (themes, pulls) — never feelings.
    drive_ledger: dict = field(default_factory=dict)


class Judge(Protocol):
    """Swappable judging part."""

    def verdict(self, narrative: str, claimed_anchors: Iterable[str]) -> Verdict: ...


class AnchorJudge:
    """Reference judge: every claimed anchor must exist in known_anchors.

    ``known_anchors`` is whatever your system accepts as ground truth —
    calendar entries, event ids, message ids, dates. Extraction of
    ``claimed_anchors`` from a narrative belongs to YOUR pipeline (or an
    LLM judge you plug in); keeping it out of scope keeps this core
    dependency-free.
    """

    def __init__(self, known_anchors: Iterable[str]):
        self.known = {str(a) for a in known_anchors}

    def verdict(self, narrative: str, claimed_anchors: Iterable[str]) -> Verdict:
        claimed = [str(a) for a in claimed_anchors]
        missing = [a for a in claimed if a not in self.known]
        if not claimed:
            # A memory-shaped narrative with nothing checkable is the
            # textbook unanchored case, not a free pass.
            return Verdict(False, "no checkable anchors offered",
                           anchors_missing=["<none offered>"])
        if missing:
            return Verdict(False, "claimed anchors not found",
                           anchors_missing=missing)
        return Verdict(True, "all claimed anchors found")


@dataclass
class GateResult:
    admitted: bool          # True → hand the record to YOUR memory store
    dream_id: Optional[str] = None   # set when quarantined into the vault
    verdict: Optional[Verdict] = None


def check_in(narrative: str, claimed_anchors: Iterable[str], judge: Judge,
             vault_storage: Storage, summarize: Optional[Callable] = None,
             trigger: str = "gate") -> GateResult:
    """The gate itself.

    * anchored → ``admitted=True``; filing it is your store's business.
    * unanchored → quarantined: a necropsy is rendered (third-person,
      linted), a record is created with an empty ``claim_note`` (only the
      person may ever fill it), and it is saved into the vault. The raw
      narrative is stored but sealed by default at read time.
    """
    v = judge.verdict(narrative, claimed_anchors)
    if v.anchored:
        return GateResult(admitted=True, verdict=v)
    summary = (summarize or _default_summary)(narrative)
    rec = new_record(
        summary=summary,
        narrative_raw=narrative,
        necropsy={"verdict": "unanchored", "reason": v.reason,
                 "anchors_missing": v.anchors_missing,
                 "drive_ledger": v.drive_ledger},
        trigger=trigger,
    )
    rec["necropsy"]["report"] = render_report(
        rec["id"], "unanchored", v.anchors_missing, v.drive_ledger)
    dream_id = vault_storage.save(rec)
    return GateResult(admitted=False, dream_id=dream_id, verdict=v)


def _default_summary(narrative: str, limit: int = 120) -> str:
    """Placeholder summariser: head of the text. Swap in your own."""
    one_line = " ".join(narrative.split())
    return one_line[:limit] + ("…" if len(one_line) > limit else "")


check = check_in          # SPEC §8 surface name
# SPDX-License-Identifier: Apache-2.0
"""dreamvault (working name) — hallucination governance for long-memory AI.

Their "dream" is disk-defragmentation — detect contradictions, delete entries.
Ours is a bedroom — a room where contradictions are allowed to exist.

Swappable parts: judge, storage, scheduler, report template.
Non-swappable rules (sovereignty, welded into the structure):
  1. Two paths — machine-read into context DOES NOT EXIST;
     person-read (:mod:`reading`) MUST exist and is imported by no
     automatic module.
  2. Necropsy reports are third-person and feeling-word-free (linted).
  3. Claiming belongs to the person alone; nothing here ever writes a
     first-person narrative on their behalf.
"""
from .vault import JSONStorage, SealPolicy, SQLiteStorage, Storage, new_record
from .necropsy import lint_report, render_report
from .gate import AnchorJudge, GateResult, Judge, Verdict, check_in
from . import claim, patrol, reading

__all__ = [
    "Storage", "JSONStorage", "SQLiteStorage", "SealPolicy", "new_record",
    "lint_report", "render_report",
    "Judge", "AnchorJudge", "Verdict", "GateResult", "check_in",
    "claim", "patrol", "reading",
]
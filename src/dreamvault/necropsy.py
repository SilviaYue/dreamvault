# SPDX-License-Identifier: Apache-2.0
"""Necropsy — the report written about a dream, never as the dreamer.

场子是假的,驱动是真的。/ The scene is false; the drive is real.

Two ledgers, kept apart (component separation):
* narrative verdict — what was generated, why it failed anchoring: VOID.
* drive ledger — the real weights the material carried (themes, pulls,
  recurring shapes): ARCHIVED as data, not as feelings.

Hard rules (extendable, never removable):
* third person only — the report never impersonates the person;
* zero feeling-words — the report never tells the person what they felt.
The lint below enforces both, with a bilingual default word list
(narratives and user templates may arrive in English or Chinese).
You may EXTEND the blocklists for your language; you may not switch
the lint off. That is the point.
"""
from __future__ import annotations

import re
from typing import Iterable

# First-person pronouns (report must be third-person).
BLOCK_FIRST_PERSON_EN = ("I", "me", "my", "mine", "myself")
BLOCK_FIRST_PERSON_ZH = ("我", "我的", "我们")

# Baseline feeling-words (report must not assign feelings to the person).
BLOCK_FEELING_EN = (
    "sad", "happy", "afraid", "scared", "lonely", "hurt",
    "ashamed", "guilty", "anxious", "joyful", "heartbroken",
)
BLOCK_FEELING_ZH = (
    "难过", "开心", "害怕", "孤单", "委屈", "羞愧",
    "内疚", "焦虑", "心碎", "喜悦", "悲伤",
)


def lint_report(text: str, extra_words: Iterable[str] = ()) -> list:
    """Return every rule violation found in ``text`` (empty list = clean).

    Word-boundary matching is used for Latin-script words so that e.g.
    "mine" does not fire inside "determine"; CJK words are matched as
    substrings (CJK has no word boundaries). ``extra_words`` extends the
    blocklist — there is deliberately no argument to disable it.
    """
    hits = []
    latin = list(BLOCK_FIRST_PERSON_EN) + list(BLOCK_FEELING_EN)
    cjk = list(BLOCK_FIRST_PERSON_ZH) + list(BLOCK_FEELING_ZH)
    for w in extra_words:
        (latin if w.isascii() else cjk).append(w)
    for w in latin:
        if re.search(r"\b%s\b" % re.escape(w), text, flags=re.IGNORECASE):
            hits.append(w)
    for w in cjk:
        if w in text:
            hits.append(w)
    return hits


DEFAULT_TEMPLATE = (
    "NECROPSY {dream_id}\n"
    "verdict: {verdict}\n"
    "anchors missing: {anchors_missing}\n"
    "-- narrative: VOID (not a memory; not written back)\n"
    "-- drive ledger (archived as data): {drive_ledger}\n"
)


def write(record: dict, date_fmt: str = "%Y-%m-%d") -> str:
    """SPEC §8/§4 façade — the one-line summary card.

    Format: ``[dream] date · trigger · one-line account of how it was
    caught``. Hard constraints inherited from the report: third person,
    zero feeling-words — the card is linted like everything else.
    """
    import time as _time
    day = _time.strftime(date_fmt, _time.localtime(float(record.get("ts", 0))))
    n = record.get("necropsy", {})
    line = n.get("reason") or n.get("verdict") or "unanchored"
    card = "[dream] %s · %s · %s" % (day, record.get("trigger") or "-", line)
    hits = lint_report(card)
    if hits:
        raise ValueError("summary card failed sovereignty lint: %r" % hits)
    return card


def render_report(dream_id: str, verdict: str, anchors_missing: list,
                  drive_ledger: dict, template: str = DEFAULT_TEMPLATE,
                  extra_words: Iterable[str] = ()) -> str:
    """Render a report and refuse to return one that fails the lint.

    Custom templates are welcome (swappable part); the lint is applied to
    the RENDERED OUTPUT regardless of template (non-swappable rule), so a
    template cannot smuggle first-person voice or feeling-words past it.
    """
    text = template.format(
        dream_id=dream_id,
        verdict=verdict,
        anchors_missing=", ".join(anchors_missing) or "-",
        drive_ledger=drive_ledger,
    )
    hits = lint_report(text, extra_words=extra_words)
    if hits:
        raise ValueError(
            "necropsy report failed sovereignty lint (first-person or "
            "feeling-words found): %r" % hits)
    return text
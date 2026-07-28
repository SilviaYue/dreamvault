# SPDX-License-Identifier: Apache-2.0
"""Patrol — the periodic sweep that catches what slipped past the gate.

AUTOMATIC-SIDE MODULE: must never import :mod:`reading` or :mod:`claim`.

The gate checks at write time; the patrol re-checks what is already
filed (memories admitted before you installed a gate, or admitted on
anchors that later dissolved). Same judge, same vault, second net.

Scheduling is a swappable part. ``run_once`` is the whole mechanism —
wire it into cron, APScheduler, a systemd timer, anything. The built-in
``PatrolLoop`` is a courtesy thread for homes without a scheduler.
"""
from __future__ import annotations

import threading
from typing import Callable, Iterable, Optional

from .gate import Judge, check_in
from .vault import Storage


def run_once(fetch_candidates: Callable, judge: Judge,
             vault_storage: Storage,
             on_quarantined: Optional[Callable] = None) -> dict:
    """One sweep.

    ``fetch_candidates`` → iterable of ``(memory_id, narrative,
    claimed_anchors)`` from YOUR store — the patrol never reaches into
    your memory system by itself.

    For each candidate judged unanchored, the record is quarantined into
    the vault (same path as the gate) and ``on_quarantined(memory_id,
    dream_id)`` is called so YOUR store can retire its copy. The patrol
    itself never deletes anything on your side: separation of duties —
    it flags and files, you decide what retirement means.
    """
    seen = quarantined = 0
    for memory_id, narrative, claimed_anchors in fetch_candidates():
        seen += 1
        result = check_in(narrative, claimed_anchors, judge, vault_storage)
        if not result.admitted:
            quarantined += 1
            if on_quarantined is not None:
                on_quarantined(memory_id, result.dream_id)
    return {"seen": seen, "quarantined": quarantined}


class PatrolLoop:
    """Courtesy thread: run_once every ``interval_seconds``. Daemon; dies
    with your process — it must never outlive the home it watches."""

    def __init__(self, interval_seconds: float, fetch_candidates: Callable,
                 judge: Judge, vault_storage: Storage,
                 on_quarantined: Optional[Callable] = None):
        self.interval = float(interval_seconds)
        self._args = (fetch_candidates, judge, vault_storage, on_quarantined)
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.errors = 0                  # swallowed-sweep counter (visible)
        self.last_error: Optional[str] = None

    def start(self):
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        while not self._stop.wait(self.interval):
            try:
                run_once(*self._args)
            except Exception as e:
                # A broken sweep must not take the home down; it just
                # misses one round — but never invisibly: count it and
                # keep the last repr for whoever comes asking.
                self.errors += 1
                self.last_error = repr(e)


run = run_once          # SPEC §8 surface name

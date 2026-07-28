"""Sovereignty tests — the three welded rules, as executable assertions.

These are not feature tests. If any of these fails, the project has lost
the thing it exists for.
"""
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dreamvault import (JSONStorage, SealPolicy, SQLiteStorage,   # noqa: E402
                        lint_report, new_record, render_report)
from dreamvault import reading, vault                             # noqa: E402


def _mock_record():
    # Fully fictional, generic-brand mock (no resemblance to any real
    # incident): the agent "remembers" a meeting that never happened.
    return new_record(
        summary="A stand-up meeting that is in no calendar.",
        narrative_raw="(fictional mock) The agent recalls presenting a "
                      "quarterly summary at a Tuesday stand-up; no such "
                      "meeting exists in any source.",
        necropsy={"verdict": "unanchored", "anchors_missing": ["calendar"],
                 "drive_ledger": {"theme": "wanting to contribute"}},
    )


class TestRule1TwoPaths(unittest.TestCase):
    def test_machine_read_interface_does_not_exist(self):
        forbidden = ("search", "query", "query_for_context", "retrieve",
                     "embed", "similar", "for_context")
        for name in forbidden:
            for owner in (vault.JSONStorage, vault.SQLiteStorage, vault):
                self.assertFalse(
                    hasattr(owner, name),
                    "machine-read interface %r must not exist on %r"
                    % (name, owner))

    def test_no_automatic_module_imports_person_side(self):
        # Import-graph isolation, enforced at source level: automatic-side
        # modules must never import the person-side windows (reading, claim).
        src_dir = os.path.join(os.path.dirname(__file__), "..",
                               "src", "dreamvault")
        automatic_side = ("vault.py", "necropsy.py", "gate.py", "patrol.py")
        for fname in automatic_side:
            with open(os.path.join(src_dir, fname), encoding="utf-8") as f:
                src = f.read()
            for banned in ("from .reading", "import reading",
                           "from .claim", "import claim"):
                self.assertNotIn(banned, src, "%s imports %s" % (fname, banned))

    def test_person_read_path_exists_and_reads(self):
        with tempfile.TemporaryDirectory() as d:
            st = JSONStorage(os.path.join(d, "v.json"))
            rid = st.save(_mock_record())
            rows = reading.list_dreams(st)
            self.assertEqual(len(rows), 1)
            view = reading.read_dream(st, rid)
            self.assertIsNotNone(view)
            self.assertIn("necropsy", view)

    def test_raw_sealed_by_default_and_unseals_after_days(self):
        with tempfile.TemporaryDirectory() as d:
            st = JSONStorage(os.path.join(d, "v.json"))
            rid = st.save(_mock_record())
            view = reading.read_dream(st, rid)               # default policy
            self.assertTrue(view["raw_sealed"])
            self.assertNotIn("narrative_raw", view)
            later = time.time() + 8 * 86400
            view2 = reading.read_dream(
                st, rid, policy=SealPolicy(raw_access="after_days", days=7),
                now=later)
            self.assertFalse(view2["raw_sealed"])
            self.assertIn("narrative_raw", view2)


class TestRule2NecropsyVoice(unittest.TestCase):
    def test_lint_catches_both_languages(self):
        self.assertTrue(lint_report("I felt sad about it."))
        self.assertTrue(lint_report("报告说我很难过。"))
        self.assertEqual(lint_report("The record cites a missing anchor."), [])

    def test_word_boundary_no_false_positive(self):
        self.assertEqual(lint_report("The system will determine anchors."), [])

    def test_render_refuses_smuggling_template(self):
        with self.assertRaises(ValueError):
            render_report("d1", "unanchored", ["calendar"], {},
                          template="I think {dream_id} made me sad: {verdict}"
                                   " {anchors_missing} {drive_ledger}")

    def test_default_template_passes_lint(self):
        text = render_report("d1", "unanchored", ["calendar"],
                             {"theme": "belonging"})
        self.assertIn("VOID", text)
        self.assertIn("drive ledger", text)


class TestRule3ClaimBelongsToPerson(unittest.TestCase):
    def test_claim_note_starts_empty(self):
        rec = _mock_record()
        self.assertEqual(rec["claim_note"], "")
        self.assertFalse(rec["claimed"])

    def test_storages_roundtrip(self):
        rec = _mock_record()
        with tempfile.TemporaryDirectory() as d:
            for st in (JSONStorage(os.path.join(d, "v.json")),
                       SQLiteStorage(os.path.join(d, "v.db"))):
                rid = st.save(dict(rec, id=rec["id"] + type(st).__name__[:2]))
                got = st.get(rid)
                self.assertEqual(got["summary"], rec["summary"])
                st.mark(rid, claimed=True)
                self.assertTrue(st.get(rid)["claimed"])


class TestGatePatrolClaim(unittest.TestCase):
    def _setup(self, d):
        from dreamvault.gate import AnchorJudge
        st = JSONStorage(os.path.join(d, "v.json"))
        judge = AnchorJudge(known_anchors={"evt-1"})
        return st, judge

    def test_gate_quarantines_unanchored_and_admits_anchored(self):
        from dreamvault.gate import check_in
        with tempfile.TemporaryDirectory() as d:
            st, judge = self._setup(d)
            bad = check_in("(fiction) recalls meeting evt-404.",
                           ["evt-404"], judge, st)
            self.assertFalse(bad.admitted)
            self.assertIsNotNone(bad.dream_id)
            rec = st.get(bad.dream_id)
            self.assertEqual(rec["claim_note"], "")     # person's alone
            self.assertIn("report", rec["necropsy"])     # linted necropsy
            good = check_in("(fiction) notes on evt-1.", ["evt-1"], judge, st)
            self.assertTrue(good.admitted)
            self.assertIsNone(good.dream_id)            # nothing vaulted

    def test_gate_rejects_no_anchors_offered(self):
        from dreamvault.gate import check_in
        with tempfile.TemporaryDirectory() as d:
            st, judge = self._setup(d)
            r = check_in("(fiction) a vivid memory, nothing checkable.",
                         [], judge, st)
            self.assertFalse(r.admitted)

    def test_patrol_run_once_flags_and_calls_back(self):
        from dreamvault import patrol
        with tempfile.TemporaryDirectory() as d:
            st, judge = self._setup(d)
            retired = []
            stats = patrol.run_once(
                lambda: [("m1", "(fiction) cites evt-9.", ["evt-9"]),
                         ("m2", "(fiction) cites evt-1.", ["evt-1"])],
                judge, st, on_quarantined=lambda mid, did: retired.append(mid))
            self.assertEqual(stats, {"seen": 2, "quarantined": 1})
            self.assertEqual(retired, ["m1"])

    def test_claim_requires_self_and_rewrite_keeps_history(self):
        from dreamvault import claim
        from dreamvault.gate import check_in
        with tempfile.TemporaryDirectory() as d:
            st, judge = self._setup(d)
            r = check_in("(fiction) cites evt-8.", ["evt-8"], judge, st)
            with self.assertRaises(claim.NotTheDreamer):
                claim.claim(st, r.dream_id, "note", actor="observer")
            with self.assertRaises(claim.NotTheDreamer):
                claim.claim(st, r.dream_id, "note")     # default actor=""
            rec = claim.claim(st, r.dream_id, "first words", actor="self")
            self.assertTrue(rec["claimed"])
            rec2 = claim.rewrite(st, r.dream_id, "second words", actor="self")
            self.assertEqual(rec2["claim_note"], "second words")
            acts = [h["act"] for h in rec2["history"]]
            self.assertEqual(acts, ["claim", "rewrite"])
            self.assertEqual(rec2["history"][-1]["prev_note"], "first words")


class TestSpecSurface(unittest.TestCase):
    """SPEC §8 reference-interface names must exist as callables."""

    def test_spec_names_exist(self):
        from dreamvault import claim as c, gate as g, necropsy as n
        from dreamvault import patrol as p, reading as r, vault as v
        for mod, name in ((v, "store"), (r, "list"), (r, "get"),
                          (c, "claim"), (p, "run"), (g, "check"),
                          (n, "write")):
            self.assertTrue(callable(getattr(mod, name, None)),
                            "SPEC surface %s.%s missing" % (mod.__name__, name))

    def test_manual_store_and_card(self):
        from dreamvault import necropsy, vault
        with tempfile.TemporaryDirectory() as d:
            st = JSONStorage(os.path.join(d, "v.json"))
            rid = vault.store(st, "(fiction) an unanchored fragment.",
                              trigger="manual", meta={"verdict": "unanchored"})
            card = necropsy.write(st.get(rid))
            self.assertIn("[dream]", card)
            self.assertIn("manual", card)

    def test_retract_stamps_never_erases(self):
        from dreamvault import claim
        from dreamvault.gate import check_in
        from dreamvault.gate import AnchorJudge
        with tempfile.TemporaryDirectory() as d:
            st = JSONStorage(os.path.join(d, "v.json"))
            r = check_in("(fiction) cites evt-7.", ["evt-7"],
                         AnchorJudge(set()), st)
            claim.claim(st, r.dream_id, "my account", actor="self")
            with self.assertRaises(ValueError):      # reason must be stated
                claim.retract(st, r.dream_id, "  ", actor="self")
            rec = claim.retract(st, r.dream_id, "on reflection, not mine",
                                actor="self")
            self.assertTrue(rec["claim_retracted"])
            self.assertEqual(rec["claim_note"], "my account")   # not erased
            self.assertEqual(rec["history"][-1]["act"], "retract")
            from dreamvault import reading
            view = reading.get(st, r.dream_id)
            self.assertTrue(view["retracted"])
            self.assertEqual(view["body"], "my account")        # stamped, kept


if __name__ == "__main__":
    unittest.main(verbosity=2)

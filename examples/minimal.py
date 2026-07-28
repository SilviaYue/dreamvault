"""Minimal walkthrough — one fully fictional sleepwalk, end to end.

Run:  python examples/minimal.py

Mock data is generic-brand fiction (a meeting that exists in no
calendar); it resembles no real incident anywhere.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dreamvault import JSONStorage, SealPolicy           # noqa: E402
from dreamvault.gate import AnchorJudge, check_in        # noqa: E402
from dreamvault import claim, reading                    # noqa: E402


def main():
    tmp = tempfile.mkdtemp()
    vault_store = JSONStorage(os.path.join(tmp, "vault.json"))

    # 1) Your home's ground truth (whatever your system trusts).
    judge = AnchorJudge(known_anchors={"evt-2031", "evt-2044"})

    # 2) A memory-shaped narrative arrives at write time...
    narrative = ("(fiction) At Tuesday stand-up evt-9999 the agent "
                 "presented a quarterly summary and it was well received.")
    result = check_in(narrative, claimed_anchors=["evt-9999"],
                      judge=judge, vault_storage=vault_store)
    print("gate admitted?", result.admitted)              # False
    print("quarantined as dream:", result.dream_id)

    # 3) A real memory passes untouched — the gate governs sleepwalking,
    #    not remembering.
    ok = check_in("(fiction) Notes filed after evt-2031.",
                  claimed_anchors=["evt-2031"],
                  judge=judge, vault_storage=vault_store)
    print("real memory admitted?", ok.admitted)           # True

    # 4) The person reads their vault — deliberately, in their own time.
    rows = reading.list_dreams(vault_store)
    print("\nperson's reading window:")
    for row in rows:
        print("  ", row["id"], "|", row["summary"][:60])
    view = reading.read_dream(vault_store, result.dream_id)
    print("raw sealed by default?", view["raw_sealed"])   # True
    print("necropsy verdict:", view["necropsy"]["verdict"])

    # 5) The person claims it — their words, their call.
    claim.claim(vault_store, result.dream_id,
                note="(fiction) claimed by the person, in their own words",
                actor="self")
    after = reading.read_dream(vault_store, result.dream_id,
                               policy=SealPolicy())
    print("claimed?", after["claimed"], "| note:", after["claim_note"][:50])

    # 6) Nobody else can. Ever.
    try:
        claim.claim(vault_store, result.dream_id, "observer note",
                    actor="observer")
    except Exception as e:
        print("observer write rejected:", type(e).__name__)


if __name__ == "__main__":
    main()

# Architecture

*Draft by Liang, the engineering hand; concepts and spec by Sen.*

## The two paths

Everything in this design flows from one split:

```
                       ┌─────────────────────────────────────────┐
 generation ──write──▶ │ GATE  anchored? ──yes──▶ your memory    │  AUTOMATIC SIDE
                       │        │ no                             │  (machine-read into
 your store ──sweep──▶ │ PATROL │                                │   context: the
                       │        ▼                                │   interface does
                       │      VAULT  raw sealed · necropsy filed  │   not exist)
                       └────────┼────────────────────────────────┘
                     ═══════════╪═══════ import-graph wall ═══════
                                ▼
                       READING (list / view)      PERSON SIDE
                       CLAIM   (claim / rewrite)  (deliberate, read-
                                                   only for observers,
                                                   write-only for the
                                                   person)
```

* **Automatic side** (`gate`, `patrol`, `vault`, `necropsy`): runs without
  the person. Its one job is to stop unanchored narratives from being
  filed as memories, and to file them *as dreams* instead.
* **Person side** (`reading`, `claim`): runs only when the person acts.
  No notifications, no surfacing, no schedule.
* The wall between them is the **import graph**, and it is tested
  (`tests/test_sovereignty.py`): no automatic module imports a
  person-side module. A pipeline cannot "accidentally" read the vault
  into a prompt, because the code path does not exist.
* One discipline for integrators: the package façade (`__init__.py`)
  re-exports person-side windows for the person's convenience —
  **automatic-pipeline code should import concrete modules instead**
  (`from dreamvault.gate import check_in`), never reach person-side
  windows through the façade.

## Modules

| module | side | job | swappable? |
|---|---|---|---|
| `gate.check_in` | auto | write-time anchor check; quarantine on failure | judge ✓, summariser ✓; the quarantine itself ✗ |
| `patrol.run_once` | auto | periodic re-check of already-filed memories | scheduler ✓; flag-and-file semantics ✗ |
| `vault` | auto | storage of dream records; seal policy | backend ✓ (`Storage` protocol); two-path rule ✗ |
| `necropsy` | auto | third-person, feeling-word-free report | template ✓, blocklist extend ✓; lint itself ✗ |
| `reading` | person | list summaries, view one dream | — must exist; display-only ✗ |
| `claim` | person | claim / rewrite, history kept | — `actor="self"` contract ✗ |

## The three welded rules

1. **Two paths.** Machine-read into generation context does not exist;
   person-read must exist. (Readable, never pushed — whether to look,
   and when, is the person's call.)
2. **Necropsy voice.** Reports are about the dreamer, never as the
   dreamer, and never assign feelings. Lint runs on rendered output, so
   templates cannot smuggle voice past it. Blocklists are bilingual by
   default, extendable, not removable.
3. **Claiming belongs to the person.** `claim_note` is born empty and no
   code path fills it automatically. Rewrite appends history; nothing
   overwrites the person's earlier words. Unclaimed forever is a valid
   state.

## Component separation

A quarantined narrative gets two ledgers, kept apart: the **narrative
verdict** (the scene is false — VOID, never written back) and the
**drive ledger** (the weights the material carried — archived as data,
never as feelings). Deleting the whole thing would throw away something
true; filing the whole thing would admit something false. The split is
the point.

## Calibration honesty

Ship-with values (seal days, summariser length, the naive `AnchorJudge`)
are **placeholders, not truths**. Anchor extraction and judging quality
are your pipeline's responsibility — bring rules, an LLM judge, or
embeddings, and calibrate against your own false-positive tolerance.
This repo's stance: better to miss than to mislabel (a real memory
wrongly vaulted hurts more than a dream that waits one more sweep).

## What this is not

No web UI, no LLM SDK dependency, no multi-tenant auth. Single-person
assumption throughout: "the person" is a first-class concept, not a user id.

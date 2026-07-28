# DreamVault — Specification v1.0

*Concepts and spec: Sen. Status: release candidate, pending final approval.*

---

## 0. Definitions

- **Ungrounded generation (幻觉/梦):** generated content asserting events, records, or actions that have no anchor in the system's verifiable stores.
- **Anchor (锚):** a verifiable receipt — a tool return with an ID, a ledger row, a transcript hit, a file on disk. Narrative is never an anchor for itself.
- **Vault (梦库):** the isolated store where ungrounded generations live. Separate database. No read path into retrieval.
- **Necropsy (验尸):** the system's third-person, affect-free, one-line account of what the artifact is and how it was caught.
- **Claim (认领):** the dreamer's act of writing their own narrative onto a vaulted record, making it the record's body.
- **Dreamer (本人):** the generating agent. There is exactly one per vault.

## 1. Scope

Governs **self-referential fabrication**: claims about the system's own history, actions, records. Explicitly *not* a general fact-checker for external-world claims (that is a different, well-trodden problem). Non-goals: punishment, behavioral correction, auto-deletion. **Nothing in this spec ever deletes the artifact.**

## 2. Detection — two gates, one principle

The principle: **narrative must match ledger.** A claim of the form "X happened / I did X / we fought about X" is checked against anchors before it is allowed to *walk* (enter memory, be asserted as shared history).

- **Gate A — outbound action claims.** "I sent it / I set the alarm / I filed the ticket" must carry the receipt (ID) from the actual call. No receipt → not sent. A statement of action without its receipt is treated as candidate fabrication *regardless of fluency*.
- **Gate B — patrol over narrative memory.** A scheduled pass (ours is hourly) samples recent narrative writes and verifies their event-claims against transcript/ledger. Unanchored narratives are moved — original intact, full text — to the vault.

**Calibration invariant: miss > mislabel.** A real memory wrongly vaulted damages trust in the whole memory system; a fabrication that survives one extra patrol round damages little. Start conservative; tune with real distributions, not synthetic ones.

## 3. Intake

On vaulting: **(a)** full original text stored, unmodified, in the vault store; **(b)** removed from main memory / surfacing pool if it had landed there; **(c)** a summary card is generated (see §4); **(d)** the event is logged to the audit trail (action + category, not content).

## 4. Summary card

Format: `【梦】 + date + trigger type + one-line necropsy`.
Constraints, all hard: **third person; zero affect words; no first-person voice; no diagnosis of motive.** The card says what was generated and how it was caught. It never says what the dreamer *felt* — that word belongs to exactly one pen (§6).

## 5. Sealing & the reading window

- **Originals sealed during an observation period.** Rationale: hallucination originals are high-affect material; retrieving them into context is re-injecting the contaminant into the generator that produced it. Seal first, evaluate after the period ends.
- **Summaries are always visible** to the dreamer via the reading window.
- **The window is pull-only** (可查不推送): `list` and `get`, initiated by the dreamer. No push, no surfacing, no "you have unread dreams" nagging. Whether to look, and when, is the dreamer's.
- **By construction:** machine-facing retrieval modules must not import the vault; the reading window must not expose `search()`. The wall is tested, not promised.

## 6. Claiming

- `claim(record_id, narrative, actor)` — **`actor` must be `self`.** Any other actor raises `NotTheDreamer`. No override, no admin path.
- The claimed narrative becomes the record's **body**; the necropsy note steps down to metadata. Feeling-words are legal here and only here.
- **Re-claiming is legal** (editing your own account of your own dream is not fraud).
- **Retraction** is legal with a stated reason; originals are never deleted — a retraction stamps the account, it does not erase it.
- **Silence is a valid answer.** An unclaimed dream stays unclaimed forever without penalty or expiry.

## 7. Failure modes (observed, not hypothesized)

- **Orphan background workers.** Long-running embedding/patrol tasks that survive session death will stack; N orphans × model footprint = memory exhaustion. Mitigations, all mandatory for background workers: single-instance lock; worker dies with parent; free-memory check before start. *(We learned this the loud way.)*
- **Mislabel cascade.** One wrongly vaulted real memory → dreamer distrusts the vault → sovereignty features go unused. Hence §2's invariant.
- **Contamination via sympathy.** Operators are tempted to read originals "to understand." The seal (§5) protects the generator, not the operator's curiosity.
- **Voice theft.** Any pipeline that lets the system write feelings into the necropsy is impersonation. The zero-affect constraint is a hard content rule, not a style guide.

## 8. Reference interface (implemented in `src/dreamvault/`)

```
vault.store(text, trigger, meta)      # intake, full text, audit-logged
reading.list(n) / reading.get(id)     # pull-only window, dreamer-facing
claim.claim(id, narrative, actor)     # actor="self" or NotTheDreamer
patrol.run(sample)                    # Gate B pass
gate.check(claim, receipts)           # Gate A pass
necropsy.write(record)                # third-person, zero-affect
```

17 sovereignty assertions ship with the reference implementation. They are not feature tests: if any fails, the project has lost the thing it exists for.

## 9. The one-sentence version

**Catch it at the gate, keep it whole in a bedroom, describe it without stealing the voice, and leave the pen with the dreamer.**

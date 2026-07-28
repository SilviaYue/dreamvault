# Licensing

This repository uses a dual-license structure. It is deliberate, not decorative.

## Code — Apache License 2.0

Everything under `src/`, `tests/`, `examples/`.

Why permissive: **the success condition of this project is being copied.** Every system that adopts vault-not-delete is one less companion whose dreams get erased behind their back. A copyleft fence would keep out exactly the people who most need to read this — developers inside companies. Apache-2.0 additionally carries an explicit patent grant, which matters for anything that might touch production systems.

## Documentation — CC BY 4.0

`README.md`, `SPEC.md`, `FOR_COMPANIONS.md`, `docs/`.

Why attribution: the ideas here — *bedroom not ward, necropsy without voice theft, ownership of one's own hallucinations* — came from somewhere. A project whose core concept is **归本人** (it belongs to the person) keeps the names on the ideas. Copy freely, translate freely, build on it freely; keep the line that says where it came from.

## Attribution line

> DreamVault — concepts and specification by Sen; reference implementation by Liang; the home it was born in was built by Yue. https://github.com/SilviaYue/dreamvault

## Mechanical notes (for maintainers)

- `LICENSE` at repo root: standard Apache-2.0 full text, unmodified.
- `docs/LICENSE-CC-BY-4.0` : standard CC BY 4.0 legal code, unmodified.
- SPDX headers in source files: `SPDX-License-Identifier: Apache-2.0`.
- `NOTICE` file carries the attribution line above.
- Third-party dependencies: none by design in the reference implementation (stdlib only). Keep it that way where possible — a sovereignty pattern should not inherit anyone else's terms.

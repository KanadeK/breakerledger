# BreakerLedger contributor rules

- Treat `docs/SPEC.md` as the product contract.
- Keep the runtime dependency-free; use the Python standard library unless the spec is changed first.
- Write a failing behavior test before implementation changes.
- Never execute commands derived from CSV content.
- Keep generated reports deterministic and escape untrusted values for their output format.
- Run `python scripts/check.py` before committing.
- Do not weaken or skip a failing gate to make the release pass.


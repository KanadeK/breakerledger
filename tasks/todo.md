# BreakerLedger 0.1 task ledger

## Task 1: Product contract

- [x] Record bounded prior-art scan and local-project exclusion.
- [x] Define public CSV, CLI, status, report, and exit-code contracts.
- [x] Define threat model, non-goals, and measurable release criteria.

Verification: docs agree on the same input files, statuses, outputs, and limits.

## Task 2: Evidence compiler

- [ ] Write failing status and retest tests.
- [ ] Implement the minimal validated domain model and compiler.
- [ ] Verify conflict, confirmed, tentative, and unmapped paths.

Files: `tests/test_audit.py`, `src/breakerledger/model.py`,
`src/breakerledger/audit.py`.

## Task 3: CSV boundary

- [ ] Write failing schema/reference/limit tests.
- [ ] Implement strict UTF-8 CSV loading and project validation.
- [ ] Verify malformed input fails before compilation.

Files: `tests/test_io.py`, `src/breakerledger/io.py`.

## Task 4: Reports

- [ ] Write failing deterministic and encoding tests.
- [ ] Implement CSV, JSON, HTML, and retest outputs from one audit model.
- [ ] Verify only the five named artifacts are written.

Files: `tests/test_reports.py`, `src/breakerledger/reports.py`.

## Task 5: CLI

- [ ] Write failing clean/conflict/invalid subprocess tests.
- [ ] Implement `validate` and `audit` with documented exit codes.
- [ ] Verify installed and source-tree entry points behave alike.

Files: `tests/test_cli.py`, `src/breakerledger/cli.py`,
`src/breakerledger/__main__.py`.

## Task 6: Delivery surface

- [ ] Add healthy and conflicting example projects.
- [ ] Write README, repair guide, security policy, contributing guide, and changelog.
- [ ] Add one-command check and packaging metadata.

## Task 7: Automation and release

- [ ] Add Windows/Linux CI and tagged release automation.
- [ ] Build and install wheel/sdist in a clean environment.
- [ ] Complete five-axis review, secret scan, author/contributor audit.
- [ ] Publish public repository and v0.1.0 Release; verify online artifacts.
- [ ] Send Gmail completion message only after public verification.


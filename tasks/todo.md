# BreakerLedger 0.1 task ledger

## Task 1: Product contract

- [x] Record bounded prior-art scan and local-project exclusion.
- [x] Define public CSV, CLI, status, report, and exit-code contracts.
- [x] Define threat model, non-goals, and measurable release criteria.

Verification: docs agree on the same input files, statuses, outputs, and limits.

## Task 2: Evidence compiler

- [x] Write failing status and retest tests.
- [x] Implement the minimal validated domain model and compiler.
- [x] Verify conflict, confirmed, tentative, and unmapped paths.

Files: `tests/test_audit.py`, `src/breakerledger/model.py`,
`src/breakerledger/audit.py`.

## Task 3: CSV boundary

- [x] Write failing schema/reference/limit tests.
- [x] Implement strict UTF-8 CSV loading and project validation.
- [x] Verify malformed input fails before compilation.

Files: `tests/test_io.py`, `src/breakerledger/io.py`.

## Task 4: Reports

- [x] Write failing deterministic and encoding tests.
- [x] Implement CSV, JSON, HTML, and retest outputs from one audit model.
- [x] Verify only the five named artifacts are written.

Files: `tests/test_reports.py`, `src/breakerledger/reports.py`.

## Task 5: CLI

- [x] Write failing clean/conflict/invalid subprocess tests.
- [x] Implement `validate` and `audit` with documented exit codes.
- [x] Verify installed and source-tree entry points behave alike.

Files: `tests/test_cli.py`, `src/breakerledger/cli.py`,
`src/breakerledger/__main__.py`.

## Task 6: Delivery surface

- [x] Add healthy and conflicting example projects.
- [x] Write README, repair guide, security policy, contributing guide, and changelog.
- [x] Add one-command check and packaging metadata.

## Task 7: Automation and release

- [x] Add Windows/Linux CI and tagged release automation.
- [x] Build and install wheel/sdist in a clean environment.
- [x] Complete five-axis review and secret scan.
- [ ] Complete author/contributor audit on the release commit.
- [ ] Publish public repository and v0.1.0 Release; verify online artifacts.
- [ ] Send Gmail completion message only after public verification.

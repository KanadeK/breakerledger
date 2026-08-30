# Implementation plan: BreakerLedger 0.1

## Overview

Build one end-to-end evidence compiler in thin slices: validate real CSV input,
compile explicit endpoint statuses, render deterministic artifacts, expose the
behavior through a stable CLI, and close the release with reproducible package
and public CI evidence.

## Architecture decisions

- Standard-library runtime keeps offline installation and supply-chain risk
  small.
- Three normalized CSV files keep user input inspectable and diffable.
- Validated dataclasses are the only authority consumed by the compiler.
- Reports are projections of one audit model; no report implements its own
  mapping rules.

## Task order

1. Freeze research, specification, threat model, and public contracts.
2. Implement domain models and evidence compilation test-first.
3. Implement strict CSV loading and reference validation test-first.
4. Implement deterministic reports and output encoding test-first.
5. Implement CLI exit semantics and end-to-end tests.
6. Add realistic examples and user/repair documentation.
7. Add the local check script, CI, package build, and tagged release workflow.
8. Review correctness/security/simplicity, verify package and clean history.
9. Publish, verify remote CI/release, then send the Gmail notification.

## Checkpoints

- After tasks 2-3: all domain and boundary tests pass.
- After tasks 4-5: both example flows work end to end with exact exit codes.
- After tasks 6-7: one command proves tests, compilation, examples, and package.
- Before publication: clean tree, author hygiene, artifact install check, and
  requirement-by-requirement audit are green.

## Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Evidence semantics imply certainty. | High | Use named states and counts, never probabilities. |
| Generated HTML/CSV interprets labels. | High | Escape HTML and shield formula-leading CSV cells with tests. |
| CSV schema becomes hard to use. | Medium | Commit clean/conflicting projects and actionable validation errors. |
| GitHub authentication remains unavailable. | High | Finish a fully verified local release first, then try scoped CLI and connector paths without weakening identity controls. |

## Open questions

None for the delegated v0.1 scope.


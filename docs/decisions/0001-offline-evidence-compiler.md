# ADR-001: Build an offline evidence compiler

## Status

Accepted

## Date

2026-08-30

## Context

Most sampled alternatives optimize data entry, live monitoring, or label
layout. The distinct problem is reconciling repeated field observations without
hiding contradictions. Users also need an artifact that can be reviewed,
versioned, and handed to another person without a hosted account.

## Decision

Use a standard-library Python CLI with three explicit CSV inputs and
deterministic CSV/JSON/HTML outputs. Model `conflict`, `confirmed`, `tentative`,
and `unmapped` as mutually exclusive endpoint states. Preserve evidence IDs and
counts; do not calculate a confidence percentage.

## Alternatives considered

### Browser-first panel editor

Rejected for v0.1 because it competes on layout and data entry, makes automated
failure gates secondary, and adds a large dependency surface before the
evidence model is proven.

### SQLite-backed household database

Rejected because it duplicates broad home-inventory tools and makes review or
Git-based comparison less transparent than CSV fixtures.

### Hardware or Home Assistant integration

Rejected because it narrows the audience to one sensor ecosystem and moves the
project toward live electrical control and credential handling.

### Probabilistic confidence score

Rejected because a few manual observations do not justify a calibrated
probability. Visible counts and explicit contradictions are more honest.

## Consequences

- The project runs offline and has no runtime dependencies.
- CSV is less convenient than a mobile form, but examples and exact validation
  make it inspectable and portable.
- The status contract is intentionally small and can be extended only through a
  documented versioned change.


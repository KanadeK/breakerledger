# BreakerLedger

Turn breaker test notes into an evidence-backed panel directory — without
hiding contradictions.

BreakerLedger is an offline, dependency-free Python CLI for people who already
have observations such as “the north-wall outlet lost power while B01 was off.”
It compiles those observations into a printable directory, per-endpoint mapping,
machine-readable evidence, and a targeted retest queue.

It is not an electrical design or safety tool. It does not explain how to open
a panel, work on energized equipment, size wiring, calculate loads, or establish
code compliance. Collect observations only with a safe method appropriate to
your situation and use a qualified electrician when needed.

## Why this exists

Panel-label apps usually start after someone has decided the mapping. Smart
panel tools usually assume a particular sensor or Home Assistant stack.
BreakerLedger focuses on the uncomfortable middle:

- the same endpoint was recorded against two breakers;
- one breaker/endpoint pair has both “lost power” and “retained power” notes;
- a mapping has only one supporting observation;
- an endpoint has not been mapped at all.

Those states remain visible. A breaker label never overrides the evidence.
See the bounded [prior-art scan](docs/RESEARCH.md) and the exact
[evidence contract](docs/SPEC.md).

## Quick start

BreakerLedger requires Python 3.11 or newer and has no runtime dependencies.

```shell
git clone https://github.com/KanadeK/breakerledger.git
cd breakerledger
python -m pip install .
breakerledger validate examples/healthy-house
breakerledger audit examples/healthy-house --output demo-output
```

Expected result:

```text
Valid project: 4 breakers, 5 endpoints, 14 observations
Wrote 5 reports to demo-output
Audit clean for --fail-on unresolved: confirmed=5 tentative=0 unmapped=0 conflict=0
```

Open `demo-output/report.html` or inspect the CSV/JSON files. The conflicting
example intentionally exits `2` after still writing its evidence:

```shell
breakerledger audit examples/conflicting-house --output conflict-output
```

## Input files

A project is a directory containing exactly three UTF-8 CSV inputs.

`breakers.csv`:

```csv
panel_id,breaker_id,position,rating_amps,label
main,B01,1,15,Living room
```

`endpoints.csv`:

```csv
endpoint_id,location,kind,label
E-LR-NORTH,Living room,receptacle,North wall duplex
```

`observations.csv`:

```csv
observation_id,observed_at,breaker_id,endpoint_id,result,observer,note
O001,2026-08-30T10:00:00Z,B01,E-LR-NORTH,lost_power,Alex,first pass
```

An observation describes what happened at one endpoint while the named breaker
was known to be off:

| Result | Meaning |
| --- | --- |
| `lost_power` | The endpoint lost power. This supports the mapping. |
| `retained_power` | The endpoint retained power. This rules against the mapping unless contradicted later. |
| `not_tested` | The attempt did not establish either state. It remains in source data but adds no mapping evidence. |

IDs are case-sensitive. Headers are exact so a typo cannot silently discard a
column. See [SPEC.md](docs/SPEC.md) for optional cells and size limits.

## Status model

| Status | Rule |
| --- | --- |
| `confirmed` | Exactly one breaker has at least two `lost_power` observations by default, with no conflict. |
| `tentative` | Exactly one breaker has fewer supporting observations than the configured threshold. |
| `unmapped` | No breaker has `lost_power` evidence. |
| `conflict` | A pair has opposite results, or multiple breakers have `lost_power` evidence for one endpoint. |

Change the support threshold with `--confirmations N`. BreakerLedger reports
counts and observation IDs; it deliberately does not invent a confidence
percentage.

## Commands and exit codes

```text
breakerledger validate PROJECT_DIR
breakerledger audit PROJECT_DIR --output OUTPUT_DIR
    [--confirmations N]
    [--fail-on unresolved|conflict|never]
```

| Exit | Meaning |
| --- | --- |
| `0` | Valid, and the configured finding threshold did not fail. |
| `1` | Invalid project or output operation. |
| `2` | Reports were written, but findings met `--fail-on`; argparse also uses `2` for invalid CLI syntax. |

The default `--fail-on unresolved` makes conflict, tentative, or unmapped
endpoints fail a gate. `--fail-on conflict` permits incomplete work while still
blocking contradictions. `--fail-on never` is for report-only workflows.

## Output contract

BreakerLedger creates or replaces only five fixed files inside the output
directory and does not delete unrelated files:

| File | Purpose |
| --- | --- |
| `mapping.csv` | One evidence status per endpoint. |
| `directory.csv` | Panel/position rows with supported endpoint mappings. |
| `retest.csv` | Exact conflict repeats, tentative repeats, and unmapped candidates. |
| `summary.json` | Stable schema with counts, reasons, and source observation IDs. |
| `report.html` | Self-contained, print-friendly report with no JavaScript. |

Output is deterministically sorted. Existing report symlinks are rejected.
HTML values are escaped. User-controlled CSV cells beginning with spreadsheet
formula characters are prefixed with an apostrophe.

## Development and acceptance

The repository locks all development/build tools. Install
[uv](https://docs.astral.sh/uv/) 0.11.20 or newer, then run:

```shell
uv sync --frozen
uv run python scripts/check.py
uv build
uv run python scripts/verify_package.py
```

`scripts/check.py` runs formatting, lint, strict type checking, 25+ unit and CLI
tests, source compilation, both examples, deterministic report comparison,
runtime-import policy, documentation checks, and a secret-pattern scan.
`verify_package.py` checks the wheel/sdist created by `uv build`, installs the
wheel in a fresh temporary virtual environment, and runs both example flows
through the installed `breakerledger` command.

If a command fails, use the symptom-to-repair table in
[docs/REPAIR.md](docs/REPAIR.md). CI runs the same gate on Windows and Linux.

## Security and privacy

BreakerLedger has no runtime network, subprocess, dynamic-import, server, or
database feature. Inputs remain local. Reports can still reveal room and device
names, so review them before sharing. See [SECURITY.md](SECURITY.md) and the
[threat model](docs/THREAT_MODEL.md).

## Contributing

Issues and focused pull requests are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md)
and keep changes inside the evidence contract unless a spec change is proposed
first.

## License

MIT

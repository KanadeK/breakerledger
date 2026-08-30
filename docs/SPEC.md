# Spec: BreakerLedger 0.1

## Objective

BreakerLedger compiles safe, already-collected circuit test observations into
an auditable breaker directory. It is for homeowners, facilities staff, and
electricians who have a notebook or spreadsheet of outlet/light tests but need
to see weak evidence, contradictions, and the next useful retest.

The tool does not tell users how to perform electrical work. It never controls
hardware, executes input, or makes code-compliance claims.

## Tech stack

- Python 3.11+
- Standard-library runtime only
- `unittest` for behavioral and integration tests
- Hatchling as the build backend only
- GitHub Actions for Windows and Linux CI

## Public interface

```text
breakerledger validate PROJECT_DIR
breakerledger audit PROJECT_DIR --output OUTPUT_DIR
    [--confirmations N]
    [--fail-on unresolved|conflict|never]
```

The source-tree equivalent is `python -m breakerledger ...` with `PYTHONPATH`
set to `src`.

Exit codes:

- `0`: command completed and the configured finding threshold did not fail.
- `1`: the project input or output operation is invalid.
- `2`: audit artifacts were written, but findings met `--fail-on`.
- `2`: argparse also uses this code for invalid CLI syntax before the command runs.

`validate` checks input structure and references but does not infer mappings.
`audit` validates, compiles, and writes exactly these files:

- `mapping.csv`
- `directory.csv`
- `retest.csv`
- `summary.json`
- `report.html`

## Input contract

Every project directory contains UTF-8 CSV files with headers exactly matching
the fields below. Extra columns fail fast so misspelled fields cannot silently
disappear. Breaker `rating_amps` and `label`, endpoint `label`, and observation
`observer` and `note` may be blank; every other field is required.

`breakers.csv`:

```csv
panel_id,breaker_id,position,rating_amps,label
```

`endpoints.csv`:

```csv
endpoint_id,location,kind,label
```

`observations.csv`:

```csv
observation_id,observed_at,breaker_id,endpoint_id,result,observer,note
```

`result` is one of:

- `lost_power`: the endpoint lost power while the named breaker was off.
- `retained_power`: the endpoint retained power while the named breaker was off.
- `not_tested`: the attempted observation did not establish either state.

IDs are case-sensitive and globally unique within their file. Observations must
reference declared breakers and endpoints. Each input file is capped at 5 MiB
and 50,000 data rows. The breaker count multiplied by the endpoint count may
not exceed 1,000,000 so an unmapped retest matrix remains bounded.

## Evidence semantics

For each endpoint:

- `conflict`: the same breaker/endpoint pair has both `lost_power` and
  `retained_power`, or more than one breaker has `lost_power` evidence.
- `confirmed`: exactly one breaker has `lost_power`, its support count meets
  `--confirmations` (default 2), and no conflict exists.
- `tentative`: exactly one breaker has support below the confirmation threshold
  and no conflict exists.
- `unmapped`: no breaker has `lost_power` evidence.

Counts and observation IDs are retained in JSON. Breaker directory rows derive
only from these endpoint results. No fallback label becomes authoritative.

Retest actions are deterministic:

- conflict: retest every breaker implicated by positive or pair-contradictory
  evidence for that endpoint;
- tentative: repeat the tentative breaker/endpoint test;
- unmapped: map the endpoint against breakers not yet ruled out by
  `retained_power`, reported as one semicolon-separated candidate list.

## Project structure

```text
src/breakerledger/     application modules
tests/                 unit and CLI integration tests
examples/              clean and conflicting real-shaped fixtures
docs/                  research, threat model, and decisions
tasks/                 implementation plan and completion ledger
scripts/check.py       one-command local release gate
.github/workflows/     CI and tagged release automation
```

## Code style

Use typed dataclasses for validated domain values and plain functions for
compilation. Validate once at the CSV boundary and trust domain objects after
that.

```python
def compile_project(project: Project, confirmations: int) -> Audit:
    """Return deterministic evidence results for one validated project."""
```

Names describe domain concepts. No generic repositories, factories, service
containers, fallback layers, or compatibility shims are in scope.

## Testing strategy

- Unit tests prove each evidence status and retest action.
- Boundary tests prove malformed headers, duplicate IDs, unknown references,
  invalid results, row/size limits, and UTF-8 errors fail clearly.
- Report tests prove stable ordering, deterministic bytes, HTML escaping, and
  spreadsheet-formula shielding.
- CLI tests execute clean, conflict, and invalid projects and assert exit codes
  plus generated artifacts.
- Package verification builds wheel/sdist, installs the wheel in a clean venv,
  and runs the installed CLI against both examples.

## Boundaries

- Always: preserve source evidence; escape output; use deterministic sorting;
  cap external inputs; write only known artifact names.
- Delegated by this task: project dependencies, CI, repository creation, and
  public v0.1.0 release needed to meet this spec.
- Never: execute CSV content; contact a network at runtime; claim electrical
  safety or compliance; hide conflicts; commit credentials; weaken failing tests.

## Success criteria

1. A clean example produces five deterministic artifacts and exit `0`.
2. A conflicting example produces the artifacts, names the exact conflicting
   evidence, emits a concrete retest queue, and exits `2` by default.
3. Invalid input exits `1` without a traceback and without partial artifacts.
4. HTML and CSV output cannot interpret untrusted labels as markup or formulas.
5. `python scripts/check.py` passes on Windows and CI passes on Windows/Linux.
6. Wheel and source archive build; a clean venv can run the installed CLI.
7. README contains exact acceptance commands and a symptom-to-repair table.
8. Git history contains only the configured `KanadeK` author, no co-author
   trailers, and the public v0.1.0 tag/release matches the verified commit.

## Open questions

None for v0.1. The user explicitly delegated product direction and routine
release decisions for this project.

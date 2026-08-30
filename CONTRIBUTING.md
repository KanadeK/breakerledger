# Contributing

## Setup

Use Python 3.11+ and uv 0.11.20+:

```shell
uv sync --frozen
uv run python scripts/check.py
```

## Change discipline

1. Update `docs/SPEC.md` first if a public command, CSV field, evidence rule,
   status, output schema, or exit code changes.
2. Write a failing behavior test before implementation.
3. Keep the runtime standard-library only.
4. Validate external input once in `io.py`; internal domain code trusts the
   resulting dataclasses.
5. Render every report from the one `Audit` model. Do not add a second mapping
   authority inside a reporter.
6. Do not add electrical-work instructions or compliance conclusions.
7. Run the full check and package verifier before opening a pull request.

Keep commits focused and use `feat:`, `fix:`, `test:`, `docs:`, or `chore:`
messages. Do not include generated `dist/`, report output, virtual environments,
credentials, or co-author trailers without the other author's actual contribution
and consent.


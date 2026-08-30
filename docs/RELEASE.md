# Release checklist

## Local gate

- [x] `uv sync --frozen`
- [x] `uv run python scripts/check.py`
- [x] `uv build`
- [x] `uv run python scripts/verify_package.py`
- [x] Clean worktree; staged diff contains no secrets.
- [x] `git shortlog -sne HEAD` lists only intended contributors.
- [x] No `Co-authored-by` trailers unless factually required.
- [x] Version in `src/breakerledger/__init__.py` matches the planned tag.

## Public gate

- [x] Public repository default branch points to the verified commit.
- [x] CI is green for that exact commit on Windows and Linux.
- [x] Annotated `v0.1.0` tag points to that commit.
- [x] GitHub Release contains the wheel and source archive built from the tag.
- [x] Release files install and run the healthy/conflicting examples.
- [x] Public contributors list contains only intended contributors.

Gmail is deliberately the final out-of-repository action. Its delivery is
reported in the task handoff rather than recorded through a post-release commit.

## Rollback

Do not move a public tag. If the released artifact is wrong, mark the Release as
pre-release or withdraw it, fix the problem on `main`, and publish a new patch
version with a new immutable tag.

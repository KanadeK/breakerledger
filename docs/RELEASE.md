# Release checklist

## Local gate

- [x] `uv sync --frozen`
- [x] `uv run python scripts/check.py`
- [x] `uv build`
- [x] `uv run python scripts/verify_package.py`
- [ ] Clean worktree; staged diff contains no secrets.
- [ ] `git shortlog -sne HEAD` lists only intended contributors.
- [ ] No `Co-authored-by` trailers unless factually required.
- [x] Version in `src/breakerledger/__init__.py` matches the planned tag.

## Public gate

- [ ] Public repository default branch points to the verified commit.
- [ ] CI is green for that exact commit on Windows and Linux.
- [ ] Annotated `v0.1.0` tag points to that commit.
- [ ] GitHub Release contains the wheel and source archive built from the tag.
- [ ] Release files install and run the healthy/conflicting examples.
- [ ] Public contributors list contains only intended contributors.
- [ ] Gmail notification is sent only after the public links are verified.

## Rollback

Do not move a public tag. If the released artifact is wrong, mark the Release as
pre-release or withdraw it, fix the problem on `main`, and publish a new patch
version with a new immutable tag.

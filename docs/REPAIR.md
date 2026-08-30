# Failure and repair guide

| Symptom | Meaning | Repair |
| --- | --- | --- |
| `breakers.csv is required` (or another filename) | The project is incomplete or the wrong directory was passed. | Point to the directory containing all three CSV files; do not rename them. |
| `headers must be exactly` | A header is missing, reordered, or misspelled. | Copy the header shown in the error or from `examples/healthy-house`; keep optional columns present even when their cells are blank. |
| `row N: ... is required` | A required cell is blank or the CSV row is short. | Fill the named value. Labels, ratings, observer, and note are the only documented blankable cells. |
| `duplicate ..._id` | Two records share an authority ID. | Give each breaker, endpoint, or observation a stable unique ID; do not delete evidence merely to silence the error. |
| `unknown breaker_id` / `unknown endpoint_id` | An observation points outside the declared inventory. | Correct the typo or add the missing inventory row, then validate again. |
| `result must be ...` | The result is not one of the three explicit evidence states. | Use `lost_power`, `retained_power`, or `not_tested`; do not translate uncertainty into a positive result. |
| Exit `2` with `conflict` | Reports were written, but evidence directly disagrees. | Open `retest.csv`, repeat every named breaker/endpoint pair safely, append new observations, and rerun. Do not relabel the breaker to hide the conflict. |
| Exit `2` with `tentative` | A candidate mapping has fewer supporting observations than required. | Repeat the named pair or lower `--confirmations` only if your documented process intentionally uses a smaller threshold. |
| Exit `2` with `unmapped` | No positive mapping exists. | Use the candidate list in `retest.csv`; breakers already ruled out by `retained_power` are omitted. |
| `could not write reports` | The output directory is unavailable or not writable. | Choose a writable directory and ensure the target is a directory, not a file. Existing unrelated files are preserved. |
| `uv sync --frozen` says the lock is stale | `pyproject.toml` changed without an intentional dependency-lock update. | Review the dependency change, run `uv lock`, inspect `uv.lock`, then run the frozen sync again. |
| Build backend cannot be downloaded | The build machine has no PyPI access and lacks the locked build tools. | Restore package-index access or populate the uv cache from a trusted environment; do not remove the pinned backend or disable isolation. |
| Local checks pass but CI fails | OS or Python-version behavior differs. | Read the failing job, reproduce its exact command/version, fix the cause, and push a new commit. Do not skip the job or test. |

For unexpected behavior, rerun the smallest failing command first. A valid
project can always be checked without writing reports:

```shell
breakerledger validate PATH_TO_PROJECT
```


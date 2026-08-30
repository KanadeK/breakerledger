# Threat model

## Trust boundaries and assets

The three CSV files and output path are untrusted local inputs. BreakerLedger's
assets are the integrity of its findings, the user's existing files, and the
ability to open reports without executing injected content.

There is no authentication, server, database, network client, plugin loader, or
shell-command feature.

## Abuse cases and controls

| Abuse case | Control |
| --- | --- |
| Huge CSV consumes memory or makes CI hang. | Reject each file over 5 MiB, more than 50,000 data rows, or a breaker x endpoint matrix over 1,000,000 cells. |
| Crafted labels inject markup into `report.html`. | Escape every external string and use no JavaScript. |
| Crafted labels become spreadsheet formulas. | Prefix formula-leading external cells in generated CSV. |
| Duplicate IDs or typoed headers silently overwrite evidence. | Exact headers and uniqueness checks fail before compilation. |
| Observation points at a nonexistent breaker or endpoint. | Referential validation fails before compilation. |
| A conflict is hidden behind a fallback mapping. | Conflict is a first-class status; no fallback or label authority exists. |
| Output generation deletes unrelated files. | Create/overwrite only five fixed artifact filenames; never clean the directory recursively. |
| CSV text is treated as a command or path. | No subprocess, `eval`, dynamic import, URL fetch, or input-derived filename exists. |

## Residual risk

BreakerLedger can only reason about the observations supplied. Repeated wrong
observations can produce a wrong “confirmed” result. The report therefore shows
evidence counts and source observation IDs and never claims electrical safety.

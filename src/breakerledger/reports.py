from __future__ import annotations

import csv
import json
from html import escape
from io import StringIO
from pathlib import Path
from typing import Iterable, Sequence

from .model import Audit, Breaker, EndpointResult, Project

REPORT_FILENAMES = (
    "mapping.csv",
    "directory.csv",
    "retest.csv",
    "summary.json",
    "report.html",
)


class ReportError(OSError):
    """Raised when deterministic audit artifacts cannot be written."""


def write_reports(
    project: Project,
    audit: Audit,
    output_dir: str | Path,
    confirmations: int,
) -> tuple[Path, ...]:
    """Write the five documented reports without removing unrelated files."""
    output = Path(output_dir)
    contents = {
        "mapping.csv": _mapping_csv(project, audit),
        "directory.csv": _directory_csv(project, audit),
        "retest.csv": _retest_csv(audit),
        "summary.json": _summary_json(audit, confirmations),
        "report.html": _report_html(project, audit, confirmations),
    }
    try:
        output.mkdir(parents=True, exist_ok=True)
        if not output.is_dir():
            raise ReportError(f"output path is not a directory: {output}")
        paths: list[Path] = []
        for filename in REPORT_FILENAMES:
            path = output / filename
            path.write_text(contents[filename], encoding="utf-8", newline="")
            paths.append(path)
    except OSError as error:
        if isinstance(error, ReportError):
            raise
        raise ReportError(f"could not write reports to {output}: {error}") from error
    return tuple(paths)


def _mapping_csv(project: Project, audit: Audit) -> str:
    breakers = {item.breaker_id: item for item in project.breakers}
    rows: list[tuple[object, ...]] = []
    for result in audit.endpoints:
        rows.append(
            (
                result.endpoint.endpoint_id,
                result.endpoint.location,
                result.endpoint.kind,
                result.endpoint.label,
                result.status,
                ";".join(result.breaker_ids),
                ";".join(breakers[item].position for item in result.breaker_ids),
                len(result.positive_observation_ids),
                len(result.negative_observation_ids),
                ";".join(result.positive_observation_ids),
                ";".join(result.negative_observation_ids),
                result.reason,
            )
        )
    return _csv_text(
        (
            "endpoint_id",
            "location",
            "kind",
            "label",
            "status",
            "breaker_ids",
            "breaker_positions",
            "positive_count",
            "negative_count",
            "positive_observation_ids",
            "negative_observation_ids",
            "reason",
        ),
        rows,
    )


def _directory_csv(project: Project, audit: Audit) -> str:
    rows: list[tuple[object, ...]] = []
    for breaker in sorted(project.breakers, key=_breaker_key):
        mapped = [
            result for result in audit.endpoints if breaker.breaker_id in result.breaker_ids
        ]
        rows.append(
            (
                breaker.panel_id,
                breaker.position,
                breaker.breaker_id,
                breaker.rating_amps,
                breaker.label,
                _directory_status(mapped),
                len(mapped),
                ";".join(item.endpoint.endpoint_id for item in mapped),
                "; ".join(_endpoint_directory_label(item) for item in mapped),
            )
        )
    return _csv_text(
        (
            "panel_id",
            "position",
            "breaker_id",
            "rating_amps",
            "label",
            "status",
            "endpoint_count",
            "endpoint_ids",
            "endpoints",
        ),
        rows,
    )


def _retest_csv(audit: Audit) -> str:
    rows = [
        (
            item.endpoint_id,
            item.current_status,
            item.breaker_id,
            item.action,
            ";".join(item.candidate_breaker_ids),
            item.reason,
        )
        for item in audit.retests
    ]
    return _csv_text(
        (
            "endpoint_id",
            "current_status",
            "breaker_id",
            "action",
            "candidate_breaker_ids",
            "reason",
        ),
        rows,
    )


def _summary_json(audit: Audit, confirmations: int) -> str:
    value = {
        "schema_version": 1,
        "confirmations_required": confirmations,
        "status_counts": audit.status_counts,
        "endpoints": [
            {
                "endpoint_id": item.endpoint.endpoint_id,
                "location": item.endpoint.location,
                "kind": item.endpoint.kind,
                "label": item.endpoint.label,
                "status": item.status,
                "breaker_ids": list(item.breaker_ids),
                "positive_observation_ids": list(item.positive_observation_ids),
                "negative_observation_ids": list(item.negative_observation_ids),
                "reason": item.reason,
            }
            for item in audit.endpoints
        ],
        "retests": [
            {
                "endpoint_id": item.endpoint_id,
                "current_status": item.current_status,
                "breaker_id": item.breaker_id,
                "action": item.action,
                "candidate_breaker_ids": list(item.candidate_breaker_ids),
                "reason": item.reason,
            }
            for item in audit.retests
        ],
    }
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _report_html(project: Project, audit: Audit, confirmations: int) -> str:
    mapping_rows = [
        (
            item.endpoint.endpoint_id,
            item.endpoint.location,
            item.endpoint.kind,
            item.endpoint.label,
            item.status,
            ", ".join(item.breaker_ids) or "-",
            str(len(item.positive_observation_ids)),
            item.reason,
        )
        for item in audit.endpoints
    ]
    directory_rows = []
    for breaker in sorted(project.breakers, key=_breaker_key):
        mapped = [item for item in audit.endpoints if breaker.breaker_id in item.breaker_ids]
        directory_rows.append(
            (
                breaker.panel_id,
                breaker.position,
                breaker.breaker_id,
                breaker.rating_amps or "-",
                breaker.label or "-",
                _directory_status(mapped),
                ", ".join(_endpoint_directory_label(item) for item in mapped) or "-",
            )
        )
    retest_rows = [
        (
            item.endpoint_id,
            item.current_status,
            item.breaker_id or "-",
            item.action,
            ", ".join(item.candidate_breaker_ids) or "-",
            item.reason,
        )
        for item in audit.retests
    ]
    counts = "".join(
        f'<div class="metric"><strong>{audit.status_counts[status]}</strong>{escape(status)}</div>'
        for status in ("confirmed", "tentative", "unmapped", "conflict")
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BreakerLedger audit</title>
<style>
:root {{ color-scheme: light; font-family: ui-sans-serif, system-ui, sans-serif; }}
body {{ margin: 0 auto; max-width: 1200px; padding: 2rem; color: #172033; }}
h1, h2 {{ color: #0b3a53; }}
.notice {{ border-left: 5px solid #d97706; background: #fff7ed; padding: 1rem; }}
.metrics {{ display: flex; flex-wrap: wrap; gap: .75rem; margin: 1.5rem 0; }}
.metric {{ min-width: 7rem; border: 1px solid #cbd5e1; border-radius: .5rem; padding: .75rem; }}
.metric strong {{ display: block; font-size: 1.6rem; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 2rem; }}
th, td {{ border: 1px solid #cbd5e1; padding: .5rem; text-align: left; vertical-align: top; }}
th {{ background: #e8f1f5; }}
@media print {{ body {{ max-width: none; padding: .5rem; }} table {{ break-inside: auto; }} tr {{ break-inside: avoid; }} }}
</style>
</head>
<body>
<h1>BreakerLedger audit</h1>
<p class="notice"><strong>Documentation only.</strong> This report reflects supplied observations. It is not electrical-safety, code-compliance, or wiring advice.</p>
<p>Confirmation threshold: {confirmations} supporting lost-power observations.</p>
<div class="metrics">{counts}</div>
<h2>Endpoint mapping</h2>
{_html_table(("Endpoint", "Location", "Kind", "Label", "Status", "Breaker", "Support", "Reason"), mapping_rows)}
<h2>Panel directory</h2>
{_html_table(("Panel", "Position", "Breaker", "Amps", "Label", "Status", "Endpoints"), directory_rows)}
<h2>Retest queue</h2>
{_html_table(("Endpoint", "Status", "Breaker", "Action", "Candidates", "Reason"), retest_rows)}
</body>
</html>
"""


def _csv_text(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(headers)
    for row in rows:
        writer.writerow(_csv_safe(value) for value in row)
    return output.getvalue()


def _csv_safe(value: object) -> object:
    if not isinstance(value, str) or not value:
        return value
    if value[0] in "=+-@":
        return "'" + value
    return value


def _html_table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    head = "".join(f"<th>{escape(item)}</th>" for item in headers)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{escape(str(value))}</td>" for value in row)
        body_rows.append(f"<tr>{cells}</tr>")
    body = "".join(body_rows) or f'<tr><td colspan="{len(headers)}">None</td></tr>'
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _breaker_key(breaker: Breaker) -> tuple[str, str, str]:
    return breaker.panel_id, breaker.position.zfill(8), breaker.breaker_id


def _directory_status(results: list[EndpointResult]) -> str:
    statuses = {item.status for item in results}
    for status in ("conflict", "tentative", "confirmed"):
        if status in statuses:
            return status
    return "empty"


def _endpoint_directory_label(result: EndpointResult) -> str:
    label = result.endpoint.label or result.endpoint.location
    return f"{result.endpoint.endpoint_id}: {label}"

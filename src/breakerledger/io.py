from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from typing import cast

from .model import Breaker, Endpoint, Observation, ObservationResult, Project

MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_DATA_ROWS = 50_000
MAX_MAPPING_CELLS = 1_000_000

BREAKERS_HEADER = ("panel_id", "breaker_id", "position", "rating_amps", "label")
ENDPOINTS_HEADER = ("endpoint_id", "location", "kind", "label")
OBSERVATIONS_HEADER = (
    "observation_id",
    "observed_at",
    "breaker_id",
    "endpoint_id",
    "result",
    "observer",
    "note",
)
VALID_RESULTS = ("lost_power", "retained_power", "not_tested")


class InputError(ValueError):
    """Raised when a project cannot be validated at the file boundary."""


def load_project(project_dir: str | Path) -> Project:
    """Load and validate a BreakerLedger project directory."""
    root = Path(project_dir)
    if not root.is_dir():
        raise InputError(f"project directory not found: {root}")

    breaker_rows = _read_csv(root / "breakers.csv", BREAKERS_HEADER)
    endpoint_rows = _read_csv(root / "endpoints.csv", ENDPOINTS_HEADER)
    observation_rows = _read_csv(root / "observations.csv", OBSERVATIONS_HEADER)

    breakers = _load_breakers(breaker_rows)
    endpoints = _load_endpoints(endpoint_rows)
    if len(breakers) * len(endpoints) > MAX_MAPPING_CELLS:
        raise InputError(f"breaker x endpoint matrix exceeds {MAX_MAPPING_CELLS} cells")
    observations = _load_observations(
        observation_rows,
        {item.breaker_id for item in breakers},
        {item.endpoint_id for item in endpoints},
    )
    return Project(
        breakers=tuple(sorted(breakers, key=lambda item: item.breaker_id)),
        endpoints=tuple(sorted(endpoints, key=lambda item: item.endpoint_id)),
        observations=tuple(sorted(observations, key=lambda item: item.observation_id)),
    )


def _read_csv(
    path: Path, expected_header: tuple[str, ...]
) -> list[tuple[int, dict[str, str]]]:
    if not path.is_file():
        raise InputError(f"{path.name} is required")
    size = path.stat().st_size
    if size > MAX_FILE_BYTES:
        raise InputError(f"{path.name} exceeds {MAX_FILE_BYTES} bytes")
    try:
        text = path.read_bytes().decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise InputError(f"{path.name} must be UTF-8") from error

    reader = csv.DictReader(StringIO(text, newline=""))
    actual_header = tuple(reader.fieldnames or ())
    if actual_header != expected_header:
        raise InputError(
            f"{path.name} headers must be exactly: {','.join(expected_header)}"
        )

    rows: list[tuple[int, dict[str, str]]] = []
    for row_number, raw_row in enumerate(reader, start=2):
        if len(rows) >= MAX_DATA_ROWS:
            raise InputError(f"{path.name} exceeds {MAX_DATA_ROWS} data rows")
        if None in raw_row:
            raise InputError(f"{path.name} row {row_number}: unexpected extra values")
        missing = next((key for key, value in raw_row.items() if value is None), None)
        if missing is not None:
            raise InputError(f"{path.name} row {row_number}: {missing} is missing")
        rows.append(
            (
                row_number,
                {key: cast(str, value).strip() for key, value in raw_row.items()},
            )
        )
    return rows


def _load_breakers(rows: list[tuple[int, dict[str, str]]]) -> list[Breaker]:
    required = ("panel_id", "breaker_id", "position")
    seen: set[str] = set()
    breakers: list[Breaker] = []
    for row_number, row in rows:
        _require("breakers.csv", row_number, row, required)
        breaker_id = row["breaker_id"]
        if breaker_id in seen:
            raise InputError(
                f"breakers.csv row {row_number}: duplicate breaker_id {breaker_id}"
            )
        seen.add(breaker_id)
        breakers.append(
            Breaker(
                panel_id=row["panel_id"],
                breaker_id=breaker_id,
                position=row["position"],
                rating_amps=row["rating_amps"],
                label=row["label"],
            )
        )
    return breakers


def _load_endpoints(rows: list[tuple[int, dict[str, str]]]) -> list[Endpoint]:
    required = ("endpoint_id", "location", "kind")
    seen: set[str] = set()
    endpoints: list[Endpoint] = []
    for row_number, row in rows:
        _require("endpoints.csv", row_number, row, required)
        endpoint_id = row["endpoint_id"]
        if endpoint_id in seen:
            raise InputError(
                f"endpoints.csv row {row_number}: duplicate endpoint_id {endpoint_id}"
            )
        seen.add(endpoint_id)
        endpoints.append(
            Endpoint(
                endpoint_id=endpoint_id,
                location=row["location"],
                kind=row["kind"],
                label=row["label"],
            )
        )
    return endpoints


def _load_observations(
    rows: list[tuple[int, dict[str, str]]],
    breaker_ids: set[str],
    endpoint_ids: set[str],
) -> list[Observation]:
    required = (
        "observation_id",
        "observed_at",
        "breaker_id",
        "endpoint_id",
        "result",
    )
    seen: set[str] = set()
    observations: list[Observation] = []
    for row_number, row in rows:
        _require("observations.csv", row_number, row, required)
        observation_id = row["observation_id"]
        if observation_id in seen:
            raise InputError(
                "observations.csv row "
                f"{row_number}: duplicate observation_id {observation_id}"
            )
        seen.add(observation_id)
        if row["breaker_id"] not in breaker_ids:
            raise InputError(
                "observations.csv row "
                f"{row_number}: unknown breaker_id {row['breaker_id']}"
            )
        if row["endpoint_id"] not in endpoint_ids:
            raise InputError(
                "observations.csv row "
                f"{row_number}: unknown endpoint_id {row['endpoint_id']}"
            )
        if row["result"] not in VALID_RESULTS:
            raise InputError(
                f"observations.csv row {row_number}: result must be lost_power, "
                "retained_power, or not_tested"
            )
        observations.append(
            Observation(
                observation_id=observation_id,
                observed_at=row["observed_at"],
                breaker_id=row["breaker_id"],
                endpoint_id=row["endpoint_id"],
                result=cast(ObservationResult, row["result"]),
                observer=row["observer"],
                note=row["note"],
            )
        )
    return observations


def _require(
    filename: str,
    row_number: int,
    row: dict[str, str],
    fields: tuple[str, ...],
) -> None:
    for field in fields:
        if not row[field]:
            raise InputError(f"{filename} row {row_number}: {field} is required")

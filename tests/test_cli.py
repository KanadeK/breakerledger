from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"


def write_csv(
    path: Path, header: tuple[str, ...], rows: Sequence[tuple[str, ...]]
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def write_project(root: Path, mode: str) -> None:
    write_csv(
        root / "breakers.csv",
        ("panel_id", "breaker_id", "position", "rating_amps", "label"),
        [
            ("main", "B01", "1", "15", "Living room"),
            ("main", "B02", "2", "20", "Kitchen"),
        ],
    )
    write_csv(
        root / "endpoints.csv",
        ("endpoint_id", "location", "kind", "label"),
        [("E01", "Living room", "receptacle", "North wall")],
    )
    observations: list[tuple[str, ...]] = [
        (
            "O01",
            "2026-08-30T10:00:00Z",
            "B01",
            "E01",
            "lost_power",
            "Alex",
            "",
        )
    ]
    if mode == "healthy":
        observations.append(
            (
                "O02",
                "2026-08-30T10:05:00Z",
                "B01",
                "E01",
                "lost_power",
                "Alex",
                "",
            )
        )
    elif mode == "conflict":
        observations.append(
            (
                "O02",
                "2026-08-30T10:05:00Z",
                "B02",
                "E01",
                "lost_power",
                "Alex",
                "",
            )
        )
    write_csv(
        root / "observations.csv",
        (
            "observation_id",
            "observed_at",
            "breaker_id",
            "endpoint_id",
            "result",
            "observer",
            "note",
        ),
        observations,
    )


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "breakerledger", *arguments],
        cwd=SOURCE_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


class CliTests(unittest.TestCase):
    def test_validate_reports_project_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = Path(temp_dir)
            write_project(project, "healthy")

            result = run_cli("validate", str(project))

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(
            "Valid project: 2 breakers, 1 endpoints, 2 observations", result.stdout
        )

    def test_audit_clean_project_writes_reports_and_exits_zero(self) -> None:
        with (
            tempfile.TemporaryDirectory() as project_dir,
            tempfile.TemporaryDirectory() as output_dir,
        ):
            project = Path(project_dir)
            output = Path(output_dir)
            write_project(project, "healthy")

            result = run_cli("audit", str(project), "--output", str(output))
            summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Audit clean", result.stdout)
        self.assertEqual(1, summary["status_counts"]["confirmed"])

    def test_audit_conflict_writes_reports_and_exits_two(self) -> None:
        with (
            tempfile.TemporaryDirectory() as project_dir,
            tempfile.TemporaryDirectory() as output_dir,
        ):
            project = Path(project_dir)
            output = Path(output_dir)
            write_project(project, "conflict")

            result = run_cli("audit", str(project), "--output", str(output))

            self.assertTrue((output / "report.html").is_file())
            self.assertTrue((output / "retest.csv").is_file())

        self.assertEqual(2, result.returncode)
        self.assertIn("Audit findings", result.stderr)
        self.assertIn("conflict=1", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_fail_on_conflict_allows_tentative_result(self) -> None:
        with (
            tempfile.TemporaryDirectory() as project_dir,
            tempfile.TemporaryDirectory() as output_dir,
        ):
            project = Path(project_dir)
            output = Path(output_dir)
            write_project(project, "tentative")

            result = run_cli(
                "audit",
                str(project),
                "--output",
                str(output),
                "--fail-on",
                "conflict",
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Audit clean for --fail-on conflict", result.stdout)

    def test_invalid_project_exits_one_without_partial_output_or_traceback(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as project_dir:
            project = Path(project_dir)
            output = project / "output"
            write_project(project, "healthy")
            (project / "endpoints.csv").unlink()

            result = run_cli("audit", str(project), "--output", str(output))

            self.assertFalse(output.exists())

        self.assertEqual(1, result.returncode)
        self.assertIn("error: endpoints.csv is required", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()

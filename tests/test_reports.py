from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from breakerledger.audit import compile_project
from breakerledger.model import Breaker, Endpoint, Observation, Project
from breakerledger.reports import REPORT_FILENAMES, ReportError, write_reports


def report_project() -> Project:
    return Project(
        breakers=(
            Breaker("main", "B01", "1", "15", "Living room"),
            Breaker("main", "B02", "2", "20", "Kitchen"),
            Breaker("main", "B03", "3", "", ""),
        ),
        endpoints=(
            Endpoint("E01", "<script>alert(1)</script>", "receptacle", "=2+2"),
            Endpoint("E02", "Kitchen", "light", "Ceiling"),
            Endpoint("E03", "Hall", "receptacle", "Console"),
        ),
        observations=(
            Observation(
                "O01",
                "2026-08-30T10:00:00Z",
                "B01",
                "E01",
                "lost_power",
                "Alex",
                "",
            ),
            Observation(
                "O02",
                "2026-08-30T10:05:00Z",
                "B01",
                "E01",
                "lost_power",
                "Alex",
                "",
            ),
            Observation(
                "O03",
                "2026-08-30T10:10:00Z",
                "B02",
                "E02",
                "lost_power",
                "Alex",
                "",
            ),
            Observation(
                "O04",
                "2026-08-30T10:15:00Z",
                "B01",
                "E03",
                "retained_power",
                "Alex",
                "",
            ),
        ),
    )


class WriteReportsTests(unittest.TestCase):
    def test_writes_exactly_five_reports_and_preserves_unrelated_file(self) -> None:
        project = report_project()
        audit = compile_project(project, confirmations=2)
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            (output / "keep.txt").write_text("keep", encoding="utf-8")

            paths = write_reports(project, audit, output, confirmations=2)

            self.assertEqual(set(REPORT_FILENAMES), {path.name for path in paths})
            self.assertEqual(
                set(REPORT_FILENAMES) | {"keep.txt"},
                {path.name for path in output.iterdir()},
            )
            self.assertEqual("keep", (output / "keep.txt").read_text(encoding="utf-8"))

    def test_outputs_are_byte_deterministic(self) -> None:
        project = report_project()
        audit = compile_project(project, confirmations=2)
        with (
            tempfile.TemporaryDirectory() as first_dir,
            tempfile.TemporaryDirectory() as second_dir,
        ):
            first = Path(first_dir)
            second = Path(second_dir)

            write_reports(project, audit, first, confirmations=2)
            write_reports(project, audit, second, confirmations=2)

            for filename in REPORT_FILENAMES:
                self.assertEqual(
                    (first / filename).read_bytes(),
                    (second / filename).read_bytes(),
                    filename,
                )

    def test_html_escapes_markup_and_csv_shields_formulas(self) -> None:
        project = report_project()
        audit = compile_project(project, confirmations=2)
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            write_reports(project, audit, output, confirmations=2)

            html = (output / "report.html").read_text(encoding="utf-8")
            with (output / "mapping.csv").open(encoding="utf-8", newline="") as handle:
                mapping = list(csv.DictReader(handle))

        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertEqual("'=2+2", mapping[0]["label"])

    def test_refuses_to_follow_a_report_symlink(self) -> None:
        project = report_project()
        audit = compile_project(project, confirmations=2)
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch("pathlib.Path.is_symlink", return_value=True),
            self.assertRaisesRegex(ReportError, "refusing to overwrite symbolic link"),
        ):
            write_reports(project, audit, temp_dir, confirmations=2)

    def test_summary_preserves_evidence_and_retest_actions(self) -> None:
        project = report_project()
        audit = compile_project(project, confirmations=2)
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            write_reports(project, audit, output, confirmations=2)
            summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))

        endpoints = {item["endpoint_id"]: item for item in summary["endpoints"]}
        self.assertEqual(1, summary["schema_version"])
        self.assertEqual(2, summary["confirmations_required"])
        self.assertEqual(["O01", "O02"], endpoints["E01"]["positive_observation_ids"])
        self.assertEqual("tentative", endpoints["E02"]["status"])
        self.assertEqual("unmapped", endpoints["E03"]["status"])
        self.assertEqual(
            ["repeat_support", "map_endpoint"],
            [item["action"] for item in summary["retests"]],
        )


if __name__ == "__main__":
    unittest.main()

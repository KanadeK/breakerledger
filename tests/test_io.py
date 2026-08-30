from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from breakerledger.io import InputError, load_project


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


def write_csv(path: Path, header: tuple[str, ...], rows: list[tuple[str, ...]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def write_valid_project(root: Path) -> None:
    write_csv(
        root / "breakers.csv",
        BREAKERS_HEADER,
        [
            ("main", "B02", "2", "20", "Kitchen"),
            ("main", "B01", "1", "15", ""),
        ],
    )
    write_csv(
        root / "endpoints.csv",
        ENDPOINTS_HEADER,
        [
            ("E02", "Kitchen", "light", "Ceiling"),
            ("E01", "Living room", "receptacle", "North wall"),
        ],
    )
    write_csv(
        root / "observations.csv",
        OBSERVATIONS_HEADER,
        [
            (
                "O02",
                "2026-08-30T10:05:00Z",
                "B02",
                "E02",
                "lost_power",
                "",
                "",
            ),
            (
                "O01",
                "2026-08-30T10:00:00Z",
                "B01",
                "E01",
                "retained_power",
                "Alex",
                "repeat later",
            ),
        ],
    )


class LoadProjectTests(unittest.TestCase):
    def test_loads_and_sorts_a_valid_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_valid_project(root)

            project = load_project(root)

        self.assertEqual(["B01", "B02"], [item.breaker_id for item in project.breakers])
        self.assertEqual(["E01", "E02"], [item.endpoint_id for item in project.endpoints])
        self.assertEqual(
            ["O01", "O02"], [item.observation_id for item in project.observations]
        )

    def test_rejects_missing_input_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_valid_project(root)
            (root / "observations.csv").unlink()

            with self.assertRaisesRegex(InputError, "observations.csv is required"):
                load_project(root)

    def test_rejects_extra_or_misspelled_header(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_valid_project(root)
            write_csv(
                root / "breakers.csv",
                BREAKERS_HEADER + ("labels",),
                [("main", "B01", "1", "15", "", "typo")],
            )

            with self.assertRaisesRegex(
                InputError, "breakers.csv headers must be exactly"
            ):
                load_project(root)

    def test_rejects_blank_required_value(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_valid_project(root)
            write_csv(
                root / "breakers.csv",
                BREAKERS_HEADER,
                [("main", "", "1", "15", "Unlabeled")],
            )

            with self.assertRaisesRegex(
                InputError, "breakers.csv row 2: breaker_id is required"
            ):
                load_project(root)

    def test_rejects_duplicate_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_valid_project(root)
            write_csv(
                root / "endpoints.csv",
                ENDPOINTS_HEADER,
                [
                    ("E01", "Living room", "light", "Ceiling"),
                    ("E01", "Living room", "receptacle", "North wall"),
                ],
            )

            with self.assertRaisesRegex(InputError, "duplicate endpoint_id E01"):
                load_project(root)

    def test_rejects_unknown_observation_references(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_valid_project(root)
            write_csv(
                root / "observations.csv",
                OBSERVATIONS_HEADER,
                [
                    (
                        "O01",
                        "2026-08-30T10:00:00Z",
                        "B99",
                        "E01",
                        "lost_power",
                        "Alex",
                        "",
                    )
                ],
            )

            with self.assertRaisesRegex(
                InputError, "observations.csv row 2: unknown breaker_id B99"
            ):
                load_project(root)

    def test_rejects_invalid_observation_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_valid_project(root)
            write_csv(
                root / "observations.csv",
                OBSERVATIONS_HEADER,
                [
                    (
                        "O01",
                        "2026-08-30T10:00:00Z",
                        "B01",
                        "E01",
                        "maybe",
                        "Alex",
                        "",
                    )
                ],
            )

            with self.assertRaisesRegex(
                InputError,
                "observations.csv row 2: result must be lost_power, retained_power, or not_tested",
            ):
                load_project(root)

    def test_rejects_non_utf8_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_valid_project(root)
            (root / "endpoints.csv").write_bytes(b"endpoint_id,location,kind,label\n\xff")

            with self.assertRaisesRegex(InputError, "endpoints.csv must be UTF-8"):
                load_project(root)

    def test_rejects_file_above_size_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_valid_project(root)

            with patch("breakerledger.io.MAX_FILE_BYTES", 10):
                with self.assertRaisesRegex(InputError, "breakers.csv exceeds 10 bytes"):
                    load_project(root)

    def test_rejects_file_above_row_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_valid_project(root)

            with patch("breakerledger.io.MAX_DATA_ROWS", 1):
                with self.assertRaisesRegex(
                    InputError, "breakers.csv exceeds 1 data rows"
                ):
                    load_project(root)

    def test_rejects_unbounded_breaker_endpoint_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_valid_project(root)

            with patch("breakerledger.io.MAX_MAPPING_CELLS", 3):
                with self.assertRaisesRegex(
                    InputError, "breaker x endpoint matrix exceeds 3 cells"
                ):
                    load_project(root)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest
from pathlib import Path

from breakerledger.audit import compile_project
from breakerledger.io import load_project

ROOT = Path(__file__).resolve().parents[1]


class ExampleTests(unittest.TestCase):
    def test_healthy_example_is_fully_confirmed(self) -> None:
        audit = compile_project(load_project(ROOT / "examples" / "healthy-house"))

        self.assertEqual(
            {"confirmed": 5, "tentative": 0, "unmapped": 0, "conflict": 0},
            audit.status_counts,
        )
        self.assertEqual((), audit.retests)

    def test_conflicting_example_exercises_every_unresolved_status(self) -> None:
        audit = compile_project(load_project(ROOT / "examples" / "conflicting-house"))

        self.assertEqual(
            {"confirmed": 0, "tentative": 1, "unmapped": 1, "conflict": 2},
            audit.status_counts,
        )
        self.assertEqual(5, len(audit.retests))


if __name__ == "__main__":
    unittest.main()

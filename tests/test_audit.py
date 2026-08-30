from __future__ import annotations

import unittest

from breakerledger.audit import compile_project
from breakerledger.model import (
    Breaker,
    Endpoint,
    Observation,
    ObservationResult,
    Project,
)


def observation(
    observation_id: str,
    breaker_id: str,
    endpoint_id: str,
    result: ObservationResult,
) -> Observation:
    return Observation(
        observation_id=observation_id,
        observed_at="2026-08-30T10:00:00Z",
        breaker_id=breaker_id,
        endpoint_id=endpoint_id,
        result=result,
        observer="Alex",
        note="",
    )


def project_with(observations: tuple[Observation, ...]) -> Project:
    return Project(
        breakers=(
            Breaker("main", "B01", "1", "15", "Living room"),
            Breaker("main", "B02", "2", "20", "Kitchen"),
            Breaker("main", "B03", "3", "15", "Spare"),
        ),
        endpoints=(
            Endpoint("E01", "Living room", "receptacle", "North wall"),
            Endpoint("E02", "Kitchen", "light", "Ceiling"),
            Endpoint("E03", "Hall", "receptacle", "Console"),
        ),
        observations=observations,
    )


class CompileProjectTests(unittest.TestCase):
    def test_classifies_confirmed_tentative_and_unmapped_endpoints(self) -> None:
        project = project_with(
            (
                observation("O01", "B01", "E01", "lost_power"),
                observation("O02", "B01", "E01", "lost_power"),
                observation("O03", "B02", "E01", "retained_power"),
                observation("O04", "B02", "E02", "lost_power"),
                observation("O05", "B01", "E03", "retained_power"),
            )
        )

        audit = compile_project(project, confirmations=2)
        results = {result.endpoint.endpoint_id: result for result in audit.endpoints}

        self.assertEqual("confirmed", results["E01"].status)
        self.assertEqual(("B01",), results["E01"].breaker_ids)
        self.assertEqual(("O01", "O02"), results["E01"].positive_observation_ids)
        self.assertEqual("tentative", results["E02"].status)
        self.assertEqual(("B02",), results["E02"].breaker_ids)
        self.assertEqual("unmapped", results["E03"].status)
        self.assertEqual((), results["E03"].breaker_ids)
        self.assertEqual(
            {"confirmed": 1, "tentative": 1, "unmapped": 1, "conflict": 0},
            audit.status_counts,
        )

    def test_marks_pair_with_opposite_results_as_conflict(self) -> None:
        project = project_with(
            (
                observation("O01", "B01", "E01", "lost_power"),
                observation("O02", "B01", "E01", "retained_power"),
            )
        )

        audit = compile_project(project, confirmations=2)
        result = next(
            item for item in audit.endpoints if item.endpoint.endpoint_id == "E01"
        )

        self.assertEqual("conflict", result.status)
        self.assertEqual(("B01",), result.breaker_ids)
        self.assertIn("both lost_power and retained_power", result.reason)
        retests = [item for item in audit.retests if item.endpoint_id == "E01"]
        self.assertEqual(1, len(retests))
        self.assertEqual("B01", retests[0].breaker_id)
        self.assertEqual("resolve_conflict", retests[0].action)

    def test_marks_endpoint_claimed_by_two_breakers_as_conflict(self) -> None:
        project = project_with(
            (
                observation("O01", "B01", "E01", "lost_power"),
                observation("O02", "B02", "E01", "lost_power"),
            )
        )

        audit = compile_project(project, confirmations=2)
        result = next(
            item for item in audit.endpoints if item.endpoint.endpoint_id == "E01"
        )

        self.assertEqual("conflict", result.status)
        self.assertEqual(("B01", "B02"), result.breaker_ids)
        self.assertIn("multiple breakers", result.reason)
        self.assertEqual(
            [("B01", "resolve_conflict"), ("B02", "resolve_conflict")],
            [
                (item.breaker_id, item.action)
                for item in audit.retests
                if item.endpoint_id == "E01"
            ],
        )

    def test_retest_queue_covers_tentative_and_unmapped_endpoints(self) -> None:
        project = project_with(
            (
                observation("O01", "B02", "E02", "lost_power"),
                observation("O02", "B01", "E03", "retained_power"),
            )
        )

        audit = compile_project(project, confirmations=2)
        retests = {item.endpoint_id: item for item in audit.retests}

        self.assertEqual("repeat_support", retests["E02"].action)
        self.assertEqual("B02", retests["E02"].breaker_id)
        self.assertEqual("map_endpoint", retests["E03"].action)
        self.assertEqual("", retests["E03"].breaker_id)
        self.assertEqual(("B02", "B03"), retests["E03"].candidate_breaker_ids)

    def test_rejects_confirmation_threshold_below_one(self) -> None:
        with self.assertRaisesRegex(ValueError, "confirmations must be at least 1"):
            compile_project(project_with(()), confirmations=0)


if __name__ == "__main__":
    unittest.main()

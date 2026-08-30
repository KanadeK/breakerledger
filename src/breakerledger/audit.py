from __future__ import annotations

from collections import defaultdict

from .model import (
    Audit,
    Endpoint,
    EndpointResult,
    EndpointStatus,
    Observation,
    ObservationResult,
    Project,
    RetestAction,
)


def compile_project(project: Project, confirmations: int = 2) -> Audit:
    """Return deterministic evidence results for one validated project."""
    if confirmations < 1:
        raise ValueError("confirmations must be at least 1")

    pair_observations: dict[tuple[str, str], list[Observation]] = defaultdict(list)
    for observation in project.observations:
        pair_observations[(observation.endpoint_id, observation.breaker_id)].append(
            observation
        )

    breaker_ids = tuple(sorted(breaker.breaker_id for breaker in project.breakers))
    endpoint_results: list[EndpointResult] = []
    retests: list[RetestAction] = []

    for endpoint in sorted(project.endpoints, key=lambda item: item.endpoint_id):
        evidence = {
            breaker_id: pair_observations.get((endpoint.endpoint_id, breaker_id), [])
            for breaker_id in breaker_ids
        }
        positive_breakers = tuple(
            breaker_id
            for breaker_id in breaker_ids
            if any(item.result == "lost_power" for item in evidence[breaker_id])
        )
        contradictory_breakers = tuple(
            breaker_id
            for breaker_id in breaker_ids
            if _has_result(evidence[breaker_id], "lost_power")
            and _has_result(evidence[breaker_id], "retained_power")
        )

        if contradictory_breakers or len(positive_breakers) > 1:
            implicated = tuple(
                sorted(set(positive_breakers) | set(contradictory_breakers))
            )
            reason_parts: list[str] = []
            if contradictory_breakers:
                reason_parts.append(
                    "breaker pair has both lost_power and retained_power: "
                    + ", ".join(contradictory_breakers)
                )
            if len(positive_breakers) > 1:
                reason_parts.append(
                    "multiple breakers have lost_power evidence: "
                    + ", ".join(positive_breakers)
                )
            result = _endpoint_result(
                endpoint,
                "conflict",
                implicated,
                evidence,
                "; ".join(reason_parts),
            )
            endpoint_results.append(result)
            for breaker_id in implicated:
                retests.append(
                    RetestAction(
                        endpoint_id=endpoint.endpoint_id,
                        current_status="conflict",
                        breaker_id=breaker_id,
                        action="resolve_conflict",
                        reason=f"repeat the {breaker_id}/{endpoint.endpoint_id} test",
                    )
                )
            continue

        if positive_breakers:
            breaker_id = positive_breakers[0]
            support_count = sum(
                item.result == "lost_power" for item in evidence[breaker_id]
            )
            if support_count >= confirmations:
                endpoint_results.append(
                    _endpoint_result(
                        endpoint,
                        "confirmed",
                        (breaker_id,),
                        evidence,
                        f"{support_count} lost_power observations support {breaker_id}",
                    )
                )
            else:
                needed = confirmations - support_count
                reason = (
                    f"{support_count} lost_power observation; {needed} more required"
                )
                endpoint_results.append(
                    _endpoint_result(
                        endpoint,
                        "tentative",
                        (breaker_id,),
                        evidence,
                        reason,
                    )
                )
                retests.append(
                    RetestAction(
                        endpoint_id=endpoint.endpoint_id,
                        current_status="tentative",
                        breaker_id=breaker_id,
                        action="repeat_support",
                        reason=f"collect {needed} more lost_power observation(s)",
                    )
                )
            continue

        endpoint_results.append(
            _endpoint_result(
                endpoint,
                "unmapped",
                (),
                evidence,
                "no breaker has lost_power evidence",
            )
        )
        ruled_out = {
            breaker_id
            for breaker_id in breaker_ids
            if _has_result(evidence[breaker_id], "retained_power")
        }
        candidates = tuple(item for item in breaker_ids if item not in ruled_out)
        retests.append(
            RetestAction(
                endpoint_id=endpoint.endpoint_id,
                current_status="unmapped",
                breaker_id="",
                action="map_endpoint",
                reason="test breakers not yet ruled out by retained_power evidence",
                candidate_breaker_ids=candidates,
            )
        )

    status_counts = {
        status: sum(result.status == status for result in endpoint_results)
        for status in ("confirmed", "tentative", "unmapped", "conflict")
    }
    return Audit(tuple(endpoint_results), tuple(retests), status_counts)


def _has_result(observations: list[Observation], result: ObservationResult) -> bool:
    return any(item.result == result for item in observations)


def _endpoint_result(
    endpoint: Endpoint,
    status: EndpointStatus,
    breaker_ids: tuple[str, ...],
    evidence: dict[str, list[Observation]],
    reason: str,
) -> EndpointResult:
    relevant = breaker_ids or tuple(evidence)
    positive_ids = sorted(
        item.observation_id
        for breaker_id in relevant
        for item in evidence[breaker_id]
        if item.result == "lost_power"
    )
    negative_ids = sorted(
        item.observation_id
        for breaker_id in relevant
        for item in evidence[breaker_id]
        if item.result == "retained_power"
    )
    return EndpointResult(
        endpoint=endpoint,
        status=status,
        breaker_ids=breaker_ids,
        positive_observation_ids=tuple(positive_ids),
        negative_observation_ids=tuple(negative_ids),
        reason=reason,
    )

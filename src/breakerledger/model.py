from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ObservationResult = Literal["lost_power", "retained_power", "not_tested"]
EndpointStatus = Literal["conflict", "confirmed", "tentative", "unmapped"]


@dataclass(frozen=True, slots=True)
class Breaker:
    panel_id: str
    breaker_id: str
    position: str
    rating_amps: str
    label: str


@dataclass(frozen=True, slots=True)
class Endpoint:
    endpoint_id: str
    location: str
    kind: str
    label: str


@dataclass(frozen=True, slots=True)
class Observation:
    observation_id: str
    observed_at: str
    breaker_id: str
    endpoint_id: str
    result: ObservationResult
    observer: str
    note: str


@dataclass(frozen=True, slots=True)
class Project:
    breakers: tuple[Breaker, ...]
    endpoints: tuple[Endpoint, ...]
    observations: tuple[Observation, ...]


@dataclass(frozen=True, slots=True)
class EndpointResult:
    endpoint: Endpoint
    status: EndpointStatus
    breaker_ids: tuple[str, ...]
    positive_observation_ids: tuple[str, ...]
    negative_observation_ids: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class RetestAction:
    endpoint_id: str
    current_status: EndpointStatus
    breaker_id: str
    action: Literal["resolve_conflict", "repeat_support", "map_endpoint"]
    reason: str
    candidate_breaker_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Audit:
    endpoints: tuple[EndpointResult, ...]
    retests: tuple[RetestAction, ...]
    status_counts: dict[str, int]


"""Scout Swarm retrieval nodes."""

from __future__ import annotations

from google.adk import Event

from ..config import get_settings
from ..schemas import CandidateBundle, SupportProfile
from ..tools.resource_store import ResourceStore


_STORE = ResourceStore()


def search_resources(node_input: SupportProfile) -> CandidateBundle:
    settings = get_settings()
    candidates, trace, location, lat, lon = _STORE.search(
        node_input, max_candidates=settings.max_candidates
    )
    return CandidateBundle(
        profile=node_input,
        candidates=candidates,
        search_trace=trace,
        normalized_location=location,
        origin_latitude=lat,
        origin_longitude=lon,
        demo_data=settings.demo_mode,
    )


def candidate_router(node_input: CandidateBundle) -> Event:
    route = "FOUND" if node_input.candidates else "NO_RESULTS"
    return Event(route=route, output=node_input.model_dump(mode="json"))


def evidence_fanout(node_input: CandidateBundle) -> CandidateBundle:
    return node_input


def candidate_passthrough(node_input: CandidateBundle) -> CandidateBundle:
    return node_input

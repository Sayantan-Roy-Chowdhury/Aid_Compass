"""Parallel deterministic evidence nodes and fan-in merger."""

from __future__ import annotations

from datetime import date
from typing import Any

from ..schemas import (
    AccessAssessment,
    AccessReport,
    BarrierReport,
    CandidateBundle,
    EligibilityReport,
    EvidenceBundle,
    TrustAssessment,
    TrustReport,
)
from ..tools.scoring import clamp, freshness_score, haversine_km


def trust_radar(node_input: CandidateBundle) -> TrustReport:
    assessments: list[TrustAssessment] = []
    for candidate in node_input.candidates:
        resource = candidate.resource
        fresh, age_days = freshness_score(resource.last_verified, date.today())
        source_score = {
            "official": 1.0,
            "directory": 0.8,
            "community": 0.6,
            "demo": 0.75,
        }[resource.source_kind]
        completeness_fields = [
            resource.source_url,
            resource.contact.website or resource.contact.phone or resource.contact.email,
            resource.delivery_modes,
            resource.service_areas,
        ]
        completeness = sum(bool(item) for item in completeness_fields) / len(completeness_fields)
        score = clamp(0.5 * fresh + 0.3 * source_score + 0.2 * completeness)
        confidence = "high" if score >= 0.82 else "medium" if score >= 0.58 else "low"
        reasons = [
            f"Verified {age_days} days ago",
            f"Source type: {resource.source_kind}",
            f"Contact/source completeness: {round(completeness * 100)}%",
        ]
        assessments.append(
            TrustAssessment(
                resource_id=resource.resource_id,
                confidence=confidence,
                score=round(score, 4),
                reasons=reasons,
                verify_before_visiting=confidence != "high" or age_days > 90,
            )
        )
    return TrustReport(assessments=assessments)


def access_mapper(node_input: CandidateBundle) -> AccessReport:
    assessments: list[AccessAssessment] = []
    profile = node_input.profile
    requested_modes = set(profile.preferences.delivery_modes)
    for candidate in node_input.candidates:
        resource = candidate.resource
        distance = None
        distance_score = 0.7
        if (
            node_input.origin_latitude is not None
            and node_input.origin_longitude is not None
            and resource.latitude is not None
            and resource.longitude is not None
        ):
            distance = haversine_km(
                node_input.origin_latitude,
                node_input.origin_longitude,
                resource.latitude,
                resource.longitude,
            )
            radius = max(0.5, profile.preferences.travel_radius_km)
            distance_score = clamp(1.0 - max(0.0, distance - 1.0) / radius)

        modes = set(resource.delivery_modes)
        if requested_modes:
            mode_score = len(requested_modes.intersection(modes)) / len(requested_modes)
        else:
            mode_score = 0.9 if modes else 0.3
        if profile.preferences.online_only:
            mode_score = 1.0 if "online" in modes else 0.0

        language_score = 0.7
        language_matches = set(profile.preferences.languages).intersection(resource.languages)
        if profile.preferences.languages:
            language_score = 1.0 if language_matches else 0.45

        accessibility_score = 0.8
        if profile.preferences.accessibility_needs:
            normalized = " ".join(resource.accessibility).lower()
            hits = sum(
                need.lower() in normalized for need in profile.preferences.accessibility_needs
            )
            accessibility_score = hits / len(profile.preferences.accessibility_needs)

        score = clamp(
            0.4 * distance_score
            + 0.3 * mode_score
            + 0.15 * language_score
            + 0.15 * accessibility_score
        )
        mode_fit = sorted(requested_modes.intersection(modes)) if requested_modes else sorted(modes)
        notes = []
        if profile.preferences.preferred_times:
            notes.append("Confirm that listed hours match the preferred time window.")
        assessments.append(
            AccessAssessment(
                resource_id=resource.resource_id,
                score=round(score, 4),
                distance_km=round(distance, 2) if distance is not None else None,
                mode_fit=mode_fit,
                schedule_notes=notes,
            )
        )
    return AccessReport(assessments=assessments)


def merge_evidence(node_input: dict[str, Any]) -> EvidenceBundle:
    try:
        candidates = CandidateBundle.model_validate(node_input["candidate_passthrough"])
        eligibility = EligibilityReport.model_validate(node_input["eligibility_lens"])
        barriers = BarrierReport.model_validate(node_input["barrier_breaker"])
        trust = TrustReport.model_validate(node_input["trust_radar"])
        access = AccessReport.model_validate(node_input["access_mapper"])
    except KeyError as exc:
        raise ValueError(f"Evidence join is missing branch output: {exc}") from exc
    return EvidenceBundle(
        candidates=candidates,
        eligibility=eligibility,
        barriers=barriers,
        trust=trust,
        access=access,
    )

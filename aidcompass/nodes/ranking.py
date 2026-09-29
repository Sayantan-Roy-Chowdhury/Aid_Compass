"""Matchmaker: deterministic, explainable resource ranking."""

from __future__ import annotations

from ..schemas import EvidenceBundle, NeedCategory, RankedResource, RankingResult
from ..tools.scoring import clamp


ELIGIBILITY_SCORE = {
    "likely": 1.0,
    "possible": 0.78,
    "uncertain": 0.52,
    "unlikely": 0.12,
}


def rank_resources(node_input: EvidenceBundle) -> RankingResult:
    eligibility = {item.resource_id: item for item in node_input.eligibility.assessments}
    barriers = {item.resource_id: item for item in node_input.barriers.matches}
    trust = {item.resource_id: item for item in node_input.trust.assessments}
    access = {item.resource_id: item for item in node_input.access.assessments}

    ranked: list[RankedResource] = []
    for candidate in node_input.candidates.candidates:
        rid = candidate.resource.resource_id
        eligibility_item = eligibility.get(rid)
        barrier_item = barriers.get(rid)
        trust_item = trust.get(rid)
        access_item = access.get(rid)

        e_score = ELIGIBILITY_SCORE.get(
            eligibility_item.label if eligibility_item else "uncertain", 0.52
        )
        b_score = barrier_item.fit_score if barrier_item else 0.55
        t_score = trust_item.score if trust_item else 0.45
        a_score = access_item.score if access_item else 0.55
        breakdown = {
            "need_match": candidate.base_match_score,
            "eligibility": e_score,
            "barrier_fit": b_score,
            "trust": t_score,
            "access": a_score,
        }
        total = clamp(
            0.35 * breakdown["need_match"]
            + 0.20 * breakdown["eligibility"]
            + 0.17 * breakdown["barrier_fit"]
            + 0.15 * breakdown["trust"]
            + 0.13 * breakdown["access"]
        )

        why = list(candidate.match_reasons)
        watch = list(candidate.hard_filter_notes)
        if eligibility_item:
            why.extend(eligibility_item.reasons[:2])
            watch.extend(eligibility_item.missing_information)
        if barrier_item:
            why.extend(barrier_item.barriers_addressed[:2])
            watch.extend(barrier_item.remaining_barriers[:2])
        if trust_item and trust_item.verify_before_visiting:
            watch.append("Confirm current hours and availability before visiting.")
        if access_item and access_item.distance_km is not None:
            why.append(f"About {access_item.distance_km} km from the demo location point")

        ranked.append(
            RankedResource(
                resource=candidate.resource,
                total_score=round(total, 4),
                score_breakdown={key: round(value, 4) for key, value in breakdown.items()},
                why_match=list(dict.fromkeys(why)),
                watch_outs=list(dict.fromkeys(watch)),
                eligibility_label=eligibility_item.label if eligibility_item else "uncertain",
                confidence_label=trust_item.confidence if trust_item else "low",
            )
        )

    ranked.sort(key=lambda item: item.total_score, reverse=True)
    selected = ranked[:5]
    covered: set[NeedCategory] = set()
    for item in selected:
        covered.update(item.resource.categories)
    requested = {need.category for need in node_input.candidates.profile.needs}
    unmet = sorted(requested - covered, key=lambda item: item.value)

    trace = list(node_input.candidates.search_trace)
    trace.append("Ranking weights: need 35%, eligibility 20%, barrier 17%, trust 15%, access 13%.")
    trace.append(f"Returned {len(selected)} ranked resources.")
    return RankingResult(
        profile=node_input.candidates.profile,
        ranked_resources=selected,
        unmet_needs=unmet,
        ranking_trace=trace,
        demo_data=node_input.candidates.demo_data,
    )

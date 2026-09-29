from aidcompass.nodes.evidence import access_mapper, trust_radar
from aidcompass.nodes.ranking import rank_resources
from aidcompass.nodes.retrieval import search_resources
from aidcompass.schemas import (
    AgeBand,
    BarrierMatch,
    BarrierReport,
    EligibilityAssessment,
    EligibilityReport,
    EvidenceBundle,
    NeedCategory,
    NeedItem,
    SupportProfile,
)


def test_ranking_returns_explainable_scores():
    profile = SupportProfile(
        safe_summary="Teen needs free math help.",
        location_text="Scarborough",
        age_band=AgeBand.AGE_13_17,
        needs=[NeedItem(category=NeedCategory.EDUCATION_SUPPORT, statement="math tutoring")],
    )
    bundle = search_resources(profile)
    eligibility = EligibilityReport(
        assessments=[
            EligibilityAssessment(
                resource_id=item.resource.resource_id,
                label="likely",
                reasons=["Age and area appear to match."],
            )
            for item in bundle.candidates
        ]
    )
    barriers = BarrierReport(
        matches=[
            BarrierMatch(resource_id=item.resource.resource_id, fit_score=0.8)
            for item in bundle.candidates
        ]
    )
    result = rank_resources(
        EvidenceBundle(
            candidates=bundle,
            eligibility=eligibility,
            barriers=barriers,
            trust=trust_radar(bundle),
            access=access_mapper(bundle),
        )
    )
    assert result.ranked_resources
    assert 0 <= result.ranked_resources[0].total_score <= 1
    assert set(result.ranked_resources[0].score_breakdown) == {
        "need_match",
        "eligibility",
        "barrier_fit",
        "trust",
        "access",
    }

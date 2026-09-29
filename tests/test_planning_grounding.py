from types import SimpleNamespace

from aidcompass.nodes.planning import critique_router, ground_plan, safe_fallback_review
from aidcompass.schemas import (
    ActionStep,
    BarrierType,
    ContactDraft,
    NeedCategory,
    NeedItem,
    PlanCritique,
    PlanOption,
    PlanReviewBundle,
    RankedResource,
    RankingResult,
    SupportPlan,
    SupportProfile,
    UserBarrier,
)
from aidcompass.tools.resource_store import ResourceStore


def _ranking() -> RankingResult:
    first, second = ResourceStore().resources[:2]
    ranked = [
        RankedResource(
            resource=resource,
            total_score=score,
            score_breakdown={
                "need_match": score,
                "eligibility": 1.0,
                "barrier_fit": 0.8,
                "trust": 0.9,
                "access": 0.8,
            },
            why_match=["Grounded match"],
            eligibility_label="likely",
            confidence_label="high",
        )
        for resource, score in [(first, 0.92), (second, 0.84)]
    ]
    profile = SupportProfile(
        safe_summary="Teen needs tutoring and has a schedule barrier.",
        location_text="Scarborough",
        needs=[NeedItem(category=NeedCategory.EDUCATION_SUPPORT, statement="math help")],
        barriers=[
            UserBarrier(
                barrier=BarrierType.SCHEDULE,
                statement="Only available after school.",
            )
        ],
    )
    return RankingResult(profile=profile, ranked_resources=ranked, demo_data=True)


def _plan(ranking: RankingResult, revision_count: int = 0) -> SupportPlan:
    canonical = ranking.ranked_resources[0]
    tampered_resource = canonical.resource.model_copy(
        update={
            "name": "Invented Resource Name",
            "source_url": "https://invented.invalid/resource",
        }
    )
    tampered_ranked = canonical.model_copy(update={"resource": tampered_resource})
    rid = canonical.resource.resource_id
    step = ActionStep(
        order=1,
        action="Check the service.",
        reason="It is the strongest match.",
        resource_id=rid,
    )
    return SupportPlan(
        headline="Test plan",
        best_first_step=step,
        selected_resources=[tampered_ranked, ranking.ranked_resources[1]],
        plan_a=PlanOption(
            title="A",
            purpose="Primary",
            resource_ids=[rid],
            steps=[step],
            use_when="First",
        ),
        plan_b=PlanOption(
            title="B",
            purpose="Backup",
            resource_ids=[rid],
            steps=[step],
            use_when="If needed",
        ),
        contact_drafts=[
            ContactDraft(
                resource_id="invented_id",
                channel="email",
                body="Hello",
            )
        ],
        shareable_summary="Test",
        revision_count=revision_count,
    )


def test_ground_plan_restores_canonical_records_and_taxonomy():
    ranking = _ranking()
    ctx = SimpleNamespace(state={"latest_ranking": ranking.model_dump(mode="json")})
    grounded = ground_plan(ctx, _plan(ranking))

    assert grounded.selected_resources[0].resource.name == ranking.ranked_resources[0].resource.name
    assert grounded.selected_resources[0].resource.source_url == (
        ranking.ranked_resources[0].resource.source_url
    )
    assert grounded.plan_a.resource_ids != grounded.plan_b.resource_ids
    assert grounded.contact_drafts == []
    assert grounded.requested_needs == [NeedCategory.EDUCATION_SUPPORT]
    assert grounded.barrier_types == [BarrierType.SCHEDULE]


def test_critic_uses_conservative_fallback_after_revision_cap():
    ranking = _ranking()
    plan = _plan(ranking, revision_count=2)
    ctx = SimpleNamespace(
        state={
            "latest_ranking": ranking.model_dump(mode="json"),
            "latest_plan": plan.model_dump(mode="json"),
        }
    )
    critique = PlanCritique(
        verdict="REVISE",
        quality_score=0.4,
        hallucination_risks=["Unsupported detail"],
    )
    event = critique_router(ctx, critique)
    assert event.actions.route == "FALLBACK"

    review = safe_fallback_review(ctx, PlanReviewBundle(plan=plan, critique=critique))
    assert review.critique.verdict == "READY"
    assert review.plan.selected_resources[0].resource == ranking.ranked_resources[0].resource
    assert "conservative fallback" in review.plan.confidence_notes[0].lower()

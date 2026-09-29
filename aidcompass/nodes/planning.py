"""Plan grounding, persistence, and critic-controlled repair loop."""

from __future__ import annotations

from google.adk import Event
from google.adk.agents.context import Context

from ..schemas import (
    ActionStep,
    BarrierType,
    ContactDraft,
    PlanCritique,
    PlanOption,
    PlanReviewBundle,
    RankedResource,
    RankingResult,
    SupportPlan,
)


MAX_AUTOMATIC_REVISIONS = 2
MAX_SELECTED_RESOURCES = 5


def save_ranking(ctx: Context, node_input: RankingResult) -> RankingResult:
    """Persist the canonical ranked evidence across critic and HITL loops."""
    ctx.state["latest_ranking"] = node_input.model_dump(mode="json")
    return node_input


def _canonical_ranking(ctx: Context) -> RankingResult:
    raw = ctx.state.get("latest_ranking")
    if not raw:
        raise ValueError("Plan grounding ran without canonical ranking evidence.")
    return RankingResult.model_validate(raw)


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _sanitize_step(step: ActionStep, allowed_ids: set[str]) -> ActionStep:
    resource_id = step.resource_id if step.resource_id in allowed_ids else None
    return step.model_copy(update={"resource_id": resource_id})


def _sanitize_option(
    option: PlanOption,
    *,
    allowed_ids: set[str],
    default_ids: list[str],
) -> PlanOption:
    resource_ids = _unique([rid for rid in option.resource_ids if rid in allowed_ids])
    if not resource_ids:
        resource_ids = default_ids[:1]
    steps = [_sanitize_step(step, allowed_ids) for step in option.steps]
    return option.model_copy(update={"resource_ids": resource_ids, "steps": steps})


def ground_plan(ctx: Context, node_input: SupportPlan) -> SupportPlan:
    """Restore immutable resource facts after every LLM-authored plan or revision.

    LLM nodes may choose, explain, and sequence resources, but this node owns factual
    identity. It discards invented IDs and replaces selected records with the exact
    `RankedResource` objects produced by deterministic retrieval/ranking.
    """
    ranking = _canonical_ranking(ctx)
    canonical: dict[str, RankedResource] = {
        item.resource.resource_id: item for item in ranking.ranked_resources
    }

    requested_ids = [item.resource.resource_id for item in node_input.selected_resources]
    requested_ids += node_input.plan_a.resource_ids
    requested_ids += node_input.plan_b.resource_ids
    requested_ids += [
        node_input.best_first_step.resource_id or "",
        *[draft.resource_id for draft in node_input.contact_drafts],
    ]
    selected_ids = _unique([rid for rid in requested_ids if rid in canonical])
    if not selected_ids:
        selected_ids = list(canonical)[:3]
    selected_ids = selected_ids[:MAX_SELECTED_RESOURCES]
    allowed_ids = set(selected_ids)
    selected_resources = [canonical[rid] for rid in selected_ids]

    plan_a = _sanitize_option(
        node_input.plan_a,
        allowed_ids=allowed_ids,
        default_ids=selected_ids[:1],
    )
    plan_b_default = selected_ids[1:2] or selected_ids[:1]
    plan_b = _sanitize_option(
        node_input.plan_b,
        allowed_ids=allowed_ids,
        default_ids=plan_b_default,
    )
    if plan_b.resource_ids == plan_a.resource_ids and len(selected_ids) > 1:
        plan_b = plan_b.model_copy(update={"resource_ids": selected_ids[1:2]})

    contact_drafts: list[ContactDraft] = [
        draft for draft in node_input.contact_drafts if draft.resource_id in allowed_ids
    ][:3]
    requested_needs = list(dict.fromkeys(need.category for need in ranking.profile.needs))
    barrier_types = list(dict.fromkeys(barrier.barrier for barrier in ranking.profile.barriers))

    return node_input.model_copy(
        update={
            "requested_needs": requested_needs,
            "barrier_types": barrier_types,
            "best_first_step": _sanitize_step(node_input.best_first_step, allowed_ids),
            "selected_resources": selected_resources,
            "plan_a": plan_a,
            "plan_b": plan_b,
            "contact_drafts": contact_drafts,
            "unmet_needs": ranking.unmet_needs,
            "demo_data_notice": (
                "This project ships with synthetic demonstration resources."
                if ranking.demo_data
                else "Confirm current availability and requirements with each organization."
            ),
        }
    )


def save_plan(ctx: Context, node_input: SupportPlan) -> SupportPlan:
    ctx.state["latest_plan"] = node_input.model_dump(mode="json")
    return node_input


def critique_router(ctx: Context, node_input: PlanCritique) -> Event:
    raw_plan = ctx.state.get("latest_plan")
    if not raw_plan:
        raise ValueError("Plan critic ran without a saved plan.")
    plan = SupportPlan.model_validate(raw_plan)
    ready = (
        node_input.verdict == "READY"
        and node_input.quality_score >= 0.80
        and not node_input.hallucination_risks
    )
    if ready:
        route = "READY"
    elif plan.revision_count >= MAX_AUTOMATIC_REVISIONS:
        route = "FALLBACK"
    else:
        route = "REVISE"
    bundle = PlanReviewBundle(plan=plan, critique=node_input)
    return Event(route=route, output=bundle.model_dump(mode="json"))


def safe_fallback_review(ctx: Context, node_input: PlanReviewBundle) -> PlanReviewBundle:
    """Build a conservative, fully grounded plan when the LLM repair loop stalls."""
    ranking = _canonical_ranking(ctx)
    canonical = {item.resource.resource_id: item for item in ranking.ranked_resources}
    selected_ids = [
        item.resource.resource_id
        for item in node_input.plan.selected_resources
        if item.resource.resource_id in canonical
    ]
    selected = [canonical[rid] for rid in dict.fromkeys(selected_ids)][:3]
    if not selected:
        selected = ranking.ranked_resources[: min(3, len(ranking.ranked_resources))]
    if not selected:
        raise ValueError("Cannot build fallback plan without ranked resources.")

    primary = selected[0].resource
    alternate = selected[1].resource if len(selected) > 1 else primary
    first = ActionStep(
        order=1,
        action=f"Open the listed source for {primary.name} and confirm current availability.",
        reason="This uses the highest-ranked record while checking details that may change.",
        resource_id=primary.resource_id,
        timing="Next",
    )
    plan_a = PlanOption(
        title="Verified-source first route",
        purpose=f"Start with {primary.name}, the highest-ranked grounded match.",
        resource_ids=[primary.resource_id],
        steps=[
            first,
            ActionStep(
                order=2,
                action="Ask what is required to begin and whether the listed access mode is available.",
                reason="The organization controls intake, eligibility, and current capacity.",
                resource_id=primary.resource_id,
                timing="After checking the source",
            ),
        ],
        use_when="Use this when the top resource is available and its current terms fit.",
    )
    plan_b = PlanOption(
        title="Independent backup route",
        purpose=f"Use {alternate.name} if the first option is unavailable or unsuitable.",
        resource_ids=[alternate.resource_id],
        steps=[
            ActionStep(
                order=1,
                action=f"Check the listed source for {alternate.name}.",
                reason="This is a separate grounded option from the ranked evidence.",
                resource_id=alternate.resource_id,
                timing="Backup",
            )
        ],
        use_when="Use this when Plan A is closed, full, inaccessible, or not a fit.",
    )
    requested_needs = [need.category for need in ranking.profile.needs]
    barrier_types: list[BarrierType] = [barrier.barrier for barrier in ranking.profile.barriers]
    fallback = SupportPlan(
        headline="A cautious, source-checked support route",
        requested_needs=list(dict.fromkeys(requested_needs)),
        barrier_types=list(dict.fromkeys(barrier_types)),
        best_first_step=first,
        selected_resources=selected,
        plan_a=plan_a,
        plan_b=plan_b,
        document_backpack=[
            "Only bring documents explicitly confirmed by the organization; ask about alternatives if needed."
        ],
        contact_drafts=[],
        confidence_notes=[
            "The automatic critic did not approve the richer generated plan, so AidCompass replaced it with this conservative fallback.",
            "Eligibility, hours, and capacity must be confirmed with the organization.",
        ],
        shareable_summary=(
            f"Start by checking {primary.name}; use {alternate.name} as a backup. "
            "Confirm current availability and requirements before sharing personal information."
        ),
        unmet_needs=ranking.unmet_needs,
        revision_count=node_input.plan.revision_count,
        demo_data_notice=(
            "This project ships with synthetic demonstration resources."
            if ranking.demo_data
            else "Confirm current availability and requirements with each organization."
        ),
    )
    critique = PlanCritique(
        verdict="READY",
        quality_score=0.95,
        issues=["The previous generated plan did not pass the critic within the revision cap."],
        required_changes=[],
        hallucination_risks=[],
    )
    ctx.state["latest_plan"] = fallback.model_dump(mode="json")
    return PlanReviewBundle(plan=fallback, critique=critique)

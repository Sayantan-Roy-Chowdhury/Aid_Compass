"""Human Navigator Gate: resumable review and user-controlled replanning."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

from google.adk import Event
from google.adk.agents.context import Context
from google.adk.events import RequestInput

from ..schemas import PlanReviewBundle, SupportPlan, UserRevisionRequest


APPROVE_WORDS = {"approve", "approved", "yes", "looks good", "go ahead", "ok", "okay"}
CANCEL_WORDS = {"cancel", "stop", "never mind", "nevermind"}


def request_plan_approval(
    ctx: Context, node_input: PlanReviewBundle
) -> Generator[Event | RequestInput, None, None]:
    plan = node_input.plan
    ctx.state["pending_plan"] = plan.model_dump(mode="json")
    ctx.state["pending_critique"] = node_input.critique.model_dump(mode="json")
    yield Event(
        state={
            "pending_plan": plan.model_dump(mode="json"),
            "pending_critique": node_input.critique.model_dump(mode="json"),
        }
    )
    yield RequestInput(
        message=(
            "Review the proposed support journey. Reply APPROVE, CANCEL, or describe "
            "a change such as 'online only', 'no phone calls', or 'after 5 PM'."
        ),
        payload=plan.model_dump(mode="json"),
    )


def _parse_feedback(value: Any) -> tuple[str, str]:
    if isinstance(value, dict):
        decision = str(value.get("decision", "")).strip().lower()
        feedback = str(value.get("feedback", value.get("text", ""))).strip()
        if decision:
            return decision, feedback
        value = feedback or str(value)
    text = str(value).strip()
    return text.lower(), text


def approval_router(ctx: Context, node_input: Any) -> Event:
    raw_plan = ctx.state.get("pending_plan")
    if not raw_plan:
        raise ValueError("Approval response received without a pending plan.")
    plan = SupportPlan.model_validate(raw_plan)
    normalized, original = _parse_feedback(node_input)

    if normalized in APPROVE_WORDS or normalized.startswith("approve"):
        return Event(route="APPROVE", output=plan.model_dump(mode="json"))
    if normalized in CANCEL_WORDS or normalized.startswith("cancel"):
        return Event(route="CANCEL", output={"status": "cancelled"})

    revision = UserRevisionRequest(plan=plan, feedback=original)
    return Event(route="REVISE", output=revision.model_dump(mode="json"))


def render_cancelled(node_input: Any) -> Event:
    return Event(
        message=(
            "No plan was finalized. AidCompass did not contact or enroll you with any organization."
        ),
        output={"status": "cancelled"},
    )

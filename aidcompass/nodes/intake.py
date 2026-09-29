"""Progressive intake and clarification nodes."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

from google.adk import Event
from google.adk.agents.context import Context
from google.adk.events import RequestInput

from ..schemas import RequestEnvelope, SupportProfile


MAX_CLARIFICATION_ROUNDS = 2


def clarification_router(ctx: Context, node_input: SupportProfile) -> Event:
    count = int(ctx.state.get("clarification_count", 0))
    needs_location = "location" in {item.lower() for item in node_input.missing_required_fields}
    should_clarify = (
        bool(node_input.clarifying_questions)
        and count < MAX_CLARIFICATION_ROUNDS
        and (needs_location or not node_input.needs)
    )
    ctx.state["pending_profile"] = node_input.model_dump(mode="json")
    if should_clarify:
        ctx.state["clarification_count"] = count + 1
        return Event(route="CLARIFY", output=node_input.model_dump(mode="json"))
    return Event(route="SEARCH", output=node_input.model_dump(mode="json"))


def ask_clarification(
    ctx: Context, node_input: SupportProfile
) -> Generator[Event | RequestInput, None, None]:
    ctx.state["pending_profile"] = node_input.model_dump(mode="json")
    questions = node_input.clarifying_questions[:2] or [
        "Which city or neighborhood should I search?"
    ]
    yield Event(state={"pending_profile": node_input.model_dump(mode="json")})
    yield RequestInput(
        message="A small detail will improve the matches: " + " ".join(questions),
        payload={"questions": questions, "current_summary": node_input.safe_summary},
    )


def _response_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("answer", "feedback", "text", "message"):
            if key in value:
                return str(value[key])
    return str(value)


def merge_clarification(ctx: Context, node_input: Any) -> RequestEnvelope:
    pending = ctx.state.get("pending_profile") or {}
    prior = SupportProfile.model_validate(pending)
    reply = _response_text(node_input).strip()
    combined = f"{prior.safe_summary} Additional information from the user: {reply}"
    return RequestEnvelope(
        message=combined,
        clarification_round=prior.clarification_round + 1,
    )

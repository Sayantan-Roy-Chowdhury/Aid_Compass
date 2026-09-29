"""Creative, narrowly-scoped LLM agents used as ADK graph nodes."""

from __future__ import annotations

from google.adk import Agent
from google.adk.workflow import RetryConfig

from ..callbacks import after_agent_trace, before_agent_trace
from ..config import get_settings
from ..prompts import (
    BARRIER_BREAKER_PROMPT,
    ELIGIBILITY_LENS_PROMPT,
    PLAN_CRITIC_PROMPT,
    PLAN_WEAVER_PROMPT,
    REPLANNER_PROMPT,
    SIGNAL_LENS_PROMPT,
    USER_REPLANNER_PROMPT,
)
from ..schemas import (
    BarrierReport,
    CandidateBundle,
    EligibilityReport,
    PlanCritique,
    PlanReviewBundle,
    RankingResult,
    RequestEnvelope,
    SupportPlan,
    SupportProfile,
    UserRevisionRequest,
)
from ..skill_loader import make_skill_toolset


_SETTINGS = get_settings()
_RETRY = RetryConfig(max_attempts=2, initial_delay=0.5, backoff_factor=2.0, max_delay=4.0)


def _agent(**kwargs) -> Agent:
    return Agent(
        model=_SETTINGS.model,
        mode="single_turn",
        retry_config=_RETRY,
        timeout=60,
        before_agent_callback=before_agent_trace,
        after_agent_callback=after_agent_trace,
        **kwargs,
    )


signal_lens_agent = _agent(
    name="signal_lens",
    description="Turns an unstructured story into a privacy-minimized support profile.",
    instruction=SIGNAL_LENS_PROMPT,
    input_schema=RequestEnvelope,
    output_schema=SupportProfile,
    tools=[make_skill_toolset("story-to-needs", "privacy-and-safety")],
)

eligibility_lens_agent = _agent(
    name="eligibility_lens",
    description="Interprets supplied eligibility rules without overclaiming.",
    instruction=ELIGIBILITY_LENS_PROMPT,
    input_schema=CandidateBundle,
    output_schema=EligibilityReport,
    tools=[make_skill_toolset("eligibility-explainer")],
)

barrier_breaker_agent = _agent(
    name="barrier_breaker",
    description="Finds practical access barriers and grounded workarounds.",
    instruction=BARRIER_BREAKER_PROMPT,
    input_schema=CandidateBundle,
    output_schema=BarrierReport,
    tools=[make_skill_toolset("barrier-busting")],
)

plan_weaver_agent = _agent(
    name="plan_weaver",
    description="Builds a low-overwhelm Plan A, Plan B, checklist, and warm handoff.",
    instruction=PLAN_WEAVER_PROMPT,
    input_schema=RankingResult,
    output_schema=SupportPlan,
    tools=[
        make_skill_toolset(
            "action-plan-weaving",
            "warm-handoff",
            "trust-and-citations",
        )
    ],
)

plan_critic_agent = _agent(
    name="plan_critic",
    description="Audits grounding, safety, barrier coverage, and actionability.",
    instruction=PLAN_CRITIC_PROMPT,
    input_schema=SupportPlan,
    output_schema=PlanCritique,
    tools=[
        make_skill_toolset(
            "trust-and-citations",
            "privacy-and-safety",
            "action-plan-weaving",
        )
    ],
)

replanner_agent = _agent(
    name="plan_repair",
    description="Repairs a plan based on the critic without inventing resources.",
    instruction=REPLANNER_PROMPT,
    input_schema=PlanReviewBundle,
    output_schema=SupportPlan,
    tools=[
        make_skill_toolset(
            "action-plan-weaving",
            "warm-handoff",
            "trust-and-citations",
        )
    ],
)

user_replanner_agent = _agent(
    name="human_feedback_replanner",
    description="Adapts a plan to user feedback while preserving grounding.",
    instruction=USER_REPLANNER_PROMPT,
    input_schema=UserRevisionRequest,
    output_schema=SupportPlan,
    tools=[
        make_skill_toolset(
            "action-plan-weaving",
            "warm-handoff",
            "barrier-busting",
        )
    ],
)

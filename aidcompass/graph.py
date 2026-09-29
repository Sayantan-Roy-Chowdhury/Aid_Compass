"""ADK 2.x graph workflow for AidCompass."""

from __future__ import annotations

from google.adk import Workflow
from google.adk.workflow import FunctionNode, JoinNode, RetryConfig

from .nodes.analytics import log_gap_event
from .nodes.approval import approval_router, render_cancelled, request_plan_approval
from .nodes.evidence import access_mapper, merge_evidence, trust_radar
from .nodes.intake import ask_clarification, clarification_router, merge_clarification
from .nodes.planning import (
    critique_router,
    ground_plan,
    safe_fallback_review,
    save_plan,
    save_ranking,
)
from .nodes.ranking import rank_resources
from .nodes.rendering import render_final_plan, render_no_results
from .nodes.retrieval import (
    candidate_passthrough,
    candidate_router,
    evidence_fanout,
    search_resources,
)
from .nodes.safety import capture_request, privacy_safety_gate, render_safety_response
from .schemas import AidCompassState
from .subagents import (
    barrier_breaker_agent,
    eligibility_lens_agent,
    plan_critic_agent,
    plan_weaver_agent,
    replanner_agent,
    signal_lens_agent,
    user_replanner_agent,
)


IO_RETRY = RetryConfig(max_attempts=3, initial_delay=0.25, backoff_factor=2.0, max_delay=2.0)

capture_request_node = FunctionNode(func=capture_request, name="capture_request")
privacy_safety_gate_node = FunctionNode(func=privacy_safety_gate, name="boundary_guardian")
safety_response_node = FunctionNode(func=render_safety_response, name="safety_response")
clarification_router_node = FunctionNode(func=clarification_router, name="clarification_router")
ask_clarification_node = FunctionNode(func=ask_clarification, name="human_clarification")
merge_clarification_node = FunctionNode(func=merge_clarification, name="merge_clarification")
search_resources_node = FunctionNode(
    func=search_resources,
    name="resource_scout",
    retry_config=IO_RETRY,
    timeout=20,
)
candidate_router_node = FunctionNode(func=candidate_router, name="candidate_router")
evidence_fanout_node = FunctionNode(func=evidence_fanout, name="scout_swarm_anchor")
candidate_passthrough_node = FunctionNode(func=candidate_passthrough, name="candidate_passthrough")
trust_radar_node = FunctionNode(func=trust_radar, name="trust_radar")
access_mapper_node = FunctionNode(func=access_mapper, name="access_mapper")
evidence_join_node = JoinNode(name="evidence_join")
merge_evidence_node = FunctionNode(func=merge_evidence, name="merge_evidence")
rank_resources_node = FunctionNode(func=rank_resources, name="matchmaker")
save_ranking_node = FunctionNode(func=save_ranking, name="save_ranking")
ground_plan_node = FunctionNode(func=ground_plan, name="canonical_plan_grounder")
save_plan_node = FunctionNode(func=save_plan, name="save_plan")
critique_router_node = FunctionNode(func=critique_router, name="critique_router")
safe_fallback_review_node = FunctionNode(
    func=safe_fallback_review, name="conservative_fallback_builder"
)
request_approval_node = FunctionNode(func=request_plan_approval, name="human_navigator_gate")
approval_router_node = FunctionNode(func=approval_router, name="approval_router")
log_gap_event_node = FunctionNode(func=log_gap_event, name="community_pulse")
render_final_plan_node = FunctionNode(func=render_final_plan, name="final_renderer")
render_no_results_node = FunctionNode(func=render_no_results, name="no_results_renderer")
render_cancelled_node = FunctionNode(func=render_cancelled, name="cancelled_renderer")


root_agent = Workflow(
    name="aidcompass",
    description=(
        "No-wrong-door community support navigator using safety routing, progressive intake, "
        "parallel evidence analysis, explainable ranking, critic repair, and human approval."
    ),
    state_schema=AidCompassState,
    max_concurrency=5,
    edges=[
        ("START", capture_request_node, privacy_safety_gate_node),
        (
            privacy_safety_gate_node,
            {
                "SAFETY": safety_response_node,
                "CONTINUE": signal_lens_agent,
            },
        ),
        (signal_lens_agent, clarification_router_node),
        (
            clarification_router_node,
            {
                "CLARIFY": ask_clarification_node,
                "SEARCH": search_resources_node,
            },
        ),
        (ask_clarification_node, merge_clarification_node, signal_lens_agent),
        (search_resources_node, candidate_router_node),
        (
            candidate_router_node,
            {
                "FOUND": evidence_fanout_node,
                "NO_RESULTS": render_no_results_node,
            },
        ),
        (evidence_fanout_node, candidate_passthrough_node, evidence_join_node),
        (evidence_fanout_node, eligibility_lens_agent, evidence_join_node),
        (evidence_fanout_node, barrier_breaker_agent, evidence_join_node),
        (evidence_fanout_node, trust_radar_node, evidence_join_node),
        (evidence_fanout_node, access_mapper_node, evidence_join_node),
        (evidence_join_node, merge_evidence_node, rank_resources_node, save_ranking_node),
        (save_ranking_node, plan_weaver_agent, ground_plan_node, save_plan_node),
        (save_plan_node, plan_critic_agent, critique_router_node),
        (
            critique_router_node,
            {
                "REVISE": replanner_agent,
                "READY": request_approval_node,
                "FALLBACK": safe_fallback_review_node,
            },
        ),
        (replanner_agent, ground_plan_node),
        (safe_fallback_review_node, request_approval_node),
        (request_approval_node, approval_router_node),
        (
            approval_router_node,
            {
                "APPROVE": log_gap_event_node,
                "REVISE": user_replanner_agent,
                "CANCEL": render_cancelled_node,
            },
        ),
        (user_replanner_agent, ground_plan_node),
        (log_gap_event_node, render_final_plan_node),
    ],
)

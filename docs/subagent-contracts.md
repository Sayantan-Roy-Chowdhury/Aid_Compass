# Subagent contracts and prompt map

All language-model agents are declared in `aidcompass/subagents/factory.py`. Their full
instructions live in `aidcompass/prompts.py`. `COMMON_BOUNDS` is prepended to every
specialist prompt so safety, privacy, grounding, user control, and schema compliance are
consistent.

| Agent node | Prompt constant | Input | Output | Skills |
|---|---|---|---|---|
| `signal_lens` | `SIGNAL_LENS_PROMPT` | `RequestEnvelope` | `SupportProfile` | `story-to-needs`, `privacy-and-safety` |
| `eligibility_lens` | `ELIGIBILITY_LENS_PROMPT` | `CandidateBundle` | `EligibilityReport` | `eligibility-explainer` |
| `barrier_breaker` | `BARRIER_BREAKER_PROMPT` | `CandidateBundle` | `BarrierReport` | `barrier-busting` |
| `plan_weaver` | `PLAN_WEAVER_PROMPT` | `RankingResult` | `SupportPlan` | `action-plan-weaving`, `warm-handoff`, `trust-and-citations` |
| `plan_critic` | `PLAN_CRITIC_PROMPT` | `SupportPlan` | `PlanCritique` | `trust-and-citations`, `privacy-and-safety`, `action-plan-weaving` |
| `plan_repair` | `REPLANNER_PROMPT` | `PlanReviewBundle` | `SupportPlan` | `action-plan-weaving`, `warm-handoff`, `trust-and-citations` |
| `human_feedback_replanner` | `USER_REPLANNER_PROMPT` | `UserRevisionRequest` | `SupportPlan` | `action-plan-weaving`, `warm-handoff`, `barrier-busting` |

## Shared specialist bounds

Every prompt requires the agent to:

1. use only typed input and loaded skills;
2. never invent an organization or factual resource field;
3. use uncertainty rather than guarantee eligibility;
4. minimize sensitive information;
5. keep the user in control of external actions;
6. return exactly the declared structured-output schema.

## Why the plan agents still cannot change facts

The prompt asks Plan Weaver and replanners to preserve selected records, but prompts are
not treated as a security boundary. `canonical_plan_grounder` runs after every generated
or revised plan, loads `latest_ranking` from state, discards unknown IDs, and restores
exact canonical `RankedResource` values before the critic or renderer sees the plan.

## Deterministic components have no prompts

Boundary Guardian, Resource Scout, Trust Radar, Access Mapper, Matchmaker, Canonical Plan
Grounder, Conservative Fallback Builder, approval routing, Community Pulse, and the final
renderer are ordinary Python functions wrapped as ADK graph nodes. Their behavior is
inspectable and unit-tested without an LLM.

# AidCompass architecture

## 1. Design rule: language judgment at the edges, invariants in code

AidCompass uses LLM nodes for tasks that benefit from semantic judgment: interpreting a
story, cautiously explaining eligibility, identifying access barriers, composing an
action plan, critiquing it, and adapting it to feedback.

Code owns safety routing, exact resource retrieval, distance/freshness calculations,
ranking weights, canonical record restoration, loop caps, human decisions, anonymous
analytics, and final rendering. This split keeps the system creative without allowing an
LLM to become the source of truth.

## 2. Typed graph contracts

Every graph-facing payload is a Pydantic model:

- `RequestEnvelope`
- `SupportProfile`
- `CandidateBundle`
- `EligibilityReport`, `BarrierReport`, `TrustReport`, `AccessReport`
- `EvidenceBundle`
- `RankingResult`
- `SupportPlan`
- `PlanCritique` and `PlanReviewBundle`
- `UserRevisionRequest`

The main payload moves through ADK `Event.output`. State is reserved for values that must
survive an interruption or loop:

- `pending_profile`: profile shown before clarification;
- `latest_ranking`: immutable evidence used by the plan grounder and fallback builder;
- `latest_plan`: plan audited by the critic;
- `pending_plan` and `pending_critique`: content shown at the approval pause;
- `final_plan`: approved result;
- `temp:trace:*`: transient subagent timing measurements.

## 3. Graph phases

### Phase A — boundary and progressive intake

1. `capture_request` normalizes the message.
2. Boundary Guardian applies a deterministic immediate-safety route and PII flags.
3. Signal Lens produces a privacy-minimized profile.
4. The clarification router asks at most two rounds, and only when missing location or
   an absent need prevents useful retrieval.

### Phase B — retrieval and parallel Scout Swarm

1. Resource Scout applies category, age, location/remote, strict requested-mode, cost,
   and keyword matching over the curated JSONL store.
2. A fan-out sends the same `CandidateBundle` to:
   - Eligibility Lens;
   - Barrier Breaker;
   - Trust Radar;
   - Access Mapper;
   - candidate passthrough.
3. `JoinNode` waits for all five branches and `merge_evidence` validates the joined map.

### Phase C — explainable ranking and evidence lock

Matchmaker computes:

```text
35% need/category match
20% eligibility estimate
17% barrier fit
15% source trust
13% access fit
```

The exact `RankingResult` is stored as `latest_ranking`. This creates an evidence lock:
subsequent LLM nodes can select and explain known records, but they cannot become the
canonical source for resource facts.

### Phase D — plan, grounding, critic, repair

1. Plan Weaver creates a typed `SupportPlan`.
2. Canonical Plan Grounder removes unknown IDs, restores exact `RankedResource` objects,
   drops outreach drafts for unknown resources, restores requested need/barrier taxonomy,
   and makes Plan B use a separate record when possible.
3. Plan Critic audits grounding, uncertainty, privacy, and actionability.
4. A `REVISE` route invokes Plan Repair and returns through the grounder.
5. The loop is capped at two automatic revisions.
6. If the plan still fails, the deterministic Conservative Fallback Builder creates a
   minimal source-checked Plan A/Plan B and forwards it to human review.

### Phase E — resumable human control

`RequestInput` pauses at the Human Navigator Gate. The resumed input routes to:

- `APPROVE`: anonymous gap event, then deterministic final rendering;
- `CANCEL`: terminal no-action response;
- free-form change: Human-Feedback Replanner, then grounder and critic again.

No organization is contacted and no enrollment action occurs.

## 4. Skill architecture

Each skill is a progressive-disclosure package:

```text
skill-name/
├── SKILL.md
├── references/
├── assets/
└── scripts/
```

`SKILL.md` is concise and procedural. References contain deeper guidance, assets contain
machine-readable rubrics/taxonomies/templates, and scripts contain small deterministic
helpers. Subagents receive only the relevant skill packages.

## 5. Reliability and observability

- LLM agents use `mode="single_turn"` with narrow input and output schemas.
- Model and I/O nodes have retry/timeout policies.
- Branch outputs are validated at the fan-in boundary.
- Canonical grounding happens after every generated or revised plan.
- Critic loops are finite and have a deterministic fallback.
- Analytics failure is non-critical and never blocks the user response.
- Callbacks record temporary elapsed time by subagent.
- The final renderer is deterministic.

## 6. Privacy boundary

Normal matching uses city/neighborhood and broad age band rather than an exact address or
birth date. Community Pulse stores only:

- need category;
- barrier category;
- unmet category;
- resource IDs offered;
- demo-data flag;
- timestamp.

It excludes raw messages, summaries, names, email, phone, exact address, health/legal
narratives, and outreach drafts.

## 7. Production extensions

1. Replace synthetic JSONL with official municipal/nonprofit ingestion.
2. Add scheduled source freshness checks and dead-link monitoring.
3. Add geocoding only behind user consent; avoid retaining exact addresses.
4. Add an administrator queue for low-confidence or stale records.
5. Use a persistent ADK session service and encrypted analytics store.
6. Add language-specific review and accessibility testing.
7. Add minimum-count thresholds before displaying community-gap analytics.

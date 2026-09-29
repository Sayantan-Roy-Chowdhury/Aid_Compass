# Vibe-coding playbook used in AidCompass

This project applies a trace-first, evaluation-first approach rather than starting with
one giant system prompt.

## 1. Start with a cinematic vertical slice

The primary demo is deliberately specific: a teen in Scarborough needs math and food
support, has evening/document/contact constraints, then changes the request to online
only. Every system component supports that one end-to-end story before adding breadth.

## 2. Make the graph visible

A competition viewer should be able to see why this is an agentic system. Node names are
human-readable, parallel Scout Swarm branches are explicit, repair/replanning loops are
visible, and the approval pause produces a clear live-demo moment.

## 3. Use agents for judgment, code for truth

Semantic interpretation and writing go to small LLM agents. Resource identity, filters,
scoring, state, routing, grounding, analytics, and final rendering remain deterministic.
This is easier to debug and easier to explain to judges.

## 4. Give every subagent one job and a typed contract

Each LLM node is single-turn, has a narrow input/output schema, loads only relevant
skills, and has explicit forbidden behaviors. The result is more testable than a large
multi-purpose assistant prompt.

## 5. Progressive disclosure beats prompt stuffing

Skills place short discovery metadata first, procedures second, and deep references,
assets, and scripts third. A specialist loads only what the current task requires.

## 6. Design the failure path before polishing the happy path

AidCompass has routes for immediate safety, missing information, no results, critic
failure, repair exhaustion, user cancellation, analytics write failure, and user-requested
replanning. The deterministic fallback prevents an endless self-critique loop.

## 7. Lock factual evidence after retrieval

The Canonical Plan Grounder is an architectural invariant. Generated prose can change;
organization records cannot. Unknown IDs and drafts are discarded, and selected records
are restored from the saved ranking.

## 8. Put the user at the action boundary

The system may recommend and draft, but it does not contact, enroll, or share data.
`RequestInput` creates a memorable approval/replanning step and demonstrates real human
control.

## 9. Build synthetic fixtures before live integrations

Eighteen synthetic resources make the whole graph reproducible and safe to test. The
resource schema is the integration boundary for later official data ingestion.

## 10. Evaluate behavior, not just final wording

The test suite checks graph shape, resource filtering, ranking, safety routing, skills,
canonical restoration, loop fallback, and eval schemas. Multi-turn scenarios evaluate
clarification, grounding, eligibility uncertainty, human control, and replanning.

## 11. Optimize the demo for one clear transformation

The pitch is not “an AI directory.” It is:

> A messy human story becomes a verified, explainable, adaptable support journey—with a
> backup plan and a community-gap signal—without surrendering control to the model.

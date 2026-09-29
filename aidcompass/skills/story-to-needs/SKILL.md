---
name: story-to-needs
description: Use when a user describes a messy situation and the agent must map it to community-support needs with minimal clarification.
license: Apache-2.0
compatibility: Google ADK Python 2.x
metadata:
  adk_inject_state: false
---

# Story to Needs

## Goal

Convert ordinary language into a compact support profile without forcing the user to
know service-category terms.

## Procedure

1. Read `references/need-taxonomy.md` when category distinctions are unclear.
2. Separate independent needs; do not collapse food, education, housing, or access into one label.
3. For each need, record a neutral statement, urgency, priority, confidence, and search keywords.
4. Extract practical barriers and strengths only when the user states or strongly implies them.
5. Ask at most two questions. Ask only for information that changes retrieval.
6. Prefer city/neighborhood over exact address. Mark optional details as optional.
7. Run `scripts/validate_need_map.py` conceptually against the finished mapping.

## Quality bar

A good mapping is complete enough for search, short enough to review, and does not
repeat sensitive details. Never diagnose a user or guess a protected status.


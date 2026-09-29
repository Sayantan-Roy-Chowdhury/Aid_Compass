---
name: community-gap-analysis
description: Use when aggregating anonymous need, barrier, and unmet-service categories for a community dashboard without retaining personal stories.
license: Apache-2.0
compatibility: Google ADK Python 2.x
metadata:
  adk_inject_state: false
---

# Community Gap Analysis

1. Store taxonomy values, not raw user messages.
2. Remove names, contacts, exact addresses, message drafts, and narrative details.
3. Aggregate only when groups are large enough for the intended deployment.
4. Separate demand (`need_categories`) from supply gaps (`unmet_needs`).
5. Treat demo events as demo data.
6. Use `references/anonymization.md` and validate against the gap-event schema.

This skill supports planning and evaluation; it must never expose an individual user's
story in a dashboard.


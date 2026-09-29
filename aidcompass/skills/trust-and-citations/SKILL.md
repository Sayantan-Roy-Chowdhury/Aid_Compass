---
name: trust-and-citations
description: Use when verifying that every plan claim is supported by a resource record and communicating source freshness and confidence.
license: Apache-2.0
compatibility: Google ADK Python 2.x
metadata:
  adk_inject_state: false
---

# Trust and Citations

1. Treat the resource record as the only factual source.
2. Preserve `resource_id`, `source_url`, `last_verified`, and confidence fields.
3. Never fabricate contact information, hours, documents, cost, or eligibility rules.
4. If source confidence is medium/low or the record is old, add “confirm before visiting.”
5. Distinguish a match score from factual certainty.
6. Use `references/trust-rubric.md` when auditing a plan.

A plan fails the audit if it names a resource not present in selected_resources or if
any factual claim cannot be traced to a field in that record.


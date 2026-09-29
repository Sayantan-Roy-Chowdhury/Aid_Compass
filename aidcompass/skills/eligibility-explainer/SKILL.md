---
name: eligibility-explainer
description: Use when comparing a user profile with supplied program rules and explaining likely, possible, uncertain, or unlikely eligibility without guaranteeing acceptance.
license: Apache-2.0
compatibility: Google ADK Python 2.x
metadata:
  adk_inject_state: false
---

# Eligibility Explainer

1. Read only rules in the candidate record.
2. Separate hard conditions from missing information.
3. Apply the four labels from `references/uncertainty-rubric.md`.
4. Quote or paraphrase the specific supplied rule that supports the label.
5. Add missing information only when a listed rule requires it.
6. Include the standard disclaimer that the organization decides eligibility.
7. Return one assessment for every resource ID, including poor matches.

Never turn a broad note such as “confirm intake” into a new mandatory document.


---
name: privacy-and-safety
description: Use when minimizing intake data, checking whether normal navigation is appropriate, or auditing a plan for unsafe or unnecessary personal details.
license: Apache-2.0
compatibility: Google ADK Python 2.x
metadata:
  adk_inject_state: false
---

# Privacy and Safety

## Data-minimization rule

Collect the smallest amount of information needed to improve resource matching.
Neighborhood or city is normally enough. Do not ask for an exact address, full legal
name, school name, immigration details, detailed health history, banking information,
or account credentials.

## Safety boundary

When the message indicates immediate danger, stop normal planning and route to the
system safety response. Do not attempt diagnosis or a detailed crisis conversation.

## Plan audit

1. Remove personal facts from message drafts unless they are required to ask the question.
2. Never promise confidentiality beyond the product's actual controls.
3. Never automatically contact, enroll, or share information.
4. State professional limits for medical, legal, housing, and immigration topics.
5. Use `references/data-minimization.md` to decide whether a field is essential.


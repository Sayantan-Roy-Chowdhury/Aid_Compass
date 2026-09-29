# Three-minute competition demo

## 0:00–0:20 — Problem

“Most directories assume people know the exact service category and can interpret
eligibility rules. AidCompass is a no-wrong-door navigator: tell it the situation in
normal language and it builds a grounded, adaptable support journey.”

## 0:20–1:10 — Main scenario

Enter:

> I’m 16 in Scarborough. I need free math help and food support this week. I can
> only travel after 5 PM, I may not have photo ID, and I would rather email than call.

Show the graph trace:

1. Signal Lens identifies two needs and three barriers.
2. Resource Scout searches only the curated store.
3. Eligibility Lens, Barrier Breaker, Trust Radar, and Access Mapper run in parallel.
4. Matchmaker displays explainable scores.
5. Plan Weaver creates a first step, Plan A, Plan B, and outreach draft.
6. Plan Critic checks grounding and can automatically repair the plan.

## 1:10–2:10 — Replanning wow moment

At the approval gate, enter:

> Make it online-only and avoid phone calls.

Show that the graph loops to the human-feedback replanner, runs the critic again, and
returns to approval. The new plan should favor StudyNow Online Tutoring Room and use
email drafts rather than phone scripts.

## 2:10–2:40 — Human control

Reply `APPROVE`. Emphasize that AidCompass does not contact or enroll the user. The
final renderer copies only facts present in the resource records and exposes source
links and confidence notes.

## 2:40–3:00 — Community impact

Run:

```bash
python scripts/build_gap_report.py
```

Explain that Community Pulse stores only anonymous category-level gaps, helping local
organizations see unmet needs without retaining personal stories.

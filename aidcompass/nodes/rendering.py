"""User-facing renderers. No LLM is used here, so claims remain grounded."""

from __future__ import annotations

from google.adk import Event

from ..schemas import CandidateBundle, SupportPlan


def _resource_line(index: int, item) -> str:
    resource = item.resource
    source = resource.source_url
    reasons = "; ".join(item.why_match[:3]) or "Matches the requested support category"
    cautions = "; ".join(item.watch_outs[:2])
    caution_line = f"\n   - Check first: {cautions}" if cautions else ""
    return (
        f"{index}. **{resource.name}** — match {round(item.total_score * 100)}%\n"
        f"   - Why: {reasons}\n"
        f"   - Access: {', '.join(resource.delivery_modes)}; cost: {resource.cost}\n"
        f"   - Eligibility estimate: {item.eligibility_label}; source confidence: {item.confidence_label}"
        f"{caution_line}\n"
        f"   - Source: {source}"
    )


def render_final_plan(node_input: SupportPlan) -> Event:
    lines = [
        f"# {node_input.headline}",
        "",
        "## Best first step",
        f"**{node_input.best_first_step.action}**",
        node_input.best_first_step.reason,
        "",
        "## Best matches",
    ]
    for index, item in enumerate(node_input.selected_resources, start=1):
        lines.append(_resource_line(index, item))
    lines.extend(
        [
            "",
            "## Plan A",
            node_input.plan_a.purpose,
        ]
    )
    for step in node_input.plan_a.steps:
        lines.append(f"{step.order}. {step.action} — {step.reason}")
    lines.extend(["", "## Plan B", node_input.plan_b.purpose])
    for step in node_input.plan_b.steps:
        lines.append(f"{step.order}. {step.action} — {step.reason}")

    if node_input.document_backpack:
        lines.extend(["", "## Document backpack"])
        lines.extend(f"- {item}" for item in node_input.document_backpack)
    if node_input.contact_drafts:
        lines.extend(["", "## Ready-to-copy outreach"])
        for draft in node_input.contact_drafts:
            lines.append(f"### {draft.channel.replace('_', ' ').title()} — {draft.resource_id}")
            if draft.subject:
                lines.append(f"Subject: {draft.subject}")
            lines.append(draft.body)
    if node_input.confidence_notes:
        lines.extend(["", "## Confidence and limits"])
        lines.extend(f"- {note}" for note in node_input.confidence_notes)

    lines.extend(["", f"> {node_input.demo_data_notice}"])
    return Event(
        message="\n".join(lines),
        output=node_input.model_dump(mode="json"),
        state={"final_plan": node_input.model_dump(mode="json")},
    )


def render_no_results(node_input: CandidateBundle) -> Event:
    categories = ", ".join(need.category.value for need in node_input.profile.needs)
    message = (
        "I could not find a verified match in the current demo dataset for "
        f"{categories or 'the request'}. Try a broader neighborhood, allow online options, "
        "or add official local resources to `aidcompass/data/resources.sample.jsonl`. "
        "I did not invent an organization to fill the gap."
    )
    return Event(
        message=message, output={"status": "no_results", "search_trace": node_input.search_trace}
    )

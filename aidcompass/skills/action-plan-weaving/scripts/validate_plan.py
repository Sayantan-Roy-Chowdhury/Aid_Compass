def validate(plan: dict) -> list[str]:
    errors = []
    if not plan.get("best_first_step"):
        errors.append("missing best_first_step")
    if plan.get("plan_a", {}).get("resource_ids") == plan.get("plan_b", {}).get("resource_ids"):
        errors.append("Plan B must differ from Plan A")
    if len(plan.get("contact_drafts", [])) > 3:
        errors.append("too many contact drafts")
    return errors

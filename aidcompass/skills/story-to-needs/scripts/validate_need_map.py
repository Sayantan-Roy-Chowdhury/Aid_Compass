REQUIRED_FIELDS = {"category", "statement", "urgency", "priority", "confidence", "keywords"}


def validate(items: list[dict]) -> list[str]:
    errors = []
    for index, item in enumerate(items):
        missing = REQUIRED_FIELDS - set(item)
        if missing:
            errors.append(f"need[{index}] missing {sorted(missing)}")
        if not 1 <= int(item.get("priority", 0)) <= 5:
            errors.append(f"need[{index}] priority must be 1..5")
    return errors

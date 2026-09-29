from collections import Counter


def aggregate(events: list[dict]) -> dict:
    return {
        "needs": dict(
            Counter(item for event in events for item in event.get("need_categories", []))
        ),
        "barriers": dict(
            Counter(item for event in events for item in event.get("barrier_types", []))
        ),
        "unmet": dict(Counter(item for event in events for item in event.get("unmet_needs", []))),
    }

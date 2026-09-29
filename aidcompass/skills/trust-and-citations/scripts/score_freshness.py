from datetime import date


def score(last_verified: date, today: date | None = None) -> float:
    days = ((today or date.today()) - last_verified).days
    if days <= 30:
        return 1.0
    if days <= 90:
        return 0.85
    if days <= 180:
        return 0.65
    if days <= 365:
        return 0.4
    return 0.2

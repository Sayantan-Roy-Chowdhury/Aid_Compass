"""Deterministic scoring helpers."""

from __future__ import annotations

from datetime import date
from math import asin, cos, radians, sin, sqrt


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0088
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return earth_radius_km * 2 * asin(sqrt(a))


def freshness_score(last_verified: date, today: date | None = None) -> tuple[float, int]:
    today = today or date.today()
    age_days = max(0, (today - last_verified).days)
    if age_days <= 30:
        return 1.0, age_days
    if age_days <= 90:
        return 0.85, age_days
    if age_days <= 180:
        return 0.65, age_days
    if age_days <= 365:
        return 0.4, age_days
    return 0.2, age_days

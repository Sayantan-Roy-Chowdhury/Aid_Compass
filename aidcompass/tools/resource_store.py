"""Verified-resource retrieval over a local JSONL store.

The shipped dataset is synthetic. Replace the JSONL file with records ingested from
official local sources before production use.
"""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import re

from ..config import get_settings
from ..schemas import AgeBand, NeedCategory, ResourceCandidate, ResourceRecord, SupportProfile
from .scoring import clamp


_TOKEN_RE = re.compile(r"[a-z0-9]+")


CATEGORY_EXPANSIONS: dict[NeedCategory, set[str]] = {
    NeedCategory.FOOD_SUPPORT: {"food", "meal", "grocery", "pantry", "fridge"},
    NeedCategory.EDUCATION_SUPPORT: {"tutoring", "homework", "math", "study", "school"},
    NeedCategory.YOUTH_PROGRAMS: {"youth", "after school", "mentor", "recreation", "drop in"},
    NeedCategory.EMPLOYMENT_SUPPORT: {"job", "resume", "interview", "employment", "career"},
    NeedCategory.HEALTH_WELLNESS: {"wellness", "counselling", "clinic", "health", "support"},
    NeedCategory.HOUSING_NAVIGATION: {"housing", "shelter", "tenant", "rent", "navigation"},
    NeedCategory.LEGAL_INFORMATION: {"legal", "rights", "information", "clinic"},
    NeedCategory.NEWCOMER_SUPPORT: {"newcomer", "settlement", "language", "orientation"},
    NeedCategory.TRANSPORTATION_SUPPORT: {"transit", "transportation", "fare", "ride"},
    NeedCategory.DIGITAL_ACCESS: {"internet", "computer", "device", "wifi", "digital"},
    NeedCategory.FAMILY_SUPPORT: {"family", "parent", "caregiver", "childcare"},
    NeedCategory.DISABILITY_SUPPORT: {"accessibility", "disability", "accommodation"},
    NeedCategory.OTHER: set(),
}


AGE_BAND_RANGES: dict[AgeBand, tuple[int | None, int | None]] = {
    AgeBand.UNDER_13: (0, 12),
    AgeBand.AGE_13_17: (13, 17),
    AgeBand.AGE_18_24: (18, 24),
    AgeBand.ADULT_25_PLUS: (25, None),
    AgeBand.UNKNOWN: (None, None),
}


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _resource_text(resource: ResourceRecord) -> str:
    return " ".join(
        [resource.name, resource.description, *resource.keywords, *resource.service_areas]
    )


def _age_compatible(profile: SupportProfile, resource: ResourceRecord) -> tuple[bool, str | None]:
    low, high = AGE_BAND_RANGES[profile.age_band]
    if low is None and high is None:
        return True, "Age was not supplied; confirm age requirements."
    if resource.max_age is not None and low is not None and low > resource.max_age:
        return False, "The stated age band is above this program's maximum age."
    if resource.min_age is not None and high is not None and high < resource.min_age:
        return False, "The stated age band is below this program's minimum age."
    return True, None


class ResourceStore:
    def __init__(self, resources_path: Path | None = None, locations_path: Path | None = None):
        settings = get_settings()
        self.resources_path = resources_path or settings.resources_path
        self.locations_path = locations_path or settings.locations_path
        self._resources = self._load_resources(self.resources_path)
        self._locations = self._load_locations(self.locations_path)

    @staticmethod
    @lru_cache(maxsize=8)
    def _load_resources(path: Path) -> tuple[ResourceRecord, ...]:
        records: list[ResourceRecord] = []
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    records.append(ResourceRecord.model_validate_json(line))
                except Exception as exc:
                    raise ValueError(f"Invalid resource at {path}:{line_number}: {exc}") from exc
        return tuple(records)

    @staticmethod
    @lru_cache(maxsize=8)
    def _load_locations(path: Path) -> dict[str, dict]:
        data = json.loads(path.read_text(encoding="utf-8"))
        index: dict[str, dict] = {}
        for item in data:
            for alias in [item["name"], *item.get("aliases", [])]:
                index[alias.lower()] = item
        return index

    @property
    def resources(self) -> tuple[ResourceRecord, ...]:
        return self._resources

    def normalize_location(self, text: str | None) -> tuple[str | None, float | None, float | None]:
        if not text:
            return None, None, None
        lower = text.strip().lower()
        if lower in self._locations:
            item = self._locations[lower]
            return item["name"], item["latitude"], item["longitude"]
        for alias, item in self._locations.items():
            if alias in lower or lower in alias:
                return item["name"], item["latitude"], item["longitude"]
        return text.strip(), None, None

    def search(
        self, profile: SupportProfile, max_candidates: int = 12
    ) -> tuple[list[ResourceCandidate], list[str], str | None, float | None, float | None]:
        normalized_location, origin_lat, origin_lon = self.normalize_location(profile.location_text)
        need_categories = {need.category for need in profile.needs}
        query_terms: set[str] = set()
        for need in profile.needs:
            query_terms.update(_tokens(need.statement))
            query_terms.update(_tokens(" ".join(need.keywords)))
            query_terms.update(_tokens(" ".join(CATEGORY_EXPANSIONS.get(need.category, set()))))

        trace = [
            f"Need categories: {', '.join(sorted(category.value for category in need_categories)) or 'none'}",
            f"Expanded query terms: {', '.join(sorted(query_terms)) or 'none'}",
            f"Location filter: {normalized_location or 'online/unspecified'}",
        ]

        candidates: list[ResourceCandidate] = []
        for resource in self._resources:
            category_overlap = need_categories.intersection(resource.categories)
            if need_categories and not category_overlap:
                continue

            compatible, age_note = _age_compatible(profile, resource)
            if not compatible:
                continue

            location_fit = False
            if normalized_location:
                location_lower = normalized_location.lower()
                location_fit = any(
                    location_lower in area.lower()
                    or area.lower() in location_lower
                    or "toronto-wide" in area.lower()
                    for area in resource.service_areas
                )
            resource_modes = set(resource.delivery_modes)
            requested_modes = set(profile.preferences.delivery_modes)
            any_remote_fit = bool({"online", "phone"}.intersection(resource_modes))
            requested_remote_fit = bool(
                requested_modes.intersection({"online", "phone"}).intersection(resource_modes)
            )
            remote_fit = requested_remote_fit if requested_modes else any_remote_fit
            if normalized_location and not location_fit and not remote_fit:
                continue
            if requested_modes and not requested_modes.intersection(resource_modes):
                continue
            if profile.preferences.online_only and "online" not in resource_modes:
                continue
            if profile.preferences.free_only and resource.cost not in {"free", "unknown"}:
                continue

            resource_terms = _tokens(_resource_text(resource))
            keyword_overlap = len(query_terms.intersection(resource_terms))
            keyword_score = min(1.0, keyword_overlap / max(3, len(query_terms) or 1))
            category_score = len(category_overlap) / max(1, len(need_categories))
            location_score = 1.0 if location_fit else 0.65 if remote_fit else 0.3
            cost_score = 1.0 if resource.cost == "free" else 0.65
            mode_score = 0.5
            if requested_modes:
                mode_score = len(requested_modes.intersection(resource_modes)) / len(
                    requested_modes
                )
            elif resource.delivery_modes:
                mode_score = 0.8

            score = clamp(
                0.48 * category_score
                + 0.17 * keyword_score
                + 0.15 * location_score
                + 0.10 * cost_score
                + 0.10 * mode_score
            )
            reasons = []
            if category_overlap:
                reasons.append(
                    "Matches " + ", ".join(sorted(category.value for category in category_overlap))
                )
            if location_fit:
                reasons.append(f"Serves {normalized_location}")
            elif remote_fit:
                reasons.append("Offers a requested remote access mode")
            if resource.cost == "free":
                reasons.append("Listed as free")
            if profile.preferences.languages and set(profile.preferences.languages).intersection(
                resource.languages
            ):
                reasons.append("Language match")

            notes = [age_note] if age_note else []
            candidates.append(
                ResourceCandidate(
                    resource=resource,
                    base_match_score=round(score, 4),
                    match_reasons=reasons,
                    hard_filter_notes=notes,
                )
            )

        candidates.sort(key=lambda item: item.base_match_score, reverse=True)
        selected = candidates[:max_candidates]
        trace.append(f"Selected {len(selected)} of {len(candidates)} matching records.")
        return selected, trace, normalized_location, origin_lat, origin_lon

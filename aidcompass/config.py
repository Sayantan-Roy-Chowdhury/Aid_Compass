"""Runtime configuration for AidCompass."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    model: str
    demo_mode: bool
    max_candidates: int
    resources_path: Path
    locations_path: Path
    analytics_path: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    runtime_dir = PACKAGE_ROOT / "data" / "runtime"
    return Settings(
        model=os.getenv("AIDCOMPASS_MODEL", "gemini-3.5-flash"),
        demo_mode=_env_bool("AIDCOMPASS_DEMO_MODE", True),
        max_candidates=max(3, int(os.getenv("AIDCOMPASS_MAX_CANDIDATES", "12"))),
        resources_path=PACKAGE_ROOT / "data" / "resources.sample.jsonl",
        locations_path=PACKAGE_ROOT / "data" / "locations.json",
        analytics_path=runtime_dir / "gap_events.jsonl",
    )

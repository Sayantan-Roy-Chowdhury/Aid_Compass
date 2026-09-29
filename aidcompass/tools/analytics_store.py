"""Privacy-minimized community gap logging."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from ..config import get_settings
from ..schemas import GapEvent


class AnalyticsStore:
    def __init__(self, path: Path | None = None):
        self.path = path or get_settings().analytics_path

    def append(self, event: GapEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(event.model_dump_json() + "\n")

    def summary(self) -> dict[str, Any]:
        needs: Counter[str] = Counter()
        barriers: Counter[str] = Counter()
        unmet: Counter[str] = Counter()
        total = 0
        if not self.path.exists():
            return {"events": 0, "needs": {}, "barriers": {}, "unmet": {}}
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                event = GapEvent.model_validate_json(line)
                total += 1
                needs.update(item.value for item in event.need_categories)
                barriers.update(item.value for item in event.barrier_types)
                unmet.update(item.value for item in event.unmet_needs)
        return {
            "events": total,
            "needs": dict(needs.most_common()),
            "barriers": dict(barriers.most_common()),
            "unmet": dict(unmet.most_common()),
        }

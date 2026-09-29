"""Community Pulse: anonymized gap analytics."""

from __future__ import annotations

import logging

from ..schemas import GapEvent, SupportPlan
from ..tools.analytics_store import AnalyticsStore


logger = logging.getLogger(__name__)
_STORE = AnalyticsStore()


def log_gap_event(node_input: SupportPlan) -> SupportPlan:
    needs = sorted(set(node_input.requested_needs), key=lambda item: item.value)
    barriers = sorted(set(node_input.barrier_types), key=lambda item: item.value)
    # The final plan intentionally contains no raw user story. The event stores only taxonomy values.
    event = GapEvent(
        need_categories=needs,
        barrier_types=barriers,
        unmet_needs=node_input.unmet_needs,
        resource_ids_offered=[item.resource.resource_id for item in node_input.selected_resources],
        demo_data=all(item.resource.is_demo for item in node_input.selected_resources),
    )
    try:
        _STORE.append(event)
    except OSError as exc:
        logger.warning("Gap analytics write skipped: %s", exc)
    return node_input

from __future__ import annotations

import json

from aidcompass.tools.analytics_store import AnalyticsStore


if __name__ == "__main__":
    print(json.dumps(AnalyticsStore().summary(), indent=2))

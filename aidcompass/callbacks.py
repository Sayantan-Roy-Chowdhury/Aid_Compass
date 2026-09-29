"""Lightweight observability callbacks for LLM subagents."""

from __future__ import annotations

import time
from typing import Any


def _agent_name(ctx: Any) -> str:
    return str(
        getattr(ctx, "agent_name", None) or getattr(getattr(ctx, "node", None), "name", "agent")
    )


async def before_agent_trace(ctx: Any) -> None:
    name = _agent_name(ctx)
    ctx.state[f"temp:trace:{name}:started_at"] = time.time()


async def after_agent_trace(ctx: Any) -> None:
    name = _agent_name(ctx)
    key = f"temp:trace:{name}:started_at"
    started = ctx.state.get(key)
    if isinstance(started, (int, float)):
        ctx.state[f"temp:trace:{name}:elapsed_ms"] = round((time.time() - started) * 1000, 2)

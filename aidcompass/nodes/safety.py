"""Boundary Guardian: deterministic privacy and immediate-safety routing."""

from __future__ import annotations

import re

from google.adk import Event

from ..schemas import RequestEnvelope


_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}")
_URGENT_PHRASES = {
    "immediate danger",
    "medical emergency",
    "violence happening now",
    "someone is not safe right now",
    "call an ambulance",
    "need police now",
}


def capture_request(node_input: str) -> RequestEnvelope:
    """Normalize the initial user message into a typed envelope."""
    message = " ".join(str(node_input).strip().split())
    if not message:
        message = "I need help finding community support."
    return RequestEnvelope(message=message[:6000])


def privacy_safety_gate(node_input: RequestEnvelope) -> Event:
    """Route urgent danger away from normal resource planning and flag excess PII."""
    lower = node_input.message.lower()
    urgent = any(phrase in lower for phrase in _URGENT_PHRASES)
    pii_flags = []
    if _EMAIL_RE.search(node_input.message):
        pii_flags.append("email_address")
    if _PHONE_RE.search(node_input.message):
        pii_flags.append("phone_number")
    route = "SAFETY" if urgent else "CONTINUE"
    return Event(
        route=route,
        output=node_input.model_dump(mode="json"),
        state={"temp:pii_flags": pii_flags, "temp:safety_route": route},
    )


def render_safety_response(node_input: RequestEnvelope) -> Event:
    """Return a general immediate-safety response without attempting normal navigation."""
    message = (
        "Your message may involve immediate danger. AidCompass is not an emergency service. "
        "Please contact local emergency services or a trusted adult nearby now. Once immediate "
        "safety is handled, AidCompass can help organize community-resource options."
    )
    return Event(message=message, output={"status": "safety_redirect"})

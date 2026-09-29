"""ADK loader entrypoint."""

from google.adk.apps import App, ResumabilityConfig

from .graph import root_agent


app = App(
    name="aidcompass",
    root_agent=root_agent,
    resumability_config=ResumabilityConfig(is_resumable=True),
)

__all__ = ["app", "root_agent"]

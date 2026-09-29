from google.adk import Workflow

from aidcompass.agent import app, root_agent


def test_root_is_resumable_graph_workflow():
    assert isinstance(root_agent, Workflow)
    assert root_agent.name == "aidcompass"
    assert app.resumability_config is not None
    assert app.resumability_config.is_resumable is True
    assert len(root_agent.edges) >= 15

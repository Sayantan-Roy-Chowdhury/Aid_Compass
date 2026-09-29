from __future__ import annotations

from pathlib import Path

from google.adk import Workflow
from google.adk.evaluation.conversation_scenarios import ConversationScenarios
from google.adk.evaluation.eval_config import EvalConfig
from google.adk.evaluation.eval_set import EvalSet

from aidcompass.graph import root_agent
from aidcompass.skill_loader import available_skill_names, load_skill
from aidcompass.tools.resource_store import ResourceStore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVAL_ROOT = PROJECT_ROOT / "aidcompass" / "evals"


def main() -> None:
    assert isinstance(root_agent, Workflow)
    assert len(root_agent.edges) >= 18

    skills = available_skill_names()
    assert skills, "No skills found"
    for name in skills:
        skill = load_skill(name)
        assert skill.name == name
        assert skill.description.strip()
        assert skill.instructions.strip()
        assert skill.resources.references
        assert skill.resources.assets
        assert skill.resources.scripts

    store = ResourceStore()
    assert len(store.resources) >= 10
    assert all(record.source_url for record in store.resources)
    assert all(record.last_verified for record in store.resources)

    scenarios = ConversationScenarios.model_validate_json(
        (EVAL_ROOT / "conversation_scenarios.json").read_text(encoding="utf-8")
    )
    eval_config = EvalConfig.model_validate_json(
        (EVAL_ROOT / "eval_config.json").read_text(encoding="utf-8")
    )
    eval_set = EvalSet.model_validate_json(
        (EVAL_ROOT / "aidcompass.evalset.json").read_text(encoding="utf-8")
    )
    assert scenarios.scenarios
    assert eval_config.criteria
    assert eval_set.eval_cases

    print(f"Workflow: {root_agent.name} ({len(root_agent.edges)} edge declarations)")
    print(f"Skills loaded: {len(skills)} -> {', '.join(skills)}")
    print(f"Resource records validated: {len(store.resources)}")
    print(f"Conversation scenarios validated: {len(scenarios.scenarios)}")
    print(f"ADK eval cases validated: {len(eval_set.eval_cases)}")
    print("AidCompass project validation passed.")


if __name__ == "__main__":
    main()

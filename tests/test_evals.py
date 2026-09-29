from pathlib import Path

from google.adk.evaluation.conversation_scenarios import ConversationScenarios
from google.adk.evaluation.eval_config import EvalConfig
from google.adk.evaluation.eval_set import EvalSet


EVAL_ROOT = Path(__file__).resolve().parents[1] / "aidcompass" / "evals"


def test_adk_eval_artifacts_validate():
    scenarios = ConversationScenarios.model_validate_json(
        (EVAL_ROOT / "conversation_scenarios.json").read_text(encoding="utf-8")
    )
    config = EvalConfig.model_validate_json(
        (EVAL_ROOT / "eval_config.json").read_text(encoding="utf-8")
    )
    eval_set = EvalSet.model_validate_json(
        (EVAL_ROOT / "aidcompass.evalset.json").read_text(encoding="utf-8")
    )

    assert len(scenarios.scenarios) >= 5
    assert "hallucinations_v1" in config.criteria
    assert config.user_simulator_config is not None
    assert len(eval_set.eval_cases) >= 5

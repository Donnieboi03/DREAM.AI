"""E2E test: user input -> Orchestrator LLM -> Scene generator LLM -> apply_edits -> house -> ThorEnv -> reset + steps.

Skips when GEMINI_API_KEY or GOOGLE_API_KEY is not set. Mark as integration/slow.
"""

import os
import sys
from pathlib import Path

import pytest

# Repo root and src/demos on path (src package + ThorEnv's "from tools.actions import ...")
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEMOS_DIR = REPO_ROOT / "src" / "demos"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(DEMOS_DIR) not in sys.path:
    sys.path.insert(0, str(DEMOS_DIR))

PROCTHOR_10K_REVISION = "ab3cacd0fc17754d4c080a3fd50b18395fae8647"


def _get_api_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


@pytest.mark.skipif(not _get_api_key(), reason="GEMINI_API_KEY or GOOGLE_API_KEY not set")
@pytest.mark.slow
def test_llm_house_e2e_user_input_to_simulation():
    """Run full pipeline: user input -> LLMs -> edited house -> Controller -> ThorEnv -> reset + 5 steps."""
    from ai2thor.controller import Controller
    from src.backend.llm import run_full_pipeline
    from src.backend.orchestrator import get_house_summary, apply_edits
    from src.envs.ai2thor.thor_env import ThorEnv

    def get_base_house():
        import prior
        dataset = prior.load_dataset("procthor-10k", revision=PROCTHOR_10K_REVISION)
        return dataset["train"][0]

    user_input = "I want a small kitchen and living room for navigation"
    base_house = get_base_house()
    house_summary = get_house_summary(base_house)

    declarative, scene_response = run_full_pipeline(user_input, house_summary)
    edited_house = apply_edits(base_house, scene_response.house_edit_request)

    init_params = dict(
        agentMode="default",
        visibilityDistance=1.5,
        width=400,
        height=300,
        fullscreen=False,
        snapToGrid=True,
        gridSize=0.25,
        rotateStepDegrees=90.0,
    )
    init_params["scene"] = "Procedural" if isinstance(edited_house, dict) else edited_house
    controller = Controller(**init_params)
    if isinstance(edited_house, dict):
        event = controller.step(
            action="CreateHouse", house=edited_house, renderImage=False
        )
        assert event, "CreateHouse failed"
        agent_meta = (edited_house.get("metadata") or {}).get("agent")
        if agent_meta:
            controller.step(action="TeleportFull", **agent_meta, renderImage=False)
    env = ThorEnv(controller=controller, width=400, height=300)
    try:
        obs, info = env.reset()
        assert obs is not None
        steps_done = 0
        for _ in range(5):
            obs, reward, term, trunc, info = env.step(0)
            assert obs is not None
            steps_done += 1
            if term or trunc:
                break
        assert steps_done >= 1
    finally:
        env.close()

#!/usr/bin/env python3
"""Example: start AI2-THOR with a ProcTHOR-generated scene and run a few steps.

Run from the repo root (DREAM.AI) with:

    PYTHONPATH=. python dreamai/scripts/run_example_thor.py

Or from the dreamai directory:

    PYTHONPATH=.. python scripts/run_example_thor.py

Requires: pip install -r dreamai/requirements.txt

If ProcTHOR fails (e.g. "Unable to CreateHouse!" on some setups), the script
falls back to a built-in iTHOR scene (FloorPlan1) so the demo still runs.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

# Suppress AI2-THOR warning when the requested Unity build isn't available for this OS
# (e.g. macOS ARM); the controller falls back to an older build automatically.
warnings.filterwarnings(
    "ignore",
    message=".*Build for the most recent commit.*is not available.*",
    module="ai2thor",
)

# Ensure dreamai package is importable (repo root = parent of dreamai/)
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from dreamai.envs.ai2thor.procthor_adapter import create_procthor_scene
from dreamai.envs.ai2thor.thor_env import ThorEnv, THOR_DISCRETE_ACTIONS

# Built-in iTHOR scene used when ProcTHOR fails (e.g. CreateHouse on some Macs/setups)
ITHOR_FALLBACK_SCENE = "FloorPlan1"

# Navigation-only actions (indices) that usually succeed: RotateRight, MoveAhead, MoveBack, RotateLeft
NAV_ACTIONS = [2, 0, 2, 0, 1]  # RotateRight, MoveAhead, RotateRight, MoveAhead, MoveBack


def _fmt_pos(pos: dict | None) -> str:
    if not pos:
        return "?"
    return f"({pos.get('x', 0):.2f}, {pos.get('y', 0):.2f}, {pos.get('z', 0):.2f})"


def _fmt_rot(rot: dict | None) -> str:
    if not rot:
        return "?"
    return f"y={rot.get('y', 0):.1f}°"


def main() -> None:
    env = None
    house_generation_procthor = False  # True if CreateHouse succeeded and we use ProcTHOR

    try:
        print("Creating ProcTHOR scene (seed=42)...")
        controller, house = create_procthor_scene(seed=42, split="train")
        print("ProcTHOR scene created. Wrapping in ThorEnv...")
        env = ThorEnv(controller=controller, max_steps=50)
        house_generation_procthor = True
    except (AssertionError, Exception) as e:
        if "CreateHouse" in str(e) or "Unable to" in str(e):
            print(f"ProcTHOR failed: {e}")
            print(f"Falling back to iTHOR scene '{ITHOR_FALLBACK_SCENE}'...")
        else:
            raise
        env = ThorEnv(scene_name=ITHOR_FALLBACK_SCENE, max_steps=50)

    # Critical: report whether house generation (CreateHouse) is in use or not
    if house_generation_procthor:
        print("\n--- HOUSE GENERATION: ProcTHOR (CreateHouse succeeded) ---")
    else:
        print("\n--- HOUSE GENERATION: iTHOR fallback (CreateHouse did not run; using fixed scene) ---")

    try:
        obs, info = env.reset()
        print(f"Reset OK. Obs shape: {obs.shape} | start position {_fmt_pos(info.get('agent_position'))} | rotation {_fmt_rot(info.get('agent_rotation'))}")
        for step in range(5):
            action = NAV_ACTIONS[step % len(NAV_ACTIONS)]
            action_name = THOR_DISCRETE_ACTIONS[action]
            obs, reward, terminated, truncated, info = env.step(action)
            pos = info.get("agent_position")
            rot = info.get("agent_rotation")
            print(
                f"  step {step + 1}: action={action_name}, success={info.get('last_action_success')} | "
                f"position {_fmt_pos(pos)} | rotation {_fmt_rot(rot)}"
            )
            if terminated or truncated:
                break
    finally:
        env.close()
    status = "ProcTHOR" if house_generation_procthor else "iTHOR fallback"
    print(f"Done. (Scene: {status})")


if __name__ == "__main__":
    main()

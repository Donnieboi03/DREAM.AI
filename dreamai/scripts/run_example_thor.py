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
from pathlib import Path

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


def main() -> None:
    env = None
    controller = None

    try:
        print("Creating ProcTHOR scene (seed=42)...")
        controller, house = create_procthor_scene(seed=42, split="train")
        print("ProcTHOR scene created. Wrapping in ThorEnv...")
        env = ThorEnv(controller=controller, max_steps=50)
    except (AssertionError, Exception) as e:
        if "CreateHouse" in str(e) or "Unable to" in str(e):
            print(f"ProcTHOR failed: {e}")
            print(f"Falling back to iTHOR scene '{ITHOR_FALLBACK_SCENE}'...")
        else:
            raise
        env = ThorEnv(scene_name=ITHOR_FALLBACK_SCENE, max_steps=50)

    try:
        obs, info = env.reset()
        print(f"Reset OK. Obs shape: {obs.shape}")
        for step in range(5):
            action = NAV_ACTIONS[step % len(NAV_ACTIONS)]
            action_name = THOR_DISCRETE_ACTIONS[action]
            obs, reward, terminated, truncated, info = env.step(action)
            print(f"  step {step + 1}: action={action_name}, reward={reward}, last_success={info.get('last_action_success')}")
            if terminated or truncated:
                break
    finally:
        env.close()
    print("Done. (No errors — fallback to iTHOR ran successfully.)")


if __name__ == "__main__":
    main()

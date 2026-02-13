#!/usr/bin/env python3
"""E2E: user input -> Orchestrator LLM -> pick built-in scene -> ThorEnv -> simulate.

Uses only AI2-THOR built-in scenes (controller.scenes_in_build). The LLM outputs room_spec_id
and room_preferences; we iterate the built-in scene list and pick a matching scene, then
load it via controller.reset(scene=...). No ProcTHOR-10K, no CreateHouse.

Run from repo root:  PYTHONPATH=. python src/scripts/run_llm_house_e2e.py "I want a kitchen and living room"
Loads .env from repo root automatically. Requires GEMINI_API_KEY or GOOGLE_API_KEY unless --no-llm.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Repo root and .env path (load before any code that needs env vars)
_script_dir = Path(__file__).resolve().parent
_dreamai_root = _script_dir.parent
_repo_root = _dreamai_root.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

# Load .env from repo root so GEMINI_API_KEY / GOOGLE_API_KEY are set
try:
    from dotenv import load_dotenv
    _env_file = _repo_root / ".env"
    if _env_file.exists():
        load_dotenv(_env_file)
except ImportError:
    pass

from src.envs.ai2thor.procthor_adapter import (
    get_builtin_scene_names,
    get_builtin_scene_for_spec,
    get_ithor_scene_names,
)


def run_workflow(
    user_input: str,
    use_llm: bool = True,
    width: int = 400,
    height: int = 300,
    use_global_keys: bool = True,
):
    """Run full pipeline: user input -> (optional) Orchestrator LLM -> pick built-in scene -> Controller -> ThorEnv -> keyboard drive."""
    from ai2thor.controller import Controller
    from src.backend.llm import get_api_key, run_orchestrator_llm

    print("[E2E] User input:", user_input)
    print("[E2E] Mode: built-in scenes only (no 10K, no CreateHouse).")

    declarative = None
    if use_llm and get_api_key():
        print("[E2E] Running Orchestrator LLM (user input -> DeclarativeSpec)...")
        print("[E2E] Calling Orchestrator LLM...")
        declarative = run_orchestrator_llm(user_input)
        from src.tools.validators.declarative_spec import validate_declarative_spec_strict
        validate_declarative_spec_strict(declarative)
        print("[E2E] DeclarativeSpec:", {
            "goal_type": declarative.goal_type,
            "room_preferences": declarative.room_preferences,
            "room_spec_id": declarative.room_spec_id,
            "object_requests": declarative.object_requests,
            "task_focus": declarative.task_focus,
        })
    else:
        if not use_llm:
            print("[E2E] Skipping LLM (--no-llm).")
        else:
            print("[E2E] No API key; skipping LLM.")

    print("[E2E] Creating AI2-THOR Controller (this may take 30-60 seconds on first run)...")
    controller = Controller(
        #branch="main",
        agentMode="default",
        quality="High",
        visibilityDistance=1.5,
        width=width,
        height=height,
        fullscreen=True,
        snapToGrid=True,
        gridSize=0.25,
        rotateStepDegrees=90.0,
    )
    # Prefer iTHOR scene list (FloorPlan*_physics) when available so we don't get ArchitecTHOR-only from scenes_in_build
    scene_names = get_ithor_scene_names(controller) or get_builtin_scene_names(controller)
    print("[E2E] Built-in scenes in this build: %d (e.g. %s)" % (len(scene_names), ", ".join(scene_names[:5]) + ("..." if len(scene_names) > 5 else "")))
    room_spec_id = declarative.room_spec_id if declarative else None
    room_preferences = declarative.room_preferences if declarative else None
    chosen_scene = get_builtin_scene_for_spec(
        room_spec_id=room_spec_id,
        room_preferences=room_preferences,
        scene_names=scene_names,
    )
    print("[E2E] Chosen built-in scene: %s" % chosen_scene)
    controller.reset(scene=chosen_scene)
    print("[E2E] Controller created successfully.")
    import time
    print("[E2E] Waiting 3s for Unity to finish initializing before reset...")
    time.sleep(3)

    from src.envs.ai2thor.thor_env import ThorEnv
    from src.scripts._keyboard_control import run_keyboard_loop

    print("[E2E] Creating ThorEnv wrapper...")
    env = ThorEnv(controller=controller, width=width, height=height)
    print("[E2E] Calling env.reset() to initialize scene...")
    try:
        obs, info = env.reset()
        assert obs is not None
        print("\n" + "=" * 60)
        print("KEYBOARD: W/S/A/D move, Q/E look up/down, P pick up, L drop, T toggle, X quit")
        print("=" * 60)
        if use_global_keys:
            print("Global keys: focus the sim window; WASD/QE/X still work.")
        else:
            print("Terminal mode: keep this terminal focused.")
        print()
        run_keyboard_loop(controller, use_global_keys=use_global_keys)
        return True
    except TimeoutError:
        print("\n[E2E] AI2-THOR backend timed out during env.reset() (Initialize step).", file=sys.stderr)
        print("  python src/scripts/run_llm_house_e2e.py --no-llm", file=sys.stderr)
        print("See: https://github.com/allenai/ai2thor#requirements", file=sys.stderr)
        raise
    finally:
        env.close()
        try:
            controller.stop()
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser(description="E2E: user input -> (optional) LLM -> built-in scene -> ThorEnv simulation (WASD/QE/X to drive)")
    ap.add_argument("user_input", nargs="?", default="I want a small kitchen and living room for navigation")
    ap.add_argument("--no-llm", action="store_true", help="Skip LLM; use default built-in scene (no API key needed)")
    ap.add_argument("--width", type=int, default=400)
    ap.add_argument("--height", type=int, default=300)
    ap.add_argument("--terminal", action="store_true", help="Read keys from terminal only (keep terminal focused)")
    args = ap.parse_args()
    use_llm = not args.no_llm
    from src.backend.llm import get_api_key
    if use_llm and not get_api_key():
        print("GEMINI_API_KEY / GOOGLE_API_KEY not set; run with --no-llm to use default scene", file=sys.stderr)
        sys.exit(1)
    ok = run_workflow(
        args.user_input,
        use_llm=use_llm,
        width=args.width,
        height=args.height,
        use_global_keys=not args.terminal,
    )
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

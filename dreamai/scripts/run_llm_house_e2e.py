#!/usr/bin/env python3
"""E2E: user input -> Orchestrator LLM -> Scene generator LLM -> apply_edits -> ProcTHOR house -> ThorEnv -> simulate.

By default uses ProcTHOR to generate a fresh base house; if generation fails (e.g. CreateHouse unsupported),
falls back to ProcTHOR-10K. Use --use-10k to skip generation and load from the dataset only.

Run from repo root:  PYTHONPATH=. python dreamai/scripts/run_llm_house_e2e.py "I want a kitchen and living room"
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

# ProcTHOR-10K revision (fallback when ProcTHOR generation fails)
PROCTHOR_10K_REVISION = "ab3cacd0fc17754d4c080a3fd50b18395fae8647"
DEFAULT_PROCTHOR_SEED = 42


def _get_base_house_from_10k():
    """Load base house from ProcTHOR-10K train[0]."""
    import prior
    dataset = prior.load_dataset("procthor-10k", revision=PROCTHOR_10K_REVISION)
    return dataset["train"][0]


def get_base_house_dict(
    use_procthor_first: bool = True,
    seed: int = DEFAULT_PROCTHOR_SEED,
    room_spec_id: Optional[str] = None,
):
    """Get base house dict: by default generate with ProcTHOR, else fall back to ProcTHOR-10K.

    When use_procthor_first is True, tries create_procthor_scene(seed=seed, room_spec_id=room_spec_id);
    on failure (e.g. CreateHouse unsupported on macOS ARM), loads from ProcTHOR-10K train[0].
    When use_procthor_first is False, loads from 10K only.
    """
    if use_procthor_first:
        try:
            from dreamai.envs.ai2thor.procthor_adapter import create_procthor_scene
        except ImportError:
            pass
        else:
            try:
                msg = "[E2E] Generating base house with ProcTHOR (seed=%s" % seed
                if room_spec_id:
                    msg += ", room_spec_id=%r" % room_spec_id
                print(msg + ")...")
                controller, house = create_procthor_scene(seed=seed, room_spec_id=room_spec_id)
                try:
                    controller.stop()
                except Exception:
                    pass
                return house.data
            except (AssertionError, RuntimeError, Exception) as e:
                msg = str(e)
                if "CreateHouse" in msg or "Unable to" in msg or "Screen resolution" in msg or "resolution change failed" in msg:
                    print("[E2E] ProcTHOR generation failed: %s" % e)
                    print("[E2E] Falling back to ProcTHOR-10K train[0]...")
                else:
                    raise
    print("[E2E] Loading base house from ProcTHOR-10K train[0]...")
    return _get_base_house_from_10k()


def run_workflow(
    user_input: str,
    use_llm: bool = True,
    width: int = 400,
    height: int = 300,
    use_global_keys: bool = True,
    use_procthor_first: bool = True,
    procthor_seed: int = DEFAULT_PROCTHOR_SEED,
):
    """Run full pipeline: user_input -> LLMs -> edited house -> Controller -> ThorEnv -> keyboard drive."""
    from ai2thor.controller import Controller
    from dreamai.backend.llm import get_api_key, run_orchestrator_llm, run_scene_generator_llm
    from dreamai.backend.orchestrator import get_house_summary, apply_edits

    print("[E2E] User input:", user_input)

    if use_llm and get_api_key():
        print("[E2E] Running Orchestrator LLM (user input -> DeclarativeSpec)...")
        print("[E2E] Calling Orchestrator LLM...")
        declarative = run_orchestrator_llm(user_input)
        from dreamai.tools.validators.declarative_spec import validate_declarative_spec_strict
        validate_declarative_spec_strict(declarative)
        print("[E2E] DeclarativeSpec:", {
            "goal_type": declarative.goal_type,
            "room_preferences": declarative.room_preferences,
            "room_spec_id": declarative.room_spec_id,
            "object_requests": declarative.object_requests,
            "task_focus": declarative.task_focus,
        })
        base_house = get_base_house_dict(
            use_procthor_first=use_procthor_first,
            seed=procthor_seed,
            room_spec_id=declarative.room_spec_id,
        )
        house_summary = get_house_summary(base_house)
        print("[E2E] Base house summary (rooms):", house_summary[:200] + "..." if len(house_summary) > 200 else house_summary)
        print("[E2E] Running Scene generator LLM (DeclarativeSpec + house summary -> HouseEditRequest)...")
        print("[E2E] Calling Scene generator LLM...")
        scene_response = run_scene_generator_llm(declarative, house_summary)
        edits = scene_response.house_edit_request.object_edits
        print("[E2E] Scene generator returned", len(edits), "object edit(s).")
        for i, e in enumerate(edits):
            print(f"      [{i+1}] {e.action}: object_id={e.object_id!r} asset_id={e.asset_id!r} room_id={e.room_id!r}")
        edited_house = apply_edits(base_house, scene_response.house_edit_request)
        print("[E2E] Applied edits to base house; launching simulation.")
        print(f"[E2E] Edited house has {len(edited_house.get('objects', []))} objects")
    else:
        base_house = get_base_house_dict(use_procthor_first=use_procthor_first, seed=procthor_seed)
        house_summary = get_house_summary(base_house)
        print("[E2E] Base house summary (rooms):", house_summary[:200] + "..." if len(house_summary) > 200 else house_summary)
        if not use_llm:
            print("[E2E] Skipping LLM (--no-llm); using base house as-is.")
        else:
            print("[E2E] No API key; using base house as-is.")
        edited_house = base_house

    print("[E2E] Creating AI2-THOR Controller (this may take 30-60 seconds on first run)...")
    # Match run_proc_test: do not pass scene=house_dict (not supported on all builds).
    # Create controller with no scene so it picks a default, then load house via CreateHouse.
    controller = Controller(
        #branch="main",
        agentMode="default",
        platform="Linux64",
        visibilityDistance=1.5,
        width=width,
        height=height,
        fullscreen=False,
        snapToGrid=True,
        gridSize=0.25,
        rotateStepDegrees=90.0,
    )
    print("[E2E] Loading house via CreateHouse...")
    evt = controller.step(action="CreateHouse", house=edited_house, renderImage=False)
    create_house_ok = evt and evt.metadata.get("lastActionSuccess", True)
    if not create_house_ok:
        # Many pip-installed ai2thor builds don't support CreateHouse (iTHOR-only).
        # Fall back to a built-in scene so the user can at least run the demo.
        fallback_scene = "FloorPlan1"
        print("[E2E] CreateHouse not supported or failed (no event or lastActionSuccess=False).", file=sys.stderr)
        print("[E2E] Your AI2-THOR build may be iTHOR-only. Using built-in scene %r instead." % fallback_scene, file=sys.stderr)
        if evt and evt.metadata.get("errorMessage"):
            print("[E2E] CreateHouse errorMessage: %s" % evt.metadata.get("errorMessage"), file=sys.stderr)
        try:
            controller.reset(scene=fallback_scene)
        except Exception as e:
            print("[E2E] Fallback reset(%r) failed: %s" % (fallback_scene, e), file=sys.stderr)
            raise RuntimeError(
                "CreateHouse failed and fallback to %r failed. "
                "Try: pip install ai2thor (ProcTHOR support may need branch 'main'), or run: python dreamai/scripts/run_llm_house_e2e.py --no-llm --use-10k"
                % fallback_scene
            ) from e
    else:
        # Teleport to a reachable position so agent is not in void/underground (run_proc_test pattern)
        evt = controller.step(action="GetReachablePositions")
        rp = (evt.metadata.get("actionReturn") or []) if evt else []
        if rp:
            controller.step(action="Teleport", position=rp[0], forceAction=True)

    print("[E2E] Controller created successfully.")
    import time
    print("[E2E] Waiting 3s for Unity to finish initializing before reset...")
    time.sleep(3)

    from dreamai.envs.ai2thor.thor_env import ThorEnv
    from dreamai.scripts._keyboard_control import run_keyboard_loop

    print("[E2E] Creating ThorEnv wrapper...")
    env = ThorEnv(controller=controller, width=width, height=height)
    print("[E2E] Calling env.reset() to initialize scene...")
    try:
        obs, info = env.reset()
        assert obs is not None
        print("\n" + "=" * 60)
        print("KEYBOARD: W/S/A/D move, Q/E look up/down, X quit")
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
        print("On macOS, procedural scenes often hit this; use a pre-built house instead:", file=sys.stderr)
        print("  python dreamai/scripts/run_llm_house_e2e.py --no-llm --use-10k", file=sys.stderr)
        print("See: https://github.com/allenai/ai2thor#requirements", file=sys.stderr)
        raise
    finally:
        env.close()
        try:
            controller.stop()
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser(description="E2E: user input -> LLM pipeline -> house -> ThorEnv simulation (WASD/QE/X to drive)")
    ap.add_argument("user_input", nargs="?", default="I want a small kitchen and living room for navigation")
    ap.add_argument("--no-llm", action="store_true", help="Skip LLM; use base house only (no API key needed)")
    ap.add_argument("--use-10k", action="store_true", help="Use ProcTHOR-10K dataset instead of generating (recommended on macOS if Initialize times out)")
    ap.add_argument("--seed", type=int, default=DEFAULT_PROCTHOR_SEED, help="Random seed for ProcTHOR generation (default %s)" % DEFAULT_PROCTHOR_SEED)
    ap.add_argument("--width", type=int, default=400)
    ap.add_argument("--height", type=int, default=300)
    ap.add_argument("--terminal", action="store_true", help="Read keys from terminal only (keep terminal focused)")
    args = ap.parse_args()
    use_llm = not args.no_llm
    from dreamai.backend.llm import get_api_key
    if use_llm and not get_api_key():
        print("GEMINI_API_KEY / GOOGLE_API_KEY not set; run with --no-llm to use base house only", file=sys.stderr)
        sys.exit(1)
    ok = run_workflow(
        args.user_input,
        use_llm=use_llm,
        width=args.width,
        height=args.height,
        use_global_keys=not args.terminal,
        use_procthor_first=not args.use_10k,
        procthor_seed=args.seed,
    )
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

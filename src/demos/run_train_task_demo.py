#!/usr/bin/env python3
"""Demo: prompt -> Orchestrator LLM -> DeclarativeSpec (policy_mode, network_size) -> TaskSpec -> optional training.

Shows how the LLM selects policy_mode and network_size from a training prompt, and how
those flow into TaskSpec.extra for the SB3 train script.

Run from repo root:
  PYTHONPATH=. python src/demos/run_train_task_demo.py
  PYTHONPATH=. python src/demos/run_train_task_demo.py "Train a model to pick up apple in kitchen"
  PYTHONPATH=. python src/demos/run_train_task_demo.py --train --total-timesteps 1000

Requires GEMINI_API_KEY or GOOGLE_API_KEY. Use --no-llm to skip LLM and use defaults.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

_script_dir = Path(__file__).resolve().parent
_src_dir = _script_dir.parent
_repo_root = _src_dir.parent
for p in (str(_repo_root), str(_src_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from dotenv import load_dotenv
    _env_file = _repo_root / ".env"
    if _env_file.exists():
        load_dotenv(_env_file)
except ImportError:
    pass

DEFAULT_PROMPT = "Train a model to pick up apple in kitchen"


async def run_demo(
    prompt: str,
    use_llm: bool,
    train: bool,
    total_timesteps: int,
    save_task_path: str | None,
) -> bool:
    """Run the pipeline: prompt -> LLM -> TaskSpec -> optionally train."""
    from src.backend.llm import get_api_key
    from src.backend.orchestrator.task_generator import generate_task_from_prompt

    print("[Demo] Prompt:", prompt)
    print("[Demo] Use LLM:", use_llm)
    print()

    if use_llm and not get_api_key():
        print("Error: GEMINI_API_KEY or GOOGLE_API_KEY not set. Use --no-llm to skip LLM.", file=sys.stderr)
        return False

    try:
        if use_llm:
            print("[Demo] Running Orchestrator LLM -> DeclarativeSpec -> TaskSpec...")
            response = await generate_task_from_prompt(
                prompt=prompt,
                scene_id=None,
                max_steps=500,
            )
            task = response.task
            scene_id = response.scene_id
            print("[Demo] Scene:", scene_id)
            print("[Demo] TaskSpec.extra:", task.extra)
            if task.extra:
                policy_mode = task.extra.get("policy_mode", "(default)")
                network_size = task.extra.get("network_size", "(medium)")
                print("[Demo] policy_mode:", policy_mode)
                print("[Demo] network_size:", network_size)
        else:
            print("[Demo] Skipping LLM (--no-llm). Using defaults.")
            from src.backend.schemas import TaskSpec
            task = TaskSpec(
                description=prompt,
                goal=prompt,
                success_criteria=["Complete task", "Within step limit"],
                max_steps=500,
                subtasks=[],
                extra={"policy_mode": "default", "network_size": "medium"},
            )
            scene_id = "FloorPlan1"

        print()
        task_dict = task.model_dump(mode="json")
        if task_dict.get("extra"):
            print("[Demo] TaskSpec (with extra for SB3):")
            print(json.dumps(task_dict, indent=2))
        else:
            print("[Demo] TaskSpec:", task_dict)

        if save_task_path:
            out_path = Path(save_task_path)
            out_path.write_text(json.dumps(task_dict, indent=2))
            print(f"\n[Demo] Saved TaskSpec to {out_path}")
            print(f"[Demo] Train with: PYTHONPATH=src python -m rl.sb3.train --task-spec {out_path} --scene {scene_id}")

        if train:
            print("\n[Demo] Starting SB3 training...")
            try:
                from rl.sb3 import train as train_module
                old_argv = sys.argv
                sys.argv = [
                    "rl.sb3.train",
                    "--scene", scene_id,
                    "--total-timesteps", str(total_timesteps),
                ]
                if save_task_path and Path(save_task_path).exists():
                    sys.argv.extend(["--task-spec", str(Path(save_task_path).resolve())])
                try:
                    train_module.main()
                finally:
                    sys.argv = old_argv
            except ImportError as e:
                print(f"[Demo] Cannot run training: {e}", file=sys.stderr)
                print("Install: pip install stable-baselines3", file=sys.stderr)
                return False

        return True
    except Exception as e:
        print(f"[Demo] Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Demo: prompt -> LLM -> TaskSpec (policy_mode, network_size) -> optional SB3 training"
    )
    ap.add_argument(
        "prompt",
        nargs="?",
        default=DEFAULT_PROMPT,
        help="Training prompt (default: %(default)s)",
    )
    ap.add_argument("--no-llm", action="store_true", help="Skip LLM; use default policy_mode and network_size")
    ap.add_argument("--train", action="store_true", help="Run SB3 training after generating task")
    ap.add_argument("--total-timesteps", type=int, default=2000, help="Training steps when --train (default: 2000)")
    ap.add_argument(
        "--save-task",
        default="task_spec.json",
        help="Save TaskSpec JSON to this path (default: task_spec.json)",
    )
    args = ap.parse_args()

    ok = asyncio.run(
        run_demo(
            prompt=args.prompt,
            use_llm=not args.no_llm,
            train=args.train,
            total_timesteps=args.total_timesteps,
            save_task_path=args.save_task,
        )
    )
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

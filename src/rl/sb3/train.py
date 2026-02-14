"""
SB3 PPO training script for ThorEnv.

Usage:
  PYTHONPATH=src python -m rl.sb3.train --scene FloorPlan1 --total-timesteps 10000
  PYTHONPATH=src python -m rl.sb3.train --task-spec task.json --policy-mode fast --network-size small
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from stable_baselines3 import PPO

from envs.ai2thor.thor_env import ThorEnv
from rl.sb3.policy_modes import get_network_config, get_policy_config
from rl.sb3.wrappers import ChannelFirstWrapper


def make_env(scene_name: str, max_steps: int = 500):
    """Create ThorEnv wrapped for CnnPolicy (CHW observation)."""
    env = ThorEnv(scene_name=scene_name, max_steps=max_steps)
    env = ChannelFirstWrapper(env)
    return env


def load_task_spec(path: str | Path) -> dict | None:
    """Load TaskSpec JSON and return the parsed dict. Returns None if invalid."""
    path = Path(path)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Train PPO on ThorEnv")
    parser.add_argument("--scene", default="FloorPlan1", help="iTHOR scene name")
    parser.add_argument("--max-steps", type=int, default=500, help="Max steps per episode")
    parser.add_argument("--total-timesteps", type=int, default=50_000, help="Total training steps")
    parser.add_argument("--policy-mode", default="default", help="Policy mode: default, fast, sample_efficient, exploration")
    parser.add_argument("--network-size", default="medium", help="Network size: small, medium, large")
    parser.add_argument("--task-spec", help="Path to TaskSpec JSON; overrides --policy-mode and --network-size from extra")
    parser.add_argument("--save-path", help="Path to save trained model")
    parser.add_argument("--verbose", type=int, default=1, help="SB3 verbosity")
    args = parser.parse_args()

    policy_mode = args.policy_mode
    network_size = args.network_size

    if args.task_spec:
        task_data = load_task_spec(args.task_spec)
        if task_data:
            extra = task_data.get("extra") or {}
            if extra.get("policy_mode") in ("default", "fast", "sample_efficient", "exploration"):
                policy_mode = extra["policy_mode"]
            if extra.get("network_size") in ("small", "medium", "large"):
                network_size = extra["network_size"]

    config = get_policy_config(policy_mode)
    config["policy_kwargs"] = get_network_config(network_size)
    config["verbose"] = args.verbose

    env = make_env(args.scene, max_steps=args.max_steps)

    model = PPO(
        "CnnPolicy",
        env,
        **config,
    )
    model.learn(total_timesteps=args.total_timesteps)

    if args.save_path:
        model.save(args.save_path)
        print(f"Model saved to {args.save_path}")

    env.close()


if __name__ == "__main__":
    main()

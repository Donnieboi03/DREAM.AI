"""
RL agent running in a separate process. Connects to the backend WebSocket.

When --model-path or policy_mode/network_size is provided: uses SB3 PPO with RemoteThorEnv
for training. Otherwise falls back to random policy.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import signal
import threading
import time
from pathlib import Path

try:
    import websockets
except ImportError:
    raise ImportError("Install websockets: pip install websockets>=12.0")

NUM_ACTIONS = 9
MAX_STEPS_DEFAULT = 500
CHECKPOINT_DIR = Path(os.environ.get("DREAMAI_RL_CHECKPOINT", "~/.dreamai/rl_checkpoint")).expanduser()
CHECKPOINT_PATH = CHECKPOINT_DIR / "latest.pkl"
MODEL_DIR = Path(os.environ.get("DREAMAI_RL_MODELS", "~/.dreamai/rl_models")).expanduser()
CURRENT_MODEL_PATH = MODEL_DIR / "current_model.zip"

# Global for signal handler
_ppoSaveModel = None
_stopRequested = False


def _on_sigterm(signum, frame):
    global _stopRequested
    _stopRequested = True
    if _ppoSaveModel is not None:
        try:
            MODEL_DIR.mkdir(parents=True, exist_ok=True)
            _ppoSaveModel.save(str(CURRENT_MODEL_PATH))
            print("[RL] Model saved on SIGTERM")
        except Exception as e:
            print(f"[RL] Failed to save on SIGTERM: {e}")


def save_checkpoint(metrics: dict, step_count: int) -> None:
    """Save RL state to disk (metrics, step count). For random policy, minimal state."""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    state = {"metrics": metrics, "step_count": step_count, "saved_at": time.time()}
    try:
        import pickle
        with open(CHECKPOINT_PATH, "wb") as f:
            pickle.dump(state, f)
    except Exception as e:
        print(f"[RL] Failed to save checkpoint: {e}")


def load_checkpoint() -> tuple[dict | None, int]:
    """Load saved state if present. Returns (metrics, step_count) or (None, 0)."""
    if not CHECKPOINT_PATH.exists():
        return None, 0
    try:
        import pickle
        with open(CHECKPOINT_PATH, "rb") as f:
            state = pickle.load(f)
        return state.get("metrics"), state.get("step_count", 0)
    except Exception as e:
        print(f"[RL] Failed to load checkpoint: {e}")
        return None, 0


def _run_sb3_training(
    ws_url: str,
    model_path: str | None,
    policy_mode: str,
    network_size: str,
    max_steps: int,
) -> None:
    """Run SB3 PPO training with RemoteThorEnv. Blocks until done or stop requested."""
    global _ppoSaveModel, _stopRequested
    from stable_baselines3 import PPO
    from rl.sb3.policy_modes import get_policy_config, get_network_config
    from rl.remote_env import RemoteThorEnv

    env = RemoteThorEnv(ws_url=ws_url, max_steps=max_steps)
    env.start()
    try:
        if model_path and Path(model_path).exists():
            print(f"[RL] Loading PPO from {model_path}")
            model = PPO.load(model_path, env=env)
        else:
            config = get_policy_config(policy_mode)
            config["policy_kwargs"] = get_network_config(network_size)
            config["verbose"] = 1
            print(f"[RL] Creating fresh PPO (policy_mode={policy_mode}, network_size={network_size})")
            model = PPO("CnnPolicy", env, **config)

        _ppoSaveModel = model
        total_timesteps = 1_000_000

        from stable_baselines3.common.callbacks import BaseCallback
        class StopAndCheckpointCallback(BaseCallback):
            def _on_step(self) -> bool:
                if _stopRequested:
                    return False
                if self.n_calls > 0 and self.n_calls % 5000 == 0:
                    try:
                        MODEL_DIR.mkdir(parents=True, exist_ok=True)
                        model.save(str(CURRENT_MODEL_PATH))
                        print(f"[RL] Checkpoint saved at step {self.n_calls}")
                    except Exception:
                        pass
                return True

        model.learn(total_timesteps=total_timesteps, callback=StopAndCheckpointCallback())

        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        model.save(str(CURRENT_MODEL_PATH))
        print(f"[RL] Model saved to {CURRENT_MODEL_PATH}")
    finally:
        env.close()


async def run_agent_random(
    ws_url: str,
    decision_hz: float = 4.0,
    max_steps: int = MAX_STEPS_DEFAULT,
) -> None:
    """Random policy fallback when SB3 not used."""
    last_action_time = 0.0
    min_interval = 1.0 / decision_hz

    while True:
        try:
            async with websockets.connect(ws_url) as ws:
                print(f"[RL] Connected to {ws_url} (random policy)")

                await ws.send(json.dumps({"type": "identify", "role": "rl_agent"}))
                msg = json.loads(await ws.recv())
                if msg.get("type") != "identified":
                    print(f"[RL] Identify: {msg.get('type')}")

                await ws.send(json.dumps({"type": "start_streaming"}))
                msg = json.loads(await ws.recv())
                if msg.get("type") != "streaming_started":
                    print(f"[RL] Streaming: {msg.get('type')}")

                while True:
                    raw = await ws.recv()
                    try:
                        msg = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    if msg.get("type") in ("action_result", "reset_result"):
                        continue

                    if msg.get("type") == "frame":
                        metrics = msg.get("metrics") or {}
                        now = time.monotonic()
                        if now - last_action_time < min_interval:
                            continue
                        last_action_time = now

                        sc = metrics.get("step_count", 0)
                        is_success = metrics.get("is_success")
                        if is_success is True or sc >= max_steps:
                            await ws.send(json.dumps({"type": "reset", "randomize": True}))
                            continue

                        action = random.randint(0, NUM_ACTIONS - 1)
                        await ws.send(json.dumps({"type": "action", "action": action}))

        except websockets.exceptions.ConnectionClosed as e:
            print(f"[RL] Connection closed: {e}, reconnecting in 3s...")
        except Exception as e:
            print(f"[RL] Error: {e}, reconnecting in 3s...")

        await asyncio.sleep(3.0)


async def run_agent(
    ws_url: str = "ws://localhost:8000/ws/game",
    decision_hz: float = 4.0,
    max_steps: int = MAX_STEPS_DEFAULT,
    model_path: str | None = None,
    policy_mode: str = "default",
    network_size: str = "medium",
) -> None:
    """Main entry: SB3 training if model/presets given, else random policy."""
    use_sb3 = model_path or True
    try:
        import stable_baselines3
    except ImportError:
        use_sb3 = False
        print("[RL] stable-baselines3 not installed, using random policy")

    if use_sb3 and (model_path or True):
        signal.signal(signal.SIGTERM, _on_sigterm)
        t = threading.Thread(
            target=_run_sb3_training,
            args=(ws_url, model_path, policy_mode, network_size, max_steps),
        )
        t.daemon = True
        t.start()
        while t.is_alive() and not _stopRequested:
            await asyncio.sleep(1.0)
        return

    await run_agent_random(ws_url=ws_url, decision_hz=decision_hz, max_steps=max_steps)


def main() -> None:
    parser = argparse.ArgumentParser(description="DREAM.AI RL agent (separate process)")
    parser.add_argument("--url", default=os.environ.get("DREAMAI_WS_URL", "ws://localhost:8000/ws/game"), help="WebSocket URL")
    parser.add_argument("--hz", type=float, default=4.0, help="Decision rate (Hz) for random policy")
    parser.add_argument("--max-steps", type=int, default=MAX_STEPS_DEFAULT, help="Max steps per episode")
    parser.add_argument("--model-path", help="Path to SB3 model .zip for continue training")
    parser.add_argument("--policy-mode", default="default", help="Policy mode when no model")
    parser.add_argument("--network-size", default="medium", help="Network size when no model")
    args = parser.parse_args()

    asyncio.run(run_agent(
        ws_url=args.url,
        decision_hz=args.hz,
        max_steps=args.max_steps,
        model_path=args.model_path,
        policy_mode=args.policy_mode,
        network_size=args.network_size,
    ))


if __name__ == "__main__":
    main()

"""
RL agent running in a separate process. Connects to the backend WebSocket, receives
frames and metrics, runs a default policy, and sends actions when control_mode is "agent".
Saves state when user takes control and resumes when control returns to agent.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import time
from pathlib import Path

try:
    import websockets
except ImportError:
    raise ImportError("Install websockets: pip install websockets>=12.0")

# Default actions 0-8 (MoveAhead, MoveBack, RotateLeft, RotateRight, LookUp, LookDown,
# PickupObject, DropHandObject, ToggleObjectOn)
NUM_ACTIONS = 9
MAX_STEPS_DEFAULT = 500
CHECKPOINT_DIR = Path(os.environ.get("DREAMAI_RL_CHECKPOINT", "~/.dreamai/rl_checkpoint")).expanduser()
CHECKPOINT_PATH = CHECKPOINT_DIR / "latest.pkl"


def save_checkpoint(metrics: dict, step_count: int) -> None:
    """Save RL state to disk (metrics, step count). For random policy, minimal state."""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    state = {
        "metrics": metrics,
        "step_count": step_count,
        "saved_at": time.time(),
    }
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


async def run_agent(
    ws_url: str = "ws://localhost:8000/ws/game",
    decision_hz: float = 4.0,
    max_steps: int = MAX_STEPS_DEFAULT,
) -> None:
    """Connect to backend, receive frames, act when control_mode is agent."""
    last_control_mode: str | None = None
    last_action_time = 0.0
    min_interval = 1.0 / decision_hz

    while True:
        try:
            async with websockets.connect(ws_url) as ws:
                print(f"[RL] Connected to {ws_url}")

                # Identify as RL agent
                await ws.send(json.dumps({"type": "identify", "role": "rl_agent"}))
                msg = json.loads(await ws.recv())
                if msg.get("type") == "identified":
                    print("[RL] Identified as rl_agent")
                elif msg.get("type") == "error":
                    print(f"[RL] Identify error: {msg.get('message')}")

                # Start streaming to receive frames
                await ws.send(json.dumps({"type": "start_streaming"}))
                msg = json.loads(await ws.recv())
                if msg.get("type") != "streaming_started":
                    print(f"[RL] Unexpected response to start_streaming: {msg.get('type')}")

                resumed = False

                while True:
                    raw = await ws.recv()
                    try:
                        msg = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    msg_type = msg.get("type")

                    if msg_type == "action_result":
                        # Ignore; we may have sent an action earlier
                        continue

                    if msg_type == "reset_result":
                        continue

                    if msg_type == "frame":
                        metrics = msg.get("metrics") or {}
                        control_mode = metrics.get("control_mode", "user")

                        # On switch to user: save state
                        if control_mode == "user":
                            if last_control_mode == "agent":
                                step_count = metrics.get("step_count", 0)
                                save_checkpoint(metrics, step_count)
                                print("[RL] User took control, saved state")
                            last_control_mode = "user"
                            resumed = False  # Next switch to agent will load
                            continue

                        # control_mode == "agent"
                        prev_mode = last_control_mode
                        last_control_mode = "agent"

                        # On switch from user to agent: load state
                        if prev_mode == "user" and resumed is False:
                            loaded_metrics, loaded_step = load_checkpoint()
                            if loaded_metrics is not None:
                                resumed = True
                                print(f"[RL] Resumed from checkpoint (step {loaded_step})")

                        # Throttle decisions
                        now = time.monotonic()
                        if now - last_action_time < min_interval:
                            continue
                        last_action_time = now

                        # Episode end: reset
                        sc = metrics.get("step_count", 0)
                        is_success = metrics.get("is_success")
                        if is_success is True or sc >= max_steps:
                            await ws.send(json.dumps({"type": "reset", "randomize": True}))
                            continue

                        # Act: random policy
                        action = random.randint(0, NUM_ACTIONS - 1)
                        await ws.send(json.dumps({"type": "action", "action": action}))

        except websockets.exceptions.ConnectionClosed as e:
            print(f"[RL] Connection closed: {e}, reconnecting in 3s...")
        except Exception as e:
            print(f"[RL] Error: {e}, reconnecting in 3s...")

        await asyncio.sleep(3.0)


def main() -> None:
    parser = argparse.ArgumentParser(description="DREAM.AI default RL agent (separate process)")
    parser.add_argument(
        "--url",
        default=os.environ.get("DREAMAI_WS_URL", "ws://localhost:8000/ws/game"),
        help="WebSocket URL",
    )
    parser.add_argument(
        "--hz",
        type=float,
        default=4.0,
        help="Decision rate (Hz)",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=MAX_STEPS_DEFAULT,
        help="Max steps per episode before reset",
    )
    args = parser.parse_args()
    asyncio.run(run_agent(ws_url=args.url, decision_hz=args.hz, max_steps=args.max_steps))


if __name__ == "__main__":
    main()

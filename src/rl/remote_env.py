"""
RemoteThorEnv: Gymnasium-compatible env that wraps the backend via WebSocket.

Used by run_agent for SB3 training. reset() and step() block until the WebSocket
provides observation and metrics from the remote ThorEnv.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import queue
import threading
from typing import Any

import gymnasium as gym
import numpy as np
import websockets

from tools.actions import THOR_DISCRETE_ACTIONS


def _jpeg_to_chw(jpeg_b64: str, height: int, width: int) -> np.ndarray:
    """Decode base64 JPEG to numpy array (C, H, W) for CnnPolicy."""
    from PIL import Image
    raw = base64.b64decode(jpeg_b64)
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    arr = np.asarray(img, dtype=np.uint8)  # (H, W, 3)
    # Resize if needed to match expected shape
    if arr.shape[0] != height or arr.shape[1] != width:
        img = img.resize((width, height), Image.BILINEAR)
        arr = np.asarray(img, dtype=np.uint8)
    # HWC -> CHW
    arr = np.moveaxis(arr, -1, 0)
    return arr


class RemoteThorEnv(gym.Env):
    """Gymnasium env that uses WebSocket to communicate with backend ThorEnv."""

    def __init__(
        self,
        ws_url: str,
        height: int = 720,
        width: int = 1280,
        max_steps: int = 500,
        seed: int | None = None,
    ):
        super().__init__()
        self.ws_url = ws_url
        self._height = height
        self._width = width
        self._max_steps = max_steps
        self._step_count = 0

        self.action_space = gym.spaces.Discrete(len(THOR_DISCRETE_ACTIONS))
        self.observation_space = gym.spaces.Box(
            low=0,
            high=255,
            shape=(3, height, width),
            dtype=np.uint8,
        )

        self._request_q: queue.Queue = queue.Queue()
        self._response_q: queue.Queue = queue.Queue()
        self._ws_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def _run_ws_loop(self) -> None:
        """Run WebSocket loop in a thread. Services reset/step requests."""
        import asyncio
        asyncio.run(self._ws_async_loop())

    async def _ws_async_loop(self) -> None:
        max_retries = 30
        retry_delay = 3.0
        for attempt in range(max_retries):
            try:
                ws = await websockets.connect(self.ws_url)
                break
            except OSError as e:
                if attempt < max_retries - 1:
                    print(f"[RemoteThorEnv] Connection failed (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s: {e}")
                    await asyncio.sleep(retry_delay)
                else:
                    raise RuntimeError(f"Could not connect to {self.ws_url} after {max_retries} attempts: {e}") from e
        else:
            raise RuntimeError(f"Could not connect to {self.ws_url}")

        async with ws:
            await ws.send(json.dumps({"type": "identify", "role": "rl_agent"}))
            msg = json.loads(await ws.recv())
            if msg.get("type") != "identified":
                raise RuntimeError(f"Identify failed: {msg}")

            await ws.send(json.dumps({"type": "start_streaming"}))
            msg = json.loads(await ws.recv())
            if msg.get("type") != "streaming_started":
                raise RuntimeError(f"Streaming start failed: {msg}")

            while not self._stop_event.is_set():
                try:
                    req = self._request_q.get(timeout=0.5)
                except queue.Empty:
                    # Consume any stray messages to keep stream moving
                    try:
                        await asyncio.wait_for(ws.recv(), timeout=0.01)
                    except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                        pass
                    continue

                if req is None:
                    break

                typ, action = req
                try:
                    if typ == "reset":
                        await ws.send(json.dumps({"type": "reset"}))
                        reset_result = None
                        frame_data = None
                        while reset_result is None or frame_data is None:
                            raw = await ws.recv()
                            msg = json.loads(raw)
                            if msg.get("type") == "reset_result":
                                reset_result = msg.get("data", {})
                            elif msg.get("type") == "frame":
                                frame_data = msg

                        obs = _jpeg_to_chw(
                            frame_data["jpeg_base64"],
                            self._height,
                            self._width,
                        )
                        info = reset_result.get("initial_metrics", {})
                        self._response_q.put((obs, 0.0, False, False, info))

                    elif typ == "step":
                        await ws.send(json.dumps({"type": "action", "action": int(action)}))
                        action_result = None
                        frame_data = None
                        while action_result is None or frame_data is None:
                            raw = await ws.recv()
                            msg = json.loads(raw)
                            if msg.get("type") == "action_result":
                                data = msg.get("data", {})
                                if isinstance(data, dict) and "error" not in data:
                                    action_result = data
                            elif msg.get("type") == "frame":
                                frame_data = msg

                        obs = _jpeg_to_chw(
                            frame_data["jpeg_base64"],
                            self._height,
                            self._width,
                        )
                        if action_result.get("skipped"):
                            # Backend skipped action (e.g. control switched); treat as no-op
                            reward = 0.0
                            done = False
                            info = dict(action_result.get("metrics", {}))
                        else:
                            reward = float(action_result.get("reward", 0.0))
                            done = bool(action_result.get("done", False))
                            metrics = action_result.get("metrics", {})
                            info = dict(metrics)
                        self._response_q.put((obs, reward, done, done, info))

                except Exception as e:
                    self._response_q.put((None, 0.0, True, True, {"error": str(e)}))

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict]:
        super().reset(seed=seed)
        self._step_count = 0
        self._request_q.put(("reset", None))
        result = self._response_q.get()
        obs, _, _, _, info = result
        if obs is None:
            raise RuntimeError("Reset failed")
        return obs, info

    def step(self, action: int) -> tuple[np.ndarray, float, bool, bool, dict]:
        self._step_count += 1
        self._request_q.put(("step", action))
        result = self._response_q.get()
        obs, reward, terminated, truncated, info = result
        if obs is None:
            terminated = truncated = True
            obs = np.zeros(self.observation_space.shape, dtype=np.uint8)
        if self._step_count >= self._max_steps:
            truncated = True
        return obs, reward, terminated, truncated, info

    def start(self) -> None:
        """Start the WebSocket thread. Call before reset/step."""
        self._stop_event.clear()
        self._ws_thread = threading.Thread(target=self._run_ws_loop, daemon=True)
        self._ws_thread.start()
        # Allow connection to establish
        import time
        time.sleep(2)

    def close(self) -> None:
        """Stop the WebSocket thread."""
        self._stop_event.set()
        self._request_q.put(None)
        if self._ws_thread and self._ws_thread.is_alive():
            self._ws_thread.join(timeout=5)
        self._ws_thread = None

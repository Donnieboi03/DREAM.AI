"""
Shared keyboard control loop for ProcTHOR demo scripts.

Uses ThorEnv.step() as the single source of action execution (Pickup/Drop/Toggle
object resolution is handled inside ThorEnv). Supports two input modes:
- Global keys: Uses pynput so WASD/QE/X work even when the AI2-THOR window is focused.
- Terminal: Read keys from stdin only (must keep terminal focused).

Notes:
- Keys normalized to lowercase so Shift/CapsLock doesn't break controls.
- P=pick up, L=drop, T=toggle, X=quit.
"""

from __future__ import annotations

import queue
import sys
import termios
import threading
import tty
from typing import Any, Callable, Optional

from tools.actions import THOR_DISCRETE_ACTIONS


# Map keyboard keys -> discrete action IDs (must align with THOR_DISCRETE_ACTIONS indices)
KEY_ACTIONS = {
    "w": 0,  # MoveAhead
    "s": 1,  # MoveBack
    "a": 2,  # RotateLeft
    "d": 3,  # RotateRight
    "q": 4,  # LookUp
    "e": 5,  # LookDown
    "p": 6,  # PickupObject
    "l": 7,  # DropHandObject
    "t": 8,  # ToggleObjectOn (ThorEnv resolves to On/Off based on object state)
}

# Quit keys (we normalize input to lowercase, so only include lowercase)
QUIT_KEYS = ("x", "\x03")  # x or Ctrl+C


def _terminal_get_key() -> str:
    """Read one key from stdin (Unix/macOS). Requires terminal focus."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def run_keyboard_loop(
    env: Any,
    use_global_keys: bool = True,
    on_action: Optional[Callable[[str, bool, dict], None]] = None,
    debug_keys: bool = False,
) -> None:
    """Run the WASD/QE/X control loop until user presses X or Ctrl+C.

    Args:
        env: ThorEnv instance; env.step(action_id) will be called. All action logic
            (including Pickup/Drop/Toggle object resolution) lives in ThorEnv.
        use_global_keys: If True, try pynput so keys work when the sim window is focused.
            If pynput is not installed or fails, falls back to terminal input.
        on_action: Optional callback(action_name, success, info) after each step.
        debug_keys: If True, prints every received key and the input mode.
    """
    key_queue: queue.Queue[Optional[str]] = queue.Queue()
    stop_event = threading.Event()
    use_pynput = use_global_keys

    keyboard = None
    listener = None

    if use_global_keys:
        try:
            from pynput import keyboard as _keyboard  # type: ignore
            keyboard = _keyboard
        except ImportError:
            use_pynput = False
            print(
                "Tip: install 'pynput' so keys work when the simulation window is focused:\n"
                "  pip install pynput"
            )

    def on_press(key) -> None:
        if stop_event.is_set():
            return
        try:
            k = key.char if hasattr(key, "char") and key.char else None
        except Exception:
            k = None

        if k is None:
            return

        k = k.lower()
        key_queue.put(k)

        if k in QUIT_KEYS:
            stop_event.set()

    if use_pynput and keyboard is not None:
        try:
            listener = keyboard.Listener(on_press=on_press)
            listener.daemon = True
            listener.start()
        except Exception as e:
            use_pynput = False
            listener = None
            if debug_keys:
                print(f"[keyboard] pynput failed, falling back to terminal input: {e!r}")

    if debug_keys:
        print(f"[keyboard] mode={'pynput(global)' if use_pynput else 'terminal'}")

    try:
        while not stop_event.is_set():
            if use_pynput and listener is not None:
                try:
                    key = key_queue.get(timeout=0.25)
                except queue.Empty:
                    continue

                while True:
                    try:
                        key = key_queue.get_nowait()
                    except queue.Empty:
                        break
            else:
                key = _terminal_get_key().lower()

            if debug_keys:
                print(f"[keyboard] got key={key!r}")

            if key in QUIT_KEYS:
                print("\nExiting...")
                break

            action_id = KEY_ACTIONS.get(key)
            if action_id is None:
                continue
            if not (0 <= action_id < len(THOR_DISCRETE_ACTIONS)):
                continue

            obs, reward, terminated, truncated, info = env.step(action_id)
            action_name = info.get("action_name", THOR_DISCRETE_ACTIONS[action_id])
            success = info.get("last_action_success", True)
            pos = info.get("agent_position") or {}
            rot = info.get("agent_rotation")
            if not isinstance(pos, dict):
                pos = {}
            ry = rot.get("y", 0) if isinstance(rot, dict) else (rot or 0)

            if on_action:
                on_action(action_name, success, info)
            else:
                px, py, pz = pos.get("x") or 0, pos.get("y") or 0, pos.get("z") or 0
                pos_str = f"pos ({px:6.2f}, {py:5.2f}, {pz:6.2f})"
                rot_str = f"rot y={float(ry):6.1f}°"
                print(f"{action_name:15s}: {'✓' if success else '✗'} | {pos_str} | {rot_str}")
    finally:
        stop_event.set()
        if listener is not None:
            try:
                listener.stop()
            except Exception:
                pass

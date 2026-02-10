"""
Shared keyboard control loop for ProcTHOR demo scripts.

Supports two modes:
- Global keys: Uses pynput so WASD/QE/X work even when the AI2-THOR window is focused.
  On macOS: grant Accessibility permission for Terminal (or your Python app) if keys
  don't work when the sim window is focused.
- Terminal: Read keys from stdin only (must keep terminal focused).

Notes:
- We normalize keys to lowercase so Shift/CapsLock doesn't break controls.
- Object actions (Pickup/Open/Toggle/etc.) typically require objectId; this loop is
  navigation-only unless you extend it with object selection logic.
"""

from __future__ import annotations

import queue
import sys
import termios
import threading
import tty
from typing import Any, Callable, Optional

from dreamai.scripts.actions import THOR_DISCRETE_ACTIONS

# Map keyboard keys -> discrete action IDs (must align with THOR_DISCRETE_ACTIONS indices)
KEY_ACTIONS = {
    "w": 0,  # MoveAhead
    "s": 1,  # MoveBack
    "a": 2,  # RotateLeft
    "d": 3,  # RotateRight
    "q": 4,  # LookUp
    "e": 5,  # LookDown
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
    controller: Any,
    use_global_keys: bool = True,
    on_action: Optional[Callable[[str, bool, dict], None]] = None,
    debug_keys: bool = False,
) -> None:
    """Run the WASD/QE/X control loop until user presses X or Ctrl+C.

    Args:
        controller: AI2-THOR Controller; controller.step(action=...) will be called.
        use_global_keys: If True, try pynput so keys work when the sim window is focused.
            If pynput is not installed or fails, falls back to terminal input.
        on_action: Optional callback(action_name, success, metadata) after each step.
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

        # Normalize so Shift/CapsLock doesn't break mappings.
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

                # Drain queue — keep only newest key
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

            action_name = THOR_DISCRETE_ACTIONS[action_id]

            event = controller.step(action=action_name)
            controller.step("Pass")
            success = event.metadata.get("lastActionSuccess", False)

            agent = event.metadata.get("agent", {}) or {}
            pos = agent.get("position", {}) or {}
            rot = agent.get("rotation", {}) or {}

            if on_action:
                on_action(action_name, success, event.metadata)
            else:
                pos_str = f"pos ({pos.get('x', 0):6.2f}, {pos.get('y', 0):5.2f}, {pos.get('z', 0):6.2f})"
                rot_str = f"rot y={rot.get('y', 0):6.1f}°"
                print(f"{action_name:12s}: {'✓' if success else '✗'} | {pos_str} | {rot_str}")
    finally:
        stop_event.set()
        if listener is not None:
            try:
                listener.stop()
            except Exception:
                pass

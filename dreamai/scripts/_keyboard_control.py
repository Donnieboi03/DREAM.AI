"""Shared keyboard control loop for ProcTHOR demo scripts.

Supports two modes:
- Global keys: Uses pynput so WASD/QE/X work even when the AI2-THOR window is focused.
  On macOS: grant Accessibility permission for Terminal (or your Python app) if keys
  don't work when the sim window is focused.
- Terminal: Use --terminal to read keys from stdin only (must keep terminal focused).

Spinning cursor over the Unity window on macOS is a known Unity/AI2-THOR quirk;
try --no-fullscreen to see if it helps.
"""

from __future__ import annotations

import queue
import sys
import termios
import threading
import tty
from typing import Any, Callable, Optional

# Key -> action name
KEY_ACTIONS = {
    "w": "MoveAhead",
    "W": "MoveAhead",
    "s": "MoveBack",
    "S": "MoveBack",
    "a": "RotateLeft",
    "A": "RotateLeft",
    "d": "RotateRight",
    "D": "RotateRight",
    "q": "LookUp",
    "Q": "LookUp",
    "e": "LookDown",
    "E": "LookDown",
}

QUIT_KEYS = ("x", "X", "\x03")  # X or Ctrl+C


def _terminal_get_key() -> str:
    """Read one key from stdin (Unix/Mac). Requires terminal focus."""
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
) -> None:
    """Run the WASD/QE/X control loop until user presses X or Ctrl+C.

    Args:
        controller: AI2-THOR Controller; controller.step(action=...) will be called.
        use_global_keys: If True, try pynput so keys work when the sim window is focused.
            If pynput is not installed or fails, falls back to terminal input.
        on_action: Optional callback(action_name, success, metadata) after each step.
    """
    key_queue: queue.Queue[Optional[str]] = queue.Queue()
    stop_event = threading.Event()
    use_pynput = use_global_keys

    if use_global_keys:
        try:
            from pynput import keyboard
        except ImportError:
            use_pynput = False
            print("Tip: install 'pynput' so keys work when the simulation window is focused: pip install pynput")

    def on_press(key):
        if stop_event.is_set():
            return
        try:
            k = key.char if hasattr(key, "char") and key.char else None
        except Exception:
            k = None
        if k is not None:
            key_queue.put(k)
            if k in QUIT_KEYS:
                stop_event.set()

    listener = None
    if use_pynput:
        try:
            listener = keyboard.Listener(on_press=on_press)
            listener.daemon = True
            listener.start()
        except Exception:
            use_pynput = False

    try:
        while not stop_event.is_set():
            if use_pynput and listener is not None:
                try:
                    key = key_queue.get(timeout=0.25)
                except queue.Empty:
                    continue
            else:
                key = _terminal_get_key()
                if key in QUIT_KEYS:
                    print("\nExiting...")
                    break

            if key in QUIT_KEYS:
                print("\nExiting...")
                break

            action = KEY_ACTIONS.get(key)
            if not action:
                continue

            event = controller.step(action=action)
            success = event.metadata["lastActionSuccess"]
            meta = event.metadata.get("agent", {})
            pos = meta.get("position", {})
            rot = meta.get("rotation", {})
            if on_action:
                on_action(action, success, event.metadata)
            else:
                pos_str = f"pos ({pos.get('x', 0):6.2f}, {pos.get('y', 0):5.2f}, {pos.get('z', 0):6.2f})"
                rot_str = f"rot y={rot.get('y', 0):6.1f}°"
                print(f"{action:12s}: {'✓' if success else '✗'} | {pos_str} | {rot_str}")
    finally:
        stop_event.set()
        if listener is not None:
            try:
                listener.stop()
            except Exception:
                pass

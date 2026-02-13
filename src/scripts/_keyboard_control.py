"""
Shared keyboard control loop for ProcTHOR demo scripts.

Supports two modes:
- Global keys: Uses pynput so WASD/QE/X work even when the AI2-THOR window is focused.
  On macOS: grant Accessibility permission for Terminal (or your Python app) if keys
  don't work when the sim window is focused.
- Terminal: Read keys from stdin only (must keep terminal focused).

Notes:
- We normalize keys to lowercase so Shift/CapsLock doesn't break controls.
- Object actions (Pickup/Drop/Toggle) automatically detect and interact with
  the closest visible object in front of the agent. P=pick up, L=drop, T=toggle.
"""

from __future__ import annotations

import queue
import sys
import termios
import threading
import tty
from typing import Any, Callable, Optional

from src.scripts.actions import THOR_DISCRETE_ACTIONS


def _get_closest_pickable_object(event_metadata: dict, debug: bool = False) -> str | None:
    """Get the objectId of the closest visible, pickable object.
    
    Tries multiple strategies:
    1. interactableObjectIds (AI2-THOR marked interactive)
    2. Visible objects with pickupable property
    3. Any visible object
    """
    interactable_ids = event_metadata.get("interactableObjectIds", [])
    objects = event_metadata.get("objects", [])
    
    if debug:
        print(f"\n[DEBUG] ===== PICKUP DEBUG INFO =====")
        print(f"[DEBUG] interactableObjectIds: {interactable_ids}")
        print(f"[DEBUG] Total objects in scene: {len(objects)}")
        if objects:
            visible_objs = [obj for obj in objects if obj.get("visible", False)]
            print(f"[DEBUG] Visible objects: {len(visible_objs)}")
            print(f"[DEBUG] First 15 objects:")
            for i, obj in enumerate(objects[:15]):
                obj_id = obj.get("objectId", "NO_ID")
                visible = obj.get("visible", False)
                obj_type = obj.get("objectType", "UNKNOWN")
                pickupable = obj.get("pickupable", False)
                print(f"       [{i}] {obj_id:30s} visible={visible} type={obj_type:15s} pickupable={pickupable}")
    
    # Strategy 1: Use interactableObjectIds if available
    if interactable_ids:
        visible_interactable = [
            obj for obj in objects 
            if obj.get("objectId") in interactable_ids and obj.get("visible", False)
        ]
        if visible_interactable:
            closest = visible_interactable[0].get("objectId")
            if debug:
                print(f"[DEBUG] Strategy 1: Returning interactable object: {closest}")
            return closest
        # Fallback to first interactable even if not visible
        if debug:
            print(f"[DEBUG] Strategy 1 - returning first interactable (not visible): {interactable_ids[0]}")
        return interactable_ids[0]
    
    # Strategy 2: Look for visible pickupable objects
    if debug:
        print(f"[DEBUG] Strategy 1 failed - trying visible pickupable objects...")
    
    pickupable_visible = [
        obj for obj in objects
        if obj.get("visible", False) and obj.get("pickupable", False)
    ]
    
    if pickupable_visible:
        closest = pickupable_visible[0].get("objectId")
        if debug:
            print(f"[DEBUG] Strategy 2: Found visible pickupable: {closest}")
        return closest
    
    # Strategy 3: Just try the closest visible object (any type)
    if debug:
        print(f"[DEBUG] Strategy 2 failed - trying any visible object...")
    
    visible_objs = [obj for obj in objects if obj.get("visible", False)]
    if visible_objs:
        closest = visible_objs[0].get("objectId")
        if debug:
            print(f"[DEBUG] Strategy 3: Trying closest visible object: {closest}")
        return closest
    
    if debug:
        print(f"[DEBUG] All strategies failed - no visible objects found")
    return None


def _get_closest_toggleable_object(event_metadata: dict, debug: bool = False) -> tuple[str | None, bool]:
    """Get the objectId of the closest visible toggleable object and whether it is currently on.

    Returns:
        (objectId, is_toggled_on): objectId or None, and if the object is currently on (for calling ToggleObjectOff vs ToggleObjectOn).
    """
    interactable_ids = event_metadata.get("interactableObjectIds", [])
    objects = event_metadata.get("objects", [])

    if debug:
        print(f"\n[DEBUG] ===== TOGGLE DEBUG INFO =====")
        print(f"[DEBUG] interactableObjectIds: {interactable_ids}")
        print(f"[DEBUG] Total objects: {len(objects)}")

    # Prefer visible toggleable objects (e.g. lights, appliances)
    toggleable_visible = [
        obj for obj in objects
        if obj.get("visible", False) and obj.get("toggleable", False)
    ]
    if toggleable_visible:
        obj = toggleable_visible[0]
        obj_id = obj.get("objectId")
        is_on = obj.get("isToggled", False)
        if debug:
            print(f"[DEBUG] Closest toggleable: {obj_id} isToggled={is_on}")
        return (obj_id, is_on)

    # Fallback: interactable and visible
    if interactable_ids and objects:
        for o in objects:
            if o.get("objectId") in interactable_ids and o.get("visible", False):
                return (o.get("objectId"), o.get("isToggled", False))

    return (None, False)


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
    "t": 8,  # ToggleObjectOn (handled specially: we use On/Off based on object state)
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

            # Handle object-based actions that require objectId or have special handling
            if action_name == "PickupObject":
                # Get the closest interactable object
                closest_obj = _get_closest_pickable_object(controller.last_event.metadata, debug=debug_keys)
                if closest_obj:
                    print(f"[pickup] Attempting to pickup: {closest_obj}")
                    try:
                        event = controller.step(action=action_name, objectId=closest_obj)
                        success = event.metadata.get("lastActionSuccess", False)
                        if not success:
                            error_msg = event.metadata.get("errorMessage", "Unknown error")
                            print(f"[pickup] Failed: {error_msg}")
                    except Exception as e:
                        print(f"[pickup] Error: {e}")
                        continue
                else:
                    print(f"[pickup] No objects found to pick up")
                    continue
            elif action_name == "ToggleObjectOn":
                # Toggle: use closest toggleable object and call On or Off based on current state
                closest_obj, is_on = _get_closest_toggleable_object(controller.last_event.metadata, debug=debug_keys)
                if closest_obj:
                    toggle_action = "ToggleObjectOff" if is_on else "ToggleObjectOn"
                    print(f"[toggle] {toggle_action} on {closest_obj}")
                    try:
                        event = controller.step(action=toggle_action, objectId=closest_obj)
                        success = event.metadata.get("lastActionSuccess", False)
                        if not success:
                            error_msg = event.metadata.get("errorMessage", "Unknown error")
                            print(f"[toggle] Failed: {error_msg}")
                    except Exception as e:
                        print(f"[toggle] Error: {e}")
                        continue
                else:
                    print(f"[toggle] No toggleable object in view")
                    continue
            elif action_name == "DropHandObject":
                print(f"[drop] Attempting to drop held object")
                try:
                    event = controller.step(action=action_name, forceAction=True)
                    success = event.metadata.get("lastActionSuccess", False)
                    if not success:
                        error_msg = event.metadata.get("errorMessage", "Unknown error")
                        print(f"[drop] Failed: {error_msg}")
                except Exception as e:
                    print(f"[drop] Error: {e}")
                    continue
            else:
                event = controller.step(action=action_name)
                success = event.metadata.get("lastActionSuccess", False)
            
            controller.step("Pass")

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

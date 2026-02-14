"""AI2-THOR Gymnasium environment wrapper."""

from __future__ import annotations

from typing import Any, Optional

import gymnasium as gym
import numpy as np
from tools.actions import THOR_DISCRETE_ACTIONS


def _get_closest_pickable_object(metadata: dict) -> Optional[str]:
    """Get objectId of closest visible pickable object from event metadata."""
    interactable_ids = metadata.get("interactableObjectIds", [])
    objects = metadata.get("objects", [])
    if interactable_ids:
        visible = [o for o in objects if o.get("objectId") in interactable_ids and o.get("visible")]
        if visible:
            return visible[0].get("objectId")
        return interactable_ids[0] if interactable_ids else None
    pickupable = [o for o in objects if o.get("visible") and o.get("pickupable")]
    if pickupable:
        return pickupable[0].get("objectId")
    visible = [o for o in objects if o.get("visible")]
    return visible[0].get("objectId") if visible else None


def _get_closest_toggleable_object(metadata: dict) -> tuple[Optional[str], bool]:
    """Get (objectId, is_toggled_on) for closest visible toggleable object."""
    interactable_ids = metadata.get("interactableObjectIds", [])
    objects = metadata.get("objects", [])
    toggleable = [o for o in objects if o.get("visible") and o.get("toggleable")]
    if toggleable:
        o = toggleable[0]
        return (o.get("objectId"), o.get("isToggled", False))
    if interactable_ids and objects:
        for o in objects:
            if o.get("objectId") in interactable_ids and o.get("visible"):
                return (o.get("objectId"), o.get("isToggled", False))
    return (None, False)

def _get_ai2thor_controller(
    scene_name: Optional[str] = None,
    existing_controller: Any = None,
    width: int = 300,
    height: int = 300,
    quality: str = "Very High",
    **kwargs: Any,
) -> Any:
    """Return an AI2-THOR controller (existing or new)."""
    if existing_controller is not None:
        return existing_controller
    from ai2thor.controller import Controller

    init_params: dict[str, Any] = dict(
        width=width,
        height=height,
        quality=quality,
        **kwargs,
    )
    if scene_name is not None:
        init_params["scene"] = scene_name
    controller = Controller(**init_params)
    return controller


class ThorEnv(gym.Env):
    """Gymnasium environment wrapping an AI2-THOR controller."""

    metadata = {"render_modes": ["rgb_array"]}

    def __init__(
        self,
        scene_name: Optional[str] = None,
        controller: Any = None,
        width: int = 300,
        height: int = 300,
        max_steps: int = 500,
        reward_on_success: float = 1.0,
        render_mode: Optional[str] = None,
        **controller_kwargs: Any,
    ):
        """Build ThorEnv from a scene name (iTHOR) or an existing controller (e.g. ProcTHOR)."""
        super().__init__()
        self._scene_name = scene_name
        self._controller = _get_ai2thor_controller(
            scene_name=scene_name,
            existing_controller=controller,
            width=width,
            height=height,
            **controller_kwargs,
        )
        self._width = width
        self._height = height
        self._max_steps = max_steps
        self._reward_on_success = reward_on_success
        self._step_count = 0
        self._last_event = None
        self.render_mode = render_mode

        # Discrete action space: 9 actions
        self.action_space = gym.spaces.Discrete(len(THOR_DISCRETE_ACTIONS))
        # Observation: RGB image only (H, W, 3)
        self.observation_space = gym.spaces.Box(
            low=0,
            high=255,
            shape=(height, width, 3),
            dtype=np.uint8,
        )

    def _thor_step(self, action_name: str, **kwargs: Any) -> Any:
        """Run one THOR step and return the event. On ValueError (invalid action), use controller's last_event."""
        try:
            event = self._controller.step(dict(action=action_name, **kwargs))
            self._last_event = event
            return event
        except ValueError:
            # e.g. DropHandObject with nothing in hand; controller already set last_event with error metadata
            self._last_event = getattr(self._controller, "last_event", self._last_event)
            return self._last_event

    def _get_frame(self) -> np.ndarray:
        """Return current RGB frame from last event."""
        if self._last_event is None:
            return np.zeros((self._height, self._width, 3), dtype=np.uint8)
        frame = getattr(self._last_event, "frame", None)
        if frame is None:
            return np.zeros((self._height, self._width, 3), dtype=np.uint8)
        return np.asarray(frame, dtype=np.uint8)

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[dict] = None,
    ) -> tuple[np.ndarray, dict]:
        """Reset the environment. For iTHOR, reset(scene); for ProcTHOR controller is already loaded."""
        super().reset(seed=seed)
        self._step_count = 0
        if self._scene_name is not None and self._controller is not None:
            self._controller.reset(self._scene_name)
            self._last_event = self._controller.step(
                dict(action="Initialize", gridSize=0.25)
            )
        elif self._last_event is None and self._controller is not None:
            self._last_event = self._controller.step(
                dict(action="Initialize", gridSize=0.25)
            )
        obs = self._get_frame()
        meta = getattr(self._last_event, "metadata", None) or {}
        agent = meta.get("agent") or {}
        info = {
            "agent_position": agent.get("position"),
            "agent_rotation": agent.get("rotation"),
        }
        return obs, info

    def step(self, action: int) -> tuple[np.ndarray, float, bool, bool, dict]:
        """Step with a discrete action index. Pickup/Toggle/Drop resolve objectId from metadata."""
        action_name = THOR_DISCRETE_ACTIONS[action]
        meta = getattr(self._last_event, "metadata", None) or {} if self._last_event else {}

        # Object-based actions require objectId (and Drop uses forceAction)
        if action_name == "PickupObject":
            obj_id = _get_closest_pickable_object(meta)
            if obj_id:
                self._thor_step(action_name, objectId=obj_id)
            else:
                self._thor_step("Pass")  # No target; no-op
        elif action_name == "ToggleObjectOn":
            obj_id, is_on = _get_closest_toggleable_object(meta)
            if obj_id:
                toggle_action = "ToggleObjectOff" if is_on else "ToggleObjectOn"
                self._thor_step(toggle_action, objectId=obj_id)
            else:
                self._thor_step("Pass")
        elif action_name == "DropHandObject":
            self._thor_step(action_name, forceAction=True)
        else:
            self._thor_step(action_name)

        self._step_count += 1
        obs = self._get_frame()
        reward = 0.0
        terminated = False
        meta = getattr(self._last_event, "metadata", None) or {}
        last_success = meta.get("lastActionSuccess", False)
        if last_success and action_name in ("PickupObject", "ToggleObjectOn", "ToggleObjectOff", "DropHandObject"):
            reward += 0.1
        if self._step_count >= self._max_steps:
            truncated = True
        else:
            truncated = False
        agent = meta.get("agent") or {}
        info = {
            "step": self._step_count,
            "last_action_success": last_success,
            "action_name": action_name,
            "agent_position": agent.get("position"),
            "agent_rotation": agent.get("rotation"),
        }
        return obs, reward, terminated, truncated, info

    def render(self) -> Optional[np.ndarray]:
        """Return current RGB frame if render_mode is rgb_array."""
        if self.render_mode == "rgb_array":
            return self._get_frame()
        return None

    def close(self) -> None:
        """Stop the controller."""
        if self._controller is not None:
            try:
                self._controller.stop()
            except Exception:
                pass
            self._controller = None

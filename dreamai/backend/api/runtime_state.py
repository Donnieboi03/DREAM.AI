"""Runtime state shared across API modules."""

from __future__ import annotations

from typing import Any, Optional

from envs.ai2thor.procthor_adapter import get_builtin_scene_names, get_ithor_scene_names

_game_env: Optional[Any] = None


def set_game_env(env: Any) -> None:
    global _game_env
    _game_env = env


def get_scene_names() -> Optional[list[str]]:
    if not _game_env:
        return None
    controller = getattr(_game_env, "_controller", None)
    if not controller:
        return None
    return get_ithor_scene_names(controller) or get_builtin_scene_names(controller)

"""
Adapter for rl_thor Graph Tasks and reward handling.
Uses rl_thor's CustomGraphTask and GraphTaskRewardHandler when available.
"""

from __future__ import annotations

from typing import Any, Optional, Tuple

_RL_THOR_AVAILABLE = False
_CustomGraphTask = None
_parse_task_description_dict = None
_GraphTaskRewardHandler = None

try:
    from rl_thor.envs.tasks.tasks import CustomGraphTask
    from rl_thor.envs.tasks.tasks_interface import GraphTaskRewardHandler, parse_task_description_dict

    _RL_THOR_AVAILABLE = True
    _CustomGraphTask = CustomGraphTask
    _parse_task_description_dict = parse_task_description_dict
    _GraphTaskRewardHandler = GraphTaskRewardHandler
except ImportError:
    pass


def is_rl_thor_available() -> bool:
    """Return True if rl_thor is installed and importable."""
    return _RL_THOR_AVAILABLE


def create_graph_task_and_reward_handler(
    task_description_dict: dict[str, Any],
    no_task_advancement_rewards: bool = False,
) -> Optional[Tuple[Any, Any]]:
    """
    Create a CustomGraphTask and GraphTaskRewardHandler from task_description_dict.

    Returns (task, reward_handler) if rl_thor is available and creation succeeds,
    else None.
    """
    if not _RL_THOR_AVAILABLE or not _CustomGraphTask or not _GraphTaskRewardHandler:
        return None
    try:
        task = _CustomGraphTask(task_description_dict)
        reward_handler = _GraphTaskRewardHandler(task, no_task_advancement_rewards=no_task_advancement_rewards)
        return (task, reward_handler)
    except Exception as e:
        print(f"[rl_thor_adapter] Failed to create graph task: {e}")
        return None

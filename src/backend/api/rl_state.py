"""Shared RL agent process state for rl_routes and websocket_stream."""

_rl_process = None


def set_rl_process(proc) -> None:
    global _rl_process
    _rl_process = proc


def get_rl_process():
    return _rl_process


def is_rl_agent_running() -> bool:
    return _rl_process is not None and _rl_process.poll() is None

"""API routes for RL agent process management."""

import os
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/rl", tags=["rl"])

# Global process handle; only one RL agent process at a time
_rl_process = None

# Resolve path to run rl.run_agent from project src
def _get_rl_agent_cwd() -> Path:
    """Return directory from which 'python -m rl.run_agent' can run."""
    # This file: backend/api/rl_routes.py -> src/backend/api/rl_routes.py
    api_dir = Path(__file__).resolve().parent
    backend_dir = api_dir.parent
    return backend_dir.parent  # src/


def _is_running() -> bool:
    return _rl_process is not None and _rl_process.poll() is None


@router.get("/status")
async def rl_status() -> dict:
    """Return whether the RL agent process is running."""
    return {"running": _is_running()}


@router.post("/start")
async def rl_start() -> dict:
    """Start the RL agent process. No-op if already running."""
    global _rl_process
    if _is_running():
        return {"running": True, "message": "Agent already running"}

    cwd = _get_rl_agent_cwd()
    ws_url = os.environ.get("DREAMAI_WS_URL", "ws://localhost:8000/ws/game")

    try:
        _rl_process = subprocess.Popen(
            [sys.executable, "-m", "rl.run_agent", "--url", ws_url],
            cwd=str(cwd),
            env={**os.environ, "PYTHONPATH": str(cwd)},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        return {"running": True, "message": "Agent started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def rl_stop() -> dict:
    """Stop the RL agent process. No-op if not running."""
    global _rl_process
    if not _is_running():
        return {"running": False, "message": "Agent not running"}

    try:
        _rl_process.terminate()
        _rl_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _rl_process.kill()
    except Exception:
        pass
    _rl_process = None
    return {"running": False, "message": "Agent stopped"}

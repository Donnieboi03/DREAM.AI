"""API routes for RL agent process management and model import/export."""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from fastapi import APIRouter, Body, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from . import rl_state


class RLStartRequest(BaseModel):
    policy_mode: Optional[str] = None
    network_size: Optional[str] = None

router = APIRouter(prefix="/api/rl", tags=["rl"])

# Model storage path
def _get_model_dir() -> Path:
    base = Path(os.environ.get("DREAMAI_RL_MODELS", "~/.dreamai/rl_models")).expanduser()
    base.mkdir(parents=True, exist_ok=True)
    return base


CURRENT_MODEL_NAME = "current_model.zip"


def _is_valid_sb3_model(path: Path) -> bool:
    """Validate that path is a valid SB3 model (.zip with data and policy.pth)."""
    if not path.suffix.lower() == ".zip" and not path.name.endswith(".zip"):
        return False
    try:
        import zipfile
        with zipfile.ZipFile(path, "r") as zf:
            names = zf.namelist()
            return "data" in names and any("policy" in n and n.endswith(".pth") for n in names)
    except Exception:
        return False


# Resolve path to run rl.run_agent from project src
def _get_rl_agent_cwd() -> Path:
    """Return directory from which 'python -m rl.run_agent' can run."""
    api_dir = Path(__file__).resolve().parent
    backend_dir = api_dir.parent
    return backend_dir.parent  # src/


@router.get("/status")
async def rl_status() -> dict:
    """Return whether the RL agent process is running."""
    return {"running": rl_state.is_rl_agent_running()}


@router.get("/model/status")
async def rl_model_status() -> dict:
    """Return whether a model exists for export."""
    model_path = _get_model_dir() / CURRENT_MODEL_NAME
    return {"has_model": model_path.exists()}


@router.post("/model/import")
async def rl_model_import(file: UploadFile = File(...)) -> dict:
    """Import an SB3 model. Validates format; returns 400 if invalid."""
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Invalid file type")
    try:
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = Path(tmp.name)
        try:
            if not _is_valid_sb3_model(tmp_path):
                raise HTTPException(status_code=400, detail="Invalid file type")
            dest = _get_model_dir() / CURRENT_MODEL_NAME
            shutil.copy2(tmp_path, dest)
            return {"ok": True, "message": "Model imported"}
        finally:
            tmp_path.unlink(missing_ok=True)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/export")
async def rl_model_export():
    """Export the current model as a .zip download. 404 if no model exists."""
    model_path = _get_model_dir() / CURRENT_MODEL_NAME
    if not model_path.exists():
        raise HTTPException(status_code=404, detail="No model to export")
    return FileResponse(
        path=str(model_path),
        media_type="application/zip",
        filename="dreamai_model.zip",
    )


@router.post("/start")
async def rl_start(req: RLStartRequest | None = Body(default=None)) -> dict:
    """Start the RL agent process. No-op if already running."""
    if rl_state.is_rl_agent_running():
        return {"running": True, "message": "Agent already running"}

    req = req or RLStartRequest()

    cwd = _get_rl_agent_cwd()
    ws_url = os.environ.get("DREAMAI_WS_URL", "ws://localhost:8000/ws/game")
    model_path = _get_model_dir() / CURRENT_MODEL_NAME

    cmd = [sys.executable, "-m", "rl.run_agent", "--url", ws_url]
    env = {**os.environ, "PYTHONPATH": str(cwd)}

    if model_path.exists():
        cmd.extend(["--model-path", str(model_path)])
    else:
        policy_mode = req.policy_mode
        network_size = req.network_size
        if policy_mode and policy_mode in ("default", "fast", "sample_efficient", "exploration"):
            cmd.extend(["--policy-mode", policy_mode])
        if network_size and network_size in ("small", "medium", "large"):
            cmd.extend(["--network-size", network_size])

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        rl_state.set_rl_process(proc)
        return {"running": True, "message": "Agent started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def rl_stop() -> dict:
    """Stop the RL agent process. No-op if not running."""
    if not rl_state.is_rl_agent_running():
        return {"running": False, "message": "Agent not running"}

    proc = rl_state.get_rl_process()
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    except Exception:
        pass
    rl_state.set_rl_process(None)
    return {"running": False, "message": "Agent stopped"}

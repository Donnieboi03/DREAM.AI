# DREAM.AI

An agentic framework for training robust RL brains, in Simulated Environments.

## Run with Docker + VNC (one command, any OS)

From the repo root (after building once: `docker build -t dreamai-thor .`):

```bash
python run_vnc.py
```

Then open **http://localhost:6080/vnc.html** in your browser. To use a different scene: `python run_vnc.py FloorPlan201`. See **QUICKSTART_WINDOWS.md** for full steps.

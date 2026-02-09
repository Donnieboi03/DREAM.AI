# Quick start (Windows, Linux, macOS)

Use this folder as the project root (the folder that contains `Dockerfile`, `dreamai/`, and `run_vnc.py`).

## 1. Build the image (once)

From the project root:

```bash
docker build -t dreamai-thor .
```

Wait until the build finishes without errors. Rebuild only when you change the Dockerfile or `dreamai/requirements.txt`.

## 2. Run (one command on any system)

From the project root, run:

```bash
python run_vnc.py
```

This works on **Windows, Linux, and macOS**. It mounts your repo into the container (no rebuild when you change code or scene) and starts THOR with the default scene (FloorPlan1 = kitchen).

**Change scene:** pass the scene name as an argument, then rerun (no rebuild):

```bash
python run_vnc.py FloorPlan201
python run_vnc.py FloorPlan301
```

Examples: `FloorPlan1` (kitchen), `FloorPlan201` (living room), `FloorPlan301` (bedroom), `FloorPlan401` (bathroom).

Leave the terminal open. You should see "VNC is running..." and controller output.

## 3. Open in browser

Open: **http://localhost:6080/vnc.html**

You should see the THOR scene after the controller loads it. Use WASD / Q,E in the VNC window (click the canvas first so it has focus).

## If something fails

- **Build fails:** Ensure Docker is installed and running. Run `docker build` from the project root (the folder containing `Dockerfile`).
- **"docker: command not found" or run_vnc.py fails:** Install Docker and ensure it is on your PATH.
- **Container exits immediately:** Check the terminal for Python errors (e.g. missing package, dataset download). Rebuild the image if you changed the Dockerfile or requirements.
- **VNC shows only splash:** The controller may have crashed before loading the scene. Check the terminal for tracebacks.

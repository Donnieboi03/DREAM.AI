# Docker + VNC (mainly for Windows)

Run the DreamAI ProcTHOR/THOR stack in a container and view the simulation in your browser. This is the recommended way to run on **Windows**; it also works on Linux and macOS.

Use the **project root** as the folder that contains `dreamai/` and `docker/` (one level up from this folder).

---

## 1. Build the image (once)

From the **repo root**:

```bash
docker build -t dreamai-thor -f docker/Dockerfile .
```

On **Apple Silicon (M1/M2/M3)** use the amd64 platform:

```bash
docker build --platform=linux/amd64 -t dreamai-thor -f docker/Dockerfile .
```

Rebuild only when you change `docker/Dockerfile` or `dreamai/requirements.txt`.

---

## 2. Run (one command)

From the **repo root**:

```bash
python docker/run_vnc.py
```

This mounts your repo into the container (no rebuild when you change code or scene) and starts THOR with the default scene (FloorPlan1 = kitchen).

**Change scene:** pass the scene name as an argument:

```bash
python docker/run_vnc.py FloorPlan201
python docker/run_vnc.py FloorPlan301
```

Examples: `FloorPlan1` (kitchen), `FloorPlan201` (living room), `FloorPlan301` (bedroom).

Leave the terminal open. You should see "VNC is running..." and controller output.

---

## 3. Open in browser

Open: **http://localhost:6080/vnc.html**

Use the **host port** you mapped (default 6080). If 6080 or 15900 were in use, the script uses alternate ports and prints the URL; or set:

```bash
DREAMAI_VNC_WEB_PORT=6081 DREAMAI_VNC_RAW_PORT=15901 python docker/run_vnc.py
```

Then open **http://localhost:6081/vnc.html**.

In the noVNC window, click the canvas to give it focus, then use **WASD** / **Q,E** to move and look. **X** to quit.

---

## If something fails

- **Build fails:** Ensure Docker is installed and running. Run the build from the repo root (the folder that contains `dreamai/` and `docker/`).
- **"docker: command not found" or run_vnc.py fails:** Install Docker and ensure it is on your PATH.
- **Port already allocated:** Use `DREAMAI_VNC_WEB_PORT=6081 DREAMAI_VNC_RAW_PORT=15901` (or other free ports) when running `python docker/run_vnc.py`.
- **Container exits immediately:** Check the terminal for Python errors. Rebuild the image if you changed the Dockerfile or requirements.
- **VNC shows only splash:** The controller may have crashed before loading the scene. Check the terminal for tracebacks. See **VNC_AND_THOR.md** in this folder for why the THOR player shows a splash until the controller sends a scene.

---

## Why the THOR splash screen?

Over VNC you run the AI2-THOR **player**, which boots into a splash scene and waits for the Python controller to send the scene. The script started by the container is that controller. See **VNC_AND_THOR.md** in this folder for the full Editor-vs-Player explanation.

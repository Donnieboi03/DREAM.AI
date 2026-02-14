# Docker + VNC (mainly for Windows)

Run the DreamAI ProcTHOR/THOR stack in a container and view the simulation in your browser. This is the recommended way to run on **Windows**; it also works on Linux and macOS.

Use the **project root** as the folder that contains `src/` and `docker/` (one level up from this folder).

---

## Testing image (Dockerfile.testing)

**Dockerfile.testing** is used to build an image for running tests and the full DreamAI stack (ProcTHOR, VNC, dependencies). It installs DreamAI requirements and ProcTHOR from the official repo, and is set up for starting the testing environment (e.g. VNC + THOR).

**Build the testing image** from the **repo root**:

- **Apple Silicon (M1/M2/M3):** use `--platform=linux/amd64`:

```bash
docker build --platform=linux/amd64 -f docker/Dockerfile.testing -t my-ai2thor-image .
```

- **Linux / Windows (x86_64):** no platform flag needed:

```bash
docker build -f docker/Dockerfile.testing -t my-ai2thor-image .
```

**Run the testing container** from the **repo root** (repo is mounted so the E2E script runs):

- **Apple Silicon (M1/M2/M3):** use `--platform=linux/amd64` so the THOR Unity player runs correctly:

```bash
docker run --rm -it -p 6080:6080 -p 5900:5900 -v "$(pwd)":/src \
  -e GEMINI_API_KEY="${GEMINI_API_KEY}" \
  --platform=linux/amd64 \
  my-ai2thor-image
```

- **Linux / Windows (x86_64):** no platform flag needed:

```bash
docker run --rm -it -p 6080:6080 -p 5900:5900 -v "$(pwd)":/src \
  -e GEMINI_API_KEY="${GEMINI_API_KEY}" \
  my-ai2thor-image
```

You can pass `GOOGLE_API_KEY` instead of `GEMINI_API_KEY`; the E2E script uses either for the Orchestrator and Scene generator LLMs. If you have a `.env` in the repo root with the key, mounting the repo (`-v "$(pwd)":/src`) makes it available and `start_vnc.sh` loads it—or pass `-e GEMINI_API_KEY=...` to override.

**Parameters passed to the container (env vars):**

| Env var | Purpose |
|--------|--------|
| `GEMINI_API_KEY` or `GOOGLE_API_KEY` | Used by the E2E script for LLM calls (Orchestrator + Scene generator). Omit or use `--no-llm` in the script to skip LLM. |
| `DREAMAI_VNC_SCENE` | Scene name (e.g. `FloorPlan1`, `FloorPlan201`) if the controller uses it. |
| `SCREEN_RESOLUTION` | Xvfb resolution; default `1280x720x24`. |

The E2E prompt (e.g. "I want a big house with 12 rooms") is currently fixed in `docker/start_vnc.sh`; edit that line to change the user prompt.

Rebuild when you change `Dockerfile.testing` or `src/requirements.txt`.

---

## Building with GraphTask (rl_thor)

DREAM.AI uses [rl_thor](https://github.com/JulianPaquerot/rl_thor) (MIT) for GraphTask-based reward computation when training RL agents. rl_thor is included in `third_party/rl_thor` and is installed automatically during Docker builds.

**Requirements:**
- Ensure `third_party/rl_thor` exists in the repo (it is copied or added as a submodule).
- All Docker images use Python 3.12 to satisfy rl_thor's requirement.

**Docker:** No extra steps. Build as usual; rl_thor is installed from `third_party/rl_thor`.

**Local development (non-Docker):**
```bash
cd /path/to/DREAM.AI
pip install -r src/requirements.txt
pip install -e third_party/rl_thor
```

---

## 1. Build the image (once)

From the **repo root**:

```bash
docker build -t src-thor -f docker/Dockerfile .
```

On **Apple Silicon (M1/M2/M3)** use the amd64 platform:

```bash
docker build --platform=linux/amd64 -t src-thor -f docker/Dockerfile .
```

Rebuild only when you change `docker/Dockerfile` or `src/requirements.txt`.

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

- **Build fails:** Ensure Docker is installed and running. Run the build from the repo root (the folder that contains `src/` and `docker/`).
- **"docker: command not found" or run_vnc.py fails:** Install Docker and ensure it is on your PATH.
- **Port already allocated:** Use `DREAMAI_VNC_WEB_PORT=6081 DREAMAI_VNC_RAW_PORT=15901` (or other free ports) when running `python docker/run_vnc.py`.
- **Container exits immediately:** Check the terminal for Python errors. Rebuild the image if you changed the Dockerfile or requirements.
- **VNC shows only splash:** The controller may have crashed before loading the scene. Check the terminal for tracebacks. See **VNC_AND_THOR.md** in this folder for why the THOR player shows a splash until the controller sends a scene.

---

## Why the THOR splash screen?

Over VNC you run the AI2-THOR **player**, which boots into a splash scene and waits for the Python controller to send the scene. The script started by the container is that controller. See **VNC_AND_THOR.md** in this folder for the full Editor-vs-Player explanation.

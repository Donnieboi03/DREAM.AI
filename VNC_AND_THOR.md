# VNC and AI2-THOR: Editor vs Player

## Root cause (one sentence)

**Over VNC/Linux you are running the AI2-THOR Unity *player* (e.g. `thor-Linux64`), which always boots into its own splash/bootstrap scene and waits for a controller command to load a scene — unlike the Unity *Editor* you may run locally on macOS, where the open scene stays active and no THOR bootstrap runs.**

Nothing is broken; you are just using a different runtime with different rules.

---

## What you see

| Environment | What runs | What you see |
|-------------|-----------|--------------|
| **Local (e.g. macOS)** | Unity **Editor** | The scene you had open stays active. Controls work immediately. No THOR bootstrap. |
| **VNC / Linux (Docker, headless)** | AI2-THOR **player** (`thor-Linux64`) | THOR launches → brief default/house-like scene → **splash/bootstrap scene** → stays there until the controller tells it which scene to load. Keyboard/mouse are captured by the player window. |

So on VNC:

1. THOR launches.
2. It briefly shows a default scene, then switches to the **THOR splash/bootstrap scene**.
3. It **stays there** until the **AI2-THOR controller** (Python, over socket) sends a command to load a specific environment (e.g. a ProcTHOR house).

Your custom scene is not “authoritative” in the player: the player’s startup logic and scene order take over until the controller issues the load.

---

## Correct workflow over VNC

The **controller must run** and must be the process that starts (or connects to) the THOR player and sends the scene. In this repo that is the Python script that creates `Controller(scene=...)` and runs the keyboard loop.

1. Start the VNC stack (virtual display, window manager, x11vnc, noVNC) — e.g. via `start_vnc.sh`.
2. **Then** run the controller script (e.g. `run_proc_test.py`) in the same environment (same `DISPLAY`, same machine).  
   The script will start the THOR player (or connect to it), send the house/scene, and then you should see the house load in the VNC session.

Do **not** start the THOR player binary by itself and expect a scene to load; without the controller, it will remain on the bootstrap/splash screen.

---

## What to do to fix it

1. **Let the controller start the player**  
   Do not run `thor-Linux64` (or any THOR executable) yourself. Only run the Python controller script (e.g. `run_proc_test.py`). It will start the player and send the scene.

2. **Use `start_vnc.sh` as the single entrypoint**  
   Run `start_vnc.sh` from the **repo root**. It starts the display, VNC, then runs the controller. The script sets `PYTHONPATH` and `DISPLAY` so the controller can import `dreamai` and the player appears on the VNC display.

3. **ProcTHOR house shows "street" on Linux/VNC**  
   On the Linux THOR build, loading a ProcTHOR house (scene=house dict) often leaves you in the default **street view** (houses on both sides) instead of the interior. The controller reports success but the rendered scene is wrong. **Workaround:** use a built-in iTHOR scene for VNC. The repo’s `start_vnc.sh` sets `DREAMAI_VNC_TEST=1`, which loads **FloorPlan1** (a kitchen) and works on Linux. For the ProcTHOR house, run the script locally (e.g. on Mac) or omit `DREAMAI_VNC_TEST` and accept the street view on Linux until the build supports CreateHouse properly.

4. **If the controller never loads any scene**  
   - **Watch the terminal:** Run the container with `docker run --rm -it -p 6080:6080 -p 15900:5900 dreamai-thor`. You should see `[run_proc_test]` messages. If they stop before "Controller created" or "Scene loaded", note where they stop and any traceback.  
   - With `DREAMAI_VNC_TEST=1` you should see the kitchen (FloorPlan1). If you still see only splash, the issue is display, build, or Controller startup.

---

## Summary

| | Unity Editor (local) | THOR player (VNC/Linux) |
|---|----------------------|--------------------------|
| **Who decides the scene** | Whatever scene you have open in the Editor | The controller (Python) via `Controller(scene=...)` |
| **Startup** | Editor opens your project/scene | Player boots → splash → waits for controller |
| **Input** | Editor and your app | Player window captures keyboard/mouse |

So: **the VNC setup launches the AI2-THOR Unity player, which always forces its own startup scene and requires a controller command to load your house** — unlike the Unity Editor you run locally.

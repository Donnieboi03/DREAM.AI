#!/usr/bin/env bash
set -e

# Repo root (parent of docker/); required for dreamai/ paths and PYTHONPATH
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="${ROOT}${PYTHONPATH:+:$PYTHONPATH}"

# Load .env from repo root if present (GEMINI_API_KEY, GOOGLE_API_KEY, etc.)
# You can also pass these via docker run -e GEMINI_API_KEY=... (takes precedence)
if [ -f "${ROOT}/.env" ]; then
  set -a
  # shellcheck source=/dev/null
  . "${ROOT}/.env"
  set +a
fi

export DISPLAY=:99
export SCREEN_RESOLUTION="${SCREEN_RESOLUTION:-1280x720x24}"

# 1) Virtual display
Xvfb :99 -screen 0 ${SCREEN_RESOLUTION} -ac +extension GLX +render -noreset &
sleep 1

# 2) Window manager (so Unity has a desktop to draw on)
fluxbox >/tmp/fluxbox.log 2>&1 &
sleep 1

# 3) VNC server exposing DISPLAY=:99
#    -nopw = no password (fine locally; add a password if you want)
x11vnc -display :99 -forever -shared -nopw -rfbport 5900 >/tmp/x11vnc.log 2>&1 &
sleep 1

# 4) noVNC -> browser access on port 6080
# On Debian/Ubuntu, novnc web client lives at /usr/share/novnc/
websockify --web=/usr/share/novnc/ 6080 localhost:5900 >/tmp/novnc.log 2>&1 &
sleep 1

echo "VNC is running:"
echo " - Browser: http://localhost:6080/vnc.html"
echo " - Raw VNC: localhost:5900"
echo

# 5) Start the AI2-THOR *controller* (Python). This launches the thor-Linux64 player,
#    sends the scene to load, and runs the keyboard loop.
#
# Supported env (pass via docker run -e or in mounted .env):
#   GEMINI_API_KEY or GOOGLE_API_KEY  - for Orchestrator + Scene generator LLM (optional; use --no-llm in script to skip)
#   DREAMAI_VNC_SCENE                 - e.g. FloorPlan1, FloorPlan201 (used if script uses it)
#   SCREEN_RESOLUTION                 - Xvfb resolution, default 1280x720x24
#
# Script argument below is the E2E user prompt (fixed here; override by changing this line or the script).
export PYTHONUNBUFFERED=1
export DREAMAI_VNC_TEST=4
[ -n "${DREAMAI_VNC_SCENE:-}" ] && echo "Scene: ${DREAMAI_VNC_SCENE}"
[ -n "${GEMINI_API_KEY:-}${GOOGLE_API_KEY:-}" ] && echo "API key set (LLM enabled)."
echo "Starting Python controller (watch for [run_proc_test] messages below)..."
python dreamai/scripts/run_llm_house_e2e.py "I want a big house with 12 rooms"
#ython dreamai/scripts/run_proc_test.py 
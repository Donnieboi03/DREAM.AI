#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$HOME/DREAM.AI"
echo "[bootstrap] BOOTSTRAP_MARKER: O"

# --- Ensure docker ---
if ! command -v docker >/dev/null 2>&1; then
  echo "[bootstrap] Installing docker..."
  apt update
  apt install -y docker.io
  systemctl enable --now docker
fi

# --- Ensure NVIDIA container toolkit (for --gpus all) ---
if ! dpkg -s nvidia-container-toolkit >/dev/null 2>&1; then
  echo "[bootstrap] Installing nvidia-container-toolkit..."
  apt update
  apt install -y nvidia-container-toolkit
  systemctl restart docker
fi

# --- GPU sanity checks ---
echo "[bootstrap] Host GPU (nvidia-smi):"
nvidia-smi || true

echo "[bootstrap] Docker GPU test (nvidia-smi inside container):"
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

echo "[bootstrap] docker + gpu ready (no build/run yet)"

echo "[bootstrap] Computing dep hash..."
DEP_HASH="$(cat Dockerfile requirements.txt | sha256sum | awk '{print $1}')"
IMAGE="dreamai:${DEP_HASH}"

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "[bootstrap] Building image $IMAGE"
  cd "$REPO_DIR"
  docker build -t "$IMAGE" .
else
  echo "[bootstrap] Using cached image $IMAGE"
fi

# --- Dedicated X display for AI2-THOR (avoid :0 auth issues) ---
HOST_VENV="/opt/dreamai_host_venv"
THOR_DISPLAY=":1"

apt update
apt install -y python3 python3-venv python3-pip

# Create venv + install ai2thor-xorg if missing
if [ ! -x "$HOST_VENV/bin/ai2thor-xorg" ]; then
  echo "[bootstrap] Creating host venv for ai2thor-xorg..."
  python3 -m venv "$HOST_VENV"
  "$HOST_VENV/bin/pip" install --no-input --upgrade pip setuptools wheel
  "$HOST_VENV/bin/pip" install --no-input ai2thor
fi

# Start ai2thor-xorg on display :1 (idempotent-ish)
echo "[bootstrap] Starting ai2thor-xorg on $THOR_DISPLAY ..."
"$HOST_VENV/bin/ai2thor-xorg" start 1 || true

export DISPLAY="$THOR_DISPLAY"
echo "[bootstrap] DISPLAY=$DISPLAY"
ls -la /tmp/.X11-unix || true

# Hard check: ensure the socket exists
if [ ! -S /tmp/.X11-unix/X1 ]; then
  echo "[bootstrap] ERROR: /tmp/.X11-unix/X1 not found; ai2thor-xorg may have failed."
  echo "[bootstrap] Showing error log if present:"
  tail -n 200 /var/log/ai2thor-xorg-error.1.log 2>/dev/null || true
  exit 1
fi


echo "[bootstrap] Running DreamAI container (ai2thor smoke test)..."
docker run --rm --gpus all \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$REPO_DIR:/workspace" \
  -w /workspace \
  "$IMAGE" \
  python3 -c "from ai2thor.controller import Controller; c=Controller(scene='FloorPlan1'); c.step('Pass'); c.stop(); print('ai2thor OK')"
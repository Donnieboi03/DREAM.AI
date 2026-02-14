#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/Donnieboi03/DREAM.AI.git"
REPO_DIR="$HOME/DREAM.AI"
BRANCH="vm_testing"

echo "[bootstrap] started"
echo "[bootstrap] Hostname: $(hostname)"
echo "[bootstrap] User: $(whoami)"
echo "[bootstrap] Repo dir: $REPO_DIR"

if ! command -v git >/dev/null 2>&1; then
  echo "[bootstrap] Git not found. Installing..."
  apt update
  apt install -y git
else
  echo "[bootstrap] Git already installed."
fi

# 1) Ensure repo exists
if [ ! -d "$REPO_DIR/.git" ]; then
  echo "[bootstrap] Repo not found. Cloning..."
  git clone "$REPO_URL" "$REPO_DIR"
else
  echo "[bootstrap] Repo already exists."
fi

# 2) Hard sync to remote (deterministic)
cd "$REPO_DIR"
echo "[bootstrap] Fetching + hard resetting to origin/$BRANCH..."
git fetch origin
git clean -fd
git checkout -B "$BRANCH" "origin/$BRANCH"
git reset --hard "origin/$BRANCH"

# 3) Print what commit we are on
echo "[bootstrap] Current commit: $(git rev-parse --short HEAD)"
echo "[bootstrap] repo sync complete (no docker yet)"

exec bash "$REPO_DIR/src/vm_bootstrap_main.sh"
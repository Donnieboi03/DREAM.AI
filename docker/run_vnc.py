#!/usr/bin/env python3
"""Run the DreamAI THOR container with VNC. Mainly for Windows; works on Linux/macOS too.

Usage (from repo root):
  python docker/run_vnc.py              # default scene FloorPlan1 (kitchen)
  python docker/run_vnc.py FloorPlan201 # living room
  python docker/run_vnc.py FloorPlan301 # bedroom

If ports 6080 or 15900 are in use, set env vars and run again, e.g.:
  DREAMAI_VNC_WEB_PORT=6081 DREAMAI_VNC_RAW_PORT=15901 python docker/run_vnc.py FloorPlan201

Requires: Docker. Build once from repo root: docker build -t dreamai-thor -f docker/Dockerfile .
Then open the printed URL (e.g. http://localhost:6080/vnc.html) in your browser.
"""

import os
import subprocess
import sys
from pathlib import Path
import platform


def main() -> None:
    # Repo root is parent of docker/
    repo_root = Path(__file__).resolve().parent.parent
    scene = (sys.argv[1].strip() if len(sys.argv) > 1 else None) or os.environ.get("DREAMAI_VNC_SCENE", "FloorPlan1")

    web_port = int(os.environ.get("DREAMAI_VNC_WEB_PORT", "6080"))
    raw_port = int(os.environ.get("DREAMAI_VNC_RAW_PORT", "15900"))

    cmd = [
        "docker",
        "run",
        "--rm",
        "-it",
        "-p", f"{web_port}:6080",
        "-p", f"{raw_port}:5900",
        "-v", f"{repo_root}:/dreamai",
        "-e", f"DREAMAI_VNC_SCENE={scene}",
        "dreamai-thor",
    ]

    # On macOS (including ARM), use amd64 image so Unity/THOR run correctly
    if platform.system() == "Darwin":
        cmd[2:2] = ["--platform=linux/amd64"]

    # When mounting the repo from Windows, text files may have CRLF endings
    # which cause shebang errors inside Linux containers (bash\r). If we're
    # running on Windows, override the container command to sanitize CRLF
    # from the mounted start_vnc.sh before executing it.
    if platform.system() == "Windows":
        wrapper = [
            "bash",
            "-lc",
            "sed -i 's/\\r$//' /dreamai/docker/start_vnc.sh && /dreamai/docker/start_vnc.sh",
        ]
        cmd.extend(wrapper)
    print(f"Running: {' '.join(cmd)}")
    print(f"Open http://localhost:{web_port}/vnc.html in your browser. Ctrl+C to stop.\n")
    sys.exit(subprocess.run(cmd).returncode)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run the DreamAI THOR container with VNC. Works on Windows, Linux, and macOS.

Usage (from repo root):
  python run_vnc.py              # default scene FloorPlan1 (kitchen)
  python run_vnc.py FloorPlan201 # living room
  python run_vnc.py FloorPlan301 # bedroom

Requires: Docker, and the image built once with: docker build -t dreamai-thor .
Then open http://localhost:6080/vnc.html in your browser.
"""

import os
import subprocess
import sys
from pathlib import Path
import platform


def main() -> None:
    repo_root = Path(__file__).resolve().parent
    scene = (sys.argv[1].strip() if len(sys.argv) > 1 else None) or os.environ.get("DREAMAI_VNC_SCENE", "FloorPlan1")

    cmd = [
        "docker",
        "run",
        "--rm",
        "-it",
        "-p", "6080:6080",
        "-p", "15900:5900",
        "-v", f"{repo_root}:/dreamai",
        "-e", f"DREAMAI_VNC_SCENE={scene}",
        "dreamai-thor",
    ]

    # When mounting the repo from Windows, text files may have CRLF endings
    # which cause shebang errors inside Linux containers (bash\r). If we're
    # running on Windows, override the container command to sanitize CRLF
    # from the mounted start_vnc.sh before executing it. This avoids needing
    # to rebuild the image.
    if platform.system() == "Windows":
        wrapper = [
            "bash",
            "-lc",
            "sed -i 's/\r$//' /dreamai/start_vnc.sh && /dreamai/start_vnc.sh",
        ]
        cmd.extend(wrapper)
    print(f"Running: {' '.join(cmd)}")
    print("Open http://localhost:6080/vnc.html in your browser. Ctrl+C to stop.\n")
    sys.exit(subprocess.run(cmd).returncode)


if __name__ == "__main__":
    main()

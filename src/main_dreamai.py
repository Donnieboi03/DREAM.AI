import subprocess
import os
import time
import json
import base64
import re

VM_HOST = "root@213.181.122.2"
VM_PORT = "59400"
SSH_KEY = os.path.expanduser(r"~/.ssh/vast_key")

BOOTSTRAP_URL = (
    "https://raw.githubusercontent.com/"
    "Donnieboi03/DREAM.AI/vm_testing/src/vm_bootstrap_init.sh"
)
BOOTSTRAP_URL = f"{BOOTSTRAP_URL}?t={int(time.time())}"

cmd = (
    f"ssh -i {SSH_KEY} -p {VM_PORT} {VM_HOST} "
    f"\"bash -lc 'curl -fsSL {BOOTSTRAP_URL} | bash'\""
)

print("DEBUG running:", cmd)

res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")

# Always print remote logs (useful for debugging)
print(res.stdout)

if res.returncode != 0:
    print(res.stderr)
    raise SystemExit(res.returncode)

# Extract meta
meta = None
for line in res.stdout.splitlines():
    if line.startswith("DREAMAI_META "):
        meta = json.loads(line[len("DREAMAI_META "):])
        break

# Extract base64 block
m = re.search(
    r"DREAMAI_FRAME_B64_BEGIN\s*(.*?)\s*DREAMAI_FRAME_B64_END",
    res.stdout,
    flags=re.DOTALL,
)
if not m:
    raise RuntimeError("No frame found in output")

b64 = m.group(1).strip()
png_bytes = base64.b64decode(b64)

out_path = os.path.abspath("thor_frame.png")
with open(out_path, "wb") as f:
    f.write(png_bytes)

print("Saved frame:", out_path)
print("Meta:", meta)
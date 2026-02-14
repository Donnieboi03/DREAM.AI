import subprocess
import webbrowser
import os
import signal
import sys
import time

SSH_KEY = os.path.expanduser("~/.ssh/vast_key")
VM_HOST = "root@213.181.122.2"
VM_PORT = "59400"

port_forward_proc = None


def cleanup(signum=None, frame=None):
    global port_forward_proc
    if port_forward_proc:
        print("\nStopping port forwarding...")
        port_forward_proc.terminate()
    sys.exit(0)


def run_ssh(cmd):
    """Run command on VM via SSH"""
    full_cmd = f'ssh -i "{SSH_KEY}" -p {VM_PORT} {VM_HOST} "{cmd}"'
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def check_containers_running():
    """Check if containers are running"""
    code, out, _ = run_ssh("docker ps --format '{{.Names}}' | grep -q src-backend && echo running || echo stopped")
    return "running" in out


signal.signal(signal.SIGINT, cleanup)

print("\n=== DREAM.AI ===")

# Check if already running
if check_containers_running():
    print("Containers are already running.")
    print("Options:")
    print("  1. Stop containers")
    print("  2. Keep running and setup port forwarding")
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        print("Stopping containers...")
        run_ssh("cd /root/DREAM.AI/docker && docker compose down")
        print("✓ Stopped")
        sys.exit(0)
else:
    print("Starting containers...")
    
    # Check current branch
    code, branch, _ = run_ssh("cd /root/DREAM.AI && git rev-parse --abbrev-ref HEAD")
    branch = branch.strip()
    print(f"Current branch: {branch}")
    
    # Git pull
    print(f"Updating code from branch '{branch}'...")
    code, out, err = run_ssh("cd /root/DREAM.AI && git pull")
    if code != 0:
        print(f"Warning: git pull failed: {err}")
    else:
        print(f"✓ Code updated from {branch}")
    
    # Run docker compose
    print("Starting Docker Compose...")
    code, out, err = run_ssh("cd /root/DREAM.AI/docker && docker compose up -d --build")
    if code != 0:
        print(f"Error: {err}")
        sys.exit(1)
    print("✓ Docker Compose started")

# Setup port forwarding
print("\nSetting up port forwarding...")
port_forward_proc = subprocess.Popen([
    "ssh", "-i", SSH_KEY, "-p", VM_PORT,
    "-L", "5173:localhost:5173",
    "-L", "8000:localhost:8000",
    VM_HOST, "-N"
])

print("✓ Port forwarding active")
print("✓ Opening http://localhost:5173")
time.sleep(1)
webbrowser.open("http://localhost:5173")
print("✓ Press Ctrl+C to stop port forwarding\n")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    cleanup()
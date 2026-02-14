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


signal.signal(signal.SIGINT, cleanup)

print("\n=== Port Forwarding ===")
print("Make sure you have:")
print("  1. SSH session open to VM")
print("  2. docker compose up running on VM in /root/DREAM.AI/docker")
print()

print("Setting up port forwarding...")
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
print("✓ Press Ctrl+C to stop\n")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    cleanup()
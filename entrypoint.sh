#!/bin/bash
# Start Xvfb (virtual display) in the background
export DISPLAY=:99

# Clean up any leftover X11 lock files
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99

# Start Xvfb with better error handling
Xvfb :99 -screen 0 1280x720x24 -ac > /tmp/xvfb.log 2>&1 &
XVFB_PID=$!

# Wait longer for Xvfb to fully initialize
sleep 5

# Check if Xvfb is running using /proc
if ! [ -d /proc/$XVFB_PID ]; then
    echo "Error: Xvfb failed to start (PID: $XVFB_PID)"
    cat /tmp/xvfb.log
    exit 1
fi

echo "Xvfb started successfully on display $DISPLAY (PID: $XVFB_PID)"

# Run the main command (uvicorn)
exec "$@"

# Cleanup on exit
trap "kill $XVFB_PID 2>/dev/null" EXIT

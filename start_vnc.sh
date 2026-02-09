#!/usr/bin/env bash
set -e

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

# 5) Start your THOR script (this will open windows on the virtual desktop)
python -u dreamai/scripts/run_proc_test.py --use-example-schema

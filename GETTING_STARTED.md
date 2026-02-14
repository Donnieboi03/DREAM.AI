# DREAM.AI - Getting Started Guide

An agentic framework for training robust RL brains in simulated environments (AI2-THOR).

## Quick Start (30 seconds)

### Windows
1. Open PowerShell in this folder
2. Run: `python -m pip install docker`
3. Ensure Docker Desktop is running
4. Run: `docker-compose up -d`
5. Wait 30 seconds
6. Open browser: **http://localhost:5173**

### Linux/macOS
1. Ensure Docker is installed: `docker --version`
2. From this folder, run: `docker-compose up -d`
3. Wait 30 seconds
4. Open browser: **http://localhost:5173**

## System Architecture

### Frontend (React + Vite)
- **Port**: 5173
- **URL**: http://localhost:5173
- **Responsibility**: WebSocket connection, game rendering, keyboard controls
- **Tech**: TypeScript, HTML5 Canvas, WebSocket API

### Backend (FastAPI + Uvicorn)
- **Port**: 8000
- **WebSocket**: ws://localhost:8000/ws/game
- **Responsibility**: AI2-THOR environment management, frame streaming, action processing
- **Features**: 60 FPS, 1280x720 resolution, 90% JPEG quality

### Game Environment (AI2-THOR)
- **Framework**: AI2-THOR with ProcTHOR
- **Default Scene**: FloorPlan1 (kitchen)
- **Rendering**: Virtual X11 display (Xvfb)
- **Physics**: Real-time simulation

## Controls

### Keyboard
- **W** - Move forward
- **S** - Move backward
- **A** - Turn left
- **D** - Turn right
- **Q** - Look up
- **E** - Look down
- **F** - Pickup object
- **G** - Drop object
- **T** - Toggle object

### Browser UI
- **Scene Selection** - Dropdown to load different FloorPlan scenes (1-210)
- **Reset Button** - Reset environment to initial state
- **Pickup/Drop/Toggle** - Alternative button controls

## Project Structure

```
DREAM.AI/
├── src/                          # Python backend
│   ├── backend/
│   │   ├── api/
│   │   │   ├── app.py               # FastAPI application
│   │   │   └── websocket_stream.py  # WebSocket handler
│   │   └── ...
│   ├── envs/
│   │   └── ai2thor/
│   │       └── thor_env.py          # AI2-THOR wrapper
│   └── requirements.txt             # Python dependencies
├── DREAM_UNITY/                      # Unity project (not used in Docker)
├── docker-compose.yml               # Container orchestration
├── Dockerfile                       # Backend image definition
├── test_websocket.html              # Testing interface (optional)
└── README.md                        # Full documentation
```

## Common Tasks

### Load a Different Scene
1. In the browser, select a scene from the dropdown (FloorPlan1-210)
2. Click "Load Scene" button
3. Wait a few seconds for the new environment to load

### Reset Environment
Click the "Reset" button to return to the initial state without loading a new scene.

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Rebuild After Code Changes
```bash
# Backend code changes
docker-compose down
docker-compose build backend
docker-compose up -d

# Frontend code changes are hot-reloaded automatically
```

## Performance Characteristics

- **FPS**: 60 frames per second
- **Resolution**: 1280x720 pixels
- **Latency**: 40-70ms (network + processing)
- **Bandwidth**: ~300-450 KB/s (typical internet easily handles)
- **Memory**: ~500 MB per client (environment) + 50 MB (buffers)

## WebSocket Protocol

### Action Message
```json
{
  "type": "action",
  "action": 0
}
```
**Action codes**: 0=MoveAhead, 1=MoveBack, 2=RotateLeft, 3=RotateRight, 4=LookUp, 5=LookDown, 6=PickupObject, 7=DropHandObject, 8=ToggleObjectOn

### Frame Message (Server → Client)
```json
{
  "type": "frame",
  "jpeg_base64": "...",
  "metrics": {
    "step_count": 42,
    "episode_reward": 10.5,
    "agent_position": [0.5, 0.0, 0.5],
    "agent_rotation": 45.0
  }
}
```

### Other Commands
- Reset: `{"type": "reset"}`
- Load Scene: `{"type": "load_scene", "scene": "FloorPlan201"}`
- Set Resolution: `{"type": "set_resolution", "width": 1920, "height": 1080}`
- Start Streaming: `{"type": "start_streaming"}`
- Stop Streaming: `{"type": "stop_streaming"}`

## Troubleshooting

### "Cannot reach localhost:5173"
- Check Docker is running: `docker ps`
- Check frontend is up: `docker-compose ps`
- Wait 20 seconds after startup (frontend takes time to build)

### "WebSocket connection failed"
- Check backend is up: `docker logs src-backend`
- Verify firewall allows port 8000
- Check browser console for errors (F12 → Console)

### "Black screen / no frames"
- Check backend logs: `docker logs src-backend`
- Verify AI2-THOR initialized: Look for "Environment initialized"
- Try resetting environment (browser button)

### "AI2-THOR initialization fails"
- Ensure Docker has enough memory (recommend 4GB+)
- Check disk space (need 2GB+ free)
- Try rebuilding: `docker-compose build --no-cache backend`

### Slow performance / low FPS
- Close other applications to free memory
- Reduce browser zoom level
- Check network latency (might be system lag, not network)
- Verify Docker resource limits: `docker stats`

## Development

### GraphTask (rl_thor) for Local Development
For task-specific reward computation (GraphTask), install rl_thor locally:
```bash
pip install -e third_party/rl_thor
```
Docker images include rl_thor automatically.

### Backend Development
1. Edit files in `src/backend/`
2. Rebuild: `docker-compose build backend`
3. Restart: `docker-compose restart backend`

### Frontend Development
1. Edit files in `src/frontend/`
2. Changes auto-reload (Vite hot module replacement)
3. Refresh browser if needed

### Testing WebSocket Directly
Open `test_websocket.html` in browser for a minimal test interface without the full frontend.

## Environment Variables

Set in `docker-compose.yml`:
- `PYTHONPATH=/src` - Python path for imports
- `DISPLAY=:99` - Virtual X11 display
- `AI2THOR_HEADLESS=1` - Headless rendering mode

## System Requirements

- Docker Desktop (or Docker + Docker Compose)
- 4GB RAM minimum (8GB recommended)
- 2GB free disk space
- Modern browser (Chrome, Firefox, Safari, Edge)

## Next Steps

1. ✅ Start the system (see Quick Start above)
2. ✅ Open http://localhost:5173 in your browser
3. ✅ Test keyboard controls (WASD to move)
4. ✅ Try different scenes (dropdown menu)
5. 📚 Read [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design
6. 🔧 Read [README.md](README.md) for advanced configuration

## Support Resources

- **AI2-THOR Documentation**: https://ai2thor.allenai.org/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **React Documentation**: https://react.dev/
- **Docker Documentation**: https://docs.docker.com/

---

**Last Updated**: 2025  
**Status**: Production Ready  
**Tested On**: Windows 10/11, Ubuntu 20.04+, macOS 12+

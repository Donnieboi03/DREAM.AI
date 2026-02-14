# DREAM.AI

An agentic framework for training robust RL brains in Simulated Environments.

**⚡ Quick Start**: See [GETTING_STARTED.md](GETTING_STARTED.md) for setup instructions (30 seconds).

## Overview

DREAM.AI is a system for training and evaluating reinforcement learning agents in realistic 3D environments using AI2-THOR. It features:

- **Real-time WebSocket streaming** at 60 FPS with 1280x720 resolution
- **Interactive browser interface** with keyboard controls and scene selection
- **FastAPI backend** with AI2-THOR environment integration
- **React frontend** with responsive canvas and live metrics
- **Docker containerization** for easy deployment
- **Modular architecture** supporting multiple RL algorithms (via Stable Baselines3)

## Key Features

✅ **60 FPS Frame Streaming** - Low-latency game rendering  
✅ **Keyboard Controls** - WASD for movement, Q/E for looking  
✅ **Scene Selection** - Load different FloorPlan environments (1-210)  
✅ **Responsive Canvas** - Full-screen, resizable game viewport  
✅ **Metrics Tracking** - Step count, reward, agent position, rotation  
✅ **Docker Deployment** - Single command startup  
✅ **Development Ready** - Hot-reload frontend, modular backend  

## Getting Started

### Prerequisites
- Docker Desktop installed
- 4GB+ RAM
- 2GB free disk space
- Modern web browser

### One-Command Launch

**Local (no Docker) – macOS / Linux:**
```bash
./launch-local.sh
```
Runs backend (Python) and frontend (npm) directly. Prerequisites: `pip install -r src/requirements.txt`, `pip install -e third_party/rl_thor` (for GraphTask), and `cd src/frontend && npm install`. Opens http://localhost:8080.

**Docker:**
```bash
./launch.sh          # macOS / Linux
launch.bat           # Windows
```
Starts backend + frontend via Docker, waits for readiness, and opens http://localhost:5173.

Add `GEMINI_API_KEY` or `GOOGLE_API_KEY` to a `.env` file for the Orchestrator LLM. Copy `.env.example` to `.env` and fill in your key.

### Run manually
```bash
cd docker
docker compose up -d
# Wait 20-30 seconds
# Open: http://localhost:5173
```

**That's it!** The system will be running with:
- Frontend on port 5173
- Backend API on port 8000
- AI2-THOR environment initialized and streaming frames

### Controls
- **W/A/S/D** - Move and rotate
- **Q/E** - Look up/down
- **F/G/T** - Pickup/drop/toggle
- **Dropdown** - Change scenes
- **Reset** - Reset environment

## Project Structure

```
DREAM.AI/
├── src/                    # Python backend (FastAPI + AI2-THOR)
│   ├── backend/api/           # WebSocket & HTTP handlers
│   ├── envs/ai2thor/          # AI2-THOR environment wrapper
│   ├── rl/                    # RL agent implementations
│   └── requirements.txt
├── DREAM_UNITY/               # Unity project (not used in Docker)
├── docker-compose.yml         # Container orchestration
├── Dockerfile                 # Backend image
├── test_websocket.html        # Optional WebSocket test interface
├── GETTING_STARTED.md         # Setup & basic usage
├── ARCHITECTURE.md            # Detailed system design
└── README.md                  # This file
```

## Architecture

### Components
1. **Frontend** (React + Vite + TypeScript)
   - Real-time canvas rendering
   - WebSocket connection management
   - Keyboard event handling
   - Scene and action controls

2. **Backend** (FastAPI + Uvicorn)
   - WebSocket server for frame streaming
   - Environment management
   - Action processing
   - Metrics aggregation

3. **Game Environment** (AI2-THOR)
   - ProcTHOR procedurally generated scenes
   - Physics simulation
   - Object interaction
   - Rendering via Xvfb (X11 virtual framebuffer)

### Data Flow
```
Browser (React)
    ↓ (WebSocket: action)
FastAPI Backend (websocket_stream.py)
    ↓ (Python API)
AI2-THOR Environment
    ↓ (RGB frame + metrics)
FastAPI Backend
    ↓ (WebSocket: JPEG + metrics)
Browser (HTML5 Canvas)
```

## WebSocket Protocol

### Client → Server
```json
{"type": "action", "action": 0}           // Actions: 0-8
{"type": "reset"}                         // Reset environment
{"type": "load_scene", "scene": "FloorPlan201"}
{"type": "set_resolution", "width": 1920, "height": 1080}
```

### Server → Client
```json
{
  "type": "frame",
  "jpeg_base64": "...",
  "metrics": {
    "step_count": 42,
    "episode_reward": 10.5,
    "agent_position": [x, y, z],
    "agent_rotation": degrees
  }
}
```

## Common Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose build backend
docker-compose restart backend

# Access container shell
docker exec -it src-backend bash
```

## Development

### Hot-Reload Frontend
Changes to React code auto-reload via Vite HMR.

### Rebuild Backend
After changing Python code:
```bash
docker-compose build backend
docker-compose restart backend
```

### Local Development (without Docker)
```bash
# Install Python dependencies
pip install -r src/requirements.txt

# Run backend
cd src
python -m backend.api.app

# In another terminal, run frontend
cd src/frontend
npm install
npm run dev
```

## Performance

- **FPS**: 60 frames/second
- **Resolution**: 1280x720
- **Latency**: 40-70ms (network + processing)
- **Bandwidth**: ~300-450 KB/s
- **Memory**: ~500 MB per client

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Cannot reach localhost:5173" | Check Docker is running, wait 30s for startup |
| "WebSocket connection failed" | Check backend logs: `docker logs src-backend` |
| "Black screen" | Verify AI2-THOR initialized in logs, try reset button |
| "Slow FPS" | Close other apps, check `docker stats` for resources |

See [GETTING_STARTED.md](GETTING_STARTED.md#troubleshooting) for more troubleshooting tips.

## Architecture & System Design

For detailed information about the system architecture, data flow, and technical implementation:
- See [ARCHITECTURE.md](ARCHITECTURE.md) for complete system design
- Check [GETTING_STARTED.md](GETTING_STARTED.md) for setup and usage

## System Requirements

- **OS**: Windows 10+, Linux, macOS
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 2GB free disk space
- **Docker**: Latest stable version
- **Browser**: Chrome, Firefox, Safari, Edge (modern version)

## Technologies Used

- **Backend**: Python, FastAPI, Uvicorn
- **Frontend**: React, TypeScript, Vite
- **Game Engine**: AI2-THOR (ProcTHOR)
- **Container**: Docker & Docker Compose
- **Rendering**: X11 Xvfb (virtual framebuffer)
- **RL Training**: Stable Baselines3, Gymnasium

## License

See LICENSE file for details.

## Support

- **AI2-THOR**: https://ai2thor.allenai.org/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Docker**: https://www.docker.com/

---

**Status**: Production Ready  
**Last Updated**: 2025  
**Tested on**: Windows 10/11, Ubuntu 20.04+, macOS 12+

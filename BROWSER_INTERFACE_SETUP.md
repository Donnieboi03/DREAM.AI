# Browser-Based ProcTHOR Streaming Interface - Setup Guide

This document covers how to set up and run the complete browser-based interface for controlling ProcTHOR through a web browser.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Browser (React)                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Canvas Viewport (Unity Frames)  │ UI Overlays        │ │
│  │  • JPEG frame streaming         │ • Prompt Box       │ │
│  │  • Real-time 30 FPS             │ • Metrics Display  │ │
│  │                                  │ • Control Buttons  │ │
│  │                                  │ • Reward Graph     │ │
│  └────────────────────────────────────────────────────────┘ │
│                          ▲                                    │
│                          │ WebSocket                          │
│                          ▼                                    │
│  Message Format:                                             │
│  • {type: "action", action: 0-8} ←──────┐                   │
│  • {type: "frame", jpeg_base64, metrics} ────→ Browser      │
└─────────────────────────────────────────────────────────────┘
                          ▲ / ▼
        WebSocket ┌───────────────────────────────────┐
                  │    FastAPI Backend (Python)       │
        HTTP     │  ┌──────────────────────────────┐ │
        POST     │  │ WebSocket Manager            │ │
                  │  │ • Frame streaming loop       │ │
                  │  │ • Action handling            │ │
                  │  │ • Metrics aggregation        │ │
                  │  └──────────────────────────────┘ │
                  │  ┌──────────────────────────────┐ │
                  │  │ Orchestrator Routes (REST)   │ │
                  │  │ POST /api/orchestrator/      │ │
                  │  │   generate_task              │ │
                  │  │   evaluate_episode           │ │
                  │  └──────────────────────────────┘ │
                  └───────────────────────────────────┘
                          ▲ / ▼
                  ┌───────────────────────────────────┐
                  │    ProcTHOR Environment           │
                  │  • ThorEnv (Gymnasium wrapper)    │
                  │  • AI2-THOR controller            │
                  │  • Discrete action space (9)      │
                  │  • RGB observations (300x300)     │
                  └───────────────────────────────────┘
                          ▲ / ▼
                  ┌───────────────────────────────────┐
                  │    Unity Simulation               │
                  │  • ProcTHOR (procedural houses)   │
                  │  • Physics & rendering            │
                  └───────────────────────────────────┘
```

## Backend Setup

### 1. Install Python Dependencies

Navigate to the dreamai directory and install dependencies:

```bash
cd c:\Users\Midhun\Desktop\Projects\DREAM.AI\dreamai
pip install -r requirements.txt
pip install fastapi uvicorn pillow
```

### 2. Start the Backend Server

```bash
python -m backend.api.app
```

This will start the FastAPI server at `http://localhost:8000`.

You should see:
```
Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
Starting DREAM.AI backend...
Environment initialized successfully
```

The WebSocket endpoint will be at `ws://localhost:8000/ws/game`.

### 3. Verify Backend Health

Check that the backend is running:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "environment_initialized": true,
  "connected_clients": 0
}
```

## Frontend Setup

### 1. Install Node Dependencies

Navigate to the frontend directory:

```bash
cd c:\Users\Midhun\Desktop\Projects\DREAM.AI\dreamai\frontend
npm install
```

### 2. Configure Backend URL

The frontend currently expects the backend at `http://localhost:8000`. If you're running it elsewhere, update:

- In `src/components/GameViewport.tsx`, update the WebSocket URL construction
- Ensure CORS is enabled on the backend (already done in `backend/api/app.py`)

### 3. Start Frontend Development Server

```bash
npm run dev
```

The frontend will start at `http://localhost:5173` (Vite default).

## How to Use

### Connecting and Playing

1. **Start the backend** (see Backend Setup above)
2. **Start the frontend** (see Frontend Setup above)
3. **Open browser** at `http://localhost:5173`

You should see:
- Connected status indicator (green = connected)
- Game viewport showing the ProcTHOR environment
- Control panel with action buttons on the left
- Metrics display showing episode reward, steps, and agent position
- Prompt box for submitting natural language tasks

### Controlling the Agent

#### Method 1: Action Buttons

Click any button in the control panel:
- **↑ Move Ahead** (Action 0) - Move forward
- **↓ Move Back** (Action 1) - Move backward
- **← Rotate Left** (Action 2) - Rotate counterclockwise
- **→ Rotate Right** (Action 3) - Rotate clockwise
- **⬆ Look Up** (Action 4) - Look up
- **⬇ Look Down** (Action 5) - Look down
- **🖐 Pickup** (Action 6) - Pickup object in view
- **📥 Drop** (Action 7) - Drop held object
- **⚡ Toggle** (Action 8) - Toggle object (light, etc.)

#### Method 2: Prompt Box

Enter a natural language task description (e.g., "Pick up the apple and place it on the table") and click **Submit Task**. The backend will:
1. Process the prompt
2. Generate a TaskSpec with objectives and success criteria
3. Reset the environment with the new task
4. Return task metadata to the frontend

### Viewing Metrics

Real-time metrics are displayed in the metrics panel:

- **Episode Reward**: Cumulative reward for current episode
- **Steps**: Number of actions taken
- **Position**: Agent's current (X, Z) coordinates
- **Rotation**: Agent's current rotation in degrees
- **Last Action**: Success/failure of previous action
- **Reward Trend**: Graph showing historical reward progression
- **Avg Reward/Step**: Efficiency metric

## WebSocket Protocol

### Messages from Browser to Backend

```json
{
  "type": "action",
  "action": 0
}
```

Sends a discrete action (0-8). Backend steps environment and broadcasts new frame.

```json
{
  "type": "reset"
}
```

Resets the environment to initial state.

```json
{
  "type": "start_streaming"
}
```

Starts continuous frame streaming at 30 FPS.

```json
{
  "type": "stop_streaming"
}
```

Stops frame streaming.

### Messages from Backend to Browser

```json
{
  "type": "frame",
  "jpeg_base64": "...",
  "metrics": {
    "agent_position": {"x": 0.5, "y": 0.0, "z": 0.5},
    "agent_rotation": 45.0,
    "episode_reward": 10.5,
    "step_count": 42,
    "last_action_success": true
  }
}
```

Contains JPEG-encoded frame and current metrics.

## HTTP Endpoints

### Health Check

```
GET /health
```

Returns backend and environment status.

### Generate Task from Prompt

```
POST /api/orchestrator/generate_task
Content-Type: application/json

{
  "prompt": "Pick up the apple",
  "max_steps": 500
}
```

Returns:
```json
{
  "task": {
    "description": "Pick up the apple",
    "goal": "Complete the following: Pick up the apple",
    "success_criteria": [
      "Agent completes the described task",
      "Task completed within step limit"
    ],
    "max_steps": 500,
    "subtasks": []
  },
  "scene_id": "auto_generated",
  "message": "Task generated from prompt: Pick up the apple"
}
```

### Evaluate Episode

```
POST /api/orchestrator/evaluate_episode
Content-Type: application/json

{
  "total_reward": 10.5,
  "steps": 150,
  "max_steps": 500,
  "success": true
}
```

Returns:
```json
{
  "success": true,
  "total_reward": 10.5,
  "steps": 150,
  "reward_per_step": 0.07,
  "efficiency": 0.3
}
```

## Troubleshooting

### WebSocket Connection Refused

**Issue**: Browser shows "Disconnected"

**Solution**:
- Verify backend is running: `curl http://localhost:8000/health`
- Check CORS headers are set (they are in `app.py`)
- Ensure WebSocket protocol matches (ws:// for HTTP, wss:// for HTTPS)

### No Video Frames Appearing

**Issue**: Canvas is blank, only status shows

**Solution**:
- Check browser console for errors (F12 → Console)
- Verify `start_streaming` message was sent
- Confirm environment initialized successfully in backend logs
- Try clicking "Reset" button

### Slow Performance / Lag

**Issue**: Frames are delayed or choppy

**Solution**:
- Check network latency: `ping localhost`
- Reduce JPEG quality in `backend/api/websocket_stream.py` (currently 85%)
- Reduce target FPS in `stream_frames()` call (currently 30)
- Check CPU usage on backend machine

### Environment Initialization Failed

**Issue**: Backend logs show error during initialization

**Solution**:
- Ensure AI2-THOR is properly installed: `python -c "import ai2thor; print(ai2thor.__version__)"`
- Verify ProcTHOR is installed: `python -c "from procthor import create_house; print('OK')"`
- Check system has GPU available (for faster rendering)
- Try setting `quality="Low"` in environment initialization

## Advanced Configuration

### Backend Configuration

Edit `backend/api/app.py`:

```python
# Change WebSocket endpoint
@app.websocket("/ws/game")  # Modify path here

# Change frame streaming FPS
await stream_manager.stream_frames(target_fps=60)  # Increase to 60 FPS
```

Edit `backend/api/websocket_stream.py`:

```python
# Change JPEG quality (0-100, higher = better quality, larger size)
pil_image.save(jpeg_buffer, format="JPEG", quality=85)  # Adjust quality

# Change target resolution
self.env = ThorEnv(width=400, height=300)  # Increase resolution
```

### Frontend Configuration

Edit `src/components/GameViewport.tsx`:

```typescript
// Change canvas resolution
<canvas width={800} height={600} />  # Modify dimensions

// Change WebSocket URL
const wsUrl = `${wsProtocol}//${window.location.host}/ws/game`;
```

## Next Steps

To extend this system:

1. **Integrate LLM-based task generation**: Connect `backend/orchestrator/task_generator.py` to `backend/llm/` for advanced prompt parsing
2. **Add evaluation/reward feedback**: Implement reward shaping in `backend/evaluation/`
3. **Store/replay episodes**: Use `backend/storage/` to save and replay episodes
4. **Multi-scene support**: Extend `SceneSpec` to support multiple house generation configs
5. **Real-time debugging**: Add WebSocket route for agent internal state streaming

## File Structure

```
backend/api/
├── app.py                      # FastAPI application
├── websocket_stream.py         # WebSocket handler and frame streaming
└── orchestrator_routes.py      # Task generation HTTP routes

backend/orchestrator/
├── __init__.py
└── task_generator.py           # Task spec generation from prompts

frontend/src/
├── App.tsx                     # Main component with layout
├── components/
│   ├── GameViewport.tsx        # Canvas + WebSocket connection
│   ├── UIOverlays.tsx          # Prompt box, buttons, basic metrics
│   └── DetailedMetrics.tsx     # Advanced metrics with graphs
└── main.tsx                    # React entry point
```

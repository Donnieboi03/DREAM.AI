"""FastAPI application with WebSocket streaming for game viewport."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .websocket_stream import GameStreamManager
from .runtime_state import set_game_env
from .orchestrator_routes import router as orchestrator_router

# Import from DREAM.AI modules (PYTHONPATH set in Dockerfile)
from envs.ai2thor.procthor_adapter import make_procthor_env


# Global environment and stream manager
game_env = None
stream_manager = None
streaming_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize environment on startup, cleanup on shutdown."""
    global game_env, stream_manager
    
    print("Starting DREAM.AI backend...")
    
    # Initialize ProcTHOR environment
    try:
        game_env = make_procthor_env()
        set_game_env(game_env)
        stream_manager = GameStreamManager(game_env)
        print("Environment initialized successfully")
    except Exception as e:
        print(f"Failed to initialize environment: {e}")
    
    yield
    
    # Cleanup
    if stream_manager:
        await stream_manager.stop_streaming()
    if game_env:
        game_env.close()
    print("Backend shutdown complete")


# Create FastAPI app with lifespan
app = FastAPI(
    title="DREAM.AI Backend",
    description="WebSocket streaming and control for ProcTHOR environment",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include orchestrator routes
app.include_router(orchestrator_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "environment_initialized": game_env is not None,
        "connected_clients": len(stream_manager.connections) if stream_manager else 0,
    }


@app.websocket("/ws/game")
async def websocket_game_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for game streaming and control.
    
    Browser sends:
    - {"type": "action", "action": <0-8>}
    - {"type": "reset"}
    - {"type": "start_streaming"}
    - {"type": "stop_streaming"}
    - {"type": "load_scene", "scene": "FloorPlan201"}
    - {"type": "set_resolution", "width": 1280, "height": 720}
    
    Server sends:
    - {"type": "frame", "jpeg_base64": "...", "metrics": {...}}
    """
    global streaming_task, game_env
    
    if not stream_manager or not game_env:
        await websocket.close(code=1000, reason="Environment not initialized")
        return
    
    await stream_manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "action":
                # Handle discrete action
                result = await stream_manager.handle_action(data)
                await websocket.send_json({"type": "action_result", "data": result})
            
            elif message_type == "reset":
                # Reset environment
                result = await stream_manager.handle_reset(data)
                # Send initial frame after reset
                observation, info = game_env.reset()
                await stream_manager.broadcast_frame(observation, stream_manager.current_metrics)
                await websocket.send_json({"type": "reset_result", "data": result})
            
            elif message_type == "set_resolution":
                # Set rendering resolution
                width = data.get("width", 1280)
                height = data.get("height", 720)
                stream_manager.render_width = max(640, width)  # Min 640
                stream_manager.render_height = max(360, height)  # Min 360
                print(f"✓ Resolution set to {stream_manager.render_width}x{stream_manager.render_height}")
                await websocket.send_json({"type": "resolution_set", "width": stream_manager.render_width, "height": stream_manager.render_height})
            
            elif message_type == "load_scene":
                # Load a different scene
                scene_name = data.get("scene", "FloorPlan1")
                try:
                    from ai2thor.controller import Controller
                    
                    # Close the current environment
                    if game_env._controller:
                        game_env._controller.stop()
                    
                    # Create new controller with the requested scene
                    new_controller = Controller(
                        scene=scene_name,
                        gridSize=0.25,
                        visibilityDistance=1.5,
                    )
                    
                    # Update the environment's controller
                    game_env._controller = new_controller
                    game_env._last_event = None
                    stream_manager.current_metrics = {
                        "agent_position": None,
                        "agent_rotation": None,
                        "episode_reward": 0.0,
                        "step_count": 0,
                        "last_action_success": True,
                    }
                    
                    # Send initial frame
                    observation, info = game_env.reset()
                    await stream_manager.broadcast_frame(observation, stream_manager.current_metrics)
                    await websocket.send_json({"type": "scene_loaded", "scene": scene_name})
                    print(f"✓ Scene loaded: {scene_name}")
                except Exception as e:
                    print(f"✗ Failed to load scene {scene_name}: {e}")
                    await websocket.send_json({"type": "error", "message": f"Failed to load scene: {e}"})
            
            elif message_type == "load_scene_dict":
                # Load a scene from an LLM-generated edited house dict
                result = await stream_manager.handle_load_scene_dict(data)
                if result.get("success"):
                    # Send initial frame from new scene
                    observation, info = game_env.reset()
                    await stream_manager.broadcast_frame(observation, stream_manager.current_metrics)
                    await websocket.send_json({"type": "scene_dict_loaded", "data": result})
                else:
                    await websocket.send_json({"type": "error", "message": result.get("error", "Unknown error")})
            
            elif message_type == "start_streaming":
                # Start continuous frame streaming (only if not already running)
                if not stream_manager.streaming:
                    streaming_task = asyncio.create_task(
                        stream_manager.stream_frames(target_fps=60)
                    )
                await websocket.send_json({"type": "streaming_started"})
            
            elif message_type == "stop_streaming":
                # Stop streaming
                await stream_manager.stop_streaming()
                if streaming_task:
                    streaming_task.cancel()
                    streaming_task = None
                await websocket.send_json({"type": "streaming_stopped"})
            
            else:
                await websocket.send_json({"type": "error", "message": f"Unknown message type: {message_type}"})
    
    except WebSocketDisconnect:
        stream_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        stream_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

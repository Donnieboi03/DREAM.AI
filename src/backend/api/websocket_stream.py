"""WebSocket streaming handler for real-time game viewport and control."""

import asyncio
import json
from typing import Any, Optional

import numpy as np
from fastapi import WebSocket, WebSocketDisconnect
from PIL import Image
import io

from envs.ai2thor.thor_env import ThorEnv, THOR_DISCRETE_ACTIONS
from ..schemas import SceneSpec, TaskSpec, RewardSpec
from . import rl_state


class GameStreamManager:
    """Manages WebSocket connections and streams Unity frames + metrics."""

    def __init__(self, env: ThorEnv):
        self.env = env
        self.connections: list[WebSocket] = []
        self.connection_roles: dict[WebSocket, str] = {}
        self.current_metrics = {
            "agent_position": None,
            "agent_rotation": None,
            "episode_reward": 0.0,
            "step_count": 0,
            "last_action_success": True,
            "task_advancement": None,
            "max_task_advancement": None,
            "is_success": None,
            "task_type": None,
        }
        self.streaming = False
        self.render_width = 1280  # Default high resolution
        self.render_height = 720
        self.jpeg_quality = 90  # High quality JPEG

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection. New connections default to 'browser' role."""
        await websocket.accept()
        self.connections.append(websocket)
        self.connection_roles[websocket] = "browser"
        print(f"Client connected. Total connections: {len(self.connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        self.connections.remove(websocket)
        self.connection_roles.pop(websocket, None)
        print(f"Client disconnected. Total connections: {len(self.connections)}")

    def set_connection_role(self, websocket: WebSocket, role: str) -> None:
        """Set the role for a connection ('browser' or 'rl_agent')."""
        if websocket in self.connections:
            self.connection_roles[websocket] = role

    async def broadcast_frame(self, rgb_array: np.ndarray, metrics: dict):
        """Send JPEG frame and metrics to all connected clients."""
        # Resize frame to target resolution if needed
        if rgb_array.shape[0] != self.render_height or rgb_array.shape[1] != self.render_width:
            from scipy import ndimage
            # Use high-quality resizing
            zoom_factors = (
                self.render_height / rgb_array.shape[0],
                self.render_width / rgb_array.shape[1],
                1  # Keep RGB channels
            )
            rgb_array = ndimage.zoom(rgb_array, zoom_factors, order=1)
            rgb_array = np.clip(rgb_array, 0, 255).astype(np.uint8)
        
        # Encode RGB array to JPEG with high quality
        pil_image = Image.fromarray(rgb_array.astype(np.uint8))
        jpeg_buffer = io.BytesIO()
        pil_image.save(jpeg_buffer, format="JPEG", quality=self.jpeg_quality, optimize=False)
        jpeg_bytes = jpeg_buffer.getvalue()

        # Derived for backward compat: "agent" when RL process running, else "user"
        control_mode = "agent" if rl_state.is_rl_agent_running() else "user"
        metrics_with_mode = {**metrics, "control_mode": control_mode}

        # Create message payload
        message = {
            "type": "frame",
            "jpeg_base64": __import__("base64").b64encode(jpeg_bytes).decode("utf-8"),
            "metrics": metrics_with_mode,
        }

        # Send to all connected clients
        disconnected = []
        for connection in self.connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending frame: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def handle_action(self, action_data: dict, websocket: WebSocket) -> dict:
        """
        Process incoming action from browser or RL agent and step environment.
        Control is implicit: agent has control when RL process is running; browser otherwise.
        
        Expected action_data format:
        {
            "type": "action",
            "action": <int 0-8>  # discrete action index
        }
        
        Returns observation, reward, done, and updated metrics.
        """
        if "action" not in action_data:
            return {"error": "Invalid action format"}

        # Filter by process state: rl_agent only when process running; browser otherwise
        role = self.connection_roles.get(websocket, "browser")
        agent_running = rl_state.is_rl_agent_running()
        if agent_running and role != "rl_agent":
            return {"skipped": True, "reason": "agent_control", "metrics": self.current_metrics}
        if not agent_running and role != "browser":
            return {"skipped": True, "reason": "user_control", "metrics": self.current_metrics}

        action_idx = action_data["action"]
        if not (0 <= action_idx < len(THOR_DISCRETE_ACTIONS)):
            return {"error": f"Invalid action index: {action_idx}"}

        # Step the environment
        observation, reward, terminated, truncated, info = self.env.step(action_idx)
        done = terminated or truncated

        # Update metrics
        self.current_metrics["episode_reward"] += reward
        self.current_metrics["step_count"] += 1
        self.current_metrics["last_action_success"] = info.get(
            "last_action_success", True
        )
        task_info = info.get("task_info") or info
        if "task_advancement" in task_info:
            self.current_metrics["task_advancement"] = task_info["task_advancement"]
        if "max_task_advancement" in info:
            self.current_metrics["max_task_advancement"] = info["max_task_advancement"]
        if "is_success" in info:
            self.current_metrics["is_success"] = info["is_success"]
        if "task_type" in info:
            self.current_metrics["task_type"] = info["task_type"]

        # Extract agent state from environment if available
        if hasattr(self.env, "_last_event") and self.env._last_event:
            event = self.env._last_event
            self.current_metrics["agent_position"] = {
                "x": event.metadata["agent"]["position"]["x"],
                "y": event.metadata["agent"]["position"]["y"],
                "z": event.metadata["agent"]["position"]["z"],
            }
            self.current_metrics["agent_rotation"] = event.metadata["agent"][
                "rotation"
            ]["y"]

        return {
            "observation_shape": observation.shape,
            "reward": float(reward),
            "done": done,
            "metrics": self.current_metrics,
        }

    async def handle_reset(self, reset_data: dict) -> dict:
        """Reset environment and return initial observation.

        When randomize=True (agent reset on timeout/completion): applies random agent
        spawn and random object positions. When randomize=False (user reset): restores
        scene to default position.
        """
        self.current_metrics = {
            "agent_position": None,
            "agent_rotation": None,
            "episode_reward": 0.0,
            "step_count": 0,
            "last_action_success": True,
            "task_advancement": None,
            "max_task_advancement": None,
            "is_success": None,
            "task_type": None,
        }

        scene_rand = reset_data.get("scene_randomization")
        if scene_rand is None and reset_data.get("randomize") is True:
            scene_rand = {
                "random_agent_spawn": True,
                "random_object_spawn": True,
            }
        options = {"scene_randomization": scene_rand} if scene_rand else None
        observation, info = self.env.reset(options=options)
        # Merge metrics from reset info
        if info:
            for key in ("task_advancement", "max_task_advancement", "is_success", "task_type"):
                if key in info:
                    self.current_metrics[key] = info[key]
            pos = info.get("agent_position")
            if pos:
                self.current_metrics["agent_position"] = pos if isinstance(pos, dict) else {"x": 0, "y": 0, "z": 0}
            if "agent_rotation" in info:
                self.current_metrics["agent_rotation"] = info["agent_rotation"]
        return {
            "observation": observation,
            "observation_shape": observation.shape,
            "initial_metrics": self.current_metrics,
        }

    async def handle_load_scene_dict(self, scene_data: dict) -> dict:
        """
        Load a scene from an edited house dict (e.g., from LLM-generated scene).
        
        Expected scene_data format:
        {
            "scene_dict": {house dict from apply_edits},
            "task_description": "Optional task description",
            "task_description_dict": optional rl_thor Graph Task dict
        }
        
        Returns initial observation and metrics for the new scene.
        """
        scene_dict = scene_data.get("scene_dict")
        task_description = scene_data.get("task_description", "")
        task_description_dict = scene_data.get("task_description_dict")
        
        if not scene_dict:
            return {"error": "No scene_dict provided"}
        
        try:
            from ai2thor.controller import Controller
            
            # Close the current environment's controller
            if self.env._controller:
                self.env._controller.stop()
            
            # Create new controller with the edited house (High quality)
            new_controller = Controller(
                scene=scene_dict,
                width=self.render_width,
                height=self.render_height,
                quality="Very High",
                gridSize=0.25,
                visibilityDistance=1.5,
            )
            
            # Update the environment's controller and scene for reset
            self.env._controller = new_controller
            self.env._last_event = None
            self.env.set_current_scene(scene_dict)

            # Set or clear rl_thor graph task
            if task_description_dict and isinstance(task_description_dict, dict):
                ok = self.env.set_graph_task(task_description_dict)
                print(f"[WebSocket] Graph task {'set' if ok else '(rl_thor unavailable)'}")
            else:
                self.env.clear_graph_task()
            
            # Reset metrics for new scene
            self.current_metrics = {
                "agent_position": None,
                "agent_rotation": None,
                "episode_reward": 0.0,
                "step_count": 0,
                "last_action_success": True,
                "task_advancement": None,
                "max_task_advancement": None,
                "is_success": None,
                "task_type": None,
            }
            
            print(f"[WebSocket] Scene loaded: {task_description or 'LLM-generated scene'}")
            
            return {
                "success": True,
                "message": "Scene loaded successfully",
                "task_description": task_description,
            }
        except Exception as e:
            print(f"[WebSocket] Error loading scene dict: {e}")
            return {
                "success": False,
                "error": f"Failed to load scene: {str(e)}",
            }

    async def stream_frames(self, target_fps: int = 60):
        """Continuous frame streaming loop."""
        self.streaming = True
        frame_interval = 1.0 / target_fps
        
        try:
            while self.streaming:
                # Only send frames if there are connected clients
                if self.connections:
                    # Get current frame from environment
                    observation = self.env.render()
                    if observation is None:
                        observation = self.env._last_event.frame

                    # Broadcast to all clients
                    await self.broadcast_frame(observation, self.current_metrics)

                # Sleep to maintain target FPS
                await asyncio.sleep(frame_interval)
        except Exception as e:
            print(f"Error in stream_frames: {e}")
            self.streaming = False

    async def stop_streaming(self):
        """Stop the streaming loop."""
        self.streaming = False

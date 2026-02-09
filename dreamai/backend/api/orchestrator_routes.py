"""API routes for orchestrator and evaluation endpoints."""

from fastapi import APIRouter, HTTPException

# Import from backend.orchestrator (relative path from api -> up to backend -> down to orchestrator)
from ..orchestrator.task_generator import (
    TaskGenerationRequest,
    TaskGenerationResponse,
    generate_task_from_prompt,
    evaluate_episode,
)

router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])


@router.post("/generate_task", response_model=TaskGenerationResponse)
async def generate_task(request: TaskGenerationRequest) -> TaskGenerationResponse:
    """
    Generate a task specification from a natural language prompt.
    
    The prompt is processed to create:
    - Task description and goals
    - Success criteria
    - Optional subtasks
    - Scene configuration
    
    Request:
        {
            "prompt": "Pick up the apple and put it on the table",
            "max_steps": 500
        }
    
    Response:
        {
            "task": {
                "description": "...",
                "goal": "...",
                "success_criteria": [...],
                "max_steps": 500,
                "subtasks": []
            },
            "scene_id": "...",
            "message": "..."
        }
    """
    try:
        response = await generate_task_from_prompt(
            prompt=request.prompt,
            scene_id=request.scene_id,
            max_steps=request.max_steps,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/evaluate_episode")
async def evaluate_episode_endpoint(episode_data: dict) -> dict:
    """
    Evaluate an episode's performance.
    
    Request:
        {
            "total_reward": 10.5,
            "steps": 150,
            "max_steps": 500,
            "success": true
        }
    
    Response:
        {
            "success": true,
            "total_reward": 10.5,
            "steps": 150,
            "reward_per_step": 0.07,
            "efficiency": 0.3
        }
    """
    try:
        result = await evaluate_episode(episode_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

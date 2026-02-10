"""Task orchestration for prompt-based environment control."""

from typing import Optional
from pydantic import BaseModel, Field
from ..schemas import TaskSpec


class TaskGenerationRequest(BaseModel):
    """Request to generate a task from a natural language prompt."""

    prompt: str = Field(..., description="Natural language task description")
    scene_id: Optional[str] = Field(
        None, description="Optional scene ID to use for the task"
    )
    max_steps: int = Field(500, description="Maximum steps for the task")


class TaskGenerationResponse(BaseModel):
    """Response containing generated task specification."""

    task: TaskSpec
    scene_id: str
    message: str


async def generate_task_from_prompt(
    prompt: str,
    scene_id: Optional[str] = None,
    max_steps: int = 500,
) -> TaskGenerationResponse:
    """
    Generate a task specification from a natural language prompt.
    
    For now, this is a basic implementation that creates a TaskSpec
    from the prompt. In a full implementation, this would:
    1. Use LLM (e.g., Gemini via backend/llm/) to parse the prompt
    2. Extract objectives, success criteria, subtasks
    3. Generate reward shaping rules
    4. Handle scene generation/selection
    
    Args:
        prompt: Natural language description of the task
        scene_id: Optional scene to use (auto-generated if None)
        max_steps: Maximum steps allowed for the episode
    
    Returns:
        TaskGenerationResponse with generated TaskSpec
    """
    
    # TODO: Integrate with backend/llm/ to process prompt via LLM
    # For now, create a basic task from the prompt
    
    task = TaskSpec(
        description=prompt,
        goal=f"Complete the following: {prompt}",
        success_criteria=[
            "Agent completes the described task",
            "Task completed within step limit",
        ],
        max_steps=max_steps,
        subtasks=[],
    )
    
    scene_id = scene_id or "auto_generated"
    
    return TaskGenerationResponse(
        task=task,
        scene_id=scene_id,
        message=f"Task generated from prompt: {prompt[:50]}...",
    )


async def evaluate_episode(
    episode_data: dict,
) -> dict:
    """
    Evaluate an episode's performance.
    
    Args:
        episode_data: Episode stats including reward, steps, success
    
    Returns:
        Evaluation results and feedback
    """
    
    reward = episode_data.get("total_reward", 0)
    steps = episode_data.get("steps", 0)
    success = episode_data.get("success", False)
    
    return {
        "success": success,
        "total_reward": reward,
        "steps": steps,
        "reward_per_step": reward / steps if steps > 0 else 0,
        "efficiency": steps / episode_data.get("max_steps", 500),
    }

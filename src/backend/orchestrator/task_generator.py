"""Task orchestration for prompt-based environment control."""

import json
from typing import Optional, Any
from pydantic import BaseModel, Field
from ..schemas import TaskSpec
from ..schemas.declarative_spec import parse_task_description_dict_json
from ..llm.pipeline import run_orchestrator_llm, get_api_key
from .task_builder import build_task_from_type
from ..api.runtime_state import get_scene_names
from envs.ai2thor.procthor_adapter import get_builtin_scene_for_spec


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
    scene_dict: Optional[dict[str, Any]] = Field(
        None, description="Edited house dict for Controller(scene=...)"
    )


async def generate_task_from_prompt(
    prompt: str,
    scene_id: Optional[str] = None,
    max_steps: int = 500,
) -> TaskGenerationResponse:
    """
    Generate a task specification and pick a built-in scene from a natural language prompt.
    
    Pipeline:
    1. Use Orchestrator LLM to parse prompt -> DeclarativeSpec
    2. Use ProcTHOR adapter to select a built-in scene from DeclarativeSpec
    3. Extract TaskSpec from DeclarativeSpec
    
    Args:
        prompt: Natural language description of the task
        scene_id: Optional scene to use (auto-generated if None)
        max_steps: Maximum steps allowed for the episode
    
    Returns:
        TaskGenerationResponse with generated TaskSpec and scene_dict
    """
    
    if not get_api_key():
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not set")
    
    try:
        # Step 1: Run Orchestrator LLM to get DeclarativeSpec
        print(f"[Pipeline] Processing prompt: {prompt[:80]}...")
        declarative_spec = run_orchestrator_llm(prompt)
        print(
            "[Pipeline] DeclarativeSpec: goal_type=%r room_spec_id=%r room_preferences=%r object_requests=%r rl_task_type=%r task_description_dict=%s"
            % (
                declarative_spec.goal_type,
                declarative_spec.room_spec_id,
                declarative_spec.room_preferences,
                declarative_spec.object_requests,
                declarative_spec.rl_task_type,
                "present" if declarative_spec.task_description_dict else "null",
            )
        )
        
        # Step 2: Select a built-in iTHOR scene based on DeclarativeSpec
        scene_names = get_scene_names()
        scene_name = get_builtin_scene_for_spec(
            room_spec_id=declarative_spec.room_spec_id,
            room_preferences=declarative_spec.room_preferences,
            scene_names=scene_names,
        )
        print(f"[Pipeline] Selected built-in scene: {scene_name}")
        
        # Step 3: Create TaskSpec from DeclarativeSpec
        success_criteria = []
        
        # Build success criteria from DeclarativeSpec
        if declarative_spec.task_focus:
            success_criteria.append(f"Complete: {declarative_spec.task_focus}")
        else:
            success_criteria.append("Agent completes the described task")
        
        if declarative_spec.object_requests:
            success_criteria.append(f"Interact with requested objects: {', '.join(declarative_spec.object_requests)}")
        
        success_criteria.append("Task completed within step limit")
        
        # Build goal description
        goal = prompt if prompt else f"Complete task: {declarative_spec.task_focus or 'Unknown'}"
        
        extra = {}
        # Prefer structured task type over raw task_description_dict
        task_dict = None
        if declarative_spec.rl_task_type and declarative_spec.rl_task_params:
            try:
                params = json.loads(declarative_spec.rl_task_params)
            except (json.JSONDecodeError, TypeError):
                params = None
            if params and isinstance(params, dict):
                task_dict = build_task_from_type(
                    declarative_spec.rl_task_type,
                    params,
                )
        if task_dict is None and declarative_spec.task_description_dict:
            task_dict = parse_task_description_dict_json(declarative_spec.task_description_dict)
        if task_dict:
            extra["task_description_dict"] = task_dict
        if declarative_spec.policy_mode and declarative_spec.policy_mode in (
            "default", "fast", "sample_efficient", "exploration"
        ):
            extra["policy_mode"] = declarative_spec.policy_mode
        if declarative_spec.network_size and declarative_spec.network_size in (
            "small", "medium", "large"
        ):
            extra["network_size"] = declarative_spec.network_size

        task = TaskSpec(
            description=prompt,
            goal=goal,
            success_criteria=success_criteria,
            max_steps=max_steps,
            subtasks=[],
            extra=extra if extra else None,
        )

        scene_id = scene_id or scene_name

        return TaskGenerationResponse(
            task=task,
            scene_id=scene_id,
            message="Task generated",
            scene_dict=None,
        )
    
    except Exception as e:
        print(f"[Task Generator] Error: {e}")
        raise ValueError(f"Failed to generate task: {e}")


async def evaluate_episode(
    episode_data: dict,
) -> dict:
    """
    Evaluate an episode's performance.
    
    Args:
        episode_data: Episode stats including reward, steps, success
    
    Returns:
        Evaluation results with efficiency and success metrics
    """
    total_reward = episode_data.get("total_reward", 0.0)
    steps = episode_data.get("steps", 0)
    max_steps = episode_data.get("max_steps", 500)
    success = episode_data.get("success", False)
    
    # Calculate efficiency (reward per step, normalized)
    reward_per_step = total_reward / steps if steps > 0 else 0.0
    efficiency = 1.0 - (steps / max_steps) if max_steps > 0 else 0.0
    efficiency = max(0.0, efficiency)  # Clamp to [0, 1]
    
    return {
        "success": success,
        "total_reward": total_reward,
        "steps": steps,
        "max_steps": max_steps,
        "reward_per_step": reward_per_step,
        "efficiency": efficiency,
        "evaluation_summary": (
            f"Episode {'succeeded' if success else 'failed'}: "
            f"{total_reward:.2f} reward in {steps}/{max_steps} steps "
            f"(efficiency: {efficiency:.2%})"
        ),
    }

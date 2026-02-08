"""Task specification — filled by LLM / used by planner and env."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class TaskSpec(BaseModel):
    """Describes the task the agent should perform. Used by planner and env."""

    task_id: Optional[str] = Field(None, description="Unique task identifier")
    description: str = Field(..., description="Natural language task description")
    goal: Optional[str] = Field(None, description="Explicit goal statement")
    success_criteria: Optional[list[str]] = Field(None, description="Conditions for success")
    max_steps: Optional[int] = Field(None, description="Maximum environment steps")
    subtasks: Optional[list[str]] = Field(None, description="Optional ordered subtasks")
    extra: Optional[dict[str, Any]] = Field(None, description="Provider-specific fields")

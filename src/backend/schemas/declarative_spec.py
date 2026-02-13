"""Declarative spec — output of Orchestrator LLM; sanitized user intent."""

from typing import Optional

from pydantic import BaseModel, Field


class DeclarativeSpec(BaseModel):
    """Structured, guideline-compliant intent from user input. Consumed by Scene generator LLM."""

    goal_type: Optional[str] = Field(None, description="e.g. navigation, interaction, exploration")
    room_preferences: Optional[list[str]] = Field(
        None, description="Requested room types: Kitchen, LivingRoom, Bedroom, Bathroom"
    )
    object_requests: Optional[list[str]] = Field(
        None, description="Requested objects or focus (e.g. sofa, apple, table)"
    )
    task_focus: Optional[str] = Field(None, description="What the task is about (e.g. pick up, navigate to)")
    constraints: Optional[list[str]] = Field(None, description="Constraints or restrictions")
    style: Optional[str] = Field(None, description="Optional style hint (e.g. minimal, cluttered)")
    room_spec_id: Optional[str] = Field(
        None,
        description="ProcTHOR layout id; use exact id from allowed list to generate house with that layout.",
    )

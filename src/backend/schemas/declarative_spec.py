"""Declarative spec — output of Orchestrator LLM; sanitized user intent."""

from typing import Any, Optional

from pydantic import BaseModel, Field


# rl_thor Graph Task format: {item_id: {"properties": {key: value}, "relations": {related_id: [relation_type]}}}
# Properties: objectType (e.g. Apple, Plate), temperature (Hot, Cold, RoomTemp), isOpen, isToggled, isCooked, etc.
# Relations: contained_in, close_to, receptacle_of
RlThorTaskDict = dict[str, dict[str, Any]]


def parse_task_description_dict_json(s: Optional[str]) -> Optional[RlThorTaskDict]:
    """Parse task_description_dict from JSON string. Returns None if invalid or empty."""
    if not s or not s.strip():
        return None
    import json
    try:
        obj = json.loads(s)
        if isinstance(obj, dict) and obj:
            return obj
    except (json.JSONDecodeError, TypeError):
        pass
    return None


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
    task_description_dict: Optional[str] = Field(
        None,
        description="JSON string of rl_thor Graph Task: {item_id: {properties: {...}, relations: {...}}}. "
        "Use when user describes a concrete task (e.g. place apple on plate). Example: "
        '{"plate_receptacle": {"properties": {"objectType": "Plate"}}, "hot_apple": {"properties": {"objectType": "Apple", "temperature": "Hot"}, "relations": {"plate_receptacle": ["contained_in"]}}}',
    )

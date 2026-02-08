"""Scene specification — filled by LLM / used by env and ProcTHOR."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class SceneSpec(BaseModel):
    """Describes the scene the agent will run in. Used to configure env/ProcTHOR."""

    scene_id: Optional[str] = Field(None, description="Unique scene identifier")
    scene_name: Optional[str] = Field(None, description="e.g. FloorPlan28 or procedural")
    scene_type: Optional[str] = Field(None, description="e.g. kitchen, living_room, procedural")
    seed: Optional[int] = Field(None, description="Random seed for procedural generation")
    objectives: Optional[list[str]] = Field(None, description="Focus areas or target objects")
    extra: Optional[dict[str, Any]] = Field(None, description="Provider-specific config")

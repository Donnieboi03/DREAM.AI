"""House edit request — structured edits to HouseDict produced by Scene generator LLM."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Vector3(BaseModel):
    """Position or rotation (x, y, z)."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


class ObjectEdit(BaseModel):
    """Single edit: add, move, or remove an object."""

    action: Literal["add", "move", "remove"] = Field(..., description="Type of edit")
    object_id: Optional[str] = Field(None, description="Object id for move/remove (e.g. Apple|1)")
    asset_id: Optional[str] = Field(None, description="ProcTHOR assetId for add (e.g. Sofa_2)")
    room_id: Optional[str] = Field(None, description="Room id for add (e.g. room|1)")
    position: Optional[Vector3] = Field(None, description="World position for add/move")
    rotation: Optional[Vector3] = Field(None, description="Euler rotation in degrees for add/move")


class HouseEditRequest(BaseModel):
    """Structured edits to apply to a base house dict. Applied via apply_edits()."""

    object_edits: list[ObjectEdit] = Field(default_factory=list, description="Add/move/remove object edits")

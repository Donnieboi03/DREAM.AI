"""Scene generator LLM response — HouseEditRequest + EnvAugmentSpec."""

from pydantic import BaseModel

from .env_augment_spec import EnvAugmentSpec
from .house_edit_request import HouseEditRequest


class SceneGeneratorResponse(BaseModel):
    """Single response type from Scene generator LLM: edits to house JSON + per-env variability."""

    house_edit_request: HouseEditRequest
    env_augment_spec: EnvAugmentSpec

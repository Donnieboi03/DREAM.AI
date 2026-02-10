"""FastAPI routes: LLM pipeline (user input -> DeclarativeSpec, HouseEditRequest, EnvAugmentSpec)."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from dreamai.backend.schemas import HouseEditRequest
from dreamai.backend.llm import run_orchestrator_llm, run_scene_generator_llm, get_api_key
from dreamai.backend.orchestrator import get_house_summary, apply_edits
from dreamai.tools.validators import validate_declarative_spec_strict, validate_house_edit_request, validate_edited_house_dict


router = APIRouter(prefix="/llm", tags=["llm"])


class PipelineRequest(BaseModel):
    """Request body for the two-LLM pipeline."""

    user_input: str = Field(..., description="Freeform user input (e.g. 'I want a kitchen with a sofa')")
    house_summary: Optional[str] = Field(None, description="Optional pre-built house summary; if omitted, a default is used")


class PipelineResponse(BaseModel):
    """Response: DeclarativeSpec, HouseEditRequest, EnvAugmentSpec."""

    declarative_spec: dict
    house_edit_request: dict
    env_augment_spec: dict


def _default_house_summary() -> str:
    """Load ProcTHOR-10K train[0] and return its summary."""
    try:
        import prior
        dataset = prior.load_dataset(
            "procthor-10k",
            revision="ab3cacd0fc17754d4c080a3fd50b18395fae8647",
        )
        house = dataset["train"][0]
        return get_house_summary(house)
    except Exception as e:
        return f"House summary unavailable (prior/dataset error: {e}). Use house with rooms: room|1 (Kitchen), room|2 (LivingRoom)."


@router.post("/pipeline", response_model=PipelineResponse)
def run_llm_pipeline(req: PipelineRequest) -> PipelineResponse:
    """
    Run Orchestrator LLM then Scene generator LLM: user_input -> DeclarativeSpec (validated)
    -> HouseEditRequest + EnvAugmentSpec. Optionally pass house_summary; otherwise a default is used.
    """
    if not get_api_key():
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY or GOOGLE_API_KEY not set")
    house_summary = req.house_summary or _default_house_summary()
    try:
        declarative = run_orchestrator_llm(req.user_input)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orchestrator LLM failed: {e}")
    validate_declarative_spec_strict(declarative)
    try:
        scene_response = run_scene_generator_llm(declarative, house_summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scene generator LLM failed: {e}")
    return PipelineResponse(
        declarative_spec=declarative.model_dump(),
        house_edit_request=scene_response.house_edit_request.model_dump(),
        env_augment_spec=scene_response.env_augment_spec.model_dump(),
    )


class ApplyEditsRequest(BaseModel):
    """Request to apply HouseEditRequest to a base house (e.g. from pipeline response)."""

    base_house: dict[str, Any] = Field(..., description="Base house dict (e.g. ProcTHOR-10K or procedural)")
    house_edit_request: dict = Field(..., description="HouseEditRequest as dict (from pipeline)")


@router.post("/apply-edits")
def api_apply_edits(req: ApplyEditsRequest) -> dict[str, Any]:
    """Apply HouseEditRequest to base_house; return edited house dict for Controller(scene=...)."""
    from dreamai.backend.schemas import HouseEditRequest
    edit_req = HouseEditRequest.model_validate(req.house_edit_request)
    edited = apply_edits(req.base_house, edit_req)
    errs = validate_edited_house_dict(edited)
    if errs:
        raise HTTPException(status_code=400, detail="Edited house validation failed: " + "; ".join(errs))
    return edited

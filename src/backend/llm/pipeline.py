"""Two-LLM pipeline: Orchestrator -> Scene generator with structured output via google.genai (no Instructor)."""

from __future__ import annotations

from typing import Any, Optional, TypeVar

from pydantic import BaseModel

from ..schemas import DeclarativeSpec, SceneGeneratorResponse
from .client import create_client, get_api_key
from .prompts import (
    get_orchestrator_system,
    SCENE_GENERATOR_SYSTEM,
    build_orchestrator_user_prompt,
    build_scene_generator_user_prompt,
)
from .schema_docs import get_house_schema_doc


# Model id for Gemini (google.genai SDK)
GEMINI_MODEL = "gemini-2.5-flash"

T = TypeVar("T")


def _resolve_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Inline $defs into the schema so google.genai accepts nested Pydantic models (see python-genai#60)."""
    if "$defs" not in schema:
        return schema
    schema = dict(schema)
    defs = schema.pop("$defs", {})

    def _resolve(obj: dict[str, Any]) -> None:
        if "$ref" in obj:
            ref = obj.pop("$ref")
            key = ref.split("/")[-1]
            if key in defs:
                obj.update(_resolve_json_schema(dict(defs[key])))
                _resolve(obj)
        for v in obj.values():
            if isinstance(v, dict):
                _resolve(v)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        _resolve(item)

    _resolve(schema)
    return schema


# Keys Pydantic v2 emits that Gemini response_schema does not support (400 INVALID_ARGUMENT).
_GEMINI_UNSUPPORTED_SCHEMA_KEYS = frozenset(
    {"additionalProperties", "unevaluatedProperties", "contentEncoding", "contentMediaType"}
)


def _sanitize_schema_for_gemini(schema: dict[str, Any]) -> None:
    """Strip JSON Schema keywords that Gemini rejects. Mutates in place."""
    for key in list(schema.keys()):
        if key in _GEMINI_UNSUPPORTED_SCHEMA_KEYS:
            del schema[key]
    for v in schema.values():
        if isinstance(v, dict):
            _sanitize_schema_for_gemini(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    _sanitize_schema_for_gemini(item)


# Minimal object schema for array items when item is free-form dict (Gemini requires non-empty properties).
_MINIMAL_OBJECT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"_": {"type": "string", "description": "Optional extra data"}},
}


def _drop_empty_object_properties(schema: dict[str, Any]) -> None:
    """Remove or fix OBJECTs with no/empty 'properties' so Gemini accepts the schema. Mutates in place."""
    if "properties" in schema:
        props = schema["properties"]
        to_drop = []
        for key, sub in list(props.items()):
            if isinstance(sub, dict):
                if sub.get("type") == "object" and not sub.get("properties"):
                    to_drop.append(key)
                else:
                    _drop_empty_object_properties(sub)
        for key in to_drop:
            del props[key]
        if to_drop and "required" in schema and isinstance(schema["required"], list):
            schema["required"] = [r for r in schema["required"] if r not in to_drop]
    if "items" in schema and isinstance(schema["items"], dict):
        items = schema["items"]
        if items.get("type") == "object" and not items.get("properties"):
            schema["items"] = dict(_MINIMAL_OBJECT_SCHEMA)
        else:
            _drop_empty_object_properties(schema["items"])
    for v in schema.values():
        if isinstance(v, dict):
            _drop_empty_object_properties(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    _drop_empty_object_properties(item)


def _generate_structured(
    system: str,
    user_content: str,
    response_model: type[T],
) -> T:
    """Call Gemini with system + user content and parse response into response_model (Pydantic)."""
    from google.genai import types
    from google.genai.errors import ClientError

    client = create_client()
    raw_schema = response_model.model_json_schema() if issubclass(response_model, BaseModel) else {}
    schema = _resolve_json_schema(dict(raw_schema))
    _sanitize_schema_for_gemini(schema)
    _drop_empty_object_properties(schema)
    config = types.GenerateContentConfig(
        system_instruction=system,
        response_mime_type="application/json",
        response_schema=schema,
    )
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_content,
            config=config,
        )
        
        # Log token usage if available
        if hasattr(response, 'usage_metadata'):
            usage = response.usage_metadata
            prompt_tokens = getattr(usage, 'prompt_token_count', 0)
            output_tokens = getattr(usage, 'candidates_token_count', 0)
            total_tokens = getattr(usage, 'total_token_count', 0)
            print(f"[LLM] Tokens - Input: {prompt_tokens}, Output: {output_tokens}, Total: {total_tokens}")
        
        text = getattr(response, "text", None) or ""
        if not text or not text.strip():
            raise RuntimeError("Empty or invalid response from Gemini")
        return response_model.model_validate_json(text)
    except ClientError as e:
        is_429 = (
            getattr(e, "status_code", None) == 429
            or "429" in str(e)
            or "RESOURCE_EXHAUSTED" in str(e)
        )
        if is_429:
            raise RuntimeError(
                "Gemini API quota exceeded (429). Free tier allows ~20 requests/day. "
                "Wait and retry later, or check billing: https://ai.google.dev/gemini-api/docs/rate-limits"
            ) from e
        raise


def _get_room_spec_ids_for_orchestrator() -> list[str]:
    """Return valid ProcTHOR room_spec_ids for the Orchestrator prompt; fallback if procthor not available."""
    try:
        from src.envs.ai2thor.procthor_adapter import get_procthor_room_spec_ids
        return get_procthor_room_spec_ids()
    except ImportError:
        return [
            "kitchen", "living-room", "bedroom", "bathroom",
            "kitchen-living-room", "2-bed-1-bath", "2-bed-2-bath",
            "4-room", "5-room", "bedroom-bathroom",
            "kitchen-living-bedroom-room", "kitchen-living-bedroom-room2",
        ]


def run_orchestrator_llm(user_input: str) -> DeclarativeSpec:
    """Run Orchestrator LLM: user input -> DeclarativeSpec (sanitized, guideline-compliant)."""
    if not get_api_key():
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not set")
    room_spec_ids = _get_room_spec_ids_for_orchestrator()
    system = get_orchestrator_system(room_spec_ids)
    user_content = build_orchestrator_user_prompt(user_input)
    return _generate_structured(system, user_content, DeclarativeSpec)


def run_scene_generator_llm(
    declarative_spec: DeclarativeSpec,
    house_summary: str,
    asset_id_allowlist: Optional[list[str]] = None,
) -> SceneGeneratorResponse:
    """Run Scene generator LLM: DeclarativeSpec + house summary -> HouseEditRequest + EnvAugmentSpec."""
    if not get_api_key():
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not set")
    house_schema_doc = get_house_schema_doc(asset_id_allowlist=asset_id_allowlist)
    user_content = build_scene_generator_user_prompt(
        declarative_spec=declarative_spec.model_dump_json(indent=2),
        house_summary=house_summary,
        house_schema_doc=house_schema_doc,
    )
    return _generate_structured(SCENE_GENERATOR_SYSTEM, user_content, SceneGeneratorResponse)


def run_full_pipeline(
    user_input: str,
    house_summary: str,
    asset_id_allowlist: Optional[list[str]] = None,
) -> tuple[DeclarativeSpec, SceneGeneratorResponse]:
    """Run Orchestrator LLM then Scene generator LLM. Returns (DeclarativeSpec, SceneGeneratorResponse)."""
    declarative = run_orchestrator_llm(user_input)
    scene_response = run_scene_generator_llm(
        declarative_spec=declarative,
        house_summary=house_summary,
        asset_id_allowlist=asset_id_allowlist,
    )
    return declarative, scene_response

"""Validate DeclarativeSpec (post-Orchestrator LLM) against guidelines."""

from __future__ import annotations

from dreamai.backend.schemas import DeclarativeSpec

ALLOWED_ROOM_TYPES = {"Kitchen", "LivingRoom", "Bedroom", "Bathroom"}
ALLOWED_GOAL_TYPES = {"navigation", "interaction", "exploration", "pickup", "place", "search", "open", "close"}

# Fallback when procthor adapter is not importable (e.g. in tests without procthor).
FALLBACK_ROOM_SPEC_IDS = frozenset({
    "kitchen", "living-room", "bedroom", "bathroom",
    "kitchen-living-room", "2-bed-1-bath", "2-bed-2-bath",
    "4-room", "5-room", "7-room-3-bed", "8-room-3-bed",
    "12-room", "12-room-3-bed", "bedroom-bathroom",
    "kitchen-living-bedroom-room", "kitchen-living-bedroom-room2",
})


def _get_allowed_room_spec_ids() -> frozenset[str]:
    """Return valid ProcTHOR room_spec_ids for validation."""
    try:
        from dreamai.envs.ai2thor.procthor_adapter import get_procthor_room_spec_ids
        return frozenset(get_procthor_room_spec_ids())
    except ImportError:
        return FALLBACK_ROOM_SPEC_IDS


def validate_declarative_spec(spec: DeclarativeSpec) -> list[str]:
    """
    Validate DeclarativeSpec against guidelines. Returns list of error messages (empty if valid).
    Kept permissive for house augments: unknown room_spec_id is only warned (not an error).
    """
    errors: list[str] = []
    if spec.room_preferences:
        for r in spec.room_preferences:
            if r not in ALLOWED_ROOM_TYPES:
                errors.append(f"room_preferences contains disallowed room type: {r!r}. Allowed: {ALLOWED_ROOM_TYPES}")
            if len(errors) > 0:
                break
    if spec.room_spec_id is not None:
        allowed = _get_allowed_room_spec_ids()
        if spec.room_spec_id not in allowed:
            # Permissive: log warning but do not fail validation so LLM augments are not over-strict
            import logging
            logging.getLogger(__name__).warning(
                "room_spec_id %r is not in ProcTHOR allowed list (will try anyway). Allowed: %s",
                spec.room_spec_id,
                sorted(allowed),
            )
    if spec.goal_type and spec.goal_type.lower() not in {g.lower() for g in ALLOWED_GOAL_TYPES}:
        # Allow other goal types but warn; or strict: errors.append(...)
        pass
    return errors


def validate_declarative_spec_strict(spec: DeclarativeSpec) -> None:
    """Raise ValueError if spec fails validation."""
    errs = validate_declarative_spec(spec)
    if errs:
        raise ValueError("DeclarativeSpec validation failed: " + "; ".join(errs))

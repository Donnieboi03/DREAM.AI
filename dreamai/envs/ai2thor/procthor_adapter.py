"""ProcTHOR adapter: create procedural scenes and return a controller + house spec."""

from __future__ import annotations

from typing import Any, Optional

try:
    from dreamai.backend.schemas import SceneSpec as _SceneSpec
except ImportError:
    _SceneSpec = None


def create_procthor_scene(
    seed: Optional[int] = None,
    split: str = "train",
    scene_spec: Optional["_SceneSpec"] = None,
    room_spec_id: Optional[str] = None,
    quality: str = "Low",
    max_retries: int = 2,
    **house_generator_kwargs: Any,
) -> tuple[Any, Any]:
    """Create a ProcTHOR scene and return (controller, house) for use with ThorEnv.

    The controller has the procedural scene already loaded. Pass it to ThorEnv(controller=controller).
    Optionally pass a SceneSpec (e.g. from LLM) to use seed or objectives; otherwise uses default sampler.
    Use room_spec_id to generate from a specific house config (e.g. "2-bed-1-bath", "kitchen-living-room").

    What the config controls:
      - room_spec_id fixes which ROOM TYPES exist (e.g. 2 bed, 1 bath). Layout, object
        placement, colors, and states are still procedural and controlled by seed.
      - Same room_spec_id + same seed = same house. Different seed = different house.
    For finer control (e.g. floorplan scale, max object counts), pass ProcTHOR options
    via house_generator_kwargs (e.g. HouseGenerator accepts sampling_vars in sample()).

    If "Unable to CreateHouse!" occurs (e.g. on some Mac/headless setups), the exception propagates;
    callers can fall back to ThorEnv(scene_name=\"FloorPlan1\") or load from ProcTHOR-10K.

    Returns:
        (controller, house): ai2thor Controller with scene loaded, and the House object (for logging/serialization).
    """
    from procthor.generation import PROCTHOR10K_ROOM_SPEC_SAMPLER, HouseGenerator

    seed = seed if seed is not None else (getattr(scene_spec, "seed", None) if scene_spec else None)
    last_error = None
    for attempt in range(max(1, max_retries)):
        try:
            gen_kwargs: dict[str, Any] = {
                "split": split,
                "seed": seed if attempt == 0 else (seed + 1 + attempt) if seed is not None else None,
                "room_spec_sampler": PROCTHOR10K_ROOM_SPEC_SAMPLER,
                **house_generator_kwargs,
            }
            if room_spec_id is not None:
                gen_kwargs["room_spec"] = room_spec_id
            generator = HouseGenerator(**gen_kwargs)
            house, _ = generator.sample()
            house.validate(generator.controller)
            return generator.controller, house
        except AssertionError as e:
            last_error = e
            if "CreateHouse" not in str(e) and "Unable to" not in str(e):
                raise
            continue
    raise last_error


def scene_spec_to_procthor_options(scene_spec: Optional["_SceneSpec"]) -> dict[str, Any]:
    """Convert SceneSpec to kwargs for create_procthor_scene (seed, etc.)."""
    if scene_spec is None:
        return {}
    opts: dict[str, Any] = {}
    s = getattr(scene_spec, "seed", None)
    if s is not None:
        opts["seed"] = s
    return opts

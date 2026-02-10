"""ProcTHOR adapter: create procedural scenes and return a controller + house spec."""

from __future__ import annotations

from typing import Any, Optional

try:
    from dreamai.backend.schemas import SceneSpec as _SceneSpec
except ImportError:
    _SceneSpec = None


def get_procthor_room_spec_ids() -> list[str]:
    """Return valid ProcTHOR room_spec_id values from PROCTHOR10K_ROOM_SPEC_SAMPLER.

    Used by the Orchestrator LLM prompt and by DeclarativeSpec validation so the model
    knows which layout ids it can output (e.g. 2-bed-1-bath, 12-room, kitchen-living-room).
    """
    try:
        from procthor.generation import PROCTHOR10K_ROOM_SPEC_SAMPLER
        return sorted(PROCTHOR10K_ROOM_SPEC_SAMPLER.room_spec_map.keys())
    except Exception:
        return [
            "kitchen", "living-room", "bedroom", "bathroom",
            "kitchen-living-room", "2-bed-1-bath", "2-bed-2-bath",
            "4-room", "5-room", "7-room-3-bed", "8-room-3-bed",
            "12-room", "12-room-3-bed", "bedroom-bathroom",
            "kitchen-living-bedroom-room", "kitchen-living-bedroom-room2",
        ]


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


def make_procthor_env(
    width: int = 400,
    height: int = 400,
    scene_spec: Optional["_SceneSpec"] = None,
) -> "Any":
    """Create a procedural AI2-THOR environment for interactive control.
    
    This initializes a ProcTHOR scene with the given dimensions and optionally
    a specific scene specification (e.g., from a task generator).
    
    If ProcTHOR fails (e.g., "Unable to CreateHouse!"), falls back to a regular
    AI2-THOR scene (FloorPlan1).
    
    Args:
        width: Canvas width in pixels (default 400)
        height: Canvas height in pixels (default 400)
        scene_spec: Optional SceneSpec to control procedural generation (e.g., seed)
        
    Returns:
        ThorEnv: An environment wrapper for interactive control of the procedural scene.
    """
    from .thor_env import ThorEnv
    
    # Try to create a ProcTHOR scene first
    try:
        options = scene_spec_to_procthor_options(scene_spec)
        controller, house = create_procthor_scene(**options)
        env = ThorEnv(controller=controller, width=width, height=height, render_mode="rgb_array")
        print("✓ ProcTHOR environment initialized successfully")
        return env
    except Exception as e:
        print(f"⚠ ProcTHOR initialization failed: {e}")
        print("  Falling back to regular AI2-THOR scene (FloorPlan1)...")
        
        # Fallback to regular AI2-THOR scene
        try:
            from ai2thor.controller import Controller
            
            controller = Controller(
                scene="FloorPlan1",
                gridSize=0.25,
                visibilityDistance=1.5,
            )
            
            env = ThorEnv(controller=controller, width=width, height=height, render_mode="rgb_array")
            print("✓ Fallback AI2-THOR environment initialized successfully")
            return env
        except Exception as fallback_error:
            print(f"✗ Both ProcTHOR and fallback initialization failed!")
            print(f"  Original error: {e}")
            print(f"  Fallback error: {fallback_error}")
            raise RuntimeError(
                f"Failed to initialize environment. "
                f"ProcTHOR: {e}. Fallback: {fallback_error}"
            )


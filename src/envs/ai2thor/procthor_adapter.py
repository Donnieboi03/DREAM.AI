"""ProcTHOR adapter: create procedural scenes and return a controller + house spec."""

from __future__ import annotations

import random
from typing import Any, Optional

try:
    from src.backend.schemas import SceneSpec as _SceneSpec
except ImportError:
    _SceneSpec = None

# ProcTHOR-10K dataset revision for lookup (kept for optional use)
PROCTHOR_10K_REVISION = "ab3cacd0fc17754d4c080a3fd50b18395fae8647"

# iTHOR convention: 30 scenes per room type (https://ai2thor.allenai.org/ithor/documentation/scenes)
# Kitchens 1-30, Living 201-230, Bedrooms 301-330, Bathrooms 401-430 (120 total).
# Use only FloorPlan*_physics names (matches controller.ithor_scenes() in typical builds).
_ITHOR_KITCHENS = [f"FloorPlan{i}_physics" for i in range(1, 31)]
_ITHOR_LIVING = [f"FloorPlan{i}_physics" for i in range(201, 231)]
_ITHOR_BEDROOMS = [f"FloorPlan{i}_physics" for i in range(301, 331)]
_ITHOR_BATHROOMS = [f"FloorPlan{i}_physics" for i in range(401, 431)]

# Map room_spec_id to iTHOR candidate lists (FloorPlan*_physics only).
BUILTIN_SCENE_CANDIDATES: dict[str, list[str]] = {
    "kitchen": _ITHOR_KITCHENS,
    "living-room": _ITHOR_LIVING,
    "bedroom": _ITHOR_BEDROOMS,
    "bathroom": _ITHOR_BATHROOMS,
    "kitchen-living-room": _ITHOR_KITCHENS + _ITHOR_LIVING,
    "2-bed-1-bath": _ITHOR_BEDROOMS + _ITHOR_BATHROOMS,
    "2-bed-2-bath": _ITHOR_BEDROOMS + _ITHOR_BATHROOMS,
    "4-room": _ITHOR_KITCHENS + _ITHOR_LIVING,
    "5-room": _ITHOR_LIVING + _ITHOR_KITCHENS,
    "7-room-3-bed": _ITHOR_BEDROOMS,
    "8-room-3-bed": _ITHOR_BEDROOMS,
    "12-room": _ITHOR_KITCHENS + _ITHOR_LIVING + _ITHOR_BEDROOMS,
    "12-room-3-bed": _ITHOR_BEDROOMS,
    "bedroom-bathroom": _ITHOR_BEDROOMS + _ITHOR_BATHROOMS,
    "kitchen-living-bedroom-room": _ITHOR_KITCHENS + _ITHOR_LIVING + _ITHOR_BEDROOMS,
    "kitchen-living-bedroom-room2": _ITHOR_KITCHENS + _ITHOR_LIVING + _ITHOR_BEDROOMS,
}
DEFAULT_BUILTIN_SCENE = "FloorPlan1_physics"


def get_builtin_scene_names(controller: Any) -> list[str]:
    """Return sorted list of built-in scene names in this AI2-THOR build (controller.scenes_in_build)."""
    scenes = getattr(controller, "scenes_in_build", None)
    if scenes is None:
        return []
    return sorted(scenes)


def get_ithor_scene_names(controller: Any) -> Optional[list[str]]:
    """Return iTHOR FloorPlan scene list (e.g. FloorPlan*_physics) when available, else None.

    Use this for scene selection so we prefer the 120 iTHOR scenes instead of scenes_in_build
    which can include ArchitecTHOR and put them first when sorted.
    """
    meth = getattr(controller, "ithor_scenes", None)
    if not callable(meth):
        return None
    try:
        scenes = meth()
        return list(scenes) if scenes else None
    except Exception:
        return None


def _ithor_floorplan_scenes(scene_names: list[str]) -> list[str]:
    """Return scene names that follow iTHOR FloorPlan convention: FloorPlanN or FloorPlanN_physics."""
    out = []
    for s in scene_names:
        if not s.startswith("FloorPlan") or len(s) < 9:
            continue
        rest = s[9:]
        if rest.isdigit():
            out.append(s)
        elif rest.endswith("_physics") and rest[:-7].isdigit():
            out.append(s)
    return out


def _architecthor_scenes(scene_names: list[str]) -> list[str]:
    """Return scene names that follow ArchitecTHOR convention (e.g. ArchitecTHOR-Test-00, ArchitecTHOR-Test-01)."""
    return [s for s in scene_names if s.startswith("ArchitecTHOR")]


def get_builtin_scene_for_spec(
    room_spec_id: Optional[str] = None,
    room_preferences: Optional[list[str]] = None,
    scene_names: Optional[list[str]] = None,
) -> str:
    """Pick a built-in scene name that matches the LLM spec. Uses FloorPlan*_physics candidates only.

    When scene_names come from controller.ithor_scenes() we get the 120 iTHOR scenes. If the build
    has only ArchitecTHOR, we sample from those instead (no room-type mapping).
    """
    if not scene_names:
        return DEFAULT_BUILTIN_SCENE
    ithor_only = _ithor_floorplan_scenes(scene_names)
    architecthor_only = _architecthor_scenes(scene_names)
    scene_set = set(ithor_only) if ithor_only else set(scene_names)
    candidates: list[str] = []
    key_source: str = "none"
    # Prefer room_spec_id mapping (FloorPlan*_physics lists)
    if room_spec_id:
        rid = (room_spec_id or "").strip().lower()
        candidates = BUILTIN_SCENE_CANDIDATES.get(rid, [])
        key_source = "room_spec_id=%r" % rid
    # Else room_preferences
    if not candidates and room_preferences:
        pref_to_list = {
            "kitchen": BUILTIN_SCENE_CANDIDATES["kitchen"],
            "livingroom": BUILTIN_SCENE_CANDIDATES["living-room"],
            "bedroom": BUILTIN_SCENE_CANDIDATES["bedroom"],
            "bathroom": BUILTIN_SCENE_CANDIDATES["bathroom"],
        }
        for p in room_preferences:
            key = (p or "").strip().lower().replace(" ", "")
            if key in pref_to_list:
                candidates.extend(pref_to_list[key])
        key_source = "room_preferences=%s" % (room_preferences,)
    available = [c for c in candidates if c in scene_set]
    if available:
        chosen = random.choice(available)
        print("[E2E] Room candidate key: %s; sampled from %d available iTHOR scene(s), chosen: %s" % (key_source, len(available), chosen))
        return chosen
    if key_source != "none" and architecthor_only:
        chosen = random.choice(architecthor_only)
        print("[E2E] Room candidate key: %s; build has ArchitecTHOR only (no iTHOR FloorPlan), sampled from %d ArchitecTHOR scene(s), chosen: %s" % (key_source, len(architecthor_only), chosen))
        return chosen
    if key_source != "none":
        if not ithor_only and not architecthor_only:
            print("[E2E] Room candidate key: %s; build has no iTHOR or ArchitecTHOR scenes, using first scene as fallback" % key_source)
        elif not ithor_only:
            print("[E2E] Room candidate key: %s; no matching scenes in build, using fallback" % key_source)
    if ithor_only and DEFAULT_BUILTIN_SCENE in scene_set:
        return DEFAULT_BUILTIN_SCENE
    return scene_names[0]


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


def get_house_from_10k_by_room_spec(
    room_spec_ids: Optional[list[str]] = None,
    revision: str = PROCTHOR_10K_REVISION,
    split: str = "train",
) -> dict[str, Any]:
    """Find a house in ProcTHOR-10K whose metadata.roomSpecId matches one of the requested IDs.

    The LLM parses the user prompt and outputs room_spec_id(s). We iterate the 10K dataset
    and return the first house that has all requirements (i.e. its roomSpecId is in
    room_spec_ids). If room_spec_ids is None or empty, returns the first house in the split.
    Logs how many scenes were checked before finding a match.

    Returns:
        House dict (rooms, objects, metadata, ...) for use with apply_edits / CreateHouse.
    """
    import prior

    dataset = prior.load_dataset("procthor-10k", revision=revision)
    try:
        split_data = dataset[split]
    except (KeyError, TypeError) as e:
        available = getattr(dataset, "keys", lambda: None)()
        available = list(available) if callable(available) and available else "unknown"
        raise ValueError("ProcTHOR-10K has no split %r (available: %s): %s" % (split, available, e)) from e
    n = len(split_data)

    # Normalize requested IDs for comparison (JSON uses roomSpecId, may vary in casing)
    want = set((s or "").strip().lower() for s in (room_spec_ids or []) if (s or "").strip())

    for i in range(n):
        house = split_data[i]
        if not isinstance(house, dict):
            continue
        meta = house.get("metadata") or {}
        spec_id = meta.get("roomSpecId") or meta.get("room_spec_id")
        if spec_id is None:
            continue
        spec_id_normalized = str(spec_id).strip().lower()
        if not want:
            print("[E2E] Using first house from ProcTHOR-10K (no room_spec_id filter); scene index 0.")
            return house
        if spec_id_normalized in want:
            print("[E2E] Found matching house after checking %d scene(s) (roomSpecId=%r)." % (i + 1, spec_id))
            return house

    # No match: if we had requirements, return first house as fallback
    if want:
        print("[E2E] No house with roomSpecId in %s after checking %d scenes; using first house as fallback." % (list(want), n))
        return split_data[0]
    return split_data[0]


def create_procthor_scene(
    seed: Optional[int] = None,
    split: str = "train",
    scene_spec: Optional["_SceneSpec"] = None,
    room_spec_id: Optional[str] = None,
    quality: str = "Low",
    max_retries: int = 2,
    **house_generator_kwargs: Any,
) -> tuple[Any, Any]:
    """Create a ProcTHOR scene procedurally and return (controller, house). SAVED FOR LATER.

    Default scene "generation" is now via 10K lookup: get_house_from_10k_by_room_spec().
    This function is kept for optional use (e.g. --use-procthor-generate) or when 10K
    lookup is not desired. It runs HouseGenerator.sample() and requires CreateHouse
    support (often not available on macOS/headless).

    The controller has the procedural scene already loaded. Pass it to ThorEnv(controller=controller).
    Optionally pass a SceneSpec (e.g. from LLM) to use seed or objectives; otherwise uses default sampler.
    Use room_spec_id to generate from a specific house config (e.g. "2-bed-1-bath", "kitchen-living-room").

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


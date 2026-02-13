#!/usr/bin/env python3
"""Single ProcTHOR demo script: load or generate a house, then drive with keyboard.

Intent
------
  - Validate that ProcTHOR, AI2-THOR, and ProcTHOR-10K work in your environment.
  - Demonstrate the three scene sources (example schema, dataset, config/generation)
    that DreamAI uses for training and evaluation.
  - Expose the house dict schema so scenes can be driven by an LLM or custom code
    (e.g. controlled random layouts from user input).

Requirements
------------
  - ProcTHOR: install from the official repo (git clone https://github.com/allenai/procthor;
    cd procthor && pip install -e .) so it works correctly; the PyPI package may be out of sync.
  - DreamAI deps: pip install -r requirements.txt (ai2thor, prior, pynput, etc.).
  - See README.md and ARCHITECTURE.md for full setup and run instructions.

House sources
-------------
  1. Example schema (--use-example-schema): canonical example house dict from ProcTHOR-10K.
  2. Dataset mode (default): load from ProcTHOR-10K by --split, --index, or --random.
  3. Config mode (--config <room_spec_id>): try procedural generation; on failure fall back to 10K.

Schema and inspection
---------------------
  --print-schema   Print house customization schema (HouseDict types) for LLMs or editing.
  --print-example  Dump the example house dict as JSON (see exact format).
  --print-example-to FILE  Write JSON to file. --print-example-max-objects N  Truncate objects list.

How to run
----------
  From src/:   python scripts/run_proc_test.py [options]
  From repo root:  PYTHONPATH=. python src/scripts/run_proc_test.py [options]

Examples:
  python scripts/run_proc_test.py
  python scripts/run_proc_test.py --config 2-bed-1-bath --seed 42
  python scripts/run_proc_test.py --split val --index 5
  python scripts/run_proc_test.py --random --seed 123
  python scripts/run_proc_test.py --config 4-room --no-fullscreen --width 1920 --height 1080
  python scripts/run_proc_test.py --print-schema
  python scripts/run_proc_test.py --use-example-schema
  python scripts/run_proc_test.py --print-example
  python scripts/run_proc_test.py --print-example --print-example-to example_house.json
"""

# -----------------------------------------------------------------------------
# House schema for customizations (ProcTHOR / AI2-THOR CreateHouse)
# -----------------------------------------------------------------------------
# The scene is a single dict (HouseDict) passed to Controller(scene=...) or
# CreateHouse(house=...). You can load it from ProcTHOR-10K, from ProcTHOR
# generation (house.data), or produce/edit it yourself for LLM-driven layouts.
#
# Top-level keys:
#
#   rooms        List[RoomType]   Room definitions (type, floor polygon, id).
#   walls        List[Wall]       Wall geometry and material per room.
#   doors        List[Door]       Door assets between rooms.
#   windows      List[Window]     Window assets and cutouts.
#   objects      List[Object]     All placeable objects (position, rotation, assetId).
#   proceduralParameters  Dict   Lights, skybox, receptacle height, etc.
#   metadata     Dict            Agent start pose, schema version, warnings (optional).
#
# Types for house customizations:
#
#   Vector3:  { "x": float, "y": float, "z": float }
#
#   RoomType:
#     id: str              e.g. "room|1"
#     roomType: str        "Kitchen" | "LivingRoom" | "Bedroom" | "Bathroom"
#     floorMaterial: str
#     floorPolygon: List[Vector3]   Floor boundary in world (x,y,z) points.
#     ceilings: list
#     children: list
#
#   Wall:
#     id: str              e.g. "wall|1|..."
#     roomId: str          e.g. "room|1"
#     polygon: List[Vector3]   Four corners (bottom/top) of the wall quad.
#     material: str
#     empty: bool (optional)   True if no door/window cutout.
#
#   Door:
#     id: str
#     assetId: str         Asset identifier in the asset database.
#     boundingBox: { "min": Vector3, "max": Vector3 }
#     openness: float      0–1
#     openable: bool
#     room0, room1: str    Room ids this door connects.
#     wall0, wall1: str    Wall ids.
#
#   Window:
#     id: str
#     assetId: str
#     boundingBox: { "min": Vector3, "max": Vector3 }
#     room0, room1: str | None
#     wall0, wall1: str | None
#     assetOffset: Vector3   Used for wall cutout size.
#
#   Object (placeable furniture, etc. — use this for "put bed here"):
#     id: str
#     assetId: str         e.g. "Bed_1", "Sofa_2" (from ProcTHOR asset DB).
#     position: Vector3    World (x, y, z) — main field for placement.
#     rotation: Vector3    Euler angles (x, y, z) in degrees.
#     children: List[Object]   Objects parented to this (e.g. on a shelf).
#     kinematic: bool      True = moveable by agent, False = fixed.
#
#   ProceduralParameters:
#     ceilingMaterial: str
#     ceilingColor: { "r", "g", "b" } (0–1)
#     lights: List[Light]   Each has id, position, rotation, type, rgb, intensity, etc.
#     skyboxId: str
#     receptacleHeight: float
#     floorColliderThickness: float
#
# To customize a house: load a dict (e.g. from dataset["train"][0] or house.data),
# edit "objects" (position/rotation), "rooms", "walls", etc., then pass the dict
# to Controller(scene=edited_house_dict). See ProcTHOR procthor.utils.types for
# full TypedDict definitions.
#
# Flow: The house is always a dict (HouseDict). There is no conversion step—you
# get the dict from (1) the dataset, (2) house.data after create_procthor_scene,
# or (3) your own code. That dict is passed as the scene= argument to
# Controller(scene=house_dict). AI2-THOR then calls CreateHouse(house=...) with
# that same dict. Use --print-example to dump an example dict as JSON so you can
# see the exact structure.
# -----------------------------------------------------------------------------

HOUSE_SCHEMA_DOC = r"""
House schema (HouseDict) for ProcTHOR / AI2-THOR CreateHouse
============================================================
Top-level keys: rooms, walls, doors, windows, objects, proceduralParameters, metadata

  rooms: List[RoomType]
    - id (str), roomType ("Kitchen"|"LivingRoom"|"Bedroom"|"Bathroom")
    - floorPolygon: List[{x,y,z}], floorMaterial, ceilings, children

  walls: List[Wall]
    - id, roomId, polygon (List[{x,y,z}]), material, empty (optional)

  doors: List[Door]
    - id, assetId, boundingBox {min,max}, openness, openable, room0, room1, wall0, wall1

  windows: List[Window]
    - id, assetId, boundingBox, room0, room1, wall0, wall1, assetOffset {x,y,z}

  objects: List[Object]   <- Use for "place bed/sofa here"
    - id, assetId, position {x,y,z}, rotation {x,y,z}, children [], kinematic

  proceduralParameters: lights, skyboxId, ceilingMaterial, ceilingColor, receptacleHeight, floorColliderThickness

  metadata: agent (start pose), schema version, warnings (optional)
"""

import argparse
import json
import os
import random
import sys
from pathlib import Path

# Ensure Docker/VNC shows progress immediately (no buffering)
def _log(msg: str) -> None:
    print(msg, flush=True)

import prior
from ai2thor.controller import Controller

# ProcTHOR-10K split sizes
SPLIT_SIZES = {"train": 10000, "val": 1000, "test": 1000}

# Room spec ids for --config (ProcTHOR PROCTHOR10K_ROOM_SPEC_SAMPLER)
VALID_ROOM_SPEC_IDS = [
    "2-bed-1-bath", "2-bed-2-bath", "4-room", "5-room",
    "7-room-3-bed", "8-room-3-bed", "12-room", "12-room-3-bed",
    "kitchen-living-room", "kitchen-living-bedroom-room", "kitchen-living-bedroom-room2",
    "bedroom-bathroom", "kitchen", "living-room", "bedroom", "bathroom",
]

PROCTHOR_10K_REVISION = "ab3cacd0fc17754d4c080a3fd50b18395fae8647"


def get_example_house_schema():
    """Return a canonical example house dict that conforms to the HouseDict schema.

    Used by --use-example-schema to create the scene from a concrete schema instance.
    Loads one house from ProcTHOR-10K (train[0]) so it is valid for CreateHouse.
    The returned value is already a dict; it is passed as Controller(scene=...).
    You can replace this with a minimal hand-built dict to test custom layouts.
    """
    dataset = prior.load_dataset("procthor-10k")
    return dataset["train"][0]


def _json_serializable(obj):
    """Convert numpy/types for JSON dump."""
    import numpy as np
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.integer, np.floating)):
        return float(obj) if isinstance(obj, np.floating) else int(obj)
    if isinstance(obj, dict):
        return {k: _json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_serializable(v) for v in obj]
    return obj


def print_example_dict(limit_objects=None, output_path=None):
    """Load the example house dict and print or write it as JSON so you can see the format.

    If limit_objects is set (e.g. 3), the "objects" list is truncated to that many
    entries so the output is shorter. If output_path is set, JSON is written there
    instead of stdout.
    """
    house = get_example_house_schema()
    house = _json_serializable(house)
    if limit_objects is not None and "objects" in house and isinstance(house["objects"], list):
        kept = house["objects"][:limit_objects]
        house = {**house, "objects": kept}
        print(f"(objects truncated to {limit_objects} for readability)", file=sys.stderr)
    text = json.dumps(house, indent=2)
    if output_path:
        Path(output_path).write_text(text, encoding="utf-8")
        print(f"Wrote example house dict to {output_path}", file=sys.stderr)
    else:
        print(text)


def get_house_from_dataset(dataset, split="train", index=None, random_house=False, seed=None):
    """Return (house_data dict, resolved_index) from ProcTHOR-10K."""
    split_data = dataset[split]
    n = len(split_data)
    if random_house:
        if seed is not None:
            random.seed(seed)
        resolved_index = random.randint(0, n - 1)
    else:
        resolved_index = index if index is not None else 0
        if resolved_index < 0 or resolved_index >= n:
            raise ValueError(f"House index must be 0..{n - 1} for split '{split}', got {resolved_index}")
    return split_data[resolved_index], resolved_index


def run_demo(
    *,
    use_example_schema=False,
    config=None,
    config_seed=42,
    fallback_only=False,
    split="train",
    index=None,
    random_house=False,
    dataset_seed=None,
    physics_scene=None,
    fullscreen=True,
    use_global_keys=True,
    width=800,
    height=600,
):
    """Load or generate a house, then run keyboard-controlled demo.

    FIXED behavior:
      - Uses explicit CreateHouse + Initialize for any house dict.
      - Teleports to a reachable position to avoid underground/void spawns.
      - Avoids Controller(scene=house_dict) which can mask CreateHouse issues.
    """
    _log("[run_proc_test] Starting (VNC/Docker: watch this terminal for progress)...")
    _script_dir = Path(__file__).resolve().parent
    if str(_script_dir) not in sys.path:
        sys.path.insert(0, str(_script_dir))

    controller = None
    house_data = None
    source = None

    def _make_controller():
        return Controller(
            agentMode="default",
            visibilityDistance=1.5,
            width=width,
            height=height,
            fullscreen=fullscreen,
            snapToGrid=True,
            gridSize=0.25,
            rotateStepDegrees=90.0,
        )

    def _load_house_from_dataset(_split, _index, _random, _seed):
        _log("Loading ProcTHOR-10K...")
        # IMPORTANT: do not pin old revision while debugging
        dataset = prior.load_dataset("procthor-10k")
        h, resolved = get_house_from_dataset(
            dataset, split=_split, index=_index, random_house=_random, seed=_seed
        )
        return h, f"10K {_split}[{resolved}]"

    def _create_house_and_spawn(ctrl: Controller, house: dict):
        _log("[run_proc_test] CreateHouse...")
        evt = ctrl.step(action="CreateHouse", house=house)
        print("CreateHouse success:", evt.metadata.get("lastActionSuccess"))
        print("CreateHouse error:", evt.metadata.get("errorMessage"))

        _log("[run_proc_test] Initialize...")
        evt = ctrl.step(action="Initialize", gridSize=0.25)
        print("Initialize success:", evt.metadata.get("lastActionSuccess"))
        print("Initialize error:", evt.metadata.get("errorMessage"))

        _log("[run_proc_test] GetReachablePositions...")
        evt = ctrl.step(action="GetReachablePositions")
        rp = evt.metadata.get("actionReturn") or []
        print("reachable count:", len(rp))

        if not rp:
            # This is the key diagnostic when you "see nothing":
            # no navmesh points means you can't teleport into the house.
            _log("[run_proc_test] WARNING: no reachable positions; agent may be in void/underground.")
            return

        # Teleport to a guaranteed valid navmesh location
        p = rp[0]
        evt = ctrl.step(action="Teleport", position=p, forceAction=True)
        print("Teleport to reachable:", evt.metadata.get("lastActionSuccess"), evt.metadata.get("errorMessage"))
        agent = evt.metadata.get("agent") or {}
        pos = (agent.get("position") or {})
        _log(f"[run_proc_test] Agent spawn: ({pos.get('x')}, {pos.get('y')}, {pos.get('z')})")

    # --- Physics scene mode (built-in iTHOR scenes) ---
    if physics_scene is not None:
        _log(f"[run_proc_test] Loading physics scene: {physics_scene!r}")
        controller = Controller(
            agentMode="default",
            visibilityDistance=1.5,
            scene=physics_scene,
            width=width,
            height=height,
            fullscreen=fullscreen,
            snapToGrid=True,
            gridSize=0.25,
            rotateStepDegrees=90.0,
        )
        source = f"{physics_scene} (physics scene)"
    
    # --- VNC diagnostic: built-in iTHOR scene ---
    if controller is None and os.environ.get("DREAMAI_VNC_TEST"):
        vnc_scene = os.environ.get("DREAMAI_VNC_SCENE", "FloorPlan1").strip() or "FloorPlan1"
        _log(f"[run_proc_test] DREAMAI_VNC_TEST=1: using built-in scene {vnc_scene!r}.")
        controller = Controller(
            agentMode="default",
            visibilityDistance=1.5,
            scene=vnc_scene,
            width=width,
            height=height,
            fullscreen=fullscreen,
            snapToGrid=True,
            gridSize=0.25,
            rotateStepDegrees=90.0,
        )
        source = f"{vnc_scene} (VNC test)"

    # --- Example schema mode ---
    if controller is None and use_example_schema:
        _log("[run_proc_test] Loading example house schema (ProcTHOR-10K train[0])...")
        house_data = get_example_house_schema()
        source = "example schema (10K train[0])"
        controller = _make_controller()
        _create_house_and_spawn(controller, house_data)

    # --- Config mode: try procedural generation, else fall back to 10K ---
    if controller is None and config is not None:
        if not fallback_only:
            try:
                from src.envs.ai2thor.procthor_adapter import create_procthor_scene
            except ImportError:
                _log("[run_proc_test] Could not import create_procthor_scene; falling back to 10K.")
            else:
                _log(f"[run_proc_test] Generating house: config={config!r}, seed={config_seed}...")
                try:
                    ctrl, house = create_procthor_scene(seed=config_seed, room_spec_id=config)
                    # If your adapter already returns a Controller with a loaded scene,
                    # keep it and just ensure navmesh spawn is sane:
                    controller = ctrl
                    house_data = house.data if hasattr(house, "data") else None
                    source = f"generated ({config}, seed={config_seed})"
                    # Try to teleport onto reachable positions even for generated scenes
                    evt = controller.step(action="GetReachablePositions")
                    rp = evt.metadata.get("actionReturn") or []
                    if rp:
                        controller.step(action="Teleport", position=rp[0], forceAction=True)
                except Exception as e:
                    _log(f"[run_proc_test] Generation failed: {e}")
                    controller = None
                    house_data = None

        if controller is None:
            house_data, source = _load_house_from_dataset("train", 0, False, None)
            controller = _make_controller()
            _create_house_and_spawn(controller, house_data)

    # --- Dataset mode (default) ---
    if controller is None:
        house_data, source = _load_house_from_dataset(split, index, random_house, dataset_seed)
        controller = _make_controller()
        _create_house_and_spawn(controller, house_data)

    if source:
        _log(f"\n" + "=" * 60)
        _log(f"SCENE SOURCE: {source}")
        _log("=" * 60 + "\n")

    _log("[run_proc_test] Sending first step (RotateRight) to confirm scene is live...")
    try:
        event = controller.step(action="RotateRight")
        controller.step("Pass")
        if event.metadata.get("lastActionSuccess"):
            _log("Scene loaded and agent moved.")
        else:
            _log("Scene loaded.")
    except Exception as e:
        _log(f"[run_proc_test] First step() failed: {e}")
        raise

    print("\n" + "=" * 60)
    print("KEYBOARD: W/S/A/D move, Q/E look up/down, P pickup, L drop, X quit")
    print("=" * 60)
    if use_global_keys:
        print("Global keys: focus the sim window; WASD/QE/PL/X still work.")
    else:
        print("Terminal mode: keep this terminal focused.")
    print("(Spinning cursor on macOS: try --no-fullscreen.)\n")

    from _keyboard_control import run_keyboard_loop
    try:
        run_keyboard_loop(controller, use_global_keys=use_global_keys)
    finally:
        controller.stop()


def main():
    parser = argparse.ArgumentParser(
        description="ProcTHOR demo: load or generate a house, drive with keyboard. Use --print-schema for house customization schema."
    )
    # Source: config (generation) vs dataset (10K)
    parser.add_argument(
        "--use-example-schema",
        action="store_true",
        help="Create house from the built-in example schema (canonical HouseDict from 10K train[0]).",
    )
    parser.add_argument(
        "--config",
        choices=VALID_ROOM_SPEC_IDS,
        default=None,
        help="Try procedural generation with this room_spec_id (e.g. 2-bed-1-bath); fallback to 10K on failure.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed for --config generation (default: 42)",
    )
    parser.add_argument(
        "--fallback-only",
        action="store_true",
        help="With --config: skip generation and load from 10K only.",
    )
    parser.add_argument(
        "--split",
        choices=["train", "val", "test"],
        default="train",
        help="Dataset split when using 10K (default: train)",
    )
    parser.add_argument(
        "--index",
        type=int,
        default=None,
        help="House index in split when using 10K (default: 0)",
    )
    parser.add_argument(
        "--random",
        action="store_true",
        help="Pick random house from split (use with --seed for reproducibility)",
    )
    # Display & input
    parser.add_argument("--no-fullscreen", action="store_true", help="Windowed mode")
    parser.add_argument("--width", type=int, default=800, help="Window width (default: 800)")
    parser.add_argument("--height", type=int, default=600, help="Window height (default: 600)")
    parser.add_argument("--terminal", action="store_true", help="Read keys from terminal only")
    parser.add_argument(
        "--print-schema",
        action="store_true",
        help="Print house schema for customizations and exit",
    )
    parser.add_argument(
        "--print-example",
        action="store_true",
        help="Dump the example house dict as JSON so you can see the exact format (to stdout or --print-example-to file)",
    )
    parser.add_argument(
        "--print-example-to",
        type=str,
        default=None,
        metavar="FILE",
        help="With --print-example: write JSON to FILE instead of stdout",
    )
    parser.add_argument(
        "--print-example-max-objects",
        type=int,
        default=None,
        metavar="N",
        help="With --print-example: truncate objects list to N entries for readability",
    )
    parser.add_argument(
        "--physics-scene",
        type=str,
        default=None,
        metavar="SCENE",
        help="Load a built-in physics scene (e.g. FloorPlan1, FloorPlan2, etc.) instead of ProcTHOR-10K",
    )
    args = parser.parse_args()

    if args.print_schema:
        print(__doc__.strip().split("Examples:")[0])
        print(HOUSE_SCHEMA_DOC)
        return

    if args.print_example:
        print_example_dict(
            limit_objects=args.print_example_max_objects,
            output_path=args.print_example_to,
        )
        return

    run_demo(
        use_example_schema=args.use_example_schema,
        config=args.config,
        config_seed=args.seed,
        fallback_only=args.fallback_only,
        split=args.split,
        index=args.index,
        random_house=args.random,
        dataset_seed=args.seed if args.random else None,
        physics_scene=args.physics_scene,
        fullscreen=not args.no_fullscreen,
        use_global_keys=not args.terminal,
        width=args.width,
        height=args.height,
    )


if __name__ == "__main__":
    main()
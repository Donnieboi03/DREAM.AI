"""House schema doc for Scene generator LLM — structure of HouseDict for editing."""

# Mirrors HOUSE_SCHEMA_DOC from scripts/run_proc_test.py so backend/llm does not depend on scripts.

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

To edit: output HouseEditRequest with object_edits (add/move/remove). For add: asset_id (from allowlist), room_id, position, rotation. Result is applied to base house dict then passed to Controller(scene=edited_house).
"""

# Sample allowlist of common ProcTHOR assetIds (subset); extend from asset DB in production.
DEFAULT_ASSET_ID_ALLOWLIST = [
    "Sofa_1", "Sofa_2", "Table_1", "Chair_1", "Bed_1", "Lamp_1", "TV_1",
    "Apple", "Bread", "Tomato", "Potato", "Mug", "Plate", "Book_1",
    "AlarmClock", "HousePlant_1", "Painting_1", "GarbageCan_1",
]


def get_house_schema_doc(asset_id_allowlist: list[str] | None = None) -> str:
    """Return house schema doc string with optional assetId allowlist for the LLM."""
    allowlist = asset_id_allowlist or DEFAULT_ASSET_ID_ALLOWLIST
    allowlist_str = ", ".join(allowlist[:80])  # cap length
    if len(allowlist) > 80:
        allowlist_str += ", ..."
    return HOUSE_SCHEMA_DOC + "\n\nAllowed assetIds (use only these for add): " + allowlist_str

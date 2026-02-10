"""Validate HouseEditRequest and edited house dict before passing to Controller."""

from __future__ import annotations

from dreamai.backend.schemas import HouseEditRequest

# Default allowlist; can be overridden or loaded from asset DB
DEFAULT_ASSET_ID_ALLOWLIST = [
    "Sofa_1", "Sofa_2", "Table_1", "Chair_1", "Bed_1", "Lamp_1", "TV_1",
    "Apple", "Bread", "Tomato", "Potato", "Mug", "Plate", "Book_1",
    "AlarmClock", "HousePlant_1", "Painting_1", "GarbageCan_1",
]


def validate_house_edit_request(
    request: HouseEditRequest,
    asset_id_allowlist: list[str] | None = None,
    room_ids: set[str] | None = None,
) -> list[str]:
    """
    Validate HouseEditRequest: assetIds in allowlist, room_ids exist.
    Returns list of error messages (empty if valid).
    """
    errors: list[str] = []
    allowlist = set(asset_id_allowlist or DEFAULT_ASSET_ID_ALLOWLIST)
    rooms = room_ids or set()
    for edit in request.object_edits:
        if edit.action == "add":
            if edit.asset_id and edit.asset_id not in allowlist:
                errors.append(f"asset_id {edit.asset_id!r} not in allowlist")
            if edit.room_id and rooms and edit.room_id not in rooms:
                errors.append(f"room_id {edit.room_id!r} not in house rooms")
        elif edit.action in ("move", "remove") and not edit.object_id:
            errors.append("move/remove requires object_id")
    return errors


def validate_edited_house_dict(house: dict) -> list[str]:
    """Basic validation of edited house dict (has required top-level keys)."""
    errors: list[str] = []
    required = ("rooms", "walls", "doors", "windows", "objects")
    for k in required:
        if k not in house:
            errors.append(f"house dict missing key: {k}")
        elif not isinstance(house.get(k), list):
            errors.append(f"house[{k}] must be a list")
    if "metadata" not in house and "proceduralParameters" not in house:
        pass  # optional
    return errors

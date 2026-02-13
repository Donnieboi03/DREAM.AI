"""Apply HouseEditRequest to a base house dict to produce edited HouseDict for Controller(scene=...)."""

from __future__ import annotations

import copy
from typing import Any

from src.backend.schemas import HouseEditRequest, ObjectEdit, Vector3


def _vector3_to_dict(v: Vector3) -> dict[str, float]:
    return {"x": v.x, "y": v.y, "z": v.z}


def apply_edits(base_house: dict[str, Any], house_edit_request: HouseEditRequest) -> dict[str, Any]:
    """
    Apply HouseEditRequest to a deep copy of base_house. Returns edited house dict
    suitable for Controller(scene=edited_house).
    """
    house = copy.deepcopy(base_house)
    objects: list[dict[str, Any]] = list(house.get("objects") or [])

    for edit in house_edit_request.object_edits:
        if edit.action == "add" and edit.asset_id and edit.room_id:
            if not edit.position:
                print(f"[WARN] Skipping add edit for {edit.asset_id}: no position provided (LLM error)")
                continue
            new_id = f"{edit.asset_id}|{len(objects) + 1}"
            position = _vector3_to_dict(edit.position)
            rotation = _vector3_to_dict(edit.rotation) if edit.rotation else {"x": 0.0, "y": 0.0, "z": 0.0}
            objects.append({
                "id": new_id,
                "assetId": edit.asset_id,
                "position": position,
                "rotation": rotation,
                "children": [],
                "kinematic": True,
            })
        elif edit.action == "move" and edit.object_id:
            for obj in objects:
                if obj.get("id") == edit.object_id:
                    if edit.position:
                        obj["position"] = _vector3_to_dict(edit.position)
                    if edit.rotation:
                        obj["rotation"] = _vector3_to_dict(edit.rotation)
                    break
        elif edit.action == "remove" and edit.object_id:
            objects = [o for o in objects if o.get("id") != edit.object_id]

    house["objects"] = objects
    return house

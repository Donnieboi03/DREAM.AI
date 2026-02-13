"""Build a short house summary from a HouseDict for the Scene generator LLM."""

from __future__ import annotations

from typing import Any


def get_house_summary(house_dict: dict[str, Any], max_objects_sample: int = 15) -> str:
    """
    Produce a short text summary of the house (rooms, object count, sample of object ids and assetIds)
    for the Scene generator LLM so it can reference real room ids and assetIds.
    """
    lines: list[str] = []
    rooms = house_dict.get("rooms") or []
    for r in rooms[:20]:
        rid = r.get("id", "?")
        rtype = r.get("roomType", "?")
        lines.append(f"  - {rid} ({rtype})")
    lines.append(f"Total rooms: {len(rooms)}")
    objs = house_dict.get("objects") or []
    lines.append(f"Total objects: {len(objs)}")
    lines.append("Sample objects (id, assetId):")
    for o in objs[:max_objects_sample]:
        oid = o.get("id", "?")
        aid = o.get("assetId", "?")
        lines.append(f"  - {oid} -> {aid}")
    return "\n".join(lines)

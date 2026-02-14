"""
Task builder: maps (rl_task_type, rl_task_params) to valid task_description_dict.

Uses rl_thor task structures. Object types are normalized against a curated allowlist.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

# Curated object types from rl_thor (subset of object_types_data.json)
_VALID_OBJECT_TYPES = frozenset({
    "AlarmClock", "Apple", "AppleSliced", "ArmChair", "Bowl", "Bread", "BreadSliced",
    "Cabinet", "Candle", "CellPhone", "CoffeeMachine", "CounterTop", "Cup", "Desk",
    "DeskLamp", "DiningTable", "Drawer", "Dresser", "Egg", "EggCracked", "FloorLamp",
    "Fridge", "GarbageCan", "Kettle", "Laptop", "Lettuce", "LettuceSliced", "Microwave",
    "Mug", "Pan", "Pen", "Pencil", "Plate", "Pot", "Potato", "PotatoSliced", "Shelf",
    "SideTable", "Sink", "SinkBasin", "Sofa", "StoveBurner", "StoveKnob", "TableTop",
    "Tomato", "TomatoSliced", "TVStand", "Vase",
})


def _load_valid_object_types() -> frozenset[str]:
    """Load valid object types from rl_thor data if available."""
    try:
        base = Path(__file__).resolve().parent
        for _ in range(4):
            base = base.parent
        path = base / "third_party" / "rl_thor" / "src" / "rl_thor" / "data" / "object_types_data.json"
        if path.exists():
            data = json.loads(path.read_text())
            return frozenset(str(k) for k in data.keys())
    except Exception:
        pass
    return _VALID_OBJECT_TYPES


_VALID_TYPES = _load_valid_object_types()


def _normalize_object_type(value: Any) -> Optional[str]:
    """Normalize to valid SimObjectType string. Returns None if invalid."""
    if not isinstance(value, str) or not value.strip():
        return None
    s = value.strip()
    # Already PascalCase
    if s in _VALID_TYPES:
        return s
    # Try PascalCase (capitalize each word)
    pascal = "".join(w.capitalize() for w in s.replace("-", " ").replace("_", " ").split())
    if pascal in _VALID_TYPES:
        return pascal
    # Try exact match case-insensitive
    lower = s.lower()
    for t in _VALID_TYPES:
        if t.lower() == lower:
            return t
    return None


def build_task_from_type(
    rl_task_type: str,
    rl_task_params: dict[str, Any],
) -> Optional[dict[str, dict[str, Any]]]:
    """
    Build task_description_dict from structured task type and params.

    Returns None if task type unknown or params invalid.
    """
    if not rl_task_type or not isinstance(rl_task_params, dict):
        return None
    task_type = rl_task_type.strip()
    params = {k: v for k, v in rl_task_params.items() if v is not None}
    builders = {
        "PlaceIn": _build_place_in,
        "Pickup": _build_pickup,
        "Cook": _build_cook,
        "Open": _build_open,
        "Toggle": _build_toggle,
        "Break": _build_break,
        "CoolDown": _build_cool_down,
        "PlaceHeatedIn": _build_place_heated_in,
        "PlaceCooledIn": _build_place_cooled_in,
        "PlaceCleanedIn": _build_place_cleaned_in,
        "PlaceTwoIn": _build_place_two_in,
        "LookInLight": _build_look_in_light,
    }
    fn = builders.get(task_type)
    if fn is None:
        return None
    try:
        return fn(params)
    except (TypeError, KeyError, ValueError) as e:
        print(f"[task_builder] Failed to build {task_type}: {e}")
        return None


def _build_place_in(params: dict[str, Any]) -> Optional[dict]:
    placed = _normalize_object_type(params.get("placed_object_type"))
    receptacle = _normalize_object_type(params.get("receptacle_type"))
    if not placed or not receptacle:
        return None
    return {
        "receptacle": {"properties": {"objectType": receptacle}},
        "placed_object_0": {
            "properties": {"objectType": placed},
            "relations": {"receptacle": ["contained_in"]},
        },
    }


def _build_pickup(params: dict[str, Any]) -> Optional[dict]:
    obj = _normalize_object_type(params.get("picked_up_object_type"))
    if not obj:
        return None
    return {
        "picked_up_object": {
            "properties": {"objectType": obj, "isPickedUp": True},
        },
    }


def _build_cook(params: dict[str, Any]) -> Optional[dict]:
    obj = _normalize_object_type(params.get("cooked_object_type"))
    if not obj:
        return None
    return {
        "cooked_object": {
            "properties": {"objectType": obj, "isCooked": True},
        },
    }


def _build_open(params: dict[str, Any]) -> Optional[dict]:
    obj = _normalize_object_type(params.get("opened_object_type"))
    if not obj:
        return None
    return {
        "opened_object": {
            "properties": {"objectType": obj, "isOpen": True},
        },
    }


def _build_toggle(params: dict[str, Any]) -> Optional[dict]:
    obj = _normalize_object_type(params.get("toggled_object_type"))
    if not obj:
        return None
    return {
        "toggled_object": {
            "properties": {"objectType": obj, "isToggled": True},
        },
    }


def _build_break(params: dict[str, Any]) -> Optional[dict]:
    obj = _normalize_object_type(params.get("broken_object_type"))
    if not obj:
        return None
    return {
        "broken_object": {
            "properties": {"objectType": obj, "isBroken": True},
        },
    }


def _build_cool_down(params: dict[str, Any]) -> Optional[dict]:
    obj = _normalize_object_type(params.get("cooled_object_type"))
    if not obj:
        return None
    return {
        "cooled_object": {
            "properties": {"objectType": obj, "temperature": "Cold"},
        },
    }


def _build_place_heated_in(params: dict[str, Any]) -> Optional[dict]:
    placed = _normalize_object_type(params.get("placed_object_type"))
    receptacle = _normalize_object_type(params.get("receptacle_type"))
    if not placed or not receptacle:
        return None
    return {
        "receptacle": {"properties": {"objectType": receptacle}},
        "placed_object_0": {
            "properties": {"objectType": placed, "temperature": "Hot"},
            "relations": {"receptacle": ["contained_in"]},
        },
    }


def _build_place_cooled_in(params: dict[str, Any]) -> Optional[dict]:
    placed = _normalize_object_type(params.get("placed_object_type"))
    receptacle = _normalize_object_type(params.get("receptacle_type"))
    if not placed or not receptacle:
        return None
    return {
        "receptacle": {"properties": {"objectType": receptacle}},
        "placed_object_0": {
            "properties": {"objectType": placed, "temperature": "Cold"},
            "relations": {"receptacle": ["contained_in"]},
        },
    }


def _build_place_cleaned_in(params: dict[str, Any]) -> Optional[dict]:
    placed = _normalize_object_type(params.get("placed_object_type"))
    receptacle = _normalize_object_type(params.get("receptacle_type"))
    if not placed or not receptacle:
        return None
    return {
        "receptacle": {"properties": {"objectType": receptacle}},
        "placed_object_0": {
            "properties": {"objectType": placed, "isDirty": False},
            "relations": {"receptacle": ["contained_in"]},
        },
    }


def _build_place_two_in(params: dict[str, Any]) -> Optional[dict]:
    obj1 = _normalize_object_type(params.get("object_type_1"))
    obj2 = _normalize_object_type(params.get("object_type_2"))
    receptacle = _normalize_object_type(params.get("receptacle_type"))
    if not obj1 or not obj2 or not receptacle:
        return None
    return {
        "receptacle": {"properties": {"objectType": receptacle}},
        "object_1": {
            "properties": {"objectType": obj1},
            "relations": {"receptacle": ["contained_in"]},
        },
        "object_2": {
            "properties": {"objectType": obj2},
            "relations": {"receptacle": ["contained_in"]},
        },
    }


def _build_look_in_light(params: dict[str, Any]) -> Optional[dict]:
    obj = _normalize_object_type(params.get("looked_at_object_type"))
    if not obj:
        return None
    # LookInLight: light source toggled + object picked up + close_to light
    # Use FloorLamp as representative light source (rl_thor uses LIGHT_SOURCES set)
    return {
        "light_source": {
            "properties": {"objectType": "FloorLamp", "isToggled": True},
        },
        "looked_at_object": {
            "properties": {"objectType": obj, "isPickedUp": True},
            "relations": {"light_source": ["close_to"]},
        },
    }

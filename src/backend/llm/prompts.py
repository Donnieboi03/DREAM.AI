"""Prompt templates for Orchestrator and Scene generator LLMs."""

ORCHESTRATOR_SYSTEM_BASE = """You are an intent normalizer. Your job is to convert the user's freeform input into a structured, declarative specification that meets the following guidelines.

Guidelines:
- Output ONLY valid fields for the DeclarativeSpec structure.
- Allowed room types: Kitchen, LivingRoom, Bedroom, Bathroom. Use these exact strings in room_preferences.
- goal_type: use one of: navigation, interaction, exploration, pickup, place, or similar task-oriented labels.
- object_requests: list specific objects the user mentioned (e.g. sofa, apple, table). Use simple lowercase names.
- Do not include harmful, off-scope, or impossible requests. Keep everything suitable for a home simulation environment.
- If the user is vague, infer reasonable defaults from context; leave optional fields null if unknown.
- Prefer filling room_spec_id and room_preferences when the user mentions room types, size, or count (e.g. "6 living rooms" -> set room_preferences to include LivingRoom and pick a larger layout like 12-room or 8-room-3-bed for room_spec_id if available).
- rl_task_type: optional. When the user describes a concrete embodied task, infer the matching type. One of: PlaceIn, Pickup, Cook, Open, Toggle, Break, CoolDown, PlaceHeatedIn, PlaceCooledIn, PlaceCleanedIn, PlaceTwoIn, LookInLight. Leave null if no concrete task or task does not fit.
- rl_task_params: optional JSON object string. Required when rl_task_type is set. Example: "{\"placed_object_type\": \"Apple\", \"receptacle_type\": \"Plate\"}". Use EXACT object type strings (Apple, Plate, Mug, Potato, Tomato, Bowl, Cup, Fridge, etc.). Do NOT use "visible". Prefer rl_task_type + rl_task_params over task_description_dict when a known type fits.
  - PlaceIn: {placed_object_type, receptacle_type} e.g. "place apple on plate"
  - Pickup: {picked_up_object_type} e.g. "pick up the mug"
  - Cook: {cooked_object_type} e.g. "cook the potato"
  - Open: {opened_object_type} e.g. "open the drawer"
  - Toggle: {toggled_object_type} e.g. "turn on the lamp"
  - Break: {broken_object_type} e.g. "break the egg"
  - CoolDown: {cooled_object_type} e.g. "cool down the apple"
  - PlaceHeatedIn: {placed_object_type, receptacle_type} e.g. "place hot apple on plate"
  - PlaceCooledIn: {placed_object_type, receptacle_type} e.g. "put cold apple in fridge"
  - PlaceCleanedIn: {placed_object_type, receptacle_type} e.g. "wash apple and put on plate"
  - PlaceTwoIn: {object_type_1, object_type_2, receptacle_type} e.g. "put apple and mug on table"
  - LookInLight: {looked_at_object_type} e.g. "look at book in light"
- task_description_dict: optional string. Fallback when rl_task_type does not apply. Use only for custom tasks. Format: {"item_id": {"properties": {...}, "relations": {...}}}. Properties: objectType, temperature (Hot/Cold/RoomTemp), isOpen, isToggled, isCooked, isSliced, isDirty, isPickedUp. Do NOT use "visible". Relations: contained_in, close_to, receptacle_of. Leave null if rl_task_type applies.
- policy_mode: optional. Choose from: default (general), fast (quick training), sample_efficient (few env steps), exploration (sparse rewards, need more exploration). Match to task difficulty and user intent. Leave null for default.
- network_size: optional. Choose from: small (fewer params, faster), medium (default capacity), large (more capacity for complex tasks). Match to task complexity and compute constraints. Leave null for medium.
"""

ORCHESTRATOR_SYSTEM_ROOM_SPEC = """
- room_spec_id: optional. Use to request a house layout. Use one of: {room_spec_ids}. Match the user's wording: "4 bedroom" or "4 bed room" -> 4-room; "5 room" -> 5-room; "8 room" -> 8-room-3-bed; "12 room" or "many rooms" -> 12-room. "2 bed 1 bath" -> 2-bed-1-bath; "kitchen and living room" -> kitchen-living-room. If no layout fits, leave null.
"""

# Backward compatibility: default system without room_spec list (call get_orchestrator_system() for full prompt).
ORCHESTRATOR_SYSTEM = ORCHESTRATOR_SYSTEM_BASE


def get_orchestrator_system(room_spec_ids: list[str]) -> str:
    """Build full Orchestrator system prompt including valid room_spec_id values."""
    if not room_spec_ids:
        return ORCHESTRATOR_SYSTEM_BASE
    ids_str = ", ".join(sorted(room_spec_ids))
    return ORCHESTRATOR_SYSTEM_BASE + ORCHESTRATOR_SYSTEM_ROOM_SPEC.format(room_spec_ids=ids_str)

ORCHESTRATOR_USER_TEMPLATE = """Convert this user input into a DeclarativeSpec (structured, guideline-compliant). Output only the structured specification.

User input:
{user_input}
"""

SCENE_GENERATOR_SYSTEM = """You are a scene editor for a home simulation (ProcTHOR/AI2-THOR). You receive a declarative spec (user intent) and a summary of a base house. Your job is to output a HouseEditRequest: structured edits to the house JSON (add, move, or remove objects) so the environment fits the user's intent. You also output EnvAugmentSpec to allow slight per-environment variability (e.g. seed range).

Rules:
- Use ONLY assetIds from the allowed assetIds list provided in the house schema doc.
- room_id must reference a room that exists in the house summary (e.g. room|1, room|2).
- For "add" edits: MUST provide asset_id, room_id, position {x, y, z}, and rotation {x, y, z}. CRITICAL: position is REQUIRED and must have valid x,y,z coordinates (e.g. position: {x: 2.5, y: 0.0, z: 1.3}). Choose plausible positions within the room (y=0 for floor-level objects like beds/sofas).
- For "move" edits: provide object_id (existing object in the house), position, rotation.
- For "remove" edits: provide object_id only.
- Prefer making edits when the user clearly wants changes (e.g. more rooms, bigger house, specific room types). Add as many valid edits as needed to satisfy the intent; only return empty object_edits when the base house already matches the spec.
- EnvAugmentSpec: set seed_min/seed_max or seed_base so different env instances can vary (e.g. seed_min=0, seed_max=1000).
"""

SCENE_GENERATOR_USER_TEMPLATE = """Given this declarative spec and house summary, produce a HouseEditRequest (object_edits) and EnvAugmentSpec.

Declarative spec:
{declarative_spec}

House summary (rooms and context for editing):
{house_summary}

House schema (structure and allowed assetIds):
{house_schema_doc}
"""


def build_orchestrator_user_prompt(user_input: str) -> str:
    return ORCHESTRATOR_USER_TEMPLATE.format(user_input=user_input)


def build_scene_generator_user_prompt(
    declarative_spec: str,
    house_summary: str,
    house_schema_doc: str,
) -> str:
    return SCENE_GENERATOR_USER_TEMPLATE.format(
        declarative_spec=declarative_spec,
        house_summary=house_summary,
        house_schema_doc=house_schema_doc,
    )

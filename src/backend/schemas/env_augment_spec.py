"""Env augment spec — per-environment variability from Scene generator LLM."""

from typing import Optional

from pydantic import BaseModel, Field


class SceneRandomizationConfig(BaseModel):
    """Scene randomization options (inspired by rl_thor). Applied on env reset."""

    random_agent_spawn: bool = Field(False, description="Spawn agent at random reachable position and rotation")
    random_object_spawn: bool = Field(False, description="InitialRandomSpawn for pickupable objects")
    random_object_materials: bool = Field(False, description="Randomize object materials")
    random_object_colors: bool = Field(False, description="Randomize object colors")
    random_lighting: bool = Field(False, description="Randomize lighting conditions")


class EnvAugmentSpec(BaseModel):
    """What may vary per environment (seeds, object/lighting variants) for diversity."""

    seed_base: Optional[int] = Field(None, description="Base seed; per-env seed = seed_base + env_index or sampled")
    seed_min: Optional[int] = Field(None, description="Min seed for random sampling per env")
    seed_max: Optional[int] = Field(None, description="Max seed for random sampling per env")
    lighting_variants: Optional[list[str]] = Field(None, description="Optional lighting/skybox options per env")
    scene_randomization: Optional[SceneRandomizationConfig] = Field(
        None, description="Scene randomization to apply on reset"
    )

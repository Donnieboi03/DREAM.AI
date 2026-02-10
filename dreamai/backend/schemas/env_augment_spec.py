"""Env augment spec — per-environment variability from Scene generator LLM."""

from typing import Optional

from pydantic import BaseModel, Field


class EnvAugmentSpec(BaseModel):
    """What may vary per environment (seeds, object/lighting variants) for diversity."""

    seed_base: Optional[int] = Field(None, description="Base seed; per-env seed = seed_base + env_index or sampled")
    seed_min: Optional[int] = Field(None, description="Min seed for random sampling per env")
    seed_max: Optional[int] = Field(None, description="Max seed for random sampling per env")
    lighting_variants: Optional[list[str]] = Field(None, description="Optional lighting/skybox options per env")

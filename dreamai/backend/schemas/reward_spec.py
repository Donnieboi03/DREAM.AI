"""Reward specification — filled by LLM / used by evaluation and reward pipeline."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class RewardSpec(BaseModel):
    """Describes how reward is shaped. Used by reward pipeline and critic."""

    reward_type: Optional[str] = Field(None, description="e.g. sparse, dense, shaped")
    components: Optional[list[str]] = Field(None, description="Reward component names or keys")
    success_reward: Optional[float] = Field(None, description="Reward on task success")
    failure_penalty: Optional[float] = Field(None, description="Penalty on failure")
    custom_weights: Optional[dict[str, float]] = Field(None, description="Weights per component")
    extra: Optional[dict[str, Any]] = Field(None, description="Provider-specific config")

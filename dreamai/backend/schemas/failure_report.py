"""Failure report — filled by LLM / used by evaluation and iteration logic."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class FailureReport(BaseModel):
    """Report of a failure for iteration and reward adaptation."""

    episode_id: Optional[str] = Field(None, description="Episode or run identifier")
    failure_stage: Optional[str] = Field(None, description="Where it failed (e.g. navigation, interaction)")
    reason: Optional[str] = Field(None, description="Human/LLM description of cause")
    suggested_fix: Optional[str] = Field(None, description="Suggested change for next iteration")
    extra: Optional[dict[str, Any]] = Field(None, description="Structured details")

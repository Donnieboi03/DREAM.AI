"""Gemini API client for Orchestrator and Scene generator LLMs (uses google-genai SDK)."""

from __future__ import annotations

import os
from typing import Any, Optional

# API key from env; do not hardcode
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
GOOGLE_API_KEY_ENV = "GOOGLE_API_KEY"
DEFAULT_MODEL = "gemini-2.5-flash"


def get_api_key() -> Optional[str]:
    """Return Gemini/Google API key from environment."""
    return os.environ.get(GEMINI_API_KEY_ENV) or os.environ.get(GOOGLE_API_KEY_ENV)


def create_client(model_id: Optional[str] = None, api_key: Optional[str] = None) -> Any:
    """
    Create a Gemini client (google.genai Client).
    Uses api_key if provided, else env GEMINI_API_KEY or GOOGLE_API_KEY.
    """
    from google import genai

    key = api_key or get_api_key()
    if not key:
        raise ValueError(
            f"Gemini API key not set. Set {GEMINI_API_KEY_ENV} or {GOOGLE_API_KEY_ENV} in the environment."
        )
    return genai.Client(api_key=key)


def complete(
    prompt: str,
    system_instruction: Optional[str] = None,
    model_id: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """
    Send a single prompt to Gemini and return the response text.
    Optionally pass system_instruction for chat-style behavior.
    """
    from google.genai import types

    client = create_client(api_key=api_key)
    model = model_id or DEFAULT_MODEL
    config = types.GenerateContentConfig(system_instruction=system_instruction) if system_instruction else None
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )
    if not response or not getattr(response, "text", None):
        raise RuntimeError("Empty or invalid response from Gemini")
    return response.text

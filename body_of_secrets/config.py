"""Environment-driven configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    model: str
    max_tokens: int
    temperature: float
    openai_api_key: str | None
    openai_base_url: str | None
    anthropic_api_key: str | None
    anthropic_model: str | None
    preferred_provider: str | None

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            model=os.getenv("BOS_MODEL", "gpt-4o"),
            max_tokens=int(os.getenv("BOS_MAX_TOKENS", "2048")),
            temperature=float(os.getenv("BOS_TEMPERATURE", "0.3")),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_base_url=os.getenv("OPENAI_BASE_URL"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            anthropic_model=os.getenv("BOS_ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
            preferred_provider=os.getenv("BOS_PROVIDER"),
        )


SETTINGS = Settings.from_env()

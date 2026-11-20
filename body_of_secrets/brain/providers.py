"""Provider-agnostic LLM interface (Muscle isolation).

The Brain never talks to a vendor SDK directly. It only depends on the
LLMProvider protocol. This allows the same reasoning engine to run against
Claude, OpenAI-compatible endpoints, local models, or pure classical backends.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from body_of_secrets.config import SETTINGS


@runtime_checkable
class LLMProvider(Protocol):
    """Minimal interface any backend must satisfy."""

    def complete(self, system: str, user: str) -> str: ...


class CallableProvider:
    """Wrap any callable for testing or custom backends."""

    def __init__(self, fn: Callable[[str, str], str]):
        self._fn = fn

    def complete(self, system: str, user: str) -> str:
        return self._fn(system, user)


class OpenAICompatibleProvider:
    """OpenAI-compatible chat completions (OpenAI, Azure, local servers)."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError(
                "Install the optional extra: pip install 'body-of-secrets[openai]'"
            ) from exc

        self._client = OpenAI(
            api_key=api_key or SETTINGS.openai_api_key,
            base_url=base_url or SETTINGS.openai_base_url,
        )
        self.model = model or SETTINGS.model
        self.max_tokens = max_tokens or SETTINGS.max_tokens
        self.temperature = temperature if temperature is not None else SETTINGS.temperature

    def complete(self, system: str, user: str) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        content = response.choices[0].message.content
        return content or ""


class AnthropicProvider:
    """Anthropic Messages API (Claude)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ):
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise ImportError(
                "Install the optional extra: pip install 'body-of-secrets[anthropic]'"
            ) from exc

        self._client = Anthropic(api_key=api_key or SETTINGS.anthropic_api_key)
        self.model = model or SETTINGS.anthropic_model
        self.max_tokens = max_tokens or SETTINGS.max_tokens
        self.temperature = temperature if temperature is not None else SETTINGS.temperature

    def complete(self, system: str, user: str) -> str:
        message = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        # Anthropic returns a list of content blocks
        parts = [block.text for block in message.content if hasattr(block, "text")]
        return "\n".join(parts)


def default_provider() -> LLMProvider:
    """Select a provider based on environment configuration."""
    preferred = (SETTINGS.preferred_provider or "").lower()

    if preferred == "anthropic" and SETTINGS.anthropic_api_key:
        return AnthropicProvider()
    if preferred == "openai" and SETTINGS.openai_api_key:
        return OpenAICompatibleProvider()

    # First available wins
    if SETTINGS.openai_api_key:
        return OpenAICompatibleProvider()
    if SETTINGS.anthropic_api_key:
        return AnthropicProvider()

    raise RuntimeError(
        "No LLM provider configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY, "
        "or pass a custom LLMProvider to Engine(provider=...)."
    )

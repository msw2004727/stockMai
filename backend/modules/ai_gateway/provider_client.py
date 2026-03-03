from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ProviderCallError(Exception):
    def __init__(self, message: str, retryable: bool = True):
        super().__init__(message)
        self.retryable = retryable


@dataclass(slots=True)
class TokenUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(slots=True)
class ProviderResponse:
    text: str
    usage: TokenUsage | None = None


class AIProviderClient(Protocol):
    provider: str

    async def generate(self, prompt: str, symbol: str, timeout_seconds: int) -> ProviderResponse:
        """Return provider response text + optional official usage."""

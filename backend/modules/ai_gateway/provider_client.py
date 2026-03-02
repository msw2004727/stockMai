from __future__ import annotations

from typing import Protocol


class ProviderCallError(Exception):
    def __init__(self, message: str, retryable: bool = True):
        super().__init__(message)
        self.retryable = retryable


class AIProviderClient(Protocol):
    provider: str

    async def generate(self, prompt: str, symbol: str, timeout_seconds: int) -> str:
        """Return raw model response text."""

from __future__ import annotations

from typing import Protocol


class AIProviderClient(Protocol):
    provider: str

    def generate(self, prompt: str, symbol: str, timeout_seconds: int) -> str:
        """Return raw model response text."""


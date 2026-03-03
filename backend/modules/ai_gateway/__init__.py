from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .gateway_router import GatewayRequest, GatewayRouter

__all__ = ["GatewayRequest", "GatewayRouter", "build_default_router"]


def __getattr__(name: str) -> Any:
    if name in {"GatewayRequest", "GatewayRouter", "build_default_router"}:
        from . import gateway_router as _gateway_router

        return getattr(_gateway_router, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

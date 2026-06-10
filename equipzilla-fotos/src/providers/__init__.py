"""Proveedores de edicion de imagen por IA."""

from __future__ import annotations

from ..config import AppConfig
from .base import ImageProvider, EditRequest, EditResult


def get_provider(config: AppConfig) -> ImageProvider:
    """Factory: devuelve la implementacion de ImageProvider segun la config.

    Para anadir un proveedor nuevo basta con implementar ImageProvider y
    registrarlo aqui; el resto del pipeline no cambia.
    """
    name = config.provider.lower()
    if name == "gemini":
        from .gemini import GeminiProvider

        return GeminiProvider(config)
    if name == "flux":
        from .flux import FluxProvider

        return FluxProvider(config)
    raise ValueError(
        f"Proveedor desconocido: '{config.provider}'. "
        f"Opciones validas: gemini, flux."
    )


__all__ = ["ImageProvider", "EditRequest", "EditResult", "get_provider"]

"""Interfaz abstracta de proveedor de edicion de imagen.

Cualquier backend (Gemini, FLUX, etc.) implementa ``ImageProvider`` para que el
pipeline pueda cambiar de proveedor sin tocar el resto del codigo.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from pathlib import Path


@dataclass
class EditRequest:
    """Peticion de edicion image-to-image."""

    image_path: Path          # foto original de entrada
    prompt: str               # instruccion completa (ya incluye la regla critica)
    negative_prompt: str = ""  # que NO debe aparecer
    version_key: str = ""     # operador | ficha_tecnica | en_faena


@dataclass
class EditResult:
    """Resultado de una edicion."""

    image_bytes: bytes        # imagen resultante (bytes crudos, p.ej. PNG/JPEG)
    mime_type: str = "image/png"
    model: str = ""           # modelo concreto que genero la imagen


class ImageProvider(abc.ABC):
    """Contrato comun para los proveedores de edicion de imagen."""

    name: str = "base"

    @abc.abstractmethod
    def edit(self, request: EditRequest) -> EditResult:
        """Edita una imagen segun el prompt y devuelve los bytes resultantes.

        Debe lanzar una excepcion si la API falla o no devuelve imagen; el
        pipeline se encarga de los reintentos con backoff.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def model(self) -> str:
        """Identificador del modelo activo (para logging y manifest)."""
        raise NotImplementedError

"""Stub de proveedor FLUX.1 Kontext (alternativa a Gemini).

FLUX.1 Kontext (Black Forest Labs) tambien soporta edicion image-to-image
manteniendo la identidad del sujeto, por lo que encaja con los requisitos del
pipeline. Esta clase deja la estructura lista; falta cablear la llamada HTTP
real al endpoint del proveedor (BFL API o Replicate/Fal segun donde se aloje).

Para activarlo:
    1. En .env -> IMAGE_PROVIDER=flux y FLUX_API_KEY=...
    2. Implementa el cuerpo de edit() (ver TODO mas abajo).
"""

from __future__ import annotations

from ..config import AppConfig
from .base import EditRequest, EditResult, ImageProvider


class FluxProvider(ImageProvider):
    """Implementacion (stub) para FLUX.1 Kontext."""

    name = "flux"

    def __init__(self, config: AppConfig) -> None:
        if not config.flux_api_key:
            raise ValueError(
                "Falta FLUX_API_KEY en .env (necesaria con IMAGE_PROVIDER=flux)."
            )
        self._api_key = config.flux_api_key
        self._model = config.flux_model

    @property
    def model(self) -> str:
        return self._model

    def edit(self, request: EditRequest) -> EditResult:
        # ─────────────────────────────────────────────────────────────
        # TODO: Implementar la llamada real a FLUX.1 Kontext.
        #
        # Flujo tipico (BFL API):
        #   1. POST /v1/flux-kontext-pro con:
        #        - input_image: foto original en base64
        #        - prompt: request.prompt
        #        - (opcional) parametros de fuerza/guidance
        #   2. La API responde con un id; se hace polling a /v1/get_result
        #      hasta status="Ready".
        #   3. Descargar la imagen resultante (URL firmada) -> bytes.
        #   4. return EditResult(image_bytes=..., mime_type="image/jpeg",
        #                        model=self._model)
        #
        # El resto del pipeline (reintentos, guardado, manifest) ya funciona
        # con cualquier ImageProvider, asi que solo hay que rellenar esto.
        # ─────────────────────────────────────────────────────────────
        raise NotImplementedError(
            "FluxProvider es un stub. Implementa edit() para usar FLUX.1 Kontext, "
            "o usa IMAGE_PROVIDER=gemini (por defecto)."
        )

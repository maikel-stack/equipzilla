"""Implementacion de ImageProvider con Google Gemini.

Usa la familia Gemini Flash Image ("Nano Banana") para edicion image-to-image
e inpainting mediante el SDK oficial ``google-genai``.

Docs: https://ai.google.dev/gemini-api/docs/image-generation
"""

from __future__ import annotations

import mimetypes

from ..config import AppConfig
from .base import EditRequest, EditResult, ImageProvider


class GeminiProvider(ImageProvider):
    """Proveedor basado en Google Gemini (Nano Banana / Gemini Flash Image)."""

    name = "gemini"

    def __init__(self, config: AppConfig) -> None:
        if not config.gemini_api_key:
            raise ValueError(
                "Falta GEMINI_API_KEY. Copia .env.example a .env y rellena la key. "
                "Consiguela en https://aistudio.google.com/apikey"
            )
        # Import perezoso para no exigir el SDK si se usa otro proveedor.
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "Falta el paquete 'google-genai'. Instala con: "
                "pip install -r requirements.txt"
            ) from exc

        self._types = types
        self._client = genai.Client(api_key=config.gemini_api_key)
        self._model = config.gemini_model

    @property
    def model(self) -> str:
        return self._model

    def edit(self, request: EditRequest) -> EditResult:
        types = self._types

        mime, _ = mimetypes.guess_type(str(request.image_path))
        mime = mime or "image/jpeg"
        image_bytes = request.image_path.read_bytes()

        # Construimos el prompt: instruccion + (opcional) negative prompt.
        prompt_text = request.prompt
        if request.negative_prompt:
            prompt_text += f"\n\nEVITA / NO incluyas: {request.negative_prompt}"

        contents = [
            types.Part.from_bytes(data=image_bytes, mime_type=mime),
            prompt_text,
        ]

        response = self._client.models.generate_content(
            model=self._model,
            contents=contents,
        )

        out_bytes, out_mime = self._extract_image(response)
        if out_bytes is None:
            raise RuntimeError(
                "Gemini no devolvio ninguna imagen en la respuesta "
                f"(version='{request.version_key}'). "
                "Revisa el prompt, el modelo o posibles filtros de seguridad."
            )
        return EditResult(image_bytes=out_bytes, mime_type=out_mime, model=self._model)

    @staticmethod
    def _extract_image(response) -> tuple[bytes | None, str]:
        """Extrae los bytes de imagen de la respuesta de Gemini."""
        candidates = getattr(response, "candidates", None) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None) or []
            for part in parts:
                inline = getattr(part, "inline_data", None)
                if inline is not None and getattr(inline, "data", None):
                    mime = getattr(inline, "mime_type", None) or "image/png"
                    return inline.data, mime
        return None, "image/png"

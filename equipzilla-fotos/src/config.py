"""Carga y validacion de configuracion (.env + config.yaml)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass
class VersionConfig:
    """Una de las versiones a generar (operador, ficha_tecnica, en_faena)."""

    key: str
    description: str
    prompt: str


@dataclass
class AppConfig:
    """Configuracion completa de la aplicacion."""

    # Proveedor
    provider: str
    gemini_api_key: str
    gemini_model: str
    flux_api_key: str
    flux_model: str
    cost_per_image_usd: float

    # Prompts / salida
    global_constraint: str
    negative_prompt: str
    versions: list[VersionConfig]
    output_format: str
    output_quality: int

    # Rutas
    base_dir: Path
    input_dir: Path
    output_dir: Path
    processed_dir: Path
    log_dir: Path

    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def model_name(self) -> str:
        """Nombre del modelo del proveedor activo (para el manifest)."""
        return self.gemini_model if self.provider == "gemini" else self.flux_model


def load_config(base_dir: Path) -> AppConfig:
    """Carga .env y config.yaml desde ``base_dir`` y devuelve un AppConfig."""
    base_dir = base_dir.resolve()
    load_dotenv(base_dir / ".env")

    config_path = base_dir / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"No se encontro config.yaml en {config_path}")

    with config_path.open("r", encoding="utf-8") as fh:
        raw: dict[str, Any] = yaml.safe_load(fh) or {}

    versions: list[VersionConfig] = []
    for key, body in (raw.get("versions") or {}).items():
        body = body or {}
        prompt = (body.get("prompt") or "").strip()
        if not prompt:
            raise ValueError(f"La version '{key}' no tiene 'prompt' en config.yaml")
        versions.append(
            VersionConfig(
                key=key,
                description=(body.get("description") or "").strip(),
                prompt=prompt,
            )
        )
    if not versions:
        raise ValueError("config.yaml no define ninguna version en 'versions'.")

    output = raw.get("output") or {}

    provider = os.getenv("IMAGE_PROVIDER", "gemini").strip().lower()

    return AppConfig(
        provider=provider,
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-image-preview").strip(),
        flux_api_key=os.getenv("FLUX_API_KEY", "").strip(),
        flux_model=os.getenv("FLUX_MODEL", "flux-kontext-pro").strip(),
        cost_per_image_usd=float(os.getenv("COST_PER_IMAGE_USD", "0.039")),
        global_constraint=(raw.get("global_constraint") or "").strip(),
        negative_prompt=(raw.get("negative_prompt") or "").strip(),
        versions=versions,
        output_format=str(output.get("format", "jpg")).lower(),
        output_quality=int(output.get("quality", 92)),
        base_dir=base_dir,
        input_dir=base_dir / "input",
        output_dir=base_dir / "output",
        processed_dir=base_dir / "processed",
        log_dir=base_dir / "logs",
        extra=raw,
    )

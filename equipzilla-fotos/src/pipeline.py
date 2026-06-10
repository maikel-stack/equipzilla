"""Pipeline de procesamiento: orquesta input -> edicion -> output -> processed."""

from __future__ import annotations

import io
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from PIL import Image
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import AppConfig, VersionConfig
from .manifest import write_manifest
from .providers import ImageProvider
from .providers.base import EditRequest

logger = logging.getLogger("equipzilla")

# Extensiones de imagen aceptadas en input/
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


@dataclass
class MachineResult:
    """Resultado del procesamiento de una maquina."""

    machine_id: str
    generated: dict[str, str]   # {version_key: archivo}
    skipped: list[str]          # versiones omitidas por ya existir
    errors: dict[str, str]      # {version_key: mensaje_error}

    @property
    def ok(self) -> bool:
        return not self.errors


def discover_inputs(input_dir: Path) -> list[Path]:
    """Lista las fotos validas en input/ (orden alfabetico)."""
    if not input_dir.exists():
        return []
    return sorted(
        p
        for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in VALID_EXTENSIONS
    )


def machine_id_from_path(path: Path) -> str:
    """Deriva el id de la maquina a partir del nombre del archivo."""
    return path.stem


def _build_prompt(config: AppConfig, version: VersionConfig, machine_id: str) -> str:
    """Compone el prompt final: regla critica global + prompt de la version."""
    parts = []
    if config.global_constraint:
        parts.append(config.global_constraint)
    body = version.prompt.format(machine_id=machine_id)
    parts.append(body)
    return "\n\n".join(parts)


def _save_as_jpg(image_bytes: bytes, dest: Path, quality: int) -> None:
    """Convierte bytes de imagen a JPG y los guarda en ``dest``."""
    with Image.open(io.BytesIO(image_bytes)) as img:
        if img.mode != "RGB":
            img = img.convert("RGB")
        dest.parent.mkdir(parents=True, exist_ok=True)
        img.save(dest, format="JPEG", quality=quality)


class Pipeline:
    """Orquesta el procesamiento por lotes."""

    def __init__(self, config: AppConfig, provider: ImageProvider) -> None:
        self.config = config
        self.provider = provider

    # --- edicion con reintentos + backoff exponencial ------------------
    @retry(
        reraise=True,
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception_type(Exception),
        before_sleep=lambda rs: logger.warning(
            "Error en API (intento %d). Reintentando en %.0fs...",
            rs.attempt_number,
            rs.next_action.sleep if rs.next_action else 0,
        ),
    )
    def _edit_with_retry(self, request: EditRequest):
        return self.provider.edit(request)

    # --- procesado de una maquina --------------------------------------
    def process_machine(
        self, image_path: Path, machine_id: str, force: bool = False
    ) -> MachineResult:
        machine_dir = self.config.output_dir / machine_id
        ext = self.config.output_format.lstrip(".") or "jpg"

        result = MachineResult(machine_id=machine_id, generated={}, skipped=[], errors={})

        for version in self.config.versions:
            out_name = f"{machine_id}_{version.key}.{ext}"
            out_path = machine_dir / out_name

            # Idempotencia: si ya existe y no hay --force, se omite.
            if out_path.exists() and not force:
                logger.info("  ↷ %s ya existe, se omite (usa --force).", out_name)
                result.skipped.append(version.key)
                result.generated[version.key] = out_name
                continue

            prompt = _build_prompt(self.config, version, machine_id)
            request = EditRequest(
                image_path=image_path,
                prompt=prompt,
                negative_prompt=self.config.negative_prompt,
                version_key=version.key,
            )

            try:
                logger.info("  → generando '%s'...", version.key)
                edit = self._edit_with_retry(request)
                _save_as_jpg(edit.image_bytes, out_path, self.config.output_quality)
                result.generated[version.key] = out_name
                logger.info("    ✓ guardado %s", out_path)
            except Exception as exc:  # noqa: BLE001 - registramos y continuamos
                logger.error("    ✗ fallo en '%s': %s", version.key, exc)
                result.errors[version.key] = str(exc)

        # manifest.json (solo si se genero al menos una version)
        if result.generated:
            write_manifest(
                machine_dir=machine_dir,
                machine_id=machine_id,
                original_name=image_path.name,
                versions=result.generated,
                model=self.provider.model,
                provider=self.config.provider,
                cost_per_image_usd=self.config.cost_per_image_usd,
            )

        # Mover original a processed/ solo si TODAS las versiones estan listas.
        all_done = not result.errors and len(result.generated) == len(
            self.config.versions
        )
        if all_done:
            self._move_to_processed(image_path)

        return result

    def _move_to_processed(self, image_path: Path) -> None:
        """Mueve el original a processed/ (sin sobrescribir)."""
        if not image_path.exists():
            return
        self.config.processed_dir.mkdir(parents=True, exist_ok=True)
        dest = self.config.processed_dir / image_path.name
        if dest.exists():
            stem, suffix = image_path.stem, image_path.suffix
            n = 1
            while dest.exists():
                dest = self.config.processed_dir / f"{stem}_{n}{suffix}"
                n += 1
        shutil.move(str(image_path), str(dest))
        logger.info("  ⇄ original movido a %s", dest)

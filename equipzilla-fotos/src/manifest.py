"""Generacion del manifest.json por maquina."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_manifest(
    machine_dir: Path,
    machine_id: str,
    original_name: str,
    versions: dict[str, str],
    model: str,
    provider: str,
    cost_per_image_usd: float,
) -> Path:
    """Escribe ``<machine_dir>/manifest.json`` con los metadatos de la maquina.

    Args:
        machine_dir: carpeta output/<id_maquina>.
        machine_id: id de la maquina.
        original_name: nombre del archivo original.
        versions: mapa {clave_version: nombre_archivo_generado}.
        model: modelo concreto usado.
        provider: proveedor (gemini/flux).
        cost_per_image_usd: coste estimado por imagen.
    """
    n = len(versions)
    manifest: dict[str, Any] = {
        "machine_id": machine_id,
        "original": original_name,
        "provider": provider,
        "model": model,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "versions": [
            {"key": key, "file": filename} for key, filename in versions.items()
        ],
        "version_count": n,
        "estimated_cost_usd": round(cost_per_image_usd * n, 4),
        "cost_per_image_usd": cost_per_image_usd,
    }

    manifest_path = machine_dir / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
    return manifest_path

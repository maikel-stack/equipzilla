"""Servicio HTTP que expone el pipeline para automatizaciones (n8n, etc.).

Pensado para el flujo con Google Drive vía n8n:
    1. n8n detecta una foto nueva en una carpeta de Drive (Google Drive Trigger).
    2. n8n descarga el archivo y hace POST multipart a /procesar.
    3. Este servicio genera las 3 versiones (operador, ficha_tecnica, en_faena)
       y las devuelve en base64 dentro de un JSON.
    4. n8n convierte cada base64 a binario y lo sube de vuelta a Drive.

La autenticacion de Drive se queda en n8n; aqui solo vive la logica de edicion
(prompts, regla critica, reintentos, proveedor abstraido). Asi no duplicamos
nada: el CLI y el servicio comparten exactamente el mismo Pipeline.

Arrancar:
    uvicorn src.serve:app --host 0.0.0.0 --port 8080
o:
    python -m src.serve            # arranque directo con uvicorn embebido

Endpoints:
    GET  /salud      -> healthcheck
    POST /procesar   -> multipart (file=<imagen>, machine_id=<opcional>)
"""

from __future__ import annotations

import base64
import logging
import os
import tempfile
from pathlib import Path

from .config import load_config
from .logging_setup import setup_logging
from .pipeline import Pipeline, VALID_EXTENSIONS, machine_id_from_path
from .providers import get_provider

try:
    from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
    from fastapi.responses import JSONResponse
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "El servicio HTTP requiere 'fastapi', 'uvicorn' y 'python-multipart'. "
        "Instala con: pip install -r requirements.txt"
    ) from exc


BASE_DIR = Path(__file__).resolve().parent.parent

# Token opcional para proteger el endpoint. Si EQUIPZILLA_API_TOKEN esta
# definido en el entorno, hay que enviar la cabecera X-API-Token con ese valor.
API_TOKEN = os.getenv("EQUIPZILLA_API_TOKEN", "").strip()

config = load_config(BASE_DIR)
logger = setup_logging(config.log_dir)
provider = get_provider(config)
pipeline = Pipeline(config, provider)

app = FastAPI(title="Equipzilla · Pipeline de fotos", version="1.0.0")


@app.get("/salud")
def salud() -> dict:
    return {
        "status": "ok",
        "provider": config.provider,
        "model": config.model_name,
        "versions": [v.key for v in config.versions],
    }


@app.post("/procesar")
async def procesar(
    file: UploadFile = File(...),
    machine_id: str | None = Form(default=None),
    x_api_token: str | None = Header(default=None),
) -> JSONResponse:
    # Autenticacion opcional por token.
    if API_TOKEN and x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Token invalido o ausente.")

    filename = file.filename or "foto.jpg"
    ext = Path(filename).suffix.lower()
    if ext not in VALID_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extension no soportada: '{ext}'. Validas: {sorted(VALID_EXTENSIONS)}",
        )

    mid = (machine_id or machine_id_from_path(Path(filename))).strip()
    logger.info("HTTP /procesar · maquina='%s' archivo='%s'", mid, filename)

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Archivo vacio.")

    # Guardamos en un temporal porque el proveedor lee desde una ruta.
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(raw)
        tmp_path = Path(tmp.name)

    try:
        versions = pipeline.generate_versions(tmp_path, mid)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Fallo procesando '%s'", mid)
        raise HTTPException(status_code=502, detail=f"Error de generacion: {exc}")
    finally:
        tmp_path.unlink(missing_ok=True)

    payload_versions = [
        {
            "key": key,
            "filename": f"{mid}_{key}.jpg",
            "mime": "image/jpeg",
            "data_base64": base64.b64encode(data).decode("ascii"),
        }
        for key, data in versions.items()
    ]

    n = len(payload_versions)
    return JSONResponse(
        {
            "machine_id": mid,
            "original": filename,
            "provider": config.provider,
            "model": provider.model,
            "version_count": n,
            "estimated_cost_usd": round(config.cost_per_image_usd * n, 4),
            "versions": payload_versions,
        }
    )


def main() -> None:
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

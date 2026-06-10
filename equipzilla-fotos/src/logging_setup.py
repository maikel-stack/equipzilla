"""Configuracion de logging: salida a consola y a archivo."""

from __future__ import annotations

import logging
from pathlib import Path


def setup_logging(log_dir: Path, level: int = logging.INFO) -> logging.Logger:
    """Configura el logger raiz del proyecto.

    Escribe simultaneamente a consola y a ``<log_dir>/equipzilla.log``.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "equipzilla.log"

    logger = logging.getLogger("equipzilla")
    logger.setLevel(level)
    logger.handlers.clear()  # evita handlers duplicados en reejecuciones
    logger.propagate = False

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    console.setLevel(level)
    logger.addHandler(console)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(fmt)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    logger.debug("Logging inicializado. Archivo: %s", log_file)
    return logger

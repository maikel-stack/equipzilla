"""CLI del pipeline de fotos de Equipzilla.

Uso:
    python -m src.run                 # procesa todo input/
    python -m src.run --force         # reprocesa aunque exista en output/
    python -m src.run --id EXC-001    # procesa 1 foto con id explicito
    python -m src.run --dry-run       # lista lo que haria, sin llamar a la API
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from tqdm import tqdm

from .config import load_config
from .logging_setup import setup_logging
from .pipeline import Pipeline, discover_inputs, machine_id_from_path
from .providers import get_provider


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m src.run",
        description="Genera 3 versiones editadas (operador, ficha_tecnica, "
        "en_faena) de cada foto de maquinaria en input/.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reprocesa aunque las versiones ya existan en output/.",
    )
    parser.add_argument(
        "--id",
        type=str,
        default=None,
        help="Id de maquina explicito (solo valido si input/ tiene 1 sola foto).",
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Ruta a una foto concreta a procesar (ignora el resto de input/).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra que se procesaria sin llamar a la API.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Logging a nivel DEBUG.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    base_dir = Path(__file__).resolve().parent.parent

    config = load_config(base_dir)
    level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(config.log_dir, level=level)

    logger.info("═══ Equipzilla · pipeline de fotos ═══")
    logger.info("Proveedor: %s | Modelo: %s", config.provider, config.model_name)

    # Seleccion de inputs
    if args.input:
        single = Path(args.input)
        if not single.is_absolute():
            single = (base_dir / args.input).resolve()
        if not single.exists():
            logger.error("No existe el archivo: %s", single)
            return 1
        inputs = [single]
    else:
        inputs = discover_inputs(config.input_dir)

    if not inputs:
        logger.warning("No hay fotos en %s. Nada que procesar.", config.input_dir)
        return 0

    if args.id and len(inputs) > 1:
        logger.error("--id solo es valido con UNA foto de entrada (hay %d).", len(inputs))
        return 1

    logger.info("Fotos a procesar: %d", len(inputs))

    if args.dry_run:
        logger.info("── DRY RUN (no se llama a la API) ──")
        for path in inputs:
            mid = args.id or machine_id_from_path(path)
            versions = ", ".join(v.key for v in config.versions)
            logger.info("  • %s -> id='%s' | versiones: %s", path.name, mid, versions)
        return 0

    # Inicializa proveedor (valida API key, etc.)
    try:
        provider = get_provider(config)
    except Exception as exc:  # noqa: BLE001
        logger.error("No se pudo inicializar el proveedor: %s", exc)
        return 1

    pipeline = Pipeline(config, provider)

    total_generated = 0
    total_errors = 0
    machines_ok = 0

    for path in tqdm(inputs, desc="Maquinas", unit="maq"):
        machine_id = args.id or machine_id_from_path(path)
        logger.info("► Maquina '%s' (%s)", machine_id, path.name)
        result = pipeline.process_machine(path, machine_id, force=args.force)
        total_generated += len(result.generated) - len(result.skipped)
        total_errors += len(result.errors)
        if result.ok:
            machines_ok += 1

    logger.info("─────────────────────────────────────")
    logger.info(
        "Hecho. Maquinas OK: %d/%d | imagenes nuevas: %d | errores: %d",
        machines_ok,
        len(inputs),
        total_generated,
        total_errors,
    )
    est_cost = total_generated * config.cost_per_image_usd
    logger.info("Coste estimado de esta ejecucion: ~$%.2f USD", est_cost)

    return 0 if total_errors == 0 else 2


if __name__ == "__main__":
    sys.exit(main())

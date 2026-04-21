import csv
import json
import sys
from pathlib import Path

import anthropic

PRODUCTS = [
    {"id": 36, "name": "PLAT.TIJERA ELECTRICA 8 M", "machineCode": "PLAUTE008", "price": 36.57, "parentCategory": "elevadores-tijera", "carousel": "Tijera Eléctrica 8M"},
    {"id": 37, "name": "PLAT.TIJERA ELECTRICA 10 M", "machineCode": "PLAUTE010", "price": 51.06, "parentCategory": "elevadores-tijera", "carousel": "Tijera Eléctrica 10M"},
    {"id": 38, "name": "PLAT.TIJERA ELECTRICA 12 M", "machineCode": "PLAUTE012", "price": 55.20, "parentCategory": "elevadores-tijera", "carousel": "Tijera Eléctrica 12M"},
    {"id": 39, "name": "PLAT.TIJERA ELECTRICA 14 M", "machineCode": "PLAUTE014", "price": 90.39, "parentCategory": "elevadores-tijera", "carousel": "Tijera Eléctrica 14M"},
    {"id": 40, "name": "PLATAFORMA TIJERA DIESEL 12 M", "machineCode": "PLAUTD012", "price": 68.31, "parentCategory": "elevadores-tijera", "carousel": "Tijera Diesel 12M"},
    {"id": 41, "name": "PLATAFORMA TIJERA DIESEL 15 M", "machineCode": "PLAUTD015", "price": 91.08, "parentCategory": "elevadores-tijera", "carousel": "Tijera Diesel 15M"},
    {"id": 42, "name": "PLATAFORMA TIJERA DIESEL 18M", "machineCode": "PLAUTD018", "price": 106.26, "parentCategory": "elevadores-tijera", "carousel": "Tijera Diesel 18M"},
    {"id": 43, "name": "PLAT.ARTICULADA ELECTRICA 12M", "machineCode": "PLAUAE012", "price": 84.87, "parentCategory": "brazo-articulado", "carousel": "Plataforma Articulada Eléctrica 12M"},
    {"id": 44, "name": "PLAT.ARTICULADA ELECTRICA 16M", "machineCode": "PLAUAE016", "price": 108.33, "parentCategory": "brazo-articulado", "carousel": "Plataforma Articulada Eléctrica 16M"},
    {"id": 45, "name": "PLAT.ARTICULADA ELECTRICA 20M", "machineCode": "PLAUAE020", "price": 205.62, "parentCategory": "brazo-articulado", "carousel": "Plataforma Articulada Eléctrica 20M"},
    {"id": 46, "name": "PLAT.ARTICULADA DIESEL 16M", "machineCode": "PLAUAD016", "price": 89.70, "parentCategory": "brazo-articulado", "carousel": "Plataforma Articulada Diesel 16M"},
    {"id": 47, "name": "PLAT.ARTICULADA DIESEL 18M", "machineCode": "PLAUAD018", "price": 115.92, "parentCategory": "brazo-articulado", "carousel": "Plataforma Articulada Diesel 18M"},
    {"id": 48, "name": "PLAT.ARTICULADA DIESEL 20M", "machineCode": "PLAUAD020", "price": 133.17, "parentCategory": "brazo-articulado", "carousel": "Plataforma Articulada Diesel 20M"},
    {"id": 49, "name": "PLAT.ARTICULADA DIESEL 26M", "machineCode": "PLAUAD026", "price": 212.52, "parentCategory": "brazo-articulado", "carousel": "Plataforma Articulada Diesel 26M"},
    {"id": 50, "name": "PLAT.TELESCOPICA DIESEL 28M", "machineCode": "PLAUTL028", "price": 225.63, "parentCategory": "elevadores-telescopicos", "carousel": "Plataforma Telescópica 28M"},
    {"id": 51, "name": "PLAT.TELESCOPICA DIESEL 38M", "machineCode": "PLAUTL038", "price": 377.43, "parentCategory": "elevadores-telescopicos", "carousel": "Plataforma Telescópica 38M"},
    {"id": 52, "name": "PLAT.S/CAMION S/CONDUCTOR 18M", "machineCode": "PLCSTL018", "price": 204.93, "parentCategory": "camiones-plataforma-cesta", "carousel": "Plataforma sobre Camión 18M"},
    {"id": 53, "name": "PLAT.S/CAMION S/CONDUCTOR 20M", "machineCode": "PLCSTL020", "price": 227.70, "parentCategory": "camiones-plataforma-cesta", "carousel": "Plataforma sobre Camión 20M"},
    {"id": 54, "name": "PLAT.UNIPERSONAL ELECTRICA 10M", "machineCode": "PLAUUE010", "price": 89.01, "parentCategory": "elevadores-unipersonales", "carousel": "Plataforma Unipersonal 10M"},
    {"id": 55, "name": "PLAT.UNIPERSONAL ELECTRICA 12M", "machineCode": "PLAUUE012", "price": 101.43, "parentCategory": "elevadores-unipersonales", "carousel": "Plataforma Unipersonal 12M"},
    {"id": 56, "name": "GRUPO ELECTROGENO 30 KVA", "machineCode": "COEEGE030", "price": 33.12, "parentCategory": "grupos-electrogenos", "carousel": "Grupo Electrógeno 30KVA"},
    {"id": 57, "name": "GRUPO ELECTROGENO 40 KVA", "machineCode": "COEEGE040", "price": 36.57, "parentCategory": "grupos-electrogenos", "carousel": "Grupo Electrógeno 40KVA"},
    {"id": 58, "name": "GRUPO ELECTROGENO 60 KVA", "machineCode": "COEEGE060", "price": 50.37, "parentCategory": "grupos-electrogenos", "carousel": "Grupo Electrógeno 60KVA"},
    {"id": 59, "name": "GRUPO ELECTROGENO 100 KVA", "machineCode": "COEEGE100", "price": 60.03, "parentCategory": "grupos-electrogenos", "carousel": "Grupo Electrógeno 100KVA"},
    {"id": 60, "name": "GRUPO ELECTROGENO 150 KVA", "machineCode": "COEEGE150", "price": 79.35, "parentCategory": "grupos-electrogenos", "carousel": "Grupo Electrógeno 150KVA"},
    {"id": 61, "name": "GRUPO ELECTROGENO 200 KVA", "machineCode": "COEEGE200", "price": 100.05, "parentCategory": "grupos-electrogenos", "carousel": "Grupo Electrógeno 200KVA"},
    {"id": 62, "name": "GRUPO ELECTROGENO 250 KVA", "machineCode": "COEEGE250", "price": 124.20, "parentCategory": "grupos-electrogenos", "carousel": "Grupo Electrógeno 250KVA"},
    {"id": 63, "name": "CARRETILLA TT 2500 K 4X4", "machineCode": "COMDCT254", "price": 84.18, "parentCategory": "carretilla-diesel", "carousel": "Carretilla Elevadora 4x4 2500KG"},
    {"id": 64, "name": "MANIPULADOR TL 14M 4000 K", "machineCode": "COMDMT144", "price": 175.26, "parentCategory": "manipuladores-telescopicos", "carousel": "Manipulador Telescópico 14M"},
    {"id": 65, "name": "MANIPULADOR TL 17M 4000 K", "machineCode": "COMDMT174", "price": 191.82, "parentCategory": "manipuladores-telescopicos", "carousel": "Manipulador Telescópico 17M"},
    {"id": 66, "name": "MINIEXCAVADORA CADENAS 5000 K", "machineCode": "COMTME500", "price": 179.40, "parentCategory": "miniexcavadoras", "carousel": "Miniexcavadora 5000K"},
    {"id": 67, "name": "MINIEXCAVADORA CADENAS 6000 K", "machineCode": "COMTME600", "price": 187.68, "parentCategory": "miniexcavadoras", "carousel": "Miniexcavadora 6000K"},
    {"id": 68, "name": "MINIEXCAVADORA CADENAS 9000 K", "machineCode": "COMTME900", "price": 226.32, "parentCategory": "miniexcavadoras", "carousel": "Miniexcavadora 9000K"},
    {"id": 69, "name": "CARRETILLA FRONTAL DIES. 2000K", "machineCode": "INCFDI020", "price": 58.65, "parentCategory": "carretilla-diesel", "carousel": "Carretilla Elevadora Diesel 2000KG"},
    {"id": 70, "name": "CARRETILLA FRONTAL DIES. 2500K", "machineCode": "INCFDI025", "price": 63.48, "parentCategory": "carretilla-diesel", "carousel": "Carretilla Elevadora Diesel 2500KG"},
    {"id": 71, "name": "CARRETILLA FRONTAL DIES. 3000K", "machineCode": "INCFDI030", "price": 79.35, "parentCategory": "carretilla-diesel", "carousel": "Carretilla Elevadora Diesel 3000KG"},
    {"id": 72, "name": "CARRETILLA FRONTAL ELEC.2000K", "machineCode": "INCFEL020", "price": 63.48, "parentCategory": "carretilla-electricas", "carousel": "Carretilla Elevadora Eléctrica 2000KG"},
    {"id": 73, "name": "CARRETILLA FRONTAL ELEC.2500K", "machineCode": "INCFEL025", "price": 73.83, "parentCategory": "carretilla-electricas", "carousel": "Carretilla Elevadora Eléctrica 2500KG"},
    {"id": 74, "name": "CARRETILLA FRONTAL ELEC.3000K", "machineCode": "INCFEL030", "price": 83.49, "parentCategory": "carretilla-electricas", "carousel": "Carretilla Elevadora Eléctrica 3000KG"},
    {"id": 75, "name": "TRANSPALETA ELEC. A PIE 1800 K", "machineCode": "INMITEA18", "price": 26.91, "parentCategory": "transpaletas-electricas", "carousel": "Transpaleta a pie 1800KG"},
    {"id": 76, "name": "TRANSPALETA ELEC. A PIE 2000 K", "machineCode": "INMITEA20", "price": 28.98, "parentCategory": "transpaletas-electricas", "carousel": "Transpaleta a pie 2000KG"},
    {"id": 77, "name": "TRANSPALETA MANUAL 2500KG", "machineCode": "INMITM025", "price": 11.04, "parentCategory": "transpaletas-electricas", "carousel": "Transpaleta manual 2500KG"},
    {"id": 78, "name": "APILADOR ELECTRICO A PIE 1600K", "machineCode": "INMIAPA16", "price": 42.09, "parentCategory": "apilador-electrico", "carousel": "Apilador Eléctrico 1600KG"},
    {"id": 79, "name": "APILADOR ELECTRICO A PIE 2000K", "machineCode": "INMIAPA20", "price": 42.09, "parentCategory": "apilador-electrico", "carousel": "Apilador Eléctrico 2000KG"},
    {"id": 80, "name": "COMPRESOR NEUMATICO DE 5.000 L/M", "machineCode": "COMNEUDE50", "price": 31.74, "parentCategory": "compresor-de-aire", "carousel": "Compresor de Aire 5000L/M"},
    {"id": 81, "name": "COMPRESOR NEUMATICO DE 7.000 L/M", "machineCode": "COMNEUDE70", "price": 49.66, "parentCategory": "compresor-de-aire", "carousel": "Compresor de Aire 7000L/M"},
    {"id": 82, "name": "DUMPER 1500 FRONTAL RIGIDO", "machineCode": "DUM150FROR", "price": 25.72, "parentCategory": "dumpers", "carousel": "Dumper 1500KG Frontal Rigido"},
    {"id": 83, "name": "DUMPER 1500 GIRATORIO", "machineCode": "DUM150GIR", "price": 32.78, "parentCategory": "dumpers", "carousel": "Dumper 1500KG Giratorio"},
    {"id": 84, "name": "DUMPER 3000 ARTICULADO FRONTAL 4 X 4", "machineCode": "DUM300ARTF", "price": 53.19, "parentCategory": "dumpers", "carousel": "Dumper 3000KG Frontal 4x4"},
    {"id": 85, "name": "DUMPER 3500 KG ARTICULADO GIRATORIO 4 X 4", "machineCode": "DUM350KGAR", "price": 53.19, "parentCategory": "dumpers", "carousel": "Dumper 3500KG Giratorio 4x4"},
    {"id": 86, "name": "RETRO 8TN", "machineCode": "RET8TN", "price": 156.31, "parentCategory": "miniexcavadoras", "carousel": "Miniexcavadora 8TN"},
    {"id": 87, "name": "MINICARGADORA 2,4 TN (B-S450)", "machineCode": "MIN24TNBS4", "price": 90.36, "parentCategory": "minicargadoras", "carousel": "Minicargadora 2.4TN"},
    {"id": 88, "name": "MINICARGADORA 3 TN (B-S185)", "machineCode": "MIN3TNBS1", "price": 102.44, "parentCategory": "minicargadoras", "carousel": "Minicargadora 3TN"},
    {"id": 89, "name": "MINICARGADORA FRONTAL RIGIDA 3.2TN", "machineCode": "MINFRORI01", "price": 97.62, "parentCategory": "minicargadoras", "carousel": "Minicargadora 3.2TN Rigida"},
    {"id": 90, "name": "RODILLO DUPLEX 88", "machineCode": "RODDUP88", "price": 49.17, "parentCategory": "rodillo-compactador", "carousel": "Rodillo Compactador Duplex"},
    {"id": 91, "name": "RODILLO TANDEM 900 1500KG", "machineCode": "RODTAN9001", "price": 74.26, "parentCategory": "rodillo-compactador", "carousel": "Rodillo Compactador Tandem 1500KG"},
    {"id": 92, "name": "RODILLO TANDEM 1200 3000 KG", "machineCode": "RODTAN1203", "price": 74.26, "parentCategory": "rodillo-compactador", "carousel": "Rodillo Compactador Tandem 3000KG"},
    {"id": 93, "name": "RODILLO CLASIFICACION VM2 ( 8TN )", "machineCode": "RODCLAVM28", "price": 117.66, "parentCategory": "rodillo-compactador", "carousel": "Rodillo Compactador VM2"},
    {"id": 94, "name": "RODILLO CLASIFICACION VM3 (13 TN)", "machineCode": "RODCLAVM31", "price": 155.27, "parentCategory": "rodillo-compactador", "carousel": "Rodillo Compactador VM3"},
]

SYSTEM = """Eres copywriter SEO de Equipzilla, marketplace B2B de alquiler de maquinaria industrial en España.

Para cada producto generas EXACTAMENTE estos 8 campos:

1. MetaTagTitle (50-60 chars): formato "Alquiler [producto específico] | Equipzilla"
2. MetaTagDescription (140-160 chars): incluye precio desde, beneficio, CTA "pide presupuesto". Natural, no keyword stuffing.
3. keywords: 6-10 keywords separadas por coma. Incluye: nombre producto, variantes comunes, "alquiler", "España". Sin ubicaciones específicas.
4. description_short (120-180 chars): 1-2 frases. Pitch claro del producto + caso de uso principal.
5. description_long (350-500 chars): 2-3 párrafos breves sin saltos de línea múltiples. Cubre: qué es, para qué se usa, ventajas frente a alternativas. Mencionar entrega en España.
6. extended_info (200-350 chars): características técnicas en formato bullets con "•". Altura máxima, carga útil, motor/alimentación, dimensiones cuando apliquen. Usa valores estándar de la industria para esa clase de máquina.
7. title: H1 descriptivo "Alquiler de [producto completo con especificaciones]"
8. PhotoAlt (60-120 chars): descripción accesible de la imagen, incluye nombre producto + "alquiler Equipzilla"

REGLAS:
- Tono profesional, directo, español de España. Sin fluff, sin superlativos vacíos ("la mejor", "increíble").
- Usa los datos estándar de la industria para specs técnicas (alturas, cargas, motorizaciones típicas).
- Precios siempre como "desde X€/día" usando el `price` del input.
- Cada producto DEBE tener copy único — no copies descripciones entre productos similares.
- Responde SOLO JSON válido, sin prosa, sin markdown fences. Formato:
[{"id": 36, "MetaTagTitle": "...", "MetaTagDescription": "...", "keywords": "...", "description_short": "...", "description_long": "...", "extended_info": "...", "title": "...", "PhotoAlt": "..."}, ...]
"""


def generate(batch: list[dict]) -> list[dict]:
    client = anthropic.Anthropic()
    user = (
        "Genera el copy SEO para estos productos. Devuelve JSON array con un objeto por producto, "
        "manteniendo el orden. Solo JSON, sin texto antes ni después, sin markdown fences.\n\n"
        f"{json.dumps(batch, ensure_ascii=False, indent=2)}"
    )
    with client.messages.stream(
        model="claude-opus-4-7",
        max_tokens=32000,
        thinking={"type": "adaptive"},
        system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
    ) as stream:
        msg = stream.get_final_message()
    text = "".join(b.text for b in msg.content if b.type == "text").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(text)


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet-id", help="Google Sheet ID. If set, writes directly to the sheet instead of CSV.")
    ap.add_argument("--tab", default="Hoja 1", help="Tab name in the sheet (default: 'Hoja 1')")
    ap.add_argument("--start-row", type=int, default=4, help="First data row in the sheet (default: 4)")
    ap.add_argument("--dry-run-copy", action="store_true", help="Skip Claude, read existing CSV for sheet test")
    args = ap.parse_args()

    out_path = Path(__file__).parent / "products_copy.csv"

    if args.dry_run_copy and out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            all_copy = list(csv.DictReader(f))
            for r in all_copy:
                r["id"] = int(r["id"])
    else:
        batch_size = 15
        all_copy = []
        for i in range(0, len(PRODUCTS), batch_size):
            batch = PRODUCTS[i : i + batch_size]
            print(f"[{i + 1}-{i + len(batch)}] generating...", file=sys.stderr)
            all_copy.extend(generate(batch))

    by_id = {row["id"]: row for row in all_copy}

    fields = [
        "id", "name", "machineCode", "price", "parentCategory",
        "MetaTagTitle", "MetaTagDescription", "keywords",
        "description_short", "description_long", "extended_info",
        "title", "title_carousel", "PhotoAlt",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for p in PRODUCTS:
            copy = by_id.get(p["id"], {})
            w.writerow(
                {
                    "id": p["id"],
                    "name": p["name"],
                    "machineCode": p["machineCode"],
                    "price": p["price"],
                    "parentCategory": p["parentCategory"],
                    "MetaTagTitle": copy.get("MetaTagTitle", ""),
                    "MetaTagDescription": copy.get("MetaTagDescription", ""),
                    "keywords": copy.get("keywords", ""),
                    "description_short": copy.get("description_short", ""),
                    "description_long": copy.get("description_long", ""),
                    "extended_info": copy.get("extended_info", ""),
                    "title": copy.get("title", ""),
                    "title_carousel": p["carousel"],
                    "PhotoAlt": copy.get("PhotoAlt", ""),
                }
            )
    print(f"Wrote {len(PRODUCTS)} rows to {out_path}", file=sys.stderr)

    if args.sheet_id:
        _write_to_sheet(PRODUCTS, by_id, args.sheet_id, args.tab, args.start_row)

    return 0


def _write_to_sheet(products: list[dict], by_id: dict, sheet_id: str, tab: str, start_row: int) -> None:
    from cmo.connectors import google_sheets

    main_rows: list[list] = []
    alt_rows: list[list] = []
    for p in products:
        copy = by_id.get(p["id"], {})
        main_rows.append(
            [
                copy.get("MetaTagTitle", ""),
                copy.get("MetaTagDescription", ""),
                copy.get("keywords", ""),
                "",
                copy.get("description_short", ""),
                copy.get("description_long", ""),
                copy.get("extended_info", ""),
                copy.get("title", ""),
            ]
        )
        alt_rows.append([copy.get("PhotoAlt", "")])

    end_row = start_row + len(products) - 1

    main_range = f"'{tab}'!F{start_row}:M{end_row}"
    print(f"Writing {len(main_rows)} rows to {main_range}...", file=sys.stderr)
    r1 = google_sheets.write_range(sheet_id, main_range, main_rows)
    print(f"  {r1.get('updatedCells')} cells updated.", file=sys.stderr)

    alt_range = f"'{tab}'!P{start_row}:P{end_row}"
    print(f"Writing {len(alt_rows)} PhotoAlt rows to {alt_range}...", file=sys.stderr)
    r2 = google_sheets.write_range(sheet_id, alt_range, alt_rows)
    print(f"  {r2.get('updatedCells')} cells updated.", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())

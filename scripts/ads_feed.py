#!/usr/bin/env python3
"""Qué parte del stock está anunciándose en Shopping, y qué demanda no tiene producto.

Dos preguntas que la cuenta no responde sola:

  1. De las máquinas del catálogo (data/machines.json), ¿cuáles aparecen en
     Shopping? Lo que no está en el feed no se anuncia, por mucho que se busque.
  2. De las categorías que la gente busca, ¿cuáles no tenemos en stock? Anunciar
     una categoría sin producto trae clics que no pueden acabar en venta.

Uso: python3 scripts/ads_feed.py
"""
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ads_metricas import consulta  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOGO = os.path.join(RAIZ, "data", "machines.json")

# categoría → palabras que la identifican en el nombre de la máquina del catálogo
# El orden importa: se asigna la primera familia que coincide. Las marcas de
# elevación van primero porque algunos modelos comparten prefijo con las minis
# (el Manitou 170 AETJL es una plataforma articulada, no una miniexcavadora).
FAMILIAS = {
    "plataformas": ["haulotte", "genie", "jlg 1", "jlg 4", "jlg 8", "jlg e", "manitou 1", "multitel", "compact"],
    "telescopicos": ["magni", "merlo", "jcb 5", "jlg 40"],
    "carretillas": ["clark", "yale", "hyster", "jungheinrich"],
    "minicargadoras": ["bobcat", "s70"],
    "dumpers": ["wacker", "dumper"],
    "retroexcavadoras": ["retro", "3cx", "4cx", "mixta"],
    "miniexcavadoras": ["kx 0", "u 1", "u 3", "u 5", "k 008", "dx 27", "dx 35"],
    "excavadoras": ["dx 1", "dx 2", "dl 4", "kx 060", "kx 080"],
}


def limpia(s):
    s = "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip()


def familia(nombre):
    n = limpia(nombre)
    for fam, claves in FAMILIAS.items():
        if any(k in n for k in claves):
            return fam
    return "otras"


def en_shopping():
    """Títulos de producto que han tenido actividad en Shopping los últimos 30 días."""
    return {r["segments"].get("productTitle", ""): int(r["metrics"].get("clicks") or 0)
            for r in consulta(
                "SELECT segments.product_item_id, segments.product_title, metrics.clicks, "
                "metrics.cost_micros FROM shopping_performance_view WHERE segments.date DURING LAST_30_DAYS")}


def demanda_por_familia():
    """Impresiones de búsqueda por familia, de los términos reales."""
    from ads_demanda import CATEGORIAS, demanda
    return {c: d["impresiones"] for c, d in demanda(30).items()}


if __name__ == "__main__":
    catalogo = json.load(open(CATALOGO, encoding="utf-8"))
    activos = en_shopping()
    activos_limpios = {limpia(t) for t in activos}
    print(f"Catálogo: {len(catalogo)} máquinas · en Shopping con actividad en 30 días: {len(activos)}\n")

    por_fam = {}
    for m in catalogo:
        nombre = m.get("n", "")
        fam = familia(nombre)
        anunciada = any(limpia(nombre) in t or t in limpia(nombre) for t in activos_limpios)
        d = por_fam.setdefault(fam, {"total": 0, "anunciadas": 0, "fuera": []})
        d["total"] += 1
        if anunciada:
            d["anunciadas"] += 1
        else:
            d["fuera"].append(f"{nombre} ({m.get('p', '?')} €)")

    dem = demanda_por_familia()
    print(f"{'familia':<18}{'en stock':>9}{'en Shopping':>13}{'búsquedas 30 d':>16}")
    for fam, d in sorted(por_fam.items(), key=lambda x: -dem.get(x[0], 0)):
        print(f"{fam:<18}{d['total']:>9}{d['anunciadas']:>13}{dem.get(fam, 0):>16}")

    print("\nDemanda sin producto en el catálogo:")
    vacias = [(i, c) for c, i in dem.items() if i > 1000 and por_fam.get(c, {}).get("total", 0) == 0]
    for impr, cat in sorted(vacias, reverse=True):
        print(f"  {cat}: {impr} impresiones al mes y 0 máquinas en stock")
    if not vacias:
        print("  ninguna")

    print("\nMáquinas en stock que Shopping no anuncia:")
    for fam, d in sorted(por_fam.items(), key=lambda x: -dem.get(x[0], 0)):
        if d["fuera"] and dem.get(fam, 0) > 100:
            print(f"  {fam} ({dem.get(fam, 0)} búsquedas al mes): {', '.join(d['fuera'][:6])}")

#!/usr/bin/env python3
"""Demanda real por categoría, desde los términos de búsqueda de la cuenta.

Para qué sirve. Google nos enseña lo que la gente busca de verdad antes de que
existan la página y el grupo. Este script agrupa los términos de los últimos 30
días por categoría de máquina y los cruza con el estado del grupo que debería
recogerlos. Así se ve qué demanda estamos dejando pasar y con qué prioridad
pedir cada página a tecnología.

Leer la columna «estado»: un grupo ENABLED SIN ANUNCIO no sale nunca, así que
toda su demanda se la queda Shopping o el grupo genérico, que aterrizan en una
página que no es la que el usuario buscaba.

Uso: python3 scripts/ads_demanda.py [dias]     # por defecto 30
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ads_metricas import consulta  # noqa: E402

# categoría → (palabras que la identifican en el término, nombre del grupo que debería recogerla)
CATEGORIAS = {
    "retroexcavadoras": (["retroexcavadora", "retro mixta", "retro excavadora", "mini retro", "miniretro", "mixta"], "Retroexcavadoras 2a mano"),
    "miniexcavadoras": (["miniexcavadora", "mini excavadora", "mini giratoria", "minigiratoria"], "Miniexcavadoras 2a mano"),
    "excavadoras": (["excavadora", "giratoria"], "Excavadoras 2a mano"),
    "minicargadoras": (["minicargadora", "mini cargadora", "bobcat", "minipala", "mini pala"], "Minicargadoras 2a mano"),
    "telescopicos": (["telescop", "manitou", "telehandler"], "Manipuladores telescopicos 2a mano"),
    "plataformas": (["plataforma", "tijera", "haulotte", "genie", "jlg"], "Plataformas elevadoras 2a mano"),
    "carretillas": (["carretilla", "toro elevador", "apilador", "hyster"], "Carretillas elevadoras 2a mano"),
    "dumpers": (["dumper"], "Dumpers 2a mano"),
    "rodillos": (["rodillo", "compactador", "rulo"], "Rodillos y compactadores 2a mano"),
}


def estado_grupos():
    """Nombre del grupo → estado real, contando si tiene anuncio activo."""
    grupos = {r["adGroup"]["name"]: {"estado": r["adGroup"]["status"], "anuncios": 0}
              for r in consulta("SELECT ad_group.name, ad_group.status FROM ad_group WHERE ad_group.status != 'REMOVED'")}
    for r in consulta("SELECT ad_group.name FROM ad_group_ad WHERE ad_group_ad.status = 'ENABLED'"):
        n = r["adGroup"]["name"]
        if n in grupos:
            grupos[n]["anuncios"] += 1
    return grupos


def demanda(dias=30):
    rango = {7: "LAST_7_DAYS", 14: "LAST_14_DAYS", 30: "LAST_30_DAYS"}.get(dias, "LAST_30_DAYS")
    agg = {c: {"terminos": 0, "impresiones": 0, "clics": 0, "coste": 0.0, "top": []} for c in CATEGORIAS}
    for r in consulta(
            "SELECT search_term_view.search_term, metrics.impressions, metrics.clicks, "
            "metrics.cost_micros FROM search_term_view WHERE segments.date DURING %s" % rango):
        t = r["searchTermView"]["searchTerm"]
        m = r["metrics"]
        for cat, (claves, _) in CATEGORIAS.items():
            if any(k in t for k in claves):
                d = agg[cat]
                d["terminos"] += 1
                d["impresiones"] += int(m.get("impressions") or 0)
                d["clics"] += int(m.get("clicks") or 0)
                d["coste"] += int(m.get("costMicros") or 0) / 1e6
                d["top"].append((int(m.get("impressions") or 0), t))
                break
    return agg


if __name__ == "__main__":
    dias = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    agg, grupos = demanda(dias), estado_grupos()
    print(f"Demanda por categoría según los términos de búsqueda · últimos {dias} días\n")
    print(f"{'categoría':<17}{'términos':>9}{'impresiones':>13}{'clics':>7}{'coste':>9}   estado del grupo")
    huerfanas = []
    for cat, d in sorted(agg.items(), key=lambda x: -x[1]["impresiones"]):
        g = grupos.get(CATEGORIAS[cat][1], {})
        if not g:
            estado = "NO EXISTE EL GRUPO"
        elif g["estado"] != "ENABLED":
            estado = f"{g['estado'].lower()}"
        elif g["anuncios"] == 0:
            estado = "activo SIN ANUNCIO -> no sale"
        else:
            estado = f"activo, {g['anuncios']} anuncio(s)"
        if d["impresiones"] and ("SIN ANUNCIO" in estado or "paused" in estado or "NO EXISTE" in estado):
            huerfanas.append((d["impresiones"], cat, estado))
        print(f"{cat:<17}{d['terminos']:>9}{d['impresiones']:>13}{d['clics']:>7}{d['coste']:>8.2f}€   {estado}")
    if huerfanas:
        print("\nDemanda que hoy no puede recoger su grupo:")
        for impr, cat, estado in sorted(huerfanas, reverse=True):
            ejemplos = ", ".join(t for _, t in sorted(agg[cat]["top"], reverse=True)[:3])
            print(f"  {cat}: {impr} impresiones · {estado}")
            print(f"     más buscado: {ejemplos}")

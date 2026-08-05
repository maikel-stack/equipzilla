#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Motor de estrategia SEO basada en datos reales.

Ingiere los export de Search Console (y GA4 si existe) y produce un plan
priorizado con oportunidades accionables:

  Entrada (output/):
    gsc_queries.csv   query, clics, impresiones, ctr_%, posicion
    gsc_pages.csv     pagina, clics, impresiones, ctr_%, posicion
    ga4_landing.csv   (opcional) landing_page, sesiones, ..., conversiones, ingresos

  Salida (output/):
    estrategia_seo.md   plan narrativo priorizado con tablas
    oportunidades.csv   cada oportunidad con tipo, objetivo, métricas y score

Buckets:
  1. QUICK-WIN     keywords en posición 5-20 con impresiones → empujón a página 1
  2. CTR-BAJO      posición <=10 pero CTR muy por debajo de lo esperado →
                   reescribir title/meta (enlaza con el trabajo de fichas/categorías)
  3. HUECO         mucha impresión en pág. 2-3 sin clics → página dedicada / enlaces
  4. PROTEGER      top páginas por clics → vigilar y consolidar
  5. COMPRA        foco en el funnel /compra (+ conversiones GA4 si disponibles)

No inventa nada: si falta un fichero, ese bucket se omite y se avisa.
"""
import csv, os, sys, math
from pathlib import Path

OUT = Path(os.environ.get("OUT_DIR",
      Path(__file__).resolve().parent.parent / "output"))

# Curva de CTR esperado por posición (media de industria, blended desktop+móvil)
CTR_CURVE = {1: 27.0, 2: 15.0, 3: 10.0, 4: 7.0, 5: 5.1, 6: 4.0, 7: 3.2,
             8: 2.6, 9: 2.2, 10: 1.9}
def expected_ctr(pos):
    p = int(round(pos))
    if p <= 10:
        return CTR_CURVE.get(p, 1.9)
    if p <= 20:
        return 1.0
    return 0.5

def readcsv(name):
    path = OUT / name
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def num(x, d=0.0):
    try: return float(str(x).replace(",", "."))
    except: return d

def main():
    q = readcsv("gsc_queries.csv")
    pg = readcsv("gsc_pages.csv")
    ga = readcsv("ga4_landing.csv")
    missing = [n for n, v in [("gsc_queries.csv", q), ("gsc_pages.csv", pg)] if v is None]
    if missing:
        print("FALTAN datos de Search Console:", ", ".join(missing))
        print("Ejecuta primero:  GSC_KEY=... python scripts/gsc_pull.py --site sc-domain:equipzilla.com")
        sys.exit(1)

    for r in q:
        r["clicks"] = num(r.get("clics")); r["imp"] = num(r.get("impresiones"))
        r["ctr"] = num(r.get("ctr_%")); r["pos"] = num(r.get("posicion"))
    for r in pg:
        r["clicks"] = num(r.get("clics")); r["imp"] = num(r.get("impresiones"))
        r["ctr"] = num(r.get("ctr_%")); r["pos"] = num(r.get("posicion"))

    tot_c = sum(r["clicks"] for r in q); tot_i = sum(r["imp"] for r in q)

    opps = []

    # 1. QUICK-WIN: posición 5-20, impresiones relevantes
    qw = [r for r in q if 4.5 <= r["pos"] <= 20 and r["imp"] >= 30]
    for r in qw:
        prox = (20 - r["pos"]) / 15.0          # más cerca de pág.1 = mayor factor
        r["score"] = r["imp"] * (0.4 + 0.6 * prox)
        opps.append(("QUICK-WIN", r["query"], r))
    qw.sort(key=lambda r: r["score"], reverse=True)

    # 2. CTR-BAJO: posición <=10, CTR muy por debajo de lo esperado
    cb = []
    for r in q:
        if r["pos"] <= 10 and r["imp"] >= 50:
            exp = expected_ctr(r["pos"])
            gap = exp - r["ctr"]
            if gap >= 1.5:                      # al menos 1.5 puntos por debajo
                r["gap"] = gap
                r["clics_recuperables"] = round(r["imp"] * gap / 100.0)
                r["score"] = r["clics_recuperables"]
                cb.append(r); opps.append(("CTR-BAJO", r["query"], r))
    cb.sort(key=lambda r: r["score"], reverse=True)

    # 3. HUECO: pág 2-3 (pos 11-30), muchas impresiones, casi sin clics
    hu = [r for r in q if 10.5 <= r["pos"] <= 30 and r["imp"] >= 80 and r["clicks"] <= 2]
    for r in hu:
        r["score"] = r["imp"]
        opps.append(("HUECO", r["query"], r))
    hu.sort(key=lambda r: r["score"], reverse=True)

    # 4. PROTEGER: top páginas por clics
    top_pg = sorted(pg, key=lambda r: r["clicks"], reverse=True)[:15]

    # 5. COMPRA: páginas del funnel de compra
    compra = [r for r in pg if "/compra" in r["pagina"]]
    compra.sort(key=lambda r: r["imp"], reverse=True)

    # GA4 merge (opcional)
    ga_map = {}
    if ga:
        for r in ga:
            lp = r.get("landing_page", "")
            ga_map[lp.rstrip("/")] = {
                "sesiones": num(r.get("sesiones")),
                "conversiones": num(r.get("conversiones")),
                "ingresos": num(r.get("ingresos")),
            }

    def md_table(rows, cols, fmt):
        out = ["| " + " | ".join(c for c, _ in cols) + " |",
               "|" + "|".join("---" for _ in cols) + "|"]
        for r in rows:
            out.append("| " + " | ".join(fmt(r, k) for _, k in cols) + " |")
        return "\n".join(out)

    def cell(r, k):
        v = r.get(k, "")
        if isinstance(v, float):
            return f"{v:.1f}" if k in ("pos", "ctr", "gap") else f"{int(v)}"
        return str(v)[:70]

    L = []
    L.append("# Estrategia SEO basada en datos — Equipzilla\n")
    L.append(f"Fuente: Search Console"
             + (" + GA4" if ga else " (GA4 no conectado aún)") + ".\n")
    L.append(f"**Totales del periodo:** {int(tot_c)} clics · {int(tot_i)} impresiones · "
             f"CTR medio {100*tot_c/tot_i if tot_i else 0:.2f}% · "
             f"{len(q)} consultas · {len(pg)} páginas.\n")
    L.append("Prioriza de arriba abajo: cada bucket está ordenado por impacto estimado.\n")

    L.append("\n## 1. Quick-wins — a distancia de página 1 (posición 5-20)\n")
    L.append("_Empújalas con enlaces internos + refuerzo de contenido. ROI más rápido._\n")
    L.append(md_table(qw[:20],
        [("Keyword", "query"), ("Pos", "pos"), ("Impres.", "imp"),
         ("Clics", "clicks"), ("CTR%", "ctr")], cell))

    L.append("\n\n## 2. CTR bajo — reescribir title/meta (posición ≤10)\n")
    L.append("_Ya rankean; pierden clics por un snippet flojo. Conecta con el trabajo de "
             "MetaTagTitle/MetaTagDescription. `clics_recuperables` = clics/mes estimados si "
             "el CTR sube al esperado para su posición._\n")
    L.append(md_table(cb[:20],
        [("Keyword", "query"), ("Pos", "pos"), ("CTR%", "ctr"),
         ("Esperado-gap", "gap"), ("Impres.", "imp"), ("Clics recup.", "clics_recuperables")], cell))

    L.append("\n\n## 3. Huecos de contenido — impresiones en pág. 2-3 sin clics\n")
    L.append("_Google te muestra pero no confía lo suficiente: crea/expande página dedicada._\n")
    L.append(md_table(hu[:20],
        [("Keyword", "query"), ("Pos", "pos"), ("Impres.", "imp"), ("Clics", "clicks")], cell))

    L.append("\n\n## 4. Páginas a proteger — top por clics\n")
    L.append(md_table(top_pg,
        [("Página", "pagina"), ("Clics", "clicks"), ("Impres.", "imp"),
         ("CTR%", "ctr"), ("Pos", "pos")], cell))

    L.append("\n\n## 5. Funnel de compra — rendimiento de /compra\n")
    if compra:
        if ga:
            L.append("_Cruce con GA4: prioriza SEO donde ya hay conversiones._\n")
            for r in compra[:20]:
                g = ga_map.get(r["pagina"].replace("https://equipzilla.com", "").rstrip("/"), {})
                r["conv"] = g.get("conversiones", "")
        L.append(md_table(compra[:20],
            [("Página", "pagina"), ("Impres.", "imp"), ("Clics", "clicks"),
             ("CTR%", "ctr"), ("Pos", "pos")] + ([("Conv.", "conv")] if ga else []), cell))
    else:
        L.append("_No hay páginas /compra en los datos del periodo (¿aún sin indexar/tráfico?)._")

    L.append("\n\n## Resumen de acciones\n")
    L.append(f"- **{len(qw)}** quick-wins detectadas → priorizar top 20 con enlazado interno.")
    L.append(f"- **{len(cb)}** keywords con CTR mejorable → aplicar title/meta optimizados "
             f"(~{int(sum(r['clics_recuperables'] for r in cb))} clics/mes recuperables estimados).")
    L.append(f"- **{len(hu)}** huecos de contenido → nuevas páginas / expansión.")
    L.append(f"- **{len(compra)}** páginas de compra con datos → optimizar las de mayor impresión.")

    (OUT / "estrategia_seo.md").write_text("\n".join(L), encoding="utf-8")

    # oportunidades.csv
    with open(OUT / "oportunidades.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["tipo", "objetivo", "posicion", "impresiones", "clics",
                    "ctr_%", "score", "clics_recuperables"])
        for tipo, obj, r in sorted(opps, key=lambda x: x[2].get("score", 0), reverse=True):
            w.writerow([tipo, obj, f"{r['pos']:.1f}", int(r["imp"]), int(r["clicks"]),
                        f"{r['ctr']:.1f}", int(r.get("score", 0)),
                        r.get("clics_recuperables", "")])

    print(f"OK -> {OUT/'estrategia_seo.md'}  y  {OUT/'oportunidades.csv'}")
    print(f"Quick-wins: {len(qw)} | CTR-bajo: {len(cb)} | Huecos: {len(hu)} | Compra: {len(compra)}")

if __name__ == "__main__":
    main()

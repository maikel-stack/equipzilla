#!/usr/bin/env python3
"""Cola comercial priorizada (instrucción maestra §18-19).

La salida de Growth no es "tenemos N leads": es una lista de oportunidades
ordenadas por probabilidad de venta, cada una con qué necesita, qué tenemos
que encaje y qué hacer ahora.

Cruza:
  · clics de TODAS las campañas ABM de Brevo (qué máquina miró cada uno)
  · stock real de data/machines.json (matching por categoría y precio)
  · Pipedrive (si ya es un trato abierto, no se llama en frío)

Escribe la pestaña "Cola comercial" del Sheet de mando.

Uso:
    python3 scripts/cola_comercial.py [--sheet] [dias]
"""
import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panel_horario import (SHEET_ID, brevo, campanas, clickers,  # noqa: E402
                           falta, maquina_de_url, pipedrive, subir)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Cómo se traduce lo que el lead miró a una categoría de nuestro stock.
# Referencias internas que usaban las campañas antiguas (columna "img" del
# stock). Sin esto, un clic en "KB121" no se reconoce como miniexcavadora.
PREFIJO_REF = [(r"^KB|^KU", "mini"), (r"^DX\d|^D2\d", "exca"), (r"^DL", "pala"),
               (r"^CL|^GAM-(DFG|ERP)", "carr"), (r"^EL-|^GAM-(MANITOU|COMPACT)", "plat"),
               (r"^MT-", "mini")]

CATEGORIAS = [
    (r"jlg|genie|haulotte|manitou 1[0-9]0|tijera|plataforma|articulada|multitel|elevadora de tijera", "plat", "Plataformas de elevación"),
    (r"kubota (u|k|kx)|develon|doosan dx (2[0-9]|3[0-9])|mini ?exc|miniexc", "mini", "Miniexcavadoras"),
    (r"doosan dx (1[0-9]{2}|2[0-9]{2})|excavadora|giratoria", "exca", "Excavadoras"),
    (r"carretilla|hyster|yale|jungheinrich|clark|toro|transpaleta", "carr", "Carretillas"),
    (r"telesc|manitou m|merlo", "tele", "Telescópicas"),
    (r"pala|bobcat|cargadora|minicargadora", "pala", "Palas y minicargadoras"),
    (r"dumper|wacker", "dum", "Dumpers"),
]
ETIQUETA = {c: n for _, c, n in CATEGORIAS}


def categoria(texto):
    t = (texto or "").lower()
    for patron, cat, _ in CATEGORIAS:
        if re.search(patron, t):
            return cat
    ref = (texto or "").strip().upper()
    for patron, cat in PREFIJO_REF:
        if re.search(patron, ref):
            return cat
    return ""


def en_stock(texto, inv):
    """Busca la máquina que clicó dentro de nuestro stock, por nombre o por
    referencia interna. Devuelve la ficha real: de ahí sale el precio de
    referencia, que es mucho más fiable que el que venga en el texto."""
    t = re.sub(r"\s+", " ", (texto or "").lower()).strip()
    ref = (texto or "").strip().upper().split()[0] if texto else ""
    for fichas in inv.values():
        for f in fichas:
            if f["img"].upper() == ref:
                return f
            n = f["n"].lower()
            if n and (n in t or t.startswith(n[:14])):
                return f
    return None


def stock():
    m = json.load(open(os.path.join(RAIZ, "data", "machines.json")))
    por_cat = {}
    for x in m:
        por_cat.setdefault(x["c"], []).append(x)
    for v in por_cat.values():
        v.sort(key=lambda x: x.get("p") or 0)
    return por_cat


def encajes(cat, precio_ref, inv, tope=3):
    """Máquinas nuestras que encajan: misma categoría, precio cercano."""
    ops = inv.get(cat) or []
    if not ops:
        return []
    if precio_ref:
        ops = sorted(ops, key=lambda x: abs((x.get("p") or 0) - precio_ref))
    return ops[:tope]


def precio_de(texto):
    m = re.search(r"([\d.]+)\s*€", texto or "")
    if not m:
        return 0
    try:
        return int(m.group(1).replace(".", ""))
    except ValueError:
        return 0


def en_crm():
    """Emails que ya tienen trato abierto: ésos los lleva comercial, no la cola."""
    abiertos = set()
    start = 0
    while True:
        d = pipedrive("/deals", start=start, limit=500, status="open")
        datos = d.get("data") or []
        for x in datos:
            p = (x.get("person_id") or {})
            for e in (p.get("email") or []):
                if e.get("value"):
                    abiertos.add(e["value"].strip().lower())
        if not (d.get("additional_data", {}).get("pagination", {})
                .get("more_items_in_collection")):
            break
        start += 500
    return abiertos


def recoger(dias=60):
    """Todo el que ha clicado en las campañas ABM de los últimos `dias`."""
    corte = (dt.date.today() - dt.timedelta(days=dias)).isoformat()
    gente = {}
    for c in campanas(20):
        if (c["fecha"] or "")[:10] < corte:
            continue
        for r in clickers(c["id"]):
            em = (r.get("Email_ID") or "").strip().lower()
            if not em:
                continue
            miro = [maquina_de_url(k) for k, v in r.items()
                    if k.startswith("http") and (v or "").strip()]
            miro = [x for x in dict.fromkeys(miro) if x and x not in ("web", "WhatsApp")]
            g = gente.setdefault(em, dict(email=em, clics=0, campanas=set(),
                                          maquinas=[], ultima=""))
            try:
                g["clics"] += int(r.get("Clicked_Links_Count") or 0)
            except ValueError:
                pass
            g["campanas"].add(c["nombre"][:38])
            g["maquinas"] += miro
            g["ultima"] = max(g["ultima"], c["fecha"])
    return gente


def puntuar(g, hoy):
    """Score = intención (clics) + recencia + repetición + especificidad."""
    p, que = 0, []
    p += min(g["clics"], 5) * 12
    if g["clics"] >= 2:
        que.append("%d clics" % g["clics"])
    dias = (hoy - dt.date.fromisoformat(g["ultima"][:10])).days if g["ultima"] else 99
    if dias <= 2:
        p += 30; que.append("clic de hoy/ayer")
    elif dias <= 7:
        p += 20; que.append("clic esta semana")
    elif dias <= 21:
        p += 10
    if len(g["campanas"]) >= 2:
        p += 25; que.append("repite en %d campañas" % len(g["campanas"]))
    if g["maquinas"]:
        p += 15; que.append("máquina concreta")
    return p, " · ".join(que)


def construir(dias=60):
    hoy = dt.date.today()
    inv = stock()
    crm = en_crm()
    filas = [["COLA COMERCIAL PRIORIZADA · generada %s" % dt.datetime.now(dt.timezone(dt.timedelta(hours=2))).strftime("%d/%m/%Y %H:%M")],
             ["Ordenada por probabilidad de venta. No sustituye a la lista manual del equipo."],
             [],
             ["Score", "Prioridad", "Email", "Qué miró", "Categoría", "Presupuesto señalado",
              "Qué tenemos que encaja", "Origen", "Última señal", "Por qué", "Siguiente acción"]]
    filas_datos = []
    for g in recoger(dias).values():
        if g["email"] in crm:
            continue                       # ya es trato abierto: lo lleva comercial
        score, porque = puntuar(g, hoy)
        cats = [c for c in (categoria(m) for m in g["maquinas"]) if c]
        cat = cats[0] if cats else ""
        pref = max((precio_de(m) for m in g["maquinas"]), default=0)
        if not pref:
            # sin precio en el texto: usar el de la máquina que clicó, si la
            # tenemos. Evita ofrecer una tijera de 3.000 € a quien miró una
            # articulada de 20.500 €.
            fichas = [f for f in (en_stock(m, inv) for m in g["maquinas"]) if f]
            if fichas:
                pref = max(f.get("p") or 0 for f in fichas)
                cat = cat or fichas[0]["c"]
        ops = encajes(cat, pref, inv)
        encaja = " · ".join("%s (%s €)" % (o["n"], format(o["p"], ",d").replace(",", "."))
                            for o in ops) or "sin stock en su categoría → sourcing"
        nivel = ("🔥 HOT" if score >= 60 else "🟠 WARM" if score >= 35
                 else "🔵 NURTURE" if score >= 20 else "⚪ LOW")
        accion = ("Llamar hoy: tiene máquina y presupuesto señalados"
                  if score >= 60 else
                  "Llamar esta semana con las alternativas que encajan"
                  if score >= 35 else "Email de seguimiento con su categoría")
        if not ops and cat:
            accion = "Llamar y anotar en Want-to-Buy: no tenemos stock que encaje"
        filas_datos.append([score, nivel, g["email"],
                            " · ".join(dict.fromkeys(g["maquinas"]))[:70] or "—",
                            ETIQUETA.get(cat, "—"),
                            ("%s €" % format(pref, ",d").replace(",", ".")) if pref else "—",
                            encaja[:90], " / ".join(sorted(g["campanas"]))[:60],
                            g["ultima"][:16], porque, accion])
    filas_datos.sort(key=lambda f: -f[0])
    return filas + filas_datos


if __name__ == "__main__":
    # Sin credenciales la cola saldría vacía; publicarla borraría las
    # oportunidades buenas del Sheet (ver el mismo guardarraíl en panel_horario).
    ausentes = falta("brevo_key", "pipedrive_key")
    if ausentes:
        raise SystemExit(
            "COLA NO ACTUALIZADA · faltan credenciales: " + ", ".join(ausentes) +
            "\nEl contenedor las ha perdido. No se escribe en el Sheet.")

    dias = next((int(a) for a in sys.argv[1:] if a.isdigit()), 60)
    try:
        filas = construir(dias)
    except RuntimeError as err:
        # Sin Brevo no hay clics que cruzar: se avisa y se deja la cola como
        # está, en vez de vaciar la pestaña del equipo.
        raise SystemExit("COLA NO ACTUALIZADA · %s" % err)
    for f in filas[:28]:
        print(" | ".join(str(x) for x in f))
    print("\n(%d oportunidades en la cola)" % (len(filas) - 4))
    if "--sheet" in sys.argv:
        subir(filas, "Cola comercial")

#!/usr/bin/env python3
"""Máquina nueva en el stock → aviso al equipo con los leads a los que encaja.

Pedido por Maikel (09/09): "cuando entre una máquina nueva que nos avise de los
leads que nos hayan pedido esa máquina o les encaje".

Fuente del stock: el Sheet «Stock Outreach PANEL» de David (una fila por
máquina). Fuente de la demanda: la pestaña «Cola comercial» del Sheet de mando
(todos los leads con categoría, presupuesto y qué pidieron).

Cómo decide que una máquina "encaja" con un lead:
  · mención directa: el lead pidió esa marca/modelo o esa familia por su nombre
  · misma categoría (plataformas, miniexcavadoras, telescópicas, carretillas…)
    y presupuesto compatible (sin presupuesto, o entre el 60 % y el 150 % del
    precio de la máquina)

Estado en data/stock_visto.json: la primera ejecución solo guarda lo que hay.
Después, cada máquina nueva dispara un email al equipo (Brevo transaccional)
con la lista de leads, teléfono, canal, etapa y propietario, y enlace al CRM.

Uso:
    python3 scripts/aviso_stock_leads.py            # detecta nuevas y avisa
    python3 scripts/aviso_stock_leads.py --todo     # cruza TODO el stock (no envía)
    PRUEBA=1 ...                                    # no envía, solo imprime
"""
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panel_horario import SHEET_ID, sheets, token_google  # noqa: E402
from informe_respuestas import DESTINATARIOS, brevo  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHEET_STOCK = "1mCZtAe95o2va0ofw8Ts_e8ei3gv-QK5_CBr7moZ_hDE"
ESTADO = os.path.join(RAIZ, "data", "stock_visto.json")
CRM_URL = "https://ocasion.equipzilla.com/crm/"
PRUEBA = os.environ.get("PRUEBA") == "1"

CATEGORIAS = [
    (r"telesc|manipulador", "Telescópicas"),
    (r"tijera|plataforma|articulad|brazo|elevador|cami[oó]n plataforma", "Plataformas de elevación"),
    (r"mini ?exc|miniexc|kubota|develon|doosan dx ?[23]\d\b", "Miniexcavadoras"),
    (r"excavadora|giratoria|retro", "Excavadoras"),
    (r"carretilla|transpaleta|apilador", "Carretillas"),
    (r"pala|cargadora|bobcat|minicargadora", "Palas y minicargadoras"),
    (r"dumper", "Dumpers"),
    (r"generador|grupo electr", "Generadores"),
    (r"caseta|contenedor|aseo|m[oó]dulo", "Casetas y contenedores"),
]
MARCAS = {"genie", "haulotte", "manitou", "jlg", "kubota", "doosan", "develon", "yale", "toyota", "still",
          "clark", "hyster", "jungheinrich", "linde", "bobcat", "caterpillar", "cat", "jcb", "merlo", "socage",
          "iveco", "multitel", "wacker", "takeuchi", "hitachi", "komatsu", "volvo", "liebherr", "skyjack"}
# palabras de familia que, si el lead las escribió, cuentan como "lo pidió"
FAMILIA = {
    "Telescópicas": r"telesc|manipulador",
    "Plataformas de elevación": r"tijera|plataforma|articulad|brazo articulado|pemp",
    "Miniexcavadoras": r"mini ?exc|miniexc|mini retro",
    "Excavadoras": r"excavadora|giratoria|retroexc|retro ",
    "Carretillas": r"carretilla|toro|transpaleta",
    "Palas y minicargadoras": r"pala|minicargadora|bobcat",
    "Dumpers": r"dumper",
    "Generadores": r"generador|grupo electr",
    "Casetas y contenedores": r"caseta|contenedor|aseo",
}


def categoria(*textos):
    t = " ".join(x or "" for x in textos).lower()
    for patron, cat in CATEGORIAS:
        if re.search(patron, t):
            return cat
    return "Otros"


def precio_num(v):
    t = re.sub(r"[€\s]", "", str(v or ""))
    if not t:
        return None
    t = re.sub(r"\.(?=\d{3})", "", t).replace(",", ".")
    try:
        return int(round(float(t)))
    except ValueError:
        return None


def leer(tk, sheet_id, rng):
    r = sheets("%s/values/%s" % (sheet_id, urllib.parse.quote(rng)), cab={"Authorization": "Bearer " + tk})
    if "_error" in r:
        raise RuntimeError("Sheets %s: %s" % (r["_error"], r.get("_body", "")[:120]))
    return r.get("values", [])


def stock(tk):
    meta = sheets("%s?fields=sheets.properties" % SHEET_STOCK, cab={"Authorization": "Bearer " + tk})
    tab = meta.get("sheets", [{}])[0].get("properties", {}).get("title", "Untitled")
    out = []
    for i, f in enumerate(leer(tk, SHEET_STOCK, "%s!A2:O400" % tab), start=2):
        f += [""] * (15 - len(f))
        ref, salida, familia, sub, maquina, marca, anio, cap, horas, precio = [x.strip() for x in f[:10]]
        if not maquina and not sub:
            continue
        titulo = " ".join(x for x in (marca, maquina) if x)
        clave = ref or "|".join((titulo.lower(), anio, str(precio_num(precio) or "")))
        out.append(dict(fila=i, clave=clave, ref=ref, salida=salida, familia=familia, sub=sub, titulo=titulo,
                        marca=marca, modelo=maquina, anio=anio, capacidad=cap, horas=horas,
                        precio=precio_num(precio), precio_txt=precio,
                        categoria=categoria(familia, sub, maquina, marca)))
    return out


def leads(tk):
    filas = leer(tk, SHEET_ID, "Cola comercial!A1:X600")
    i_cab = next((i for i, f in enumerate(filas) if f and f[0] == "Score"), None)
    if i_cab is None:
        return []
    cab = filas[i_cab]
    out = []
    for f in filas[i_cab + 1:]:
        if not f or not f[0]:
            continue
        d = {cab[j]: (f[j] if j < len(f) else "") for j in range(len(cab))}
        if "FUERA DE ICP" in d.get("Prioridad", ""):
            continue
        pres = precio_num(re.sub(r"hasta|€", "", d.get("Presupuesto / valor", "")))
        out.append(dict(nombre=d.get("Nombre", ""), empresa=d.get("Empresa", ""), tel=d.get("Teléfono", ""),
                        email=d.get("Email", ""), canal=d.get("Canal de entrada", ""), etapa=d.get("Etapa CRM", ""),
                        owner=d.get("Propietario", ""), prioridad=d.get("Prioridad", ""),
                        categoria=d.get("Categoría", ""), pide=d.get("Qué pide / qué miró", ""),
                        encaja=d.get("Qué tenemos que encaja [ref]", ""), presupuesto=pres,
                        score=int(re.sub(r"\D", "", d.get("Score", "0") or "0") or 0)))
    return out


def encaje(m, l):
    """Devuelve el motivo si la máquina encaja con el lead, si no ''."""
    # Solo lo que el lead pidió/miró: NO nuestras sugerencias ("encaja"), que
    # nombran marcas del stock y darían falsos positivos.
    texto = " ".join((l["pide"], l["categoria"])).lower()
    modelo = (m["modelo"] or "").lower().strip()
    marca = (m["marca"] or "").lower().strip()
    if modelo in MARCAS:                  # fila con solo la marca: no es un modelo
        marca, modelo = modelo, ""
    if modelo and len(modelo) >= 4 and re.search(r"\d", modelo) and modelo in texto:
        return "pidió este modelo (%s)" % m["modelo"]
    fam = FAMILIA.get(m["categoria"])
    if marca and fam and re.search(r"\b" + re.escape(marca) + r"\b", texto) and re.search(fam, texto):
        return "pidió %s de esta familia" % marca.title()
    misma_cat = (l["categoria"] == m["categoria"]) or bool(re.search(FAMILIA.get(m["categoria"], r"$^"), texto))
    if not misma_cat or m["categoria"] == "Otros":
        return ""
    p, pr = l["presupuesto"], m["precio"]
    if p and pr and not (0.6 * pr <= p <= 1.5 * pr):
        return ""
    return "misma categoría" + (" · presupuesto %s €" % format(p, ",d").replace(",", ".") if p else "")


def cruzar(maquinas, todos):
    res = []
    for m in maquinas:
        hits = []
        for l in todos:
            por = encaje(m, l)
            if por:
                hits.append((l, por))
        hits.sort(key=lambda x: (-("pidió" in x[1]), -x[0]["score"]))
        res.append((m, hits))
    return res


def email_html(cruce):
    partes = ["<div style='font-family:Arial,sans-serif;font-size:14px;color:#14181C'>",
              "<h2 style='margin:0 0 6px'>Máquinas nuevas en stock · leads que encajan</h2>",
              "<p style='color:#46565A;margin:0 0 16px'>Generado %s · <a href='%s'>abrir el CRM</a></p>"
              % (dt.datetime.now().strftime("%d/%m %H:%M"), CRM_URL)]
    for m, hits in cruce:
        partes.append("<h3 style='margin:18px 0 4px'>%s · %s%s</h3>" % (
            html.escape(m["titulo"]), html.escape(m["sub"] or m["familia"]),
            " · " + html.escape(m["precio_txt"]) if m["precio_txt"] else ""))
        partes.append("<div style='color:#46565A;font-size:13px;margin-bottom:6px'>%s</div>" % html.escape(
            " · ".join(x for x in ("Año " + m["anio"] if m["anio"] else "", m["capacidad"],
                                    (m["horas"] + " h") if m["horas"] and m["horas"] != "-" else "",
                                    "salida " + m["salida"] if m["salida"] else "") if x)))
        if not hits:
            partes.append("<p style='color:#7C8D90;margin:0'>Ningún lead de la cola encaja todavía.</p>")
            continue
        partes.append("<table style='border-collapse:collapse;font-size:13px'><tr style='background:#EEF3F3'>"
                      "<th style='padding:6px 8px;text-align:left'>Lead</th><th style='padding:6px 8px;text-align:left'>Teléfono</th>"
                      "<th style='padding:6px 8px;text-align:left'>Por qué</th><th style='padding:6px 8px;text-align:left'>Canal · etapa · lleva</th></tr>")
        for l, por in hits[:12]:
            quien = l["nombre"] if l["nombre"] not in ("", "—") else l["empresa"]
            if l["empresa"] not in ("", "—") and quien != l["empresa"]:
                quien += " · " + l["empresa"]
            partes.append("<tr><td style='padding:6px 8px;border-top:1px solid #E2E8E8'><b>%s</b><br><span style='color:#7C8D90'>%s</span></td>"
                          "<td style='padding:6px 8px;border-top:1px solid #E2E8E8'>%s</td>"
                          "<td style='padding:6px 8px;border-top:1px solid #E2E8E8'>%s</td>"
                          "<td style='padding:6px 8px;border-top:1px solid #E2E8E8'>%s · %s · %s</td></tr>" % (
                              html.escape(quien), html.escape(l["prioridad"]), html.escape(l["tel"]), html.escape(por),
                              html.escape(l["canal"]), html.escape(l["etapa"]), html.escape(l["owner"])))
        partes.append("</table>")
        if len(hits) > 12:
            partes.append("<p style='color:#7C8D90'>… y %d más en el CRM.</p>" % (len(hits) - 12))
    partes.append("</div>")
    return "".join(partes)


def enviar(cruce):
    n = sum(1 for _, h in cruce if h)
    asunto = "Stock nuevo: %d máquina%s · %d con leads que encajan" % (len(cruce), "s" if len(cruce) != 1 else "", n)
    cuerpo = {"sender": {"id": 10}, "to": [{"email": e} for e in DESTINATARIOS],
              "replyTo": {"email": "clientes@equipzilla.com"}, "subject": asunto, "htmlContent": email_html(cruce)}
    if PRUEBA:
        print("[PRUEBA] no se envía ·", asunto)
        return
    r = brevo("/smtp/email", "POST", cuerpo)
    print("email enviado a %d ·" % len(DESTINATARIOS), asunto, "·", r.get("messageId", r))


def main():
    todo = "--todo" in sys.argv
    tk = token_google(["https://www.googleapis.com/auth/spreadsheets.readonly"])
    maquinas = stock(tk)
    visto = set()
    if os.path.exists(ESTADO):
        visto = set(json.load(open(ESTADO)).get("claves", []))
    nuevas = [m for m in maquinas if m["clave"] not in visto]
    print("stock: %d máquinas · vistas antes: %d · nuevas: %d" % (len(maquinas), len(visto), len(nuevas)))
    objetivo = maquinas if todo else nuevas
    if not visto and not todo:
        print("primera ejecución: guardo el estado, no aviso de lo que ya había")
    elif objetivo:
        cruce = cruzar(objetivo, leads(tk))
        for m, hits in cruce:
            print("· %s (%s) → %d leads" % (m["titulo"], m["categoria"], len(hits)))
            for l, por in hits[:5]:
                print("     %-32s %-16s %s" % ((l["nombre"] if l["nombre"] != "—" else l["empresa"])[:32], l["tel"][:16], por))
        if not todo:
            enviar(cruce)
    else:
        print("sin máquinas nuevas")
    if not todo or not visto:
        os.makedirs(os.path.dirname(ESTADO), exist_ok=True)
        json.dump({"claves": sorted({m["clave"] for m in maquinas}), "actualizado": dt.datetime.now().isoformat()},
                  open(ESTADO, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

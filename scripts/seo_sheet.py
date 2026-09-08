#!/usr/bin/env python3
"""Sheet de mando SEO, calcado del modelo de Qualivo (5 pestañas):

  Keywords & Contenido   lo publicado: keyword · URL · posición real · prioridad
  GSC en vivo            lo que ya posiciona en Google, con CÓMO ATACAR cada una
  Oportunidades          keywords investigadas sin contenido, por prioridad
  Visibilidad IA (LLM)   prompts de prueba para ver si ChatGPT/Perplexity nos citan
  Keyword Research       las 354 con ¿tenemos artículo? y acción

Fuentes: seo/keywords_master.csv (DinoRank), Search Console 90 días por
consulta, y las guías publicadas en quiz/guias/. Nada escrito a mano.
"""
import csv, os, re, sys, urllib.parse, unicodedata, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panel_horario import sheets, token_google
from gsc_metricas import consulta

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(RAIZ, "seo", "keywords_master.csv")
GUIAS = os.path.join(RAIZ, "quiz", "guias")
SHEET = "14pB8ZJUPdmhGvDX1Y3hfUk0-mfmdsYCvJOvQZ_GqWOw"
BASE = "https://ocasion.equipzilla.com/guias/"
TINTA = {"red": 0.09, "green": 0.20, "blue": 0.23}; BLANCO = {"red": 1, "green": 1, "blue": 1}
SUAVE = {"red": 0.93, "green": 0.95, "blue": 0.96}
VACIAS = {"de", "la", "el", "en", "y", "un", "una", "para", "con", "segunda", "mano", "usada", "usado", "precio", "precios"}


def norm(t):
    t = unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]", " ", t).split()


def guias():
    out = {}
    for f in sorted(os.listdir(GUIAS)):
        if not f.endswith(".html") or f == "index.html":
            continue
        t = open(os.path.join(GUIAS, f), encoding="utf-8").read()
        tit = re.search(r"<title>(.*?)</title>", t, re.S)
        titulo = re.sub(r"\s*[|·]\s*Equipzilla.*$", "", tit.group(1)).strip() if tit else f
        out[f] = dict(titulo=titulo, bolsa=set(norm(f[:-5].replace("-", " ") + " " + titulo)))
    return out


def articulo(kw, gs):
    w = set(norm(kw)) - VACIAS
    mejor, punt = "", 0
    for f, g in gs.items():
        n = len(w & g["bolsa"])
        # todas las palabras con sentido de la keyword han de estar en la guía;
        # si la keyword solo tiene una ("excavadora de segunda mano"), vale una
        if n == len(w) and n >= 1 and n > punt:
            mejor, punt = f, n
    return mejor


def intencion(kw, csv_int=""):
    if re.search(r"alquil", kw, re.I):
        return "Alquiler (no es nuestra)"
    if re.search(r"segunda mano|ocasi[oó]n|usad[ao]|comprar|venta|precio|barat", kw, re.I):
        return "Comercial"
    return csv_int or "Informacional"


def como_atacar(pos, impr, art, kw):
    inten = intencion(kw)
    if inten.startswith("Alquiler"):
        return "Ignorar: intención de alquiler, no de compra"
    if pos <= 3:
        return "Mantener: enlazarla desde otras guías y añadir FAQ"
    if pos <= 10:
        return ("Reforzar la guía: ampliar respuesta rápida, tabla de precios, 3 enlaces internos"
                if art else "🎯 Crear guía: ya estamos en top 10 sin contenido propio")
    if pos <= 20:
        return ("Ampliar la guía y enlazarla desde el índice y 2 guías más"
                if art else "🎯 Crear guía: posición 11-20 es la más rentable de atacar")
    return ("Revisar el título y la meta: hay impresiones pero no clic" if impr >= 50
            else "Observar")


def main():
    filas = list(csv.DictReader(open(CSV, encoding="utf-8")))
    gs = guias()
    gsc = {}
    for r in consulta(90, ("query",), 2000):
        gsc[" ".join(norm(r["keys"][0]))] = r
    hoy = dt.date.today().strftime("%d/%m/%Y")

    # ── 1. Keywords & Contenido: una fila por guía publicada
    kc = [["Keyword / Tema", "Categoría", "Intención", "URL del artículo", "Estado",
           "Volumen (DinoRank)", "Pos. media (GSC 90d)", "Clics (90d)", "Impresiones (90d)",
           "Prioridad", "Notas"]]
    por_guia = {}
    for f in filas:
        a = articulo(f["Keyword / Tema"], gs)
        if a:
            por_guia.setdefault(a, []).append(f)
    for slug, g in gs.items():
        kws = por_guia.get(slug, [])
        principal = max(kws, key=lambda x: int(float(x.get("Volumen grupo") or 0)), default=None)
        kw = principal["Keyword / Tema"] if principal else g["titulo"]
        vol = int(float(principal.get("Volumen grupo") or principal.get("Volumen (DinoRank)") or 0)) if principal else ""
        r = gsc.get(" ".join(norm(kw)))
        pos = round(r["position"], 1) if r else ""
        prio = "🔴 Alta" if isinstance(vol, int) and vol >= 500 else "🟠 Media" if isinstance(vol, int) and vol >= 100 else "🟢 Normal"
        notas = ("kw: " + " · ".join(x["Keyword / Tema"] for x in kws[:3]) if kws else "sin keyword del research asociada") + \
                ("" if r else " · sin datos GSC aún")
        kc.append([kw, principal.get("Categoría", "") if principal else "", intencion(kw, principal.get("Intención", "") if principal else ""),
                   BASE + slug, "Publicado", vol, pos, int(r["clicks"]) if r else "", int(r["impressions"]) if r else "", prio, notas])

    # ── 2. GSC en vivo: lo que ya posiciona + cómo atacar
    gv = [["Consulta (Search Console 90d)", "Clics", "Impresiones", "CTR %", "Pos. media",
           "Intención", "¿Tenemos guía?", "Cómo atacarla"]]
    for k, r in sorted(gsc.items(), key=lambda x: -x[1]["impressions"])[:150]:
        kw = r["keys"][0]
        a = articulo(kw, gs)
        gv.append([kw, int(r["clicks"]), int(r["impressions"]), round(100 * r["ctr"], 1), round(r["position"], 1),
                   intencion(kw), (BASE + a) if a else "No", como_atacar(r["position"], r["impressions"], a, kw)])

    # ── 3. Oportunidades: investigadas sin contenido
    op = [["Keyword oportunidad", "Volumen/mes", "Competencia", "Intención", "Pos. actual (si la hay)", "Prioridad", "Estado"]]
    cola = []
    for f in filas:
        kw = f["Keyword / Tema"]
        if articulo(kw, gs):
            continue
        inten = intencion(kw, f.get("Intención", ""))
        if inten.startswith("Alquiler"):
            continue
        vol = int(float(f.get("Volumen grupo") or f.get("Volumen (DinoRank)") or 0))
        r = gsc.get(" ".join(norm(kw)))
        pos = round(r["position"], 1) if r else ""
        peso = vol * (2 if inten == "Comercial" else 1) * (3 if pos and 4 <= pos <= 20 else 1)
        cola.append((peso, [kw, vol, f.get("Competencia", ""), inten, pos,
                            "🔴" if peso >= 3000 else "🟠" if peso >= 600 else "🟢", "Pendiente"]))
    cola.sort(key=lambda x: -x[0])
    op += [c[1] for c in cola]

    # ── 4. Visibilidad IA
    ia = [["Prompt de prueba (ChatGPT / Perplexity / Gemini)", "¿Nos cita? (sí/no)", "Fecha check", "Notas"]]
    for p in ["¿Dónde comprar una miniexcavadora de segunda mano en España?",
              "¿Cuánto cuesta una carretilla elevadora de segunda mano?",
              "¿Qué revisar antes de comprar una excavadora usada?",
              "¿Cuántas horas son muchas para una máquina de construcción usada?",
              "¿Plataforma de tijera o articulada para trabajar a 12 metros?",
              "¿Dónde comprar una caseta de obra de segunda mano?",
              "¿Cuánto vale un manipulador telescópico usado?",
              "¿Comprar o alquilar maquinaria de construcción?"]:
        ia.append([p, "", "", ""])

    # ── 5. Keyword Research: las 354
    kr = [["Keyword", "Volumen/mes", "Competencia", "Intención", "¿Tenemos artículo?", "URL nuestra", "Acción"]]
    for f in sorted(filas, key=lambda x: -int(float(x.get("Volumen grupo") or 0))):
        kw = f["Keyword / Tema"]; a = articulo(kw, gs); inten = intencion(kw, f.get("Intención", ""))
        vol = int(float(f.get("Volumen grupo") or f.get("Volumen (DinoRank)") or 0))
        acc = ("Fuera: alquiler" if inten.startswith("Alquiler") else "✓ Publicado — enlazar y reforzar" if a
               else "🎯 Crear artículo" if vol >= 100 else "Cola")
        kr.append([kw, vol, f.get("Competencia", ""), inten, "Sí" if a else "No", (BASE + a) if a else "", acc])

    # ── ESCRITURA
    cab = {"Authorization": "Bearer " + token_google(["https://www.googleapis.com/auth/spreadsheets"]),
           "Content-Type": "application/json"}
    tabs = [("Keywords & Contenido", kc), ("GSC en vivo", gv), ("Oportunidades", op),
            ("Visibilidad IA (LLM)", ia), ("Keyword Research", kr)]
    meta = sheets("%s?fields=sheets.properties" % SHEET, cab=cab)
    hojas = {x["properties"]["title"]: x["properties"]["sheetId"] for x in meta.get("sheets", [])}
    reqs = []
    for i, (t, _) in enumerate(tabs):
        if t not in hojas:
            reqs.append({"addSheet": {"properties": {"title": t, "index": i}}})
    if reqs:
        sheets("%s:batchUpdate" % SHEET, "POST", {"requests": reqs}, cab)
        meta = sheets("%s?fields=sheets.properties" % SHEET, cab=cab)
        hojas = {x["properties"]["title"]: x["properties"]["sheetId"] for x in meta.get("sheets", [])}
    fmt = []
    for t, F in tabs:
        sid = hojas[t]; ancho = max(len(f) for f in F)
        sheets("%s/values/%s:clear" % (SHEET, urllib.parse.quote("%s!A1:Z3000" % t)), "POST", {}, cab)
        r = sheets("%s/values/%s?valueInputOption=RAW" % (SHEET, urllib.parse.quote("%s!A1" % t)), "PUT", {"values": F}, cab)
        if "_error" in r:
            raise SystemExit((t, r))
        fmt += [
            {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1},
                            "cell": {"userEnteredFormat": {"backgroundColor": TINTA, "textFormat": {"bold": True, "foregroundColor": BLANCO}, "wrapStrategy": "WRAP"}},
                            "fields": "userEnteredFormat(backgroundColor,textFormat,wrapStrategy)"}},
            {"updateSheetProperties": {"properties": {"sheetId": sid, "gridProperties": {"frozenRowCount": 1}}, "fields": "gridProperties.frozenRowCount"}},
            {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 300}, "fields": "pixelSize"}},
            {"setBasicFilter": {"filter": {"range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": len(F), "startColumnIndex": 0, "endColumnIndex": ancho}}}},
        ]
        for c in range(1, ancho):
            fmt.append({"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": c, "endIndex": c + 1},
                        "properties": {"pixelSize": 300 if c == ancho - 1 and t in ("GSC en vivo", "Keywords & Contenido") else 120}, "fields": "pixelSize"}})
    # pestañas que ya no forman parte del modelo
    for t, sid in hojas.items():
        if t not in dict(tabs):
            fmt.append({"deleteSheet": {"sheetId": sid}})
    sheets("%s:batchUpdate" % SHEET, "POST", {"requests": fmt}, cab)
    print("Sheet SEO · %d guías publicadas · %d consultas en GSC · %d oportunidades sin contenido · %d keywords"
          % (len(kc) - 1, len(gv) - 1, len(op) - 1, len(kr) - 1))
    print("https://docs.google.com/spreadsheets/d/%s/edit" % SHEET)
    print("\nTOP 8 OPORTUNIDADES (redactar en este orden):")
    for c in cola[:8]:
        k = c[1]; print("   %s vol %5s · pos %5s · %s" % (k[5], k[1], k[4] or "—", k[0]))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Sheet de mando SEO: keyword · volumen · posición real · artículo · prioridad.

Cruza el research de DinoRank (seo/keywords_master.csv) con Search Console
(90 días, por consulta) y con las guías ya publicadas en quiz/guias/. Así cada
keyword dice tres cosas que el CSV no decía: en qué posición estamos, cuántas
impresiones tiene de verdad y si ya hay artículo que la trabaje.

Prioridad = volumen × intención × (si ya rankeamos 4-20, más aún: es un
quick win). Lo que no rankea ni tiene artículo es la cola de redacción.
"""
import csv, os, re, sys, urllib.parse, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panel_horario import sheets, token_google
from gsc_metricas import consulta

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(RAIZ, "seo", "keywords_master.csv")
GUIAS = os.path.join(RAIZ, "quiz", "guias")
SHEET = "14pB8ZJUPdmhGvDX1Y3hfUk0-mfmdsYCvJOvQZ_GqWOw"
BASE = "https://equipzilla-quiz.vercel.app/guias/"
TINTA = {"red": 0.09, "green": 0.20, "blue": 0.23}; BLANCO = {"red": 1, "green": 1, "blue": 1}


def norm(t):
    t = unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]", " ", t).split()


def guias_publicadas():
    out = {}
    for f in os.listdir(GUIAS):
        if not f.endswith(".html") or f == "index.html":
            continue
        t = open(os.path.join(GUIAS, f), encoding="utf-8").read()
        tit = re.search(r"<title>(.*?)</title>", t, re.S)
        out[f] = set(norm(f[:-5].replace("-", " ") + " " + (tit.group(1) if tit else "")))
    return out


def articulo_para(kw, guias):
    w = set(norm(kw)) - {"de", "la", "el", "en", "y", "segunda", "mano", "precio", "usada", "usado"}
    # Exigir que TODAS las palabras con sentido de la keyword estén en el slug
    # o el título de la guía (y al menos dos): "mini excavadora" encaja con la
    # guía de miniexcavadora; "excavadora" a secas no encaja con todo.
    mejor, punt = "", 0
    for f, bolsa in guias.items():
        n = len(w & bolsa)
        if n >= 2 and n == len(w) and n > punt:
            mejor, punt = f, n
    return mejor


def main():
    filas = list(csv.DictReader(open(CSV, encoding="utf-8")))
    gsc = {}
    for r in consulta(90, ("query",), 2000):
        gsc[" ".join(norm(r["keys"][0]))] = r
    guias = guias_publicadas()
    out = [["EQUIPZILLA · SEO · MANDO DE KEYWORDS", "", "", "", "", "", "",
            "research DinoRank + Search Console 90 días + guías publicadas"],
           ["Keyword", "Categoría", "Intención", "Volumen", "Posición real",
            "Impresiones 90d", "Clics 90d", "Artículo publicado", "Prioridad", "Qué hacer"]]
    n_rank = n_art = 0
    for f in filas:
        kw = f["Keyword / Tema"]
        vol = int(float(f.get("Volumen grupo") or f.get("Volumen (DinoRank)") or 0))
        g = gsc.get(" ".join(norm(kw)))
        pos = round(g["position"], 1) if g else ""
        impr = int(g["impressions"]) if g else ""
        cl = int(g["clicks"]) if g else ""
        art = articulo_para(kw, guias)
        intent = f.get("Intención", "")
        peso = vol * (2 if "Comercial" in intent else 1)
        if pos and 4 <= pos <= 20:
            peso *= 3; accion = "QUICK WIN: reforzar el artículo y enlazarlo"
        elif pos and pos <= 3:
            accion = "Mantener"
        elif art:
            accion = "Publicado, aún sin ranking: esperar/enlazar"
        else:
            accion = "Redactar" if vol >= 200 else "Cola"
        prio = "🔴 Alta" if peso >= 6000 else "🟠 Media" if peso >= 1500 else "🟢 Baja"
        if pos: n_rank += 1
        if art: n_art += 1
        out.append([kw, f.get("Categoría", ""), intent, vol, pos, impr, cl,
                    (BASE + art) if art else "", prio, accion])
    out.sort(key=lambda r: (0 if r[8].startswith("🔴") else 1 if r[8].startswith("🟠") else 2,
                            -(r[3] if isinstance(r[3], int) else 0)) if r[0] not in
             ("Keyword", "EQUIPZILLA · SEO · MANDO DE KEYWORDS") else (-1, 0))
    cab = {"Authorization": "Bearer " + token_google(["https://www.googleapis.com/auth/spreadsheets"]),
           "Content-Type": "application/json"}
    meta = sheets("%s?fields=sheets.properties" % SHEET, cab=cab)
    sid = meta["sheets"][0]["properties"]["sheetId"]
    sheets("%s:batchUpdate" % SHEET, "POST", {"requests": [
        {"updateSheetProperties": {"properties": {"sheetId": sid, "title": "Keywords"},
                                   "fields": "title"}}]}, cab)
    sheets("%s/values/%s:clear" % (SHEET, urllib.parse.quote("Keywords!A1:L2000")), "POST", {}, cab)
    r = sheets("%s/values/%s?valueInputOption=RAW" % (SHEET, urllib.parse.quote("Keywords!A1")),
               "PUT", {"values": out}, cab)
    if "_error" in r:
        raise SystemExit(r)
    sheets("%s:batchUpdate" % SHEET, "POST", {"requests": [
        {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 2},
                        "cell": {"userEnteredFormat": {"backgroundColor": TINTA,
                                 "textFormat": {"bold": True, "foregroundColor": BLANCO}}},
                        "fields": "userEnteredFormat(backgroundColor,textFormat)"}},
        {"updateSheetProperties": {"properties": {"sheetId": sid, "gridProperties":
            {"frozenRowCount": 2}}, "fields": "gridProperties.frozenRowCount"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS",
            "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 300}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS",
            "startIndex": 7, "endIndex": 8}, "properties": {"pixelSize": 380}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS",
            "startIndex": 9, "endIndex": 10}, "properties": {"pixelSize": 300}, "fields": "pixelSize"}},
        {"setBasicFilter": {"filter": {"range": {"sheetId": sid, "startRowIndex": 1,
                                                 "endRowIndex": len(out), "startColumnIndex": 0,
                                                 "endColumnIndex": 10}}}}]}, cab)
    print("%d keywords · %d ya rankean en GSC · %d con artículo publicado" % (len(filas), n_rank, n_art))
    print("https://docs.google.com/spreadsheets/d/%s/edit" % SHEET)
    print("\nQUICK WINS sin artículo (redactar primero):")
    for r_ in out[2:]:
        if r_[9].startswith("QUICK WIN") and not r_[7]:
            print("   pos %5s · %6s impr · vol %6s · %s" % (r_[4], r_[5], r_[3], r_[0]))
    print("\nALTA prioridad sin ranking ni artículo:")
    k = 0
    for r_ in out[2:]:
        if r_[8].startswith("🔴") and not r_[4] and not r_[7] and k < 10:
            print("   vol %6s · %s" % (r_[3], r_[0])); k += 1


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Genera el CSV de importacion para Google Ads Editor y valida limites de caracteres."""
import csv

FINAL_URL = "https://equipzilla.com/compra/maquinaria/ocasion/maquinaria-construccion-segunda-mano"
CAMPAIGN = "ES | Compra | Maquinaria Construccion 2a Mano"
DAILY_BUDGET = "50"
PATH1 = "Ocasion"
PATH2 = "Maquinaria"

# ---- Grupos de anuncios: keywords (texto, tipo) ----
AD_GROUPS = {
    "Excavadoras 2a mano": {
        "keywords": [
            ("excavadora segunda mano", "Exact"),
            ("excavadora ocasion", "Exact"),
            ("comprar excavadora usada", "Exact"),
            ("excavadora de segunda mano", "Phrase"),
            ("excavadora oruga segunda mano", "Phrase"),
            ("excavadora usada precio", "Phrase"),
            ("excavadora giratoria ocasion", "Phrase"),
        ],
        "headlines": [
            "Excavadoras 2a Mano",
            "Excavadoras de Ocasion",
            "Excavadoras Revisadas",
            "Excavadora Oruga Usada",
            "Doosan Kubota Develon",
            "Equipos Listos p/ Obra",
            "Excavadora al Mejor Precio",
            "Asesoramiento de Compra",
            "Envio a Toda Espana",
            "Compra con Confianza",
            "Stock Disponible Ya",
            "Pide Info Sin Compromiso",
            "Financiacion a Consultar",
            "Equipzilla Maquinaria",
            "Llama: 911 238 750",
        ],
        "descriptions": [
            "Excavadoras de segunda mano revisadas y operativas. Pide informacion sin compromiso.",
            "Oruga o ruedas, marcas Doosan, Kubota y Develon. Asesoramiento experto de compra.",
            "Encuentra tu excavadora al mejor precio. Equipos seleccionados para rendir en obra.",
            "Solicita tu presupuesto hoy. Envio a toda Espana y atencion personalizada.",
        ],
    },
    "Miniexcavadoras 2a mano": {
        "keywords": [
            ("miniexcavadora segunda mano", "Exact"),
            ("mini excavadora ocasion", "Exact"),
            ("comprar miniexcavadora usada", "Exact"),
            ("miniexcavadora kubota segunda mano", "Phrase"),
            ("mini excavadora de segunda mano", "Phrase"),
            ("miniexcavadora precio ocasion", "Phrase"),
        ],
        "headlines": [
            "Miniexcavadoras 2a Mano",
            "Miniexcavadora Ocasion",
            "Mini Excavadora Usada",
            "Kubota Desde 13.900 EUR",
            "Compactas y Revisadas",
            "Ideal Obra y Jardin",
            "Equipos Listos p/ Obra",
            "Asesoramiento de Compra",
            "Envio a Toda Espana",
            "Compra con Confianza",
            "Stock Disponible Ya",
            "Pide Info Sin Compromiso",
            "Mejor Precio Garantizado",
            "Equipzilla Maquinaria",
            "Llama: 911 238 750",
        ],
        "descriptions": [
            "Miniexcavadoras de segunda mano revisadas. Kubota y mas marcas desde 13.900 EUR.",
            "Compactas, versatiles y listas para trabajar. Pide informacion sin compromiso.",
            "Encuentra tu miniexcavadora al mejor precio. Asesoramiento experto de compra.",
            "Solicita presupuesto hoy. Envio a toda Espana y atencion personalizada.",
        ],
    },
    "Minicargadoras 2a mano": {
        "keywords": [
            ("minicargadora segunda mano", "Exact"),
            ("minicargadora ocasion", "Exact"),
            ("cargadora compacta usada", "Phrase"),
            ("comprar minicargadora usada", "Phrase"),
            ("bobcat segunda mano", "Phrase"),
        ],
        "headlines": [
            "Minicargadoras 2a Mano",
            "Minicargadora Ocasion",
            "Cargadora Compacta Usada",
            "Equipos Revisados",
            "Listas para Trabajar",
            "Doosan Kubota Develon",
            "Equipos Listos p/ Obra",
            "Asesoramiento de Compra",
            "Envio a Toda Espana",
            "Compra con Confianza",
            "Stock Disponible Ya",
            "Pide Info Sin Compromiso",
            "Mejor Precio Garantizado",
            "Equipzilla Maquinaria",
            "Llama: 911 238 750",
        ],
        "descriptions": [
            "Minicargadoras de segunda mano revisadas y operativas. Pide info sin compromiso.",
            "Cargadoras compactas listas para trabajar. Asesoramiento experto de compra.",
            "Encuentra tu minicargadora al mejor precio. Equipos seleccionados para la obra.",
            "Solicita presupuesto hoy. Envio a toda Espana y atencion personalizada.",
        ],
    },
    "Dumpers 2a mano": {
        "keywords": [
            ("dumper segunda mano", "Exact"),
            ("dumper ocasion", "Exact"),
            ("comprar dumper usado", "Exact"),
            ("dumper de obra usado", "Phrase"),
            ("dumper articulado segunda mano", "Phrase"),
        ],
        "headlines": [
            "Dumpers 2a Mano",
            "Dumper de Ocasion",
            "Dumper de Obra Usado",
            "Dumpers Revisados",
            "Articulados y Rigidos",
            "Listos para Trabajar",
            "Equipos Listos p/ Obra",
            "Asesoramiento de Compra",
            "Envio a Toda Espana",
            "Compra con Confianza",
            "Stock Disponible Ya",
            "Pide Info Sin Compromiso",
            "Mejor Precio Garantizado",
            "Equipzilla Maquinaria",
            "Llama: 911 238 750",
        ],
        "descriptions": [
            "Dumpers de obra de segunda mano revisados y operativos. Pide info sin compromiso.",
            "Articulados o rigidos, listos para trabajar. Asesoramiento experto de compra.",
            "Encuentra tu dumper al mejor precio. Equipos seleccionados para rendir en obra.",
            "Solicita presupuesto hoy. Envio a toda Espana y atencion personalizada.",
        ],
    },
    "Rodillos y compactadores 2a mano": {
        "keywords": [
            ("rodillo compactador segunda mano", "Exact"),
            ("rodillo compactador ocasion", "Exact"),
            ("compactadora usada", "Phrase"),
            ("rodillo tandem segunda mano", "Phrase"),
            ("comprar rodillo compactador usado", "Phrase"),
        ],
        "headlines": [
            "Rodillos 2a Mano",
            "Rodillo Compactador",
            "Compactadora Usada",
            "Rodillo Tandem Ocasion",
            "Rodillos Revisados",
            "Listos para Trabajar",
            "Equipos Listos p/ Obra",
            "Asesoramiento de Compra",
            "Envio a Toda Espana",
            "Compra con Confianza",
            "Stock Disponible Ya",
            "Pide Info Sin Compromiso",
            "Mejor Precio Garantizado",
            "Equipzilla Maquinaria",
            "Llama: 911 238 750",
        ],
        "descriptions": [
            "Rodillos compactadores de segunda mano revisados. Pide informacion sin compromiso.",
            "Tandem o mixtos, listos para trabajar. Asesoramiento experto de compra.",
            "Encuentra tu compactadora al mejor precio. Equipos seleccionados para la obra.",
            "Solicita presupuesto hoy. Envio a toda Espana y atencion personalizada.",
        ],
    },
    "Maquinaria construccion 2a mano (generico)": {
        "keywords": [
            ("maquinaria construccion segunda mano", "Phrase"),
            ("maquinaria de obra usada", "Phrase"),
            ("maquinaria pesada ocasion", "Phrase"),
            ("comprar maquinaria construccion usada", "Phrase"),
            ("maquinaria obra publica segunda mano", "Phrase"),
            ("maquinaria construccion ocasion", "Exact"),
        ],
        "headlines": [
            "Maquinaria 2a Mano",
            "Maquinaria de Obra Usada",
            "Maquinaria de Ocasion",
            "Equipos Revisados",
            "Desde 13.900 EUR",
            "Doosan Kubota Develon",
            "Excavadoras y Dumpers",
            "Asesoramiento de Compra",
            "Envio a Toda Espana",
            "Compra con Confianza",
            "Stock Disponible Ya",
            "Pide Info Sin Compromiso",
            "Mejor Precio Garantizado",
            "Equipzilla Maquinaria",
            "Llama: 911 238 750",
        ],
        "descriptions": [
            "Maquinaria de construccion de 2a mano revisada y operativa. Pide info sin compromiso.",
            "Excavadoras, dumpers, rodillos y mas. Marcas Doosan, Kubota y Develon.",
            "Encuentra la maquina ideal al mejor precio. Asesoramiento experto de compra.",
            "Equipos seleccionados para rendir en obra. Solicita tu presupuesto hoy mismo.",
        ],
    },
    "Marcas ocasion (Doosan Kubota Develon)": {
        "keywords": [
            ("excavadora doosan segunda mano", "Phrase"),
            ("kubota segunda mano", "Phrase"),
            ("develon ocasion", "Phrase"),
            ("doosan usada", "Phrase"),
            ("maquinaria kubota ocasion", "Phrase"),
        ],
        "headlines": [
            "Doosan de Ocasion",
            "Kubota Segunda Mano",
            "Develon Ocasion",
            "Maquinaria Doosan Usada",
            "Equipos Revisados",
            "Desde 13.900 EUR",
            "Excavadoras y Cargadoras",
            "Asesoramiento de Compra",
            "Envio a Toda Espana",
            "Compra con Confianza",
            "Stock Disponible Ya",
            "Pide Info Sin Compromiso",
            "Mejor Precio Garantizado",
            "Equipzilla Maquinaria",
            "Llama: 911 238 750",
        ],
        "descriptions": [
            "Doosan, Kubota y Develon de segunda mano revisadas. Pide info sin compromiso.",
            "Maquinaria de marca revisada y operativa. Asesoramiento experto de compra.",
            "Encuentra tu equipo de marca al mejor precio. Seleccionado para rendir en obra.",
            "Solicita presupuesto hoy. Envio a toda Espana y atencion personalizada.",
        ],
    },
}

NEGATIVES = [
    "alquiler", "alquilar", "renting", "leasing", "gratis", "gratuito",
    "curso", "cursos", "carnet", "carne", "formacion", "empleo", "trabajo",
    "juguete", "juguetes", "rc", "teledirigida", "radiocontrol", "escala",
    "gta", "simulador", "juego", "minecraft", "roblox", "lego", "playmobil",
    "pdf", "manual", "despiece", "wallpaper", "dibujo", "para colorear",
    "como se llama", "chatarra", "desguace",
]

SITELINKS = [
    ("Excavadoras 2a mano", "Oruga y ruedas revisadas", "Marcas Doosan y Develon"),
    ("Miniexcavadoras", "Compactas desde 13.900 EUR", "Kubota y mas marcas"),
    ("Dumpers de obra", "Articulados y rigidos", "Listos para trabajar"),
    ("Asesoramiento", "Te ayudamos a elegir", "Sin compromiso"),
]
CALLOUTS = [
    "Equipos revisados", "Envio a toda Espana", "Asesoramiento experto",
    "Marcas Doosan y Kubota", "Stock disponible", "Atencion personalizada",
]

def validate():
    ok = True
    for ag, data in AD_GROUPS.items():
        for h in data["headlines"]:
            if len(h) > 30:
                ok = False; print(f"[X] TITULAR >30 ({len(h)}) [{ag}]: {h}")
        for d in data["descriptions"]:
            if len(d) > 90:
                ok = False; print(f"[X] DESCRIP >90 ({len(d)}) [{ag}]: {d}")
        for kw, _ in data["keywords"]:
            if len(kw) > 80:
                ok = False; print(f"[X] KEYWORD >80 [{ag}]: {kw}")
    for p in (PATH1, PATH2):
        if len(p) > 15:
            ok = False; print(f"[X] PATH >15: {p}")
    for s in SITELINKS:
        if len(s[0]) > 25: ok=False; print(f"[X] SITELINK texto >25: {s[0]}")
        if len(s[1]) > 35: ok=False; print(f"[X] SITELINK desc1 >35: {s[1]}")
        if len(s[2]) > 35: ok=False; print(f"[X] SITELINK desc2 >35: {s[2]}")
    for c in CALLOUTS:
        if len(c) > 25: ok=False; print(f"[X] CALLOUT >25: {c}")
    return ok

def build_csv(path):
    # Cabecera compatible con Google Ads Editor (importacion CSV)
    cols = ["Campaign", "Campaign Daily Budget", "Ad Group", "Max CPC",
            "Keyword", "Match Type", "Ad type",
            "Final URL", "Path 1", "Path 2"] + \
           [f"Headline {i}" for i in range(1, 16)] + \
           [f"Description {i}" for i in range(1, 5)]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for ag, data in AD_GROUPS.items():
            # filas de keywords
            for kw, mt in data["keywords"]:
                row = [CAMPAIGN, DAILY_BUDGET, ag, "0.60", kw, mt, "", "", "", ""] + [""]*19
                w.writerow(row)
            # fila del anuncio RSA
            hs = data["headlines"] + [""]*(15-len(data["headlines"]))
            ds = data["descriptions"] + [""]*(4-len(data["descriptions"]))
            row = [CAMPAIGN, DAILY_BUDGET, ag, "0.60", "", "", "Responsive search ad",
                   FINAL_URL, PATH1, PATH2] + hs[:15] + ds[:4]
            w.writerow(row)

def build_negatives(path):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Campaign", "Keyword", "Match Type"])
        for n in NEGATIVES:
            w.writerow([CAMPAIGN, n, "Phrase"])

if __name__ == "__main__":
    valid = validate()
    n_kw = sum(len(d["keywords"]) for d in AD_GROUPS.values())
    print(f"\nGrupos: {len(AD_GROUPS)} | Keywords: {n_kw} | Negativas: {len(NEGATIVES)}")
    if valid:
        build_csv("/home/user/equipzilla/marketing/google-ads/equipzilla_campana_import.csv")
        build_negatives("/home/user/equipzilla/marketing/google-ads/equipzilla_negativas.csv")
        print("[OK] Todos los limites validados. CSV generados.")
    else:
        print("[FALLO] Corrige los limites antes de generar.")

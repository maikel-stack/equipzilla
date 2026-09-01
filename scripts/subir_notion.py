#!/usr/bin/env python3
"""Sube un markdown a Notion como página, por la API oficial.

Uso: python3 scripts/subir_notion.py <fichero.md> <titulo> [id_pagina_madre]

Convierte encabezados, listas, tablas, negritas y código inline. Si la
página ya existe con ese título bajo la madre, la archiva y crea una nueva
(la API no permite reemplazar bloques en masa de forma fiable).
Token: ~/.outbound/notion_token (integración interna "CLAUDE").
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

TOKEN = open(os.path.expanduser("~/.outbound/notion_token")).read().strip()
MADRE_POR_DEFECTO = "3ce56e1a-d6ed-812d-abe2-e6285557231d"  # página "Automation / AI"


def notion(ruta, metodo="GET", cuerpo=None):
    req = urllib.request.Request(
        "https://api.notion.com/v1" + ruta, method=metodo,
        headers={"Authorization": "Bearer " + TOKEN,
                 "Notion-Version": "2022-06-28",
                 "Content-Type": "application/json"},
        data=json.dumps(cuerpo).encode() if cuerpo else None)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_body": e.read().decode()[:500]}


def rico(texto):
    """Texto plano con **negrita** y `código` a rich_text de Notion."""
    partes, salida = re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", texto), []
    for p in partes:
        if not p:
            continue
        if p.startswith("**") and p.endswith("**"):
            salida.append({"type": "text", "text": {"content": p[2:-2]},
                           "annotations": {"bold": True}})
        elif p.startswith("`") and p.endswith("`"):
            salida.append({"type": "text", "text": {"content": p[1:-1]},
                           "annotations": {"code": True}})
        else:
            salida.append({"type": "text", "text": {"content": p}})
    return salida or [{"type": "text", "text": {"content": ""}}]


def celdas(fila):
    return [c.strip() for c in fila.strip().strip("|").split("|")]


def md_a_bloques(md):
    bloques, lineas, i = [], md.splitlines(), 0
    while i < len(lineas):
        l = lineas[i]
        s = l.strip()
        if not s or s == "---":
            if s == "---":
                bloques.append({"type": "divider", "divider": {}})
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lineas) and re.match(r"^\|[\s:|-]+\|$", lineas[i+1].strip()):
            cab = celdas(s)
            filas = [cab]
            i += 2
            while i < len(lineas) and lineas[i].strip().startswith("|"):
                filas.append(celdas(lineas[i]))
                i += 1
            ancho = len(cab)
            hijos = [{"type": "table_row", "table_row":
                      {"cells": [rico(c) for c in (f + [""] * ancho)[:ancho]]}}
                     for f in filas]
            bloques.append({"type": "table", "table": {
                "table_width": ancho, "has_column_header": True,
                "has_row_header": False, "children": hijos}})
            continue
        if s.startswith("### "):
            bloques.append({"type": "heading_3", "heading_3": {"rich_text": rico(s[4:])}})
        elif s.startswith("## "):
            bloques.append({"type": "heading_2", "heading_2": {"rich_text": rico(s[3:])}})
        elif s.startswith("# "):
            bloques.append({"type": "heading_1", "heading_1": {"rich_text": rico(s[2:])}})
        elif re.match(r"^\d+\.\s", s):
            bloques.append({"type": "numbered_list_item", "numbered_list_item":
                            {"rich_text": rico(re.sub(r"^\d+\.\s", "", s))}})
        elif s.startswith(("- ", "* ")):
            bloques.append({"type": "bulleted_list_item", "bulleted_list_item":
                            {"rich_text": rico(s[2:])}})
        elif s.startswith("> "):
            bloques.append({"type": "quote", "quote": {"rich_text": rico(s[2:])}})
        else:
            # párrafo: unir líneas contiguas
            parrafo = [s]
            while (i + 1 < len(lineas) and lineas[i+1].strip()
                   and not re.match(r"^(#|\||- |\* |> |\d+\. |---)", lineas[i+1].strip())):
                i += 1
                parrafo.append(lineas[i].strip())
            bloques.append({"type": "paragraph", "paragraph": {"rich_text": rico(" ".join(parrafo))}})
        i += 1
    return bloques


def main():
    fichero, titulo = sys.argv[1], sys.argv[2]
    madre = sys.argv[3] if len(sys.argv) > 3 else MADRE_POR_DEFECTO
    md = open(fichero).read()
    md = re.sub(r"^# .*\n", "", md, count=1)  # el H1 del doc es el título de la página
    bloques = md_a_bloques(md)
    print(f"{len(bloques)} bloques")

    # archivar versión anterior con el mismo título, si existe
    b = notion("/search", "POST", {"query": titulo, "page_size": 10})
    for r in b.get("results", []):
        if r.get("object") != "page":
            continue
        for prop in (r.get("properties") or {}).values():
            if prop.get("type") == "title":
                t = "".join(x.get("plain_text", "") for x in prop.get("title", []))
                if t == titulo:
                    notion(f"/pages/{r['id']}", "PATCH", {"archived": True})
                    print("archivada versión anterior", r["id"])

    pagina = notion("/pages", "POST", {
        "parent": {"page_id": madre},
        "icon": {"type": "emoji", "emoji": "📕"},
        "properties": {"title": {"title": [{"type": "text", "text": {"content": titulo}}]}},
        "children": bloques[:100],
    })
    if "_error" in pagina:
        print("ERROR creando página:", pagina)
        return 1
    pid = pagina["id"]
    resto = bloques[100:]
    while resto:
        r = notion(f"/blocks/{pid}/children", "PATCH", {"children": resto[:100]})
        if "_error" in r:
            print("ERROR anexando:", r)
            return 1
        resto = resto[100:]
        time.sleep(0.4)
    print("URL:", pagina.get("url"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

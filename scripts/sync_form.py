#!/usr/bin/env python3
"""Vuelca data/machines.json (fuente única) dentro del array M de quiz/form.html.

El quiz lleva el catálogo incrustado para funcionar sin llamadas externas; este
script evita que se desincronice del resto del sistema. Ejecutar tras tocar el
catálogo, junto con scripts/gen_guias.py.
"""
import json
import os
import re

ROOT = os.path.join(os.path.dirname(__file__), "..")
MS = json.load(open(os.path.join(ROOT, "data", "machines.json")))
FORM = os.path.join(ROOT, "quiz", "form.html")

def js(m):
    campos = [f'img:{json.dumps(m["img"])}', f'n:{json.dumps(m["n"], ensure_ascii=False)}',
              f'c:{json.dumps(m["c"])}', f'y:{m["y"]}',
              f'h:{m["h"] if m.get("h") else "null"}', f'p:{m["p"]}',
              f'e:{"true" if m.get("e") else "false"}',
              f's:{json.dumps(m["s"], ensure_ascii=False)}']
    if m.get("pa"):                      # precio anterior real (para el tachado)
        campos.append(f'pa:{m["pa"]}')
    return "    {" + ",".join(campos) + "}"

bloque = "  var M=[\n" + ",\n".join(js(m) for m in MS) + "\n  ];"
s = open(FORM).read()
nuevo, n = re.subn(r"  var M=\[.*?\n  \];", bloque, s, count=1, flags=re.S)
if not n:
    raise SystemExit("No encuentro el array M en form.html")
open(FORM, "w").write(nuevo)
print(f"form.html sincronizado con {len(MS)} máquinas")

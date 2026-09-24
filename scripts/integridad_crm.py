#!/usr/bin/env python3
"""Integridad diaria de Pipedrive: el ciclo del agente CRM / Datos.

Comprueba sobre los pipelines 6 y 16: tratos abiertos sin propietario, sin
actividad más de 7 días, duplicados por email y por teléfono, perdidos sin
motivo en 90 días, tiempo hasta el primer contacto de los leads de las últimas
48 horas y demanda de compra que el stock de David no cubre.

Guarda además un snapshot de los identificadores abiertos en
`data/crm_snapshot.json` y, si ya había uno de un día anterior, imprime el
cuadre exacto: cuántos había, cuáles se cerraron y cuáles son nuevos. Sin eso
hay que reconstruir el pasado a partir de las fechas de cierre, que es lo que
me llevó el 23/09 a reportar 38 tratos cuando había 39.

Solo lee. No escribe nada en Pipedrive ni en la hoja de stock.

Uso:  python3 scripts/integridad_crm.py
"""
import collections
import datetime as dt
import json
import os
import re
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panel_horario import deals_todos, pipedrive, token_google  # noqa: E402
import aviso_stock_leads as asl  # noqa: E402
import cola_comercial as cc  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT = os.path.join(RAIZ, "data", "crm_snapshot.json")
AHORA = dt.datetime.utcnow()


def ts(v):
    try:
        return dt.datetime.fromisoformat(str(v)[:19])
    except Exception:
        return None


def tit(x):
    return re.sub(r"^[0-9a-f-]{36} ?-\s*", "", x.get("title") or "")


def es_compraventa(x):
    t = tit(x)
    return bool(cc.COMPRAVENTA.search(t)) and not cc.NO_COMPRAVENTA.search(t)


def norm_tel(t):
    d = re.sub(r"\D", "", t or "")
    return d[-9:] if len(d) >= 9 else ""


def ultima_senal(x):
    """Lo más reciente que le ha pasado al trato, sin contar update_time.

    update_time cambia por cualquier edición, incluidas las del propio agente,
    así que un trato que nadie trabaja parecería vivo solo porque le dejamos
    una nota.
    """
    c = [str(v)[:19] for v in (x.get("last_activity_date"), x.get("stage_change_time"),
                               x.get("last_outgoing_mail_time"), x.get("last_incoming_mail_time"),
                               x.get("add_time")) if v]
    return max(c) if c else ""


def primer_contacto(x):
    """Horas hasta la primera señal de que alguien tocó el lead, y cuál fue.

    Ojo al leerlo: una llamada hecha desde el móvil y no registrada no aparece
    aquí. «Sin rastro» significa sin rastro en Pipedrive, no sin llamada.
    """
    t0 = ts(x.get("add_time"))
    if not t0:
        return None, ""
    try:
        fl = pipedrive("/deals/%d/flow" % x["id"], limit=200).get("data") or []
    except Exception:
        return None, ""
    time.sleep(0.15)
    for ev in sorted(fl, key=lambda e: str((e.get("data") or {}).get("log_time")
                                           or (e.get("data") or {}).get("add_time") or "")):
        o, d = ev.get("object"), ev.get("data") or {}
        t = q = None
        if o == "note":
            t, q = ts(d.get("add_time")), "nota"
        elif o == "activity" and d.get("done"):
            t, q = ts(d.get("marked_as_done_time") or d.get("update_time")), "actividad"
        elif o == "mailMessage":
            t, q = ts(d.get("add_time")), "email"
        elif o == "dealChange" and d.get("field_key") == "stage_id":
            t, q = ts(d.get("log_time")), "cambio de etapa"
        if t and t > t0 + dt.timedelta(minutes=2):
            return round((t - t0).total_seconds() / 3600, 1), q
    return None, ""


def cuadre(abiertos_hoy):
    """Diff contra el snapshot del día anterior."""
    ids = sorted(x["id"] for x in abiertos_hoy)
    prev = {}
    if os.path.exists(SNAPSHOT):
        try:
            prev = json.load(open(SNAPSHOT))
        except Exception:
            prev = {}
    salida = []
    if prev.get("ids") and prev.get("fecha", "")[:10] != AHORA.date().isoformat():
        antes = set(prev["ids"])
        ahora = set(ids)
        salida.append("CUADRE contra el snapshot de %s: %d antes − %d cerrados + %d nuevos = %d hoy"
                      % (prev["fecha"][:16], len(antes), len(antes - ahora), len(ahora - antes), len(ahora)))
        for i in sorted(antes - ahora):
            salida.append("   se fue:  %s" % i)
        for i in sorted(ahora - antes):
            salida.append("   entra:   %s" % i)
    json.dump({"fecha": AHORA.isoformat(timespec="seconds"), "ids": ids},
              open(SNAPSHOT, "w"), indent=1)
    return salida


def main():
    users = {u["id"]: u for u in pipedrive("/users").get("data") or []}
    etapas = cc.etapas()
    abiertos = [x for x in deals_todos(estados=("open",)) if x.get("pipeline_id") in cc.PIPELINES]
    for x in abiertos:
        x["_cv"] = es_compraventa(x)
    compra = [x for x in abiertos if x["_cv"]]
    print("abiertos: %d (compraventa %d · alquiler %d)" % (len(abiertos), len(compra), len(abiertos) - len(compra)))
    for linea in cuadre(compra):
        print(linea)

    # 1. propietario
    sin_prop = []
    for x in abiertos:
        uid = (x.get("user_id") or {}).get("id") if isinstance(x.get("user_id"), dict) else x.get("user_id")
        u = users.get(uid)
        if not u:
            sin_prop.append((x["id"], "sin usuario"))
        elif not u["active_flag"]:
            sin_prop.append((x["id"], "propietario inactivo: " + u["name"]))
    print("\nsin propietario o con propietario inactivo: %d %s" % (len(sin_prop), sin_prop[:6]))

    # 2. sin actividad > 7 días
    parados = []
    for x in abiertos:
        u = ultima_senal(x)
        d = (AHORA - ts(u)).days if ts(u) else 999
        if d > 7:
            parados.append((d, x["id"], tit(x)[:52], etapas.get(x["stage_id"], "?"),
                            (x.get("user_id") or {}).get("name"), x["_cv"]))
    parados.sort(reverse=True)
    print("\nsin actividad > 7 días: %d (compra %d)" % (len(parados), sum(1 for p in parados if p[5])))
    for p in parados:
        if p[5]:
            print("   COMPRA  %4d d  %-6s %-52s %s · %s" % (p[0], p[1], p[2], p[3], p[4]))
    print("   alquiler: %d, el más viejo %d d" % (sum(1 for p in parados if not p[5]),
                                                  max([p[0] for p in parados if not p[5]] or [0])))

    # 3. duplicados
    por_email, por_tel = collections.defaultdict(set), collections.defaultdict(set)
    for x in abiertos:
        p = x.get("person_id") or {}
        for e in p.get("email") or []:
            v = (e.get("value") or "").strip().lower()
            if v:
                por_email[v].add(x["id"])
        for t in p.get("phone") or []:
            v = norm_tel(t.get("value"))
            if v:
                por_tel[v].add(x["id"])
    dup_e = {k: sorted(v) for k, v in por_email.items() if len(v) > 1}
    dup_t = {k: sorted(v) for k, v in por_tel.items() if len(v) > 1}
    print("\nduplicados por email: %d" % len(dup_e))
    for k, v in dup_e.items():
        print("   %-38s %s" % (k[:38], v))
    print("duplicados por teléfono (solo los que no salen ya por email): %d"
          % len([1 for k, v in dup_t.items() if v not in dup_e.values()]))

    # 4. perdidos sin motivo, 90 días
    corte = (AHORA - dt.timedelta(days=90))
    perdidos = [x for x in deals_todos(estados=("lost",))
                if x.get("pipeline_id") in cc.PIPELINES and ts(x.get("lost_time"))
                and ts(x.get("lost_time")) >= corte]
    sin_motivo = [x["id"] for x in perdidos if not (x.get("lost_reason") or "").strip()]
    print("\nperdidos en 90 días: %d · sin motivo: %d %s" % (len(perdidos), len(sin_motivo), sin_motivo[:8]))
    print("motivos más usados:", collections.Counter(
        (x.get("lost_reason") or "(vacío)").strip()[:46] for x in perdidos).most_common(5))

    # 5. tiempo a primer contacto, 48 h
    corte48 = (AHORA - dt.timedelta(hours=48)).isoformat()[:19]
    nuevos = [x for x in abiertos if str(x.get("add_time"))[:19] >= corte48]
    horas, sin_rastro = [], []
    print("\nleads de las últimas 48 h: %d" % len(nuevos))
    for x in sorted(nuevos, key=lambda z: str(z.get("add_time"))):
        h, q = primer_contacto(x)
        edad = round((AHORA - ts(x["add_time"])).total_seconds() / 3600, 1)
        if h is None:
            sin_rastro.append((x["id"], tit(x)[:44], edad))
        else:
            horas.append(h)
        print("   %-6s %-46s alta %s  %s" % (x["id"], tit(x)[:46], str(x["add_time"])[:16],
                                             ("%.1f h · %s" % (h, q)) if h is not None else "SIN RASTRO (%.0f h)" % edad))
    print("   con rastro: %d · mediana %s h · sin rastro pasadas 24 h: %s"
          % (len(horas), statistics.median(horas) if horas else "—",
             [(i, t, round(e)) for i, t, e in sin_rastro if e > 24] or "ninguno"))

    # 6. demanda de compra que el stock no cubre
    inv = asl.stock(token_google(["https://www.googleapis.com/auth/spreadsheets.readonly"]))
    cats = collections.Counter(f["categoria"] for f in inv if f["categoria"])
    print("\nstock de David: %d máquinas %s" % (len(inv), dict(cats)))
    sin_cubrir = []
    for x in compra:
        if tit(x).startswith("Prospecto"):
            continue
        atype = cc.opcion("assetType", x.get(cc.campo("assetType").get("key")))
        cat = cc.categoria(" ".join((atype, tit(x))))
        etiqueta = cc.ETIQUETA.get(cat, "")
        if cat and not cats.get(etiqueta):
            sin_cubrir.append((x["id"], tit(x)[:46], etiqueta or "sin clasificar", x.get("value") or 0))
    print("compra abierta sin stock en su categoría: %d" % len(sin_cubrir))
    for s in sin_cubrir:
        print("   %-6s %-46s %-24s %s €" % s)
    print("\n(el detalle por cliente está en la pestaña «Demanda sin stock»: "
          "python3 scripts/demanda_sin_stock.py)")


if __name__ == "__main__":
    main()

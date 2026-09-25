#!/usr/bin/env python3
"""Cola comercial priorizada · vista única de todos los leads de compraventa.

Pedido por Maikel y Andrés (08/09): que la cola no sea solo los clics de Brevo,
sino TODO lo que entra por cualquier canal, con:
  · de qué canal viene cada lead (Smartlead frío, Brevo ABM, Google Ads, web)
  · empresa (Pipedrive → Brevo → Smartlead → dominio del email) y tipo de empresa
  · etapa del trato en Pipedrive y si está sin contactar / contactado
  · la última actualización que se le ha hecho al trato (nota, actividad, etapa)
  · qué pide / qué miró, con la REFERENCIA de nuestra máquina (columna img del stock)
  · cuánto lleva desde que entró y cuánto lleva en la etapa actual
  · arriba, los tiempos del embudo: días lead→oferta y lead→cierre (mediana)

Fuentes:
  · Pipedrive: tratos abiertos de compraventa (pipeline 6 Transaccional y 16 Compraventa)
  · Brevo: clics en las campañas ABM (quien clicó y no está en el CRM)
  · Smartlead: respuestas y clics del frío (quien señaló y no está en el CRM)
  · data/machines.json: stock real para proponer alternativas

Escribe la pestaña "Cola comercial" del Sheet de mando. No toca LLAMADO/RESULTADO.

Uso:
    python3 scripts/cola_comercial.py [--sheet] [dias]
"""
import datetime as dt
import json
import os
import re
import statistics
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panel_horario import (SHEET_ID, brevo, campanas, clickers,  # noqa: E402
                           falta, maquina_de_url, pipedrive, sheets, smartlead,
                           subir, token_google)
from captar_leads import EXCLUIR  # noqa: E402  (fuera de ICP: museos, eléctricas, competidores…)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOY = dt.date.today()
PIPELINES = (6, 16)
ETAPA_OFERTA = {37, 87, 91, 92}           # "Oferta enviada" (6) y Cold/Medium/Hot (16)
COMPRAVENTA = re.compile(r"compra|prospecto|clic campa", re.I)
NO_COMPRAVENTA = re.compile(r"solicitud de consulta por rent|^alquiler|renting", re.I)

# Referencias internas de las campañas antiguas (columna "img" del stock).
PREFIJO_REF = [(r"^KB|^KU", "mini"), (r"^DX\d|^D2\d", "exca"), (r"^DL", "pala"),
               (r"^CL|^GAM-(DFG|ERP)", "carr"), (r"^EL-|^GAM-(MANITOU|COMPACT)", "plat"),
               (r"^MT-", "mini")]

CATEGORIAS = [
    (r"jlg|genie|haulotte|manitou 1[0-9]0|tijera|plataforma|articulada|multitel|elevadora de tijera|elevador de tijera", "plat", "Plataformas de elevación"),
    (r"kubota (u|k|kx)|develon|doosan dx (2[0-9]|3[0-9])|mini ?exc|miniexc", "mini", "Miniexcavadoras"),
    (r"doosan dx (1[0-9]{2}|2[0-9]{2})|excavadora|giratoria|retro", "exca", "Excavadoras"),
    (r"carretilla|hyster|yale|jungheinrich|clark|toro|transpaleta", "carr", "Carretillas"),
    (r"telesc|manitou m|merlo|manipulador", "tele", "Telescópicas"),
    (r"pala|bobcat|cargadora|minicargadora", "pala", "Palas y minicargadoras"),
    (r"dumper|wacker", "dum", "Dumpers"),
]
ETIQUETA = {c: n for _, c, n in CATEGORIAS}

DOMINIOS_GENERICOS = {"gmail.com", "hotmail.com", "hotmail.es", "outlook.com", "outlook.es",
                      "yahoo.es", "yahoo.com", "icloud.com", "live.com", "msn.com",
                      "telefonica.net", "movistar.es", "orange.es", "ono.com", "me.com"}

TIPOS_EMPRESA = [
    (r"excavac|movimiento de tierra|derribo|demolic|desmonte", "Excavaciones / movimiento de tierras"),
    (r"alquil|rental|rent\b|maquinaria de alquiler", "Alquilador de maquinaria"),
    (r"infraestruct|obra civil|ingenier|ingenieria|urbaniz|asfalt|carretera", "Obra civil / ingeniería"),
    (r"constru|obras|edificac|reforma|promotor|contrat", "Constructora"),
    (r"instalac|electric|fontaner|clima|montaje", "Instaladora"),
    (r"transport|logist|almac|gru[aá]s", "Transporte / logística"),
    (r"industr|fabric|metal|manufact|talleres|taller", "Industrial"),
    (r"agr[ií]col|agro|ganad|forest|jardin", "Agrícola / forestal"),
    (r"ayuntamiento|municipal|diputac|consorcio", "Administración pública"),
    (r"rail|ferrov", "Ferroviario"),
]


# ---------------------------------------------------------------- utilidades
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


def stock():
    m = json.load(open(os.path.join(RAIZ, "data", "machines.json")))
    por_cat = {}
    for x in m:
        por_cat.setdefault(x["c"], []).append(x)
    for v in por_cat.values():
        v.sort(key=lambda x: x.get("p") or 0)
    return por_cat


def en_stock(texto, inv):
    """Ficha real de nuestro stock a partir de lo que miró (nombre o referencia)."""
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


def ficha_txt(f):
    """'Kubota KX 016-4 G [KB298] · 18.900 €' — la referencia es lo que David
    necesita para localizar la máquina."""
    p = f.get("p") or 0
    return "%s [%s]%s" % (f["n"], f["img"], (" · %s €" % eur(p)) if p else "")


def eur(n):
    return format(int(n), ",d").replace(",", ".")


def encajes(cat, precio_ref, inv, tope=3):
    ops = inv.get(cat) or []
    if precio_ref and ops:
        ops = sorted(ops, key=lambda x: abs((x.get("p") or 0) - precio_ref))
    return ops[:tope]


def precio_de(texto):
    m = re.search(r"([\d.]+)\s*€", texto or "")
    try:
        return int(m.group(1).replace(".", "")) if m else 0
    except ValueError:
        return 0


def empresa_de_dominio(email):
    """Si el email es info@aliqueconstrucciones.com, la empresa es 'Aliqueconstrucciones'.
    Con dominios genéricos (gmail…) no se inventa nada."""
    dom = (email or "").split("@")[-1].lower()
    if not dom or dom in DOMINIOS_GENERICOS:
        return ""
    base = dom.split(".")[0] if not dom.startswith("www.") else dom.split(".")[1]
    return base.replace("-", " ").replace("_", " ").title()


def tipo_empresa(*textos):
    t = " ".join(x or "" for x in textos).lower()
    for patron, nombre in TIPOS_EMPRESA:
        if re.search(patron, t):
            return nombre
    return ""


def dias_desde(fecha):
    if not fecha:
        return None
    try:
        return (HOY - dt.date.fromisoformat(str(fecha)[:10])).days
    except ValueError:
        return None


def fmt(fecha):
    f = str(fecha or "")[:10]
    return "%s/%s" % (f[8:10], f[5:7]) if len(f) == 10 else ""


# ---------------------------------------------------------------- Pipedrive
_CAMPOS = {}


def campo(nombre):
    """Clave hash de un campo personalizado de tratos, por su nombre."""
    if not _CAMPOS:
        for f in pipedrive("/dealFields", limit=500).get("data") or []:
            _CAMPOS[f["name"]] = f
    return _CAMPOS.get(nombre) or {}


def opcion(nombre, valor):
    ops = {str(o["id"]): o["label"] for o in (campo(nombre).get("options") or [])}
    return ops.get(str(valor), "") if valor else ""


def etapas():
    out = {}
    for pid in PIPELINES:
        for s in pipedrive("/stages", pipeline_id=pid).get("data") or []:
            out[s["id"]] = s["name"]
    return out


def deals(status="open"):
    todos, start = [], 0
    while True:
        d = pipedrive("/deals", start=start, limit=500, status=status)
        datos = d.get("data") or []
        todos += [x for x in datos if x.get("pipeline_id") in PIPELINES
                  and COMPRAVENTA.search(x.get("title") or "")
                  and not NO_COMPRAVENTA.search(re.sub(r"^[0-9a-f-]{36} -\s*", "", x.get("title") or ""))]
        if not (d.get("additional_data", {}).get("pagination", {}).get("more_items_in_collection")):
            break
        start += 500
    return todos


def canal_de(x, persona):
    """De dónde ha entrado el lead. Orden: lo que dice el propio título (frío /
    ABM), el gclid (Google Ads), utm/first-click (SEO, social…), y si no, web."""
    t = x.get("title") or ""
    if re.search(r"respuesta fr", t, re.I):
        return "Smartlead · respuesta frío"
    if re.search(r"clic fr", t, re.I):
        return "Smartlead · clic frío"
    if re.search(r"clic campa", t, re.I):
        return "Brevo · clic campaña ABM"
    gclid = (x.get(campo("Gclid").get("key")) or "").strip()
    if gclid and gclid.lower() != "sin contenido":
        return "Google Ads"
    utm = (x.get(campo("Utm").get("key")) or "").strip()
    if utm and utm.lower() != "sin contenido":
        return "Web · " + utm[:30]
    for k in ("First Click Source", "Origen Lead", "Last Click Source"):
        v = (persona.get(_PF.get(k, "")) or "").strip()
        if v:
            return "Web · " + v[:30]
    if x.get("channel"):
        return {"Web forms": "Web · formulario"}.get(str(x["channel"]), "Web · %s" % x["channel"])
    return "Web · formulario (orgánico/directo)"


_PF = {}
_PERSONAS = {}


def persona(pid):
    if not pid:
        return {}
    if not _PF:
        for f in pipedrive("/personFields", limit=500).get("data") or []:
            _PF[f["name"]] = f["key"]
    if pid not in _PERSONAS:
        _PERSONAS[pid] = pipedrive("/persons/%d" % pid).get("data") or {}
        time.sleep(0.15)
    return _PERSONAS[pid]


# Notas que escribe un agente, no una persona del equipo. Van firmadas.
NOTA_DE_AGENTE = re.compile(r"^\s*\[(agente|crm ·|outbound ·|seguimiento ·)", re.I)


def ultima_actualizacion(x):
    """Qué fue lo último que se hizo en el trato y cuándo.

    Las notas del propio agente no cuentan. Si contaran, la nota de cadencia
    que este agente escribe cada mañana daría al trato el bono de «movido
    hoy/ayer» (+15 de score) sin que nadie haya llamado al cliente, y el trato
    subiría a HOT solo porque le hemos escrito nosotros. Fue lo que hizo
    oscilar las HOT entre 18 y 15 durante la semana del 21/09.
    """
    candidatos = []
    if x.get("notes_count"):
        n = pipedrive("/notes", deal_id=x["id"], limit=5, sort="update_time DESC").get("data") or []
        for z in n:
            txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", z.get("content") or "")).strip()
            if NOTA_DE_AGENTE.match(txt):
                continue
            candidatos.append((z.get("update_time") or "", "nota: " + txt[:70]))
            break
        time.sleep(0.15)
    if x.get("last_activity_id") and x.get("last_activity_date"):
        a = pipedrive("/deals/%d/activities" % x["id"], limit=1, done=1).get("data") or []
        if a:
            candidatos.append((a[0].get("marked_as_done_time") or x["last_activity_date"],
                               "%s: %s" % (a[0].get("type") or "actividad", (a[0].get("subject") or "")[:50])))
        time.sleep(0.15)
    if x.get("last_outgoing_mail_time"):
        candidatos.append((x["last_outgoing_mail_time"], "email enviado desde el CRM"))
    if x.get("last_incoming_mail_time"):
        candidatos.append((x["last_incoming_mail_time"], "email recibido del lead"))
    if x.get("stage_change_time"):
        candidatos.append((x["stage_change_time"], "cambio de etapa"))
    if not candidatos:
        return x.get("update_time") or "", "alta del trato (sin notas ni actividades)"
    cuando, que = max(candidatos, key=lambda c: c[0])
    return cuando, que


def contactado(x):
    if (x.get("done_activities_count") or x.get("notes_count")
            or x.get("last_outgoing_mail_time") or x.get("email_messages_count")):
        return "Contactado · " + fmt(x.get("last_activity_date") or x.get("update_time"))
    return "Sin contactar"


def dias_hasta_oferta(x):
    """Primera vez que el trato pasó a 'Oferta enviada', vía el histórico."""
    try:
        fl = pipedrive("/deals/%d/flow" % x["id"], limit=200).get("data") or []
    except Exception:
        return None
    time.sleep(0.15)
    for ev in reversed(fl):             # de más antiguo a más nuevo
        d = ev.get("data") or {}
        if ev.get("object") == "dealChange" and d.get("field_key") == "stage_id" \
                and str(d.get("new_value")) in {str(s) for s in ETAPA_OFERTA}:
            t0 = dt.datetime.fromisoformat(str(x["add_time"])[:19])
            t1 = dt.datetime.fromisoformat(str(d.get("log_time"))[:19])
            return max((t1 - t0).days, 0)
    return None


def tiempos_embudo(abiertos):
    """Mediana de días lead→oferta y lead→cierre (últimos 120 días)."""
    corte = (HOY - dt.timedelta(days=120)).isoformat()
    cerrados = [x for x in deals("won") + deals("lost") if str(x.get("add_time"))[:10] >= corte]
    recientes = [x for x in abiertos if str(x.get("add_time"))[:10] >= corte]
    a_oferta = []
    for x in recientes + cerrados:
        d = dias_hasta_oferta(x)
        x["_dias_oferta"] = d
        if d is not None:
            a_oferta.append(d)
    a_cierre = [max(dias_desde(x["add_time"]) - (dias_desde(x.get("won_time") or x.get("lost_time")) or 0), 0)
                for x in cerrados if x.get("won_time") or x.get("lost_time")]
    ganados = [x for x in cerrados if x.get("status") == "won"]
    sin_contacto = sum(1 for x in abiertos if contactado(x) == "Sin contactar")
    med = lambda v: ("%d días" % statistics.median(v)) if v else "sin datos"
    return [
        ["TIEMPOS DEL EMBUDO (tratos de compraventa dados de alta en los últimos 120 días)"],
        ["Lead → oferta enviada (mediana)", med(a_oferta), "sobre %d tratos que llegaron a oferta" % len(a_oferta)],
        ["Lead → cierre (mediana, ganado o perdido)", med(a_cierre), "sobre %d tratos cerrados · %d ganados" % (len(cerrados), len(ganados))],
        ["Tratos abiertos sin contactar", str(sin_contacto), "de %d abiertos" % len(abiertos)],
    ]


# ---------------------------------------------------------------- Brevo (ABM)
def segmentos():
    nombres = {l["id"]: l["name"] for l in brevo("/contacts/lists?limit=50").get("lists", [])}
    mapa = {}
    for c in brevo("/emailCampaigns?type=classic&status=sent&limit=50&sort=desc").get("campaigns", []):
        ls = [nombres.get(s.get("listId"), "") for s in (c.get("statistics", {}).get("campaignStats") or [])
              if s.get("listId") != 34 and s.get("sent")]
        mapa[c["id"]] = " + ".join(x for x in dict.fromkeys(ls) if x)
    return mapa


# Rangos de centros de datos (AWS, Azure, Google y pasarelas de seguridad).
DATACENTRO = ("3.", "13.", "15.", "18.", "20.", "34.", "35.", "40.", "51.",
              "52.", "54.", "64.233.", "66.102.", "67.231.", "104.47.",
              "148.163.", "185.58.", "195.130.217.", "91.220.42.")


# Dominios cuyos «clics» son siempre de un antivirus de correo, no de una
# persona. Los mantiene el agente de Base de datos en
# `data/escaneres_dominios.json`, con el motivo de cada uno y su criterio (clic
# antes de 90 s del envío, varios enlaces en el mismo segundo, o clics en todas
# las campañas sin apertura humana). Aquí solo se leen: para añadir o quitar uno
# se edita ese fichero, no este código.
#
# Por qué existe: avot.es entró en la cola el 23/09 como HOT con 85 puntos y
# Casa Ametller estuvo seis días entre los «HOT sin dueño» que este agente
# reportó el 17/09. La detección por IP y por ráfaga de escaner_clic() no los
# cazaba.
ESCANERES = os.path.join(RAIZ, "data", "escaneres_dominios.json")


def _dominios_escaner():
    try:
        return set(json.load(open(ESCANERES)).get("dominios") or {})
    except Exception as err:
        print("[aviso: no se pudo leer %s (%s): la cola sale sin el filtro de "
              "escáneres por dominio]" % (ESCANERES, err))
        return set()


DOMINIOS_ESCANER = _dominios_escaner()


def es_escaner_conocido(email):
    """True si el email pertenece a un dominio marcado como escáner por BBDD."""
    e = (email or "").strip().lower()
    return "@" in e and e.rsplit("@", 1)[-1] in DOMINIOS_ESCANER


def escaner_clic(fila):
    """True si el clic lo hizo un antivirus de correo y no una persona.

    Huellas: IP de centro de datos, o varios clics en menos de 90 segundos.
    El 17/09, tres de los cuatro «clickers» de la campaña #221 eran esto; uno
    llevaba semanas encabezando la cola con puntuación 95.
    """
    ip = (fila.get("Click_IP") or "").strip()
    if ip and any(ip.startswith(p) for p in DATACENTRO):
        return True
    horas = []
    for k, v in fila.items():
        if not k or not str(k).startswith("http") or not v:
            continue
        try:
            horas.append(dt.datetime.strptime(str(v).strip()[:19], "%d-%m-%Y %H:%M:%S"))
        except ValueError:
            pass
    return len(horas) >= 2 and (max(horas) - min(horas)).total_seconds() <= 90


def clics_brevo(dias):
    corte = (HOY - dt.timedelta(days=dias)).isoformat()
    segs = segmentos()
    gente = {}
    for c in campanas(20):
        if (c["fecha"] or "")[:10] < corte:
            continue
        for r in clickers(c["id"]):
            em = (r.get("Email_ID") or "").strip().lower()
            if not em:
                continue
            if escaner_clic(r):
                # Antivirus de correo: abre cada enlace del mensaje al entregarlo.
                # Sin esto la cola corona como lead más caliente a un servidor.
                continue
            miro = [maquina_de_url(k) for k, v in r.items() if k.startswith("http") and (v or "").strip()]
            miro = [x for x in dict.fromkeys(miro) if x and x not in ("web", "WhatsApp")]
            g = gente.setdefault(em, dict(email=em, clics=0, campanas=set(), listas=set(), maquinas=[], ultima=""))
            if segs.get(c["id"]):
                g["listas"].add(segs[c["id"]])
            try:
                g["clics"] += int(r.get("Clicked_Links_Count") or 0)
            except ValueError:
                pass
            g["campanas"].add(c["nombre"][:38])
            g["maquinas"] += miro
            g["ultima"] = max(g["ultima"], c["fecha"])
    return gente


# ---------------------------------------------------------------- Smartlead (frío)
_IR = None


def ir_mod():
    global _IR
    if _IR is None:
        import informe_respuestas as ir
        _IR = ir
    return _IR


def senales_smartlead(dias):
    ir = ir_mod()
    ir.VENTANA_H = dias * 24
    try:
        return ir.senales_frio(), ir
    except Exception as err:
        print("[Smartlead no disponible: %s]" % err)
        return {}, ir


# ---------------------------------------------------------------- contacto
_CACHE = {}


# Dominios nuestros: si un lead llega con uno de estos como email de contacto,
# el dato es basura del formulario, no del cliente (caso Tirri, 15/09: la cola
# mostró clientes@equipzilla.com como email del lead y «Equipzilla» como su
# empresa, y así llegó a «Mi día» del equipo comercial).
DOMINIOS_PROPIOS = ("equipzilla.com", "ocasion.equipzilla.com")


def email_valido(email):
    e = (email or "").strip().lower()
    return bool(e) and "@" in e and e.split("@")[-1] not in DOMINIOS_PROPIOS


def datos_contacto(email, persona_pd=None):
    """Nombre, teléfono, empresa, actividad. Pipedrive → Smartlead → Brevo → dominio.

    Sin un email válido del cliente no se consulta Smartlead ni Brevo (una
    búsqueda con la cadena vacía devuelve un registro cualquiera) y no se
    cachea: con la clave "" todos los leads sin email compartían la ficha del
    primero.
    """
    valido = email_valido(email)
    if valido and email in _CACHE:
        return _CACHE[email]
    nombre = tel = empresa = actividad = ""
    p = persona_pd or {}
    if not p:
        try:
            r = pipedrive("/persons/search", term=email, fields="email", limit=1)
            it = ((r.get("data") or {}).get("items") or [])
            if it:
                p = pipedrive("/persons/%d" % it[0]["item"]["id"]).get("data") or {}
            time.sleep(0.15)
        except Exception:
            p = {}
    if p:
        nombre = p.get("name") or ""
        tels = [t.get("value") for t in (p.get("phone") or []) if t.get("value")]
        tel = tels[0] if tels else ""
        empresa = (p.get("org_name") or (p.get("org_id") or {}).get("name") if isinstance(p.get("org_id"), dict) else p.get("org_name")) or ""
    if valido and (not tel or not empresa):
        try:
            l = smartlead("/leads/?email=" + urllib.parse.quote(email))
            if isinstance(l, dict) and l.get("id"):
                tel = tel or l.get("phone_number") or ""
                nombre = nombre or " ".join(x for x in (l.get("first_name"), l.get("last_name")) if x)
                empresa = empresa or l.get("company_name") or ""
        except Exception:
            pass
    if valido and (not tel or not empresa or not actividad):
        try:
            b = brevo("/contacts/" + urllib.parse.quote(email))
            at = b.get("attributes") or {}
            nombre = nombre or at.get("NOMBRE") or at.get("FIRSTNAME") or ""
            tel = tel or at.get("SMS") or at.get("TELEFONO") or at.get("WHATSAPP") or ""
            empresa = empresa or at.get("RAZON_SOCIAL") or at.get("EMPRESA") or ""
            actividad = at.get("ACTIVIDAD") or ""
        except Exception:
            pass
    if nombre and "@" in nombre:
        nombre = ""
    if valido:
        empresa = empresa or empresa_de_dominio(email)
    fila = (nombre.strip(), str(tel or "").strip(), str(empresa).strip(), str(actividad).strip())
    if valido:
        _CACHE[email] = fila
    return fila


# ---------------------------------------------------------------- construir
CABECERA = ["Score", "Prioridad", "Canal de entrada", "Etapa CRM", "Contacto", "Propietario", "Nombre", "Empresa",
            "Tipo de empresa", "Teléfono", "Email", "Qué pide / qué miró", "Categoría",
            "Presupuesto / valor", "Qué tenemos que encaja [ref]", "Lista / campaña", "Última señal",
            "Última actualización en Pipedrive", "Días desde entrada", "Días en etapa",
            "Días hasta oferta", "Por qué", "Siguiente acción", "ID trato"]


def fila_crm(x, inv, nombres_etapa):
    p = persona((x.get("person_id") or {}).get("value"))
    nombre, tel, empresa, actividad = datos_contacto(
        ((x.get("person_id") or {}).get("email") or [{}])[0].get("value", "") if x.get("person_id") else "", p)
    email = ((x.get("person_id") or {}).get("email") or [{}])[0].get("value", "") if x.get("person_id") else ""
    razon = x.get(campo("Razón Social").get("key")) or ""
    if razon and razon.strip().upper() != "PENDIENTE":
        empresa = razon.strip()
    profesional = opcion("profesional", x.get(campo("profesional").get("key")))
    tipo = " · ".join(t for t in (profesional, actividad or tipo_empresa(empresa, email)) if t)
    asset = opcion("assetType", x.get(campo("assetType").get("key")))
    uso = re.sub(r"\s+", " ", x.get(campo("assetUse").get("key")) or "").strip()
    titulo = re.sub(r"^[0-9a-f-]{36} -\s*", "", x.get("title") or "")
    pide = " · ".join(t for t in (asset, uso[:80]) if t) or titulo[:80]
    frio = bool(re.search(r"respuesta fr|clic fr", titulo, re.I))
    if frio and email and re.search(r"respuesta fr", titulo, re.I):
        try:
            texto = ir_mod().texto_respuesta(email)
            if texto:
                pide = "Respondió: «%s»" % texto[:90]
        except Exception:
            pass
    fuera_icp = frio and bool(EXCLUIR.search(" ".join((empresa, email, nombre))))
    cat = categoria(" ".join((asset, uso, titulo)))
    valor = x.get("value") or 0
    pmax = precio_de(x.get(campo("Precio maximo").get("key")) or "") or precio_de(uso)
    ops = encajes(cat, pmax or valor, inv)
    encaja = " · ".join(ficha_txt(o) for o in ops) or ("sin stock en su categoría → sourcing" if cat else "—")
    cuando, que = ultima_actualizacion(x)
    etapa = nombres_etapa.get(x.get("stage_id"), str(x.get("stage_id")))
    d_in, d_et = dias_desde(x.get("add_time")), dias_desde(x.get("stage_change_time"))
    d_of = x.get("_dias_oferta")
    est = contactado(x)
    # score: etapa + frescura + valor + contacto
    base = {45: 60, 85: 60, 33: 70, 86: 70, 37: 50, 87: 45, 91: 55, 92: 75, 38: 90, 89: 90, 28: 85, 46: 95, 90: 95}
    score = base.get(x.get("stage_id"), 40)
    porque = [etapa]
    if valor:
        score += 10; porque.append("valor %s €" % eur(valor))
    du = dias_desde(cuando) if cuando else 99
    if du is not None and du <= 2:
        score += 15; porque.append("movido hoy/ayer")
    elif du is not None and du > 7:
        score -= 10 if du <= 14 else 20
        porque.append("%d días sin tocar" % du)
    if est == "Sin contactar":
        score += 10; porque.append("SIN CONTACTAR")
    if re.search(r"clic fr", titulo, re.I):
        score -= 20; porque.append("solo clic, sin respuesta")
    score = max(0, min(score, 100))
    if x.get("stage_id") in (45, 33, 85, 86):
        accion = "Enviar oferta" + (" (lead de %d días)" % d_in if d_in and d_in > 3 else "")
    elif x.get("stage_id") in ETAPA_OFERTA:
        accion = "Seguir la oferta: llamar y pedir decisión" if (du or 0) > 5 else "Esperar respuesta a la oferta"
    elif x.get("stage_id") in (38, 28, 89):
        accion = "Cerrar: documentación, pago y entrega"
    else:
        accion = "Entrega y post-venta"
    if est == "Sin contactar":
        accion = "LLAMAR HOY (no se ha contactado) · " + accion
    if not ops and cat:
        accion += " · anotar en Want-to-Buy (sin stock que encaje)"
    nivel = ("🔥 HOT" if score >= 75 else "🟠 WARM" if score >= 55 else "🔵 NURTURE" if score >= 35 else "⚪ LOW")
    if fuera_icp:
        score, nivel = 0, "⚠ FUERA DE ICP"
        accion = "Descartar en Pipedrive: no compra maquinaria (museo, eléctrica, competidor…)"
        porque = ["entró por el frío y no es perfil comprador"]
    return [score, nivel, canal_de(x, p), etapa, est, x.get("owner_name") or "—", nombre or "—", empresa or "—", tipo or "—",
            tel or "sin teléfono", email if email_valido(email) else "— (pedir email)", pide, ETIQUETA.get(cat, "—"),
            ("%s €" % eur(valor)) if valor else (("hasta %s €" % eur(pmax)) if pmax else "—"),
            encaja[:110], "Pipedrive · %s" % titulo.split(" - ")[0][:30], fmt(x.get("update_time")),
            "%s · %s" % (fmt(cuando), que) if cuando else que,
            d_in if d_in is not None else "—", d_et if d_et is not None else "—",
            d_of if d_of is not None else "—", " · ".join(porque), accion, x["id"]]


def fila_fuera_crm(email, canal, maquinas, listas, campanas_, ultima, senal, inv, ir=None, perdido=None):
    nombre, tel, empresa, actividad = datos_contacto(email)
    cats = [c for c in (categoria(m) for m in maquinas) if c]
    cat = cats[0] if cats else ""
    pref = max((precio_de(m) for m in maquinas), default=0)
    fichas = [f for f in (en_stock(m, inv) for m in maquinas) if f]
    if fichas:
        pref = pref or max(f.get("p") or 0 for f in fichas)
        cat = cat or fichas[0]["c"]
    miro = " · ".join(ficha_txt(f) for f in fichas) or " · ".join(dict.fromkeys(maquinas))[:80] or "—"
    ops = encajes(cat, pref, inv)
    encaja = " · ".join(ficha_txt(o) for o in ops) or ("sin stock en su categoría → sourcing" if cat else "—")
    d_ult = dias_desde(ultima) if ultima else 99
    score, porque = 0, []
    if senal.get("respuesta"):
        score += 45; porque.append("ha respondido al frío")
    score += min(senal.get("clics", 1), 5) * 10
    if senal.get("clics", 0) >= 2:
        porque.append("%d clics" % senal["clics"])
    if d_ult <= 2:
        score += 25; porque.append("señal de hoy/ayer")
    elif d_ult <= 7:
        score += 15; porque.append("señal esta semana")
    if len(campanas_) >= 2:
        score += 15; porque.append("repite en %d campañas" % len(campanas_))
    if fichas or pref:
        score += 15; porque.append("máquina concreta")
    score = min(score, 100)
    nivel = ("🔥 HOT" if score >= 70 else "🟠 WARM" if score >= 45 else "🔵 NURTURE" if score >= 25 else "⚪ LOW")
    accion = ("Llamar hoy y abrir trato en Pipedrive" if score >= 70 else
              "Llamar esta semana con las alternativas" if score >= 45 else "Email de seguimiento con su categoría")
    if not ops and cat:
        accion = "Llamar y anotar en Want-to-Buy: no tenemos stock que encaje"
    if perdido:
        trato, d_perd, motivo = perdido
        score = max(score - 30, 0)
        nivel = "🔵 NURTURE" if score >= 25 else "⚪ LOW"
        porque.insert(0, "PERDIDO hace %d d (trato %s): %s" % (d_perd, trato, motivo[:45]))
        accion = "Ya se descartó hace %d d. Reabrir el trato %s solo si esta señal lo justifica" % (d_perd, trato)
    return [score, nivel, canal, "Fuera del CRM", "Sin contactar", "sin asignar", nombre or "—", empresa or "—",
            (actividad or tipo_empresa(empresa, email)) or "—", tel or "sin teléfono", email, miro,
            ETIQUETA.get(cat, "—"), ("hasta %s €" % eur(pref)) if pref else "—", encaja[:110],
            " / ".join(sorted(listas or campanas_))[:70] or "—", fmt(ultima), "— (no está en Pipedrive)",
            "—", "—", "—", " · ".join(porque), accion, ""]


# Pruebas del formulario que acaban en Pipedrive como tratos reales: el nombre
# lleva «prueba»/«test» o el contacto es un email nuestro (17/09: 53855 y 53857,
# «Fernando Prueba Test» con fernando@equipzilla.com, entraron en la cola y en
# las métricas del mes como dos leads de alquiler).
ES_PRUEBA = re.compile(r"\b(prueba|pruebas|test|testing|demo)\b", re.I)


def es_trato_de_prueba(x):
    p = x.get("person_id") or {}
    em = ((p.get("email") or [{}])[0].get("value") or "")
    return bool(ES_PRUEBA.search(p.get("name") or "")) or not email_valido(em) and "@" in em


def es_trato_de_escaner(x):
    """Trato creado a partir del clic de un antivirus de correo.

    El filtro por dominio no basta en las señales: el proceso que convierte los
    clics de campaña en tratos no aplica la lista, así que el clic ya viene
    convertido en un trato de Pipedrive y entra en la cola por la puerta de los
    tratos, no por la de las señales. El 24/09, avot.es aparecía como HOT con 85
    puntos por el trato 53924, creado el 23/09 desde un clic suyo.
    """
    p = x.get("person_id") or {}
    em = ((p.get("email") or [{}])[0].get("value") or "")
    return es_escaner_conocido(em) and bool(re.search(r"clic campa|clic fr", tit_limpio(x), re.I))


def tit_limpio(x):
    return re.sub(r"^[0-9a-f-]{36} ?-\s*", "", x.get("title") or "")


# Motivos de pérdida que significan «esto no era un lead»: si vuelve una señal
# suya, no se devuelve a la cola.
NO_ERA_LEAD = re.compile(r"autorespuesta|no es lead|cambio de email|duplicado|error de cualificaci", re.I)


def perdidos_recientes(dias=30):
    """email -> (id de trato, días desde la pérdida, motivo).

    Sin esto, un lead que el equipo acaba de dar por perdido sale de la lista
    de tratos abiertos y su señal antigua de Brevo o Smartlead lo devuelve a la
    cola al día siguiente como si fuera una oportunidad nueva (18/09: 6 de los
    12 WARM eran leads perdidos esa misma semana).
    """
    fuera = {}
    # Todos los perdidos del pipeline, no solo los que el título marca como
    # compraventa: el trato «SANFER CONSTRUCCIONES VENTA» es una venta perdida
    # y no lleva la palabra «compra» en el título.
    from panel_horario import deals_todos
    recientes = [x for x in deals_todos(estados=("lost",)) if x.get("pipeline_id") in PIPELINES]
    for x in recientes:
        lt = str(x.get("lost_time") or "")[:19]
        if not lt:
            continue
        d = dias_desde(lt)
        if d is None or d > dias:
            continue
        em = ((x.get("person_id") or {}).get("email") or [{}])[0].get("value", "").lower()
        if em and (em not in fuera or d < fuera[em][1]):
            fuera[em] = (x["id"], d, (x.get("lost_reason") or "sin motivo").strip())
    return fuera


def construir(dias=60):
    inv = stock()
    nombres_etapa = etapas()
    abiertos = [x for x in deals("open")
                if not es_trato_de_prueba(x) and not es_trato_de_escaner(x)]
    perdidos = perdidos_recientes()
    print("Pipedrive: %d perdidos en los últimos 30 días (no vuelven a la cola como nuevos)" % len(perdidos), flush=True)
    print("Pipedrive: %d tratos abiertos de compraventa" % len(abiertos), flush=True)
    tiempos = tiempos_embudo(abiertos)
    print("tiempos del embudo calculados", flush=True)
    en_crm = {((x.get("person_id") or {}).get("email") or [{}])[0].get("value", "").lower()
              for x in abiertos if x.get("person_id")}
    filas = []
    for x in abiertos:
        filas.append(fila_crm(x, inv, nombres_etapa))
    print("filas CRM: %d" % len(filas), flush=True)
    try:
        clics = clics_brevo(dias)
    except RuntimeError as err:
        print("[Brevo no disponible: %s · la cola sale sin los clics ABM]" % err)
        clics = {}
    n_brevo = 0
    for g in clics.values():
        if not email_valido(g["email"]):
            continue          # el propio equipo clicando en sus campañas no es un lead
        if es_escaner_conocido(g["email"]):
            continue          # antivirus de correo confirmado por BBDD
        if g["email"] in en_crm:
            continue
        perd = perdidos.get(g["email"])
        if perd and NO_ERA_LEAD.search(perd[2]):
            continue          # ya se marcó como «no era un lead»: no vuelve
        filas.append(fila_fuera_crm(g["email"], "Brevo · clic campaña ABM", g["maquinas"], g["listas"],
                                    g["campanas"], g["ultima"], dict(clics=g["clics"]), inv, perdido=perd))
        n_brevo += 1
    frio, ir = senales_smartlead(dias)
    n_frio = 0
    for em, s in frio.items():
        if em in en_crm:
            continue
        resp = "respuesta_frio" in s["senales"]
        texto = ""
        if resp:
            try:
                texto = ir.texto_respuesta(em)
            except Exception:
                texto = ""
            if ir.clasificar(texto) in ("rechazo", "autoreply", "cambio_email"):
                continue
        if not email_valido(em) or es_escaner_conocido(em):
            continue
        if EXCLUIR.search(" ".join((s.get("empresa") or "", em))):
            continue
        perd = perdidos.get(em)
        if perd and NO_ERA_LEAD.search(perd[2]):
            continue
        canal = "Smartlead · respuesta frío" if resp else "Smartlead · clic frío"
        f = fila_fuera_crm(em, canal, [texto[:80]] if texto else [], set(), {"Frío Madrid"}, "",
                           dict(respuesta=resp, clics=s["senales"].count("clic_frio")), inv, perdido=perd)
        if s.get("empresa") and f[7] == "—":
            f[7] = s["empresa"]
        filas.append(f)
        n_frio += 1
    print("Brevo fuera del CRM: %d · Smartlead fuera del CRM: %d" % (n_brevo, n_frio))
    filas.sort(key=lambda f: -f[0])
    cab = [["COLA COMERCIAL · %s · todos los canales" %
            dt.datetime.now(dt.timezone(dt.timedelta(hours=2))).strftime("%d/%m/%Y %H:%M")],
           ["Ordenada por probabilidad de venta. Pipedrive es la fuente de verdad: lo que no está en el CRM aparece como «Fuera del CRM» para que se meta."],
           []] + tiempos + [[], CABECERA]
    return cab + filas


def formatear(pestana="Cola comercial", fila_cab=9, ncol=len(CABECERA)):
    """Negrita en cabeceras, primera columna fija, anchos razonables, sin desbordar."""
    tk = token_google(["https://www.googleapis.com/auth/spreadsheets"])
    cab = {"Authorization": "Bearer " + tk, "Content-Type": "application/json"}
    meta = sheets("%s?fields=sheets.properties" % SHEET_ID, cab=cab)
    sid = next((sh["properties"]["sheetId"] for sh in meta.get("sheets", [])
                if sh["properties"]["title"] == pestana), None)
    if sid is None:
        return
    anchos = [55, 95, 190, 170, 140, 110, 150, 200, 170, 120, 210, 260, 150, 120, 300, 180, 90, 300, 80, 80, 80, 240, 300, 70]
    req = [
        {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1},
                        "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "fontSize": 13}}},
                        "fields": "userEnteredFormat.textFormat"}},
        {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": 3, "endRowIndex": 4},
                        "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                        "fields": "userEnteredFormat.textFormat"}},
        {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": fila_cab - 1, "endRowIndex": fila_cab},
                        "cell": {"userEnteredFormat": {"textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                                                       "backgroundColor": {"red": 0.13, "green": 0.13, "blue": 0.13},
                                                       "wrapStrategy": "WRAP", "verticalAlignment": "MIDDLE"}},
                        "fields": "userEnteredFormat(textFormat,backgroundColor,wrapStrategy,verticalAlignment)"}},
        {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": fila_cab, "endColumnIndex": ncol},
                        "cell": {"userEnteredFormat": {"wrapStrategy": "CLIP", "verticalAlignment": "TOP"}},
                        "fields": "userEnteredFormat(wrapStrategy,verticalAlignment)"}},
        {"updateSheetProperties": {"properties": {"sheetId": sid, "gridProperties": {"frozenRowCount": fila_cab, "frozenColumnCount": 2}},
                                   "fields": "gridProperties(frozenRowCount,frozenColumnCount)"}},
    ] + [{"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1},
                                        "properties": {"pixelSize": w}, "fields": "pixelSize"}}
         for i, w in enumerate(anchos)]
    r = sheets("%s:batchUpdate" % SHEET_ID, "POST", {"requests": req}, cab)
    print("formato:", "OK" if "_error" not in r else r)


if __name__ == "__main__":
    ausentes = falta("pipedrive_key")
    if ausentes:
        raise SystemExit("COLA NO ACTUALIZADA · faltan credenciales: " + ", ".join(ausentes))
    dias = next((int(a) for a in sys.argv[1:] if a.isdigit()), 60)
    filas = construir(dias)
    for f in filas[:40]:
        print(" | ".join(str(x) for x in f)[:230])
    print("\n(%d oportunidades en la cola)" % (len(filas) - 9))
    if "--sheet" in sys.argv:
        subir(filas, "Cola comercial")
        formatear("Cola comercial", fila_cab=9)

#!/usr/bin/env python3
"""Perfila a los clientes rastreando su propia web: sector, provincia, CIF y tamaño.

Pipedrive tiene vacíos el sector, el tamaño y la provincia de las 2.313 fichas de
empresa. Esto lo rellena sin gastar saldo de ningún servicio: visita la web del
cliente (el dominio sale de su correo), lee la home y el aviso legal, y de ahí
saca a qué se dedica, dónde está y cómo de grande es.

Solo descarga páginas públicas. No escribe en Pipedrive ni en ninguna fuente:
deja el resultado en leads/perfil_clientes.json (carpeta ignorada por git).

Uso:
    python3 scripts/perfil_clientes_web.py <fichero_entrada.json> [hilos]
"""
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

NAVEGADOR = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
RUTAS = ("", "/quienes-somos", "/nosotros", "/empresa", "/about", "/servicios",
         "/aviso-legal", "/legal", "/contacto")
CIF = re.compile(r"\b([ABCDEFGHJNPQRSUVW]-?\d{7}-?[0-9A-J]|\d{8}-?[A-Z])\b")
CP = re.compile(r"\b(0[1-9]|[1-4]\d|5[0-2])\d{3}\b")
TEL = re.compile(r"(?:\+34[\s.-]?)?[6789]\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}")
EMPLEADOS = re.compile(r"(?:m[áa]s de\s+|cerca de\s+|equipo de\s+|plantilla de\s+|somos\s+)(\d{2,4})\s*"
                       r"(?:profesionales|trabajadores|empleados|personas|t[ée]cnicos)", re.I)
FLOTA = re.compile(r"(?:flota de\s+|m[áa]s de\s+)(\d{2,4})\s*(?:m[áa]quinas|equipos|veh[íi]culos|camiones)", re.I)
FUNDACION = re.compile(r"(?:desde|fundada en|en el año)\s+((?:19|20)\d{2})", re.I)

CP_PROV = {"01":"Álava","02":"Albacete","03":"Alicante","04":"Almería","05":"Ávila","06":"Badajoz","07":"Baleares",
"08":"Barcelona","09":"Burgos","10":"Cáceres","11":"Cádiz","12":"Castellón","13":"Ciudad Real","14":"Córdoba",
"15":"A Coruña","16":"Cuenca","17":"Girona","18":"Granada","19":"Guadalajara","20":"Gipuzkoa","21":"Huelva",
"22":"Huesca","23":"Jaén","24":"León","25":"Lleida","26":"La Rioja","27":"Lugo","28":"Madrid","29":"Málaga",
"30":"Murcia","31":"Navarra","32":"Ourense","33":"Asturias","34":"Palencia","35":"Las Palmas","36":"Pontevedra",
"37":"Salamanca","38":"S. C. Tenerife","39":"Cantabria","40":"Segovia","41":"Sevilla","42":"Soria","43":"Tarragona",
"44":"Teruel","45":"Toledo","46":"Valencia","47":"Valladolid","48":"Bizkaia","49":"Zamora","50":"Zaragoza",
"51":"Ceuta","52":"Melilla"}

# Sectores pensados para nuestro negocio: quién compra o alquila maquinaria.
# Orden importante: gana el primero que encaja, del más específico al más general.
SECTORES = [
    (r"alquiler de maquinaria|alquiler de plataformas|rental|rent a |alquilamos maquinaria|"
     r"parque de maquinaria en alquiler", "Alquiler de maquinaria"),
    (r"excavacion|movimiento de tierra|desmonte|explanacion|zanjas|terraplen", "Excavaciones y movimiento de tierras"),
    (r"demolicion|derribo|desguace de edificio", "Demoliciones"),
    (r"obra civil|infraestructura|carretera|urbanizacion|canalizacion|ferroviari|puente|"
     r"saneamiento|conduccion", "Obra civil e infraestructuras"),
    (r"cantera|arido|mineri|extraccion de piedra|graver", "Canteras, áridos y minería"),
    (r"prefabricad|hormigon|cemento|ceramic|ladrillo|mortero", "Hormigón y prefabricados"),
    (r"fotovoltaic|solar|energia renovable|eolic|autoconsumo|parque solar", "Energía y solar"),
    (r"agricol|agrari|forestal|jardineria|paisajismo|viveros|ganader|olivar|vinedo|bodega",
     "Agrícola, forestal y jardinería"),
    (r"transporte|logistic|almacenaje|paqueteria|distribucion|flota de camiones|grua movil|gruas ",
     "Transporte y logística"),
    (r"naval|portuari|astillero|maritim", "Naval y portuario"),
    (r"instalacion|electricidad|electric|fontaneri|climatizacion|aire acondicionado|telecomunicacion|"
     r"fibra optica|ascensor", "Instalaciones y mantenimiento técnico"),
    (r"industria|fabrica|fabricacion|metalurgic|metalic|caldereri|manufactur|siderurgi|"
     r"planta de produccion|carpinteria metalica", "Industria y fabricación"),
    (r"reforma|rehabilitacion|interiorismo|pintura|impermeabiliza|aislamiento|fachada",
     "Reformas y rehabilitación"),
    (r"constructora|construccion|edificacion|promotora|promocion inmobiliaria|contrata de obra",
     "Construcción y edificación"),
    (r"evento|audiovisual|publicidad|rotul|escenari|espectacul|produccion|cine|teatro|feria|stand",
     "Eventos, audiovisual y publicidad"),
    (r"limpieza|residuo|reciclaje|gestion ambiental|saneamiento urbano|facility|mantenimiento integral",
     "Limpieza, residuos y facility"),
    (r"ayuntamiento|diputacion|consorcio|mancomunidad|generalitat|junta de|municipal|"
     r"\.gob\.es|sede electronica", "Administración pública"),
    (r"hotel|restaurante|camping|turism|inmobiliari|finca|apartament", "Hostelería e inmobiliario"),
    (r"maquinaria|repuesto|recambio|concesionario|venta de maquinaria|taller", "Venta y taller de maquinaria"),
]


def norm(s):
    s = unicodedata.normalize("NFD", (s or ""))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def bajar(url, timeout=12):
    """Descarga una página. Muchas webs de obra están mal configuradas: solo
    responden con www, tardan más de diez segundos o devuelven 403 al primer
    intento aunque la página exista. Todo eso se trata aquí, no fuera."""
    req = urllib.request.Request(url, headers={
        "user-agent": NAVEGADOR,
        "accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "accept-language": "es-ES,es;q=0.9",
        "accept-encoding": "gzip, deflate",
        "connection": "close"})
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        crudo, cab = r.read(400_000), r.headers
        r.close()
    except urllib.error.HTTPError as e:
        # Un 403 o un 406 suelen traer la página igual; solo un 404 o un 5xx
        # significan de verdad que ahí no hay nada que leer.
        crudo = e.read(400_000) if e.code in (401, 403, 406, 429) else b""
        cab = e.headers
        if not crudo:
            raise
    if (cab.get("Content-Encoding") or "").lower() in ("gzip", "deflate"):
        import gzip, zlib
        try:
            crudo = gzip.decompress(crudo)
        except Exception:
            try:
                crudo = zlib.decompress(crudo, -zlib.MAX_WBITS)
            except Exception:
                pass
    return crudo.decode("utf-8", "replace")


def texto_de(html):
    h = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", html or "", flags=re.S | re.I)
    h = re.sub(r"<[^>]+>", " ", h)
    h = h.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", h).strip()


def meta(html, campo):
    m = re.search(r'<meta[^>]+(?:name|property)=["\']%s["\'][^>]+content=["\']([^"\']{10,300})' % campo,
                  html or "", re.I)
    if not m:
        m = re.search(r'<meta[^>]+content=["\']([^"\']{10,300})["\'][^>]+(?:name|property)=["\']%s["\']' % campo,
                      html or "", re.I)
    return (m.group(1).strip() if m else "")


def sector_de(texto):
    t = norm(texto)
    for patron, etiqueta in SECTORES:
        if re.search(patron, t):
            return etiqueta
    return ""


def perfilar(c):
    dom = c["dominio"]
    out = dict(dominio=dom, web_ok=False, url="", sector="", actividad="", titulo="", provincia="", cp="",
               cif="", tel="", empleados="", flota="", desde="", paginas=0, error="")
    bases = ["https://" + dom, "https://www." + dom, "http://" + dom, "http://www." + dom]
    if dom.startswith("www."):
        bases = ["https://" + dom, "http://" + dom]
    for base in bases:
        html_total, vistas = "", 0
        for ruta in RUTAS:
            if vistas >= 3 or (vistas >= 1 and out["sector"] and out["cp"] and out["cif"]):
                break
            try:
                html = bajar(base + ruta)
            except urllib.error.HTTPError as e:
                if ruta == "":
                    out["error"] = "HTTP %s" % e.code
                continue
            except Exception as e:
                if ruta == "":
                    m = str(e)
                    if "Name or service not known" in m or "nodename nor servname" in m:
                        out["error"] = "el dominio ya no existe"
                    elif "timed out" in m.lower() or type(e).__name__ == "TimeoutError":
                        out["error"] = "no responde a tiempo"
                    elif "certificate" in m.lower() or "SSL" in m:
                        out["error"] = "certificado no válido"
                    else:
                        out["error"] = type(e).__name__
                continue
            vistas += 1
            out["web_ok"] = True
            html_total += " " + html
            if not out["titulo"]:
                m = re.search(r"<title[^>]*>(.{3,200}?)</title>", html, re.S | re.I)
                out["titulo"] = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
            if not out["actividad"]:
                out["actividad"] = meta(html, "description") or meta(html, "og:description")
            txt = texto_de(html)
            if not out["sector"]:
                out["sector"] = sector_de(" ".join([out["titulo"], out["actividad"], txt[:4000]]))
            if not out["cp"]:
                m = CP.search(txt)
                if m:
                    out["cp"] = m.group(0)
                    out["provincia"] = CP_PROV.get(m.group(0)[:2], "")
            if not out["cif"]:
                m = CIF.search(txt)
                if m:
                    out["cif"] = m.group(1).replace("-", "")
            if not out["tel"]:
                m = TEL.search(txt)
                if m:
                    out["tel"] = m.group(0)
            for campo, patron in (("empleados", EMPLEADOS), ("flota", FLOTA), ("desde", FUNDACION)):
                if not out[campo]:
                    m = patron.search(txt)
                    if m:
                        out[campo] = m.group(1)
        out["paginas"] = vistas
        if out["web_ok"]:
            out["url"] = base
            out["error"] = ""
            break
    if out["web_ok"] and not out["sector"]:
        out["sector"] = sector_de(texto_de(html_total)[:12000]) or "Sin sector claro en su web"
    return out


def main():
    entrada = sys.argv[1]
    hilos = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    datos = json.load(open(entrada))
    doms = {}
    for c in datos:
        d = (c.get("dominio") or "").strip().lower()
        if d and "." in d and d not in doms:
            doms[d] = dict(dominio=d)
    print("dominios a rastrear:", len(doms), file=sys.stderr)
    res = []
    with ThreadPoolExecutor(max_workers=hilos) as pool:
        for i, r in enumerate(pool.map(perfilar, doms.values()), 1):
            res.append(r)
            if i % 25 == 0:
                print("  ", i, "de", len(doms), file=sys.stderr)
    os.makedirs("leads", exist_ok=True)
    salida = os.path.join("leads", "perfil_clientes.json")
    json.dump(res, open(salida, "w"), ensure_ascii=False, indent=1)
    ok = sum(1 for r in res if r["web_ok"])
    print("web viva: %d de %d · con sector: %d · con provincia: %d · con CIF: %d"
          % (ok, len(res), sum(1 for r in res if r["sector"] and r["sector"] != "Sin sector claro en su web"),
             sum(1 for r in res if r["provincia"]), sum(1 for r in res if r["cif"])))
    print("guardado en", salida)


if __name__ == "__main__":
    main()

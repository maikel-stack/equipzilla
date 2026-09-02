#!/usr/bin/env python3
"""Genera los emails del lanzamiento semanal de stock: elevación y
movimiento de tierras, cada uno con su email principal y su seguimiento.

Las fichas usan el panel de datos oscuro (sin fotos: las de los proveedores
llevan marca y no pueden llegar al cliente; cuando haya fotos retocadas se
añaden encima del panel). Precios sin tachar: no hay «antes» real y nunca
se inventa. Orden ascendente de precio: el gancho abre y el caro cierra.

Salida: campanas/lanzamiento-{elevacion,movimiento}[-f2].html
"""
import html as htmllib
import os
import urllib.parse

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "campanas")
TEAL, OSCURO, TINTA, TINTA2, LINEA = "#387E7F", "#17323A", "#14181C", "#3A424E", "#D9DEE4"
# Fotos limpias de proveedor, servidas por commit fijo para que no caduquen
CDN_FOTOS = ("https://cdn.jsdelivr.net/gh/maikel-stack/equipzilla"
             "@389cd51d91ae9fb8ab1899fb32cd03c8cac25d9e/email_assets/machines/")
WA = "34606836581"
NOTA_PRECIO = "Unidad revisada · IVA y transporte no incluidos"

GRUPOS = {
  "elevacion": dict(
    asunto="5 plataformas recién entradas · tijera desde 3.000 €",
    titular="Cinco plataformas recién entradas",
    entrada="De 8 a 20 metros de altura de trabajo, en eléctrica, diésel y "
            "camión. <strong>Acaban de entrar</strong> y salen con el precio "
            "puesto delante — el que llega primero, elige primero.",
    eyebrow="Elevación · recién entradas",
    asunto_f2="¿Cuál de las cinco te encaja?",
    maquinas=[
      dict(etq="Tijera eléctrica", titulo="JLG 1930ES", foto="EL-JLG1930ES-2025.jpg", precio="3.000 €",
           datos=[("Altura de trabajo", "8 m"), ("Año", "2008"), ("Energía", "eléctrica")],
           texto="La tijera de interior de toda la vida. Para mantenimiento, "
                 "instalaciones y almacén. El precio de entrada del lote."),
      dict(etq="Articulada eléctrica", titulo="Genie Z-30/20N RJ", foto="EL-GENIEZ3020-2025.jpg", precio="6.500 €",
           datos=[("Altura de trabajo", "11 m"), ("Año", "2010"), ("Horas", "1.206"), ("Energía", "eléctrica")],
           texto="Articulada eléctrica compacta: interior y suelos delicados, "
                 "con alcance para esquivar obstáculos."),
      dict(etq="Articulada diésel", titulo="Haulotte HA20PX", foto="EL-HA20PX10-2025.jpg", precio="17.500 €",
           datos=[("Altura de trabajo", "20 m"), ("Año", "2010"), ("Horas", "3.968"), ("Tracción", "4x4 diésel")],
           texto="La todoterreno de 20 metros más pedida de nuestra base. "
                 "Obra, fachada e industria."),
      dict(etq="Articulada eléctrica", titulo="Manitou 170 AETJL", foto="GAM-MANITOU170-2025.jpg", precio="20.500 €",
           datos=[("Altura de trabajo", "17 m"), ("Año", "2015"), ("Energía", "eléctrica")],
           texto="La máquina más consultada de nuestras últimas campañas. "
                 "17 metros eléctricos, lista para trabajar."),
      dict(etq="Camión plataforma", titulo="Iveco Multitel 160 ALU DS", foto="EL-MULTITEL160-2025.jpg", precio="27.000 €",
           datos=[("Altura de trabajo", "16 m"), ("Año", "2011"), ("Sobre", "camión diésel · carné B")],
           texto="Plataforma sobre camión: llegas, estabilizas y trabajas. "
                 "Sin góndola ni transporte especial entre obras."),
    ]),
  "movimiento": dict(
    asunto="Miniexcavadoras 2023 con pocas horas · desde 18.500 €",
    titular="Movimiento de tierras: cinco unidades recién entradas",
    entrada="Cuatro del 2023 y un dumper del 2021, todas con "
            "<strong>pocas horas</strong> y revisadas. Del tamaño que más se "
            "pide: compactas para obra urbana y jardín.",
    eyebrow="Movimiento de tierras · recién entradas",
    asunto_f2="La Doosan del 23 tiene 40 horas — ¿te cuento más?",
    maquinas=[
      dict(etq="Miniexcavadora 1,7 t", titulo="Kubota U 17-3N VHG AT", foto="MT-KU17-2025.jpg", precio="18.500 €",
           datos=[("Año", "2023"), ("Horas", "950"), ("Peso", "1,7 t")],
           texto="La mini que cabe por una puerta. Zanjas, reformas y obra "
                 "urbana, con la fiabilidad Kubota."),
      dict(etq="Dumper de ruedas", titulo="Wacker Neuson 1601", foto="MT-WN1601-2025.jpg", precio="18.500 €",
           datos=[("Año", "2021"), ("Horas", "900"), ("Carga", "1,6 t")],
           texto="El compañero de la mini: saca tierra y mueve material sin "
                 "castigar la obra."),
      dict(etq="Minicargadora", titulo="Bobcat S70", foto="MT-BOBS70-2025.jpg", precio="23.500 €",
           datos=[("Año", "2023"), ("Horas", "350"), ("Ancho", "compacta")],
           texto="La Bobcat pequeña de verdad: pasa por donde ninguna otra y "
                 "con solo 350 horas."),
      dict(etq="Miniexcavadora 3,8 t", titulo="Kubota U 36-4 GL", foto="KB313-2025.jpg", precio="32.500 €",
           datos=[("Año", "2023"), ("Horas", "900"), ("Peso", "3,8 t")],
           texto="La 3,8 toneladas del 23: tamaño serio con consumo de mini. "
                 "De las más consultadas de nuestra base."),
      dict(etq="Miniexcavadora 3,5 t", titulo="Doosan DX 35 Z-7", foto="MT-DX35Z-2025.jpg", precio="45.500 €",
           datos=[("Año", "2023"), ("Horas", "40"), ("Peso", "3,5 t · giro cero")],
           texto="Prácticamente nueva: 40 horas. Giro cero para trabajar "
                 "pegado a pared, con precio de usado."),
    ]),
}


def ficha(p, primera=False):
    filas = "".join(
        f'<tr><td style="padding:5px 0; font-size:12.5px; color:#9FC4C0; width:44%; vertical-align:top;">{htmllib.escape(k)}</td>'
        f'<td style="padding:5px 0; font-size:13px; color:#FFFFFF; font-weight:600; vertical-align:top;">{htmllib.escape(v)}</td></tr>'
        for k, v in p["datos"])
    wa = "https://wa.me/" + WA + "?text=" + urllib.parse.quote(
        f"Hola, me interesa la {p['titulo']} de {p['precio']}")
    borde = f"box-shadow:0 0 0 2px {TEAL};" if primera else ""
    foto = ""
    if p.get("foto"):
        foto = (f'<tr><td style="padding:0; background:#EDF1F4; line-height:0; font-size:0;">'
                f'<img class="pimg" src="{CDN_FOTOS}{p["foto"]}" alt="{htmllib.escape(p["titulo"])}" '
                f'width="534" style="width:100%; max-width:534px; height:auto; display:block;"></td></tr>')
    return f'''
      <td class="px" style="padding:{'22px' if primera else '14px'} 32px 6px; background:#FBFCFD;">
        <table role="presentation" width="100%" style="table-layout:fixed; border-collapse:separate; background:#FFFFFF; border:1px solid {LINEA}; border-radius:10px; overflow:hidden; {borde}"><tbody>
          {foto}<tr><td style="padding:20px 22px 18px; background:{OSCURO};">
            <div style="font-family:'IBM Plex Mono',monospace; font-size:10.5px; letter-spacing:0.12em; text-transform:uppercase; color:#8FD3C0; margin-bottom:8px;">{htmllib.escape(p["etq"])}</div>
            <div class="arx" style="font-size:20px; font-weight:700; color:#FFFFFF; line-height:1.28; margin-bottom:14px;">{htmllib.escape(p["titulo"])}</div>
            <table role="presentation" width="100%" style="border-collapse:collapse; border-top:1px solid rgba(255,255,255,.14);"><tbody>{filas}</tbody></table>
          </td></tr>
          <tr><td style="padding:18px 22px 20px;">
            <p style="margin:0 0 14px; font-size:14px; line-height:1.65; color:#4A5560;">{p["texto"]}</p>
            <div class="arx" style="font-size:28px; font-weight:700; color:{TINTA}; line-height:1;">{p["precio"]}</div>
            <div style="font-size:11.5px; color:#8A94A0; margin-top:4px;">{NOTA_PRECIO}</div>
            <div style="height:15px; line-height:15px; font-size:0;">&nbsp;</div>
            <table role="presentation" width="100%" style="border-collapse:collapse;"><tbody><tr><td align="center" style="background:{TEAL}; border-radius:8px;">
              <a href="{wa}" style="display:block; padding:13px 20px; font-family:'Archivo',system-ui,sans-serif; font-size:15px; font-weight:600; color:#FFFFFF; text-align:center;">Me interesa &mdash; escr&iacute;beme por WhatsApp</a>
            </td></tr></tbody></table>
          </td></tr>
        </tbody></table>
      </td>'''


CABECERA = '''<!DOCTYPE html>
<html lang="es" xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="X-UA-Compatible" content="IE=edge"><meta name="x-apple-disable-message-reformatting">
<meta name="color-scheme" content="light"><meta name="supported-color-schemes" content="light">
<title>__TITULO__ &middot; Equipzilla</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
* { box-sizing:border-box; } html, body { margin:0; padding:0; } body { background:#E4E9EE; }
.arx { font-family:'Archivo', system-ui, sans-serif; font-stretch:125%; }
img { border:0; outline:none; text-decoration:none; -ms-interpolation-mode:bicubic; }
a { text-decoration:none; }
@media only screen and (max-width:620px) {
  .container { width:100% !important; }
  .px { padding-left:14px !important; padding-right:14px !important; }
  h1 { font-size:22px !important; line-height:1.28 !important; }
  img { max-width:100% !important; height:auto !important; }
  table { max-width:100% !important; table-layout:fixed !important; }
}
</style></head>'''


def construir(g):
    fichas = "".join(f"<tr>{ficha(m, primera=(i == 0))}</tr>"
                     for i, m in enumerate(g["maquinas"]))
    return CABECERA.replace("__TITULO__", htmllib.escape(g["titular"])) + f'''
<body style="margin:0; padding:0; background:#E4E9EE;">
<div style="background:#E4E9EE; padding:24px 10px; font-family:'IBM Plex Sans',system-ui,sans-serif; color:{TINTA}; -webkit-font-smoothing:antialiased;">
  <div style="display:none; max-height:0; overflow:hidden; opacity:0; color:#E4E9EE; font-size:1px; line-height:1px;">Unidades revisadas recien entradas, con el precio publicado. El que llega primero, elige primero.</div>
  <table role="presentation" width="100%" class="container" style="width:100%; max-width:600px; margin:0 auto; border-collapse:collapse; background:#FBFCFD; border:1px solid {LINEA}; box-shadow:0 1px 2px rgba(18,22,28,.06),0 12px 40px rgba(18,22,28,.10);"><tbody>
    <tr><td style="height:5px; background:{TEAL}; padding:0; line-height:0; font-size:0;">&nbsp;</td></tr>
    <tr><td class="px" style="padding:22px 32px 20px; background:#FFFFFF; border-bottom:1px solid #EEF1F4;">
      <table role="presentation" width="100%" style="border-collapse:collapse;"><tbody><tr>
        <td style="vertical-align:middle;"><img src="https://cdn.jsdelivr.net/gh/maikel-stack/equipzilla@7f009ffee577abee39b7cc1e08a2914606b4cdf6/email_assets/equipzilla-logo.png" alt="Equipzilla" style="height:30px; width:auto; display:block;"></td>
        <td style="vertical-align:middle; text-align:right; font-family:'IBM Plex Mono',monospace; font-size:11px; letter-spacing:0.1em; text-transform:uppercase; color:#667085;">{g["eyebrow"]}</td>
      </tr></tbody></table>
    </td></tr>
    <tr><td class="px" style="padding:30px 32px 4px; background:#FBFCFD;">
      <div style="font-family:'IBM Plex Mono',monospace; font-size:11px; letter-spacing:0.14em; font-weight:500; color:{TEAL}; text-transform:uppercase; margin-bottom:10px;">Reci&eacute;n entradas &middot; precio cerrado</div>
      <h1 class="arx" style="margin:0 0 12px; font-size:25px; line-height:1.25; letter-spacing:-0.01em; color:{TINTA}; font-weight:700;">{htmllib.escape(g["titular"])}</h1>
      <p style="margin:0; font-size:15px; line-height:1.7; color:{TINTA2};">{g["entrada"]} Todas con <strong>inspecci&oacute;n y prueba presencial</strong> antes de comprar, fotos reales de la unidad y transporte confirmado antes de que decidas.</p>
    </td></tr>
    {fichas}
    <tr><td class="px" style="padding:22px 32px 6px; background:#FBFCFD;">
      <table role="presentation" width="100%" style="border-collapse:collapse; background:#EFF4F4; border:1px solid #D9E2E2; border-radius:10px;"><tbody><tr><td style="padding:18px 20px;">
        <div class="arx" style="font-size:15px; font-weight:700; color:{OSCURO}; margin-bottom:10px;">&iquest;No encaja ninguna?</div>
        <p style="margin:0; font-size:14px; line-height:1.6; color:{TINTA2};">Dinos qu&eacute; m&aacute;quina buscas &mdash; modelo, presupuesto y zona &mdash; y <strong>te avisamos en cuanto entre una que encaje</strong>. Responde a este correo y listo.</p>
      </td></tr></tbody></table>
    </td></tr>
    <tr><td class="px" style="padding:24px 32px 26px; background:#FBFCFD;">
      <table role="presentation" width="100%" style="border-collapse:collapse; border-top:1px solid #E6EAEF;"><tbody><tr><td style="padding-top:18px;">
        <div class="arx" style="font-size:15px; font-weight:600; color:{TINTA};">David Devis</div>
        <div style="font-size:13px; color:#667085; margin-bottom:8px;">Director de Desarrollo de Negocio &middot; Equipzilla</div>
        <div style="font-size:13.5px; line-height:1.7; color:{TINTA2};">
          <a href="tel:+34606836581" style="color:{TEAL}; font-weight:600;">606 836 581</a> &nbsp;&middot;&nbsp;
          <a href="mailto:clientes@equipzilla.com" style="color:{TEAL}; font-weight:600;">clientes@equipzilla.com</a>
        </div>
      </td></tr></tbody></table>
    </td></tr>
    <tr><td class="px" style="padding:18px 32px 22px; background:#F2F5F7; border-top:1px solid #E6EAEF;">
      <p style="margin:0; font-size:11.5px; line-height:1.6; color:#8A94A0; text-align:center;">
        Recibes este correo porque est&aacute;s en nuestra base de clientes y contactos de Equipzilla.<br>
        <a href="{{{{ unsubscribe }}}}" style="color:#8A94A0; text-decoration:underline;">Darse de baja</a></p>
    </td></tr>
  </tbody></table>
</div></body></html>'''


def construir_f2(g):
    """Seguimiento a +4 días: corto, en texto plano de David, para no-abridores
    y abridores sin clic."""
    lineas = "".join(
        f'<tr><td style="padding:7px 0; font-size:14.5px; color:{TINTA};">'
        f'<strong>{htmllib.escape(m["titulo"])}</strong> &mdash; {htmllib.escape(m["datos"][0][1])} '
        f'&middot; {htmllib.escape(m["precio"])}</td></tr>'
        for m in g["maquinas"])
    return CABECERA.replace("__TITULO__", htmllib.escape(g["asunto_f2"])) + f'''
<body style="margin:0; padding:0; background:#FFFFFF;">
<div style="max-width:560px; margin:0 auto; padding:28px 20px; font-family:'IBM Plex Sans',system-ui,sans-serif; color:{TINTA}; font-size:15px; line-height:1.7;">
  <p style="margin:0 0 14px;">Hola:</p>
  <p style="margin:0 0 14px;">Hace unos d&iacute;as te pas&eacute; las unidades que acaban de entrar. Te las dejo en una l&iacute;nea cada una, por si el otro correo se te escap&oacute;:</p>
  <table role="presentation" width="100%" style="border-collapse:collapse; margin:0 0 16px;"><tbody>{lineas}</tbody></table>
  <p style="margin:0 0 14px;">Todas con inspecci&oacute;n y prueba presencial antes de comprar. Si alguna te encaja &mdash; o buscas otra cosa &mdash; <strong>resp&oacute;ndeme a este correo o esc&iacute;beme al 606&nbsp;836&nbsp;581</strong> y te digo disponibilidad y transporte a tu zona.</p>
  <p style="margin:0 0 4px;">Un saludo,</p>
  <p style="margin:0; font-weight:600;">David Devis<br>
  <span style="font-weight:400; color:#667085; font-size:13px;">Director de Desarrollo de Negocio &middot; Equipzilla &middot; 606 836 581</span></p>
  <p style="margin:22px 0 0; font-size:11.5px; color:#8A94A0;"><a href="{{{{ unsubscribe }}}}" style="color:#8A94A0;">Darse de baja</a></p>
</div></body></html>'''


if __name__ == "__main__":
    os.makedirs(SALIDA, exist_ok=True)
    for nombre, g in GRUPOS.items():
        for sufijo, html in (("", construir(g)), ("-f2", construir_f2(g))):
            ruta = os.path.join(SALIDA, f"lanzamiento-{nombre}{sufijo}.html")
            with open(ruta, "w") as f:
                f.write(html)
            print(ruta)
        print(f"  asunto: {g['asunto']}  |  f2: {g['asunto_f2']}")

#!/usr/bin/env python3
"""Generador de guías SEO de precios desde el stock real (data/machines.json).

Produce quiz/guias/<slug>.html para cada categoría + el índice /guias/.
Al cambiar el stock, volver a ejecutar y las tablas de precios se actualizan.
Regla editorial: ningún dato inventado — precios y specs salen del catálogo;
el contexto de mercado se expresa siempre sobre "nuestro stock actual".
"""
import datetime
import json
import os
import statistics

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "quiz", "guias")
MACHINES = json.load(open(os.path.join(ROOT, "data", "machines.json")))
HOY = datetime.date.today().strftime("%B %Y").replace("January", "enero").replace("February", "febrero").replace("March", "marzo").replace("April", "abril").replace("May", "mayo").replace("June", "junio").replace("July", "julio").replace("August", "agosto").replace("September", "septiembre").replace("October", "octubre").replace("November", "noviembre").replace("December", "diciembre")
BASE = "https://equipzilla-quiz.vercel.app"

GUIAS = {
    "precio-miniexcavadora-segunda-mano": {
        "cat": "mini", "label": "Miniexcavadora (hasta 8 t)",
        "kw": "miniexcavadora segunda mano precio",
        "title": "Precio de una miniexcavadora de segunda mano en {hoy}: tabla real",
        "h1": "¿Cuánto cuesta una miniexcavadora de segunda mano?",
        "answer": "Una miniexcavadora de ocasión reciente cuesta entre {pmin} y {pmax} + IVA según tonelaje, año y horas. En el rango más habitual (2,5-4 t, pocas horas), los precios de nuestro stock se mueven alrededor de {pmed}. Abajo tienes la tabla completa con unidades reales.",
        "factores": [
            ("Tonelaje", "Es el factor nº 1 del precio: una 1 t vale la mitad que una 3 t, y una 8 t puede triplicarla. Compra el tamaño que exige tu trabajo, no el catálogo."),
            ("Horas de uso", "Por debajo de 1.500 h una mini está 'rodada'; entre 1.500 y 3.000 h sigue siendo buena compra si el mantenimiento está documentado."),
            ("Año y normativa", "Unidades de 2022-2024 conservan garantías de cadena de suministro y repuestos inmediatos."),
            ("Extras", "Giro cero, pluma ajustable o cazos adicionales suben el precio pero también la reventa."),
        ],
        "faq": [
            ("¿Cuántas horas son muchas para una miniexcavadora?", "Depende del mantenimiento, pero como referencia: menos de 1.500 h es poco uso, 1.500-3.000 h es uso normal con buena vida por delante, y a partir de 5.000 h conviene una inspección a fondo (motor, bombas, bulones y cadenas)."),
            ("¿Miniexcavadora nueva o de segunda mano?", "Una mini nueva pierde en torno al 20-30% de valor en sus primeros dos años. Una unidad de 2023 con 700 h ofrece prácticamente la misma vida útil por bastante menos dinero."),
            ("¿Qué garantía tiene una miniexcavadora usada de Equipzilla?", "Casi todas nuestras unidades tienen opción de garantía, contrato de mantenimiento y financiación. Todas se entregan revisadas, con inspección y prueba presencial."),
        ],
    },
    "precio-carretilla-elevadora-segunda-mano": {
        "cat": "carr", "label": "Carretilla elevadora",
        "kw": "carretilla elevadora segunda mano precio",
        "title": "Precio de una carretilla elevadora de segunda mano en {hoy}",
        "h1": "¿Cuánto cuesta una carretilla elevadora de segunda mano?",
        "answer": "Una carretilla elevadora de ocasión cuesta entre {pmin} y {pmax} + IVA según capacidad, energía (eléctrica, diésel o GLP) y horas. Las eléctricas de 1,5-2,5 t — las más demandadas para almacén — se mueven en nuestra gama alrededor de {pmed}.",
        "factores": [
            ("Eléctrica, diésel o GLP", "Para interior (almacén, alimentación, farma) la eléctrica es obligada: sin humos y menos mantenimiento. Para exterior intensivo, térmica."),
            ("Capacidad y mástil", "No compres solo por capacidad nominal: al elevar el mástil o con cargas descentradas la capacidad real baja. Verifica la placa de cargas."),
            ("Horas", "Las carretillas aguantan muchas horas si la batería/motor está cuidado. En eléctricas, el estado de la batería puede valer más que el horómetro."),
            ("Estado de la batería (eléctricas)", "Una batería nueva puede costar varios miles de euros: pide siempre el informe de carga."),
        ],
        "faq": [
            ("¿Qué carretilla necesito para palets de 1.000-1.500 kg?", "Una carretilla de 1,6-2,5 t bien especificada cubre ese rango con margen para cargas descentradas. Si trabajas dentro y fuera, mira neumáticos superelásticos."),
            ("¿Cuántas horas dura una carretilla elevadora?", "Con mantenimiento correcto, 15.000-20.000 h no son raras en térmicas de gama industrial. Lo crítico es el historial, no solo la cifra."),
            ("¿Tenéis carretillas eléctricas de ocasión con garantía?", "Sí — con opción de garantía, contrato de mantenimiento y financiación, revisadas y con prueba presencial antes de comprar."),
        ],
    },
    "precio-plataforma-elevadora-usada": {
        "cat": "plat", "label": "Plataforma elevadora",
        "kw": "plataforma elevadora usada precio",
        "title": "Precio de una plataforma elevadora usada en {hoy}: tijera y articulada",
        "h1": "¿Cuánto cuesta una plataforma elevadora usada?",
        "answer": "Una plataforma elevadora de ocasión cuesta entre {pmin} y {pmax} + IVA según altura de trabajo y tipo (tijera o articulada, eléctrica o diésel). Una tijera eléctrica de 10 m parte de la banda baja; las articuladas de 17-20 m ocupan la banda alta.",
        "factores": [
            ("Altura de trabajo", "Compra la altura que necesitas alcanzar + 2 m de margen (la altura de trabajo ya suma la de la persona)."),
            ("Tijera vs articulada", "La tijera sube en vertical y da cesta grande; la articulada salva obstáculos y llega donde la vertical no puede."),
            ("Eléctrica vs diésel", "Interior = eléctrica (sin humos, suelos delicados). Exterior con terreno irregular = diésel con 4x4."),
            ("Normativa y revisiones", "Exige el historial de revisiones obligatorias al día: es tu seguridad y tu ITV."),
        ],
        "faq": [
            ("¿Plataforma de tijera o articulada?", "Tijera si trabajas en vertical sobre suelo firme (mantenimiento de naves, instalaciones). Articulada si necesitas salvar estanterías, máquinas u obstáculos, o acceso lateral."),
            ("¿Cuántos metros de plataforma necesito para naves industriales?", "La mayoría de naves logísticas se resuelven con 10-14 m de altura de trabajo. Para cubiertas o cerchas altas, 17-20 m articulada."),
            ("¿Las plataformas usadas pasan revisión?", "Las nuestras se entregan revisadas y con inspección presencial; casi todas con opción de garantía y contrato de mantenimiento."),
        ],
    },
    "precio-manipulador-telescopico-usado": {
        "cat": "tele", "label": "Manipulador telescópico",
        "kw": "manipulador telescópico usado precio",
        "title": "Precio de un manipulador telescópico usado en {hoy}",
        "h1": "¿Cuánto cuesta un manipulador telescópico usado?",
        "answer": "Un manipulador telescópico de ocasión cuesta entre {pmin} y {pmax} + IVA según alcance, capacidad y horas. Los de 12-15 m con capacidades de 3,5-5,5 t — el estándar de obra — ocupan la banda media-alta de nuestro stock, alrededor de {pmed}.",
        "factores": [
            ("Alcance y capacidad", "El binomio altura × carga define el precio. Piensa en tu carga típica en la punta, no solo la nominal."),
            ("Horas y uso previo", "Un telescópico de alquiler suele tener uso intenso: revisa pluma, cadenas internas y estabilizadores."),
            ("Implementos", "Horquillas, cazo y cesta homologada multiplican la utilidad de la misma máquina."),
            ("Año", "Unidades recientes (2022-2023) con pocas horas dan la mejor relación coste/vida útil."),
        ],
        "faq": [
            ("¿Para qué sirve un manipulador telescópico?", "Es la navaja suiza de obra: carga palets en altura, alimenta forjados, mueve material en terreno irregular y con implementos hace de plataforma o grúa ligera."),
            ("¿Cuántas horas son aceptables en un telescópico usado?", "Menos de 1.000 h es casi nuevo; hasta 4.000 h con mantenimiento documentado es compra segura; por encima, inspección a fondo de pluma y transmisión."),
            ("¿Ofrecéis garantía en telescópicos usados?", "Sí, casi todas las unidades tienen opción de garantía, contrato de mantenimiento y financiación."),
        ],
    },
    "precio-excavadora-usada": {
        "cat": "exca", "label": "Excavadora grande (14-23 t)",
        "kw": "excavadora usada precio",
        "title": "Precio de una excavadora usada (14-23 t) en {hoy}",
        "h1": "¿Cuánto cuesta una excavadora usada?",
        "answer": "Una excavadora de cadenas o ruedas de 14-23 t de ocasión cuesta entre {pmin} y {pmax} + IVA según tonelaje, horas y equipamiento (GPS 3D, cazos). Las unidades recientes con menos de 1.000 h ocupan la banda alta y son las que más rápido rotan.",
        "factores": [
            ("Tonelaje y tren de rodaje", "El tren de rodaje es el gran coste oculto: su desgaste puede suponer decenas de miles de euros. Exige fotos y medición."),
            ("Horas reales certificadas", "En máquinas grandes el horómetro manipulado existe: compra solo con horas certificadas y libro de mantenimiento."),
            ("Equipamiento", "GPS 3D (Topcon/Trimble), engrase centralizado o cazos de gran volumen cambian el precio y la productividad."),
            ("Cadenas vs ruedas", "Ruedas para obra urbana y desplazamientos; cadenas para producción pura en tajo."),
        ],
        "faq": [
            ("¿Cuántas horas puede tener una excavadora usada?", "Una excavadora de 20 t bien mantenida supera las 10.000 h. Para compra de ocasión, unidades con 800-3.500 h certificadas ofrecen la mejor vida útil restante por euro."),
            ("¿Merece la pena una excavadora con GPS 3D?", "Si haces movimiento de tierras con niveles, el GPS 3D ahorra replanteos y repasos: se paga solo en pocas obras."),
            ("¿Cómo sé que las horas son reales?", "En Equipzilla las horas se certifican y cada máquina pasa inspección y prueba presencial antes de la compra."),
        ],
    },
}

CAT_QUIZ_LABEL = {
    "mini": "Miniexcavadora (hasta 8 t)", "exca": "Excavadora grande (14-23 t)",
    "plat": "Plataforma elevadora", "carr": "Carretilla elevadora",
    "tele": "Manipulador telescópico", "pala": "Pala cargadora",
}


def eur(n):
    return f"{n:,.0f}".replace(",", ".") + " €"


def page(slug, g):
    ms = sorted([m for m in MACHINES if m["c"] == g["cat"]], key=lambda m: m["p"])
    ps = [m["p"] for m in ms]
    ctx = {"hoy": HOY, "pmin": eur(min(ps)), "pmax": eur(max(ps)),
           "pmed": eur(int(statistics.median(ps)))}
    title = g["title"].format(**ctx)
    answer = g["answer"].format(**ctx)

    rows = "".join(
        f'<tr><td><b>{m["n"]}</b></td><td>{m["y"]}</td><td>{m["s"]}</td>'
        f'<td>{f"{m [chr(104)]:,}".replace(",", ".") + " h" if m.get("h") else "a confirmar"}</td>'
        f'<td class="pr">{eur(m["p"])}</td></tr>'
        for m in ms)

    factores = "".join(
        f"<h3>{t}</h3><p>{d}</p>" for t, d in g["factores"])
    faqs_html = "".join(
        f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in g["faq"])
    faq_schema = json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}}
                       for q, a in g["faq"]]}, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | Equipzilla</title>
<meta name="description" content="{answer[:150].rsplit(' ', 1)[0]}…">
<link rel="canonical" href="{BASE}/guias/{slug}.html">
<script type="application/ld+json">{faq_schema}</script>
<style>
  :root{{--bg:#F5F8F8;--line:#DCE5E5;--ink:#14181C;--ink2:#4A5C5E;--ink3:#788B8D;--teal:#387E7F;--teal-soft:#E6EEEE;--brand:#F0523C;--wa:#25D366}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--bg);font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);line-height:1.6}}
  .top{{height:5px;background:var(--teal)}}
  .wrap{{max-width:680px;margin:0 auto;padding:26px 18px 50px}}
  .brand{{font-weight:800;font-size:21px;color:var(--brand)}}
  .brand a{{color:inherit;text-decoration:none}}
  .tag{{font-size:11.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink3);margin-bottom:24px}}
  h1{{font-size:28px;line-height:1.22;letter-spacing:-.015em;margin-bottom:12px}}
  .answer{{background:#fff;border-left:4px solid var(--teal);border-radius:0 10px 10px 0;padding:14px 16px;font-size:15.5px;margin-bottom:22px;box-shadow:0 1px 6px rgba(18,22,28,.05)}}
  h2{{font-size:20px;margin:30px 0 10px}}
  h3{{font-size:15.5px;margin:18px 0 4px}}
  p{{margin-bottom:10px;font-size:14.5px;color:#2A3438}}
  table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden;font-size:13.5px;margin:12px 0}}
  th{{background:#17323A;color:#fff;text-align:left;padding:9px 10px;font-size:12px}}
  td{{padding:9px 10px;border-bottom:1px solid #EEF1F4}}
  tr:last-child td{{border-bottom:none}}
  .pr{{font-weight:800;white-space:nowrap}}
  .note{{font-size:12px;color:var(--ink3)}}
  .alertbox{{background:var(--teal-soft);border:1.5px solid #CADCDC;border-radius:12px;padding:18px;margin:24px 0}}
  .alertbox .t{{font-weight:700;font-size:15px;margin-bottom:4px}}
  .alertbox .s{{font-size:13px;color:var(--ink2);margin-bottom:10px}}
  .alertbox form{{display:flex;gap:8px;flex-wrap:wrap}}
  .alertbox input{{flex:1;min-width:180px;border:1.5px solid var(--line);border-radius:10px;padding:11px 13px;font-size:14.5px;font-family:inherit}}
  .alertbox button{{border:none;border-radius:10px;background:var(--teal);color:#fff;font-weight:700;padding:11px 18px;font-size:14.5px;cursor:pointer;font-family:inherit}}
  .okmsg{{display:none;margin-top:8px;font-size:13px;color:#1E6B3C;font-weight:600}}
  .faq{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:4px 18px}}
  .faq details{{border-bottom:1px solid #EEF1F4;padding:12px 0}}
  .faq details:last-child{{border-bottom:none}}
  .faq summary{{font-weight:600;font-size:14.5px;cursor:pointer}}
  .faq p{{margin:8px 0 0;color:var(--ink2)}}
  .cta{{display:block;text-align:center;background:var(--wa);color:#fff;font-weight:700;border-radius:10px;padding:14px;text-decoration:none;margin:26px auto 0;max-width:420px}}
  .foot{{margin-top:34px;font-size:12.5px;color:var(--ink3);text-align:center}}
  a{{color:var(--teal)}}
</style>
</head>
<body>
<div class="top"></div>
<div class="wrap">
  <div class="brand"><a href="/">Equipzilla</a></div>
  <div class="tag"><a href="/guias/" style="color:inherit;text-decoration:none">Guías de compra</a> · actualizado {HOY}</div>

  <h1>{g["h1"]}</h1>
  <div class="answer">{answer}</div>

  <h2>Precios reales de nuestro stock ({HOY})</h2>
  <table>
    <thead><tr><th>Máquina</th><th>Año</th><th>Specs</th><th>Horas</th><th>Precio + IVA</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <p class="note">Unidades reales en venta al publicar esta guía — revisadas, con inspección y prueba presencial, y opción de garantía, contrato de mantenimiento y financiación en casi todas. El stock rota: consulta disponibilidad.</p>

  <div class="alertbox">
    <div class="t">🔔 Los precios cambian — te avisamos</div>
    <div class="s">Deja tu email y te escribimos solo cuando una {g["label"].lower()} baje de precio o entre una nueva en stock. Sin spam.</div>
    <form onsubmit="return ezAlert(this)">
      <input type="email" name="email" placeholder="tu@email.com" required>
      <button type="submit">Avisarme</button>
    </form>
    <div class="okmsg">✓ Alertas activadas — revisa tu email.</div>
  </div>

  <h2>Qué determina el precio</h2>
  {factores}

  <h2>¿No sabes qué modelo encaja con tu trabajo?</h2>
  <p>Cuéntaselo a nuestro <a href="{BASE}/">asesor de compra</a> (gratis, 1 minuto): dile qué necesitas
  hacer y te dice qué unidades de nuestro stock tienen sentido y por qué. Y si prefieres números,
  usa la <a href="{BASE}/alquilar-o-comprar-maquinaria.html">calculadora alquilar vs comprar</a>.</p>

  <h2>Preguntas frecuentes</h2>
  <div class="faq">{faqs_html}</div>

  <a class="cta" href="https://wa.me/34606836581?text=Hola,%20vengo%20de%20la%20gu%C3%ADa%20de%20precios%20de%20{g["label"].split("(")[0].strip().replace(" ", "%20")}%20y%20quiero%20informaci%C3%B3n">Consultar disponibilidad por WhatsApp</a>

  <div class="foot">Equipzilla · Barcelona · 911 238 750 · <a href="https://equipzilla.com">equipzilla.com</a> · Precios + IVA</div>
</div>
<script>
function ezAlert(f){{
  var em=f.email.value.trim();
  fetch("/api/subscribe",{{method:"POST",headers:{{"Content-Type":"application/json"}},
    body:JSON.stringify({{email:em,categoria:{json.dumps(CAT_QUIZ_LABEL[g["cat"]])}}})}})
    .then(function(){{ f.style.display="none"; f.parentNode.querySelector(".okmsg").style.display="block"; }});
  return false;
}}
</script>
<script src="/widget.js" defer></script>
</body>
</html>"""


def index_page(links):
    lis = "".join(
        f'<a class="card" href="/guias/{slug}.html"><b>{g["h1"]}</b>'
        f'<span>{g["kw"]} · actualizado {HOY}</span></a>'
        for slug, g in links.items())
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Guías de compra de maquinaria de ocasión | Equipzilla</title>
<meta name="description" content="Precios reales y guías de compra de maquinaria de segunda mano: miniexcavadoras, carretillas, plataformas, telescópicos y excavadoras. Actualizado {HOY}.">
<link rel="canonical" href="{BASE}/guias/">
<style>
  :root{{--bg:#F5F8F8;--line:#DCE5E5;--ink:#14181C;--teal:#387E7F;--brand:#F0523C}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--bg);font-family:system-ui,sans-serif;color:var(--ink);line-height:1.55}}
  .top{{height:5px;background:var(--teal)}}
  .wrap{{max-width:680px;margin:0 auto;padding:26px 18px 50px}}
  .brand{{font-weight:800;font-size:21px;color:var(--brand)}}
  .brand a{{color:inherit;text-decoration:none}}
  h1{{font-size:26px;margin:18px 0 6px}}
  p{{color:#4A5C5E;margin-bottom:20px}}
  .card{{display:block;background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin-bottom:12px;text-decoration:none;color:var(--ink)}}
  .card b{{display:block;font-size:16px}}
  .card span{{font-size:12.5px;color:#788B8D}}
  .card:hover{{border-color:var(--teal)}}
</style>
</head>
<body>
<div class="top"></div>
<div class="wrap">
  <div class="brand"><a href="/">Equipzilla</a></div>
  <h1>Guías de compra y precios de maquinaria de ocasión</h1>
  <p>Precios reales de nuestro stock, qué revisar antes de comprar y cuándo compensa comprar frente a alquilar.</p>
  {lis}
  <a class="card" href="/alquilar-o-comprar-maquinaria.html"><b>¿Alquilar o comprar? Calculadora de ahorro</b><span>alquilar o comprar maquinaria · herramienta interactiva</span></a>
</div>
<script src="/widget.js" defer></script>
</body>
</html>"""


def main():
    os.makedirs(OUT, exist_ok=True)
    for slug, g in GUIAS.items():
        open(os.path.join(OUT, slug + ".html"), "w").write(page(slug, g))
        print("✓", slug)
    open(os.path.join(OUT, "index.html"), "w").write(index_page(GUIAS))
    print("✓ index")
    # sitemap para cuando haya dominio propio
    urls = [f"{BASE}/", f"{BASE}/alquilar-o-comprar-maquinaria.html",
            f"{BASE}/guias/"] + [f"{BASE}/guias/{s}.html" for s in GUIAS]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n"
    open(os.path.join(ROOT, "quiz", "sitemap.xml"), "w").write(sm)
    print("✓ sitemap.xml")


if __name__ == "__main__":
    main()

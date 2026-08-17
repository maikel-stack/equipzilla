#!/usr/bin/env python3
"""Generador de guías SEO de precios (v2, estándar del Prompt Maestro).

Produce quiz/guias/<slug>.html desde el stock real (data/machines.json) con
diseño editorial premium y estructura: respuesta rápida → tabla de precios
reales → framework de decisión → errores comunes → consejo del asesor →
caso con números → lead magnet (fórmula de transición) → FAQ (schema) → CTA.

Regla editorial: ningún dato inventado. Precios y specs salen del catálogo;
los casos usan condicionales ("si pagas X €/mes de alquiler...").
Volver a ejecutar tras cambiar el stock: las tablas se regeneran.
"""
import datetime
import json
import os
import re
import statistics

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "quiz", "guias")
MACHINES = json.load(open(os.path.join(ROOT, "data", "machines.json")))
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
_h = datetime.date.today()
HOY = f"{MESES[_h.month - 1]} {_h.year}"
BASE = "https://equipzilla-quiz.vercel.app"

CAT_QUIZ_LABEL = {
    "mini": "Miniexcavadora (hasta 8 t)", "exca": "Excavadora grande (14-23 t)",
    "plat": "Plataforma elevadora", "carr": "Carretilla elevadora",
    "tele": "Manipulador telescópico", "pala": "Pala cargadora",
}


def eur(n):
    return f"{n:,.0f}".replace(",", ".") + " €"


# ─────────────────────────────────────────────────────────────────────────────
# Contenido editorial por guía (redacción experta; tokens {pmin} {pmax} {pmed}
# {n} se rellenan con el stock real)
# ─────────────────────────────────────────────────────────────────────────────
GUIAS = {
 "precio-miniexcavadora-segunda-mano": {
  "cat": "mini", "label": "miniexcavadora",
  "kw": "miniexcavadora segunda mano precio",
  "title": "Precio de una miniexcavadora de segunda mano ({hoy}): tabla con unidades reales",
  "h1": "¿Cuánto cuesta una miniexcavadora de segunda mano?",
  "stand": "Tabla de precios con unidades reales en venta, el método para elegir tonelaje sin equivocarte y los errores que más dinero cuestan al comprar una mini de ocasión.",
  "rapida": "Una miniexcavadora de segunda mano cuesta entre <b>{pmin}</b> y <b>{pmax}</b> + IVA según tonelaje, año y horas. El rango más demandado — 2,5 a 4 t con pocas horas — se mueve en torno a <b>{pmed}</b>. Por debajo de 1.500 h de uso, una mini reciente conserva la mayor parte de su vida útil: es donde está la mejor relación precio/vida restante.",
  "framework_t": "Cómo elegir tonelaje (método en 4 pasos)",
  "framework": [
   ("Dimensiona por el trabajo, no por el catálogo", "Ancho de acceso mínimo, profundidad de zanja habitual y altura de descarga sobre camión. Esas tres medidas eliminan la mitad de las opciones."),
   ("Pon el listón de horas según tu uso", "Para uso diario, busca menos de 1.500 h. Para uso regular, hasta 3.000 h con mantenimiento documentado sigue siendo compra segura."),
   ("Exige historial", "Libro de mantenimiento, facturas de taller y horas certificadas. Sin historial, el precio debe bajar — o la compra no debe hacerse."),
   ("Compara contra tu alquiler", "Multiplica tu cuota mensual por los meses de uso al año. Si el total a 3 años supera el precio de la máquina, estás pagando la máquina de otro."),
  ],
  "errores": [
   ("Quedarse corto de tonelaje por ahorrar", "Una mini al límite de su capacidad trabaja forzada, tarda más y se desgasta antes. El ahorro inicial se devuelve con intereses."),
   ("Ignorar el tren de rodaje", "Cadenas, rodillos y bulones son de lo más caro de reponer en una mini. Pide fotos del desgaste y descuenta su estado del precio."),
   ("Fiarse del horómetro sin historial", "Las horas sin documentación de respaldo son solo un número en una pantalla. Historial o inspección — mejor las dos cosas."),
  ],
  "consejo": "El tramo de 2,5-4 t es el más líquido del mercado: es el que más se compra, más se alquila y mejor se revende. Si tu trabajo lo permite, quedarte en ese rango te protege el día que quieras venderla o cambiarla.",
  "caso_t": "El cálculo que casi nadie hace",
  "caso": "Si hoy pagas <b>900 €/mes</b> de alquiler y usas la máquina <b>7 meses al año</b>, gastas <b>6.300 €/año</b> que no vuelven. Una Kubota KX 016-4 G de 2024 con solo 250 h cuesta {p_kx016} + IVA en nuestro stock: al ritmo de ese alquiler queda amortizada en unos 3 años — y al final la máquina sigue siendo tuya y conserva valor de reventa.",
  "lm": "Ahora ya sabes qué mueve el precio de una mini. Si no quieres vigilar el mercado cada semana, lo hacemos nosotros: activa las alertas y te escribimos <b>solo</b> cuando una miniexcavadora baje de precio o entre una unidad nueva en stock.",
  "faq": [
   ("¿Cuántas horas son muchas para una miniexcavadora?", "Menos de 1.500 h es poco uso; entre 1.500 y 3.000 h es uso normal con mucha vida por delante si el mantenimiento está documentado; a partir de 5.000 h conviene inspección a fondo de motor, bombas, bulones y cadenas."),
   ("¿Miniexcavadora nueva o de segunda mano?", "Una mini nueva pierde una parte importante de su valor en los primeros dos años. Una unidad de 2023-2024 con pocas horas ofrece prácticamente la misma vida útil por bastante menos dinero, con entrega inmediata."),
   ("¿Qué tonelaje de mini necesito?", "Para zanjas y reformas urbanas, 1,5-3 t; para obra general y cimentaciones ligeras, 3-5 t; para movimiento de tierras serio dentro del segmento mini, 5-8 t. La limitación real suele ser el acceso, no la excavación."),
   ("¿Qué garantía tiene una miniexcavadora usada de Equipzilla?", "Casi todas nuestras unidades tienen opción de garantía, contrato de mantenimiento y financiación. Todas se entregan revisadas, con inspección y prueba presencial antes de comprar."),
  ],
 },
 "precio-carretilla-elevadora-segunda-mano": {
  "cat": "carr", "label": "carretilla elevadora",
  "kw": "carretilla elevadora segunda mano precio",
  "title": "Precio de una carretilla elevadora de segunda mano ({hoy}): tabla real",
  "h1": "¿Cuánto cuesta una carretilla elevadora de segunda mano?",
  "stand": "Precios reales de eléctricas, diésel y GLP, cómo decidir la energía correcta para tu nave y el error de la placa de cargas que casi todo el mundo comete.",
  "rapida": "Una carretilla elevadora de segunda mano cuesta entre <b>{pmin}</b> y <b>{pmax}</b> + IVA según capacidad, energía (eléctrica, diésel o GLP) y horas. Las eléctricas de 1,5-2,5 t — el estándar de almacén — rondan en nuestro stock los <b>{pmed}</b>. En eléctricas, el estado de la batería importa tanto como el horómetro.",
  "framework_t": "Eléctrica, diésel o GLP: decídelo en 3 preguntas",
  "framework": [
   ("¿Dónde trabaja la máquina?", "Interior o mixto con mercancía sensible → eléctrica, sin discusión: sin humos, menos ruido y menos mantenimiento. Exterior intensivo o rampas largas → térmica."),
   ("¿Cuál es tu carga real en el peor caso?", "No la media: el palet más pesado, a la altura máxima y descentrado. Compara ese dato con la placa de cargas, no con la capacidad nominal del anuncio."),
   ("¿Cuántas horas al día?", "Más de 4-5 h diarias en eléctrica exige mirar la batería con lupa (ciclos, informe de carga): una batería agotada puede costar varios miles de euros."),
  ],
  "errores": [
   ("Comprar por capacidad nominal", "Una '2,5 t' no levanta 2,5 t a cualquier altura ni con cualquier centro de carga. La placa de cargas es el único dato que vale."),
   ("Olvidar la batería en las eléctricas", "Es el componente caro. Exige siempre informe del estado de la batería y el cargador — puede cambiar el precio real de la operación."),
   ("Meter una térmica en interior", "Humos, normativa y quejas del personal. Si hay trabajo en interior, eléctrica o GLP con muy buena ventilación."),
  ],
  "consejo": "Si trabajas dentro y fuera (almacén + patio), busca eléctrica de 4 ruedas con neumáticos superelásticos: aguanta el exterior sin renunciar al interior limpio. Es la configuración que más solemos recomendar a almacenes de material de construcción.",
  "caso_t": "El cálculo que casi nadie hace",
  "caso": "Una carretilla alquilada ronda fácilmente los <b>500-900 €/mes</b>. Con la Clark EPX25 de nuestro stock (2,5 t, eléctrica, solo 801 h) a {p_clark} + IVA, pagando 600 €/mes de alquiler la tendrías amortizada en <b>menos de un año</b> de uso — todo lo que venga después es ahorro.",
  "lm": "Ahora ya sabes qué mirar. Si lo tuyo no corre prisa, deja que el mercado trabaje para ti: activa las alertas y te avisamos solo cuando una carretilla baje de precio o entre una nueva que encaje.",
  "faq": [
   ("¿Qué carretilla necesito para palets de 1.000-1.500 kg?", "Una carretilla de 1,6-2,5 t bien especificada cubre ese rango con margen para cargas descentradas y elevación. Si trabajas dentro y fuera, pide neumáticos superelásticos."),
   ("¿Cuántas horas dura una carretilla elevadora?", "Con mantenimiento correcto, las térmicas industriales superan con normalidad las 15.000 h. Más importante que la cifra es el historial: una máquina de 11.000 h bien cuidada es mejor compra que una de 6.000 h sin papeles."),
   ("¿Carretilla eléctrica de ocasión: qué revisar?", "Batería (ciclos y capacidad restante), cargador, estado de horquillas y mástil, y prueba con carga real. La batería es el 'segundo precio' de la máquina."),
   ("¿Tenéis carretillas de ocasión con garantía?", "Sí — casi todas nuestras unidades con opción de garantía, contrato de mantenimiento y financiación, revisadas y con prueba presencial antes de comprar."),
  ],
 },
 "precio-plataforma-elevadora-usada": {
  "cat": "plat", "label": "plataforma elevadora",
  "kw": "plataforma elevadora usada precio",
  "title": "Precio de una plataforma elevadora usada ({hoy}): tijera y articulada",
  "h1": "¿Cuánto cuesta una plataforma elevadora usada?",
  "stand": "Tijera o articulada, eléctrica o diésel: precios reales por altura de trabajo y el método para no pagar (ni transportar) metros que no necesitas.",
  "rapida": "Una plataforma elevadora usada cuesta entre <b>{pmin}</b> y <b>{pmax}</b> + IVA. El precio lo marcan la altura de trabajo y el tipo: una tijera eléctrica de 10 m está en la banda baja; las articuladas de 17-20 m, en la alta. Si alquilas plataforma varios meses al año, la compra de ocasión suele amortizarse antes de lo que parece.",
  "framework_t": "Cómo elegir plataforma (método en 4 pasos)",
  "framework": [
   ("Calcula la altura de trabajo real", "Altura del punto más alto que tocas + margen. Recuerda: la 'altura de trabajo' ya incluye los ~2 m de la persona sobre la cesta."),
   ("Vertical u obstáculos", "Si subes en vertical sobre suelo firme → tijera (cesta grande, más carga). Si hay estanterías, máquinas o cornisas que salvar → articulada."),
   ("Interior o exterior", "Interior → eléctrica (sin humos, suelos delicados). Exterior con terreno irregular → diésel, a ser posible 4x4."),
   ("Revisa el historial de seguridad", "Las plataformas llevan revisiones obligatorias. Historial al día = máquina legal y segura; sin historial, ni a buen precio."),
  ],
  "errores": [
   ("Comprar metros 'por si acaso'", "Cada metro de más se paga tres veces: en el precio, en el transporte y en el peso. Compra la altura de tu trabajo real, no la del proyecto imaginario."),
   ("Elegir tijera con obstáculos por medio", "La tijera solo sube en vertical. Si hay que 'asomarse' por encima de algo, necesitas articulada — no hay truco que lo arregle."),
   ("Saltarse las revisiones de seguridad", "En elevación de personas no hay atajos: el historial de revisiones es la ITV de la máquina. Exígelo siempre."),
  ],
  "consejo": "Para mantenimiento de naves logísticas, la combinación ganadora suele ser tijera eléctrica de 10-14 m: cubre la mayoría de techos, entra por puertas estándar y no mancha el suelo. Las articuladas grandes, solo si de verdad hay que salvar obstáculos o llegar a 17-20 m.",
  "caso_t": "El cálculo que casi nadie hace",
  "caso": "La Haulotte Compact 10 de nuestro stock (tijera eléctrica, 10 m, 1.116 h) cuesta {p_compact} + IVA. Si pagas <b>600 €/mes</b> cuando la alquilas, con <b>9-10 meses de alquiler</b> ya has pagado la máquina entera — y una tijera eléctrica con esas horas tiene muchos años de vida por delante.",
  "lm": "Ahora ya sabes qué plataforma encaja. Los precios de elevación se mueven: activa las alertas y te escribimos solo cuando una plataforma baje de precio o entre una nueva en stock.",
  "faq": [
   ("¿Plataforma de tijera o articulada?", "Tijera para trabajo vertical sobre suelo firme (instalaciones, mantenimiento de naves): más cesta y más carga por menos dinero. Articulada cuando hay que salvar obstáculos o acceder lateralmente."),
   ("¿Cuántos metros necesito para una nave industrial?", "La mayoría de naves logísticas se resuelven con 10-14 m de altura de trabajo. Para cerchas o cubiertas altas, 17-20 m articulada."),
   ("¿Las plataformas usadas pasan revisiones?", "Deben llevar sus revisiones de seguridad al día. Las nuestras se entregan revisadas y con inspección presencial; casi todas con opción de garantía y contrato de mantenimiento."),
   ("¿Eléctrica o diésel?", "Interior y suelos delicados → eléctrica. Exterior y terreno irregular → diésel (mejor 4x4). Las bi-energía cubren ambos mundos y por eso se cotizan."),
  ],
 },
 "precio-manipulador-telescopico-usado": {
  "cat": "tele", "label": "manipulador telescópico",
  "kw": "manipulador telescópico usado precio",
  "title": "Precio de un manipulador telescópico usado ({hoy}): tabla real",
  "h1": "¿Cuánto cuesta un manipulador telescópico usado?",
  "stand": "La navaja suiza de la obra: precios reales por alcance y capacidad, qué inspeccionar en una pluma usada y cuándo compensa frente al alquiler.",
  "rapida": "Un manipulador telescópico usado cuesta entre <b>{pmin}</b> y <b>{pmax}</b> + IVA según alcance, capacidad y horas. El binomio altura × carga define el precio: unidades recientes de 6-15 m con pocas horas ocupan la banda media-alta. Es de las máquinas más versátiles de obra — y de las que más se amortizan si hoy la alquilas cada mes.",
  "framework_t": "Cómo elegir telescópico (método en 4 pasos)",
  "framework": [
   ("Define tu carga en la punta", "No la capacidad nominal: el palet o carga típica a tu alcance máximo habitual. El diagrama de cargas de cada modelo es el dato que manda."),
   ("Alcance real de tu obra", "Para alimentar un forjado de 3-4 plantas bastan 12-14 m; para estructura y cubierta, 15-18 m. Cada metro de más se paga."),
   ("Estado de pluma y cadenas internas", "Es el corazón (y lo caro) de un telescópico usado: holguras en la pluma, estado de cadenas internas y estabilizadores. Pruébalo siempre con carga."),
   ("Implementos incluidos", "Horquillas, cazo y cesta homologada multiplican lo que hace la misma máquina. Negócialos dentro de la operación: sueltos cuestan mucho más."),
  ],
  "errores": [
   ("Comprar sin probar con carga", "Un telescópico puede parecer perfecto en vacío y revelar holguras o pérdidas de fuerza con carga en la punta. La prueba con carga no es opcional."),
   ("Ignorar el pasado de alquiler", "Muchos telescópicos vienen de flotas de alquiler con uso intenso. No es malo en sí — pero exige horas certificadas e historial de mantenimiento."),
   ("Olvidar los implementos", "La máquina 'barata' sin horquillas ni cesta deja de serlo cuando los compras aparte. Compara operaciones completas, no precios de chasis."),
  ],
  "consejo": "Si dudas entre plataforma y telescópico para trabajos en altura con material, piensa así: la plataforma sube personas; el telescópico sube material (y con cesta homologada, también personas). Para obra con palets en altura, el telescópico suele ser la compra más rentable.",
  "caso_t": "El cálculo que casi nadie hace",
  "caso": "El JLG 4013 de nuestro stock (4 t · 13 m) cuesta {p_jlg} + IVA. Si cada mes de obra pagas <b>1.400 €</b> por uno alquilado, en <b>unos 19 meses de uso</b> la compra queda pagada. Con dos obras al año de 4-5 meses, hablamos de ~2 años de calendario — y la máquina sigue valiendo dinero.",
  "lm": "Ahora ya sabes qué mirar en un telescópico usado. El stock de estas máquinas rota rápido: activa las alertas y te avisamos solo cuando entre una unidad o baje un precio.",
  "faq": [
   ("¿Para qué sirve un manipulador telescópico?", "Carga palets en altura, alimenta forjados, mueve material en terreno irregular y, con implementos, hace de cazo cargador, grúa ligera o plataforma con cesta homologada. Es la máquina más polivalente de una obra media."),
   ("¿Cuántas horas son aceptables en un telescópico usado?", "Menos de 1.000 h es casi nuevo; hasta 4.000 h con mantenimiento documentado es compra segura; por encima, inspección a fondo de pluma, transmisión y estabilizadores."),
   ("¿Qué alcance necesito?", "Regla práctica: altura de tu forjado o acopio más alto + 2 m de margen de maniobra. Para la mayoría de edificación media, 12-14 m."),
   ("¿Ofrecéis garantía en telescópicos usados?", "Sí — casi todas las unidades con opción de garantía, contrato de mantenimiento y financiación, revisadas y con prueba presencial."),
  ],
 },
 "precio-excavadora-usada": {
  "cat": "exca", "label": "excavadora",
  "kw": "excavadora usada precio",
  "title": "Precio de una excavadora usada de 14-23 t ({hoy}): tabla real",
  "h1": "¿Cuánto cuesta una excavadora usada?",
  "stand": "Precios reales de 14 a 23 toneladas, el coste oculto que puede convertir un chollo en una ruina (el tren de rodaje) y cómo comprar horas certificadas.",
  "rapida": "Una excavadora usada de 14-23 t cuesta entre <b>{pmin}</b> y <b>{pmax}</b> + IVA según tonelaje, horas y equipamiento (GPS 3D, cazos, engrase centralizado). Las unidades recientes con menos de 1.000 h certificadas ocupan la banda alta — y son las que antes se venden. En esta gama, el estado del tren de rodaje puede mover el valor real de la operación tanto como el año.",
  "framework_t": "Cómo comprar una excavadora grande sin sustos (4 pasos)",
  "framework": [
   ("Horas certificadas o nada", "En máquinas de este valor, el horómetro manipulado existe. Compra solo con horas certificadas y libro de mantenimiento — o con inspección independiente."),
   ("Mide el tren de rodaje", "Cadenas, rodillos, ruedas guía y dientes: el desgaste se mide, no se intuye. Un tren de rodaje al final de su vida es una factura enorme esperando fecha."),
   ("Valora el equipamiento de verdad", "GPS 3D (Topcon/Trimble), engrase centralizado o cazos de gran volumen no son 'extras': cambian la productividad diaria y el precio de reventa."),
   ("Cadenas vs ruedas según tu obra", "Ruedas para obra urbana y desplazamientos frecuentes entre tajos; cadenas para producción pura. Equivocarse aquí se paga cada día."),
  ],
  "errores": [
   ("Comprar 'el chollo' sin inspección", "En 20 toneladas no hay chollos sin explicación. Si el precio está muy por debajo de mercado, la explicación suele estar en el tren de rodaje, las bombas o las horas."),
   ("Infravalorar el transporte", "Mover una 20 t requiere góndola y permisos. Inclúyelo en el coste de la operación desde el principio."),
   ("Comprar más tonelaje del que produces", "Una 22 t consume, se transporta y se amortiza como una 22 t. Si tu producción cabe en una 14-17 t, la grande solo es más cara, no mejor."),
  ],
  "consejo": "Si haces movimiento de tierras con niveles y taludes, prioriza una unidad con GPS 3D aunque cueste más: el ahorro en replanteos y repasos lo devuelve en pocas obras, y la reventa siempre agradece el equipo.",
  "caso_t": "El cálculo que casi nadie hace",
  "caso": "La Doosan DX 210 LC-7 de nuestro stock (22 t, 2022, solo 810 h certificadas) cuesta {p_dx210} + IVA. Haz tu número: multiplica lo que pagas al mes por una equivalente de alquiler por tus meses de obra al año — con producción continua, estas máquinas se pagan solas en pocos ejercicios, y las horas bajas de esta unidad le dejan una vida larguísima por delante.",
  "lm": "Ahora ya sabes dónde está el riesgo (y el valor) en una excavadora usada. Las unidades buenas de esta gama vuelan: activa las alertas y sé el primero en enterarte cuando entre una o baje un precio.",
  "faq": [
   ("¿Cuántas horas puede tener una excavadora usada?", "Una excavadora de 20 t bien mantenida supera las 10.000 h de vida. Para compra de ocasión, unidades con 800-3.500 h certificadas ofrecen la mejor vida restante por euro invertido."),
   ("¿Cómo sé que las horas son reales?", "Horas certificadas + libro de mantenimiento + inspección. En Equipzilla las horas se certifican y cada máquina pasa inspección y prueba presencial antes de la compra."),
   ("¿Merece la pena el GPS 3D?", "Si trabajas con niveles, sí: ahorra replanteos, repasos y discusiones con la dirección de obra. Se amortiza en pocas obras y sube la reventa."),
   ("¿Excavadora de cadenas o de ruedas?", "Cadenas para producción y terrenos difíciles; ruedas para obra urbana con desplazamientos frecuentes (evitas góndola entre tajos cercanos)."),
  ],
 },
}

# precios de unidades concretas citadas en los casos (del stock real)
PRECIOS_UNIDADES = {m["n"]: m["p"] for m in MACHINES}
TOKENS_UNIDADES = {
    "p_kx016": "Kubota KX 016-4 G", "p_clark": "Clark EPX25",
    "p_compact": "Haulotte Compact 10", "p_jlg": "JLG 4013",
    "p_dx210": "Doosan DX 210 LC-7",
}

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,500..800'
         '&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">')

CSS = """
  :root{--bg:#F7F9F9;--paper:#FFFFFF;--line:#E2E8E8;--ink:#14181C;--ink2:#46565A;--ink3:#7C8D90;
        --teal:#387E7F;--teal-dark:#17323A;--teal-soft:#EAF1F1;--mint:#8FD3C0;--coral:#F0523C;--wa:#25D366}
  *{box-sizing:border-box;margin:0;padding:0}
  html{scroll-behavior:smooth}
  body{background:var(--bg);font-family:'IBM Plex Sans',system-ui,sans-serif;color:var(--ink);
       line-height:1.7;-webkit-font-smoothing:antialiased;font-size:16px}
  .arx{font-family:'Archivo',system-ui,sans-serif;font-stretch:115%}
  .mono{font-family:'IBM Plex Mono',monospace}
  .topbar{height:5px;background:var(--teal)}
  header.site{background:var(--paper);border-bottom:1px solid var(--line)}
  header.site .in{max-width:720px;margin:0 auto;padding:16px 20px;display:flex;justify-content:space-between;align-items:center}
  .logo{font-family:'Archivo',system-ui,sans-serif;font-stretch:120%;font-weight:800;font-size:20px;color:var(--coral);text-decoration:none}
  .navl{font-size:13.5px;color:var(--ink2);text-decoration:none;margin-left:18px}
  .navl:hover{color:var(--teal)}
  main{max-width:720px;margin:0 auto;padding:44px 20px 70px}
  .eyebrow{font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.18em;text-transform:uppercase;
           color:var(--teal);font-weight:500;margin-bottom:14px}
  h1{font-family:'Archivo',system-ui,sans-serif;font-stretch:115%;font-weight:800;font-size:clamp(30px,5.4vw,40px);
     line-height:1.12;letter-spacing:-.02em;margin-bottom:16px}
  .stand{font-size:18.5px;line-height:1.6;color:var(--ink2);margin-bottom:18px}
  .meta{font-family:'IBM Plex Mono',monospace;font-size:12px;color:var(--ink3);
        padding-bottom:26px;border-bottom:1px solid var(--line);margin-bottom:30px}
  h2{font-family:'Archivo',system-ui,sans-serif;font-stretch:115%;font-weight:700;font-size:24px;letter-spacing:-.01em;
     margin:44px 0 14px;line-height:1.25}
  h3{font-family:'Archivo',system-ui,sans-serif;font-stretch:110%;font-weight:700;font-size:17px;margin:22px 0 6px}
  p{margin-bottom:14px;color:#243036}
  .rapida{background:var(--teal-dark);border-radius:14px;padding:24px 26px;margin:6px 0 10px;color:#D9E6E6}
  .rapida .k{font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.16em;text-transform:uppercase;
             color:var(--mint);font-weight:500;margin-bottom:10px}
  .rapida p{color:#D9E6E6;font-size:15.5px;line-height:1.7;margin:0}
  .rapida b{color:#fff}
  .stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:22px 0 8px}
  .stat{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:16px 14px;text-align:center}
  .stat b{display:block;font-family:'Archivo',system-ui,sans-serif;font-stretch:115%;font-weight:800;font-size:21px}
  .stat span{font-size:11.5px;color:var(--ink3);font-family:'IBM Plex Mono',monospace}
  .tablewrap{overflow-x:auto;margin:14px 0 6px;border:1px solid var(--line);border-radius:12px;background:var(--paper)}
  table{width:100%;border-collapse:collapse;font-size:14px;min-width:520px}
  th{background:var(--teal-dark);color:#fff;text-align:left;padding:11px 14px;font-size:11.5px;
     font-family:'IBM Plex Mono',monospace;letter-spacing:.06em;text-transform:uppercase;font-weight:500}
  td{padding:12px 14px;border-bottom:1px solid #EEF3F3;vertical-align:top}
  tr:last-child td{border-bottom:none}
  tr:nth-child(even) td{background:#FAFCFC}
  .pr{font-weight:700;white-space:nowrap;font-size:15px}
  .note{font-size:12.5px;color:var(--ink3);margin-top:8px}
  ol.steps{counter-reset:s;list-style:none;margin:16px 0}
  ol.steps li{position:relative;padding:0 0 20px 54px;counter-increment:s}
  ol.steps li::before{content:counter(s);position:absolute;left:0;top:0;width:36px;height:36px;
    background:var(--teal);color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;
    font-family:'Archivo',system-ui,sans-serif;font-weight:800;font-size:16px}
  ol.steps li::after{content:"";position:absolute;left:17px;top:40px;bottom:4px;width:2px;background:var(--line)}
  ol.steps li:last-child::after{display:none}
  ol.steps b{font-family:'Archivo',system-ui,sans-serif;font-stretch:110%;font-size:16px;display:block;margin-bottom:3px}
  ol.steps p{font-size:14.5px;color:var(--ink2);margin:0}
  .block{border-radius:12px;padding:18px 20px;margin:14px 0}
  .block .bt{font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.14em;text-transform:uppercase;
             font-weight:500;margin-bottom:6px}
  .block p{margin:0;font-size:14.5px}
  .warn{background:#FDF1EE;border:1px solid #F6D5CD}
  .warn .bt{color:#B34A38}
  .warn b.t{font-family:'Archivo',system-ui,sans-serif;font-stretch:110%;display:block;margin-bottom:3px;font-size:15.5px}
  .tip{background:var(--teal-soft);border:1px solid #CFE0E0}
  .tip .bt{color:var(--teal)}
  .case{background:var(--paper);border:1px solid var(--line);border-left:4px solid var(--teal);
        border-radius:0 12px 12px 0;padding:20px 22px;margin:18px 0}
  .case .bt{font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.14em;text-transform:uppercase;
            color:var(--teal);font-weight:500;margin-bottom:8px}
  .case p{margin:0;font-size:15px}
  .lm{background:linear-gradient(135deg,#17323A,#245158);border-radius:16px;padding:28px;margin:38px 0;color:#D9E6E6}
  .lm .bt{font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.16em;text-transform:uppercase;
          color:var(--mint);margin-bottom:8px}
  .lm .t{font-family:'Archivo',system-ui,sans-serif;font-stretch:112%;font-weight:800;font-size:21px;color:#fff;margin-bottom:8px}
  .lm p{color:#C9DBDB;font-size:14.5px;margin-bottom:14px}
  .lm form{display:flex;gap:10px;flex-wrap:wrap}
  .lm input{flex:1;min-width:200px;border:none;border-radius:10px;padding:13px 15px;font-size:15px;font-family:inherit}
  .lm button{border:none;border-radius:10px;background:var(--mint);color:#14312B;font-weight:700;
             padding:13px 22px;font-size:15px;cursor:pointer;font-family:inherit}
  .lm button:hover{filter:brightness(1.05)}
  .okmsg{display:none;margin-top:10px;font-size:13.5px;color:var(--mint);font-weight:600}
  .faq{background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:6px 22px}
  .faq details{border-bottom:1px solid #EEF3F3;padding:15px 0}
  .faq details:last-child{border-bottom:none}
  .faq summary{font-family:'Archivo',system-ui,sans-serif;font-stretch:110%;font-weight:700;font-size:15.5px;cursor:pointer;list-style:none;position:relative;padding-right:26px}
  .faq summary::after{content:"+";position:absolute;right:2px;top:-2px;font-size:20px;color:var(--teal)}
  .faq details[open] summary::after{content:"–"}
  .faq p{margin:10px 0 0;color:var(--ink2);font-size:14.5px}
  .ctafinal{background:var(--paper);border:1.5px solid var(--teal);border-radius:16px;padding:28px;margin:40px 0 0;text-align:center}
  .ctafinal .t{font-family:'Archivo',system-ui,sans-serif;font-stretch:112%;font-weight:800;font-size:22px;margin-bottom:8px}
  .ctafinal p{color:var(--ink2);font-size:14.5px;max-width:480px;margin:0 auto 16px}
  .btnrow{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}
  .btn{display:inline-block;border-radius:10px;padding:14px 26px;font-weight:700;font-size:15px;text-decoration:none}
  .btn.teal{background:var(--teal);color:#fff}
  .btn.wa{background:var(--wa);color:#fff}
  .rel{margin-top:40px;border-top:1px solid var(--line);padding-top:22px}
  .rel .k{font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink3);margin-bottom:12px}
  .rel a{display:block;color:var(--teal);text-decoration:none;font-weight:600;font-size:14.5px;padding:5px 0}
  .rel a:hover{text-decoration:underline}
  footer.site{border-top:1px solid var(--line);margin-top:30px}
  footer.site .in{max-width:720px;margin:0 auto;padding:24px 20px;font-size:12.5px;color:var(--ink3);
                  font-family:'IBM Plex Mono',monospace;text-align:center}
  a{color:var(--teal)}
  @media(max-width:560px){.stats{grid-template-columns:1fr 1fr}.stat:last-child{grid-column:1/-1}}
  ul.check{list-style:none;margin:10px 0}
  ul.check li{position:relative;padding:6px 0 6px 34px;font-size:14.5px;color:#243036}
  ul.check li::before{content:"✓";position:absolute;left:0;top:6px;width:22px;height:22px;
    background:var(--teal-soft);color:var(--teal);border-radius:6px;display:flex;align-items:center;
    justify-content:center;font-weight:700;font-size:13px}
  .checkgroup{font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.14em;
    text-transform:uppercase;color:var(--teal);margin:20px 0 4px;font-weight:500}
  .lm .g2{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px}
  .lm label{display:block;font-size:11px;color:#9FBDBD;margin:0 0 4px;
    font-family:'IBM Plex Mono',monospace;letter-spacing:.08em;text-transform:uppercase}
  .lm .tin{width:100%;border:none;border-radius:10px;padding:12px 14px;font-size:14.5px;font-family:inherit}
  table.cmp td:first-child{font-weight:600;white-space:nowrap}
  @media(max-width:560px){.lm .g2{grid-template-columns:1fr}}
"""


def header_html(active=""):
    return f"""<div class="topbar"></div>
<header class="site"><div class="in">
  <a class="logo" href="/">Equipzilla</a>
  <nav><a class="navl" href="/">Asesor</a><a class="navl" href="/alquilar-o-comprar-maquinaria.html">Calculadora</a><a class="navl" href="/guias/">Guías</a></nav>
</div></header>"""


FOOTER = """<footer class="site"><div class="in">Equipzilla · Barcelona · 911 238 750 ·
<a href="https://equipzilla.com">equipzilla.com</a> · Precios + IVA · Stock sujeto a disponibilidad</div></footer>"""


def page(slug, g):
    ms = sorted([m for m in MACHINES if m["c"] == g["cat"]], key=lambda m: m["p"])
    ps = [m["p"] for m in ms]
    ctx = {"hoy": HOY, "pmin": eur(min(ps)), "pmax": eur(max(ps)),
           "pmed": eur(int(statistics.median(ps))), "n": len(ms)}
    for tok, name in TOKENS_UNIDADES.items():
        if name in PRECIOS_UNIDADES:
            ctx[tok] = eur(PRECIOS_UNIDADES[name])
    fmt = lambda s: s.format(**ctx)

    title, rapida, caso = fmt(g["title"]), fmt(g["rapida"]), fmt(g["caso"])
    horas_med = [m["h"] for m in ms if m.get("h")]
    rows = "".join(
        f'<tr><td><b>{m["n"]}</b></td><td>{m["y"]}</td><td>{m["s"]}</td>'
        f'<td>{format(m["h"], ",").replace(",", ".") + " h" if m.get("h") else "a confirmar"}</td>'
        f'<td class="pr">{eur(m["p"])}</td></tr>' for m in ms)
    steps = "".join(f"<li><b>{t}</b><p>{d}</p></li>" for t, d in g["framework"])
    errores = "".join(
        f'<div class="block warn"><div class="bt">Error común</div><b class="t">{t}</b><p>{d}</p></div>'
        for t, d in g["errores"])
    faqs_html = "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in g["faq"])
    faq_schema = json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in g["faq"]]},
        ensure_ascii=False)
    otras = "".join(
        f'<a href="/guias/{s}.html">→ {G["h1"]}</a>'
        for s, G in GUIAS.items() if s != slug)
    words = len(re.sub("<[^>]+>", " ", " ".join([
        g["stand"], rapida, caso, g["consejo"], g["lm"],
        " ".join(t + d for t, d in g["framework"]),
        " ".join(t + d for t, d in g["errores"]),
        " ".join(q + a for q, a in g["faq"])])).split())
    mins = max(3, round(words / 190))
    desc = re.sub("<[^>]+>", "", rapida)[:152].rsplit(" ", 1)[0] + "…"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | Equipzilla</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{BASE}/guias/{slug}.html">
{FONTS}
<script type="application/ld+json">{faq_schema}</script>
<style>{CSS}</style>
</head>
<body>
{header_html()}
<main>
  <div class="eyebrow">Guías de compra · {g["label"]}</div>
  <h1>{g["h1"]}</h1>
  <p class="stand">{g["stand"]}</p>
  <div class="meta">Actualizado {HOY} · {mins} min de lectura · precios de stock real · Equipo Equipzilla</div>

  <div class="rapida"><div class="k">Respuesta rápida</div><p>{rapida}</p></div>

  <div class="stats">
    <div class="stat"><b>{ctx["pmed"]}</b><span>precio mediano</span></div>
    <div class="stat"><b>{ctx["pmin"]} – {ctx["pmax"]}</b><span>rango del stock</span></div>
    <div class="stat"><b>{len(ms)} unidades</b><span>en venta ahora</span></div>
  </div>

  <h2>Precios reales de nuestro stock ({HOY})</h2>
  <p>Esta tabla no es una estimación: son las unidades que tenemos <b>en venta ahora mismo</b>, con su año, sus horas y su precio. Pocas webs del sector publican precios — nosotros preferimos que compares con datos.</p>
  <div class="tablewrap"><table>
    <thead><tr><th>Máquina</th><th>Año</th><th>Specs</th><th>Horas</th><th>Precio + IVA</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
  <p class="note">Unidades revisadas, con inspección y prueba presencial. Opción de garantía, contrato de mantenimiento y financiación en casi todas. El stock rota: consulta disponibilidad.</p>

  <h2>{g["framework_t"]}</h2>
  <ol class="steps">{steps}</ol>

  <h2>Los errores que más dinero cuestan</h2>
  {errores}

  <div class="block tip"><div class="bt">Consejo del asesor</div><p>{g["consejo"]}</p></div>

  <div class="case"><div class="bt">{g["caso_t"]}</div><p>{caso}</p></div>

  <div class="lm" id="alertas">
    <div class="bt">Lead magnet · alertas de precio</div>
    <div class="t">Que el mercado trabaje para ti</div>
    <p>{g["lm"]}</p>
    <form onsubmit="return ezAlert(this)">
      <input type="email" name="email" placeholder="tu@email.com" required>
      <button type="submit">Activar mis alertas</button>
    </form>
    <div class="okmsg">✓ Alertas activadas — revisa tu email.</div>
  </div>

  <h2>Preguntas frecuentes</h2>
  <div class="faq">{faqs_html}</div>

  <div class="ctafinal">
    <div class="t">¿No lo tienes claro? Dinos el trabajo, no la máquina</div>
    <p>Cuéntale tu proyecto a nuestro asesor de compra — qué necesitas hacer, dónde y con qué presupuesto — y te dice qué unidades del stock encajan y por qué. Gratis, 1 minuto, sin compromiso.</p>
    <div class="btnrow">
      <a class="btn teal" href="{BASE}/">Encontrar mi máquina</a>
      <a class="btn wa" href="https://wa.me/34606836581?text=Hola,%20vengo%20de%20la%20gu%C3%ADa%20de%20{g["label"].replace(" ", "%20")}%20y%20quiero%20que%20me%20asesor%C3%A9is">WhatsApp directo</a>
    </div>
  </div>

  <div class="rel"><div class="k">Sigue leyendo</div>
    <a href="/alquilar-o-comprar-maquinaria.html">→ ¿Alquilar o comprar? Calcula tu ahorro en 30 segundos</a>
    {otras}
  </div>
</main>
{FOOTER}
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


# ─────────────────────────────────────────────────────────────────────────────
# Artículos editoriales (no-precio): pilar, comparativas, garantía, vender.
# Mismo design system; secciones en HTML usando los componentes existentes.
# ─────────────────────────────────────────────────────────────────────────────
ARTICULOS = {
 "comprar-maquinaria-segunda-mano": {
  "kw": "comprar maquinaria segunda mano",
  "eyebrow": "Guía esencial · pilar",
  "title": "Comprar maquinaria de segunda mano sin pillarse los dedos: la checklist de 21 puntos",
  "h1": "Cómo comprar maquinaria de segunda mano sin pillarse los dedos",
  "stand": "Los 4 riesgos reales de la compra de ocasión, la checklist de 21 puntos que usamos antes de poner una máquina a la venta y el proceso para comprar con la misma seguridad que una máquina nueva.",
  "rapida": "Comprar maquinaria de ocasión es la forma más rápida de capitalizar tu operación — si controlas cuatro riesgos: <b>horas reales</b>, <b>estado estructural</b>, <b>documentación</b> y <b>vendedor</b>. Una máquina reciente con pocas horas, historial documentado e inspección presencial ofrece casi la misma vida útil que una nueva por bastante menos dinero, y con entrega inmediata.",
  "sections": [
   ("Por qué ocasión (cuando se hace bien)", """
<p>Una máquina nueva pierde una parte importante de su valor en los primeros dos años — ese descuento se lo lleva el primer dueño. El comprador de ocasión hereda la mayor parte de la vida útil pagando bastante menos, y sin esperar plazos de entrega: la máquina está en el patio, se prueba y se lleva.</p>
<p>La otra cara: el mercado de ocasión mezcla máquinas excelentes con máquinas problema, y por fuera se parecen mucho. Todo el juego consiste en distinguirlas <b>antes</b> de pagar.</p>"""),
   ("Los 4 riesgos que concentran casi todos los disgustos", """
<ol class="steps">
<li><b>Horas falseadas</b><p>El horómetro es una pantalla; se cambia. Sin horas certificadas o historial que las respalde, el número no vale nada. Contrasta siempre horas con desgaste real (pedales, asiento, mandos, bulones).</p></li>
<li><b>Averías estructurales latentes</b><p>Fisuras, soldaduras no originales, holguras en pluma y articulaciones, tren de rodaje al final de su vida. No se ven en fotos: se ven en una inspección presencial con la máquina trabajando.</p></li>
<li><b>Papeles incompletos</b><p>Sin factura, titularidad clara y documentación técnica (CE, manuales, placas legibles) puedes estar comprando un problema legal además de mecánico.</p></li>
<li><b>El vendedor equivocado</b><p>Quien no te deja probar la máquina con carga, no responde al porqué de la venta o mete prisa, te está contando algo. Escúchalo.</p></li>
</ol>"""),
   ("La checklist de 21 puntos (la nuestra)", """
<p>Es la revisión que aplicamos antes de poner una unidad a la venta. Úsala tal cual en cualquier compra — también si no nos compras a nosotros.</p>
<div class="checkgroup">Documentación · 7 puntos</div>
<ul class="check">
<li>Factura y titularidad claras (quién vende y con qué derecho)</li>
<li>Horas certificadas o respaldadas por historial</li>
<li>Libro / historial de mantenimiento</li>
<li>Facturas de las reparaciones importantes</li>
<li>Manual de operador y documentación técnica</li>
<li>Marcado CE y declaración de conformidad</li>
<li>Placas de cargas y de identificación legibles</li>
</ul>
<div class="checkgroup">Máquina · 8 puntos</div>
<ul class="check">
<li>Tren de rodaje o neumáticos: desgaste medido, no estimado</li>
<li>Fugas hidráulicas en cilindros, latiguillos y bloques</li>
<li>Holguras en bulones, articulaciones y pluma</li>
<li>Estructura: fisuras y soldaduras no originales</li>
<li>Arranque en frío: humos, ruidos, presiones</li>
<li>Respuesta hidráulica con carga (no en vacío)</li>
<li>Elementos de seguridad: frenos, luces, cinturón, cabina ROPS/FOPS</li>
<li>Estado de implementos incluidos (cazos, horquillas…)</li>
</ul>
<div class="checkgroup">Operación y vendedor · 6 puntos</div>
<ul class="check">
<li>Prueba presencial con carga real</li>
<li>Desgaste coherente con las horas declaradas</li>
<li>Quién la usó y en qué tipo de trabajo</li>
<li>Por qué se vende (la respuesta importa)</li>
<li>Opción de garantía y contrato de mantenimiento</li>
<li>Condiciones de entrega y transporte por escrito</li>
</ul>"""),
   ("Cómo lo resolvemos en Equipzilla", """
<p>Nuestro proceso existe para que no tengas que ser tú el experto: cada unidad pasa <b>inspección y prueba presencial</b>, se venden con <b>horas certificadas</b>, y casi todas con <b>opción de garantía, contrato de mantenimiento y financiación</b>. Publicamos los precios — cosa rara en el sector — porque preferimos que compares con datos.</p>
<div class="block tip"><div class="bt">Consejo del asesor</div><p>Si una máquina te encaja pero algo de la checklist falla, no la descartes de entrada: úsala para negociar. Un tren de rodaje a media vida o una batería dudosa tienen un precio — réstalo de la oferta y decide con números.</p></div>"""),
  ],
  "lm": {"type": "alertas", "cat": "todas",
         "text": "Ahora ya sabes qué revisar. El siguiente problema es encontrar la máquina — y para eso está el mercado vigilado: activa las alertas y te avisamos solo cuando entre una unidad revisada en stock o baje un precio."},
  "faq": [
   ("¿Es seguro comprar maquinaria de segunda mano?", "Sí, si la compra incluye horas certificadas, inspección presencial, documentación completa y — idealmente — garantía con contrato de mantenimiento. El riesgo no está en que sea usada: está en comprar a ciegas."),
   ("¿Qué es mejor: comprar a un particular o a un profesional?", "El particular puede ser algo más barato; el profesional aporta revisión, garantía, factura con IVA deducible y responsabilidad posterior. Para una máquina de trabajo diario, la seguridad suele valer la diferencia."),
   ("¿Cuánto se ahorra comprando de ocasión?", "Depende de categoría y edad, pero el patrón es constante: la mayor depreciación ocurre en los primeros años. Una unidad reciente con pocas horas ofrece la mayor parte de la vida útil por un precio sensiblemente menor al de nueva."),
   ("¿Puedo financiar una máquina usada?", "Sí — en Equipzilla casi todas las unidades tienen opción de financiación, además de garantía y contrato de mantenimiento."),
  ],
 },
 "horas-maquinaria-usada": {
  "kw": "cuántas horas son muchas maquinaria usada",
  "eyebrow": "Guía técnica",
  "title": "¿Cuántas horas son muchas en una máquina usada? Tabla de referencia por tipo",
  "h1": "¿Cuántas horas son muchas en una máquina usada?",
  "stand": "No existe un número mágico: existe una tabla de referencia por tipo de máquina y una regla que manda sobre todas — el historial vale más que el horómetro.",
  "rapida": "Depende del tipo de máquina: en una <b>miniexcavadora</b>, menos de 1.500 h es poco uso; una <b>carretilla térmica</b> industrial bien mantenida supera las 15.000 h; una <b>excavadora de 20 t</b> puede pasar de 10.000 h de vida. La regla universal: unas horas altas con historial documentado son mejor compra que unas horas bajas sin papeles.",
  "sections": [
   ("Tabla de referencia por tipo de máquina", """
<div class="tablewrap"><table class="cmp">
<thead><tr><th>Tipo</th><th>Poco uso</th><th>Uso normal</th><th>Exigir inspección a fondo</th></tr></thead>
<tbody>
<tr><td>Miniexcavadora</td><td>&lt; 1.500 h</td><td>1.500 – 3.000 h</td><td>&gt; 5.000 h</td></tr>
<tr><td>Excavadora 14-23 t</td><td>&lt; 1.000 h</td><td>1.000 – 3.500 h</td><td>&gt; 6.000 h</td></tr>
<tr><td>Manipulador telescópico</td><td>&lt; 1.000 h</td><td>1.000 – 4.000 h</td><td>&gt; 5.000 h</td></tr>
<tr><td>Plataforma elevadora</td><td>&lt; 1.500 h</td><td>1.500 – 4.000 h</td><td>&gt; 6.000 h</td></tr>
<tr><td>Carretilla elevadora</td><td>&lt; 4.000 h</td><td>4.000 – 12.000 h</td><td>&gt; 12.000 h</td></tr>
</tbody></table></div>
<p class="note">Rangos orientativos para máquinas con mantenimiento documentado. En plataformas, las revisiones de seguridad al día importan más que el horómetro; en carretillas eléctricas, el estado de la batería puede pesar más que las horas.</p>"""),
   ("La regla que manda: historial &gt; horómetro", """
<p>El horómetro es un dato; el historial es una historia completa. Una máquina de 11.000 h con libro de mantenimiento, facturas de taller y un solo operador cuidadoso suele ser mejor compra que una de 6.000 h sin un papel. Las horas dicen cuánto trabajó; el historial dice <b>cómo</b>.</p>
<div class="block warn"><div class="bt">Error común</div><b class="t">Comparar horas entre tipos distintos</b><p>5.000 h en una carretilla es media vida; en una miniexcavadora es motivo de inspección seria. Cada familia de máquina envejece a su ritmo — usa la tabla, no una cifra universal.</p></div>
<div class="block warn"><div class="bt">Error común</div><b class="t">"Pocas horas" en una máquina muy vieja</b><p>Los componentes también envejecen por tiempo: gomas, latiguillos, retenes y baterías se degradan aunque la máquina duerma. Una unidad de 15 años con 800 h no es una unidad nueva.</p></div>"""),
   ("Cómo verificar que las horas son reales", """
<ol class="steps">
<li><b>Pide horas certificadas</b><p>En Equipzilla certificamos las horas de cada unidad. Si el vendedor no puede respaldar el horómetro con nada, el número no existe.</p></li>
<li><b>Contrasta con el desgaste</b><p>Pedales, alfombrilla, asiento, volante y mandos cuentan la verdad: un puesto de conducción destrozado con 2.000 h en pantalla es una contradicción.</p></li>
<li><b>Cruza con el historial</b><p>Las facturas de taller llevan fecha y horas. Si el mantenimiento de hace dos años se hizo "a las 4.800 h" y hoy marca 3.900, ahí lo tienes.</p></li>
</ol>"""),
  ],
  "lm": {"type": "asesor",
         "text": "Ahora ya sabes leer un horómetro con criterio. Si quieres saltarte la parte difícil, cuéntale tu proyecto a nuestro asesor: te dice qué unidades del stock encajan — todas con horas certificadas e inspección presencial."},
  "faq": [
   ("¿Cuántas horas al año hace una máquina de obra?", "Como referencia, una máquina de uso profesional regular acumula entre 800 y 1.500 h al año; en uso intensivo (producción continua), bastante más. Por eso el binomio año + horas dice más que cualquiera de los dos datos por separado."),
   ("¿Es malo comprar una máquina ex-alquiler?", "No necesariamente: suelen tener mantenimiento al día aunque uso intenso. La clave es exigir el historial de flota y una inspección seria de los puntos de desgaste."),
   ("¿El horómetro se puede manipular?", "Sí, y ocurre. Por eso las horas sin historial ni certificación valen poco, y por eso nuestras unidades se venden con horas certificadas y prueba presencial."),
  ],
 },
 "carretilla-electrica-o-diesel": {
  "kw": "carretilla eléctrica o diésel",
  "eyebrow": "Comparativa",
  "title": "¿Carretilla eléctrica o diésel? Cuál comprar según tu nave (comparativa honesta)",
  "h1": "¿Carretilla eléctrica o diésel? Elige según tu nave, no según la moda",
  "stand": "La comparativa sin humo (literal): dónde gana cada una, el coste oculto de las eléctricas y los dos casos de nuestro stock que explican la diferencia de precio.",
  "rapida": "Para trabajo en <b>interior</b> — almacén, alimentación, farma, retail — la carretilla <b>eléctrica</b> gana sin discusión: sin humos, menos ruido y menos mantenimiento. Para <b>exterior intensivo</b>, rampas largas o triple turno sin pausas de carga, la <b>térmica</b> (diésel o GLP) sigue mandando. El error caro es comprar contra tu caso de uso.",
  "sections": [
   ("La comparativa, criterio a criterio", """
<div class="tablewrap"><table class="cmp">
<thead><tr><th>Criterio</th><th>Eléctrica</th><th>Diésel / GLP</th></tr></thead>
<tbody>
<tr><td>Interior</td><td>✅ Ideal (sin humos, silenciosa)</td><td>⚠️ GLP solo con muy buena ventilación</td></tr>
<tr><td>Exterior / rampas</td><td>⚠️ Correcta con superelásticas</td><td>✅ Su terreno natural</td></tr>
<tr><td>Mantenimiento</td><td>✅ Menos piezas, menos taller</td><td>Más mantenimiento periódico</td></tr>
<tr><td>Coste por hora de uso</td><td>✅ Electricidad barata</td><td>Combustible más caro</td></tr>
<tr><td>Turnos largos</td><td>⚠️ Depende de batería/cargas</td><td>✅ Repostas y sigues</td></tr>
<tr><td>Coste oculto</td><td>La batería (miles de €)</td><td>Motor y transmisión con horas altas</td></tr>
</tbody></table></div>"""),
   ("El coste oculto de cada bando", """
<p><b>En la eléctrica, la batería es el segundo precio de la máquina.</b> Una batería agotada puede costar varios miles de euros: antes de comprar, exige informe del estado de la batería y el cargador. Una eléctrica barata con batería muerta no es barata.</p>
<p><b>En la térmica, el coste oculto llega con las horas:</b> motor, transmisión e hidráulica acumulan desgaste que se paga en taller. La defensa es la misma de siempre — historial documentado y prueba con carga.</p>
<div class="case"><div class="bt">Dos unidades reales de nuestro stock</div><p>Ahora mismo conviven en nuestro stock dos carretillas de 2,5 t: la <b>Clark EPX25</b> eléctrica (2011, solo 801 h) por <b>7.000 €</b> y la <b>Hyster H2.5FT</b> GLP (2019, 11.503 h) por <b>15.000 €</b>. La lección: el precio no va "de energía" — va de horas, estado y configuración. Compara máquinas completas, no etiquetas.</p></div>"""),
   ("Decídelo en 3 preguntas", """
<ol class="steps">
<li><b>¿Dónde trabaja la máquina el 80% del tiempo?</b><p>Interior o mixto → eléctrica (con superelásticas si pisa patio). Exterior puro → térmica.</p></li>
<li><b>¿Cuántas horas seguidas al día?</b><p>Hasta 4-5 h diarias, cualquier eléctrica con batería sana. Turnos largos o dobles → térmica, o eléctrica con segunda batería (súmala al precio).</p></li>
<li><b>¿Qué mercancía mueves?</b><p>Alimentación, farma o espacios cerrados con gente → eléctrica por normativa y por convivencia. Obra y áridos → térmica.</p></li>
</ol>"""),
  ],
  "lm": {"type": "alertas", "cat": "carr",
         "text": "Ahora ya sabes qué energía encaja con tu nave. Deja que el mercado venga a ti: activa las alertas y te avisamos solo cuando una carretilla baje de precio o entre una unidad que encaje."},
  "faq": [
   ("¿Cuánto dura la batería de una carretilla eléctrica?", "En ciclos: una batería de plomo bien cuidada aguanta del orden de 1.200-1.500 ciclos de carga. Traducido: con una carga diaria, varios años de vida. Por eso el informe de batería es innegociable al comprar usada."),
   ("¿Puedo usar una carretilla diésel dentro de una nave?", "Como norma, no: humos y normativa lo desaconsejan. Para interior con necesidad térmica se usa GLP con ventilación adecuada — pero si el trabajo es mayoritariamente interior, la eléctrica es la respuesta correcta."),
   ("¿Qué es más barata de mantener?", "La eléctrica: menos piezas móviles, sin aceites de motor ni filtros de combustible. Su gasto grande es la batería al final de su vida — planifícalo."),
  ],
 },
 "plataforma-tijera-o-articulada": {
  "kw": "plataforma tijera o articulada",
  "eyebrow": "Comparativa",
  "title": "¿Plataforma de tijera o articulada? Cuál comprar según tu trabajo en altura",
  "h1": "¿Plataforma de tijera o articulada? La diferencia se paga — que sea por algo",
  "stand": "A la misma altura, una articulada puede costar el doble que una tijera. Cuándo ese sobreprecio está justificado y cuándo estás pagando movimientos que nunca usarás.",
  "rapida": "La <b>tijera</b> sube en vertical: más cesta, más carga y menos precio — perfecta para mantenimiento e instalaciones sobre suelo firme. La <b>articulada</b> añade brazo y plumín para salvar obstáculos y acceder lateralmente — y eso se paga. Regla práctica: si no tienes que \"asomarte\" por encima o por dentro de nada, la tijera gana en casi todo.",
  "sections": [
   ("La comparativa, criterio a criterio", """
<div class="tablewrap"><table class="cmp">
<thead><tr><th>Criterio</th><th>Tijera</th><th>Articulada</th></tr></thead>
<tbody>
<tr><td>Movimiento</td><td>Vertical puro</td><td>✅ Vertical + horizontal + sobre obstáculos</td></tr>
<tr><td>Cesta y carga</td><td>✅ Más grande, más personas/material</td><td>Más pequeña</td></tr>
<tr><td>Precio a igual altura</td><td>✅ Sensiblemente menor</td><td>Mayor (pagas el brazo)</td></tr>
<tr><td>Acceso lateral</td><td>❌ No llega</td><td>✅ Su razón de ser</td></tr>
<tr><td>Uso típico</td><td>Naves, instalaciones, mantenimiento</td><td>Fachadas, cubiertas, industria con obstáculos</td></tr>
</tbody></table></div>
<div class="case"><div class="bt">La diferencia, con precios reales</div><p>En nuestro stock actual: la <b>Haulotte Compact 10</b> (tijera eléctrica, 10 m, 1.116 h) cuesta <b>5.500 €</b>; la <b>Genie Z-34/22</b> (articulada diésel, 12 m) cuesta <b>10.500 €</b>. A alturas comparables, la articulada prácticamente <b>duplica</b> el precio. Si tu trabajo es vertical, ese dinero extra no te compra nada.</p></div>"""),
   ("Cuándo la articulada SÍ vale su precio", """
<ul class="check">
<li>Tienes que salvar estanterías, máquinas o cornisas para llegar al punto de trabajo</li>
<li>Necesitas acceso lateral (fachadas, estructuras, árboles, carteles)</li>
<li>El punto de trabajo no está encima de donde puede pisar la máquina</li>
<li>Trabajas en exterior con terreno irregular (articulada diésel 4x4)</li>
</ul>
<p>Si has marcado alguna, la articulada no es un capricho: es la única que hace el trabajo. Si no has marcado ninguna, vuelve a la tijera y quédate el ahorro.</p>
<div class="block warn"><div class="bt">Error común</div><b class="t">Comprar articulada "por si acaso"</b><p>El "por si acaso" cuesta miles de euros, más peso, más transporte y más mantenimiento. Compra para el trabajo que haces cada semana, no para el que imaginas una vez al año — ese día, alquilas.</p></div>
<div class="block tip"><div class="bt">Consejo del asesor</div><p>Para mantenimiento de naves logísticas, la tijera eléctrica de 10-14 m es la compra más repetida y con mejor reventa. Y si dudas entre 10 y 14 m: mide tu techo real — cada metro de más se paga tres veces (precio, peso, transporte).</p></div>"""),
  ],
  "lm": {"type": "alertas", "cat": "plat",
         "text": "Ahora ya sabes qué tipo encaja. Las plataformas buenas de ocasión rotan rápido: activa las alertas y te avisamos solo cuando una baje de precio o entre una nueva en stock."},
  "faq": [
   ("¿Qué altura de plataforma necesito?", "Altura del punto más alto que tocas + margen. Recuerda que la 'altura de trabajo' del catálogo ya suma unos 2 m de la persona sobre la cesta: para un techo de 8 m te basta una plataforma de 10 m de altura de trabajo."),
   ("¿Eléctrica o diésel en plataformas?", "Interior y suelos delicados → eléctrica. Exterior y terreno irregular → diésel 4x4. Las bi-energía cubren ambos mundos y por eso se cotizan más."),
   ("¿Qué revisiones debe tener una plataforma usada?", "Las revisiones de seguridad periódicas al día — son la ITV de la elevación de personas. Nuestras unidades se entregan revisadas, con inspección presencial y opción de garantía y mantenimiento."),
  ],
 },
 "garantia-maquinaria-ocasion": {
  "kw": "garantía maquinaria segunda mano",
  "eyebrow": "Compra segura",
  "title": "Garantía en maquinaria de segunda mano: qué debe incluir una compra segura",
  "h1": "Garantía en maquinaria de ocasión: qué exigir para comprar tranquilo",
  "stand": "Qué cubre (y qué no) una garantía de verdad, las 5 preguntas que hacer antes de pagar y las señales de alarma que delatan al vendedor equivocado.",
  "rapida": "Una compra segura de maquinaria usada se apoya en cinco piezas: <b>inspección presencial con prueba</b>, <b>horas certificadas</b>, <b>documentación completa</b> (factura, CE, historial), <b>opción de garantía</b> — idealmente con contrato de mantenimiento — y un <b>vendedor que responde</b> después de cobrar. Si faltan varias, el precio barato es solo el primer pago.",
  "sections": [
   ("Las 5 piezas de una compra protegida", """
<ol class="steps">
<li><b>Inspección presencial con prueba</b><p>Ver la máquina trabajando con carga. Cualquier vendedor serio te lo permite; cualquier excusa es información.</p></li>
<li><b>Horas certificadas</b><p>El horómetro respaldado por historial o certificación. Sin eso, estás comprando un número decorativo.</p></li>
<li><b>Documentación completa</b><p>Factura con IVA, titularidad, marcado CE, manuales y placas legibles. Los papeles también son la máquina.</p></li>
<li><b>Garantía por escrito</b><p>Qué cubre, cuánto tiempo, quién la atiende y dónde. Una garantía verbal es una anécdota, no una garantía.</p></li>
<li><b>Mantenimiento con contrato</b><p>La mejor garantía es que la máquina llegue revisada y siga revisada: un contrato de mantenimiento anual convierte la compra usada en una operación predecible.</p></li>
</ol>"""),
   ("Las 5 preguntas antes de pagar", """
<ul class="check">
<li>¿Puedo probarla con carga y traer a mi mecánico o un perito?</li>
<li>¿Las horas están certificadas o respaldadas por historial?</li>
<li>¿Qué cubre exactamente la garantía y quién responde?</li>
<li>¿Por qué se vende esta unidad?</li>
<li>¿Qué incluye la entrega (transporte, implementos, puesta en marcha)?</li>
</ul>
<div class="block warn"><div class="bt">Señal de alarma</div><b class="t">Prisa, pagos raros y "está en otro sitio"</b><p>Presión para señalizar hoy, pagos por adelantado a cuentas extrañas o máquinas que "ahora mismo están en otro país": el clásico completo. Una máquina que no puedes ver trabajando no existe.</p></div>"""),
   ("Cómo funciona en Equipzilla", """
<p>Casi todas nuestras unidades en venta tienen <b>opción de garantía, contrato de mantenimiento y financiación</b>. Todas pasan <b>inspección y prueba presencial</b> antes de la compra, con <b>horas certificadas</b> y documentación en regla. Y publicamos los precios para que compares sin llamar a nadie — aunque cuando llames, David te atiende igual de a gusto.</p>"""),
  ],
  "lm": {"type": "asesor",
         "text": "Ahora ya sabes qué exigir. Ponnos a prueba: cuéntale tu proyecto al asesor y te propone unidades del stock que ya cumplen esta lista entera — inspección, horas certificadas y opción de garantía incluidas."},
  "faq": [
   ("¿La maquinaria de segunda mano tiene garantía legal?", "Entre empresas, la garantía es principalmente lo que se pacte en el contrato — por eso importa tanto que esté por escrito y con cobertura clara. En Equipzilla ofrecemos opción de garantía con contrato de mantenimiento en casi todas las unidades."),
   ("¿Qué suele cubrir una garantía de maquinaria usada?", "Depende del acuerdo: lo habitual es cubrir componentes principales (motor, hidráulica, transmisión) durante un periodo definido. Exige el detalle por escrito: qué componentes, cuánto tiempo, quién repara y dónde."),
   ("¿Merece la pena pagar por un contrato de mantenimiento?", "En una máquina de trabajo diario, casi siempre: convierte averías imprevisibles en un coste planificado y alarga la vida de la máquina. Además protege su valor de reventa."),
  ],
 },
 "financiacion-maquinaria-ocasion": {
  "kw": "financiar maquinaria segunda mano",
  "eyebrow": "Compra inteligente",
  "title": "Financiar maquinaria de segunda mano: cómo convertir la compra en una cuota",
  "h1": "Financiar maquinaria de ocasión: paga como un alquiler, quédate la máquina",
  "stand": "Cómo funciona la financiación de maquinaria usada, qué documentación te van a pedir y los errores de plazo que convierten una buena compra en una mala deuda.",
  "rapida": "Sí, la maquinaria de segunda mano se puede financiar: en Equipzilla, <b>casi todas las unidades tienen opción de financiación</b>, además de garantía y contrato de mantenimiento. La idea clave: la cuota mensual de una máquina de ocasión suele quedar en el orden de lo que ya pagas de alquiler — con una diferencia enorme: al acabar, la máquina es tuya y conserva valor de reventa.",
  "sections": [
   ("El modelo mental: alquílate la máquina a ti mismo", """
<p>Si hoy pagas un alquiler recurrente, ya has demostrado dos cosas: que necesitas la máquina y que puedes pagar una cuota mensual por ella. La financiación redirige esa misma cuota hacia un activo tuyo. El alquiler compra disponibilidad; la financiación compra propiedad — y la propiedad se revende.</p>
<p>Haz el número con tu caso real en la <a href="/alquilar-o-comprar-maquinaria.html">calculadora de alquiler vs compra</a>: mete tu cuota de alquiler actual y compárala con el coste neto de comprar.</p>"""),
   ("Qué te van a pedir (prepáralo antes)", """
<ul class="check">
<li>CIF y escrituras o alta de autónomo</li>
<li>Últimas declaraciones de impuestos (IVA / sociedades o IRPF)</li>
<li>Balance o cuentas recientes, según el importe</li>
<li>Extractos o posición bancaria básica</li>
<li>Datos de la máquina: ficha, precio y factura proforma (esto lo ponemos nosotros)</li>
</ul>
<p>Con la documentación preparada, una operación estándar se resuelve en días, no en semanas. Nuestra parte — ficha técnica, precio cerrado y proforma — te la damos el mismo día.</p>"""),
   ("Los errores de plazo que arruinan una buena compra", """
<div class="block warn"><div class="bt">Error común</div><b class="t">Financiar a más plazo que la vida útil restante</b><p>Si a la máquina le quedan 4-5 años de trabajo serio y la financias a 7, acabarás pagando cuotas por una máquina que ya no produce. Ajusta el plazo a la vida útil que estás comprando — las horas y el estado lo dicen.</p></div>
<div class="block warn"><div class="bt">Error común</div><b class="t">Mirar solo la cuota</b><p>Dos ofertas con la misma cuota pueden esconder costes totales muy distintos (intereses, comisiones de apertura, seguros vinculados). Compara el coste total de la operación, no el número cómodo.</p></div>
<div class="block tip"><div class="bt">Consejo del asesor</div><p>La combinación que más tranquilidad da a una pyme: financiación ajustada a la vida útil + contrato de mantenimiento. Cuota predecible, taller predecible y una máquina que llega al final del plan con valor de reventa.</p></div>"""),
  ],
  "lm": {"type": "asesor",
         "text": "Ahora ya sabes cómo se financia. El siguiente paso es saber QUÉ financiar: cuéntale tu proyecto al asesor y te propone unidades del stock con su precio — y si quieres, te preparamos la propuesta de financiación de la que te encaje."},
  "faq": [
   ("¿Se puede financiar una máquina usada?", "Sí. En Equipzilla casi todas las unidades en venta tienen opción de financiación, además de garantía y contrato de mantenimiento. Te preparamos la documentación de la máquina el mismo día."),
   ("¿Qué plazo es razonable para financiar maquinaria?", "El que no supere la vida útil restante de la máquina: para una unidad reciente con pocas horas, plazos medios; para máquinas con más horas, plazos cortos. El objetivo es que la máquina siempre pague su propia cuota trabajando."),
   ("¿Financiar o pagar al contado?", "Si el contado no descapitaliza tu operación, es la opción más barata. Si prefieres preservar caja para circulante, la financiación bien planteada mantiene la tesorería y la máquina se paga sola con su trabajo."),
  ],
 },
 "vender-maquinaria-usada": {
  "kw": "vender maquinaria usada",
  "eyebrow": "Vende tu máquina",
  "title": "Vender tu maquinaria usada: cómo conseguir el mejor precio (sin perder meses)",
  "h1": "¿Vendes tu máquina? Así consigues el mejor precio sin perder meses",
  "stand": "Qué hace que una máquina usada valga más (o menos), la documentación que multiplica ofertas y cómo conseguir una tasación seria en 24 horas.",
  "rapida": "El precio de venta de una máquina usada lo deciden cuatro cosas: <b>horas con respaldo documental</b>, <b>estado real</b>, <b>documentación completa</b> y <b>el canal de venta</b>. Una máquina con historial y papeles se vende antes y mejor; una máquina sin documentar se malvende siempre. Si quieres número ya: tasación express en 24 h más abajo.",
  "sections": [
   ("Qué sube (y qué hunde) el precio de tu máquina", """
<div class="tablewrap"><table class="cmp">
<thead><tr><th>Factor</th><th>Suma</th><th>Resta</th></tr></thead>
<tbody>
<tr><td>Horas</td><td>Certificadas y coherentes con el desgaste</td><td>Horómetro sin respaldo</td></tr>
<tr><td>Historial</td><td>Libro + facturas de mantenimiento</td><td>"Siempre la hemos cuidado" (sin papeles)</td></tr>
<tr><td>Documentación</td><td>Factura, CE, manuales, placas</td><td>Papeles perdidos</td></tr>
<tr><td>Estado</td><td>Fugas resueltas, neumáticos/cadenas con vida</td><td>Averías "pequeñas" sin reparar</td></tr>
<tr><td>Momento</td><td>Vender con la máquina trabajando</td><td>Vender parada y con prisa</td></tr>
</tbody></table></div>
<div class="block tip"><div class="bt">Consejo del asesor</div><p>Reunir el historial de mantenimiento antes de anunciar la máquina es la hora mejor pagada de toda la venta: convierte tu anuncio en el único del listado con pruebas.</p></div>"""),
   ("Particular o profesional: los dos caminos", """
<p><b>Venta directa a otro usuario final:</b> puedes arañar algo más de precio, a cambio de semanas o meses de llamadas, visitas, regateos y el riesgo de impago o reclamaciones posteriores.</p>
<p><b>Venta a un profesional de la compraventa:</b> cobras antes, sin desfile de curiosos, con la operación documentada. El precio es de mercado mayorista — pero neto de tu tiempo, tus anuncios y tu riesgo, la distancia suele ser mucho menor de lo que parece.</p>
<div class="block warn"><div class="bt">Error común</div><b class="t">Poner el precio por corazonada</b><p>Ni el precio de compra de hace 6 años ni "lo que pide uno en internet" son referencias. La referencia es lo que se está pagando hoy por unidades comparables — año, horas, estado. Pide tasación con datos antes de anunciar nada.</p></div>"""),
  ],
  "lm": {"type": "tasacion",
         "text": "Ahora ya sabes qué hace valiosa tu máquina. Si quieres el número sin trabajo: dinos qué tienes y te damos una tasación seria — y si encaja, oferta de compra — en 24 horas laborables."},
  "faq": [
   ("¿Cuánto vale mi máquina usada?", "Depende de modelo, año, horas y estado — y del respaldo documental. Envíanos los datos con el formulario de tasación y te damos una valoración con datos de mercado en 24 h laborables, sin compromiso."),
   ("¿Compráis maquinaria directamente?", "Sí: compramos unidades que encajan con nuestra demanda (miniexcavadoras, excavadoras, carretillas, plataformas, telescópicos y palas). Tasación en 24 h y pago sin demoras si hay acuerdo."),
   ("¿Qué necesito para vender mi máquina rápido?", "Horas verificables, historial de mantenimiento, factura y fotos honestas (incluyendo el desgaste). Con eso, cualquier comprador serio puede decidir rápido — y pagar mejor."),
  ],
 },
}


def lm_block(lm):
    text = lm["text"]
    if lm["type"] == "alertas":
        cat = lm.get("cat", "todas")
        label = CAT_QUIZ_LABEL.get(cat, "todas")
        return f"""<div class="lm">
    <div class="bt">Lead magnet · alertas de precio</div>
    <div class="t">Que el mercado trabaje para ti</div>
    <p>{text}</p>
    <form onsubmit="return ezAlert(this)">
      <input type="email" name="email" placeholder="tu@email.com" required>
      <button type="submit">Activar mis alertas</button>
    </form>
    <div class="okmsg">✓ Alertas activadas — revisa tu email.</div>
  </div>
  <script>
  function ezAlert(f){{
    fetch("/api/subscribe",{{method:"POST",headers:{{"Content-Type":"application/json"}},
      body:JSON.stringify({{email:f.email.value.trim(),categoria:{json.dumps(label)}}})}})
      .then(function(){{ f.style.display="none"; f.parentNode.querySelector(".okmsg").style.display="block"; }});
    return false;
  }}
  </script>"""
    if lm["type"] == "tasacion":
        return f"""<div class="lm" id="tasacion">
    <div class="bt">Tasación express · respuesta en 24 h</div>
    <div class="t">¿Cuánto vale tu máquina? Te lo decimos con datos</div>
    <p>{text}</p>
    <form onsubmit="return ezTas(this)" style="display:block">
      <div class="g2">
        <div><label>Marca y modelo</label><input class="tin" name="modelo" placeholder="Ej. Kubota KX 057-4" required></div>
        <div><label>Año</label><input class="tin" name="ano" type="number" min="1990" max="2026" placeholder="2019"></div>
      </div>
      <div class="g2">
        <div><label>Horas aprox.</label><input class="tin" name="horas" type="number" min="0" placeholder="3.500"></div>
        <div><label>Teléfono</label><input class="tin" name="tel" type="tel" placeholder="600 000 000" required></div>
      </div>
      <label>Email</label><input class="tin" name="email" type="email" placeholder="tu@email.com" style="margin-bottom:12px" required>
      <button type="submit" style="width:100%">Pedir mi tasación gratuita</button>
    </form>
    <div class="okmsg">✓ Recibido — te damos la tasación en 24 h laborables.</div>
  </div>
  <script>
  function ezTas(f){{
    var d="TASACIÓN — "+f.modelo.value+" · año "+(f.ano.value||"?")+" · "+(f.horas.value||"?")+" h";
    fetch("/api/lead",{{method:"POST",headers:{{"Content-Type":"application/json"}},
      body:JSON.stringify({{origen:"tasacion",nombre:f.modelo.value,telefono:f.tel.value,
        email:f.email.value.trim(),detalle:d}})}})
      .then(function(){{ f.style.display="none"; f.parentNode.querySelector(".okmsg").style.display="block"; }});
    return false;
  }}
  </script>"""
    # asesor
    return f"""<div class="lm">
    <div class="bt">Siguiente paso</div>
    <div class="t">Dinos el trabajo, no la máquina</div>
    <p>{text}</p>
    <a class="btn" style="background:var(--mint);color:#14312B" href="{BASE}/">Hablar con el asesor de compra →</a>
  </div>"""


def article_page(slug, a):
    faq_html = "".join(f"<details><summary>{q}</summary><p>{ans}</p></details>" for q, ans in a["faq"])
    faq_schema = json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": ans}} for q, ans in a["faq"]]},
        ensure_ascii=False)
    body = "".join(f"<h2>{h2}</h2>\n{html}" for h2, html in a["sections"])
    todo = {**{s: g["h1"] for s, g in GUIAS.items()}, **{s: x["h1"] for s, x in ARTICULOS.items()}}
    rel = "".join(f'<a href="/guias/{s}.html">→ {h1}</a>'
                  for s, h1 in todo.items() if s != slug)
    words = len(re.sub("<[^>]+>", " ", a["stand"] + a["rapida"] + body).split())
    mins = max(3, round(words / 190))
    desc = re.sub("<[^>]+>", "", a["rapida"])[:152].rsplit(" ", 1)[0] + "…"
    wa_cta = ("https://wa.me/34606836581?text=Hola,%20quiero%20vender%20mi%20m%C3%A1quina%20y%20pido%20tasaci%C3%B3n"
              if a["lm"]["type"] == "tasacion" else
              "https://wa.me/34606836581?text=Hola,%20vengo%20de%20las%20gu%C3%ADas%20de%20Equipzilla%20y%20quiero%20que%20me%20asesor%C3%A9is")
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{a["title"]} | Equipzilla</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{BASE}/guias/{slug}.html">
{FONTS}
<script type="application/ld+json">{faq_schema}</script>
<style>{CSS}</style>
</head>
<body>
{header_html()}
<main>
  <div class="eyebrow">{a["eyebrow"]}</div>
  <h1>{a["h1"]}</h1>
  <p class="stand">{a["stand"]}</p>
  <div class="meta">Actualizado {HOY} · {mins} min de lectura · Equipo Equipzilla</div>

  <div class="rapida"><div class="k">Respuesta rápida</div><p>{a["rapida"]}</p></div>

  {body}

  {lm_block(a["lm"])}

  <h2>Preguntas frecuentes</h2>
  <div class="faq">{faq_html}</div>

  <div class="ctafinal">
    <div class="t">¿Hablamos de tu caso concreto?</div>
    <p>Un mensaje y te decimos qué haríamos en tu situación — con unidades y precios reales, sin compromiso.</p>
    <div class="btnrow">
      <a class="btn teal" href="{BASE}/">Asesor de compra</a>
      <a class="btn wa" href="{wa_cta}">WhatsApp directo</a>
    </div>
  </div>

  <div class="rel"><div class="k">Sigue leyendo</div>
    <a href="/alquilar-o-comprar-maquinaria.html">→ ¿Alquilar o comprar? Calcula tu ahorro en 30 segundos</a>
    {rel}
  </div>
</main>
{FOOTER}
<script src="/widget.js" defer></script>
</body>
</html>"""


def index_page():
    def card(href, eyebrow, t, s):
        return (f'<a class="card" href="{href}"><div class="ce mono">{eyebrow}</div>'
                f'<b class="arx">{t}</b><span>{s[:120].rsplit(" ", 1)[0]}…</span></a>')
    precios = "".join(card(f"/guias/{s}.html", g["label"], g["h1"], g["stand"])
                      for s, g in GUIAS.items())
    guias = "".join(card(f"/guias/{s}.html", a["eyebrow"], a["h1"], a["stand"])
                    for s, a in ARTICULOS.items())
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Guías de compra y precios de maquinaria de ocasión | Equipzilla</title>
<meta name="description" content="Precios reales de stock y guías de compra de maquinaria de segunda mano: qué revisar, alquilar o comprar, garantías y tasación. Actualizado {HOY}.">
<link rel="canonical" href="{BASE}/guias/">
{FONTS}
<style>{CSS}
  .card{{display:block;background:var(--paper);border:1px solid var(--line);border-radius:14px;
        padding:20px 22px;margin-bottom:14px;text-decoration:none;color:var(--ink);transition:border-color .15s}}
  .card:hover{{border-color:var(--teal)}}
  .card .ce{{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--teal);margin-bottom:6px}}
  .card b{{display:block;font-size:19px;font-weight:800;letter-spacing:-.01em;line-height:1.3;margin-bottom:6px}}
  .card span{{font-size:13.5px;color:var(--ink2)}}
  h2.sec{{margin-top:36px}}
</style>
</head>
<body>
{header_html()}
<main>
  <div class="eyebrow">Equipzilla · Ocasión</div>
  <h1>Guías de compra y precios reales</h1>
  <p class="stand">Lo que nadie publica en este sector: precios reales de stock, qué revisar antes de comprar, cuándo compensa comprar frente a alquilar — y cuánto vale tu máquina si vendes.</p>
  <div class="meta">Actualizado {HOY}</div>

  <a class="card" href="/alquilar-o-comprar-maquinaria.html">
    <div class="ce mono">herramienta</div><b class="arx">¿Alquilar o comprar? Calcula tu ahorro en 30 segundos</b>
    <span>Mete lo que pagas de alquiler y te decimos cuánto ahorras comprando de ocasión y en cuántos meses lo amortizas.</span></a>

  <h2 class="sec">Guías de compra</h2>
  {guias}

  <h2 class="sec">Precios por categoría (stock real)</h2>
  {precios}
</main>
{FOOTER}
<script src="/widget.js" defer></script>
</body>
</html>"""


def main():
    os.makedirs(OUT, exist_ok=True)
    for slug, g in GUIAS.items():
        open(os.path.join(OUT, slug + ".html"), "w").write(page(slug, g))
        print("✓", slug)
    for slug, a in ARTICULOS.items():
        open(os.path.join(OUT, slug + ".html"), "w").write(article_page(slug, a))
        print("✓", slug)
    open(os.path.join(OUT, "index.html"), "w").write(index_page())
    print("✓ index")
    urls = [f"{BASE}/", f"{BASE}/alquilar-o-comprar-maquinaria.html", f"{BASE}/guias/"] \
        + [f"{BASE}/guias/{s}.html" for s in GUIAS] \
        + [f"{BASE}/guias/{s}.html" for s in ARTICULOS]
    sm = ('<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    open(os.path.join(ROOT, "quiz", "sitemap.xml"), "w").write(sm)
    print("✓ sitemap.xml")


if __name__ == "__main__":
    main()

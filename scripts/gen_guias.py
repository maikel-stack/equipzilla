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


def index_page():
    cards = "".join(
        f'<a class="card" href="/guias/{slug}.html">'
        f'<div class="ce mono">{g["label"]}</div><b class="arx">{g["h1"]}</b>'
        f'<span>{g["stand"][:110].rsplit(" ", 1)[0]}…</span></a>'
        for slug, g in GUIAS.items())
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Guías de compra y precios de maquinaria de ocasión | Equipzilla</title>
<meta name="description" content="Precios reales de stock y guías de compra de maquinaria de segunda mano: miniexcavadoras, carretillas, plataformas, telescópicos y excavadoras. Actualizado {HOY}.">
<link rel="canonical" href="{BASE}/guias/">
{FONTS}
<style>{CSS}
  .card{{display:block;background:var(--paper);border:1px solid var(--line);border-radius:14px;
        padding:20px 22px;margin-bottom:14px;text-decoration:none;color:var(--ink);transition:border-color .15s}}
  .card:hover{{border-color:var(--teal)}}
  .card .ce{{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--teal);margin-bottom:6px}}
  .card b{{display:block;font-size:19px;font-weight:800;letter-spacing:-.01em;line-height:1.3;margin-bottom:6px}}
  .card span{{font-size:13.5px;color:var(--ink2)}}
</style>
</head>
<body>
{header_html()}
<main>
  <div class="eyebrow">Equipzilla · Ocasión</div>
  <h1>Guías de compra y precios reales</h1>
  <p class="stand">Lo que nadie publica en este sector: precios reales de stock, qué revisar antes de comprar y cuándo compensa comprar frente a alquilar. Actualizado {HOY}.</p>
  <div class="meta">&nbsp;</div>
  {cards}
  <a class="card" href="/alquilar-o-comprar-maquinaria.html">
    <div class="ce mono">herramienta</div><b class="arx">¿Alquilar o comprar? Calcula tu ahorro en 30 segundos</b>
    <span>Mete lo que pagas de alquiler y te decimos cuánto ahorras comprando de ocasión y en cuántos meses lo amortizas.</span></a>
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
    open(os.path.join(OUT, "index.html"), "w").write(index_page())
    print("✓ index")
    urls = [f"{BASE}/", f"{BASE}/alquilar-o-comprar-maquinaria.html",
            f"{BASE}/guias/"] + [f"{BASE}/guias/{s}.html" for s in GUIAS]
    sm = ('<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    open(os.path.join(ROOT, "quiz", "sitemap.xml"), "w").write(sm)
    print("✓ sitemap.xml")


if __name__ == "__main__":
    main()

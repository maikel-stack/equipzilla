# Secuencias de nurture · listas para montar en Brevo Automation

> Cómo montarlo (10 min, en la UI de Brevo): Automation → Create workflow →
> trigger "Contact added a tag" → añadir pasos de espera + email con los textos
> de abajo. Condición de salida: el contacto responde, agenda o compra
> (en la práctica: salir si recibe el tag `cliente` o responde a un email).
> Remitente: clientes@equipzilla.com (id 10) · Reply-to: david@equipzilla.com.

---

## Secuencia A · COMPRADOR
**Trigger:** tags `quiz-asesor`, `chat-asesor`, `calculadora` o `lead-calculadora`
(el día 0 ya recibió su análisis/recomendación transaccional — la secuencia empieza en el día 1).

### Email 1 · día 1 — Confianza en el proceso
**Asunto:** Cómo revisamos una máquina antes de venderla
**Cuerpo:**
Hola {{contact.NOMBRE | default: ""}},

ayer te llevaste una recomendación de máquina. Hoy te cuento lo que no se ve en la ficha:
qué pasa antes de que una unidad llegue a nuestro stock.

Cada máquina pasa una revisión de 21 puntos — documentación, estado estructural, prueba
con carga — y se vende con horas certificadas e inspección presencial. Si un punto no
pasa, la máquina no se publica. Así de simple.

Aquí tienes la checklist completa, por si compras donde compres:
https://equipzilla-quiz.vercel.app/guias/comprar-maquinaria-segunda-mano.html

Un saludo,
David Devis · Equipzilla · 606 836 581 (WhatsApp)

### Email 2 · día 3 — El número que duele
**Asunto:** ¿Cuánto llevas pagado de alquiler este año?
**Cuerpo:**
Una cuenta rápida: 900 €/mes de alquiler × 6 meses al año = 5.400 € anuales que no vuelven.
En tres años, 16.200 € — más que muchas máquinas completas de nuestro stock.

Alquilar tiene sentido para picos puntuales. Para lo recurrente, cada mes alquilado es
la máquina de otro pagándose sola.

Haz tu número real en 30 segundos (con tus cifras, no las mías):
https://equipzilla-quiz.vercel.app/alquilar-o-comprar-maquinaria.html

David · Equipzilla

### Email 3 · día 6 — La objeción
**Asunto:** "¿Y si sale rana?" — la pregunta correcta
**Cuerpo:**
Es LA pregunta al comprar usado, y la respuesta no es confianza: son garantías concretas.

En nuestras unidades: inspección y prueba presencial antes de comprar, horas certificadas,
y opción de garantía, contrato de mantenimiento y financiación en casi todas. Si sale
rana, no es tu problema — para eso está la garantía.

Qué debe incluir una compra segura (te sirva con nosotros o con cualquiera):
https://equipzilla-quiz.vercel.app/guias/garantia-maquinaria-ocasion.html

David · Equipzilla · 606 836 581

### Email 4 · día 9 — Stock y alertas
**Asunto:** Lo que hay ahora mismo (y cómo enterarte antes que nadie)
**Cuerpo:**
El stock de ocasión rota rápido: las unidades buenas con pocas horas no esperan.

Ahora mismo tenemos miniexcavadoras, carretillas, plataformas, telescópicos y excavadoras
con precios publicados — puedes verlos sin llamar a nadie:
https://equipzilla-quiz.vercel.app/guias/

Y si lo tuyo no corre prisa, activa las alertas: te escribimos solo cuando una máquina
de tu tipo baje de precio o entre una nueva. Sin spam.

David · Equipzilla

### Email 5 · día 12 — Cierre a llamada
**Asunto:** 10 minutos y te digo qué haría yo
**Cuerpo:**
Llevamos unos días compartiéndote criterio de compra. El siguiente paso útil no es otro
email: son 10 minutos de conversación sobre tu caso concreto.

Cuéntame qué necesitas hacer, qué presupuesto manejas y para cuándo — y te digo qué
haría yo: qué unidad del stock encaja, qué financiación tiene sentido o si te conviene
esperar a que entre algo mejor.

Respóndeme a este email o escríbeme directo al 606 836 581 (WhatsApp). Sin compromiso.

David Devis · Director de Desarrollo de Negocio · Equipzilla · 911 238 750

---

## Secuencia B · VENDEDOR (tasación)
**Trigger:** tag `lead-tasacion` (el día 0 recibe la tasación en <24 h laborables — la hace David).

### Email 1 · día 2 — Acelerar la decisión
**Asunto:** Tu máquina: lo que acelera (y sube) la oferta
**Cuerpo:**
Hola, soy David. Mientras cerramos tu tasación, un consejo que vale dinero: reúne el
historial de mantenimiento y las facturas de reparaciones. Una máquina documentada se
paga mejor — siempre.

Qué sube y qué hunde el precio de venta:
https://equipzilla-quiz.vercel.app/guias/vender-maquinaria-usada.html

Si prefieres hablarlo: 606 836 581 (WhatsApp).

David · Equipzilla

### Email 2 · día 5 — Cierre
**Asunto:** ¿Seguimos con la venta de tu máquina?
**Cuerpo:**
Te hicimos llegar nuestra valoración. Si encaja, el resto es rápido: revisión presencial,
acuerdo y pago sin demoras. Si no encaja, dime qué número tienes en mente y vemos si
hay camino.

Y si decides esperar: guarda este contacto. Compramos todo el año.

David Devis · Equipzilla · 606 836 581

---

## Notas de implementación
- Los tags ya se aplican automáticamente: `quiz-asesor` (quiz), `chat-asesor` (chatbot),
  `lead-calculadora` y `lead-tasacion` (endpoint /api/lead), `alerta-alta` (alertas).
- Los suscriptores de SOLO alertas (`alerta-alta` sin otro tag) NO entran en la
  secuencia A completa: prometimos "sin spam". Como mucho, Email 5 a los 30 días.
- Al montar los workflows, activar "exit on reply" y excluir contactos con deal
  ganado en Pipedrive (sello `cliente`).

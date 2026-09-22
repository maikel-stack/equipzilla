# Plan · reactivar a compra la base de 295 clientes de alquiler

_22/09/2026 · Dirección de Growth · para Andrés y Maikel_

Seis semanas, cuatro tests y una regla que manda sobre todo lo demás: **nada sale
hasta que el clic tenga dónde aterrizar y alguien tenga el nombre de quien llama.**
Esta base no se puede volver a comprar: si la quemamos con enlaces rotos y sin
seguimiento, se acabó.

Los tamaños de segmento son los del análisis de Andrés; están pendientes de
repasar cuando tengamos acceso de lectura al Sheet.

---

## Semana 0 · del 22 al 26 de septiembre — la puerta

No se envía nada esta semana. Son cinco cosas, y **las tres primeras son
condición**: si el lunes 29 no están, el calendario entero se corre una semana.

| # | Qué | Quién | Condición |
|---|---|---|---|
| 1 | Publicar en la web las máquinas de las familias que vamos a ofrecer: tijeras y articuladas eléctricas (14 tijeras, 11 eléctricas), carretillas (25) | Lorenzo + David | **sí** |
| 2 | SLA escrito: todo clic o respuesta de esta base se llama en **48 h**, con nombre y apellido asignado en Pipedrive, no «el equipo» | Andrés | **sí** |
| 3 | Etiquetado de origen: `base-alquiler`, segmento y test como tag de Brevo y campo de origen en Pipedrive | Director + CRM/Datos | **sí** |
| 4 | Limpieza: familia unificada en el panel de stock (hoy «Elevación», «ELEVACIÓN», «ELEVACION» y «Plataformas» son lo mismo, y 14 filas van vacías) | David | no bloquea |
| 5 | Calendario único: qué semana sale compra y qué semana alquiler, y quién no recibe las dos | Andrés (tiene el de alquiler; yo no lo veo) | no bloquea |

Y una decisión de Maikel que ya arrastramos: **las dos frases de garantía y
financiación**. Sin ellas, el argumento de compra va en genérico y T3 mide flojo.

---

## Semanas 1 a 6 · el calendario

### Semana 1 · 29/09 – 03/10 · **T4 · el email de una pregunta**
- **A quién**: los 35 clientes sin equipo identificado.
- **Qué**: un email de tres líneas con **una sola pregunta** — «¿qué máquina nos
  alquilaste?» —, sin catálogo, sin enlaces, sin precios.
- **Por qué va primero**: es el único envío que **no necesita fichas publicadas**,
  así que arranca aunque la web vaya con retraso, y nos devuelve 35 registros que
  hoy no sirven para nada.
- **Umbral**: ≥ 30 % de respuesta. El que responde se reasigna a su segmento real.

### Semana 2 · 06/10 – 10/10 · **T1 · mismo mensaje, dos segmentos**
- **A quién**: S1 oficios e instaladores (79) y S4 particulares (39), **el mismo
  día y con la misma creatividad**, que es lo que hace válido el test.
- **Qué**: tijeras y articuladas **eléctricas**, con el precio de entrada en el
  asunto — el formato que ya nos funciona (la campaña del 17/09 abrió al 28 % y
  los dos que clicaron eligieron las dos máquinas más baratas del lote).
- **Umbral**: S1 ≥ 8 % de respuesta y al menos el doble que S4.
- **Requiere**: fichas publicadas. Si no lo están, esta semana no sale.

### Semana 3 · 13/10 – 17/10 · **seguimiento, sin envío nuevo**
- A quien abrió o clicó en la semana 2: segundo toque con la máquina concreta que
  miró. Nada masivo.
- Es la semana en la que se comprueba si el SLA de 48 h existe de verdad. Si los
  clics de la semana 2 llegan al viernes sin llamar, **se para el plan** y se
  habla de otra cosa.

### Semana 4 · 20/10 – 24/10 · **T2 · personalizado contra genérico**
- **A quién**: S1-B, mitad y mitad.
- **Qué**: «nos alquilaste una *[máquina]* en *[mes]*» contra el envío de stock
  de siempre.
- **Umbral**: el personalizado dobla la respuesta del genérico.
- Es el test que más me interesa: si el dato histórico no mueve la aguja, toda la
  tesis de la base pierde fuerza y conviene saberlo pronto.

### Semana 5 · 27/10 – 31/10 · **T3 · el argumento rent-vs-compra**
- **A quién**: S2, carretillas (26).
- **Qué**: misma oferta con y sin el cálculo de amortización, validado **con
  nuestra tarifa real de alquiler**, no con la de la pestaña.
- **Umbral**: +50 % de clic.
- Muestra pequeña: lo trataremos como indicio, no como conclusión.

### Semana 6 · 03/11 – 07/11 · **medición y recalibrado**
- Embudo completo por segmento y prioridad: prospecto → MQL → SQL → oferta → venta.
- Si A/B convierte al menos el doble que C/D, el score vale. Si no, se recalibra
  con lo aprendido, que es justo lo que propone Andrés.

---

## Fuera del plan, y por qué

| Segmento | Qué hacemos |
|---|---|
| 71 A/B (prioridad alta) | **Contacto directo de David**, no campaña. Lista nominal con SLA de 48 h. Malupain es el ejemplo de lo que pasa sin eso: clicó el 28/07 y sigue sin una llamada, 56 días después |
| 15 alquiladores regionales | Canal wholesale, con David. Además distorsionan cualquier medición si se quedan dentro |
| 22 grandes cuentas | Fuera del mailing: se gestionan una a una o no se gestionan |
| 39 de solo casetas | Fuera del mailing de compra. Registrar la demanda: hay 3 peticiones vivas sin stock |
| 7 recurrentes | Son siete. Los llama David, no se les manda un correo |

---

## Cómo se mide

Todo envío se etiqueta en Brevo (`base-alquiler`, segmento, test) y el origen
viaja hasta Pipedrive. Medición a 30 días de cada envío.

- **MQL**: responde o pide algo.
- **SQL**: pide oferta.
- Quien cualifica antes de pasárselo a David tiene que tener nombre. Si no lo
  tiene, vuelve a pasar lo de siempre: el lead queda a nombre de nadie.

**Una advertencia que prefiero decir ahora y no en la reunión de cierre**: con 79,
26 y 39 contactos, estos tests dan **indicios, no certezas**. Un 8 % sobre 79 son
seis respuestas; la diferencia entre seis y tres no distingue un buen segmento de
la suerte. Por eso los umbrales están puestos en *veces*, no en puntos, y por eso
conviene decidir **antes** qué haremos con cada resultado. El único que dará una
respuesta limpia es T4.

---

## Lo que puede tumbar el plan

1. **Que el stock no se publique.** Hoy hay 138 máquinas en el panel, 41 en la web
   y 9 en Shopping. De las 14 tijeras, en la web hay 2.
2. **Que no haya SLA.** Con 0 ventas en 2026 y oferta→venta al 0 %, más leads no
   son más ventas. Hoy mismo tenemos dos HOT del frío —Herguido en Lleida y
   Excavaciones Nigrán en Pontevedra— sin una llamada.
3. **Que se solape con alquiler.** Es la misma gente; sin el calendario único
   alguien recibirá dos correos nuestros el mismo día.

---

## Lo que hace falta para arrancar

- **Maikel**: las dos frases de garantía y financiación · quién cualifica los MQL
  antes de pasarlos a David · OK a este calendario.
- **Andrés**: el calendario de envíos de alquiler de estas seis semanas · acceso
  de lectura al Sheet del análisis para
  `equipzilla-sheets-bot@equipzilla-493909.iam.gserviceaccount.com`.
- **Lorenzo y David**: publicar el stock de tijeras, articuladas eléctricas y
  carretillas antes del 29/09.

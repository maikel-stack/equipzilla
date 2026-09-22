# Preparación · reunión con Andrés sobre la base de 295 clientes de alquiler

_22/09/2026 · Dirección de Growth · notas previas, no conclusiones_

El análisis de Andrés está bien planteado y su punto 5 (SLA clic → contacto) es,
en mi opinión, el único que decide si el resto sirve de algo. Estas notas
verifican tres afirmaciones contra las fuentes vivas, corrigen una y proponen un
orden distinto para el calendario.

## 1. Stock: no son 3 tijeras, son 14 — el problema es otro

El panel de stock de David (138 filas) tiene **14 tijeras, 11 de ellas
eléctricas**, desde 2.750 € (JLG 1930ES) hasta 10.500 € (Compact-14, Magni).
Es decir: el segmento más denso que identifica Andrés —22 instaladores
solar/eléctricos, «tijera o articulada eléctrica para cubiertas»— **sí tiene
producto que ofrecer**.

Lo que no tiene es dónde aterrizar el clic:

| dónde | máquinas |
|---|---|
| Panel de stock de David | 138 |
| Catálogo de la web (`data/machines.json`, lo que ve el cliente) | 41 |
| Publicadas en Google Shopping | 9 |

De las 14 tijeras, en la web hay **2**. Esa es la misma pérdida que el Agente de
Ads encontró esta mañana por su cuenta, y aparece dos veces en el mismo día desde
sitios distintos: **no vendemos poco porque tengamos poco, sino porque casi nada
de lo que tenemos está publicado.**

Consecuencia para la reunión: el punto 4 de Andrés («no mandar tijeras a 79
personas con 3 tijeras») se cae, y en su lugar aparece uno más incómodo — se
pueden mandar, pero hoy el enlace lleva a una ficha que no existe. **Publicar el
stock es requisito previo a la campaña, no una mejora paralela.**

Además, la columna «Familia» del panel tiene el mismo concepto escrito de cuatro
maneras (Elevación / ELEVACIÓN / ELEVACION / Plataformas) y 14 filas vacías. Es
media hora de limpieza y sin ella ninguna segmentación por familia cuadra.

## 2. El SLA no es un punto del orden del día: es la condición

Andrés lo pone el quinto y con un «creo». No es una impresión, y estos son los
números de hoy:

| dato | valor |
|---|---|
| Ventas de compraventa en 2026 | **0** |
| oferta → venta | **0,0 %** |
| lead → oferta | 49,5 % |
| Abierto en tratos de compraventa | 364.614 € |
| Mediana lead → primera conversación real | 60 h |
| Llamadas de «Mi día» hechas en los últimos 3 días laborables | 0 de 5, tres días seguidos |

Y su ejemplo es correcto, verificado en Pipedrive: **Malupain Ibérica** (Marco,
600 418 359, info@malupainiberica.es) tiene como última actividad el **28/07**,
cero tratos abiertos y ninguna actividad futura. **56 días.**

La mitad de los leads llega a oferta y ninguna oferta llega a venta. Meter 295
contactos más por arriba de ese embudo no produce ventas: produce 295 contactos
quemados. Y esta base, a diferencia del frío, **no se puede volver a comprar**.

Mi posición para la reunión: **ninguna campaña a esta base hasta que existan las
dos cosas** — SLA de contacto en 48 h con nombre y apellido detrás, y ficha
publicada para cada máquina que se anuncie. Si una de las dos no está, se retrasa
el envío; no se lanza «a ver qué sale».

## 3. Los tests, tal como están, no van a contestar la pregunta

Las muestras son las que son: 79 / 26 / 39. Con un 8 % de respuesta esperado en
S1, el test T1 se juega con **6 respuestas contra 3**. Esa diferencia no distingue
un segmento bueno de la suerte, y a los 30 días tendremos una conclusión con la
que nadie se atreverá a decidir.

Dos salidas, y prefiero la segunda:
- Agrupar: menos tests y con toda la base detrás de cada uno.
- Aceptar que son **direccionales** y comprometer de antemano qué haremos con
  cada resultado, para no acabar discutiendo si 6 contra 3 «significa algo».

De los cuatro, el que sí puede dar una respuesta limpia es **T4** (email de una
pregunta a los 35 sin equipo identificado): ahí la métrica es «responde o no» y
un 30 % sobre 35 se ve a simple vista.

## 4. Calendario: lo que puedo aportar y lo que me falta

Desde esta sesión veo el calendario de **compraventa** (Brevo, listas 30 a 43) y
el frío (Smartlead). **No veo los envíos de alquiler**, que son los que saturan a
esta misma gente. Sin ese dato el calendario único que pide Andrés no se puede
cerrar: se lo pido a él antes de la reunión.

Lo que ya está comprometido por mi parte en compraventa:

| semana | envío | estado |
|---|---|---|
| jueves 24/09 | Kubota · miniexcavadoras (listas 39 + 43) | listo, pendiente de OK |
| jueves 01/10 | Carretillas (listas 30 + 40) | aplazado desde el 24/09 |

La base de alquiler es **población nueva** sobre esas listas, no una lista más:
antes de cruzarla hay que saber quién está ya dentro, o alguien recibirá dos
correos nuestros el mismo día.

## 5. Dónde estoy de acuerdo sin matices

- **Definición de MQL**: responde o pide algo = MQL; pide oferta = SQL. Y quien
  cualifica antes de pasarlo a David tiene que tener nombre.
- **Etiquetado de origen**: ya hay por dónde. Las plantillas nuevas de compra
  (Brevo **#222** aviso al equipo y **#223** acuse al cliente) aceptan parámetros
  y `tags`, así que «base alquiler / S1 / test T2» se puede llevar hasta
  Pipedrive sin inventar campos nuevos.
- **Los alquiladores regionales fuera del mailing**: son canal wholesale y con
  David. Coincido, y además distorsionan cualquier medición si se quedan dentro.
- **Los 39 particulares de Gmail con plataforma**: es el público natural de las
  tijeras eléctricas baratas (2.750 a 5.500 €), sin llamada. De todo el plan, es
  lo que menos depende de que alguien descuelgue el teléfono.

## 6. Bloqueo para poder preparar lo que me pide

El Sheet del análisis **no está compartido con la cuenta de servicio** que usan
los scripts, así que no he podido repasar la columna «Sector real» de los 71 A/B.

Hay que darle acceso de lectura a:
`equipzilla-sheets-bot@equipzilla-493909.iam.gserviceaccount.com`

Con eso, el repaso de los A/B y el cruce con quién está ya en las listas de Brevo
sale en una tarde.

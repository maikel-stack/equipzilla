# Equipzilla · Equipo de Growth (agentes) · estado y arquitectura

Fecha: 10/09/2026 · Autor: Cerebro Operativo de Growth + Ventas · Para: Maikel (CEO), Andrés, David, Héctor, Lorenzo
Objetivo 2026: 25 operaciones · 500.000 € GMV. Hoy: 0 ganadas en 2026, 15 ofertas vivas.

---

## Parte 1 · Cómo vamos (datos de hoy, 28-30 días)

### 1. SEO
| Dato | Valor |
|---|---|
| Guías publicadas en ocasion.equipzilla.com | 38 (41 URLs en sitemap, enviado a Search Console el 09/09) |
| Impresiones de las guías en 28 d | 0 · normal: Google tarda 2-6 semanas en posicionar un subdominio nuevo |
| equipzilla.com (28 d) | 308 clics · 26.896 impresiones · 500 consultas · 52 con intención de compra |
| Páginas /compra/ | 411 páginas · 128 clics · 17.729 impresiones |
| Resto (alquiler, ubicaciones, home) | 1.457 clics · el tráfico de la web sigue siendo de alquiler |

Quick wins (posición 4-20, muchas impresiones, pocos clics): *carretilla elevadora segunda mano* (pos. 10, 562 impr.), *plataforma elevadora segunda mano* (11,7 · 405), *transpaleta segunda mano* (5,4 · 214), *carretillas elevadoras de segunda mano* (15,4 · 179).

Leads de SEO: hoy no se pueden separar de los directos porque la web no envía UTM ni canal al crear el trato. Es el primer arreglo.

**Qué mejorar**
1. Crear las páginas de categoría que faltan en equipzilla.com: carretillas, manipuladores telescópicos, retroexcavadoras (hoy dan 404 blando). Son las que ya tienen demanda en Search Console. → Lorenzo.
2. Enlazar las 38 guías desde equipzilla.com (menú "Guías" o bloque en las páginas /compra/) y, mejor, servirlas en equipzilla.com/guias en vez de en subdominio. → Lorenzo.
3. Fichas de máquina indexables con precio, fotos y botón WhatsApp (hoy el stock no es rastreable). → Lorenzo + David (fotos).
4. Ritmo: 5 guías/semana sobre las consultas con intención de compra + 1 comparativa/mes. → Agente SEO.
5. Enviar UTM/canal/gclid en los formularios. → Lorenzo.

### 2. Google Ads (30 días)
| Campaña | Clics | Coste | Conversiones | CPA |
|---|---|---|---|---|
| Search · ES Compra | 632 | 536 € | 3 | 179 € |
| Shopping | 2.516 | 522 € | 2 | 261 € |
| Total | 3.148 | 1.058 € | 5 | 212 € |

Hecho esta semana: etiquetas de conversión reales (quiz enviado, chat contactado), 60+ negativas, 4 grupos de anuncio por categoría con URL propia (retro y plataformas activos; carretillas y telescópicos en pausa hasta que exista la página), conversiones offline desde Pipedrive preparadas.

**Qué mejorar**
1. Presupuesto: 20+20 €/día es muy poco para aprender. Propuesta 40 € Search + 50 € Shopping. → Maikel (OK).
2. Activar Data Manager API en Google Cloud para que las ofertas y ventas de Pipedrive vuelvan a Ads y la puja aprenda con ventas, no con formularios. → Maikel (1 clic).
3. Importar los eventos clave de GA4 (WhatsApp, CTA compra) como conversiones secundarias. → Agente Ads (cuando Maikel dé acceso de admin en Ads o lo haga él).
4. Merchant Center con todo el stock (hoy Shopping tiene una parte). → Lorenzo + David.
5. Landings por categoría (punto 1 de SEO) para activar los dos grupos pausados.

### 3. Outbound (Smartlead · frío Madrid)
| Dato | Valor |
|---|---|
| Leads cargados / enviados | 996 / 863 |
| Respuestas | 20 (2,3 %) · 21 clics · 27 rebotes |
| Envíos por paso | 1º 377 · 2º 222 · 3º 186 · 4º 78 |
| Clasificación de respuestas en Smartlead | ninguna (20 sin clasificar) |

**Qué mejorar**
1. Clasificar las 20 respuestas (interesado / no ahora / no es su área / baja) y que cada "interesado" sea un trato en Pipedrive con dueño. → Agente Outbound, hoy.
2. Tanda 2: 1.000 empresas nuevas (Barcelona, Valencia, Sevilla) con la lista de exclusión ampliada. Necesita clave de Apify. → Maikel.
3. Segundo ángulo: "compramos tu máquina" a propietarios (alquiladores, constructoras con parque), no solo "vendemos". Alimenta stock, que es el cuello de botella. → Agente Outbound.
4. Añadir 2 buzones para pasar de ~40 a ~100 envíos/día sin dañar la reputación.

### 4. Base de datos (Brevo · ABM)
| Dato | Valor |
|---|---|
| Envíos acumulados (10 campañas) | 12.244 · 26,2 % apertura · 56 personas con clic |
| Lanzamiento #220 (ayer) | 1.262 enviados · 283 aperturas · 1 clic |
| Mejor campaña | "Oportunidades bajo mercado" (13/08): 26 clickers · precio es lo que mueve |
| Pendiente de cargar | 3.112 históricos · 178 tratos perdidos reactivables |

**Qué mejorar**
1. Cargar los 3.112 históricos y los 178 perdidos en una lista "Reactivación" con una secuencia de 3 emails. → Maikel (fichero) + Agente BBDD.
2. Segmentar por interés real (qué clicó cada uno: plataformas, carretillas, movimiento de tierras) y enviar solo lo que encaja. Hoy todo va a todos.
3. Enriquecer empresa por dominio (tipo, tamaño, provincia) para priorizar llamadas.
4. Una campaña semanal fija (jueves 9:00) con precio visible y 4-6 máquinas. El precio dobla los clics.
5. Limpiar rebotes (44 ayer) y bajas cada semana.

### 5. CRM (Pipedrive + CRM visual)
| Dato | Valor |
|---|---|
| Ofertas vivas | 15 (12 en "Oferta enviada", 2 en entrega, 1 validada) |
| Nuevas este mes / ganadas | 2 / 0 |
| Leads nuevos 24 h (todo el pipeline) | 14 |

Hecho: CRM visual en ocasion.equipzilla.com/crm con usuarios personales (Maikel, Andrés, David, Héctor, Lorenzo), cola comercial unificada (Pipedrive + Brevo + Smartlead), tablero por etapas, cuentas, demandas, stock cruzado con demanda, notas que van a Pipedrive, aviso de stock nuevo a leads que encajan. Sin base de datos propia: Pipedrive es la fuente de verdad (contrato con Lorenzo en docs/crm-os/01-arquitectura-piloto.md).

**Qué mejorar**
1. Disciplina de etapas: todo lead nuevo tocado en < 24 h y con etapa cambiada. Hoy hay tratos en "Oferta enviada" desde hace semanas sin nota.
2. Motivo de pérdida obligatorio (precio, plazo, sin stock, no contesta, compró a otro). Sin eso no aprendemos.
3. Campo "canal de entrada" en Pipedrive alimentado por la web (UTM). → Lorenzo.
4. Registrar la demanda que no podemos servir (pide una retro de 8 t y no tenemos) como demanda captada para buscar stock.

### 6. Seguimientos
12 ofertas enviadas sin respuesta es el dinero más cercano (263.000 € en juego según la cola).

**Propuesta de cadencia** (la ejecuta el agente, la llamada la hace David/Héctor):
- D+2: llamada. Si no contesta, WhatsApp corto.
- D+5: email con alternativa (otra máquina similar más barata o más nueva) y pregunta directa: "¿sigue en pie?".
- D+10: último toque, "cierro la ficha, si cambia algo me dices". Se marca perdido con motivo.
- Cada mañana el agente pone en "Mi día" las 5 llamadas prioritarias con el guion y la máquina alternativa.

---

## Parte 2 · Arquitectura del equipo de agentes

Principio: un agente por canal, con entrada, salida, cadencia y KPI únicos. Yo (Director de Growth) orquesto, reporto a Maikel y doy indicaciones a cada agente. Ningún agente crea datos fuera de Pipedrive, Brevo, Smartlead, Ads, GA4 o el repositorio (contrato con tecnología).

```
                      MAIKEL (CEO) ─── Andrés (manager comercial)
                              │
                 DIRECTOR DE GROWTH (yo)
      parte diario 8:30 · plan semanal lunes · cierre viernes
                              │
   ┌──────────┬──────────┬────┴─────┬──────────┬──────────┬──────────┐
  SEO       ADS      OUTBOUND     BBDD/ABM     CRM/DATOS  SEGUIMIENTO  ANALÍTICA
   │          │          │            │            │            │           │
 guías    pujas     frío        Brevo      cola/score   copiloto     GA4/GSC
 GSC      negativas respuestas  reactivac. stock↔dem.  de David     panel
 landings landings  tanda 2     segmentos  alertas      cadencias    informes
                              │
                     PIPEDRIVE (fuente de verdad) ← David / Héctor ejecutan
```

| Agente | Misión | Entradas | Salidas | Cadencia | KPI que reporta |
|---|---|---|---|---|---|
| **Director de Growth** | Prioriza, alinea, decide qué se hace cada semana | Reportes de los 7 agentes, objetivo GMV | Parte diario, plan semanal, indicaciones a cada agente, escalado a Maikel | Diario 8:30 · Lunes · Viernes | Leads/semana, ofertas/semana, cierres, coste por lead por canal |
| **Agente SEO** | Traer demanda orgánica de compra | Search Console, consultas con intención, stock | 5 guías/semana, quick wins, propuestas de páginas a Lorenzo, enlazado interno | Publica L-V · informe viernes | Impresiones y clics de /compra/ y guías, consultas nuevas en top 20, leads SEO |
| **Agente Google Ads** | Leads de pago al menor CPA | Ads API, GA4, Pipedrive (gclid) | Ajuste de pujas y negativas, anuncios nuevos, conversiones offline subidas, alerta si CPA > 150 € | Diario 8:00 | Leads/día, CPA, % conversión a oferta |
| **Agente Outbound** | Conversaciones con empresas que no nos conocen | Apify/Smartlead, exclusiones, stock | Listas nuevas, secuencias, clasificación de respuestas, trato en Pipedrive por cada interesado, aviso a David en < 1 h | Vigilante cada hora · tanda nueva quincenal | Respuestas positivas/semana, tratos creados, reuniones |
| **Agente Base de datos** | Sacar oportunidades de los 5.000+ contactos que ya tenemos | Brevo, histórico, clics | Campaña semanal, segmentos por interés, reactivación, higiene de lista, clickers a la cola | Jueves 9:00 envío · limpieza lunes | Clickers/semana, leads de BBDD, bajas |
| **Agente CRM / Datos** | Que la cola sea fiable y nadie se pierda | Pipedrive, Brevo, Smartlead, stock | Cola comercial, score, stock↔demanda, aviso de stock nuevo, integridad, informe del piloto para Lorenzo | Cada hora | Tiempo a primer contacto, leads sin dueño, tratos sin actividad > 7 d |
| **Agente Seguimiento** | Que ninguna oferta muera en silencio | Ofertas abiertas, notas, stock | "Mi día" con 5 llamadas, borradores de email/WhatsApp, alternativa de máquina, autopsia de perdidos | Diario 8:00 · autopsia viernes | Ofertas contestadas, ofertas cerradas (ganadas o perdidas con motivo), días en "Oferta enviada" |
| **Agente Analítica** | Una sola verdad de los números | GA4, GSC, Ads, Brevo, Smartlead, Pipedrive | Panel en vivo, informe 7 h / 17 h, tabla mensual, alertas de caída | Cada hora · 8:00 · 15:00 | Embudo completo por canal: visitas → leads → ofertas → ventas |

### Cómo nos alineamos
- **8:30 parte diario** (Discord): leads nuevos, ofertas tocadas, lo que hay que hacer hoy. Lo redacto yo con lo que me reportan los agentes.
- **Lunes plan semanal**: 3 prioridades por agente. Maikel y Andrés lo aprueban o cambian.
- **Viernes cierre**: KPI de la semana contra objetivo, qué funcionó, qué se para.
- **Mensual**: revisión de canal por coste por lead y por oferta; se mueve presupuesto al que mejor convierte.
- Cualquier envío a clientes (campaña, secuencia nueva) pasa por OK humano. Las llamadas y las ofertas las hacen David y Héctor; los agentes preparan, no cierran.

### Cómo se implementa (sin nueva capa tecnológica)
Cada agente es una rutina programada con su script en el repositorio `equipzilla` (ya existen: panel horario, vigilante, informe 8:00/15:00, parte diario, cola comercial, aviso de stock, conversiones offline, publicación de guías). Lo que falta es formalizar tres rutinas nuevas (Ads diario, Seguimiento diario, BBDD semanal) y que cada una escriba su reporte en el mismo sitio (Sheet de mando + Discord). No hay servidores nuevos ni bases de datos nuevas.

---

## Parte 3 · Prioridades próximas 2 semanas
| # | Acción | Quién | Impacto |
|---|---|---|---|
| 1 | Llamar las 12 ofertas en "Oferta enviada" con la cadencia D+2/5/10 | David, Héctor (Agente Seguimiento prepara) | Es el dinero más cercano |
| 2 | Clasificar las 20 respuestas del frío y crear tratos | Agente Outbound → David | Leads calientes ya pagados |
| 3 | Presupuesto Ads 40/50 €/día + Data Manager API | Maikel | Duplicar leads de pago |
| 4 | Páginas de categoría (carretillas, telescópicos, retro) + UTM en formularios | Lorenzo | Activa 2 grupos de Ads y mide SEO |
| 5 | Clave Apify → tanda 2 de frío (1.000 empresas) + ángulo "compramos tu máquina" | Maikel → Agente Outbound | Más conversaciones y más stock |
| 6 | Cargar 3.112 históricos + 178 perdidos → reactivación | Maikel (fichero) → Agente BBDD | Oportunidades a coste cero |
| 7 | Campaña semanal jueves con precio visible | Agente BBDD (OK Maikel) | Clics x2 respecto a sin precio |
| 8 | Motivo de pérdida obligatorio y leads tocados < 24 h | Andrés | Aprender y no perder leads |

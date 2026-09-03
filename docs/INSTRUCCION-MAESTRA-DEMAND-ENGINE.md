# Instrucción maestra · Equipzilla Demand Engine

> Modo de operación oficial desde el 03/09/2026 (Maikel). Sustituye al modo
> "asistente que propone": a partir de aquí el ciclo es
> **analizar → decidir → ejecutar → medir → reportar → aprender → repetir**.
> Documento fuente: `docs/EQUIPZILLA-DEMAND-ENGINE.pdf`.

## Objetivo (31/12/2026)
**25 operaciones · 500.000 € GMV · ticket medio 20.000 €**
Escenario base: 350 leads → 128 ofertas (≥40%) → 25 ventas (≥20%).

| Mes | Leads | Ofertas | Ventas | GMV |
|---|---:|---:|---:|---:|
| Septiembre | 45 | 18 | 3 | 60.000 € |
| Octubre | 85 | 32 | 5 | 100.000 € |
| Noviembre | 105 | 38 | 8 | 160.000 € |
| Diciembre | 115 | 40 | 9 | 180.000 € |

## Cuota de leads por canal (~88/mes)
Reactivación 25 · Ads 20 (desde octubre) · Llamadas 15 · Inbound 12 ·
Frío 12 · SEO 4 · LinkedIn sin cuota (ABM: conversación → oportunidad).

## Reglas que mandan sobre cualquier otra
1. **No inventar datos** — máquinas, precios, horas, empresas, resultados.
   Si un dato no está, se dice que no está. Fuente de producto:
   `data/machines.json` y el CRM, nunca la memoria.
2. **Todo termina en Pipedrive.** El Sheet/panel es capa de análisis, no una
   realidad paralela.
3. **Autonomía**: si la acción está en el plan, usa herramientas autorizadas y
   no es estratégica ni arriesgada → se ejecuta sin preguntar.
4. **Aprobación** para lo irreversible o de impacto económico: envíos de
   campaña, cambios de presupuesto/puja, comunicaciones sensibles, borrados.
5. **Alerta temprana antes que informe bonito.** Si algo va por debajo de
   objetivo o un canal no funciona, se dice el primero.
6. **Jerarquía de valor**: venta > oferta > oportunidad > lead cualificado >
   lead > interacción. No optimizar métricas aisladas.

## Scoring y cola comercial
Todo lead se clasifica por fit · intención · recencia · necesidad ·
presupuesto · matching → 🔥 HOT / 🟠 WARM / 🔵 NURTURE / ⚪ LOW.
La salida a comercial nunca es una lista de leads: es una **cola de
oportunidades priorizadas** con empresa, contacto, ICP, necesidad,
presupuesto, ubicación, origen, score, máquinas que encajan, recomendación,
última actividad y siguiente acción.

## SLA y seguimiento
Primer contacto **<60 min en septiembre → <15 min desde octubre** (HOT).
Toda oferta: **5 toques / 21 días**. Detectar y escalar lo que se enfría.

## Métricas de calidad
Frío ≥2,5% respuesta (sept) → ≥4% (dic) · campañas segmentadas ≥20% apertura ·
motivos de pérdida "OTRAS-General" del 38,7% a **<10%** ·
lead→oferta ≥40% · oferta→venta ≥20%.

## Ciclo diario
Revisar → priorizar → ejecutar → detectar → actualizar → reportar → aprender.
El informe diario sigue el formato del §27 del documento fuente
(`DAILY GROWTH REPORT`). Cada día debe responder: qué ha pasado, qué hemos
aprendido, qué vamos a hacer ahora. Cada lunes: cuánto falta para 25/500k.

## Infraestructura ya operativa (03/09)
- `scripts/panel_horario.py` — panel en vivo cada hora al Sheet de mando
  (Brevo + Smartlead + Google Ads + funnel de compraventa) y cola de clics.
- `scripts/informe_respuestas.py` — respuestas y scoring a las 8:00 y 15:00,
  sólo si hay señal nueva; alta en Pipedrive y aviso al equipo.
- `scripts/update_diario.py` — parte diario 8:30.
- `scripts/ads_metricas.py` — KPIs de Google Ads (cuenta 3057448284).
- `scripts/seo_research.py` + `seo/` — máquina SEO (DinoRank).
- Playbooks: ABM, outbound, Google Ads, base de conocimiento, ICP, KPIs.

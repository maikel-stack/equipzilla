# EQUIPZILLA CRM OS · Diseño V1

> **Nota 10/09/2026**: este documento es la *especificación del modelo de datos* que negocio entrega a tecnología, no una base de datos a desplegar en el piloto. El piloto corre sobre Pipedrive + vistas derivadas, sin base de datos propia. Ver `01-arquitectura-piloto.md`.

Documento de diseño previo a la implementación (instrucción maestra, punto 60).
Cubre: arquitectura, modelo de datos, entidades, relaciones, estados, permisos,
eventos, APIs, scoring, workflows, UX y MVP. El esquema físico está en
`docs/crm-os/schema.sql`.

Fecha: 09/09/2026 · Autor: Cerebro Operativo de Growth + Ventas · Para: Maikel, Andrés

---

## 0. Regla de oro y punto de partida

**FIT × INTENT × RECENCY × VALUE**, no lead count. La unidad central es **la
necesidad de compra**, no la empresa ni el lead.

Punto de partida real (no hipotético):

| Fuente hoy | Qué tiene | Qué pasa a ser en el CRM OS |
|---|---|---|
| Pipedrive (pipeline 6 «Transaccional», 195 tratos compra, 178 perdidos / 2 ganados) | tratos con persona, assetType, assetUse, Razón Social, gclid | `opportunities` + `demands` + `companies` + `contacts` (migración) |
| Brevo (listas ABM «Alquiló X», «Reactivación», clics por campaña) | contactos con EMPRESA, RAZON_SOCIAL, ACTIVIDAD, TELEFONO; clics por máquina | `contacts` + `intent_signals` (clic, apertura) + `campaigns` |
| Smartlead (frío Madrid, 996 leads, respuestas y clics) | empresa, email, respuesta en texto | `companies` + `intent_signals` (respuesta, clic) + `demands` (texto → necesidad) |
| Web (quiz, chat, formularios en Vercel) | nombre, teléfono, máquina, presupuesto, zona | `demands` + `intent_signals` (formulario, precio, calculadora) |
| Sheet «Stock Outreach PANEL» de David (117 filas) | ref, familia, máquina, año, horas, precio, salida | `machines` (+ `suppliers`) |
| Histórico de demanda (~3.112 registros) | empresa, qué pidió, cuándo | `demands` en estado `REACTIVATION` + `companies` |
| Cola comercial / CRM visual (ocasion.equipzilla.com/crm) | score, canal, etapa, propietario, notas | se convierte en **Priority Queue** + **My Day** del OS |

Todo lo que ya se ha construido (vigilante horario, cola comercial, panel,
CRM visual, aviso de stock) es la **capa de ingestión y la V0 de UX**. No se
tira: se reconecta a la base de datos nueva.

---

## 1. Arquitectura

```
                 ┌──────────────── INGESTIÓN (conectores) ────────────────┐
  Pipedrive ─────┤  Brevo  ─ Smartlead ─ Web (quiz/chat/forms) ─ Stock Sheet │─ Histórico 3.112
                 └───────────────────────────┬─────────────────────────────┘
                                             ▼  eventos normalizados
                                    ┌─────────────────┐
                                    │  IDENTIFICACIÓN │  dedupe → company / contact
                                    └────────┬────────┘
                                             ▼
        ┌───────────────────────── CRM DATABASE (Postgres) ─────────────────────────┐
        │ companies · contacts · demands · intent_signals · opportunities · machines │
        │ machine_matches · activities · tasks · offers · deals · suppliers · …      │
        │ events (append-only) · scores · score_events · audit_logs                  │
        └───────┬───────────────┬──────────────────┬──────────────────┬──────────────┘
                ▼               ▼                  ▼                  ▼
        SCORING ENGINE    MATCHING ENGINE    AUTOMATION ENGINE     AI LAYER (Claude)
        fit·intent·       demand ↔ machine   reglas SI/ENTONCES     agentes: qualification,
        recency·value     explicable         → tasks/notifs         buyer intel, matching,
                                                                    follow-up, copilot
                ▼               ▼                  ▼                  ▼
        ┌──────────────────────────── API (REST, JSON, token) ──────────────────────┐
        └──────────────────────────────────┬────────────────────────────────────────┘
                                           ▼
                 UI (Vercel, /crm): My Day · Priority Queue · Account 360 · Opportunity 360
                 · Demandas · Stock & matching · Dashboards (CEO / Sales / Demanda / Mercado)
```

Decisiones de arquitectura:

- **Base de datos**: Postgres. Recomendación: Neon (serverless) conectado al
  proyecto Vercel `equipzilla-quiz` vía Marketplace (`DATABASE_URL`). Es lo
  único que no puedo crear yo: necesita la cuenta de Vercel de Qualivo/Equipzilla.
- **Backend**: funciones serverless Node en `quiz/api/` (ya existen `crm.js`,
  `lead.js`, `chat.js`, `metrics.js`). Se organizan en `api/crm/*`.
- **Ingestión**: los scripts Python actuales (`informe_respuestas`,
  `cola_comercial`, `aviso_stock_leads`, `panel_horario`) pasan a escribir
  eventos en la API del CRM en vez de en Sheets. Las rutinas siguen igual.
- **Pipedrive en V1**: sigue siendo la fuente de verdad de etapas y notas
  (sincronización de lectura cada 15 min + escritura de etapa/nota como hoy).
  En V1.5 se decide el corte. Así el equipo no cambia de herramienta de golpe.
- **IA**: Claude API (modelo `claude-opus-5`, thinking adaptativo) sobre datos
  estructurados. Cada agente recibe el JSON de la entidad y devuelve JSON con
  `explicacion[]`. Nada de chat libre en V1.
- **API-first**: la UI solo habla con la API. Los scripts también.
- **Separación**: CRM DB ≠ marketplace (machines se sincroniza, no se duplica
  el catálogo web) ≠ analytics (vistas materializadas) ≠ comunicación (Brevo,
  Smartlead, WhatsApp) ≠ IA ≠ automatización.

---

## 2. Modelo de datos (entidades y relaciones)

```
companies 1─n contacts
companies 1─n demands ─n intent_signals
companies 1─n opportunities ─n activities, tasks, offers
demands   1─n machine_matches n─1 machines n─1 suppliers
opportunities 1─1 deals 1─n deal_items n─1 machines
demands   1─n sourcing_requests
companies 1─n rental_history
campaigns 1─n campaign_members n─1 contacts
scores (snapshot por entidad) · score_events (explicación) · events (append-only)
users n─1 teams · tags n─n (entity_tags) · audit_logs · ai_insights · lost_reasons
```

Cobertura del «modelo de datos mínimo (7 entidades)» de Qualivo: 1 Máquinas
(ledger) = `machines` (propietario, semáforo, PVP ágil 60–90 d, precio compra
teórico, alta/baja, publicado_en, verificado_en) · 2 Propietarios/alquiladores =
`suppliers` · 3 Clientes = `companies` (ICP, canal_origen, índice de
recurrencia) + `rental_history` · 4 Leads/oportunidades = `opportunities` con
`lost_reasons` codificados · 5 Ofertas = `offers` (alternativas B y C) ·
6 Operaciones = `deals` (margen, días desde alta/lead, desviación vs PVP,
servicios) · 7 Demanda capturada = `demands` (se cruza con cada alta de
`machines` → `machine_matches` → notificación). Además `stage_history` (de → a,
quién, cuándo) para medir tiempos y `channel_costs` para el CAC.

Claves de deduplicación (unique parciales, ver schema.sql):

- `companies`: `cif` (si existe) · `dominio` (si no es genérico) · `nombre_normalizado + provincia`.
- `contacts`: `email` (lower) · `telefono_normalizado` (E.164).
- `machines`: `ref` (referencia interna) o `source + source_id`.
- `intent_signals`: `source + source_id` (un clic de Brevo no entra dos veces).

Regla: **nunca se borra físicamente**. `deleted_at` y `merged_into_id` en
companies/contacts; `audit_logs` guarda quién cambió qué y el valor anterior.

Campos completos en `schema.sql`. Resumen de lo específico de Equipzilla:

- `companies.icp` ∈ {A comprador profesional, B industria/logística, C obra/modular, D alquiler} + `icp_secundario`, `fit_score`, `intent_score`, `recency_score`, `value_score`, `total_score`, `lifecycle_stage`, `excluded` + `excluded_reason`.
- `demands`: tipo_maquina, categoría, marca, modelo, peso, potencia, año/horas min-max, presupuesto min-max, ubicación + radio, accesorios, uso, urgencia, financing/renting/buy, `status`, `expires_at`. **Existe aunque no haya máquina** (demanda capturada).
- `intent_signals.type` ∈ {solicitud_compra, respuesta_outbound, respuesta_whatsapp, email_abierto, email_respondido, clic, visita_repetida, consulta_maquina, solicitud_precio, solicitud_disponibilidad, calculadora_rent_vs_buy, alerta_creada, descarga, formulario, historico_alquiler, renting, visita_categoria}; `strength` viene de `score_rules` (configurable), no del código.
- `machines`: categoría, tipo, marca, modelo, año, horas, precio, precio_propietario, ubicación, `supplier_id`, estado, equipamiento, accesorios, fotos (URL internas), disponibilidad, `source`, `verificado_en` (última verificación con el propietario).
- `opportunities`: company, contact, demand, owner, source, campaign, `stage` (configurable en `pipeline_stages`), expected_value, probability, expected_margin, next_action, next_action_date, close_date, `lost_reason_id` obligatorio al perder.
- `deals` / `deal_items`: precio final, margen €, servicios (transporte, garantía, mantenimiento), días desde alta de máquina y desde demanda.

---

## 3. Estados

**demands.status**: NEW → QUALIFYING → ACTIVE → SOURCING → MATCHED → NEGOTIATING → WON | LOST | EXPIRED | REACTIVATION.
Transiciones automáticas: ACTIVE sin match 24 h → SOURCING; sin actividad > `expires_days` (por categoría) → EXPIRED; nueva señal sobre EXPIRED/LOST → REACTIVATION.

**opportunities.stage** (tabla `pipeline_stages`, editable): NEW → QUALIFIED → SOURCING → MATCHED → CONTACTED → INTERESTED → MACHINE_REVIEW → OFFER → NEGOTIATION → WON | LOST.
Mapeo con Pipedrive durante V1: Lead recibido = NEW · Enviar oferta = QUALIFIED/MATCHED · Oferta enviada = OFFER · Aceptada = NEGOTIATION · Alquilador asignado / Entrega = WON (en curso).

**companies.lifecycle_stage**: PROSPECT → ENGAGED → CUSTOMER → RECURRING → DORMANT · EXCLUDED (con motivo).

**machines.estado**: DISPONIBLE · RESERVADA · VENDIDA · RETIRADA · PENDIENTE_VERIFICAR.

**tasks.status**: OPEN → DONE | SKIPPED (con motivo).

---

## 4. Scoring (configurable, explicable)

Cuatro dimensiones, cada una 0–100, guardadas por separado en `scores`:

- **FIT** (¿podría comprar?): reglas en `score_rules(kind='fit')` sobre sector, actividad, tamaño, flota, ICP, localización, histórico, ticket potencial. Ej.: `actividad ~ excavac|movimiento de tierras` → +30; ICP A → +25; flota propia → +15; excluida → 0.
- **INTENT** (¿busca ahora?): suma de `intent_signals.strength` de los últimos N días, con frecuencia (nº señales distintas) y tipo. Ej.: solicitud_compra 40 · respuesta_outbound 30 · solicitud_precio 30 · clic 8 · apertura 2.
- **RECENCY**: `intent_decay` exponencial sobre `days_since_last_intent` (vida media configurable, inicial 14 días). Se guardan `last_intent_at`, `recent_signal_count`, `recent_high_intent_signals`.
- **VALUE**: presupuesto de la demanda o valor esperado de la oportunidad, normalizado por categoría.

`total = w_fit·FIT + w_intent·INTENT + w_recency·RECENCY + w_value·VALUE` con pesos en `score_config` (inicial 0.25 / 0.35 / 0.25 / 0.15). Umbrales iniciales HOT ≥ 80, WARM 60–79, NURTURE 40–59, LOW < 40; también en `score_config`.

**Explicabilidad**: cada recálculo escribe en `score_events` la lista de reglas
aplicadas con su aporte («ICP A +25», «respondió hace 2 días +30», «sin
presupuesto −0»). La UI muestra siempre la lista, nunca solo el número.

**Calibración**: `score_events` + `deals` permiten medir qué reglas predicen
oferta, cierre y margen. En V2 se ajustan pesos con datos; en V1 solo se
registran.

---

## 5. Eventos (event model)

Tabla `events` append-only: `event_id, type, occurred_at, company_id, contact_id, demand_id, opportunity_id, machine_id, source, source_id, payload jsonb, actor_user_id`.

Tipos V1: company_created, contact_created, demand_created, intent_detected,
machine_viewed, machine_clicked, quote_requested, message_sent, message_replied,
call_completed, offer_created, machine_matched, deal_won, deal_lost,
rental_completed, alert_created, stage_changed, note_added, task_created, task_done.

Los eventos alimentan scoring (trigger a recálculo), timeline (Account 360) y automatizaciones.

---

## 6. Matching (demand ↔ machine)

`match_score` 0–100 explicable, calculado al crear/actualizar una demanda o
una máquina. Factores y pesos iniciales (tabla `match_config`):

| Factor | Peso | Regla |
|---|---|---|
| categoría / tipo | 30 | igual = 30; familia compatible = 15 |
| presupuesto | 20 | dentro = 20; ±15 % = 12; ±30 % = 5 |
| año | 10 | dentro de min-max = 10 |
| horas | 10 | ≤ horas_max = 10; ≤ +20 % = 5 |
| ubicación | 10 | misma provincia = 10; radio = 6; misma CCAA = 3 |
| marca / modelo pedido | 10 | modelo = 10; marca = 6 |
| características / accesorios | 5 | cada coincidencia +2,5 |
| disponibilidad / urgencia | 5 | disponible y urgente = 5 |

Salida: `machine_matches(demand_id, machine_id, score, explicacion jsonb)`.
Bandas: ≥ 90 excelente · 75–89 muy bueno · 60–74 razonable · < 60 baja prioridad.
Automatización: nueva máquina con match ≥ 90 → notificación al owner de la demanda
(es la versión estructurada de `aviso_stock_leads.py`).

---

## 7. APIs (V1, REST, JSON, token de usuario)

```
POST /api/crm/auth/login                       → token (usuario + rol)
GET  /api/crm/my-day                           → HOT, follow-ups, new intent, new demands, sourcing, at-risk
GET  /api/crm/queue?owner=&icp=&limit=          → priority queue explicada
GET/POST/PATCH /api/crm/companies[/:id]        · GET /companies/:id/360
GET/POST/PATCH /api/crm/contacts[/:id]
GET/POST/PATCH /api/crm/demands[/:id]          · GET /demands/:id/matches
POST /api/crm/signals                           (ingestión: conectores y web)
GET/POST/PATCH /api/crm/opportunities[/:id]    · GET /opportunities/:id/360 · POST /:id/stage · POST /:id/lose
GET/POST/PATCH /api/crm/machines[/:id]         · POST /machines/sync (desde Sheet/marketplace)
GET/POST/PATCH /api/crm/activities · /tasks · /offers · /deals
POST /api/crm/ingest/{pipedrive|brevo|smartlead|web|historico|stock}   (idempotente por source_id)
GET  /api/crm/search?q=                          (empresa, CIF, contacto, máquina, demanda, teléfono, email)
GET  /api/crm/dashboards/{ceo|sales|demand|market|growth}
POST /api/crm/ai/{qualify|buyer-brief|next-action}   (V1: solo lectura y explicación)
```

Todas las escrituras registran `audit_logs` y emiten `events`. Todas las
listas aceptan filtros (`icp`, `score_min`, `status`, `owner`, `categoria`,
`provincia`, `since`) y paginación.

---

## 8. Permisos

Roles en `users.role`: `sales` (ve y edita lo asignado + cola), `manager`
(ve el equipo, reasigna), `admin` (todo, configuración de scoring y pipeline),
`marketing` (campañas + dashboards, sin teléfonos de leads no asignados),
`sourcing` (demandas + máquinas + proveedores). Permiso por objeto y acción en
`permissions(role, object, action)`; comprobación en la API, no en la UI.

Usuarios iniciales: Maikel (admin), Andrés (manager), David (sales), Héctor
(sales), Zilia (sales), Lorenzo (admin técnico).

---

## 9. UX V1

Principio: cada pantalla responde «¿qué necesito hacer ahora?». Estilo: el
sistema visual ya definido (Archivo + IBM Plex, teal #0D9488, tinta #14181C),
sin gráficos decorativos. Móvil: My Day, ficha, llamar, WhatsApp, nota, tarea.

1. **My Day** (inicio de sales): HOT · Follow-up hoy · New intent · New demands · Sourcing · At risk · Recomendaciones IA. Cada fila: quién, por qué (explicación del score), siguiente acción, botones llamar / WhatsApp / nota / hecho.
2. **Priority Queue**: «¿A quién contacto ahora?» ordenada por total_score × valor × probabilidad, con la explicación en una línea («Respondió ayer al frío: busca una mixta de 30–40k → LLAMAR AHORA»). Es la evolución de la cola comercial actual.
3. **Account 360**: identidad y contactos · fit (ICP + score explicado) · intent (señales recientes) · demandas · historial (compras, alquileres, oportunidades) · timeline de actividad · máquinas consultadas/propuestas · pipeline · revenue/margen · memoria comercial (objeciones, presupuesto, máquinas descartadas) · AI insights.
4. **Opportunity 360**: cliente · necesidad · intención · máquinas candidatas con match explicado · actividades y conversaciones · oferta · alternativas · probabilidad, valor, margen · próxima acción · riesgos · recomendación IA. Perder exige motivo.
5. **Demandas**: tablero por status; «demanda sin matching» destacada → botón «crear sourcing».
6. **Stock & matching**: inventario con demanda que encaja (lo que hoy es la vista Stock del CRM visual) + «demanda sin stock».
7. **Dashboards**: CEO (pipeline, revenue, margen, win rate, forecast, ICP y canal), Sales (pipeline, tareas, HOT, conversión), Demanda (activas, no cubiertas, categorías, presupuestos, ubicaciones), Mercado (inventario, precios, gaps).

---

## 10. Ingestión y migración

| Origen | Cómo entra | Reglas |
|---|---|---|
| Pipedrive | sync cada 15 min (deals abiertos + cerrados 180 d, persons, notes, activities) | título `Prospecto - Respuesta frío` → source smartlead; gclid real → source google_ads; `assetType` + `assetUse` → demand; `Razón Social` → company; etapa → stage mapeada; notas → activities |
| Brevo | listas ABM → contacts/companies (EMPRESA, RAZON_SOCIAL, ACTIVIDAD, TELEFONO); clics → intent_signals(clic, máquina) ; aperturas → signal débil | `source_id = campaña+email+url` |
| Smartlead | leads → companies/contacts; respuestas → intent_signals(respuesta_outbound) + demand (texto clasificado: MAQUINA/RECHAZO/AUTOREPLY, lo que hace `informe_respuestas.py`) | rechazo → company.excluded=false pero signal negativa; autoreply → ignorar |
| Web (quiz, chat, formularios) | `api/lead.js`, `api/chat.js`, `api/submit.js` llaman a `POST /api/crm/ingest/web` además de Pipedrive | identificación por email/teléfono; crea demand + signal(formulario/solicitud_precio) |
| Stock Sheet de David | `POST /machines/sync` cada hora | ref o fila como source_id; cambios de precio → event |
| Histórico 3.112 | importación única (CSV) | companies + demands(status REACTIVATION, expires_at pasado); no cuentan como intent hasta nueva señal |
| Alquiler (rental_history) | importación desde Pipedrive «Alquiler» y listas Brevo «Alquiló X» | alimenta módulo rent→buy (V1.5) |

Deduplicación en ingestión: normalizar nombre (minúsculas, sin S.L./S.A./tildes),
dominio del email (ignorar gmail/hotmail…), teléfono E.164, CIF. Conflictos
→ `merge_candidates` para revisión humana, nunca sobrescritura silenciosa.

---

## 11. Automatizaciones V1 (motor de reglas, tabla `automations`)

1. total_score > 80 → task «LLAMAR HOY» al owner (o a la cola si no hay owner).
2. demand ACTIVE sin match ≥ 60 durante 24 h → status SOURCING + sourcing_request.
3. nueva machine con match ≥ 90 → notificación al owner de cada demanda (email + My Day).
4. opportunity sin actividad X días (por etapa: OFFER 5 d, INTERESTED 7 d) → «at risk» en My Day.
5. señal nueva sobre company DORMANT o demand REACTIVATION → opportunity de reactivación.
6. rental_history: ≥ 3 alquileres misma categoría en 12 meses → task «evaluar rent vs buy» (V1.5).
7. lost → exige lost_reason; genera event deal_lost para Growth.

Notificaciones solo accionables: cliente caliente, máquina encaja ≥ 90,
demanda 24 h sin matching, oportunidad enfriándose, histórico que vuelve.

---

## 12. IA (V1: explicación; V1.5–V2: acción)

Agentes como funciones puras sobre JSON (Claude API, salida JSON validada):

- **Qualification agent** (V1): explica fit/intent/recency con las reglas aplicadas; propone ICP cuando falta.
- **Buyer intelligence agent** (V1): resumen de la empresa y la necesidad a partir de señales, respuestas y notas («busca mixta 30–40k, obra en Toledo, urgente»).
- **Follow-up agent** (V1): next best action justificada («Llamar hoy: respondió ayer y no tiene oferta»).
- **Matching agent** (V1.5): reordena candidatas y redacta por qué.
- **Sourcing / Reactivation / Market intelligence / Growth agent** (V2).

Regla: la IA lee `events`, `scores`, `demands`, `machine_matches`; nunca decide
sola una etapa ni envía nada a clientes.

---

## 13. MVP y calendario

**V1 (3 sprints de 1 semana, tras tener la base de datos)**

- Sprint 1 · datos: Postgres + schema + migraciones; conectores Pipedrive, Brevo, Smartlead, web, stock, histórico; dedupe; API base; auth por usuario.
- Sprint 2 · operación: scoring configurable + explicación; Priority Queue; My Day; Account 360; Opportunity 360 (mover etapa, perder con motivo, notas, tareas); búsqueda global; filtros.
- Sprint 3 · inteligencia mínima: matching explicable + vista Stock; automatizaciones 1–5; dashboards CEO / Sales / Demanda; agentes de explicación; importación CSV; criterios de aceptación.

**V1.5**: WhatsApp y email desde la ficha, sourcing completo, rent→buy, reactivación automática, corte con Pipedrive.
**V2**: copilot, market intelligence y benchmark de precios, demand intelligence, scoring predictivo calibrado con datos.

**Criterio de éxito V1**: un comercial abre My Day y en < 30 s responde las 10
preguntas del punto 62; Dirección responde las suyas con los dashboards CEO y
Demanda sin pedir un Excel.

---

## 14. Decisiones que necesito

1. **Base de datos**: Neon Postgres vía Vercel Marketplace en el proyecto `equipzilla-quiz` (plan gratuito para V1). Hay que activarlo desde el panel de Vercel; en cuanto exista `DATABASE_URL`, ejecuto el esquema y arranco el Sprint 1.
2. **Pipedrive** durante V1: mantenerlo como fuente de verdad con sincronización bidireccional (mi recomendación), o cortar ya. Cortar ya implica que el equipo deja de usar Pipedrive desde el primer día y que el histórico de 178 perdidos se migra sin actividad.
3. **Usuarios y roles** iniciales (propuesta en el punto 8) y si Zilia / Andrea López siguen llevando compraventa además de alquiler.
4. **Histórico 3.112**: dónde está (CSV, Sheet, Pipedrive) para preparar la importación.
5. **Dominio**: seguir en ocasion.equipzilla.com/crm o pedir a Lorenzo `crm.equipzilla.com`.

Con la base de datos creada empiezo a construir; sin ella, el resto del diseño
(esquema, conectores, scoring, UI) puede avanzar en local y sobre datos de
prueba, pero no se puede poner en manos del equipo.

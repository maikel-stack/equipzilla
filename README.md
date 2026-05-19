# Equipzilla Bot System — Documentación Técnica

Sistema de automatización para **Equipzilla** (marketplace B2B de alquiler de maquinaria industrial en España), construido sobre **n8n Cloud** + **Claude AI** + **Pipedrive CRM** + **respond.io (WhatsApp)**.

---

## Arquitectura general

```
Cliente web
    │
    ▼
Formulario web ──► Pipedrive (nuevo deal)
                        │
                        ▼ webhook
                   ┌────────────────────────────────────────────────────┐
                   │  n8n Cloud (equipzillaproduccion.app.n8n.cloud)    │
                   │                                                    │
                   │  1. Lead Scoring Bot  ──► Discord/Slack alert      │
                   │  2. Auto Presupuesto  ──► WhatsApp + nota CRM      │
                   │  3. Gestor Respuestas ◄── WhatsApp reply           │
                   └────────────────────────────────────────────────────┘
                        │                        ▲
                        ▼                        │
                   respond.io (WhatsApp) ────────┘
                        │
                        ▼
                   Cliente recibe presupuesto y responde SÍ/NO
```

---

## Workflows

### 1. A03 · Lead Scoring Bot (`xHPqfbcBfzRi9mwy`)

**Trigger:** Pipedrive webhook `pipedrive-lead` (webhook ID Pipedrive: 1890348)

**Flujo:**
1. Extrae datos del deal (máquina, empresa, duración, CIF, teléfono)
2. Llama a Claude con criterios de scoring ponderados
3. Escribe nota en Pipedrive con puntuación 1-10 + tier ALTO/MEDIO/BAJO
4. Envía alerta a Discord con resumen y acción recomendada

**Scoring Claude — Criterios:**
| Criterio | Peso | Descripción |
|----------|------|-------------|
| Duración del alquiler | 35% | 1-3d→bajo, 1-3sem→medio, 1+mes→alto |
| Tipo de empresa | 25% | Con CIF > empresa pequeña > particular |
| Tipo de maquinaria | 20% | Pesada/especializada > estándar |
| Información completa | 10% | Presupuesto y localización definidos |
| Señales de recurrencia | 10% | Contrato/gestión, cliente existente |

**Tiers:**
- `ALTO (7-10)` → Contactar en < 2 horas
- `MEDIO (4-6)` → Contactar en el día
- `BAJO (1-3)` → Nurturing automático

---

### 2. A03 · Auto Presupuesto (`axdargrbpFiIMHwt`)

**Trigger:** Pipedrive webhook `pipedrive-quote` (webhook ID Pipedrive: 1891384)

**Flujo:**
```
Webhook ──► Extraer datos ──► Preparar payload Claude ──► Claude calcula
                                                                │
                              ┌─────────────────────────────────┘
                              ▼
                    ¿can_quote=true AND total<1000 AND tiene teléfono?
                              │
               ┌──────────────┴──────────────┐
              SÍ                            NO
               │                             │
               ▼                             ▼
        Enviar WhatsApp            Nota: requiere revisión manual
               │ (onError: continue)
               ▼
        Añadir nota Pipedrive
               │
               ▼
        Mover a "Oferta enviada" (stage 37)
```

**Lógica de tarifa GAM 2026:**
- Alquiler **< 7 días** → tarifa **P3** (63% del PVP)
- Alquiler **≥ 7 días** → tarifa **P4** (54% del PVP)
- `base = tarifa_diaria × días`
- `seguro = base × 15%`
- `ecofee = 15€` (siempre)
- `batería = 10€` (solo máquinas eléctricas)
- `total = base + seguro + ecofee + batería`

**Condición auto-presupuesto:**
- `can_quote = true` (Claude identifica la máquina en tarifa)
- `total < 1.000€`
- Teléfono del cliente disponible

**Nodos clave:**

| Nodo | Tipo | Descripción |
|------|------|-------------|
| `Pipedrive Webhook` | Webhook | Recibe POST de Pipedrive |
| `Webhook Response` | Respond | Responde OK inmediatamente |
| `Extraer datos del deal` | Code | Parsea deal, normaliza teléfono a E.164 |
| `Preparar payload Claude` | Code | Construye objeto JS con system prompt + tarifa completa |
| `Claude · Calcular Presupuesto` | HTTP | POST `https://api.anthropic.com/v1/messages` |
| `Parsear presupuesto` | Code | Parsea JSON de Claude, strip markdown |
| `¿Auto presupuesto posible?` | IF | Condición triple: can_quote + total + phone |
| `Enviar WhatsApp Oferta` | HTTP | POST `https://api.respond.io/v2/contact/phone:{phone}/message` |
| `Añadir nota presupuesto Pipedrive` | HTTP | POST `/v1/notes` con tag `[EQUIPZILLA_QUOTE]` |
| `Mover a Oferta enviada` | HTTP | PUT `/v1/deals/{id}` → stage 37, pipeline 6 |
| `Nota: no auto presupuesto` | HTTP | POST `/v1/notes` con motivo de revisión manual |

**JSON devuelto por Claude:**
```json
{
  "can_quote": true,
  "machine_matched": "Tijera eléctrica 10m",
  "tariff_period": "P3",
  "days": 2,
  "daily_rate": 46.62,
  "base_price": 93.24,
  "insurance": 13.99,
  "ecofee": 15.00,
  "battery": 10.00,
  "total": 132.23,
  "currency": "EUR",
  "whatsapp_text": "Hola Maikel, te enviamos tu presupuesto...",
  "note_text": "PRESUPUESTO AUTOMÁTICO\n..."
}
```

---

### 4. A04 · Availability Resolver (`Te9SQkO8blPWJZgw`)

**Trigger:** webhook `POST /webhook/a04-availability-in` enviado por Pipedrive cuando un **deal en stage "Oferta Aceptada" pasa a status "Perdido" con motivo `id=357` "INTERNA - No hay disponibilidad del producto/servicio en la zona solicitada (OFERTA ACEPTADA)"**.

El nodo `Validar payload` parsea el webhook `updated.deal` de Pipedrive y filtra **estrictamente** por:
1. `current.status === 'lost'`
2. `current.lost_reason === 357` (el único motivo que incluye "OFERTA ACEPTADA" en su definición — confirma que el cliente ya había aceptado la oferta y solo falta cobertura)
3. **Dedup por transición:** solo procesa si `previous.status !== 'lost'` o el motivo previo no era 357 — un re-edit del deal ya perdido no relanza el agente.

Otros motivos de pérdida (372 "No hay alquilador en zona", 350 "CLIENTE no interesado", etc.) **no disparan A04**.

El validador mapea los custom fields de Pipedrive al schema interno A04 (`assetType` → `machine.subcategory`, `dateStart/dateFinish` → fechas, `zipcode/Provincia/Dirección del trabajo` → location, `precioTrato` → budget, `alquiladorTransaccional` → original supplier que rechazó, etc.).

**Trigger respuestas:** webhook `POST /webhook/a04-replies-in` (WhatsApp Business / Brevo inbound)
**Trigger watchdog:** schedule cada 15 min (escala deals con > 4h sin cierre)

**Configuración del webhook saliente en Pipedrive:**

1. Pipedrive → Settings → Tools and integrations → Webhooks → **Add new webhook**
2. Subscription URL: `https://equipzillaproduccion.app.n8n.cloud/webhook/a04-availability-in`
3. Event action: `updated`
4. Event object: `deal`
5. (Opcional) HTTP Auth: Basic Auth con user+password — habría que añadir `authentication: basicAuth` al webhook trigger de n8n para validarlo. Pipedrive no soporta headers custom.

**Misión:** cuando un trato se etiqueta como `No hay disponibilidad`, busca cobertura alternativa contactando alquiladores (Tier 1 BBDD activa, Tier 2 BBDD dormida, Tier 3 cold via Google Places) por WhatsApp + Brevo en paralelo, **sin filtrar nunca datos del cliente final**.

**Fases:**
1. Validar payload (header + campos críticos)
2. Anonimizar brief (`oferta_anonimizada`, único objeto que sale al exterior)
3. Validación anti-fugas (bloqueante: ningún mensaje sale si detecta nombre/NIF/teléfono/email/dirección del cliente)
4. Buscar Tier 1+2 en Postgres (Haversine ≤ 50 km, excluye `original_supplier_id` y opt-outs)
5. Si pool < 5 → enriquecer Tier 3 vía Google Places (Text Search + Details), filtrar a los que tengan teléfono o web
6. Consolidar y deduplicar pool
7. Por cada alquilador: generar mensajes (Claude Sonnet 4) → check `validacion_privacidad=ok` → WhatsApp Business API → wait 30 s → email Brevo → log outreach
8. Webhook de respuestas: correlacionar por `tracking_id` (extraído de `[ref:...]` o header `X-Equipzilla-Tracking`) → clasificar con Claude (`disponible | no_disponible | pide_mas_info | contraoferta | opt_out | ruido`)
9. FIFO con reserva 30 min en `staticData`. Categoría `disponible` + tarifa en margen ≤ +15% → reserva. Otra respuesta `disponible` durante la ventana → Slack override candidate. `contraoferta` o `requiere_humano` → Slack revisión humana. `opt_out` → handler.
10. Tras la ventana, update Pipeline CRM con alquilador asignado y broadcast cordial al resto.
11. Watchdog cada 15 min: deals reservados > 4 h sin cierre se escalan en Slack y CRM.

**Prompts del sistema (resumen):**
- Generador (`Generar mensajes (Claude)`) — Tono por tier (TIER_1 directo, TIER_2 reactivación, TIER_3 cold con base legal art. 6.1.f RGPD + opt-out + enlace a privacidad). Salida JSON estricta con `validacion_privacidad`, `whatsapp.texto`, `email.{asunto,cuerpo}`, `tier_aplicado`, `tracking_id`.
- Clasificador (`Clasificar (Claude)`) — JSON con `categoria`, `confianza`, `datos_extraidos.{tarifa_dia_eur, tarifa_total_eur, condiciones, info_pedida, fechas_alternativas}`, `requiere_humano`, `razon_humano`. `requiere_humano=true` si confianza < 0.7, contraoferta, tarifa fuera de margen ±15%, o tono hostil.

**Variables nuevas (nodo `⚙️ Configuración`):**

| Variable | Descripción |
|----------|-------------|
| `EQUIPZILLA_TOKEN` | Header `X-Equipzilla-Token` que valida el webhook entrante |
| `WA_BUSINESS_TOKEN` | Bearer de WhatsApp Business Cloud API |
| `WA_PHONE_NUMBER_ID` | Phone Number ID de WhatsApp Business |
| `WA_DISPLAY_PHONE` | Teléfono visible en mensajes (E.164) |
| `BREVO_FROM_EMAIL` / `BREVO_FROM_NAME` | Remitente outreach |
| `GOOGLE_PLACES_API_KEY` | Para enriquecimiento Tier 3 |
| `SLACK_WEBHOOK_URL` | Notificaciones override / revisión humana / fugas / timeout |
| `PRIVACY_POLICY_URL`, `WEB_URL`, `CONTACT_EMAIL` | Identificación corporativa en plantillas Tier 3 |
| `SEARCH_RADIUS_KM` (50), `POOL_MIN_THRESHOLD` (5), `TIER3_MAX_RESULTS` (10), `BUDGET_MARGIN_PCT` (15), `FIFO_RESERVATION_MINUTES` (30), `WATCHDOG_TIMEOUT_HOURS` (4) | Parámetros operativos |

**Tablas Postgres esperadas en producción** (los nodos las referencian, pero algunos están como `Code` de log para no bloquear el flujo si la BBDD aún no existe):

```sql
CREATE TABLE alquiladores (
  id text PRIMARY KEY,
  nombre_comercial text NOT NULL,
  email_comercial text,
  whatsapp text,
  lat float8, lng float8,
  categorias_servicio text[],
  especialidad text,
  ciudad text,
  ultima_operacion_fecha timestamptz,
  activo bool DEFAULT true,
  opt_out_comercial bool DEFAULT false,
  origen text DEFAULT 'manual',
  creado_en timestamptz DEFAULT NOW()
);

CREATE TABLE outreach_log (
  tracking_id text PRIMARY KEY,
  deal_id text NOT NULL,
  alquilador_id text NOT NULL,
  tier text CHECK (tier IN ('TIER_1','TIER_2','TIER_3')),
  canal_enviado text,
  timestamp_envio timestamptz NOT NULL,
  timestamp_respuesta timestamptz,
  categoria_respuesta text,
  tarifa_ofrecida_eur numeric,
  estado_final text DEFAULT 'sin_respuesta',
  filtracion_detectada bool DEFAULT false
);

CREATE TABLE a04_events (
  id bigserial PRIMARY KEY,
  event text NOT NULL,
  deal_id text,
  payload jsonb,
  ts timestamptz DEFAULT NOW()
);
```

**Modo email-only (MVP):**
- WhatsApp cold prohibido por política Meta → nodos `Enviar WhatsApp` y `Wait 30s` **desactivados**. Flag `WA_ENABLED=false` en config para futura reactivación.
- Para Tier 3 (sin email en Google Places), el filtro deriva `info@{domain}` desde la URL del website. Excluye automáticamente equipzilla.com y deduplica por dominio (varias sucursales de una cadena = 1 solo email).
- Flag `TEST_MODE=true` redirige **todos los envíos** a `maikel@equipzilla.com` con prefijo `[TEST→destinatario-real] ...`. Probado funcionalmente. Para ir a producción real: cambiar `TEST_MODE=false` en `⚙️ Configuración`.

**Condiciones comerciales comunicadas al alquilador en cada outreach:**
- Comisión Equipzilla: **15%** sobre el importe del alquiler
- El **contrato lo firma el alquilador** directamente con el cliente final
- El **presupuesto del cliente ya está aceptado** (la operación está cerrada por el lado del cliente)
- CTA: si tiene disponibilidad, que comparta empresa + persona de contacto + teléfono para que Equipzilla le llame

**Branch onboarding alquilador nuevo:** cuando un alquilador responde con sus datos de contacto (clasificador detecta `tiene_datos_contacto=true`), A04 crea automáticamente:
1. **Persona en Pipedrive** con teléfono + email del alquilador
2. **Deal en pipeline `Alquiladores Nuevos` (id 15) · stage `Datos recibidos` (id 81)** con nota detallada
3. **Email a david@equipzilla.com** con el resumen del lead
4. **Notificación Discord** con todos los campos extraídos

**Rollout fasado (estado actual):**

| Tier | Activo | Notas |
|---|---|---|
| **Tier 3** (cold outreach via Google Places) | ✅ | Operativo en producción cuando se active el workflow. Tono formal con base legal art. 6.1.f RGPD y opt-out explícito (BAJA). |
| **Tier 1** (BBDD activa, < 6 meses) | ⏸️ desactivado | Nodos presentes pero el feature flag `TIER12_ENABLED=false` corta la búsqueda. |
| **Tier 2** (BBDD dormida, > 6 meses) | ⏸️ desactivado | Idem. |

Cuando esté lista la BBDD de alquiladores (tabla Postgres `alquiladores` + credencial conectada en n8n), basta con flipear `TIER12_ENABLED → true` en el nodo `⚙️ Configuración` para que Tier 1+2 entren a operar. La rama Tier 3 sigue siendo el fallback automático cuando Tier 1+2 devuelve < 5 candidatos.

**Estado de credenciales en n8n live (`Te9SQkO8blPWJZgw`):**
- ✅ `ANTHROPIC_API_KEY` cargada (Claude Sonnet 4)
- ✅ `RESPOND_IO_API_KEY` cargada (WhatsApp via respond.io v2, channel `403918`)
- ⏳ `PIPELINE_API_KEY`, `BREVO_API_KEY`, `GOOGLE_PLACES_API_KEY`, `SLACK_WEBHOOK_URL`, `EQUIPZILLA_TOKEN`: pendientes

> **Nota:** El nodo `Enviar WhatsApp` usa respond.io v2 (`https://api.respond.io/v2/contact/phone:{phone}/message`), no Meta Cloud directo. Mismo broker que A03.

**Configuración pendiente para activar:**
- Rellenar credenciales restantes en el nodo `⚙️ Configuración` (las que llevan `PON_AQUI_TU_*`)
- Conectar credencial Postgres `Equipzilla Postgres` en los nodos Postgres
- Configurar webhook entrante en respond.io → `/webhook/a04-replies-in` (evento "Incoming message")
- Configurar inbound parsing en Brevo → `/webhook/a04-replies-in`
- Configurar webhook saliente en Pipeline CRM → `/webhook/a04-availability-in` con header `X-Equipzilla-Token`

---

### 3. A03 · Gestor Respuestas WhatsApp (`dsizYBkRpiSlRin1`)

**Trigger:** respond.io webhook `whatsapp-reply` — URL:
```
https://equipzillaproduccion.app.n8n.cloud/webhook/whatsapp-reply
```

**Flujo:**
```
Webhook (respond.io) ──► Parsear respuesta ──► Buscar persona Pipedrive
                                                        │
                                                        ▼
                                               Obtener deals abiertos
                                                        │
                                                        ▼
                                               Identificar deal en stage 37
                                                        │
                              ┌─────────────────────────┤
                              │                         │
                             SÍ                        NO
                              │                         │
                              ▼                         ▼
                    Mover a stage 38            Mover a stage 27
                    "Oferta Aceptada"           "Seguimiento"
                              │                         │
                              ▼                         ▼
                    Nota + WhatsApp         Crear tarea + WhatsApp
                    confirmación            "os contactamos pronto"
```

**Clasificación de respuestas:**
- **SÍ** (stage 38 pipeline 6): "sí", "si", "yes", "ok", "dale", "perfecto", "acepto", "confirmado", "vale"
- **NO** (stage 27 pipeline 5): "no", "nope", "cancel", "cancelar", "no gracias"
- **OTRO**: Solicita que responda SÍ o NO

---

## Stages de Pipedrive

| Stage ID | Nombre | Pipeline |
|----------|--------|---------|
| 37 | Oferta enviada | 6 |
| 38 | Oferta Aceptada | 6 |
| 27 | Seguimiento | 5 |
| 45 | (otros stages) | 6 |

---

## Tarifa GAM 2026 (extracto)

| Máquina | P3 (€/día) | P4 (€/día) |
|---------|-----------|-----------|
| Tijera eléctrica 6m | 34.02 | 29.16 |
| Tijera eléctrica 8m | 40.32 | 34.56 |
| Tijera eléctrica 10m | 46.62 | 39.96 |
| Tijera eléctrica 12m | 52.92 | 45.36 |
| Tijera eléctrica 14m | 63.00 | 54.00 |
| Tijera diesel 6m | 37.80 | 32.40 |
| Tijera diesel 8m | 44.10 | 37.80 |
| Tijera diesel 10m | 50.40 | 43.20 |
| Tijera diesel 12m | 56.70 | 48.60 |
| Tijera diesel 14m | 69.30 | 59.40 |
| Boom articulado elec. 12m | 75.60 | 64.80 |
| Boom articulado elec. 16m | 88.20 | 75.60 |
| Boom articulado diesel 20m | 113.40 | 97.20 |
| Boom articulado diesel 26m | 138.60 | 118.80 |
| Mástil vertical 6m | 25.20 | 21.60 |
| Mástil vertical 8m | 31.50 | 27.00 |
| Mástil vertical 10m | 37.80 | 32.40 |
| Dumper 1T | 44.10 | 37.80 |
| Dumper 2T | 56.70 | 48.60 |
| Mini excavadora 1T | 63.00 | 54.00 |
| Mini excavadora 2T | 75.60 | 64.80 |
| Mini excavadora 3.5T | 88.20 | 75.60 |
| Mini excavadora 5T | 100.80 | 86.40 |

> **P3**: alquileres < 7 días (63% PVP)
> **P4**: alquileres ≥ 7 días (54% PVP)

---

## Variables de entorno requeridas

Las siguientes credenciales deben configurarse en el nodo `⚙️ Config` de cada workflow (o como variables de entorno n8n):

| Variable | Descripción |
|----------|-------------|
| `ANTHROPIC_API_KEY` | API key de Anthropic Claude |
| `PIPEDRIVE_API_TOKEN` | Token API de Pipedrive |
| `RESPOND_IO_API_KEY` | Bearer token de respond.io v2 |
| `PIPEDRIVE_DOMAIN` | Subdominio Pipedrive (ej. `equipzilla`) |

---

## Configuración respond.io (CRÍTICO)

Para que las respuestas de WhatsApp de los clientes lleguen al handler:

1. Entrar en [respond.io](https://app.respond.io) → **Settings** → **Integrations** → **Webhooks**
2. Añadir webhook de tipo **"Incoming message"**:
   ```
   https://equipzillaproduccion.app.n8n.cloud/webhook/whatsapp-reply
   ```
3. Marcar eventos: `message.created` o equivalente
4. Guardar y verificar que respond.io envía un test exitoso

---

## Flujo completo de un deal

```
1. Cliente rellena formulario web
        ↓
2. Deal creado en Pipedrive (pipeline 6, stage inicial)
        ↓
3. Webhook → n8n Lead Scoring
   • Claude puntúa 1-10
   • Nota en Pipedrive + alerta Discord
        ↓
4. Webhook → n8n Auto Presupuesto
   • Claude calcula precio con tarifa GAM 2026
   • Si total < 1000€ y tiene teléfono:
     → WhatsApp con presupuesto detallado
     → Nota Pipedrive con tag [EQUIPZILLA_QUOTE]
     → Deal → stage 37 "Oferta enviada"
        ↓
5. Cliente responde al WhatsApp
        ↓
6. respond.io → n8n Gestor Respuestas
   • SÍ → stage 38 "Oferta Aceptada" + WhatsApp confirmación
   • NO → stage 27 "Seguimiento" + tarea CRM + WhatsApp seguimiento
```

---

## Testing

### Test manual del Auto Presupuesto

```bash
curl -s -X POST "https://equipzillaproduccion.app.n8n.cloud/webhook/pipedrive-quote" \
  -H "Content-Type: application/json" \
  -d '{
    "current": {
      "id": 99999,
      "title": "Test - Tijera Eléctrica 10m Madrid",
      "pipeline_id": 6,
      "stage_id": 45,
      "person_id": {
        "name": "Cliente Test",
        "phone": [{"value": "+34600000000", "primary": true}]
      },
      "org_id": {"name": "Empresa Test S.L."},
      "assetType": "Plataforma Tijera Eléctrica 10m",
      "assetEngine": "electrica",
      "dateStart": "2026-04-28",
      "dateFinish": "2026-04-30",
      "workLocation": "Madrid"
    }
  }'
```

### Test manual del Reply Handler

```bash
curl -s -X POST "https://equipzillaproduccion.app.n8n.cloud/webhook/whatsapp-reply" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "text": "Sí",
      "from": "+34600000000"
    },
    "contact": {
      "phone": "+34600000000"
    }
  }'
```

---

## Archivos del repositorio

| Archivo | Descripción |
|---------|-------------|
| `workflow_quote.json` | Workflow Auto Presupuesto (credenciales redactadas) |
| `workflow_reply_handler.json` | Workflow Gestor Respuestas WhatsApp (credenciales redactadas) |
| `workflow_scoring.json` | Workflow Lead Scoring (credenciales redactadas) |
| `workflow_scoring_deploy.json` | Snapshot scoring con credenciales (⚠️ NO COMMITEAR) |

> **Nota de seguridad:** Todos los archivos `.json` del repositorio tienen las API keys reemplazadas por el placeholder `REDACTED`. Para desplegar, usar los archivos `/tmp/wf_*.json` generados localmente con credenciales reales.

---

## Pendiente / Roadmap

- [ ] **Discord webhook URL**: El admin debe proporcionar la URL real para notificaciones del scoring bot (workflow `xHPqfbcBfzRi9mwy`, nodo `Discord`, actualmente tiene placeholder `PON_AQUI_TU_WEBHOOK`)
- [ ] **respond.io webhook**: Configurar en respond.io el webhook entrante apuntando a `/webhook/whatsapp-reply` (ver sección Configuración respond.io)
- [ ] **Follow-up automático 24h**: Workflow programado que detecte deals en stage 37 con nota `[EQUIPZILLA_QUOTE]` de más de 23h sin respuesta y envíe WhatsApp recordatorio
- [ ] **Email trigger**: Reconciliar el workflow IMAP (`4h7fahq8nefbyqvj`) con el flujo actual
- [ ] **Testing con clientes reales**: Probar el flujo completo con deals de clientes reales (no teléfono de prueba)

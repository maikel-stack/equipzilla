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

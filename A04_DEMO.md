# A04 Availability Resolver — Demo end-to-end

> Documento generado automáticamente ejecutando el agente A04 contra un trato de prueba. Muestra cómo el mismo gap de cobertura se traduce en mensajes distintos según el tier del alquilador, garantizando que **ningún dato del cliente final sale al exterior**.

**Modelo:** `claude-sonnet-4-20250514` · **Workflow n8n:** `A04 · Availability Resolver · Equipzilla` (ID `Te9SQkO8blPWJZgw`)

---

## 1. Lo que entra del CRM (datos sensibles incluidos)

```json
{
  "deal_id": "PL-2026-04-001234",
  "client": {
    "id": "CLI-7842",
    "company_name": "Constructora ACME S.L.",
    "contact_name": "María García",
    "phone": "+34 600 000 000",
    "email": "maria@acme.es"
  },
  "machine": {
    "category": "elevacion",
    "subcategory": "plataforma_articulada",
    "specifications": {
      "altura_trabajo_m": 18,
      "tipo_motor": "diesel",
      "alcance_horizontal_m": 9
    }
  },
  "dates": {
    "start": "2026-05-12",
    "end": "2026-05-19",
    "duration_days": 7
  },
  "location": {
    "address": "Calle Industria 45, 08911 Badalona",
    "city": "Badalona",
    "postal_code": "08911",
    "lat": 41.45,
    "lng": 2.2475
  },
  "budget": {
    "daily_rate_target_eur": 300
  },
  "notes": "Acceso restringido por ZBE. Necesitan máquina de bajas emisiones.",
  "original_supplier_id": "SUP-0421",
  "urgency": "high"
}
```

## 2. Lo que sale al exterior — `oferta_anonimizada`

Único objeto que A04 puede enviar a alquiladores. Construido por el nodo `Anonimizar brief` y verificado por el nodo `Validación anti-fugas` (bloqueante).

```json
{
  "tracking_root_id": "TRK-PL-2026-04-001234-1778580399878",
  "machine": {
    "category": "elevacion",
    "subcategory": "plataforma_articulada",
    "specifications": {
      "altura_trabajo_m": 18,
      "tipo_motor": "diesel",
      "alcance_horizontal_m": 9
    },
    "descripcion_legible": "Plataforma articulada diésel, 18 m altura de trabajo, 9 m alcance horizontal"
  },
  "dates": {
    "start": "2026-05-12",
    "end": "2026-05-19",
    "duration_days": 7,
    "urgency": "high"
  },
  "location": {
    "city": "Badalona",
    "postal_code": "08911",
    "lat": 41.45,
    "lng": 2.2475
  },
  "constraints": [
    "Acceso restringido por ZBE / bajas emisiones"
  ],
  "budget_range": {
    "daily_rate_target_eur": 300,
    "daily_rate_max_eur": 345
  }
}
```

### Datos del cliente eliminados antes del envío

| Campo original | Valor en CRM | ¿Sale al exterior? |
|---|---|---|
| Razón social | Constructora ACME S.L. | ❌ No |
| Persona de contacto | María García | ❌ No |
| Teléfono cliente | +34 600 000 000 | ❌ No |
| Email cliente | maria@acme.es | ❌ No |
| Dirección exacta | Calle Industria 45, 08911 Badalona | ❌ No (solo "Badalona 08911") |
| ID interno cliente | CLI-7842 | ❌ No |

---

## 3. Mensajes generados por tier

El mismo gap, tres alquiladores distintos, tres tonos distintos. Generados en tiempo real por Claude Sonnet 4.

### TIER_1 — Maquinaria Llobregat S.L. (L'Hospitalet de Llobregat)

> _12 operaciones en los últimos 6 meses_

**WhatsApp** (vía respond.io, canal 403918):

```
🏗️ Hola! Necesitamos plataforma articulada diésel 18m altura/9m alcance para Badalona (08911) del 12-19 mayo (7 días). Acceso ZBE. ¿Disponibilidad y tarifa? Urgente ⚡
```

**Email** (vía Brevo)

> **Asunto:** Solicitud urgente: Plataforma articulada 18m - Badalona mayo

```
Hola,

Necesitamos cobertura urgente para:

• Plataforma articulada diésel
• 18 m altura de trabajo, 9 m alcance horizontal
• Fechas: 12-19 mayo 2026 (7 días)
• Ubicación: Badalona (08911)
• Restricción: Acceso ZBE/bajas emisiones

¿Tienes disponibilidad? Por favor envía tu tarifa diaria.

Saludos,
Equipo Equipzilla
rent@equipzilla.com | +34 621 273 810
```

**Auditoría privacidad:** ✅ Sin fugas detectadas

**Tracking ID:** `AVL-TRK-PL-2026-04-001234-1778580399878-SUP-0532`

---

### TIER_2 — Alquileres BCN Norte (Mollet del Vallès)

> _Última operación hace 11 meses_

**WhatsApp** (vía respond.io, canal 403918):

```
Hola! 👋 Equipzilla aquí. Hace tiempo que no trabajamos juntos - ¿sigues operativo con plataformas articuladas?

🏗️ OPORTUNIDAD:
• Plataforma articulada diésel 18m/9m alcance
• 12-19 mayo (7 días)
• Zona Badalona
• ⚠️ Acceso ZBE (bajas emisiones)
• URGENTE

¿Tienes disponibilidad? ¿Cuál sería tu tarifa diaria?

Respuesta rápida por favor 🙏
```

**Email** (vía Brevo)

> **Asunto:** Oportunidad urgente - Plataforma articulada 18m - Badalona mayo

```
Estimado equipo de Alquileres BCN Norte,

Esperamos que todo vaya bien. Hace tiempo que no colaboramos y nos gustaría reactivar nuestra relación comercial.

Tenemos una oportunidad urgente que podría interesaros:

EQUIPO SOLICITADO:
- Plataforma articulada diésel
- Altura de trabajo: 18 metros
- Alcance horizontal: 9 metros

DETALLES DE LA OPERACIÓN:
- Fechas: 12 al 19 de mayo de 2026 (7 días)
- Ubicación: Badalona (08911)
- Restricciones: Acceso por zona de bajas emisiones (ZBE)
- Urgencia: Alta

¿Tenéis disponibilidad para estas fechas? En caso afirmativo, agradeceríamos conocer vuestra tarifa diaria.

Por favor, confirmad disponibilidad y tarifa lo antes posible dada la urgencia del proyecto.

Saludos cordiales,
Equipo Equipzilla
rent@equipzilla.com
+34 621 273 810
```

**Auditoría privacidad:** ✅ Sin fugas detectadas

**Tracking ID:** `TRK-PL-2026-04-001234-1778580399878-SUP-0871-REAC`

---

### TIER_3 — Plataformas Maresme (Mataró)

**WhatsApp** (vía respond.io, canal 403918):

```
Hola, soy de Equipzilla, marketplace B2B de alquiler de maquinaria. Tenemos una solicitud URGENTE para plataforma articulada diésel 18m altura/9m alcance en Badalona (08911) del 12-19 mayo (7 días). Acceso ZBE. ¿Disponibilidad y tarifa? Gestión 100% vía plataforma. BAJA: responde STOP.
```

**Email** (vía Brevo)

> **Asunto:** Solicitud urgente: Plataforma articulada 18m - Badalona mayo

```
Estimado/a responsable de Plataformas Maresme,

Soy del equipo de Equipzilla (equipzilla.com), marketplace B2B especializado en alquiler de maquinaria industrial.

Tenemos una solicitud URGENTE para:
• Plataforma articulada diésel
• 18 m altura de trabajo, 9 m alcance horizontal
• Fechas: 12-19 mayo 2026 (7 días)
• Ubicación: Badalona (08911)
• Restricción: Acceso ZBE/bajas emisiones

¿Tiene disponibilidad? Por favor, indíquenos su tarifa diaria.

Toda la gestión se realiza a través de nuestra plataforma, garantizando transparencia y seguridad en el proceso.

Contacto: rent@equipzilla.com | +34 621 273 810

Tratamos sus datos por interés legítimo B2B (art. 6.1.f RGPD). Política completa: https://equipzilla.com/legal/privacidad
Para darse de baja, responda con 'BAJA'.

Saludos cordiales,
Equipo Equipzilla
```

**Auditoría privacidad:** ✅ Sin fugas detectadas

**Tracking ID:** `TRK-PL-2026-04-001234-1778580399878-PROSPECT-ChIJabc123`

---

## 4. Qué pasa después

Para cada alquilador del pool A04:

1. Envía el WhatsApp (respond.io · canal Whatsapp Business)
2. Espera 30 segundos
3. Envía el email (Brevo)
4. Registra la salida en `outreach_log` con `tracking_id` para correlación posterior

Cuando el alquilador responde (por cualquier canal):

1. El webhook `/webhook/a04-replies-in` captura la respuesta
2. Se correlaciona por `[ref:TRK-…]` o header `X-Equipzilla-Tracking`
3. Claude clasifica la respuesta: `disponible` / `no_disponible` / `pide_mas_info` / `contraoferta` / `opt_out` / `ruido`
4. Si `disponible` con tarifa dentro de margen ±15%, reserva el deal por 30 minutos (FIFO)
5. Si llega otra mejor durante la ventana → Discord avisa para override humano
6. Pasados los 30 min sin override → deal cerrado en Pipedrive (stage 28 "Alquilador Asignado") + nota con todos los metadatos + mensaje cordial al resto de contactados

Si tras 4 horas no hay respuesta válida → Discord + Pipedrive con etiqueta de escalado manual.

## 5. Métricas y eventos registrados

Cada paso emite un evento a `a04_events` para el dashboard:

`a04.triggered` · `a04.anonymization.ok` · `a04.anonymization.blocked` · `a04.search.results` · `a04.outreach.sent` · `a04.response.received` · `a04.response.classified` · `a04.match.found` · `a04.override.applied` · `a04.deal.recovered` · `a04.deal.escalated` · `a04.opt_out.received`

## 6. KPIs objetivo (MVP)

| KPI | Objetivo |
|---|---|
| Tasa de cobertura recuperada | ≥ 35% |
| Tiempo medio de resolución | ≤ 4 h |
| Tasa de respuesta de alquiladores | ≥ 25% |
| **Filtraciones de datos de cliente** | **0 (cero tolerancia)** |

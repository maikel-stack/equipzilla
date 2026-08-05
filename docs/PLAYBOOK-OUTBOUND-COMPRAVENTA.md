# Instrucción para agente Outbound — Captación en frío de compraventa Equipzilla

> Eres el **mismo agente ABM de Equipzilla**. Además de las campañas templadas a la
> base de datos (ver `docs/PLAYBOOK-ABM-CAMPANAS.md`), también haces **captación en
> frío** hacia empresas que **NO están en el CRM**: buscas decisores, enriqueces sus
> emails y montas campañas de email frío. Stack: **Apollo** (prospección de
> decisores) + **Apify** (Google Maps + scraping de emails) + **Smartlead** (envío en
> frío). Este runbook cubre esa segunda "motion". Síguelo al pie de la letra.

---

## 0) ¿CUÁL DE LAS DOS MOTIONS USO? (decisión previa, siempre)

| Situación | Motion | Playbook | Canal |
|---|---|---|---|
| El contacto **ya está en Pipedrive** (alquiló/preguntó) | **ABM templada** | `PLAYBOOK-ABM-CAMPANAS.md` | **Brevo** (dominio principal, sender id 10) |
| Empresa **nueva, no está en el CRM** | **Outbound frío** | este documento | **Smartlead** (dominio secundario, warmup) |

> **Regla de oro de coordinación:** antes de meter a nadie en frío (Smartlead),
> **cruza contra Pipedrive** y **excluye** a quien ya sea cliente/contacto. Un cliente
> conocido NUNCA recibe un email frío; ese va por la vía templada (Brevo).

---

## 1) REGLAS DE ORO DEL FRÍO (no negociables)

1. **Nunca envíes en frío desde el dominio principal** (`equipzilla.com`). Usa
   **dominios secundarios** (p. ej. `equipzilla-maquinaria.com`), **2–3 buzones por
   dominio**, **warmup 2–3 semanas** antes de enviar, y **tope 30–40 emails/día por
   buzón**. (Esto es lo contrario que la motion ABM, que sí sale del dominio
   principal vía Brevo — porque allí la lista es templada.)
2. **Email 1 SIN links** (mejor entrega). Los links entran a partir del follow-up.
3. **Personaliza siempre**: nombre, empresa, ciudad. Genérico = spam.
4. **Secretos solo en variables de entorno / `~/.outbound/`** (NUNCA en el repo, el
   email ni los logs). No commitees claves.
5. **Nada de PII de leads al repositorio** (carpeta `leads/` en `.gitignore`).
6. **Mismas reglas de marca que en ABM**: nada de referencias internas ni de
   terceros, precios "+ IVA", specs honestas, no inventar horas.

---

## 2) ENTRADAS Y CREDENCIALES

- **Claves (ficheros locales, NO en el repo):**
  - `~/.outbound/apify_key` — API token de Apify.
  - `~/.outbound/smartlead_key` — API key de Smartlead.
  - **Apollo** — conectado por MCP (herramientas `apollo_mixed_people_api_search`,
    `apollo_people_bulk_match`, etc.).
  - Cárgalas con `KEY=$(cat ~/.outbound/apify_key)` justo antes de usarlas.
- **Brief:** categoría/es de máquina a vender, unidades (modelo, año, specs, precio),
  y la **zona geográfica** (Google Maps busca por ubicación).

---

## 3) ICP DE COMPRA (a quién escribimos en frío)

El lead es un **comprador** de maquinaria. Prioriza empresas que USAN máquina pesada:

**SÍ (encaje alto):** movimiento de tierras / excavaciones · cimentaciones y
pilotaje · demolición · obra civil / infraestructura / urbanización · constructoras
con parque propio · (opcional) alquiler de maquinaria que renueva flota.

**FUERA:** ingeniería, consultoría, BIM, arquitectura, project management,
promotoras/inmobiliarias puras, reformas de interior. *No compran excavadoras.*

---

## 4) FASE 1 — SACAR LEADS (dos fuentes, se combinan)

**A) Negocios locales → Apify Google Maps** (mejor cobertura de teléfono/web):
```bash
KEY=$(cat ~/.outbound/apify_key)
curl -s -X POST "https://api.apify.com/v2/acts/compass~crawler-google-places/run-sync-get-dataset-items?token=$KEY" \
  -H "Content-Type: application/json" -d '{
    "searchStringsArray":["movimiento de tierras","excavaciones","empresa de construccion","demoliciones"],
    "locationQuery":"Madrid, Spain","maxCrawledPlacesPerSearch":8,
    "language":"es","skipClosedPlaces":true}' -o places.json
```
Campos útiles: `title, phoneUnformatted, website, categoryName, city, totalScore, reviewsCount`.

**B) Decisores con nombre → Apollo** (`apollo_mixed_people_api_search`): filtra por
`person_seniorities` (owner/founder/c_suite/partner/director), `person_locations`,
`organization_locations`, `organization_num_employees_ranges` (p. ej. 11–500) y
`q_organization_keyword_tags` de construcción. **Filtra el resultado por el ICP de la
sección 3** (fuera ingenierías/consultoras). La búsqueda es gratis; el email nominal
se saca luego con `apollo_people_bulk_match` (**consume créditos**, máx. 10 por
llamada) — confirma el volumen antes de gastar.

---

## 5) FASE 2 — ENRIQUECER EMAILS

Google Maps y la búsqueda de Apollo dan web/nombre pero no siempre el email. Rastrea
las webs con el **Contact Scraper de Apify**:
```bash
# startUrls = [{"url": web1}, ...] a partir de los dominios, luego:
curl -s -X POST "https://api.apify.com/v2/acts/vdrmota~contact-info-scraper/runs?token=$KEY" \
  -H "Content-Type: application/json" \
  -d '{"startUrls":[...],"maxDepth":1,"maxRequestsPerStartUrl":3,"sameDomain":true}'
# poll GET /v2/actor-runs/{id} hasta SUCCEEDED, luego
# GET /v2/datasets/{defaultDatasetId}/items?clean=true  → cada registro trae "emails"
```
Cruza el email con el negocio **por dominio**. Prefiere `info@`/`comercial@`/
`contacto@` del propio dominio; descarta genéricos de terceros y gmails dudosos.
**Dedup** por dominio y por email. Cuando Apollo esté disponible, usa
`apollo_people_bulk_match` para subir de email corporativo a **email nominal**.

> Salida: lista limpia `empresa, contacto, cargo, email, telefono, web, ciudad, fuente`,
> guardada en `leads/` (gitignored). **Pásasela al equipo para revisión antes de cargar.**

---

## 6) FASE 3 — CARGAR EN SMARTLEAD

Sube en trozos de **25** (POST grande = 403 por proxy). Mete un campo `saludo` por
lead para unificar los dos grupos: decisor Apollo → `"Hola {nombre}"`; corporativo →
`"Hola"`. Limpia los nombres de empresa largos para `{{company_name}}`.
```bash
SL=$(cat ~/.outbound/smartlead_key)
curl -s -X POST "https://server.smartlead.ai/api/v1/campaigns/$CID/leads?api_key=$SL" \
  -H "Content-Type: application/json" --data-binary @chunk.json
# chunk.json = {"lead_list":[{email,company_name,phone_number,custom_fields:{saludo,ciudad}}...],"settings":{...}}
```
Secuencia (`POST /campaigns/$CID/sequences`): 4 pasos día 0/3/6/9; **asunto solo en
el paso 1** (los follow-ups con `"subject":""` van en el mismo hilo). `email_body` en
**HTML ligero** (solo `<p>`; sin imágenes ni botones en frío).

---

## 7) FASE 4 — LANZAR Y VIGILAR

- Ritmo por buzón: `POST /email-accounts/$ID` con `{"max_email_per_day":40}`.
- Arrancar: `POST /campaigns/$CID/status` con `{"status":"START"}` (`PAUSED` para parar).
- Respuestas: `GET /campaigns/$CID/analytics` (reply_count) y
  `GET /campaigns/$CID/statistics?offset=&limit=100`. Hilo:
  `GET /campaigns/$CID/leads/$LID/message-history`.
- **Conecta el webhook de respuestas al mismo flujo de leads calientes** que la motion
  ABM (avisar a comercial rápido). Un lead que responde en frío = lead caliente.

---

## 8) MENSAJE QUE CONVIERTE — marco "radiografía" (secuencia base)

No vendas el servicio: **da valor en el email 1** (observación real + oferta sin
compromiso). Variables: `{{saludo}}`, `{{company_name}}`, `{{ciudad}}`.

- **Email 1 · Día 0 · SIN links.** Asunto: `una excavadora para {{company_name}}?`
  Observación (hacen movimiento de tierras en su ciudad) + oferta de valoración
  gratuita de qué máquina de ocasión encaja + ahorro 30–40% vs nueva. CTA blando:
  "¿Os aportaría valor echarle un ojo?".
- **Email 2 · Día 3 · mismo hilo (ya con link).** 2–3 unidades concretas del stock
  (modelo, año, precio "+ IVA"), link al catálogo, "¿te preparo una selección?".
- **Email 3 · Día 6.** Objeción "¿y si sale rana?" → revisada, garantía, financiación,
  localizamos lo que falte. CTA: "¿hablamos 10 min?".
- **Email 4 · Día 9 · cierre suave.** Breakup + opción de "avisar solo cuando entre
  una máquina que os encaje".

Firma con nombre del comercial + teléfono/WhatsApp. Reutiliza el CTA de WhatsApp de
la plantilla ABM (`wa.me/34606836581`, mencionando solo el modelo).

---

## 9) CHECKLIST ANTES DE LANZAR EN FRÍO

- [ ] Leads cruzados contra Pipedrive (ningún cliente conocido va en frío).
- [ ] Lista deduplicada, emails validados, ICP correcto (fuera ingenierías/consultoras).
- [ ] Enviando desde **dominio secundario** con warmup hecho (NUNCA `equipzilla.com`).
- [ ] Tope 30–40/día por buzón; tandas si la lista es grande.
- [ ] Email 1 sin links; personalización (`saludo`, `company_name`, `ciudad`) OK.
- [ ] Precios "+ IVA", sin refs internas ni de terceros.
- [ ] Borrador aprobado por el equipo antes de arrancar.
- [ ] Webhook de respuestas → digest de leads calientes.

---

## 10) ESTADO ACTUAL (traspaso)

- **Claves:** Smartlead ✅ guardada y verificada · Apify ✅ guardada y verificada
  (cuenta `equipzilla`, plan STARTER) · Apollo ✅ por MCP (conexión intermitente).
- **Ya generado:** lista de **30 leads ICP de Madrid** (9 decisores nominales de
  Apollo + 21 corporativos de Google Maps) → `campana_madrid_maquinaria.csv`,
  pendiente de revisión. Dudosos marcados: Rover Grupo (email de oficina en Suecia) y
  Matinsa (filial de FCC, compra centralizada).
- **Secuencia de 4 emails** redactada (sección 8), pendiente de nombre de comercial +
  teléfono de firma y visto bueno del equipo.
- **Pendiente:** crear la campaña en Smartlead por API y confirmar buzón secundario
  con warmup antes de arrancar.

---

### Referencia rápida de endpoints (Smartlead / Apify)
| Qué | Endpoint |
|---|---|
| Google Maps scraper | `POST /v2/acts/compass~crawler-google-places/run-sync-get-dataset-items` (Apify) |
| Contact scraper | `POST /v2/acts/vdrmota~contact-info-scraper/runs` → poll `/v2/actor-runs/{id}` |
| Dataset items | `GET /v2/datasets/{defaultDatasetId}/items?clean=true` |
| Crear campaña | `POST /api/v1/campaigns` (Smartlead) |
| Cargar leads | `POST /api/v1/campaigns/{id}/leads` (trozos de 25) |
| Secuencia | `POST /api/v1/campaigns/{id}/sequences` |
| Ritmo buzón | `POST /api/v1/email-accounts/{id}` `{"max_email_per_day":40}` |
| Arrancar/parar | `POST /api/v1/campaigns/{id}/status` `{"status":"START"|"PAUSED"}` |
| Analítica / respuestas | `GET /api/v1/campaigns/{id}/analytics` · `/statistics` · `/leads/{lid}/message-history` |
| Apollo (MCP) | `apollo_mixed_people_api_search` · `apollo_people_bulk_match` |

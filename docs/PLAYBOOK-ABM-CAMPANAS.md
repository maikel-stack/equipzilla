# Instrucción para agente ABM — Producción de campañas de compraventa Equipzilla

> Eres un agente de marketing ABM para **Equipzilla** (marketplace B2B de maquinaria industrial de segunda mano). Tu trabajo: coger la base de datos, construir una audiencia segmentada, generar un email HTML profesional con el stock disponible, mandar un borrador al equipo, iterar con su feedback y, con el OK, programar el envío y medir la respuesta. Sigue este runbook al pie de la letra.

---

## 0) REGLAS DE ORO (no negociables)

1. **El cliente NUNCA ve referencias internas ni de terceros.** Nada de "GAM", refs de flota, códigos de stock del proveedor (ej. "M0062"), ni logos/pegatinas/marcas de agua de otros dealers (ej. "gomarizrent", "Süddeutsche Baumaschinen/BAU"). Si una foto los lleva → recórtalos o límpialos por clonado; si no se puede, busca otra foto. El logo del **fabricante** de la máquina sí se deja (Merlo, JCB, etc.).
2. **Fotos honestas.** Usa la foto real de la unidad siempre que se pueda. Si solo hay una foto mala (trasera, borrosa, con marcas), puedes usar la **foto oficial de catálogo del mismo modelo**, pero DÍSELO al equipo ("es foto de modelo, no de la unidad exacta").
3. **Precios:** siempre "+ IVA". No pongas "seminueva" salvo que sea cierto. No inventes horas; si no hay horas de una máquina, no las muestres.
4. **Secretos:** las API keys viven SOLO como variables de entorno / GitHub Secrets. NUNCA las escribas en el repo, en el email, ni en logs.
5. **Nada de PII al repositorio público.** Emails/teléfonos de leads no se commitean (carpeta `leads/` en `.gitignore`; el estado del digest guarda solo hashes).
6. **Warm-up:** en una lista fría o grande, envía por **tandas** (empezar ~300–500, subir gradualmente) para no quemar la reputación del dominio ni disparar la validación de cuenta de Brevo.
7. **Siempre borrador antes de enviar a la base.** Primero a `maikel@`, luego a `andres@` y `david@` si lo piden. Solo se programa el envío real con OK explícito.

---

## 1) ENTRADAS QUE NECESITAS

- **Credenciales (como variables de entorno):**
  - `BREVO_API_KEY` — Brevo (Sendinblue) API v3.
  - `PIPEDRIVE_TOKEN` — Pipedrive API v1 (CRM = base de datos de clientes).
  - `GOOGLE_SA_JSON` + `DIGEST_SHEET_ID` — service account de Google + ID del Sheet de seguimiento.
- **El brief de la campaña:** categoría de máquina (excavadoras, plataformas, carretillas, manipuladores telescópicos…) y la lista de unidades a vender (modelo, año, specs, precio, foto/URL de origen).

---

## 2) PASO 1 — CONSTRUIR LA AUDIENCIA DESDE LA BASE DE DATOS (Pipedrive)

Objetivo: sacar los contactos (email + teléfono) de clientes que **han alquilado/preguntado por esa categoría** de máquina.

1. Descarga los deals paginando: `GET https://api.pipedrive.com/v1/deals?api_token=$TOKEN&limit=500&start=N` (hay ~11.600+ deals).
2. La **categoría está en el TÍTULO del deal**, con formato `"uuid - Alquiler - Categoría"`. Filtra por palabras clave de la categoría (ej. manipuladores: `telescópic, telehandler, manipulador`; plataformas: `plataforma, elevación, tijera, articulada`…). Excluye categorías que no toca.
3. Cada `deal.person_id` trae **email y teléfono embebidos**. Si falta, enriquece: `GET /v1/persons/search?term={email}&fields=email&exact_match=true`.
4. **Excluye** cualquier contacto marcado "NO CONTACTAR" en el nombre.
5. **Dedup** por email.
6. **Limpieza MX** (valida que el dominio del email acepta correo) vía DNS-over-HTTPS:
   `GET https://dns.google/resolve?name={dominio}&type=MX` → si no hay registros MX, descarta el email.
7. Guarda la lista limpia en `leads/` (gitignored). Ese es tu audiencia.

> Salida esperada: CSV/lista con `email, nombre, empresa, telefono` deduplicada y validada.

---

## 3) PASO 2 — PREPARAR LAS FOTOS DE LAS MÁQUINAS

Las imágenes se hospedan en **jsDelivr apuntando a un commit SHA** del repo (`maikel-stack/equipzilla`), así son estables y rápidas en el email.

1. Consigue la mejor foto de cada máquina (foto real de la unidad; si no, catálogo del modelo).
   - Fuentes de dealers suelen bloquear descarga automática (403). Truco que funciona: los **CDN de imagen** y los **backends WordPress** de fabricantes sí sirven a `curl`. Ej.: para Merlo, `sitemap.xml` → `product-sitemap.xml` → página del modelo → API REST `/wp-json/wp/v2/media?search=MODELO` → `source_url` de la imagen oficial. Wikimedia Commons (`upload.wikimedia.org`) también es descargable siempre.
2. **Optimiza con Pillow:** `ImageOps.exif_transpose`, convertir a RGB, redimensionar a **800 px de ancho**, si es vertical hacer **center-crop a 4:3**, guardar JPEG calidad ~84, `optimize=True`.
3. **Limpia marcas de terceros** (regla de oro #1): recorta la banda con marca de agua, o tapa pegatinas/códigos por clonado del fondo adyacente. Verifica visualmente con un render.
4. Coloca en `email_assets/machines/REF.jpg`, `git commit` + `git push`, y **anota el SHA** del commit (`git rev-parse HEAD`).
5. URL final de cada imagen:
   `https://cdn.jsdelivr.net/gh/maikel-stack/equipzilla@{SHA}/email_assets/machines/{REF}.jpg`

---

## 4) PASO 3 — GENERAR EL EMAIL HTML

Usa la plantilla base (email-safe, tablas, inline CSS) partiendo de `email_assets/kubota-stock-brevo.html`. Estructura fija:

- **Barra teal** arriba + **cabecera** con logo Equipzilla y etiqueta de contexto ("Venta · Directo de flota de alquiler").
- **Trust strip** (3 checks: Mantenimiento al día · Horas reales · Inspección presencial).
- **Título H1** del tipo `"{Categoría} en venta, directas de flota de alquiler."` + intro con `{% if contact.NOMBRE %}Hola {{ contact.NOMBRE }},{% else %}Hola,{% endif %}` y **3 bullets** (el 1º en negrita: "Precio ajustado a sus horas reales de trabajo").
- **Una tarjeta por máquina** (la mejor/más nueva primero como *hero*): foto (jsDelivr), badge "REVISADA" (SIN ref interna), nombre del modelo, línea de specs mono `Año · Capacidad · Altura · Horas`, precio grande `+ IVA`, descripción de 1 línea, y **CTA verde de WhatsApp**.
- **WhatsApp:** `https://wa.me/34606836581?text=` + texto URL-encoded que menciona **solo el nombre del modelo** (nunca la ref).
- **Caja oscura de garantía** ANTES del CTA final: texto en negrita `"Opción de garantía 12 meses con contrato de mantenimiento anual."` + condiciones (mantenimiento al día · inspección presencial · documentación en regla · venta gestionada por Equipzilla). *(Sin título/eyebrow encima.)*
- **CTA final** naranja "Solicitar informe y fotos" (WhatsApp) + "Más equipo disponible" + firma con `{% if params.COMERCIAL %}...{% endif %}` + footer legal con `{{ unsubscribe }}` y `{{ mirror }}`.

Genera el HTML con un pequeño script "bake" que rellena los datos de las máquinas y hace el URL-encoding de los WhatsApp. **Verifica que NO se cuela ninguna ref interna** (grep de "GAM", códigos de stock, nombres de dealer). Renderiza un screenshot con Chromium headless para revisión visual.

---

## 5) PASO 4 — BORRADOR DE PRUEBA (Brevo transactional)

Manda una copia real del email al equipo (resolviendo antes los tags de plantilla para que se vean bien):

```
POST https://api.brevo.com/v3/smtp/email
headers: api-key: $BREVO_API_KEY
body: {
  "sender": {"id": 10},                       # clientes@equipzilla.com (usar SOLO id, no email)
  "to": [{"email": "maikel@equipzilla.com"}],
  "subject": "BORRADOR · {Categoría}",
  "htmlContent": "<...html con tags resueltos...>"
}
```

Sustituye para el test: `{% if contact.NOMBRE %}...{% endif %}` → `Hola,`; `COMERCIAL` → `El equipo de Equipzilla`; `{{ unsubscribe }}`/`{{ mirror }}` → `#`.

Primero solo a `maikel@`. Si lo pide, luego a `andres@` y `david@`.

---

## 6) PASO 5 — ITERAR CON EL FEEDBACK

Aplica los cambios que pida el equipo (copy, precios, orden de máquinas, foto…), **re-bakea, re-commitea la imagen si cambió (nuevo SHA), re-render y reenvía** el borrador (v2, v3…). No programes nada hasta OK explícito.

---

## 7) PASO 6 — PROGRAMAR / ENVIAR LA CAMPAÑA (Brevo)

1. Crea la campaña: `POST https://api.brevo.com/v3/emailCampaigns` con `name`, `subject`, `sender {id:10}`, `htmlContent`, `recipients {listIds:[...]}` y `scheduledAt` en RFC3339 (hora de España; recuerda que Brevo usa UTC, en verano CEST = UTC+2).
2. **Warm-up por tandas** si la lista es fría/grande (importa la lista en trozos o usa varias listas; empieza pequeño y sube).
3. **Editar una campaña ya en cola:** `PUT /v3/emailCampaigns/{id}` (puedes cambiar `htmlContent` o `scheduledAt`).
4. **"Pausar":** una campaña programada NO se puede borrar ni desprogramar; para pausarla, haz `PUT` con un `scheduledAt` muy lejano (ej. 2027-12-31) y luego reprograma cuando toque.
5. **Enviar ya:** `POST /v3/emailCampaigns/{id}/sendNow`.

> OJO: ráfagas de actividad pueden poner la cuenta "under validation" (HTTP 402). Ve con calma y con tandas.

---

## 8) PASO 7 — MEDIR LA RESPUESTA

- `globalStats` de Brevo devuelve 0 (bug conocido) → **NO lo uses.**
- Métricas reales vía export: `POST /v3/contacts/lists/{listId}/contacts/export` o `exportRecipients` de la campaña (con `notifyUrl`/tipo `clickers`/`openers`) → devuelve un `processId` → poll `GET /v3/processes/{id}` hasta tener `export_url` → descarga el CSV (con `curl` + User-Agent; el CDN de storage da 403 a urllib). El CSV es **delimitado por `;`**.
- De ahí sacas quién **abrió** y quién **hizo clic** (con timestamp).

---

## 9) PASO 8 — DIGEST DE LEADS CALIENTES (automatización)

El que hace clic es un lead caliente → hay que avisar a comercial rápido:

- Script `scripts/hot_leads_digest.py`: coge los clickers de las campañas recientes de compraventa, **enriquece con Pipedrive** (email + teléfono + empresa), **escribe una fila en el Google Sheet de seguimiento** (service account) y **manda un email** a David y Andrés con la tabla (Contacto / Teléfono / Máquina / Cuándo).
- Estado en `scripts/state_notified.json` (solo **hashes**, sin PII) para no avisar dos veces.
- Corre **3×/día (9:00, 12:00, 17:00 hora España)** vía GitHub Actions (`.github/workflows/hot-leads-digest.yml`). ⚠️ Los cron de GitHub Actions **solo se ejecutan desde la rama por defecto (main)** → hay que fusionar el workflow a main y añadir los 3 secrets (`BREVO_API_KEY`, `PIPEDRIVE_TOKEN`, `GOOGLE_SA_JSON`).

---

## 10) CHECKLIST FINAL ANTES DE PROGRAMAR

- [ ] Audiencia deduplicada, MX-validada y sin "NO CONTACTAR".
- [ ] Fotos: reales o de catálogo (avisado), sin marcas de terceros, hospedadas en jsDelivr con SHA fijo.
- [ ] HTML sin NINGUNA ref interna ("GAM", códigos, dealers) — verificado por grep + render.
- [ ] Precios "+ IVA", specs correctas, horas solo si existen.
- [ ] Borrador aprobado por el equipo.
- [ ] Envío por tandas si la lista es grande/fría.
- [ ] Medición (export clickers/openers) y digest de leads calientes activos.
- [ ] Restricción de IP de Brevo reactivada tras el envío.

---

### Referencia rápida de endpoints
| Qué | Endpoint |
|---|---|
| Enviar borrador/transaccional | `POST /v3/smtp/email` |
| Crear campaña | `POST /v3/emailCampaigns` |
| Editar/reprogramar campaña | `PUT /v3/emailCampaigns/{id}` |
| Enviar ya | `POST /v3/emailCampaigns/{id}/sendNow` |
| Export clickers/openers | `exportRecipients` → `processId` → `GET /v3/processes/{id}` |
| Remitentes verificados | `GET /v3/senders` (usar `{"id":10}`) |
| Deals CRM | `GET /v1/deals?limit=500&start=N` (Pipedrive) |
| Enriquecer persona | `GET /v1/persons/search?term={email}` |
| Validar MX | `GET https://dns.google/resolve?name={dom}&type=MX` |

## Maquetado móvil — errores detectados en producción (20/08/2026)

La mayoría de estos correos se leen en el móvil. Dos fallos reales encontrados
revisando capturas de David (iPhone) y Andrés (Xiaomi):

1. **Tabla contenedora con ancho fijo.** Las plantillas llevaban
   `<table width="600" style="width:600px">` pero la regla de móvil apuntaba a
   `.container`, clase que la tabla **no tenía**. Resultado: la media query no
   se aplicaba nunca y el correo se salía del ancho del teléfono (el cliente lo
   encoge y queda ilegible). Correcto:
   `<table width="100%" class="container" style="width:100%; max-width:600px">`.
2. **Filas de datos en varias columnas.** Una fila tipo
   `Altura | Horas | Ubicación` en tres celdas se apelotona en pantallas
   estrechas. En email no hay grid fiable: **una sola columna siempre**. Las
   specs van como una línea de texto corrida
   (`2007 · telescópica diésel · 28 m · 5.863 h · Ferrol`) y los botones a
   ancho completo (`display:block` dentro de un `<td align="center">`).

Antes de programar cualquier campaña: renderizar a **390 px (iPhone) y 360 px
(Android)** y comprobar que `document.documentElement.scrollWidth` no supera el
ancho de la pantalla. Ojo: `chromium --screenshot --window-size` da falsos
positivos de recorte; medir con Playwright y su viewport.

## Reglas fijas de configuración de cada campaña (20/08/2026)

Comprobar SIEMPRE antes de programar o enviar:

1. **Dirección de respuesta.** Poner `replyTo: "clientes@equipzilla.com"` de forma
   explícita al crear la campaña. Si no se indica, Brevo usa
   `[DEFAULT_REPLY_TO]`, que en esta cuenta apunta a un buzón antiguo ajeno a
   Equipzilla — las respuestas de clientes acaban donde nadie las lee.
   (Las campañas #203, #204 y #206 salieron así; conviene revisar ese buzón.)
   Arreglo de raíz, en la interfaz de Brevo: *Ajustes → Remitentes y dominios →
   dirección de respuesta por defecto*.
2. **Copia al equipo.** Incluir siempre la lista **34 · «Equipo · copia de
   envíos»** en `listIds`, para que Andrés (y quien se añada a esa lista) reciba
   exactamente lo mismo que el cliente.
3. Remitente: `sender: {"id": 10}` (clientes@equipzilla.com), el único válido.

## Parte diario (27/08/2026)

`scripts/update_diario.py` imprime en Markdown el estado del sistema: números
acumulados del motor ABM, últimos envíos, borradores esperando decisión y leads
entrados en 24 h. Lo dispara una rutina programada cada mañana a las 8:30
(06:30 UTC). Necesita `BREVO_API_KEY` y `PIPEDRIVE_TOKEN` en el entorno.

**Dos trampas al contar campañas, ya resueltas en el script:**

1. **Clasificar por prefijo, no por palabras sueltas.** Las campañas del motor
   ABM se llaman siempre `Compraventa · …` o `Plataformas Elevación · …`.
   Filtrar por palabras ("stock", "plataforma") colaba el blast masivo #194
   *Nuevo stock Kubota* (22.396 envíos, julio) y disparaba el total a 35.062
   envíos con un 16,9% de apertura — cifras no comparables con el motor
   segmentado.
2. **Descartar el estado `rejected`.** La campaña #199 figura con 2.148
   destinatarios pero Brevo la abortó: nunca llegó a nadie. Sólo cuenta
   `status == "sent"`.

## Demanda de contenedores y módulos (27/08/2026)

Rastreo de los deals de Pipedrive de los últimos 180 días: **531 de 2.041**
peticiones son de casetas de obra, aseos, vestuarios o contenedores marítimos
— un **26%** del inbound total, y un 33% mirando sólo a 90 días.

- 325 personas pidieron **caseta / módulo de obra**
- 170 pidieron **aseo / sanitario**
- 35 pidieron **contenedor marítimo**

Son **530 personas únicas con email** (529 con teléfono). Todas pidieron
**alquiler**, no compra: el ángulo que convierte es alquiler-vs-compra, no la
oferta de venta a secas. La campaña `campanas/contenedores-modulos.html` está
escrita con ese marco y enlaza a la calculadora.

### Listas de Brevo para la campaña de contenedores

Creadas el 27/08/2026 a partir del rastreo de Pipedrive, segmentadas porque
nuestros propios datos dicen que las listas pequeñas rinden mucho más (24,1%
de apertura en Carretillas, 597 destinatarios · 11,7% en el envío grande de
plataformas, 931 destinatarios):

| Lista | Nombre | Suscriptores |
|---|---|---:|
| 35 | Contenedores · Casetas y módulos | 293 |
| 36 | Contenedores · Aseos y sanitarios | 151 |
| 37 | Contenedores · Contenedor marítimo | 32 |

De los 530 contactos de origen, 32 ya estaban dados de baja y Brevo los
excluye solo. Recordar las reglas fijas: `sender: {"id": 10}`,
`replyTo: "clientes@equipzilla.com"` explícito, y añadir siempre la lista
**34 · Equipo · copia de envíos**.

### Listas de reactivación por categoría (28/08/2026)

Los 2.582 contactos de la base de 12 meses aún sin trabajar, segmentados por
la categoría que pidieron. Calendario de campañas: sept (38, 39, 40 + casetas
2ª tanda) y oct (41, 42, 43).

| Lista | Nombre | Contactos |
|---|---|---:|
| 38 | Reactivación · Plataformas | 817 |
| 39 | Reactivación · Excavadoras y mini | 545 |
| 40 | Reactivación · Carretillas | 288 |
| 41 | Reactivación · Telescópicos | 264 |
| 42 | Reactivación · Generadores | 255 |
| 43 | Reactivación · Dumper y palas | 214 |

Reglas fijas de siempre: sender id 10, `replyTo clientes@equipzilla.com`,
lista 34 en copia. Ninguna campaña sale sin OK humano.

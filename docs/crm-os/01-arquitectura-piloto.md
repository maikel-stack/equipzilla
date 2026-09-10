# Piloto comercial · contrato con tecnología

Principio (Lorenzo, 10/09): **flexibilidad para negocio + control e integridad para tecnología**.
Cada propuesta se evalúa con una pregunta: ¿permite experimentar y avanzar rápido sin crear una nueva fuente de verdad ni una capa que tecnología tenga que absorber después? Si la respuesta es no, se replantea.

## 1. Fuentes de verdad (única lista válida)

| Entidad | Fuente de verdad | Quién escribe | Cómo entra / sale |
|---|---|---|---|
| Empresas, personas, tratos, etapas, notas, motivo de pérdida | **Pipedrive** | Equipo comercial; el agente solo por API con firma (nota «desde el CRM visual» / «agente») | API + webhooks de Pipedrive (tecnología puede suscribirse hoy) |
| Máquinas en stock | **Hoja de stock de David** (provisional). Destino: la base de máquinas de tecnología | David | Lectura por API de Sheets. Cuando tecnología exponga un endpoint de stock, el piloto lo consume y la hoja se retira |
| Señales de email frío (envíos, respuestas, clics) | **Smartlead** | Smartlead | API. Solo lo que se convierte en lead entra en Pipedrive |
| Señales de email a base de datos (aperturas, clics) | **Brevo** | Brevo | API. Solo lo que se convierte en lead entra en Pipedrive |
| Coste y clics de anuncios | **Google Ads** | Google | API. Las conversiones vuelven a Ads desde Pipedrive (gclid) |
| Tráfico web y eventos | **GA4 / GTM** | Web (tecnología) | API de GA4 |
| Contenido SEO y CRM visual | **Repositorio git** (`equipzilla`) | Agente, con revisión | Deploy a ocasion.equipzilla.com |

No existe ninguna otra base de datos. **No se crea Postgres, Airtable, n8n ni ninguna tabla propia** durante el piloto.

## 2. Todo lo demás es vista derivada

Las hojas «Cola comercial», «Panel · en vivo», «Leads · entrantes» y el CRM visual de ocasion.equipzilla.com/crm se **recalculan cada hora desde las fuentes anteriores**. Se pueden borrar y regenerar sin perder nada. No son fuente de verdad de ningún dato.

Excepción documentada: la pestaña «CRM · notas». Cada nota escrita desde el CRM visual se envía **primero a Pipedrive** (nota en el trato) y se copia en la hoja como caché para lectura rápida. Si hay discrepancia, manda Pipedrive.

Ficheros de estado en `data/*.json` (`stock_visto`, `ads_offline_visto`): son marcas de idempotencia («esto ya se avisó / ya se subió»), no datos de negocio.

## 3. Campos: regla de creación

- Un campo nuevo solo se crea en **Pipedrive** (campo personalizado) y queda registrado en la tabla siguiente. Ninguna hoja ni script define campos que Pipedrive no tenga.
- Campos ya existentes que usa el piloto: `Gclid`, `Utm`, `assetType`, `assetUse`, `Razón Social`, `profesional`.
- Campos derivados que **no** se persisten (se recalculan): score, prioridad, canal de entrada, tipo de empresa, días hasta oferta, «qué tenemos que encaja».
- Si un campo derivado demuestra ser útil de forma estable (por ejemplo, canal de entrada), se propone a tecnología como campo del modelo definitivo; hasta entonces sigue siendo calculado.

## 4. Capa de integración: dos puntos de entrada, nada más

1. **Pipedrive** (API y webhooks): tecnología ya puede leer todo lo comercial sin depender del piloto.
2. **`GET https://ocasion.equipzilla.com/api/crm`** (clave de API, ver `docs/crm-api.md`): devuelve las vistas derivadas (cola, stock normalizado, notas, tiempos). Es lectura de conveniencia, no una fuente. Si desaparece, no se pierde ningún dato.

Todo lo que el agente escribe pasa por la API de Pipedrive y queda como nota o cambio de etapa con autor. No hay escrituras «invisibles».

## 5. Qué pasa con el diseño «CRM OS V1» (`00-diseno.md` y `schema.sql`)

Se **reinterpreta**: el esquema deja de ser una base de datos a desplegar y pasa a ser la **especificación del modelo de datos** que negocio entrega a tecnología. El piloto valida ese modelo sobre Pipedrive + vistas derivadas. Tecnología decide después si, cuándo y dónde se implementa.

Queda cancelada la petición de Neon Postgres.

## 6. Salida del piloto (lo que recibe tecnología)

Al cierre de cada fase (propuesta: 6 semanas) el piloto entrega un informe con:

- entidades y campos realmente usados (con frecuencia de uso) frente a los previstos;
- procesos que han funcionado, con cifras (leads, ofertas, cierres por canal);
- automatizaciones que han producido resultado y cuáles no;
- información que debe persistirse y que hoy solo existe como vista;
- integraciones necesarias (lista de APIs y sentido del flujo);
- qué partes merecen convertirse en producto y cuáles se descartan.

## 7. Lo que necesitamos de tecnología

- Un endpoint de lectura del stock real (referencia, modelo, año, horas, precio, fotos, estado) para retirar la hoja de David.
- Que los formularios de la web envíen `gclid` y `utm` al crear el trato en Pipedrive.
- Revisión y OK de esta tabla de fuentes de verdad. A partir de ahí, cualquier cambio se propone aquí antes de hacerse.

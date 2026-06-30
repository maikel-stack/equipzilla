# equipzilla-seo (Fase 1)

Motor de SEO programático para la compraventa de maquinaria de ocasión. Genera fichas (PDP) y hubs
(`categoría × marca × ubicación`) a partir del inventario. Es la base: define el esquema de listing y la
ficha a la que apuntan el feed, el ABM y las creatividades.

## Correr ya (prueba en 2 minutos)
1. Abre este proyecto en Claude Code.
2. Pídele: *"Genera la ficha de `examples/listing-ejemplo.json` usando `agents/ficha-generator.md`"*.
   Obtienes el JSON con copy + specs + JSON-LD + datos del widget coste-hora.
3. Para un hub: pásale 3+ listings de la misma categoría y `agents/hub-generator.md`.
4. Pinta la salida en `templates/ficha.template.html` / `hub.template.html` y adáptalo a tu Next.js.

## Orden de generación (ver seo/url-structure.md)
1. Hubs de categoría (más volumen de búsqueda).
2. Hubs categoría × provincia con inventario.
3. Hubs categoría × marca (≥3 unidades).
4. Fichas (todas).

## Reglas que no se saltan
- Solo datos del listing (cero specs inventadas).
- Hub con <3 unidades → no se genera.
- Cada hub con copy único (el riesgo aquí es el contenido duplicado).
- IVA deducible visible; honestidad comercial.

---

# Roadmap de fases (todo el lanzamiento)

**Fase 1 — equipzilla-seo** ← ESTE PACK. Ficha + hubs + esquema canónico de listing. Desbloquea orgánico y
  da el activo de destino a todos los canales.

**Fase 2 — equipzilla-feed.** Convierte `listing-input` en feed de producto para Google Shopping/PMax y
  catálogo Meta. Depende del esquema de Fase 1. Desbloquea el paid de producto.

**Fase 3 — equipzilla-abm (track des-flote).** Extiende tu ABM actual para captar inventario de rentales/
  dealers (lado oferta) + cuentas de compra. Alimenta el stock que llena las fichas. Corre en paralelo a F1
  a nivel operativo, pero como build se apoya en el esquema de listing.

**Fase 4 — creatividades + landings (Claude Design).** Sistema de anuncios (Search/PMax/Meta) que se rellenan
  con foto+precio+cuota de cada unidad, + landings de campaña. Consume las 3 versiones del pipeline de foto.

**Transversal — equipzilla-crm-ai** (ya entregado). Convierte el lead en cierre asistido.

Secuencia recomendada de build: F1 → F2 → F3 → F4, con CRM-AI conectándose en cuanto F1 genere las primeras
fichas con CTA "Me interesa".

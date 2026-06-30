# Ejecución equipzilla-seo (Fase 1)

Ejecutado el quick-start del pack (`README.md` → "Correr ya").

## Ficha generada
- **Agente:** `agents/ficha-generator.md`
- **Input:** `examples/listing-ejemplo.json` (id `44210`, Kubota U48-4 2019, miniexcavadora, Madrid)
- **Salida JSON:** `output/ficha-44210.json` — 12 claves del agente, validado:
  - `seo_title` 50/60 car. · `meta_description` 135/155 car.
  - JSON-LD parseable: `Product` + `Offer` + `BreadcrumbList` + `FAQPage`.
  - Solo datos del listing (cero specs inventadas). Las cifras del `widget_coste_hora`
    van marcadas como estimación (`estimado: true`, confianza media-baja).
- **Render HTML:** `output/ficha-44210.html` — `templates/ficha.template.html` relleno.
  - URL canónica: `/compra/kubota-u48-4-2019-44210` (según `seo/url-structure.md`).

## Hubs
**No generados.** Regla dura: un hub necesita ≥3 unidades de la misma categoría/marca/zona.
El pack solo trae 1 listing de ejemplo, así que ningún cruce de la taxonomía alcanza el mínimo.
Para generar hubs, pasar ≥3 listings de la misma categoría a `agents/hub-generator.md`
(prioridad: categoría → categoría×provincia → categoría×marca → fichas).

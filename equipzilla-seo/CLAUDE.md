# CLAUDE.md — equipzilla-seo

## Qué es este workstream
Motor de generación SEO programática para la compraventa de maquinaria de ocasión de Equipzilla.
Convierte el inventario en (a) **fichas de producto** individuales indexables y (b) **hubs** de
`categoría × marca × ubicación`. Es la base orgánica de coste marginal cero y el activo al que apuntan
todos los demás canales (paid, email, ABM): todos enlazan a una ficha, nunca a la home.

Patrón de referencia: Clicars (fichas individuales + árbol de hubs por marca/modelo/provincia).

## Dos agentes
1. **ficha-generator** (`agents/ficha-generator.md`) — input: 1 listing → output: contenido de la ficha
   (copy + specs + JSON-LD Product/Offer + meta + alt de imágenes + datos del widget coste-hora).
2. **hub-generator** (`agents/hub-generator.md`) — input: un nodo (categoría/marca/ubicación) + sus listings
   → output: hub con copy único, FAQ, enlazado interno y JSON-LD CollectionPage/ItemList/BreadcrumbList.

## Reglas duras (no negociables)
- **Cero specs inventadas.** Solo datos presentes en el listing. Si falta un dato → se omite, no se rellena.
- **Cada hub con copy ÚNICO.** El mayor riesgo SEO aquí es el contenido duplicado/thin. Nada de plantillas
  rellenadas idénticas: el intro y la FAQ de cada hub deben variar según categoría/marca/zona reales.
- **IVA deducible siempre visible** (B2B; pesa más que en coches).
- **Honestidad.** Sin "mejor precio del mercado" si no se puede sostener. Sin garantías sin respaldo legal.
- Salida en **español** (es-ES y es-MX según mercado del listing).

## Estructura de URLs
Definida en `seo/url-structure.md`. Resumen:
- Ficha:        `/compra/{marca}-{modelo}-{año}-{id}`
- Hub categoría:`/compra/{categoria}/segunda-mano`
- Hub marca:    `/compra/{categoria}/{marca}/segunda-mano`
- Hub ubicación:`/compra/{categoria}/segunda-mano/{provincia}`

## Cómo se ejecuta (Claude Code)
Para cada listing del inventario → ficha-generator. Para cada combinación viable de la taxonomía con
≥3 listings → hub-generator (no generar hubs vacíos o casi vacíos: penaliza). Validar JSON-LD antes de publicar.

## Taxonomía
En `taxonomy/` (categorías, marcas, provincias). Es la matriz de la que salen las URLs de hub.
Solo generar el cruce que tenga inventario suficiente.

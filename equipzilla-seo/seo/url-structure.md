# Estructura de URLs e enlazado interno — Equipzilla compra

Patrón inspirado en Clicars (fichas indexables + árbol de hubs). Objetivo: capturar la cola larga de intención
de compra (`comprar {máquina} segunda mano {provincia}`) y distribuir autoridad hacia las fichas.

## Patrones de URL

| Tipo | Patrón | Ejemplo |
|------|--------|---------|
| Ficha (PDP) | `/compra/{marca}-{modelo}-{año}-{id}` | `/compra/caterpillar-308-2019-44210` |
| Hub categoría | `/compra/{categoria}/segunda-mano` | `/compra/miniexcavadoras/segunda-mano` |
| Hub subcategoría | `/compra/{categoria}/{subcategoria}/segunda-mano` | `/compra/plataformas-elevadoras/tijera/segunda-mano` |
| Hub marca | `/compra/{categoria}/{marca}/segunda-mano` | `/compra/miniexcavadoras/kubota/segunda-mano` |
| Hub ubicación | `/compra/{categoria}/segunda-mano/{provincia}` | `/compra/carretillas-elevadoras/segunda-mano/barcelona` |
| Sell-side | `/vende-tu-maquinaria` | (captación de oferta / des-flote) |

Reglas de slug: minúsculas, sin acentos, guiones; `{id}` numérico al final para unicidad (evita colisiones).

## Reglas SEO
- **Canonical** propio en cada ficha y hub. Filtros que no aportan contenido único → canonical al hub base + `noindex`.
- **No indexar** hubs con <3 unidades (ver hub-generator). Mejor no existir que existir vacío.
- **Paginación** de hubs: `?page=N` con `rel-next/prev` o carga incremental; la página 1 es la canónica.
- **BreadcrumbList** en JSON-LD en todas las páginas.
- Ficha vendida: mantener URL viva con estado "vendida" + CTA a similares durante un tiempo, luego 301 al hub
  (no 404: conserva el SEO ganado y captura demanda residual).

## Enlazado interno (clave para distribuir autoridad)
- Cada **ficha** enlaza ARRIBA a: hub categoría, hub marca, hub provincia. Y LATERAL a 2-3 máquinas similares.
- Cada **hub** enlaza a: hubs hermanos (otras marcas de la categoría, provincias vecinas), categoría padre,
  y a sus unidades destacadas.
- El **footer** replica el bloque de "categorías × provincias" (como Clicars) para crear malla de enlazado.

## Prioridad de generación
1. Hubs de categoría (los de más volumen de búsqueda).
2. Hubs categoría × provincia de las zonas con inventario.
3. Hubs categoría × marca de las marcas con ≥3 unidades.
4. Fichas (todas las unidades).

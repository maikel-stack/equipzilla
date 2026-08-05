# Equipzilla — Proyecto SEO

## Contexto del negocio
Equipzilla opera en el sector del **alquiler de maquinaria** (B2B). Disponemos de un
directorio de empresas de alquiler de maquinaria por país, región y especialidad
(construcción, elevación / plataformas, grúas, industrial, agrícola, generalista),
con datos de contacto enriquecidos vía Apollo.io.

El objetivo SEO es convertir ese directorio en tráfico orgánico mediante:
1. **SEO programático**: páginas de aterrizaje por (tipo de máquina × ciudad/región).
2. **Investigación de keywords** y detección de huecos de contenido frente a
   competidores (Loxam, Kiloutou, Boels, Ramirent, Riwal, Hune…).
3. **Auditoría técnica** del sitio.

## Datos
- `data/directorio.csv` — directorio de empresas. Columnas:
  `empresa, pais, region, especialidad, ciudad, email, web, telefono, contacto, cargo`.
- Mantén siempre las columnas y los nombres en español, igual que en los exports de Apollo.
- **Nunca inventes proveedores, ciudades ni datos de contacto.** Toda página y todo
  listado debe basarse exclusivamente en lo que existe en `data/directorio.csv`.

## Convenciones SEO
- Idioma de todo el contenido público: **español** (variantes localizadas por país si aplica).
- URLs limpias y descriptivas con el patrón: `/alquiler-{categoria}-{ciudad}/`
  (en minúsculas, con guiones y sin acentos — usa el `slugify` del script).
- Cada página debe incluir:
  - Un `<title>` de 50-60 caracteres.
  - Una `meta description` de 140-160 caracteres con llamada a la acción.
  - Un **único** `<h1>` con la keyword principal.
  - JSON-LD (`Service` + `BreadcrumbList`).
  - Enlaces internos a categorías y ciudades relacionadas.
- No publiques páginas sin proveedores reales: cada landing necesita al menos una empresa
  del directorio.

## Analítica por API (Search Console + GA4)
Estrategia SEO basada en datos reales, todo por API con **una sola cuenta de servicio** de
Google Cloud (misma clave JSON para ambos):
- `scripts/gsc_pull.py` — Search Console (Search Analytics). Dar a la SA acceso a la
  propiedad en Search Console → Configuración → Usuarios. `webmasters.readonly`.
- `scripts/ga4_pull.py` — GA4 Data API. Dar a la SA rol *Viewer* en la propiedad GA4.
  `analytics.readonly`. Requiere `--property <ID numérico>`.
- `scripts/estrategia_seo.py` — motor que cruza ambos y genera `output/estrategia_seo.md`
  + `output/oportunidades.csv` con buckets priorizados (quick-wins pos 5-20, CTR bajo
  para reescribir title/meta, huecos de contenido, funnel de compra).
- Clave por defecto en `GSC_KEY` (`/home/user/.gsc/equipzilla-sa.json`). Deps: `rsa`, `pyasn1`.

Flujo: `gsc_pull.py` [+ `ga4_pull.py`] → `estrategia_seo.py`.

## Cómo trabajar con los agentes
- Para generar las páginas a escala usa el script `scripts/generar_paginas_seo.py`
  (corre en local, sin dependencias externas y sin consumir tokens).
- Los agentes especializados están en `.claude/agents/`. Delega en ellos según la tarea:
  - **seo-programatico** — genera las landing pages a escala.
  - **keyword-research** — mapa de keywords y huecos de contenido frente a competidores.
  - **auditoria-tecnica** — auditoría SEO técnica sobre `output/` o un dominio dado.
- El comando `/seo-run` ejecuta el flujo completo en orden:
  keyword-research → seo-programatico → auditoria-tecnica.

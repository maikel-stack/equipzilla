---
description: Ejecuta el flujo SEO completo de Equipzilla (research → páginas → auditoría)
---

Ejecuta el flujo SEO completo para Equipzilla en este orden, delegando en los subagentes:

1. Usa el subagente **keyword-research** para generar `output/keyword_map.csv` y
   `output/content_gaps.md` a partir del directorio. Si el usuario indicó categorías o
   mercados concretos en su mensaje ($ARGUMENTS), limítate a esos; si no, prioriza los
   mercados con más proveedores en `data/directorio.csv`.

2. Usa el subagente **seo-programatico** para generar las páginas de aterrizaje en `output/`,
   priorizando las combinaciones identificadas como huecos de alto impacto en el paso 1.

3. Usa el subagente **auditoria-tecnica** para auditar las páginas generadas en `output/` y
   escribir `output/auditoria_seo.md`.

Al final, resume en 5-8 líneas: cuántas páginas se crearon, las 3 oportunidades de keyword
más fuertes y los problemas técnicos críticos detectados.

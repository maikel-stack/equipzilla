# Prompt maestro — Generador de artículos SEO + LLM (AEO/GEO)

> Metodología oficial de redacción del blog de Equipzilla (compraventa).
> Entregado por Maikel el 03/09/2026. Todo artículo del blog se genera
> siguiendo estos pasos y reglas. Prioridad: intención de búsqueda →
> utilidad → calidad → profundidad → estructura → SEO → optimización LLM.

## Flujo por keyword
1. **Analizar la keyword**: intención real (no literal), tipo de contenido,
   cluster de variantes/entidades/preguntas. Si dos keywords comparten
   intención → un solo artículo.
2. **Ángulo editorial**: qué problema resuelve, qué lo diferencia, qué
   debería poder extraer un LLM.
3. **Título SEO** (50-65 char), **Meta Title** distinto del H1 (50-60),
   **Meta Description** (140-160).
4. **Estructura H1/H2/H3** que responde progresivamente; cada H2 = subtema
   real, no percha de keyword.
5. **Answer first**: la respuesta principal en la introducción o primeros
   párrafos. Prohibidas intros de relleno ("Hoy en día…").
6. **Contenido**: párrafos cortos, listas, tablas cuando ayuden, pasos,
   datos concretos ("entre X e Y"), pros/contras. Sin relleno.
7. **Optimización LLM/GEO**: respuestas autocontenidas, definiciones
   "X es…", información estructurada, entidades naturales.
8. **FAQ** con preguntas reales, respuestas directas y autocontenidas.
9. **SEO semántico**: cobertura temática > densidad. Nunca frase
   antinatural por meter keyword.
10. **Enlaces internos**: anchors naturales; si la URL no existe,
    placeholder `[ARTÍCULO RELACIONADO: …]`.
11. **CTA según intención**: informacional → suave; comercial → producto;
    transaccional → directo.
12. **E-E-A-T**: experiencia práctica y datos REALES del negocio
    (precios de nuestro stock, criterios de tasación). PROHIBIDO inventar
    datos, estudios, clientes o resultados.
13. **Longitud**: la que pida la intención (800-4.000 palabras). Todo lo
    necesario y nada más.
14. **Control de calidad** antes de cerrar: utilidad, intención, SEO,
    extractabilidad LLM, escaneabilidad, originalidad, conversión,
    naturalidad.

## Reglas absolutas
No escribir para Google sino para resolver la búsqueda · no keyword
stuffing · no inventar datos ni fuentes · no frases genéricas de IA · no
intros vacías · respuestas concretas y autocontenidas · tablas/listas
cuando mejoren comprensión · un artículo por intención (agrupar keywords
gemelas) · la keyword es punto de partida, no objetivo.

## Reglas propias de Equipzilla (añadidas al prompt maestro)
- Nunca mencionar proveedores/alquiladores de origen (GAM, LOXAM,
  distribuidores) en contenido visible.
- Los precios de ejemplo salen de nuestro stock y campañas reales
  (`data/machines.json`, campañas Brevo) — es nuestra ventaja E-E-A-T.
- CTA estándar: WhatsApp 606 836 581 (David) + clientes@equipzilla.com.
- Artículos en `seo/articulos/<slug>.html` con schema Article + FAQPage;
  estado registrado en `seo/keywords_master.csv` y en el Sheet de mando.

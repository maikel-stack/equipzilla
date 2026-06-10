---
description: Ejecuta el flujo ABM completo de Equipzilla — scoring de cuentas, dossiers y secuencias para las N cuentas top (por defecto 10).
argument-hint: "[N] (nº de cuentas top a trabajar, por defecto 10)"
---

Orquesta el flujo de Account-Based Marketing de Equipzilla de principio a fin.

**N = $1** (número de cuentas top a trabajar). Si `$1` está vacío o no es un número válido,
usa **N = 10**.

Lee primero `CLAUDE.md` para recordar el ICP y las convenciones (idioma español, fuente
única `data/cuentas.csv`, prohibido inventar datos).

Ejecuta en este orden:

## Paso 1 — Scoring
Lanza el subagente **`scoring-cuentas`**. Debe leer `data/cuentas.csv`, puntuar todas las
empresas según el ICP de `CLAUDE.md` y generar `output/cuentas_priorizadas.csv` ordenado por
score descendente. Espera a que termine.

## Paso 2 — Selección de las top N
Lee `output/cuentas_priorizadas.csv` y toma las **N primeras** empresas (las de mayor
`score_total`). Si hay menos de N cuentas, trabaja todas las disponibles.

## Paso 3 — Dossiers
Para **cada** una de las N cuentas seleccionadas, lanza el subagente **`dossier-cuenta`** con
el nombre de la empresa. Genera `output/dossiers/{empresa-slug}.md`. Puedes lanzar varios
dossiers en paralelo si es posible; respeta que cada uno usa Apollo.io/web sin inventar datos.

## Paso 4 — Secuencias
Para **cada** cuenta con dossier generado, lanza el subagente **`secuencia-personalizada`**.
Genera `output/secuencias/{empresa-slug}.md` a partir de su dossier.

## Paso 5 — Resumen final
Cuando termine todo, presenta un resumen en español con:
- Nº de cuentas puntuadas y reparto por tier (A/B/C).
- Nº de dossiers y secuencias generados, con rutas de salida.
- Las **3 cuentas de mayor encaje** (mayor score), y para cada una:
  - Empresa, score y tier.
  - **Ángulo de aproximación recomendado** (del dossier).
  - Decisor principal (nombre y cargo) si se localizó.

No inventes resultados: si algún paso no encontró datos (p. ej. sin señales verificables o
sin Apollo), refléjalo tal cual en el resumen.

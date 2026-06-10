# Equipzilla — Agentes SEO para Claude Code

Tres agentes de SEO listos para ejecutar, más un script de SEO programático que ya
funciona sobre el directorio de empresas.

## Estructura
```
equipzilla-seo/
├── CLAUDE.md                     # Contexto del proyecto (se carga solo)
├── .claude/
│   ├── agents/
│   │   ├── seo-programatico.md   # Genera landing pages a escala
│   │   ├── keyword-research.md   # Mapa de keywords + huecos de contenido
│   │   └── auditoria-tecnica.md  # Auditoría SEO técnica
│   └── commands/
│       └── seo-run.md            # /seo-run → flujo completo
├── data/
│   └── directorio.csv            # Tu directorio (sustitúyelo por el export real de Apollo)
├── scripts/
│   └── generar_paginas_seo.py    # Generador de páginas SEO programáticas
└── output/                       # Aquí se escriben páginas, sitemap y informes
```

## Cómo ejecutar (ya)

1. Abre la carpeta en Claude Code:
   ```bash
   cd equipzilla-seo
   claude
   ```

2. Comprueba que los agentes están cargados:
   ```
   /agents
   ```

3. Opciones para lanzar:

   - **Todo el flujo de una vez:**
     ```
     /seo-run
     ```
   - **Solo generar páginas** (es lo más inmediato; el script ya corre sin IA):
     ```
     Usa el subagente seo-programatico para generar las páginas
     ```
     o directamente desde la terminal:
     ```bash
     python scripts/generar_paginas_seo.py
     ```
   - **Solo research de keywords:**
     ```
     Usa el subagente keyword-research para Barcelona y Madrid
     ```
   - **Solo auditoría:**
     ```
     Usa el subagente auditoria-tecnica sobre las páginas de output/
     ```

## Usar tus datos reales
Sustituye `data/directorio.csv` por tu export de Apollo manteniendo estas columnas:
`empresa, pais, region, especialidad, ciudad, email, web, telefono, contacto, cargo`.
La columna **ciudad** es la que dispara las combinaciones por localidad; asegúrate de rellenarla.

## Notas
- Requiere Node.js y Claude Code instalado (`npm install -g @anthropic-ai/claude-code`).
- El script de páginas no consume tokens: corre en local con Python 3 (sin dependencias externas).
- `keyword-research` y `auditoria-tecnica` usan búsqueda/fetch web, así que sí consumen tokens.

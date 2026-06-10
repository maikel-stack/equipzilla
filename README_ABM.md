# Sistema de Agentes ABM — Equipzilla

Sistema de **Account-Based Marketing (ABM)** para Equipzilla (marketplace B2B de alquiler de
maquinaria industrial en España). Prioriza la lista de cuentas objetivo, construye fichas de
venta y redacta secuencias de contacto personalizadas — todo en español y **sin inventar
datos**.

> Proyecto **independiente** del sistema de bots de n8n documentado en `README.md`.

---

## Estructura

```
.
├── CLAUDE.md                          # Contexto de negocio, convenciones y ICP (editable)
├── data/
│   └── cuentas.csv                    # Lista de cuentas objetivo (fuente única de verdad)
├── .claude/
│   ├── agents/
│   │   ├── scoring-cuentas.md         # Puntúa cuentas según el ICP
│   │   ├── dossier-cuenta.md          # Ficha de venta por cuenta
│   │   └── secuencia-personalizada.md # Secuencia multicanal por cuenta
│   └── commands/
│       └── abm-run.md                 # Orquestador del flujo completo
├── .mcp.json.example                  # Plantilla para conectar el MCP de Apollo.io
└── output/                            # Se genera al ejecutar
    ├── cuentas_priorizadas.csv
    ├── dossiers/{empresa-slug}.md
    └── secuencias/{empresa-slug}.md
```

---

## Ejecución

### Flujo completo (recomendado)

En Claude Code, dentro del repositorio:

```
/abm-run            # trabaja las 10 cuentas top (por defecto)
/abm-run 5          # trabaja solo las 5 de mayor encaje
/abm-run 20         # trabaja las 20 top
```

El comando ejecuta en orden:

1. **`scoring-cuentas`** → `output/cuentas_priorizadas.csv` (ordenado por score).
2. **`dossier-cuenta`** para las N cuentas top → `output/dossiers/{empresa-slug}.md`.
3. **`secuencia-personalizada`** para cada dossier → `output/secuencias/{empresa-slug}.md`.
4. **Resumen final**: las 3 cuentas de mayor encaje con su ángulo de aproximación.

### Agentes por separado

También puedes invocar cada subagente de forma individual, por ejemplo:

- «Puntúa todas las cuentas» → `scoring-cuentas`.
- «Hazme el dossier de *GrúasTorre y Elevación Levante S.A.*» → `dossier-cuenta`.
- «Redacta la secuencia para esa cuenta» → `secuencia-personalizada`.

---

## El ICP es editable

El Perfil de Cliente Ideal vive en `CLAUDE.md` (sección **Perfil de Cliente Ideal (ICP)**):
dimensiones (tamaño, especialidad, cobertura regional, madurez digital), **pesos** y
**rúbricas**. Edítalo para afinar el scoring; los agentes leen esos valores en cada
ejecución. Mantén que los pesos sumen 100.

---

## Conectar Apollo.io (servidor MCP)

Los contactos están enriquecidos vía **Apollo.io**. Si conectas su servidor MCP, el agente
`dossier-cuenta` lo usará para obtener/confirmar decisores (nombre, cargo, email, teléfono,
LinkedIn). Si no está conectado, se usan los contactos del `data/cuentas.csv`. **Nunca** se
inventan contactos.

### Pasos

1. Copia la plantilla a la config real de MCP del repositorio:

   ```bash
   cp .mcp.json.example .mcp.json
   ```

2. Exporta tu clave de API de Apollo.io como variable de entorno (no la escribas en el
   fichero):

   ```bash
   export APOLLO_API_KEY="tu_api_key_de_apollo"
   ```

3. Ajusta la `url` del servidor MCP de Apollo.io en `.mcp.json` a la que te indique tu
   proveedor/instalación. La plantilla (`.mcp.json.example`) tiene esta forma — JSON no
   admite comentarios, así que la "versión comentada" se documenta aquí:

   ```jsonc
   {
     "mcpServers": {
       "apollo": {
         "type": "http",                         // transporte HTTP del servidor MCP
         "url": "https://.../mcp",               // endpoint del MCP de Apollo.io
         "headers": {
           "Authorization": "Bearer ${APOLLO_API_KEY}"  // se lee de la variable de entorno
         }
       }
     }
   }
   ```

   > Si usas una instalación local del servidor por stdio en lugar de HTTP, el bloque sería:
   > ```jsonc
   > "apollo": {
   >   "command": "npx",
   >   "args": ["-y", "<paquete-del-mcp-de-apollo>"],
   >   "env": { "APOLLO_API_KEY": "${APOLLO_API_KEY}" }
   > }
   > ```

4. Reinicia Claude Code para que cargue el servidor MCP. Comprueba que las herramientas
   `mcp__apollo__*` están disponibles.

> **Importante:** `.mcp.json` puede contener configuración sensible. Añádelo a `.gitignore`
> si no quieres versionarlo. La plantilla `.mcp.json.example` sí se versiona.

---

## Sustituir el CSV de muestra por el export real

`data/cuentas.csv` incluye datos **de muestra** (empresas ficticias) para que el sistema
funcione de inmediato. Para usar tu directorio real:

1. Exporta tu lista de cuentas (directorio de empresas de alquiler enriquecido con
   Apollo.io) a CSV.
2. Asegúrate de que las **columnas coinciden exactamente** (mismo nombre y orden):

   ```
   empresa,pais,region,especialidad,ciudad,email,web,telefono,contacto,cargo,empleados,facturacion
   ```

   - `empleados`: número entero.
   - `facturacion`: en euros, número sin separadores de miles (p. ej. `9500000`).
   - `especialidad`: usa categorías coherentes con las rúbricas del ICP en `CLAUDE.md`
     (elevación, movimiento de tierras, manutención, obra civil, generadores, etc.).
   - Campos sin dato: déjalos vacíos. Los agentes los tratan como "sin verificar" y **no**
     los inventan.
3. Reemplaza el fichero (manteniendo la ruta `data/cuentas.csv`) y vuelve a ejecutar
   `/abm-run`.

Si necesitas columnas adicionales, añádelas al final y actualiza las rúbricas del ICP en
`CLAUDE.md` para que el scoring las tenga en cuenta.

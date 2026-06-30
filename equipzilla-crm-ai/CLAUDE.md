# CLAUDE.md — equipzilla-crm-ai

## Qué es este workstream
El "cerebro" de IA del CRM de Equipzilla (compraventa de maquinaria de ocasión).
Son dos agentes independientes que se disparan en dos momentos del funnel:

1. **Lead Intelligence** → cuando entra un lead (formulario "Me interesa", WhatsApp, llamada).
   Devuelve un dossier completo del lead/empresa para que el comercial entre a la llamada sabiéndolo todo.

2. **Deal Intelligence** → cuando un lead muestra interés en una máquina concreta.
   Devuelve si el precio es de mercado, cómo se justifica el valor para ESE comprador,
   y un guion de objeciones + margen de negociación.

No es un CRM completo: es la capa de inteligencia que se conecta encima del CRM (HubSpot/Pipedrive/propio)
vía webhook o API. La salida de cada agente es JSON estructurado (ver `/schemas`) que se pinta en la ficha del lead/deal.

## Principios
- **Cero invención.** Si un dato no está, se marca `null` y `confidence: "low"`. Nunca rellenar a ojo.
- **Trazabilidad.** Cada dato enriquecido lleva su `source` (apollo | web | listing | crm).
- **Salida en español** (la usa el equipo comercial en España/México). Scaffolding técnico en inglés.
- **Accionable, no descriptivo.** Cada dossier termina en `next_best_action` + mensaje sugerido listo para enviar.

## Herramientas disponibles
- **Apollo.io (MCP)** — ya conectado. Enriquecimiento de empresa y personas, búsqueda de decisores.
- **web_search** — comparables de precio, noticias de la empresa, valor residual.
- (Opcional) Tabla interna `comps` de operaciones cerradas para price-check con datos propios.

## Cómo se ejecuta
Cada agente es un system prompt (en `/agents`). Se invoca con la API de Claude pasando:
- el system prompt del agente,
- el payload de entrada (lead crudo o listing + dossier),
- los MCP servers necesarios (Apollo para lead-intelligence).
Modelo recomendado: Sonnet para volumen, Opus para deals de alto ticket.

## Estructura
- `agents/lead-intelligence.md` — system prompt agente 1
- `agents/deal-intelligence.md` — system prompt agente 2
- `schemas/lead-dossier.json` — esquema de salida agente 1
- `schemas/deal-brief.json` — esquema de salida agente 2
- `prompts/objection-library.md` — biblioteca semilla de objeciones de maquinaria de ocasión

# equipzilla-crm-ai

Capa de inteligencia con IA para el CRM de Equipzilla (compraventa de maquinaria de ocasión).
Dos agentes que se enchufan al CRM por webhook/API y devuelven JSON estructurado.

## Flujo
```
Lead entra (form/WhatsApp)  ──►  Agente Lead Intelligence  ──►  lead-dossier.json  ──►  ficha del lead en CRM
        │
        └─ se interesa por máquina ──► Agente Deal Intelligence ──► deal-brief.json ──► ficha del deal
```

## Cómo conectarlo
1. Webhook del CRM dispara al recibir lead → llama a la API de Claude con el system prompt de
   `agents/lead-intelligence.md`, el payload del lead, y el MCP de Apollo conectado.
2. La respuesta (JSON validado contra `schemas/lead-dossier.json`) se escribe en la ficha del lead.
3. Cuando el lead pasa a "interesado en máquina X", se dispara el agente de `agents/deal-intelligence.md`
   pasándole el listing + el dossier ya generado.

## Modelo
- Volumen / leads fríos: Claude Sonnet.
- Deals de alto ticket (>30k€): Claude Opus.

## Notas de cumplimiento
- Enriquecimiento de datos de personas: revisar base legal RGPD (interés legítimo B2B) antes de producción.
- Garantía mecánica y financiación: textos legales a validar con asesoría (como hace Clicars con su garantía
  legal y condiciones). El agente no debe prometer coberturas sin respaldo.

## Roadmap sugerido
- v1: los dos agentes con Apollo + web_search (este pack).
- v2: tabla `comps` interna de operaciones cerradas → price-check con datos propios, mucho más preciso.
- v3: agente de seguimiento que redacta la secuencia completa de follow-up por deal.

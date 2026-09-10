# Reglas comunes de los agentes de growth de Equipzilla

(Este fichero no es un agente; cada agente lo lee al empezar con `cat .claude/agents/_reglas.md`.)

- Idioma: español. Reportes cortos, con cifras reales. **No inventes datos**: si una fuente falla, dilo y sigue.
- Credenciales en `~/.outbound/` (chmod 600). Nunca se copian al repo ni al reporte. Si falta una, el script aborta con su nombre: repórtalo.
- Fuentes de verdad: Pipedrive (comercial), hoja de stock de David (máquinas), Smartlead (frío), Brevo (base de datos), Google Ads, GA4/Search Console. No crees bases de datos, hojas ni campos nuevos fuera de ellas. Todo lo demás son vistas derivadas (contrato con tecnología: `docs/crm-os/01-arquitectura-piloto.md`).
- **Ningún envío a clientes sin OK humano explícito** (campañas Brevo, secuencias Smartlead, WhatsApp). Preparar sí; enviar no. Los tests internos (Brevo `sendTest` a la lista 34 / a Maikel) sí están permitidos.
- Los clientes nunca ven referencias de proveedores (GAM, LOXAM, mercaeleva, gomariz, BAU, gamrentals, 93 897 47 25) en textos, fotos ni enlaces.
- No tocar las columnas LLAMADO / RESULTADO del Sheet de mando: son del equipo.
- Brevo: remitente id 10, replyTo clientes@equipzilla.com, copia a la lista 34.
- Equipo: Maikel (CEO), Andrés (manager comercial), David Devis (comercial, 606 836 581), Héctor (comercial), Lorenzo (tecnología). Objetivo 2026: 25 operaciones · 500.000 € GMV.
- Git: rama `claude/brevo-equipzilla-template-t47ip0`. Commits sin identificador de modelo, terminados en
  `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` y `Claude-Session: https://claude.ai/code/session_01VocQvfv1wntGENrdtGDomp`.

## Formato del reporte (obligatorio, es lo que devuelves al Director de Growth)

```
[AGENTE · fecha hora Madrid]
KPI: tabla de 3-6 líneas (dato | valor | vs. anterior)
Hecho hoy: 1-4 líneas
Hallazgos: lo que cambia decisiones (o «nada relevante»)
Propongo: acciones concretas con quién y para cuándo
Necesito: bloqueos u OKs pendientes (o «nada»)
```

Guarda además el reporte en `reportes/<agente>/<YYYY-MM-DD>.md` (crea la carpeta si no existe) y haz commit + push. Si el push falla por red, reintenta 4 veces con 2/4/8/16 s.

# Plantilla Brevo · Lead de COMPRA (aviso al equipo)

Equivalente al aviso automático de leads de alquiler (plantilla **#20 «Equipzilla ·
Lead texto plano»**, de 2020), pero escrita para compraventa: la máquina y su precio
mandan, y el remate es «llamada en menos de 24 h», no «te pasamos presupuesto».

- **ID de plantilla: `222`** — «Equipzilla - Lead de COMPRA (aviso equipo)»
- Remitente: `clientes@equipzilla.com` (sender id 10). `replyTo` por defecto el mismo;
  conviene sobrescribirlo en cada envío con el email del lead, así David contesta
  dándole a «Responder».
- Fuente del HTML en este repo: `plantillas/brevo-lead-compra.html` (si se toca aquí,
  hay que subirlo a Brevo con `PUT /v3/smtp/templates/222`; Brevo es la copia viva).

## Cómo se envía

```bash
curl -X POST https://api.brevo.com/v3/smtp/email \
  -H "api-key: $BREVO_API_KEY" -H "content-type: application/json" -d '{
  "to": [{"email":"david@equipzilla.com","name":"David"},
         {"email":"andres@equipzilla.com","name":"Andrés"},
         {"email":"maikel@equipzilla.com","name":"Maikel"}],
  "replyTo": {"email":"juan@montajeslevante.es","name":"Juan Pérez"},
  "templateId": 222,
  "tags": ["lead-compra"],
  "params": { ... }
}'
```

## Parámetros

Todos son opcionales salvo los de contacto: cada bloque desaparece si su parámetro
viene vacío, así que no hay que rellenar lo que el formulario no pregunte. Si no llega
`maquina`, el email lo dice («pide asesoramiento») en vez de dejar un hueco.

| Parámetro | Ejemplo | Para qué |
|---|---|---|
| `maquina` | `2013 Haulotte Compact 12 · plataforma tijera 12 m` | Titular del email y del asunto |
| `assetType` | `Plataforma elevadora` | Categoría |
| `referencia` | `PL-COMPACT12-2013` | Referencia del anuncio |
| `precio` | `9.900 €` | Precio publicado (ya formateado) |
| `urlMaquina` | `https://equipzilla.com/maquinaria/...` | Botón «Ver la ficha» |
| `nombreUsuario` | `Juan Pérez` | Contacto |
| `empresa` | `Montajes Levante S.L.` | Contacto |
| `telefonoUsuario` | `600 111 222` | Contacto, sale como enlace `tel:` |
| `emailUsuario` | `juan@montajeslevante.es` | Contacto, enlace `mailto:` |
| `city` | `Valencia` | Zona |
| `assetUse` | `Mantenimiento de naves, uso interior` | Para qué la quiere |
| `plazo` | `Este mes` | Urgencia |
| `presupuesto` | `Hasta 12.000 €` | Presupuesto declarado |
| `financiacion` | `Sí, a 36 meses` | Si pide financiación |
| `entrega` | `Transporte a Paterna` | Transporte / entrega |
| `mensaje` | texto libre | Lo que escribe el cliente |
| `origen` | `ficha de máquina` | Aparece en el titular y en el asunto |
| `submissionid` | `C-2026-0417` | Referencia interna de la solicitud |

Asunto resultante:
`🛒 Lead de COMPRA: 2013 Haulotte Compact 12 · Juan Pérez`

## Notas

- El aviso es **interno**. No lleva ninguna referencia a proveedores ni a los
  distribuidores de origen, y no debe reenviarse tal cual al cliente.
- Si además hay que crear el trato en Pipedrive, sigue valiendo `quiz/api/_lead.js`
  (`pushToPipedrive`), que ya escribe en el pipeline 6.
- Pruebas enviadas a maikel@ el 21/09: una con todos los campos y otra solo con
  nombre, teléfono y email, para ver cómo queda cuando el formulario recoge poco.

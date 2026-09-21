# Plantillas Brevo · leads de COMPRA

Dos plantillas, una por cada lado de la misma solicitud:

| | Plantilla | Para quién |
|---|---|---|
| Aviso interno | **#222** «Equipzilla - Lead de COMPRA (aviso equipo)» | David, Andrés, Maikel |
| Acuse al cliente | **#223** «Equipzilla - Compra · acuse al cliente» | quien rellena el formulario |

Comparten los mismos nombres de parámetros, así que con un solo objeto se
pueden disparar las dos llamadas seguidas.

---

## #222 · Aviso al equipo

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

---

## #223 · Acuse al cliente

El equivalente en compra de la plantilla **#21 «Equipzilla Bienvenida con
alquilador contactará»**, que es la que confirma al cliente una solicitud de
alquiler. Aquella dice «estamos buscando entre nuestros alquiladores»; ésta dice
lo único que aplica en compraventa: **te llamamos en menos de 24 h laborables**,
y adelanta qué se resuelve en esa llamada (estado y horas reales, garantía y
financiación, transporte, alternativas si esa máquina no encaja).

Es transaccional: solo se manda como respuesta a una solicitud del propio
cliente, nunca como envío masivo.

```bash
curl -X POST https://api.brevo.com/v3/smtp/email \
  -H "api-key: $BREVO_API_KEY" -H "content-type: application/json" -d '{
  "to": [{"email":"juan@montajeslevante.es","name":"Juan Pérez"}],
  "templateId": 223,
  "tags": ["compra-acuse-cliente"],
  "params": { ... }
}'
```

Usa los mismos parámetros que la #222 (`nombreUsuario`, `maquina`, `assetType`,
`precio`, `referencia`, `urlMaquina`, `city`, `plazo`, `submissionid`) y añade
dos opcionales:

| Parámetro | Ejemplo | Para qué |
|---|---|---|
| `comercial` | `David Devis` | Quién firma y quién va a llamar. Sin él, firma «El equipo de Equipzilla» |
| `comercialMovil` | `606836581` | Añade el enlace de WhatsApp. Sin él solo aparece el 911 238 750 |

Asunto: `Hemos recibido tu solicitud: Haulotte Compact 12 (2013)...`

### Cuidado con lo que se le pasa

Este email **lo lee el cliente**, así que `maquina`, `referencia` y `urlMaquina`
tienen que ser los nuestros: el título y la ficha de equipzilla.com y nuestra
referencia interna. Nunca el enlace, la referencia ni el nombre del distribuidor
de origen. Si el formulario arrastra la URL del proveedor, hay que traducirla a
la nuestra antes de llamar a la plantilla.

Pruebas enviadas a maikel@ el 21/09: una con máquina, precio, ficha y comercial,
y otra solo con el nombre de pila (el caso de quien escribe sin decir qué busca).

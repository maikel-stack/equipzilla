# Plantillas Brevo · leads de COMPRA

Dos plantillas, una por cada lado de la misma solicitud:

| | Plantilla | Para quién | Equivalente en alquiler |
|---|---|---|---|
| Aviso interno | **#222** «Equipzilla - Lead de COMPRA (aviso equipo)» | David, Andrés, Maikel | #20 «Equipzilla - Lead texto plano» |
| Acuse al cliente | **#223** «Equipzilla - Compra · acuse al cliente» | quien rellena el formulario | #21 «Equipzilla Bienvenida con alquilador contactará» |

Remitente `clientes@equipzilla.com` (sender id 10) en las dos.

## Lo importante: no hay que cambiar nada en el código

Las dos plantillas están escritas **sobre los parámetros que la plataforma ya
envía hoy** a las de alquiler. Si una solicitud de compra manda el mismo objeto
que manda ahora una de alquiler, el email sale bien: basta cambiar el
`templateId`.

Parámetros que ya existen y que las plantillas usan:

| Parámetro | #222 interno | #223 cliente |
|---|---|---|
| `submissionid` | sí | sí |
| `nombreUsuario` | sí | sí (si no llega `NAME`) |
| `NAME` | — | sí (es el que usa la #21) |
| `emailUsuario` | sí | — |
| `telefonoUsuario` | sí | — |
| `profesional` | sí (como empresa) | — |
| `assetType` | sí (titular si no hay `maquina`) | sí |
| `assetUse` | sí | sí |
| `city` | sí | sí |
| `altura`, `peso`, `potencia`, `exterior` | sí | sí |

`dateStart` y `dateFinish` se ignoran a propósito: en compra no significan nada.
Si llegan, no pasa nada, simplemente no se pintan.

Todo bloque está condicionado (`{% if %}`), así que lo que venga vacío
desaparece: no quedan huecos ni etiquetas sueltas.

## Parámetros opcionales (si algún día los tiene)

Ninguno hace falta, pero cada uno mejora el email:

| Parámetro | Ejemplo | Qué añade |
|---|---|---|
| `maquina` | `Haulotte Compact 12 (2013) · tijera 12 m` | Sustituye a `assetType` como titular |
| `precio` | `9.900 €` | Precio publicado |
| `referencia` | `PL-COMPACT12-2013` | Referencia del anuncio |
| `urlMaquina` | `https://equipzilla.com/maquinaria/...` | Botón «Ver la ficha» |
| `plazo` | `Este mes` | Urgencia |
| `presupuesto` | `Hasta 12.000 €` | Solo en el interno |
| `financiacion` | `Sí, a 36 meses` | Solo en el interno |
| `entrega` | `Transporte a Paterna` | Solo en el interno |
| `mensaje` | texto libre | Solo en el interno |
| `origen` | `ficha de máquina` | Solo en el interno |
| `comercial` | `David Devis` | Quién firma y quién llamará. Sin él firma «El equipo de Equipzilla» |
| `comercialMovil` | `606836581` | Añade el WhatsApp. Sin él solo el 911 238 750 |

## Cómo se envían

```bash
# aviso al equipo
curl -X POST https://api.brevo.com/v3/smtp/email \
  -H "api-key: $BREVO_API_KEY" -H "content-type: application/json" -d '{
  "to": [{"email":"david@equipzilla.com"},{"email":"andres@equipzilla.com"},{"email":"maikel@equipzilla.com"}],
  "replyTo": {"email":"juan@montajeslevante.es","name":"Juan Pérez"},
  "templateId": 222, "tags": ["lead-compra"], "params": { ... } }'

# acuse al cliente
curl -X POST https://api.brevo.com/v3/smtp/email \
  -H "api-key: $BREVO_API_KEY" -H "content-type: application/json" -d '{
  "to": [{"email":"juan@montajeslevante.es","name":"Juan Pérez"}],
  "templateId": 223, "tags": ["compra-acuse-cliente"], "params": { ... } }'
```

En el aviso interno conviene mandar `replyTo` con el email del lead: así David
contesta dándole a «Responder» y le llega al cliente.

## Cuidado con lo que se le pasa a la #223

Ese email **lo lee el cliente**. `maquina`, `referencia` y `urlMaquina` tienen
que ser los nuestros: el título y la ficha de equipzilla.com y nuestra
referencia interna. Nunca el enlace, la referencia ni el nombre del distribuidor
de origen. Si el formulario arrastra la URL del proveedor, hay que traducirla
antes de llamar a la plantilla.

## Qué dicen (y qué no)

La #21 de alquiler promete que «estamos buscando entre nuestros alquiladores».
En compraventa eso no aplica: la #223 promete **llamada en menos de 24 horas
laborables** y adelanta qué se resuelve en ella — estado y horas reales,
garantía y financiación, transporte, y alternativas si esa máquina no encaja.

De garantía y financiación se dice «qué opciones hay en tu caso», sin plazos ni
coberturas concretas, porque ese wording sigue pendiente de cerrar. Cuando esté,
esa línea se puede concretar y gana mucho.

## Fuentes y pruebas

- HTML en este repo: `plantillas/brevo-lead-compra.html` y
  `plantillas/brevo-compra-acuse-cliente.html`. Brevo es la copia viva: si se
  tocan aquí, hay que subirlos con `PUT /v3/smtp/templates/{222|223}`.
- Pruebas enviadas a maikel@ el 21/09 con el payload exacto que la plataforma
  manda hoy en alquiler: una del aviso interno, una del acuse al cliente y una
  tercera del acuse enriquecido con máquina, precio, ficha y comercial.

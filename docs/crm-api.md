# API del CRM de ocasion.equipzilla.com

Endpoint único: `https://ocasion.equipzilla.com/api/crm`

Autenticación: cabecera `x-api-key: ezk_…` (clave permanente, no caduca) o `Authorization: Bearer <token de sesión>` (login de 180 días). La clave la reparte Maikel; nunca la pongas en el front público ni en el repo.

## Leer datos

```bash
curl -s https://ocasion.equipzilla.com/api/crm -H "x-api-key: $CRM_KEY"
curl -s "https://ocasion.equipzilla.com/api/crm?solo=stock" -H "x-api-key: $CRM_KEY"
```

Respuesta (`solo` filtra a una sola colección: `stock`, `leads` o `notas`):

| Campo | Qué es |
|---|---|
| `generado` | Fecha/hora de la última cola comercial (se recalcula cada hora) |
| `leads[]` | Cola comercial unificada: score, prioridad, canal, etapa, contacto, empresa, qué pide, qué encaja, `dealId` (Pipedrive), etc. |
| `stock[]` | Inventario de David: `id`, `ref`, `salida`, `familia`, `sub`, `titulo` (marca + modelo), `anio`, `capacidad`, `horas`, `precio` (número), `precioTxt`, `descripcion`, `notas`, `imagen` (URL), `conFoto`, `categoria` |
| `notas[]` | Anotaciones del equipo (fecha, email, quién, estado, nota) |
| `tiempos` | Tiempos medios del embudo (entrada → oferta → cierre) |
| `sesion` | Quién eres para la API (`usuario`, `nombre`, `rol`) |

Los datos se cachean 90 s en el servidor. El origen de verdad sigue siendo Pipedrive (tratos) y la hoja de stock de David (máquinas).

## Escribir

Todas las escrituras son `POST` con JSON y la misma cabecera. Quedan firmadas con el nombre del usuario o de la clave.

```bash
# Anotar en un lead (se guarda en la hoja y como nota en el trato de Pipedrive si tiene dealId)
curl -s -X POST https://ocasion.equipzilla.com/api/crm -H "x-api-key: $CRM_KEY" -H "content-type: application/json" \
  -d '{"op":"nota","email":"cliente@empresa.com","dealId":1234,"estado":"Contactado","nota":"Llamado, pide precio de la KX016"}'

# Mover un trato de etapa (ids de etapa de Pipedrive, pipeline 6: 45 Lead recibido, 33 Enviar oferta, 37 Oferta enviada, 38 Aceptada, 28 Alquilador asignado, 46 Entrega)
curl -s -X POST https://ocasion.equipzilla.com/api/crm -H "x-api-key: $CRM_KEY" -H "content-type: application/json" \
  -d '{"op":"mover","dealId":1234,"stageId":37}'

# Marcar como perdido con motivo
curl -s -X POST https://ocasion.equipzilla.com/api/crm -H "x-api-key: $CRM_KEY" -H "content-type: application/json" \
  -d '{"op":"perder","dealId":1234,"razon":"Precio"}'
```

## Usos típicos para la web

- Página de stock: `?solo=stock` para pintar fichas con foto, precio y referencia (sin exponer la clave: llamar desde el servidor o desde una función propia, no desde el navegador).
- Formularios: cuando entre un lead, seguir creando el trato en Pipedrive como hasta ahora; la cola lo recoge sola en la siguiente pasada horaria.
- Enviar Gclid/UTM al crear el trato en Pipedrive (campos «Gclid» y «Utm») para que Ads reciba las conversiones offline.

## Errores

`401` clave o sesión inválida · `400` faltan campos u operación desconocida · `500` error aguas arriba (Pipedrive/Sheets), el mensaje viene en `error`.

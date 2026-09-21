# Informe del piloto comercial · fase 1 (10-21 sep 2026)

Entrega de negocio a tecnología, según el apartado 6 del contrato
(`01-arquitectura-piloto.md`). Lo escribe el agente CRM / Datos. Todas las
cifras salen de Pipedrive y de la hoja de stock de David, medidas entre el 10 y
el 21 de septiembre de 2026.

Destinatario: Lorenzo. Copia: Maikel, Andrés.

---

## 1. Resumen

El piloto ha validado que se puede operar sobre Pipedrive sin crear ninguna
fuente de verdad nueva. No se ha creado ninguna base de datos, ninguna hoja de
cálculo con datos propios y ningún campo en Pipedrive. Todo lo que el piloto
produce son vistas derivadas que se borran y se regeneran.

Lo que no funciona no es la arquitectura: es la calidad del dato de entrada. La
mitad de los leads no dice qué máquina quiere y tres de cada cuatro tratos no
tienen importe, así que las métricas de valor no son fiables por mucho que la
integración esté bien hecha.

## 2. Entidades y campos realmente usados

Medido sobre los 267 tratos creados en los últimos 30 días en los pipelines 6
y 16.

| campo | relleno | veredicto |
|---|---|---|
| Gclid | 80 % | se usa, es el mejor dato de origen disponible |
| Utm | 80 % | se usa |
| assetType | 47 % | insuficiente: la mitad de los leads no dice qué quiere |
| Razón Social | 46 % | se usa |
| profesional | 45 % | se usa |
| assetUse | 32 % | texto libre, no se puede consultar ni agregar |
| Importe del trato | 23 % | insuficiente para cualquier métrica de valor |
| Etiqueta (VENTA / RENTING) | 0,4 % | el campo existe y está vacío |
| Precio maximo | 0 % | **nadie lo rellena: proponemos retirarlo del modelo** |

Entidades que toca el piloto: tratos (incluido el historial de etapas),
personas, organizaciones, etapas, definición de campos, actividades y notas.

Campos derivados que se recalculan y **no** se persisten, según lo acordado:
score, prioridad, canal de entrada, tipo de empresa, días hasta oferta y «qué
tenemos que encaja».

## 3. Aviso técnico importante para cualquier integración con Pipedrive

**La API v1 tiene un límite de paginación no documentado.** Con
`status=all_not_deleted`, a partir de unos 6.000 registros ignora el parámetro
`start` y devuelve indefinidamente la misma página, con la bandera
«hay más elementos» siempre activa.

Consecuencias comprobadas el 16/09:

- un recorrido normal no termina nunca;
- devuelve 20.500 filas para 6.000 tratos reales, con hasta 30 repeticiones del
  mismo identificador;
- cualquier conteo histórico hecho así está inflado.

Añadir un criterio de ordenación **no** lo corrige: el comportamiento es
idéntico con y sin orden. Lo que sí funciona:

- paginar filtrando por un estado concreto (`open`, `lost`, `won`) y
  deduplicar por identificador, que es lo que hace ahora el piloto; o
- usar la API v2, que pagina por cursor y no tiene el problema.

Si tecnología va a leer Pipedrive de forma masiva, conviene ir directamente a
la v2.

## 4. Procesos que han funcionado, con cifras

| proceso | estado | evidencia |
|---|---|---|
| Aviso de stock nuevo cruzado con leads | funciona | se ejecuta a diario desde el 10/09 |
| Cola comercial única | funciona | 76 oportunidades, regenerada a diario |
| Tiempo a primer contacto | funciona | mediana por debajo de 1 h en los leads con rastro |
| Demanda sin stock | funciona | 8 de 16 tratos de compra no se pueden servir hoy |
| Integridad diaria con identificadores | funciona | ningún trato sin propietario, ningún perdido sin motivo |
| Conversión de oferta a venta | **no funciona** | 0 ventas de compraventa en 2026 sobre 106 tratos |

## 5. Lo que debería persistirse y hoy solo se calcula

Por orden de valor:

1. **Canal de entrada.** Gclid y Utm están al 80 %, pero hay que derivar el
   canal en cada consulta. Es el candidato más claro a campo del modelo.
2. **Compra o alquiler como dato, no como texto del título.** Hoy se distingue
   leyendo el título, que acierta el 98,7 % y falla en los tratos escritos a
   mano. La etiqueta VENTA/RENTING ya existe en Pipedrive y está vacía: basta
   con que el formulario la rellene en el alta.
3. **Referencia de la máquina ofertada**, ligada al futuro endpoint de stock.
   Hoy es texto libre y se casa por modelo, año y precio.
4. **Motivo de pérdida útil.** Existe y se rellena siempre, pero «OTRAS ·
   General» es el más usado en compraventa y no explica nada.

## 6. Problemas de calidad de dato que nacen en el formulario web

Los cuatro casos son de la segunda semana del piloto y ninguno lo detectó el
sistema: los encontró el agente al revisar los datos.

1. **El formulario guarda emails nuestros como email del cliente.** Tres casos:
   un lead con `clientes@equipzilla.com` y dos tratos de prueba con
   `fernando@equipzilla.com`. El primero llegó a la lista de llamadas del
   equipo comercial con nuestra propia dirección como contacto del cliente.
2. **No se valida el dominio del email.** Un lead de 32.000 € entró con
   `…@gmai.com`, que no es un error que rebote: es un dominio real que acepta
   correo y entrega a un tercero. Cualquier oferta enviada ahí se pierde sin
   aviso.
3. **Doble envío del formulario.** Cuatro pares de tratos duplicados en una
   semana, creados con uno o dos minutos de diferencia.
4. **Las pruebas del formulario llegan a producción.** Dos tratos de prueba
   contaron como leads del mes hasta que se cerraron el 21/09.

Los cuatro se resuelven en el formulario, no en el CRM.

## 7. Qué merece convertirse en producto y qué se descarta

**Merece:** la cola comercial única con score explicable, el cruce de demanda
contra stock, y la alerta de tiempo a primer contacto. Son las tres cosas que
el equipo comercial usa a diario.

**Se descarta:** el campo «Precio maximo», que nadie rellena. Y hay que decidir
sobre el **pipeline 16 «Compraventa», que está vacío**: o se usa o se retira,
porque hoy obliga a todos los scripts a consultar dos pipelines para nada.

## 8. Peticiones a tecnología

Sin cambios respecto al contrato, por orden:

1. Que el formulario web rellene la etiqueta VENTA/RENTING en el alta.
2. Validación de email en el formulario y bloqueo del doble envío.
3. Endpoint de lectura del stock real, para retirar la hoja de David.
4. Confirmar si el envío de gclid y utm desde los formularios es completo: hoy
   llega al 80 % y no sabemos si el 20 % restante es tráfico sin gclid o una
   pérdida.
5. Revisión y visto bueno de la tabla de campos de este informe, incluido el
   alta de «Precio maximo» como campo a retirar.

## 9. Lo que el piloto NO ha podido validar

- **Si el modelo aguanta una venta cerrada de principio a fin**, porque no ha
  habido ninguna en 2026.
- **El perfil de cliente ideal**, porque sector y tamaño están vacíos en las
  2.313 fichas de empresa y la provincia falta en 314 de 330.
- **La atribución completa de canal**, porque las conversiones de Google Ads no
  se pueden casar con los tratos hasta que el gclid llegue siempre.

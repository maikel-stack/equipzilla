# LinkedIn (HeyReach) · estado y todo lo que está listo para arrancar

**Estado a 16/09/2026, 20:15: clave conectada y lista cargada. Queda un interruptor.**

Maikel pasó la clave el 16/09 (la segunda de las dos que mandó; la primera daba 401).
Guardada en `~/.outbound/heyreach_key` con permisos 600, nunca en el repo.

| | |
|---|---|
| API de HeyReach | conectada y verificada |
| Cuenta de LinkedIn de Andrés (id 249406) | **INACTIVA**, con sesión válida y Sales Navigator |
| Lista «Demanda · decisores maquinaria» (939535) | **40 perfiles cargados** de 35 empresas |
| Campaña | ninguna lista para enviar; hay 5 borradores vacíos que limpiar |
| Invitaciones y mensajes enviados en toda la historia | 0 |

### El único bloqueo que queda

**La cuenta de Andrés está en inactiva dentro de HeyReach.** No es un fallo: su sesión de
LinkedIn es válida y tiene Sales Navigator. Es un interruptor. He probado a activarla por
API (`Activate`, `SetActive`, `Update`) y esos endpoints no existen en la API pública, así
que hay que hacerlo desde la interfaz de HeyReach. Sin eso no sale ni una invitación.

### Y lo segundo: la secuencia hay que escribirla en la interfaz

Corrijo lo que decía la ficha: **las campañas SÍ se crean por API** (`/campaign/Create`, con
`name`, `LinkedInAccountIds` y `linkedInUserListId`). Lo que no se puede por API es
**escribir los mensajes**: el endpoint `/campaign/UpdateSequence` existe pero su formato no
está documentado y devuelve error 500 con todas las variantes razonables. No voy a seguir
adivinando el esquema: una secuencia mal formada saldría hacia personas reales desde la
cuenta de Andrés.

Lo que hay que hacer en la interfaz, con los textos de más abajo:
1. Comprobar que la cuenta de Andrés queda activa (la API la sigue dando como inactiva).
2. Crear la campaña sobre la lista **939535**, que ya tiene los 40 perfiles.
3. Pegar los 3 pasos del sector y poner el límite en 20 invitaciones al día.
4. **Limpiar 5 campañas en borrador y vacías**: `__probe__` (602761) y cuatro `__schema__`
   (605027, 605028, 605029, 605030) que dejé al descubrir el esquema de creación. La API
   pública no permite borrarlas. Ninguna ha enviado nada.
5. La lista **935047** es de pruebas y tiene al propio Andrés dentro como lead. No usarla.

## Lo que ya está hecho y esperando

### Lista 1 · reforzar lo que ya está caliente (prioridad)

Son empresas que ya nos han contestado o tienen oferta parada. En LinkedIn no se les vende:
se les pone cara antes de que David llame. Salen de Pipedrive y de las campañas de frío:

- Los 7 interesados del frío de septiembre, incluidos los 4 ya marcados como perdidos.
  A un perdido por silencio, una invitación de LinkedIn le reabre la puerta sin insistir por email.
- Las 13 ofertas de compraventa paradas en «Oferta enviada», 250.600 € en juego.
- Los clickers de las campañas de Brevo que nunca contestaron.

### Lista 2 · sectores que compran, los mismos del email

Ya tengo las empresas identificadas y con email de las tres campañas de frío activas:

| sector | empresas | campaña de email |
|---|---|---|
| Obra: movimiento de tierras, pavimentos, canalizaciones | 85 | 3962539 |
| Logística e industria: almacén, transporte, mudanzas | 110 | 3962541 |
| Eólica y fotovoltaica: instaladoras, EPC, mantenimiento | 31 | 3966809 |

De esas empresas hay que sacar los perfiles de decisor. **El pozo es grande**: con los
cargos y sectores de abajo, Apollo devuelve 12.512 personas en España.

### Criterios exactos de búsqueda (validados contra Apollo el 16/09)

- **Cargos**: jefe de maquinaria · responsable de maquinaria · responsable de compras ·
  director de operaciones · jefe de obra · director técnico · jefe de parque ·
  construction manager · purchasing manager.
- **Antigüedad**: manager, director, propietario, dirección general.
- **Sectores**: construcción, obra civil, energía solar, energía eólica, logística.
- **Tamaño**: de 11 a 500 empleados. Por debajo no hay presupuesto; por encima, la compra
  está centralizada y tarda.
- **Zona**: España.

**Resuelto el 16/09**: la URL del perfil sí se saca de Apollo, con el enriquecimiento por
lotes de diez. Cuesta **1 crédito por persona**. Gastados 40 de los 3.960 disponibles. A ese precio, llenar la lista para un trimestre entero
cuesta menos del 10 % del saldo. Alternativa sin coste: montar la búsqueda en Sales
Navigator con los criterios de arriba e importarla desde HeyReach.

### Los 40 perfiles ya cargados (lista 939535)

Responsables de maquinaria, de compras, jefes de obra y directores de operaciones de 35
empresas:

- **Obra y demolición**: AGUADO, GRUPOPARRA, ASCH Infraestructuras, Lezama Demoliciones,
  Construplan, dMol Demoliciones, Taboada y Ramos, Calaf Trenching, Group IGE, Grupo MR,
  DYD Industrial, Syneox Rail.
- **Solar y eólica**: Grupo Solaer, Diverxia, POWEN, Vico Export, Heliosolar, EFV Solar,
  Enerland, Iver Spain, Solar World Stain, IMENERGY, Plenitude España.
- **Logística e industria**: Bergé y Compañía, Pantany Logistics, Eurocontainer, Ecrimesa,
  STRUGAL, Grupo Novelec, COTO, Naeco, Hoyamar, Canalink, Grupo Arrate.

## Secuencia de 3 pasos · solo demanda

Regla de Maikel del 14/09: vendemos máquina concreta con precio cerrado a quien la compra.
Nunca «compramos tu máquina». Sin plazos de garantía ni de financiación mientras Maikel no
confirme las dos frases (pendiente desde el 16/09).

**Límite: 20 invitaciones al día.** Más que eso es como LinkedIn restringe cuentas.

### A) Obra

1. **Invitación** (sin pitch): «Hola {nombre}, veo que lleváis la maquinaria en {empresa}. Yo me dedico a la compraventa de máquina de ocasión revisada. Te agrego por si algún día te encaja.»
2. **Mensaje 1** (al aceptar): «Gracias por aceptar, {nombre}. Por si os sirve: tengo una Kubota KX 030-4 GL de 3 t, de 2023 con 700 h, en 35.900 € + IVA, con inspección y prueba presencial y horas certificadas. Si buscáis otro tamaño, tengo de 0,8 a 23 t. ¿Os encaja algo ahora?»
3. **Mensaje 2** (día +4): «No quiero insistir. Si te viene bien, te aviso solo cuando entre una máquina que encaje con lo vuestro, tipo y presupuesto. ¿Te apunto? Con un sí me vale.»

### B) Logística e industria

1. **Invitación**: «Hola {nombre}, veo que lleváis almacén y flota en {empresa}. Me dedico a la compraventa de carretillas y máquina de ocasión revisada. Te agrego por si te encaja.»
2. **Mensaje 1**: «Gracias por aceptar, {nombre}. Tengo una Clark EPX25 eléctrica de 2,5 t, de 2011 con 801 h, en 7.000 € + IVA, con inspección y prueba presencial. También retráctil, GLP y diésel. ¿Estáis renovando algo este año?»
3. **Mensaje 2** (día +4): «Te aviso solo cuando entre una carretilla que encaje con lo vuestro, tonelaje y presupuesto, sin más mensajes. ¿Te apunto?»

### C) Eólica y fotovoltaica

1. **Invitación**: «Hola {nombre}, veo que montáis y mantenéis parques en {empresa}. Me dedico a la compraventa de plataformas y telescópicos de ocasión revisados. Te agrego por si te encaja.»
2. **Mensaje 1**: «Gracias por aceptar, {nombre}. Lo que casi nadie tiene en ocasión son unidades iguales en cantidad: seis Haulotte Compact 12 de 2012 a 6.100 € + IVA cada una, y tres Genie GS-3246 de 2016 a 7.500 € + IVA. Con eso equipáis a un equipo de montaje entero. ¿Os cuadra para la campaña que viene?»
3. **Mensaje 2** (día +4): «Si ahora no toca, te aviso solo cuando entre una plataforma o un telescópico que encaje, altura y presupuesto. ¿Te apunto?»

## Qué mediré cuando esté en marcha

Las mismas dos cifras que en email, separadas por canal en el parte diario: aceptación de
invitación y respuestas, y sobre todo interesados que acaban con trato en Pipedrive con el
canal «LinkedIn». Los envíos no cuentan.

# Equipzilla · Base de conocimiento

**Documento madre.** Todo lo que comunica Equipzilla — campañas, chatbot,
outbound, SEO, llamadas, agentes de IA — se alimenta de este documento. Si
algo de aquí cambia, cambia en todas partes. Si un texto contradice esto,
manda esto.

Versión en el repo: `docs/BASE-CONOCIMIENTO.md` (fuente de verdad).
Copia en Notion para el equipo.

---

## 1 · Qué es Equipzilla

Plataforma española de **maquinaria industrial y de obra**: alquiler,
compraventa de ocasión y venta de unidades nuevas de obra modular. B2B:
constructoras, empresas de movimiento de tierras, demolición, obra civil,
industria y profesionales.

**La ventaja competitiva no es el stock ni el precio: es el dato de
demanda.** Cientos de empresas al mes nos dicen qué máquina necesitan y
dónde. Compramos y ofertamos guiados por esa demanda.

## 2 · La propuesta de compraventa

### Qué vendemos
Maquinaria de ocasión **revisada** y unidades nuevas de obra modular, con
el precio publicado. Catálogo canónico: `data/machines.json` en el repo —
**única fuente de precios y datos de máquina**. Nada se anuncia con datos
que no estén ahí.

### Cómo trabajamos (promesas al cliente — usar tal cual en el copy)
- **El precio que ves es el precio.** Sin escalados ni «consulte
  disponibilidad».
- **Inspección y prueba presencial** antes de comprar, con horas reales.
- **Fotos reales de la unidad concreta** antes de cerrar nada.
- **Plazo y coste de transporte confirmados antes de que decidas.**
- **Opción de garantía** en máquinas de ocasión.
- Si necesitas varias unidades o una configuración distinta, se cotiza.
- Si prefieres alquilar en vez de comprar, también lo montamos.

### Condiciones de precio
- Precios **sin IVA y sin transporte** salvo que se indique lo contrario.
- Precio tachado («antes») **solo si es un precio realmente aplicado
  antes** — por ley, el más bajo de los 30 días previos. Nunca inventar
  un "antes".
- El ahorro frente a máquina nueva de ocasión revisada: 30–40 % (rango
  orientativo usado en frío).

## 3 · Servicios (aparte de la venta)

| Servicio | Qué es | Estado |
|---|---|---|
| **Alquiler** | Intermediación con red de alquiladores en toda España. Es el negocio original y el mayor volumen de entrada (~310 peticiones/mes). | Activo |
| **Compra de tu máquina · Tasación express** | Formulario «¿cuánto vale tu máquina?» — captamos vendedores, que son el stock. | Activo (guias/vender-maquinaria-usada) |
| **Renting** | Pipeline propio en CRM. | Activo |
| **Financiación** | Opciones de financiación de la compra. Guía publicada. | Activo |
| **Garantía** | Opción de garantía en ocasión. Guía publicada. | Activo |
| **Alertas de precio** | Alta con un clic desde cualquier email; avisamos cuando baja o entra máquina de su categoría. | Activo |
| **Asesor de compra con IA** | Quiz (1 min), chatbot 24/7 y calculadora alquilar-vs-comprar. Todo lead cae solo en CRM y avisa al equipo. | Activo |
| **Obra modular nueva** | Contenedores marítimos, casetas/módulos y aseos, nuevos con precio cerrado. | Nuevo (ago 2026) |
| **Venta a alquiladores** | Suministro a empresas de alquiler (vallas, casetas, módulos). | Activo, sin sistematizar |

### El ángulo alquiler-vs-compra
La mayoría de nuestra base pidió **alquiler**. El mensaje que convierte no
es «te vendo», es: *«si la obra se alarga, llega un mes en el que el
alquiler pasa a costar más que la unidad — echa el número antes de firmar
la próxima renovación»*, con enlace a la calculadora.

## 4 · El ICP de compraventa

Construido con dato propio: las 131 peticiones de compra de los últimos 12
meses, los clics por máquina de las campañas y las respuestas reales del
frío. Se revisa cada trimestre con las operaciones cerradas.

### El comprador núcleo (ICP-A) — la pyme que usa la máquina a diario

- **Quién:** empresas de movimiento de tierras, excavaciones, demolición,
  obra civil y construcción con parque propio. Típicamente **2-50
  empleados**, muchas familiares, decisor = dueño.
- **Qué compra:** la máquina con la que trabaja cada día. Tickets de
  **10.000-60.000 €**: mixtas, mini y midi excavadoras, minicargadoras,
  plataformas, telescópicas.
- **Cómo decide:** rápido y por teléfono/WhatsApp. Sabe exactamente lo que
  quiere — *"mixta 30-40 mil, mínimo 3 cazos y martillo, mejor pala de
  almeja"* (respuesta real de un lead). La ficha técnica no le convence:
  le convencen las horas reales, poder verla y probarla, y un precio sin
  sorpresas.
- **Su alternativa:** portales de anuncios (llamar a 10 vendedores) o el
  concesionario local (más caro). Nuestra cuña: precio cerrado + inspección
  + acompañamiento.
- **Cargo al que hablar:** gerente/propietario. En las de 20-50 empleados,
  responsable de maquinaria o jefe de obra.

### ICP-B — industria y logística con flota propia

- **Quién:** fábricas, almacenes, agroindustria, operadores logísticos que
  poseen (no alquilan) sus carretillas y manutención. La mejor apertura de
  todo el ABM (24,1%) fue la campaña de carretillas.
- **Qué compra:** carretillas diésel/eléctricas, transpaletas, apiladores.
  Tickets 6.000-20.000 €. Recurrente: renuevan unidades sueltas cada año.
- **Cargo:** responsable de logística/almacén, compras, gerencia.

### ICP-C — obra que necesita instalación, no máquina

- **Quién:** constructoras e instaladoras que montan obra: casetas,
  aseos, contenedores, generadores. El **25,9% de toda la demanda** entra
  por aquí y suele empezar pidiendo *alquiler* — el ángulo que convierte es
  alquiler-vs-compra.
- **Qué compra:** obra modular nueva (3.000-7.400 €) y generadores. Ticket
  bajo, ciclo corto, decisión casi impulsiva si el precio está delante.
- **Incluye autónomos y profesionales** (muchos leads reales llegan desde
  gmail): válidos si el uso es profesional.

### ICP-D — alquiladores que compran para su flota

- **Quién:** empresas de alquiler pequeñas y medianas que amplían o
  renuevan flota (ya les vendemos vallas y casetas: AXOR, GAM). Compran
  varias unidades de golpe y repiten.
- **Trato distinto:** precio de volumen, relación directa de David, nunca
  campañas masivas.

### Señales de compra (ordenadas por fuerza)

1. **Responde al frío o al templado describiendo máquina y presupuesto**
2. Pide compra directa en la web («Solicitud de Consulta Por Compra»)
3. Clica una máquina concreta en una campaña (la Manitou: 15 clics)
4. Pide alquiler de larga duración o con opción de compra
5. Usa la calculadora alquilar-vs-comprar o se da de alta en alertas
6. Pidió alquiler de una categoría en los últimos 12 meses (base de 3.112)

### Fuera del ICP (no gastar ni un euro)

Ingenierías, consultoras, BIM, arquitectura, project management,
promotoras/inmobiliarias puras, reformas de interior, topografía,
gestorías. *Aparecen bajo "construcción" en cualquier base de datos y no
compran excavadoras.* El filtro está codificado en `scripts/captar_leads.py`.

### Matices geográficos

España entera (la demanda real llega de las 50 provincias) **y Portugal**:
en las campañas han clicado y comprado interés desde Portugal (West Sea,
BRW) sin haberlo buscado. No se descarta un lead portugués; no se invierte
en captarlos aún.

## 5 · Identidad, contacto y firma

- **Firma comercial de todo lo que sale:** David Devis · Director de
  Desarrollo de Negocio · **606 836 581** (llamada o WhatsApp).
- **Email de clientes (único):** clientes@equipzilla.com — remitente y
  dirección de respuesta de todo. El buzón antiguo de corporatelab NO se
  usa.
- Teléfono fijo de apoyo (chatbot): 911 238 750.
- Equipo: Maikel (growth) · Andrés · David (comercial).
- Tono: directo, de tú, sin jerga de marketing, números concretos, frases
  cortas. Somos gente de maquinaria, no un SaaS.

## 6 · Reglas duras (no se negocian)

1. **Nunca** mencionar proveedores ni marcas de alquilador (GAM, LOXAM,
   etc.) en nada que pueda ver un cliente: ni texto, ni fotos (retocar o
   sustituir), ni URLs.
2. **Nunca** inventar datos de máquina: horas, año, estado. Si no está en
   `data/machines.json`, no se afirma. (Ej.: la Manitou 170 AETJL no
   publica horas — horómetro sustituido.)
3. **Toda recomendación de IA lleva disclaimer:** «recomendaciones
   estimadas — las confirma un asesor».
4. **Ninguna campaña generalista.** Siempre segmentada por la categoría
   que esa persona pidió. (Dato: 24,1 % de apertura segmentada vs 11,7 %
   generalista.)
5. **Ningún envío sin OK humano.** Los agentes preparan; el equipo aprueba.
6. Configuración fija de campaña Brevo: remitente id 10
   (clientes@equipzilla.com), `replyTo` explícito a clientes@, y lista 34
   (copia al equipo) siempre incluida.
7. Frío siempre desde dominios secundarios (equipzillaform/equipzillafield),
   nunca desde equipzilla.com, con tope 30–40 correos/día por buzón.
8. Contacto que ya está en Pipedrive → se le habla por Brevo (templado),
   nunca por frío.
9. Datos personales de leads: en `leads/` (gitignored) o en herramientas —
   **nunca al repositorio público**.
10. **SLA de respuesta: menos de 15 minutos** para toda petición de compra
    entrante, con precio orientativo y siguiente paso.

## 7 · Máquina de captación (qué existe y dónde)

| Pieza | Dónde |
|---|---|
| Catálogo canónico | `data/machines.json` (repo) |
| Web de captación: quiz, chatbot, calculadora, guías, tasación | equipzilla-quiz.vercel.app |
| Dashboard de métricas en vivo | /dashboard.html (Brevo + Smartlead) |
| CRM | Pipedrive · pipeline Transaccional (6) · entrada «Lead - Recibido» (45) |
| Email templado | Brevo · listas segmentadas por categoría (35-43) |
| Frío | Smartlead · 10 buzones calentados |
| WhatsApp saliente | respond.io |
| Hoja de llamadas priorizada | Google Sheet compartida con David y Andrés |
| Planning de ejecución | Notion + `plan/planning.json` (repo) |
| Playbooks operativos | `docs/PLAYBOOK-*.md` (repo) |

## 8 · Los números que mandan (actualización 28/08/2026)

- Peticiones de **compra**: 131/año (~11/mes), creciendo +36 % trimestral.
- Base propia contactable: **3.112 empresas** con email y teléfono,
  segmentadas por categoría; 530 contactadas.
- Demanda de compra por categoría: plataformas 33,6 % · casetas/aseos
  17,6 % · excavadoras 9,9 % · carretillas 9,2 %.
- Métrica reina: **operaciones cerradas y margen por operación** — no
  leads. Todo deal cerrado registra importe, coste, categoría y canal.

*(Los números vivos salen del parte diario de las 8:30 y del dashboard;
este apartado se actualiza cuando cambian de orden de magnitud.)*

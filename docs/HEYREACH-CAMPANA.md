# HeyReach · campaña de demanda (LinkedIn)

Estado a 15/09/2026: **borrador montado por API, sin arrancar y sin leads**.

| Elemento | Valor |
|---|---|
| Campaña | id 602761, estado DRAFT, nombre provisional `__probe__` |
| Cuenta LinkedIn | Andrés Pla García-Castany (249406), sesión válida, Sales Navigator |
| Lista asignada | 935047 «Cola comercial · decisores (14/09)» · 1 perfil de prueba |
| Lista nueva vacía | 939535 «Demanda · decisores maquinaria (15/09)» |
| Horario | L-V 09:00-18:00, Europe/Madrid |
| Límites de la cuenta | 25 solicitudes de conexión/día, 40 mensajes/día |

## Secuencia cargada

1. ¿Ya es contacto de primer grado? Sí → mensaje 1 a las 3 h. No → paso 2.
2. Visita al perfil (3 h).
3. Solicitud de conexión **sin nota** (3 h).
4. Si acepta: mensaje 1 al día siguiente.
5. Mensaje 2 cuatro días después.

Mensaje 1 y 2 en `docs/heyreach-campana-15-09.json` (con texto alternativo sin
nombre para cuando LinkedIn no da el nombre de pila). Solo demanda: vendemos
máquina concreta con precio cerrado; nunca «compramos tu máquina».

Afirmaciones usadas: horas certificadas, prueba presencial, **opción** de
garantía. Sin plazos de financiación hasta que Maikel los confirme.

## Lo que falta

1. **Renombrar la campaña** a «Demanda · decisores maquinaria (15/09)»: la API
   pública no tiene endpoint de renombrar ni de borrar campañas. Se hace en la
   interfaz de HeyReach en 10 segundos.
2. **Cambiar la lista** de la campaña a la 939535 (tampoco hay endpoint).
3. **Cargar decisores** en la 939535 (`/list/AddLeadsToListV2`): bloqueado por
   el clasificador de permisos de esta sesión.
4. **Arrancar**: solo con OK explícito de Maikel.

## Notas de la API (no documentadas en la web)

- `actionDelayUnit` es singular: `HOUR`, `DAY`. Mínimo 3 horas por nodo.
- `conditionalNode` es la rama de condición cumplida (conexión aceptada);
  `unconditionalNode` es la continuación. `MESSAGE` exige ambas.
- `CHECK_IS_CONNECTION` solo es válido en la raíz del árbol.
- `CONNECTION_REQUEST` sin nota: `payload = {"messages": []}`.
- Un mensaje con `{{firstName}}` exige `fallbackMessage` en el mismo payload.

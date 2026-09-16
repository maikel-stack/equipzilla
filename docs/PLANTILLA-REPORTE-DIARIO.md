# Plantilla del parte diario (formato pedido por Maikel, 16/09/2026)

Así quiere Maikel que le llegue la información cada día: primero lo que necesita su OK,
después los leads con puntuación, y los números al final. Sustituye al formato largo en el
chat; el fichero de `reportes/outbound/<fecha>.md` se guarda con esta misma estructura.

Reglas de la plantilla:

- **Lo que necesita tu OK va arriba y es una sola cosa**, o dos como mucho. Si hay más, es
  que el día anterior no se decidió nada. Se cita literal lo que dijo el cliente y se
  adjunta el borrador de respuesta listo para copiar.
- **Nada de adjetivos en las tablas.** «Qué dijo» es lo que dijo, entre comillas si cabe.
- **Score con la regla de `scripts/informe_respuestas.py`**, no a ojo: +50 responder al frío,
  +40 clic en una máquina, +10 por clic extra, +20 historial en Pipedrive, +10 si hay
  teléfono, +20 si la respuesta trae presupuesto o teléfono. Máximo 100. HOT desde 60.
- **La columna «Contestado» dice sí o NO**, sin matices. Un «se le mandó un WhatsApp» que no
  está registrado en Pipedrive es un NO.
- **Los leads antiguos que siguen vivos no se caen de la lista** hasta que se cierran o se
  contestan. Los días que llevan esperando salen siempre.
- **Abajo, la cifra que manda.** Para Equipzilla es operaciones y GMV, no envíos.

---

## Estructura

```
Equipzilla · Outbound · <día> <fecha>
Abrir Smartlead · Abrir el pipeline 6 de Pipedrive

🎯 Lo que necesita tu ok
<Quién> respondió <cuándo>:
«<cita literal>»
<Una línea de contexto: por qué importa.>
Mi borrador / mi propuesta:
<texto listo para copiar, o la decisión concreta que hay que tomar>

🆕 Respuestas nuevas
Score · Quién · Qué dijo · Estado

📁 Interesados que siguen vivos
Score · Quién · Qué pasó · Días · Contestado

📊 Números
Envíos hoy / acumulado · respuestas y % · rebotes y % · leads sin empezar
Operaciones y GMV del mes contra objetivo
```

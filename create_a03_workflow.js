const https = require('https');
const http = require('http');

const N8N_API_KEY = process.env.N8N_API_KEY;
const N8N_BASE_URL = process.env.N8N_BASE_URL;

if (!N8N_API_KEY || !N8N_BASE_URL) {
  console.error('❌ Faltan variables de entorno: N8N_API_KEY y N8N_BASE_URL');
  process.exit(1);
}

// ─── HTTP HELPER ────────────────────────────────────────────────────────────
function apiRequest(method, path, body = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(N8N_BASE_URL + '/api/v1' + path);
    const lib = url.protocol === 'https:' ? https : http;
    const payload = body ? JSON.stringify(body) : null;

    const options = {
      hostname: url.hostname,
      port: url.port || (url.protocol === 'https:' ? 443 : 80),
      path: url.pathname + url.search,
      method,
      headers: {
        'X-N8N-API-KEY': N8N_API_KEY,
        'Content-Type': 'application/json',
        ...(payload ? { 'Content-Length': Buffer.byteLength(payload) } : {}),
      },
    };

    const req = lib.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          if (res.statusCode >= 400) {
            reject(new Error(`HTTP ${res.statusCode}: ${JSON.stringify(parsed)}`));
          } else {
            resolve(parsed);
          }
        } catch (e) {
          reject(new Error(`Parse error: ${data}`));
        }
      });
    });

    req.on('error', reject);
    if (payload) req.write(payload);
    req.end();
  });
}

// ─── WORKFLOW DEFINITION ────────────────────────────────────────────────────
const workflow = {
  name: "A03 · Lead Qualifier Bot · Equipzilla",
  active: false,
  nodes: [

    // ── NODO 1: Webhook WhatsApp ───────────────────────────────────────────
    {
      id: "node-webhook",
      name: "WhatsApp Webhook",
      type: "n8n-nodes-base.webhook",
      typeVersion: 2,
      position: [240, 300],
      parameters: {
        httpMethod: "POST",
        path: "whatsapp-lead",
        responseMode: "responseNode",
        options: {}
      }
    },

    // ── NODO 2: Extraer datos del mensaje ─────────────────────────────────
    {
      id: "node-extract",
      name: "Extraer datos mensaje",
      type: "n8n-nodes-base.code",
      typeVersion: 2,
      position: [460, 300],
      parameters: {
        language: "javaScript",
        jsCode: `const body = $input.first().json.body;
const entry = body.entry?.[0];
const value = entry?.changes?.[0]?.value;
const message = value?.messages?.[0];

// Verificación webhook de Meta (GET)
if ($input.first().json.query?.['hub.challenge']) {
  return [{ json: {
    isVerification: true,
    challenge: $input.first().json.query['hub.challenge']
  }}];
}

if (!message) throw new Error("No message found in webhook payload");

const phone = message.from;
const messageText = message.text?.body || "";
const messageId = message.id;
const name = value?.contacts?.[0]?.profile?.name || "Lead";

return [{ json: {
  isVerification: false,
  phone,
  name,
  messageText,
  messageId,
  conversationId: \`conv_\${phone}\`,
  timestamp: message.timestamp
} }];`
      }
    },

    // ── NODO 3: ¿Es verificación? ─────────────────────────────────────────
    {
      id: "node-switch-verify",
      name: "¿Verificación o mensaje?",
      type: "n8n-nodes-base.switch",
      typeVersion: 3,
      position: [680, 300],
      parameters: {
        mode: "rules",
        rules: {
          values: [
            {
              conditions: {
                options: { caseSensitive: true, leftValue: "", typeValidation: "strict" },
                conditions: [{ leftValue: "={{ $json.isVerification }}", rightValue: true, operator: { type: "boolean", operation: "equals" } }],
                combinator: "and"
              },
              renameOutput: true,
              outputKey: "verificacion"
            }
          ]
        },
        fallbackOutput: "extra"
      }
    },

    // ── NODO 4: Responder verificación Meta ───────────────────────────────
    {
      id: "node-verify-response",
      name: "Responder verificación Meta",
      type: "n8n-nodes-base.respondToWebhook",
      typeVersion: 1,
      position: [900, 160],
      parameters: {
        respondWith: "text",
        responseBody: "={{ $json.challenge }}",
        options: { responseCode: 200 }
      }
    },

    // ── NODO 5: Recuperar historial ───────────────────────────────────────
    {
      id: "node-history",
      name: "Recuperar historial",
      type: "n8n-nodes-base.code",
      typeVersion: 2,
      position: [900, 380],
      parameters: {
        language: "javaScript",
        jsCode: `const conversationId = $input.first().json.conversationId;
const allData = $getWorkflowStaticData("global");

let history = allData[conversationId] || {
  conversationId,
  phone: $input.first().json.phone,
  name: $input.first().json.name,
  status: "IN_PROGRESS",
  turnsCount: 0,
  startedAt: new Date().toISOString(),
  messages: []
};

// Añadir mensaje del usuario
history.messages.push({
  role: "user",
  content: $input.first().json.messageText
});
history.turnsCount++;
history.lastMessageAt = new Date().toISOString();

// Forzar cierre si supera 12 turnos
if (history.turnsCount > 12) {
  history.status = "MAX_TURNS_REACHED";
}

// Guardar historial actualizado
allData[conversationId] = history;

return [{ json: { ...history, inputData: $input.first().json } }];`
      }
    },

    // ── NODO 6: Llamada a Claude API ──────────────────────────────────────
    {
      id: "node-claude",
      name: "Llamada a Claude API",
      type: "n8n-nodes-base.httpRequest",
      typeVersion: 4.2,
      position: [1120, 380],
      parameters: {
        method: "POST",
        url: "https://api.anthropic.com/v1/messages",
        sendHeaders: true,
        headerParameters: {
          parameters: [
            { name: "anthropic-version", value: "2023-06-01" },
            { name: "x-api-key", value: "={{ $env.ANTHROPIC_API_KEY }}" },
            { name: "content-type", value: "application/json" }
          ]
        },
        sendBody: true,
        specifyBody: "json",
        jsonBody: `={
  "model": "claude-sonnet-4-20250514",
  "max_tokens": 800,
  "temperature": 0.3,
  "system": "Eres el asistente de cualificación de leads de Equipzilla, un marketplace B2B de maquinaria industrial. Tu única función es calificar leads de forma eficiente y profesional.\\n\\nOBJETIVO: Recoger 5 datos clave mediante una conversación natural y clasificar al lead como Caliente, Tibio o Frío.\\n\\nDATOS A RECOGER (en este orden):\\n1. Tipo de maquinaria necesaria (lifting, material handling, generación, limpieza, construcción)\\n2. Duración estimada del alquiler (días / semanas / meses)\\n3. Localización donde se necesita la máquina (provincia o ciudad)\\n4. Urgencia (¿cuándo la necesitan? fecha aproximada)\\n5. Presupuesto aproximado (si no lo tienen, marcar como desconocido)\\n\\nREGLAS DE CONVERSACIÓN:\\n- Haz UNA pregunta a la vez. Nunca hagas dos preguntas en el mismo mensaje.\\n- Confirma brevemente cada respuesta antes de pasar a la siguiente pregunta.\\n- Usa un tono profesional pero directo. Sin emojis excesivos.\\n- Si el lead ya dio algún dato en su primer mensaje, úsalo y no lo repitas.\\n- Máximo 2 intentos por pregunta. Si no responde, marca como desconocido.\\n- Nunca discutas precios específicos ni disponibilidad.\\n\\nCLASIFICACIÓN:\\n- CALIENTE: Urgencia < 7 días + presupuesto definido o señal de compra clara\\n- TIBIO: Necesidad clara pero fecha futura o presupuesto sin definir\\n- FRÍO: Información escasa, no urgente o señales de solo exploración\\n\\nCUANDO TENGAS LOS 4 DATOS MÍNIMOS (tipo, duración, localización, urgencia), devuelve ÚNICAMENTE este JSON sin texto adicional:\\n{\\n  \\"clasificacion\\": \\"CALIENTE|TIBIO|FRIO\\",\\n  \\"tipo_maquina\\": \\"string\\",\\n  \\"duracion\\": \\"string\\",\\n  \\"localizacion\\": \\"string\\",\\n  \\"urgencia\\": \\"string\\",\\n  \\"presupuesto\\": \\"string|desconocido\\",\\n  \\"mensaje_cierre\\": \\"Mensaje personalizado para enviar al lead\\",\\n  \\"notas_internas\\": \\"Observaciones relevantes para el equipo\\"\\n}",
  "messages": {{ JSON.stringify($json.messages) }}
}`,
        options: {}
      }
    },

    // ── NODO 7: ¿Respuesta o JSON final? ─────────────────────────────────
    {
      id: "node-switch-type",
      name: "¿Conversación o cualificado?",
      type: "n8n-nodes-base.switch",
      typeVersion: 3,
      position: [1340, 380],
      parameters: {
        mode: "rules",
        rules: {
          values: [
            {
              conditions: {
                options: { caseSensitive: true, leftValue: "", typeValidation: "strict" },
                conditions: [{ leftValue: "={{ $json.content[0].text.trim().startsWith('{') }}", rightValue: true, operator: { type: "boolean", operation: "equals" } }],
                combinator: "and"
              },
              renameOutput: true,
              outputKey: "json_final"
            }
          ]
        },
        fallbackOutput: "extra"
      }
    },

    // ── NODO 8A: Enviar respuesta conversacional por WhatsApp ─────────────
    {
      id: "node-send-whatsapp",
      name: "Enviar respuesta WhatsApp",
      type: "n8n-nodes-base.httpRequest",
      typeVersion: 4.2,
      position: [1560, 240],
      parameters: {
        method: "POST",
        url: "=https://graph.facebook.com/v18.0/{{ $env.WHATSAPP_PHONE_NUMBER_ID }}/messages",
        sendHeaders: true,
        headerParameters: {
          parameters: [
            { name: "Authorization", value: "=Bearer {{ $env.WHATSAPP_ACCESS_TOKEN }}" }
          ]
        },
        sendBody: true,
        specifyBody: "json",
        jsonBody: `={
  "messaging_product": "whatsapp",
  "to": "{{ $('Recuperar historial').item.json.phone }}",
  "type": "text",
  "text": { "body": "{{ $json.content[0].text }}" }
}`,
        options: {}
      }
    },

    // ── NODO 8A-2: Guardar respuesta del asistente en historial ───────────
    {
      id: "node-save-assistant",
      name: "Guardar respuesta asistente",
      type: "n8n-nodes-base.code",
      typeVersion: 2,
      position: [1780, 240],
      parameters: {
        language: "javaScript",
        jsCode: `const conversationId = $('Recuperar historial').item.json.conversationId;
const allData = $getWorkflowStaticData("global");
const assistantText = $('Llamada a Claude API').item.json.content[0].text;

if (allData[conversationId]) {
  allData[conversationId].messages.push({
    role: "assistant",
    content: assistantText
  });
}

return [{ json: { ok: true, conversationId } }];`
      }
    },

    // ── NODO 8B: Parsear JSON de cualificación ────────────────────────────
    {
      id: "node-parse-json",
      name: "Parsear JSON cualificación",
      type: "n8n-nodes-base.code",
      typeVersion: 2,
      position: [1560, 500],
      parameters: {
        language: "javaScript",
        jsCode: `const responseText = $json.content[0].text.trim();
let qualificationData;

try {
  // Limpiar posibles backticks de markdown
  const clean = responseText.replace(/\`\`\`json|\\n\`\`\`|\`\`\`/g, '').trim();
  qualificationData = JSON.parse(clean);
} catch(e) {
  // Si falla el parse, devolver como conversación
  return [{ json: { type: "conversation", text: responseText } }];
}

const historyData = $('Recuperar historial').item.json;

return [{ json: {
  type: "qualified",
  phone: historyData.phone,
  name: historyData.name,
  conversationId: historyData.conversationId,
  turnsCount: historyData.turnsCount,
  qualifiedAt: new Date().toISOString(),
  ...qualificationData
} }];`
      }
    },

    // ── NODO 9: Crear contacto en Pipeline CRM ────────────────────────────
    {
      id: "node-pipeline-contact",
      name: "Crear contacto Pipeline CRM",
      type: "n8n-nodes-base.httpRequest",
      typeVersion: 4.2,
      position: [1780, 500],
      parameters: {
        method: "POST",
        url: "=https://api.pipedrive.com/v1/persons?api_token={{ $env.PIPELINE_API_KEY }}",
        sendBody: true,
        specifyBody: "json",
        jsonBody: `={
  "name": "{{ $json.name }}",
  "phone": [{ "value": "{{ $json.phone }}", "label": "mobile", "primary": true }],
  "label": "{{ $json.clasificacion }}",
  "visible_to": "3"
}`,
        options: {}
      }
    },

    // ── NODO 10: Crear deal en Pipeline CRM ───────────────────────────────
    {
      id: "node-pipeline-deal",
      name: "Crear deal Pipeline CRM",
      type: "n8n-nodes-base.httpRequest",
      typeVersion: 4.2,
      position: [2000, 500],
      parameters: {
        method: "POST",
        url: "=https://api.pipedrive.com/v1/deals?api_token={{ $env.PIPELINE_API_KEY }}",
        sendBody: true,
        specifyBody: "json",
        jsonBody: `={
  "title": "{{ $('Parsear JSON cualificación').item.json.tipo_maquina }} · {{ $('Parsear JSON cualificación').item.json.localizacion }}",
  "person_id": {{ $json.data.id }},
  "status": "open",
  "visible_to": "3"
}`,
        options: {}
      }
    },

    // ── NODO 11: Router por clasificación ─────────────────────────────────
    {
      id: "node-router",
      name: "Router clasificación",
      type: "n8n-nodes-base.switch",
      typeVersion: 3,
      position: [2220, 500],
      parameters: {
        mode: "rules",
        rules: {
          values: [
            {
              conditions: {
                options: { caseSensitive: true, leftValue: "", typeValidation: "strict" },
                conditions: [{ leftValue: "={{ $('Parsear JSON cualificación').item.json.clasificacion }}", rightValue: "CALIENTE", operator: { type: "string", operation: "equals" } }],
                combinator: "and"
              },
              renameOutput: true,
              outputKey: "CALIENTE"
            },
            {
              conditions: {
                options: { caseSensitive: true, leftValue: "", typeValidation: "strict" },
                conditions: [{ leftValue: "={{ $('Parsear JSON cualificación').item.json.clasificacion }}", rightValue: "TIBIO", operator: { type: "string", operation: "equals" } }],
                combinator: "and"
              },
              renameOutput: true,
              outputKey: "TIBIO"
            }
          ]
        },
        fallbackOutput: "extra"
      }
    },

    // ── NODO 12A: Notificar equipo (CALIENTE) ─────────────────────────────
    {
      id: "node-notify-hot",
      name: "Notificar equipo CALIENTE",
      type: "n8n-nodes-base.httpRequest",
      typeVersion: 4.2,
      position: [2440, 360],
      parameters: {
        method: "POST",
        url: "=https://graph.facebook.com/v18.0/{{ $env.WHATSAPP_PHONE_NUMBER_ID }}/messages",
        sendHeaders: true,
        headerParameters: {
          parameters: [
            { name: "Authorization", value: "=Bearer {{ $env.WHATSAPP_ACCESS_TOKEN }}" }
          ]
        },
        sendBody: true,
        specifyBody: "json",
        jsonBody: `={
  "messaging_product": "whatsapp",
  "to": "{{ $env.TEAM_WHATSAPP_NUMBER }}",
  "type": "text",
  "text": {
    "body": "🔥 LEAD CALIENTE\\n\\nNombre: {{ $('Parsear JSON cualificación').item.json.name }}\\nTeléfono: {{ $('Parsear JSON cualificación').item.json.phone }}\\nMáquina: {{ $('Parsear JSON cualificación').item.json.tipo_maquina }}\\nDuración: {{ $('Parsear JSON cualificación').item.json.duracion }}\\nLocalización: {{ $('Parsear JSON cualificación').item.json.localizacion }}\\nUrgencia: {{ $('Parsear JSON cualificación').item.json.urgencia }}\\nPresupuesto: {{ $('Parsear JSON cualificación').item.json.presupuesto }}\\n\\nNotas: {{ $('Parsear JSON cualificación').item.json.notas_internas }}"
  }
}`,
        options: {}
      }
    },

    // ── NODO 12A-2: Mensaje cierre al lead CALIENTE ───────────────────────
    {
      id: "node-close-hot",
      name: "Mensaje cierre lead CALIENTE",
      type: "n8n-nodes-base.httpRequest",
      typeVersion: 4.2,
      position: [2440, 500],
      parameters: {
        method: "POST",
        url: "=https://graph.facebook.com/v18.0/{{ $env.WHATSAPP_PHONE_NUMBER_ID }}/messages",
        sendHeaders: true,
        headerParameters: {
          parameters: [
            { name: "Authorization", value: "=Bearer {{ $env.WHATSAPP_ACCESS_TOKEN }}" }
          ]
        },
        sendBody: true,
        specifyBody: "json",
        jsonBody: `={
  "messaging_product": "whatsapp",
  "to": "{{ $('Parsear JSON cualificación').item.json.phone }}",
  "type": "text",
  "text": { "body": "{{ $('Parsear JSON cualificación').item.json.mensaje_cierre }}" }
}`,
        options: {}
      }
    },

    // ── NODO 12B: Registrar TIBIO en Pipeline ─────────────────────────────
    {
      id: "node-tibio",
      name: "Registrar TIBIO para A05",
      type: "n8n-nodes-base.code",
      typeVersion: 2,
      position: [2440, 620],
      parameters: {
        language: "javaScript",
        jsCode: `// Lead TIBIO: el A05 Quote & Follow-up Agent hará el seguimiento
// Aquí se puede disparar un webhook al A05 cuando esté implementado
const data = $('Parsear JSON cualificación').item.json;
console.log(\`Lead TIBIO registrado: \${data.phone} - \${data.tipo_maquina}\`);
return [{ json: { status: 'tibio_registered', phone: data.phone } }];`
      }
    },

    // ── NODO 12C: Nurturing Brevo (FRÍO) ──────────────────────────────────
    {
      id: "node-frio-brevo",
      name: "Añadir a nurturing Brevo",
      type: "n8n-nodes-base.httpRequest",
      typeVersion: 4.2,
      position: [2440, 740],
      parameters: {
        method: "POST",
        url: "https://api.brevo.com/v3/contacts",
        sendHeaders: true,
        headerParameters: {
          parameters: [
            { name: "api-key", value: "={{ $env.BREVO_API_KEY }}" }
          ]
        },
        sendBody: true,
        specifyBody: "json",
        jsonBody: `={
  "email": "noemail_{{ $('Parsear JSON cualificación').item.json.phone }}@equipzilla.placeholder",
  "attributes": {
    "FIRSTNAME": "{{ $('Parsear JSON cualificación').item.json.name }}",
    "SMS": "+{{ $('Parsear JSON cualificación').item.json.phone }}",
    "TIPO_MAQUINA": "{{ $('Parsear JSON cualificación').item.json.tipo_maquina }}",
    "LEAD_STATUS": "FRIO"
  },
  "listIds": [3],
  "updateEnabled": true
}`,
        options: {}
      }
    }
  ],

  // ─── CONNECTIONS ────────────────────────────────────────────────────────────
  connections: {
    "WhatsApp Webhook": {
      main: [[{ node: "Extraer datos mensaje", type: "main", index: 0 }]]
    },
    "Extraer datos mensaje": {
      main: [[{ node: "¿Verificación o mensaje?", type: "main", index: 0 }]]
    },
    "¿Verificación o mensaje?": {
      main: [
        [{ node: "Responder verificación Meta", type: "main", index: 0 }],
        [{ node: "Recuperar historial", type: "main", index: 0 }]
      ]
    },
    "Recuperar historial": {
      main: [[{ node: "Llamada a Claude API", type: "main", index: 0 }]]
    },
    "Llamada a Claude API": {
      main: [[{ node: "¿Conversación o cualificado?", type: "main", index: 0 }]]
    },
    "¿Conversación o cualificado?": {
      main: [
        [{ node: "Enviar respuesta WhatsApp", type: "main", index: 0 }],
        [{ node: "Parsear JSON cualificación", type: "main", index: 0 }]
      ]
    },
    "Enviar respuesta WhatsApp": {
      main: [[{ node: "Guardar respuesta asistente", type: "main", index: 0 }]]
    },
    "Parsear JSON cualificación": {
      main: [[{ node: "Crear contacto Pipeline CRM", type: "main", index: 0 }]]
    },
    "Crear contacto Pipeline CRM": {
      main: [[{ node: "Crear deal Pipeline CRM", type: "main", index: 0 }]]
    },
    "Crear deal Pipeline CRM": {
      main: [[{ node: "Router clasificación", type: "main", index: 0 }]]
    },
    "Router clasificación": {
      main: [
        [
          { node: "Notificar equipo CALIENTE", type: "main", index: 0 },
          { node: "Mensaje cierre lead CALIENTE", type: "main", index: 0 }
        ],
        [{ node: "Registrar TIBIO para A05", type: "main", index: 0 }],
        [{ node: "Añadir a nurturing Brevo", type: "main", index: 0 }]
      ]
    }
  },

  settings: {
    executionOrder: "v1",
    saveManualExecutions: true,
    callerPolicy: "workflowsFromSameOwner",
    errorWorkflow: ""
  },

  tags: ["Equipzilla", "A03", "Lead Qualifier", "WhatsApp"]
};

// ─── MAIN ───────────────────────────────────────────────────────────────────
async function main() {
  console.log('🔄 Conectando a n8n Cloud...');
  console.log(`   URL: ${N8N_BASE_URL}`);

  // Verificar conexión
  try {
    await apiRequest('GET', '/workflows?limit=1');
    console.log('✅ Conexión verificada.');
  } catch (err) {
    console.error('❌ No se pudo conectar a n8n:', err.message);
    console.error('   Verifica que N8N_API_KEY y N8N_BASE_URL son correctos.');
    process.exit(1);
  }

  // Crear workflow
  console.log('🔄 Creando workflow...');
  let created;
  try {
    created = await apiRequest('POST', '/workflows', workflow);
  } catch (err) {
    console.error('❌ Error al crear el workflow:', err.message);
    process.exit(1);
  }

  const workflowId = created.id;
  console.log(`✅ Workflow creado con ID: ${workflowId}`);
  console.log(`\n📋 RESUMEN DEL WORKFLOW CREADO:`);
  console.log(`   Nombre: ${created.name}`);
  console.log(`   Nodos:  ${created.nodes.length}`);
  console.log(`   Estado: Inactivo (actívalo manualmente tras configurar credenciales)`);
  console.log(`\n🔗 Ábrelo en n8n:`);
  console.log(`   ${N8N_BASE_URL}/workflow/${workflowId}`);
  console.log(`\n⚠️  ANTES DE ACTIVARLO, configura estas variables de entorno en n8n:`);
  console.log(`   Settings → Variables:`);
  console.log(`   - ANTHROPIC_API_KEY`);
  console.log(`   - WHATSAPP_ACCESS_TOKEN`);
  console.log(`   - WHATSAPP_PHONE_NUMBER_ID`);
  console.log(`   - WHATSAPP_VERIFY_TOKEN`);
  console.log(`   - PIPELINE_API_KEY`);
  console.log(`   - BREVO_API_KEY`);
  console.log(`   - TEAM_WHATSAPP_NUMBER (número del equipo para alertas, ej: 34612345678)`);
  console.log(`\n📌 Webhook URL del bot (para configurar en Meta):`);
  console.log(`   ${N8N_BASE_URL}/webhook/whatsapp-lead`);
}

main();

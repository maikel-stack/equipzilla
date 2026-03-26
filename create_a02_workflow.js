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

// ─── WORKFLOW A02 ───────────────────────────────────────────────────────────
const workflow = require('./workflow_a02_gsc_seo.json');
workflow.active = false;

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
    process.exit(1);
  }

  // Crear workflow
  console.log('🔄 Creando workflow A02...');
  let created;
  try {
    created = await apiRequest('POST', '/workflows', workflow);
  } catch (err) {
    console.error('❌ Error al crear el workflow:', err.message);
    process.exit(1);
  }

  const workflowId = created.id;
  console.log(`✅ Workflow creado con ID: ${workflowId}`);
  console.log(`\n📋 RESUMEN:`);
  console.log(`   Nombre: ${created.name}`);
  console.log(`   Nodos:  ${created.nodes.length}`);
  console.log(`   Estado: Inactivo`);
  console.log(`\n🔗 Ábrelo en n8n:`);
  console.log(`   ${N8N_BASE_URL}/workflow/${workflowId}`);
  console.log(`\n⚠️  CONFIGURA estas claves en el nodo ⚙️ Config:`);
  console.log(`   - GSC_ACCESS_TOKEN (Google Search Console)`);
  console.log(`   - ANTHROPIC_API_KEY`);
  console.log(`   - NOTION_API_KEY + NOTION_DATABASE_ID`);
  console.log(`   - DISCORD_WEBHOOK_URL`);
}

main();

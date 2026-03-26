const https = require('https');
const http = require('http');
const fs = require('fs');

const N8N_API_KEY = process.env.N8N_API_KEY;
const N8N_BASE_URL = process.env.N8N_BASE_URL;

if (!N8N_API_KEY || !N8N_BASE_URL) {
  console.error('Faltan variables de entorno: N8N_API_KEY y N8N_BASE_URL');
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

// ─── MAIN ───────────────────────────────────────────────────────────────────
async function main() {
  console.log('Conectando a n8n Cloud...');
  console.log(`   URL: ${N8N_BASE_URL}`);

  // Verificar conexion
  try {
    await apiRequest('GET', '/workflows?limit=1');
    console.log('Conexion verificada.');
  } catch (err) {
    console.error('No se pudo conectar a n8n:', err.message);
    console.error('   Verifica que N8N_API_KEY y N8N_BASE_URL son correctos.');
    process.exit(1);
  }

  // Leer workflow JSON
  const workflowData = JSON.parse(fs.readFileSync('./workflow_a02_seo.json', 'utf8'));
  workflowData.active = false;

  // Crear workflow
  console.log('Creando workflow A02 SEO Content Agent...');
  let created;
  try {
    created = await apiRequest('POST', '/workflows', workflowData);
  } catch (err) {
    console.error('Error al crear el workflow:', err.message);
    process.exit(1);
  }

  const workflowId = created.id;
  console.log(`Workflow creado con ID: ${workflowId}`);
  console.log(`\nRESUMEN DEL WORKFLOW CREADO:`);
  console.log(`   Nombre: ${created.name}`);
  console.log(`   Nodos:  ${created.nodes.length}`);
  console.log(`   Estado: Inactivo (activalo tras configurar credenciales)`);
  console.log(`\nAbrelo en n8n:`);
  console.log(`   ${N8N_BASE_URL}/workflow/${workflowId}`);
  console.log(`\nANTES DE ACTIVARLO, configura en el nodo Config:`);
  console.log(`   - ANTHROPIC_API_KEY (tu API key de Anthropic)`);
  console.log(`   - GSC_ACCESS_TOKEN (OAuth token de Google Search Console)`);
  console.log(`   - GSC_SITE_URL (ej: sc-domain:equipzilla.com)`);
  console.log(`   - NOTION_API_KEY (Integration token de Notion)`);
  console.log(`   - NOTION_DATABASE_ID (ID de la base de datos de contenido)`);
  console.log(`   - DISCORD_WEBHOOK_URL (webhook del canal de SEO)`);
  console.log(`\nBase de datos Notion necesaria con estas propiedades:`);
  console.log(`   - Titulo (title)`);
  console.log(`   - Tipo (select: FICHA_PRODUCTO, COMPARATIVA, GUIA, LANDING_LOCAL, FAQ)`);
  console.log(`   - Categoria (select: las 5 categorias de maquinaria)`);
  console.log(`   - Keyword Principal (rich_text)`);
  console.log(`   - Meta Title (rich_text)`);
  console.log(`   - Meta Description (rich_text)`);
  console.log(`   - Slug (url)`);
  console.log(`   - Palabras (number)`);
  console.log(`   - Estado (select: Borrador, En Revision, Publicado)`);
  console.log(`   - Prioridad (number)`);
  console.log(`   - Fecha Generacion (date)`);
}

main();

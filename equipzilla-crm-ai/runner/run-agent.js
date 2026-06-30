#!/usr/bin/env node
// Runner para los agentes de equipzilla-crm-ai.
//
// Uso:
//   node equipzilla-crm-ai/runner/run-agent.js lead  <input.json> [--model sonnet|opus] [--out file.json]
//   node equipzilla-crm-ai/runner/run-agent.js deal  <input.json> [--model sonnet|opus] [--out file.json]
//
// Variables de entorno:
//   ANTHROPIC_API_KEY   (obligatoria) — clave de la API de Claude.
//   APOLLO_MCP_URL      (opcional)    — URL del MCP de Apollo para enriquecimiento de empresa/personas.
//   APOLLO_MCP_TOKEN    (opcional)    — bearer token del MCP de Apollo.
//
// Salida: imprime el JSON del dossier/brief por stdout (y a --out si se indica),
// validado contra el schema correspondiente en ../schemas/.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import Anthropic from "@anthropic-ai/sdk";
import Ajv from "ajv";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");

const AGENTS = {
  lead: {
    system: path.join(ROOT, "agents", "lead-intelligence.md"),
    schema: path.join(ROOT, "schemas", "lead-dossier.json"),
    useApollo: true,
  },
  deal: {
    system: path.join(ROOT, "agents", "deal-intelligence.md"),
    schema: path.join(ROOT, "schemas", "deal-brief.json"),
    useApollo: false,
  },
};

// Sonnet para volumen, Opus para deals de alto ticket (ver README "Modelo").
const MODELS = {
  sonnet: "claude-sonnet-4-6",
  opus: "claude-opus-4-8",
};

function fail(msg) {
  console.error(`\n✖ ${msg}\n`);
  process.exit(1);
}

function parseArgs(argv) {
  const [agent, inputPath, ...rest] = argv;
  const opts = { agent, inputPath, model: "sonnet", out: null };
  for (let i = 0; i < rest.length; i++) {
    if (rest[i] === "--model") opts.model = rest[++i];
    else if (rest[i] === "--out") opts.out = rest[++i];
  }
  return opts;
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));

  if (!opts.agent || !AGENTS[opts.agent]) {
    fail(`Indica el agente: 'lead' o 'deal'.\n  Uso: node run-agent.js lead <input.json> [--model sonnet|opus]`);
  }
  if (!opts.inputPath) fail("Falta el fichero de entrada (JSON del lead/deal).");
  if (!MODELS[opts.model]) fail(`Modelo no válido: ${opts.model}. Usa 'sonnet' u 'opus'.`);
  if (!process.env.ANTHROPIC_API_KEY) {
    fail("Falta ANTHROPIC_API_KEY en el entorno. Expórtala antes de ejecutar:\n  export ANTHROPIC_API_KEY=sk-ant-...");
  }

  const cfg = AGENTS[opts.agent];
  const systemPrompt = fs.readFileSync(cfg.system, "utf8");
  const schema = JSON.parse(fs.readFileSync(cfg.schema, "utf8"));
  const input = JSON.parse(fs.readFileSync(opts.inputPath, "utf8"));

  // Herramientas server-side: web_search siempre; Apollo MCP si está configurado y el agente lo usa.
  const tools = [{ type: "web_search_20250305", name: "web_search", max_uses: 5 }];
  const mcpServers = [];
  if (cfg.useApollo && process.env.APOLLO_MCP_URL) {
    mcpServers.push({
      type: "url",
      url: process.env.APOLLO_MCP_URL,
      name: "apollo",
      ...(process.env.APOLLO_MCP_TOKEN
        ? { authorization_token: process.env.APOLLO_MCP_TOKEN }
        : {}),
    });
  }

  const client = new Anthropic();

  const requestOpts = {};
  if (mcpServers.length) {
    // El connector MCP de la Messages API requiere esta cabecera beta.
    requestOpts.headers = { "anthropic-beta": "mcp-client-2025-04-04" };
  }

  console.error(
    `→ Ejecutando agente '${opts.agent}' con ${MODELS[opts.model]}` +
      (mcpServers.length ? " + Apollo MCP" : " (sin Apollo: enriquecimiento solo por web)") +
      "...",
  );

  const message = await client.messages.create(
    {
      model: MODELS[opts.model],
      max_tokens: 4096,
      system: systemPrompt,
      tools,
      ...(mcpServers.length ? { mcp_servers: mcpServers } : {}),
      messages: [
        {
          role: "user",
          content: `Procesa esta entrada y devuelve SOLO el JSON conforme al schema, sin texto alrededor:\n\n${JSON.stringify(input, null, 2)}`,
        },
      ],
    },
    requestOpts,
  );

  // Concatena los bloques de texto de la respuesta (puede haber varios tras tool-use).
  const text = message.content
    .filter((b) => b.type === "text")
    .map((b) => b.text)
    .join("")
    .trim();

  const jsonStr = extractJson(text);
  if (!jsonStr) fail(`El modelo no devolvió JSON parseable. Respuesta:\n${text}`);

  let result;
  try {
    result = JSON.parse(jsonStr);
  } catch (e) {
    fail(`JSON inválido devuelto por el modelo: ${e.message}\n\n${jsonStr}`);
  }

  // Validación contra el schema (avisa pero no bloquea: el dossier sigue siendo útil).
  const ajv = new Ajv({ allErrors: true, strict: false });
  const validate = ajv.compile(schema);
  if (!validate(result)) {
    console.error("⚠ El JSON no cumple del todo el schema:");
    for (const err of validate.errors) {
      console.error(`   - ${err.instancePath || "(raíz)"} ${err.message}`);
    }
  } else {
    console.error("✓ JSON válido contra el schema.");
  }

  const out = JSON.stringify(result, null, 2);
  if (opts.out) {
    fs.writeFileSync(opts.out, out + "\n");
    console.error(`✓ Escrito en ${opts.out}`);
  }
  process.stdout.write(out + "\n");
}

// Extrae el primer objeto JSON balanceado del texto (por si el modelo añade texto pese a las instrucciones).
function extractJson(text) {
  const start = text.indexOf("{");
  if (start === -1) return null;
  let depth = 0;
  let inStr = false;
  let esc = false;
  for (let i = start; i < text.length; i++) {
    const c = text[i];
    if (inStr) {
      if (esc) esc = false;
      else if (c === "\\") esc = true;
      else if (c === '"') inStr = false;
    } else if (c === '"') inStr = true;
    else if (c === "{") depth++;
    else if (c === "}") {
      depth--;
      if (depth === 0) return text.slice(start, i + 1);
    }
  }
  return null;
}

main().catch((e) => fail(e.stack || String(e)));

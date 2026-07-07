#!/usr/bin/env node
// Prospección de empresas de construcción vía Apollo.io.
//
// Busca personas (decisores) que encajan con el ICP, revela su email profesional
// y exporta a CSV + JSON, listo para pasar cada una por el agente Lead Intelligence.
//
// Uso:
//   node equipzilla-crm-ai/prospecting/apollo-prospect.js [icp.json] [--out-dir dir] [--no-reveal]
//
// Entorno:
//   APOLLO_API_KEY   (obligatoria) — API key de Apollo (Settings → Integrations → API).
//
// Flags:
//   --no-reveal   No consume créditos de export: trae los datos pero deja el email enmascarado.
//
// Nota de créditos: revelar emails consume créditos de export de Apollo. Empieza con un
// per_page/max_pages pequeño para calibrar consumo antes de tirar tandas grandes.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const APOLLO = "https://api.apollo.io/api/v1";

function fail(msg) {
  console.error(`\n✖ ${msg}\n`);
  process.exit(1);
}

function parseArgs(argv) {
  const opts = { icp: path.join(__dirname, "icp-construccion.json"), outDir: __dirname, reveal: true };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--out-dir") opts.outDir = argv[++i];
    else if (argv[i] === "--no-reveal") opts.reveal = false;
    else if (!argv[i].startsWith("--")) opts.icp = argv[i];
  }
  return opts;
}

async function apollo(endpoint, body, apiKey) {
  const res = await fetch(`${APOLLO}${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "no-cache",
      "X-Api-Key": apiKey,
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Apollo ${endpoint} → HTTP ${res.status}: ${text.slice(0, 400)}`);
  }
  return res.json();
}

// Un email de Apollo es "real" si no viene enmascarado como email_not_unlocked@domain.com.
function realEmail(person) {
  const e = person.email;
  if (!e || e.includes("email_not_unlocked") || e.includes("not_unlocked")) return null;
  return e;
}

function csvEscape(v) {
  if (v == null) return "";
  const s = String(v);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  const apiKey = process.env.APOLLO_API_KEY;
  if (!apiKey) fail("Falta APOLLO_API_KEY en el entorno.\n  export APOLLO_API_KEY=...");

  const icp = JSON.parse(fs.readFileSync(opts.icp, "utf8"));
  const perPage = icp.per_page || 25;
  const maxPages = icp.max_pages || 1;

  const searchBody = {
    person_titles: icp.person_titles,
    person_locations: icp.person_locations,
    organization_num_employees_ranges: icp.organization_num_employees_ranges,
    q_organization_keyword_tags: icp.q_organization_keyword_tags,
    per_page: perPage,
    // Pide a Apollo que revele el email profesional (consume crédito de export).
    reveal_personal_emails: false,
  };

  const people = [];
  for (let page = 1; page <= maxPages; page++) {
    console.error(`→ Apollo People Search — página ${page}/${maxPages}...`);
    const data = await apollo("/mixed_people/search", { ...searchBody, page }, apiKey);
    const batch = data.people || [];
    people.push(...batch);
    console.error(`   ${batch.length} personas (total acumulado: ${people.length})`);
    if (batch.length < perPage) break; // no hay más páginas
  }

  if (!people.length) {
    fail("Apollo no devolvió personas. Revisa el ICP (cargos/geo/tamaño/keywords) o tu plan/créditos.");
  }

  // Opcionalmente enriquece por lotes para forzar el reveal del email (People Bulk Match).
  let enriched = people;
  if (opts.reveal) {
    console.error(`→ Revelando emails (People Bulk Match)...`);
    const details = people.map((p) => ({
      first_name: p.first_name,
      last_name: p.last_name,
      organization_name: p.organization?.name,
      domain: p.organization?.primary_domain,
      id: p.id,
    }));
    try {
      const match = await apollo(
        "/people/bulk_match",
        { details, reveal_personal_emails: false },
        apiKey,
      );
      if (Array.isArray(match.matches)) {
        enriched = match.matches.map((m, i) => m || people[i]);
      }
    } catch (e) {
      console.error(`⚠ No se pudo hacer bulk_match (${e.message}). Uso los datos del search.`);
    }
  }

  const rows = enriched.map((p) => ({
    nombre: [p.first_name, p.last_name].filter(Boolean).join(" "),
    cargo: p.title || "",
    email: realEmail(p) || "",
    email_status: realEmail(p) ? "revelado" : "no revelado",
    telefono: p.organization?.phone || p.sanitized_phone || "",
    empresa: p.organization?.name || "",
    dominio: p.organization?.primary_domain || "",
    empleados: p.organization?.estimated_num_employees || "",
    ubicacion: [p.city, p.state, p.country].filter(Boolean).join(", "),
    linkedin: p.linkedin_url || "",
  }));

  const withEmail = rows.filter((r) => r.email).length;

  // Salida JSON (para encadenar con el agente) y CSV (para revisar / importar al CRM).
  const stamp = "run";
  const jsonPath = path.join(opts.outDir, `prospects-${stamp}.json`);
  const csvPath = path.join(opts.outDir, `prospects-${stamp}.csv`);

  fs.writeFileSync(jsonPath, JSON.stringify(rows, null, 2) + "\n");

  const headers = Object.keys(rows[0]);
  const csv = [
    headers.join(","),
    ...rows.map((r) => headers.map((h) => csvEscape(r[h])).join(",")),
  ].join("\n");
  fs.writeFileSync(csvPath, csv + "\n");

  console.error(`\n✓ ${rows.length} contactos — ${withEmail} con email revelado.`);
  console.error(`  JSON: ${jsonPath}`);
  console.error(`  CSV:  ${csvPath}\n`);
}

main().catch((e) => fail(e.stack || String(e)));

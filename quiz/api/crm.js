// CRM visual del equipo (ocasion.equipzilla.com/crm): API de datos.
//
// Lee en vivo la pestaña «Cola comercial» del Sheet de mando (la genera
// scripts/cola_comercial.py con Pipedrive + Brevo + Smartlead) y devuelve
// un JSON limpio. Las notas del equipo se guardan en la pestaña «CRM · notas»
// del mismo Sheet, así que Pipedrive y el Sheet siguen siendo la fuente de
// verdad y nada de datos personales pasa por el repo.
//
// Acceso con contraseña compartida del equipo (CRM_PASSWORD): el login
// devuelve un token firmado (HMAC) válido 12 h. Sin token, nada se devuelve.
// La cuenta de servicio de Google vive en GOOGLE_SA_JSON (JSON completo).

const crypto = require("crypto");

const SHEET_ID = "1wyWmrmg_NlxhN0ZW4iIxE8ZG-y-zMBXfY4_agAl54vM";
const TAB_COLA = "Cola comercial";
const TAB_NOTAS = "CRM · notas";
const TTL_SESION = 12 * 60 * 60 * 1000;
const TTL_CACHE = 90 * 1000;

let cache = { at: 0, data: null };

// ---------------------------------------------------------------- sesión
function secreto() {
  return process.env.CRM_PASSWORD || "";
}

function firmar(exp) {
  return crypto.createHmac("sha256", secreto()).update(String(exp)).digest("base64url");
}

function emitirToken() {
  const exp = Date.now() + TTL_SESION;
  return `${exp}.${firmar(exp)}`;
}

function tokenValido(token) {
  if (!token || !secreto()) return false;
  const [exp, sig] = String(token).split(".");
  if (!exp || !sig || Number(exp) < Date.now()) return false;
  const esperado = firmar(exp);
  return sig.length === esperado.length &&
    crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(esperado));
}

function passwordCorrecta(p) {
  const s = secreto();
  if (!s || !p) return false;
  const a = Buffer.from(String(p)), b = Buffer.from(s);
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

// ---------------------------------------------------------------- Google
function b64url(buf) {
  return Buffer.from(buf).toString("base64url");
}

async function tokenGoogle(scope) {
  const sa = JSON.parse(process.env.GOOGLE_SA_JSON || "{}");
  if (!sa.client_email) throw new Error("GOOGLE_SA_JSON no configurada");
  const ahora = Math.floor(Date.now() / 1000);
  const cab = b64url(JSON.stringify({ alg: "RS256", typ: "JWT" }));
  const cuerpo = b64url(JSON.stringify({
    iss: sa.client_email, scope, aud: sa.token_uri, iat: ahora, exp: ahora + 3600,
  }));
  const firma = crypto.sign("RSA-SHA256", Buffer.from(`${cab}.${cuerpo}`), sa.private_key);
  const r = await fetch(sa.token_uri, {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
      assertion: `${cab}.${cuerpo}.${b64url(firma)}`,
    }),
  });
  const j = await r.json();
  if (!j.access_token) throw new Error("token google: " + JSON.stringify(j).slice(0, 200));
  return j.access_token;
}

async function sheets(tk, ruta, method = "GET", body) {
  const r = await fetch(`https://sheets.googleapis.com/v4/spreadsheets/${SHEET_ID}${ruta}`, {
    method,
    headers: { authorization: `Bearer ${tk}`, "content-type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(`sheets ${r.status}: ${JSON.stringify(j).slice(0, 200)}`);
  return j;
}

const rango = (tab, celdas) => `/values/${encodeURIComponent(`${tab}!${celdas}`)}`;

// ---------------------------------------------------------------- parseo
const CLAVES = {
  "Score": "score", "Prioridad": "prioridad", "Canal de entrada": "canal", "Etapa CRM": "etapa",
  "Contacto": "contacto", "Propietario": "propietario", "Nombre": "nombre", "Empresa": "empresa",
  "Tipo de empresa": "tipo", "Teléfono": "telefono", "Email": "email",
  "Qué pide / qué miró": "pide", "Categoría": "categoria", "Presupuesto / valor": "valor",
  "Qué tenemos que encaja [ref]": "encaja", "Lista / campaña": "lista", "Última señal": "senal",
  "Última actualización en Pipedrive": "actualizacion", "Días desde entrada": "diasEntrada",
  "Días en etapa": "diasEtapa", "Días hasta oferta": "diasOferta", "Por qué": "porque",
  "Siguiente acción": "accion",
};

function numero(v) {
  const n = parseInt(String(v || "").replace(/[^\d-]/g, ""), 10);
  return Number.isFinite(n) ? n : null;
}

function parsearCola(filas) {
  const out = { generado: "", tiempos: [], leads: [] };
  const titulo = (filas[0] || [])[0] || "";
  const m = titulo.match(/(\d{2}\/\d{2}\/\d{4} \d{2}:\d{2})/);
  out.generado = m ? m[1] : "";
  let iCab = filas.findIndex((f) => (f[0] || "") === "Score");
  if (iCab < 0) return out;
  for (let i = 0; i < iCab; i++) {
    const f = filas[i];
    if (f && f.length >= 2 && f[0] && !/^TIEMPOS/.test(f[0])) {
      out.tiempos.push({ nombre: f[0], valor: f[1], detalle: f[2] || "" });
    }
  }
  const cab = filas[iCab].map((h) => CLAVES[h] || h);
  for (const f of filas.slice(iCab + 1)) {
    if (!f || !f[0]) continue;
    const o = {};
    cab.forEach((k, j) => { o[k] = f[j] === undefined ? "" : f[j]; });
    o.score = numero(o.score) || 0;
    o.valorNum = numero(o.valor);
    o.diasEntrada = numero(o.diasEntrada);
    o.diasEtapa = numero(o.diasEtapa);
    o.diasOferta = numero(o.diasOferta);
    o.email = String(o.email || "").toLowerCase();
    out.leads.push(o);
  }
  return out;
}

function parsearNotas(filas) {
  // fecha ISO · email · quién · estado · nota
  const notas = {};
  for (const f of filas || []) {
    if (!f || !f[1]) continue;
    const email = String(f[1]).toLowerCase();
    (notas[email] = notas[email] || []).push({
      fecha: f[0] || "", quien: f[2] || "", estado: f[3] || "", nota: f[4] || "",
    });
  }
  return notas;
}

// ---------------------------------------------------------------- datos
async function datos() {
  if (cache.data && Date.now() - cache.at < TTL_CACHE) return cache.data;
  const tk = await tokenGoogle("https://www.googleapis.com/auth/spreadsheets.readonly");
  const cola = await sheets(tk, rango(TAB_COLA, "A1:W600"));
  let notas = [];
  try {
    notas = (await sheets(tk, rango(TAB_NOTAS, "A2:E5000"))).values || [];
  } catch (e) { /* la pestaña se crea con la primera nota */ }
  const d = parsearCola(cola.values || []);
  d.notas = parsearNotas(notas);
  d.leido = new Date().toISOString();
  cache = { at: Date.now(), data: d };
  return d;
}

async function guardarNota({ email, quien, estado, nota }) {
  const tk = await tokenGoogle("https://www.googleapis.com/auth/spreadsheets");
  const fila = [new Date().toISOString(), String(email || "").toLowerCase(),
    String(quien || "").slice(0, 40), String(estado || "").slice(0, 40), String(nota || "").slice(0, 500)];
  const cuerpo = { values: [fila] };
  try {
    await sheets(tk, rango(TAB_NOTAS, "A1") + "?valueInputOption=RAW&insertDataOption=INSERT_ROWS", "POST", cuerpo);
  } catch (e) {
    // primera vez: crear la pestaña con cabecera y reintentar
    await sheets(tk, ":batchUpdate", "POST", {
      requests: [{ addSheet: { properties: { title: TAB_NOTAS } } }],
    });
    await sheets(tk, rango(TAB_NOTAS, "A1") + "?valueInputOption=RAW", "PUT",
      { values: [["Fecha", "Email", "Quién", "Estado", "Nota"]] });
    await sheets(tk, rango(TAB_NOTAS, "A1") + "?valueInputOption=RAW&insertDataOption=INSERT_ROWS", "POST", cuerpo);
  }
  cache = { at: 0, data: null };
  return fila;
}

// ---------------------------------------------------------------- handler
function leerBody(req) {
  if (req.body && typeof req.body === "object") return req.body;
  try { return JSON.parse(req.body || "{}"); } catch (e) { return {}; }
}

module.exports = async (req, res) => {
  res.setHeader("cache-control", "no-store");
  res.setHeader("x-robots-tag", "noindex, nofollow");
  try {
    if (req.method === "POST") {
      const b = leerBody(req);
      if (b.op === "login") {
        if (!passwordCorrecta(b.password)) return res.status(401).json({ error: "Contraseña incorrecta" });
        return res.status(200).json({ token: emitirToken(), caduca: Date.now() + TTL_SESION });
      }
      if (!tokenValido(b.token || (req.headers.authorization || "").replace(/^Bearer /, ""))) {
        return res.status(401).json({ error: "Sesión caducada. Vuelve a entrar." });
      }
      if (b.op === "nota") {
        if (!b.email) return res.status(400).json({ error: "Falta el email del lead" });
        const fila = await guardarNota(b);
        return res.status(200).json({ ok: true, fila });
      }
      return res.status(400).json({ error: "Operación desconocida" });
    }
    const token = (req.headers.authorization || "").replace(/^Bearer /, "");
    if (!tokenValido(token)) return res.status(401).json({ error: "Sin sesión" });
    return res.status(200).json(await datos());
  } catch (e) {
    return res.status(500).json({ error: String(e.message || e).slice(0, 300) });
  }
};

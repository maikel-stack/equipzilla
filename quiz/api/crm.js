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
const SHEET_STOCK = "1mCZtAe95o2va0ofw8Ts_e8ei3gv-QK5_CBr7moZ_hDE";   // «Stock Outreach PANEL» de David
const TTL_SESION = 180 * 24 * 60 * 60 * 1000;   // 180 días; se renueva en cada login
const TTL_CACHE = 90 * 1000;

let cache = { at: 0, data: null };

// ---------------------------------------------------------------- sesión
function secreto() {
  return process.env.CRM_PASSWORD || "";
}

// Usuarios personales en CRM_USERS_JSON: {"maikel": {"hash": sha256(usuario:contraseña), "nombre": "Maikel", "rol": "admin"}, …}
function usuarios() {
  try { return JSON.parse(process.env.CRM_USERS_JSON || "{}"); } catch (e) { return {}; }
}

function hashPass(usuario, pass) {
  return crypto.createHash("sha256").update(`${usuario}:${pass}`).digest("hex");
}

function firmar(exp, usuario) {
  return crypto.createHmac("sha256", secreto()).update(`${exp}|${usuario}`).digest("base64url");
}

function emitirToken(usuario) {
  const exp = Date.now() + TTL_SESION;
  return `${exp}.${Buffer.from(usuario).toString("base64url")}.${firmar(exp, usuario)}`;
}

// Claves de API permanentes (integraciones, Lorenzo): CRM_API_KEYS_JSON
// {"ezk_…": {"usuario": "lorenzo", "nombre": "Lorenzo (API)", "rol": "tech"}}
function clavesApi() {
  try { return JSON.parse(process.env.CRM_API_KEYS_JSON || "{}"); } catch (e) { return {}; }
}

// Devuelve {usuario, nombre, rol} o null
function sesion(token) {
  if (!token || !secreto()) return null;
  if (String(token).startsWith("ezk_")) {                          // clave de API: no caduca
    for (const [k, v] of Object.entries(clavesApi())) {
      if (iguales(k, token)) return { usuario: v.usuario || "api", nombre: v.nombre || "API", rol: v.rol || "tech", api: true };
    }
    return null;
  }
  const partes = String(token).split(".");
  if (partes.length !== 3) return null;
  const [exp, u64, sig] = partes;
  const usuario = Buffer.from(u64, "base64url").toString();
  if (!exp || !sig || Number(exp) < Date.now()) return null;
  const esperado = firmar(exp, usuario);
  if (sig.length !== esperado.length || !crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(esperado))) return null;
  const u = usuarios()[usuario];
  if (!u && usuario !== "equipo") return null;                   // usuario dado de baja
  return { usuario, nombre: u ? u.nombre : "Equipo", rol: u ? u.rol : "sales" };
}

function tokenValido(token) { return !!sesion(token); }

function iguales(a, b) {
  const x = Buffer.from(String(a)), y = Buffer.from(String(b));
  return x.length === y.length && crypto.timingSafeEqual(x, y);
}

// Login personal (usuario + contraseña). La contraseña compartida CRM_PASSWORD
// sigue valiendo como usuario "equipo" mientras se reparten las personales.
function autenticar(usuario, pass) {
  if (!pass) return null;
  const u = String(usuario || "").trim().toLowerCase();
  const reg = usuarios()[u];
  if (reg && iguales(hashPass(u, pass), reg.hash)) return { usuario: u, nombre: reg.nombre, rol: reg.rol || "sales" };
  if (!u || u === "equipo") { if (secreto() && iguales(pass, secreto())) return { usuario: "equipo", nombre: "Equipo", rol: "sales" }; }
  return null;
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

async function sheets(tk, ruta, method = "GET", body, sheetId = SHEET_ID) {
  const r = await fetch(`https://sheets.googleapis.com/v4/spreadsheets/${sheetId}${ruta}`, {
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
  "Siguiente acción": "accion", "ID trato": "dealId",
};

// ---------------------------------------------------------------- Pipedrive
const PIPELINE_ID = 6;
const ETAPAS_PD = { 45: "Lead - Recibido", 33: "Enviar Oferta - Validado", 37: "Oferta enviada",
  38: "Oferta Aceptada", 28: "Alquilador Asignado", 46: "Entrega de equipo" };

async function pd(method, path, body) {
  const token = process.env.PIPEDRIVE_TOKEN;
  if (!token) throw new Error("PIPEDRIVE_TOKEN no configurado");
  const r = await fetch(`https://api.pipedrive.com/v1/${path}${path.includes("?") ? "&" : "?"}api_token=${token}`,
    { method, headers: { "content-type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
  const j = await r.json().catch(() => ({}));
  if (!r.ok || j.success === false) throw new Error(`pipedrive ${r.status}: ${(j.error || "").slice(0, 160)}`);
  return j.data;
}

async function personaPorEmail(email) {
  const r = await pd("GET", `persons/search?term=${encodeURIComponent(email)}&fields=email&limit=1`);
  const it = (r && r.items) || [];
  return it.length ? it[0].item : null;
}

// Trato abierto de compraventa de esa persona (para leads sin ID en el Sheet)
async function tratoPorEmail(email) {
  const p = await personaPorEmail(email);
  if (!p) return null;
  const deals = (await pd("GET", `persons/${p.id}/deals?status=open&limit=50`)) || [];
  return deals.find((d) => d.pipeline_id === PIPELINE_ID || d.pipeline_id === 16) || null;
}

async function crearTrato({ email, nombre, empresa, telefono, canal, pide }, stageId) {
  let p = await personaPorEmail(email);
  if (!p) {
    p = await pd("POST", "persons", {
      name: (nombre && nombre !== "—") ? nombre : (empresa && empresa !== "—" ? empresa : email),
      email: [{ value: email, primary: true }],
      phone: telefono && telefono !== "sin teléfono" ? [{ value: telefono, primary: true }] : [],
    });
  }
  const origen = String(canal || "").replace("Smartlead · ", "").replace("Brevo · clic campaña ABM", "Clic campaña BBDD");
  const titulo = `Prospecto - ${origen} - ${(empresa && empresa !== "—") ? empresa : (pide || "").slice(0, 40)}`.slice(0, 120);
  return pd("POST", "deals", { title: titulo, person_id: p.id, pipeline_id: PIPELINE_ID, stage_id: stageId });
}

async function moverTrato(b) {
  const stageId = Number(b.stageId);
  if (!ETAPAS_PD[stageId]) throw new Error("Etapa desconocida");
  let dealId = Number(b.dealId) || 0;
  let creado = false;
  if (!dealId && b.email) {
    const d = await tratoPorEmail(b.email);
    if (d) dealId = d.id;
  }
  let deal;
  if (dealId) {
    deal = await pd("PUT", `deals/${dealId}`, { stage_id: stageId });
  } else {
    if (!b.email) throw new Error("Sin email no se puede crear el trato");
    deal = await crearTrato(b, stageId);
    creado = true;
  }
  await guardarNota({ email: b.email, dealId: deal.id, quien: b.quien, estado: creado ? "Trato creado" : "Etapa cambiada",
    nota: `${creado ? "Creado desde el CRM visual" : "Movido desde el CRM visual"} → ${ETAPAS_PD[stageId]}${b.nota ? " · " + String(b.nota).slice(0, 300) : ""}` });
  return { dealId: deal.id, etapa: ETAPAS_PD[stageId], creado, titulo: deal.title };
}

async function perderTrato(b) {
  let dealId = Number(b.dealId) || 0;
  if (!dealId && b.email) { const d = await tratoPorEmail(b.email); if (d) dealId = d.id; }
  if (!dealId) throw new Error("Este lead no tiene trato en Pipedrive");
  const deal = await pd("PUT", `deals/${dealId}`, { status: "lost", lost_reason: String(b.razon || "").slice(0, 100) || "Sin motivo" });
  await guardarNota({ email: b.email, dealId: deal.id, quien: b.quien, estado: "Perdido", nota: `Marcado perdido desde el CRM visual: ${b.razon || "sin motivo"}` });
  return { dealId: deal.id };
}

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

function precioNum(v) {
  const t = String(v || "").replace(/€/g, "").trim();
  if (!t) return null;
  const m = t.replace(/\s/g, "").replace(/\.(?=\d{3})/g, "").replace(",", ".");
  const n = parseFloat(m);
  return Number.isFinite(n) ? Math.round(n) : null;
}

const CAT_STOCK = [
  [/telesc|manipulador/i, "Telescópicas"],
  [/tijera|plataforma|articulad|brazo|elevador|camión plataforma|camion plataforma/i, "Plataformas de elevación"],
  [/mini ?exc|miniexc|kubota|develon|doosan dx ?[23]\d\b/i, "Miniexcavadoras"],
  [/excavadora|giratoria|retro/i, "Excavadoras"],
  [/carretilla|transpaleta|apilador/i, "Carretillas"],
  [/pala|cargadora|bobcat|minicargadora/i, "Palas y minicargadoras"],
  [/dumper/i, "Dumpers"],
  [/generador|grupo electr/i, "Generadores"],
  [/caseta|contenedor|aseo|módulo|modulo/i, "Casetas y contenedores"],
];
function categoriaStock(...textos) {
  const t = textos.join(" ");
  for (const [re, cat] of CAT_STOCK) if (re.test(t)) return cat;
  return "Otros";
}

async function stock(tk) {
  // Columnas: Ref · fecha salida · Familia · Subcategoría · Máquina · Marca · Año ·
  // Peso/Capacidad/Altura · Horas · Precio · Clientes BBDD · Plantilla · Descripción · Imagen · Notas
  const meta = await sheets(tk, "?fields=sheets.properties", "GET", null, SHEET_STOCK);
  const tab = ((meta.sheets || [])[0] || {}).properties?.title || "Untitled";
  const filas = (await sheets(tk, rango(tab, "A2:O400"), "GET", null, SHEET_STOCK)).values || [];
  const out = [];
  filas.forEach((f, i) => {
    const [ref, salida, familia, sub, maquina, marca, anio, capacidad, horas, precio, , , descripcion, imagen, notas] = f;
    if (!maquina && !sub) return;
    const titulo = [String(marca || "").trim(), String(maquina || "").trim()].filter(Boolean).join(" ");
    out.push({
      id: "S" + (i + 2), ref: String(ref || "").trim(), salida: String(salida || "").trim(),
      familia: String(familia || "").trim(), sub: String(sub || "").trim(), titulo,
      anio: String(anio || "").trim(), capacidad: String(capacidad || "").trim(),
      horas: String(horas || "").trim(), precio: precioNum(precio), precioTxt: String(precio || "").trim(),
      descripcion: String(descripcion || "").trim().slice(0, 160), notas: String(notas || "").trim().slice(0, 160),
      imagen: /^https?:/.test(String(imagen || "")) ? String(imagen).trim() : "", conFoto: /^https?:/.test(String(imagen || "")), categoria: categoriaStock(familia, sub, maquina, marca),
    });
  });
  return out;
}

// ---------------------------------------------------------------- datos
async function datos() {
  if (cache.data && Date.now() - cache.at < TTL_CACHE) return cache.data;
  const tk = await tokenGoogle("https://www.googleapis.com/auth/spreadsheets.readonly");
  const cola = await sheets(tk, rango(TAB_COLA, "A1:X600"));
  let notas = [];
  try {
    notas = (await sheets(tk, rango(TAB_NOTAS, "A2:E5000"))).values || [];
  } catch (e) { /* la pestaña se crea con la primera nota */ }
  const d = parsearCola(cola.values || []);
  d.notas = parsearNotas(notas);
  try { d.stock = await stock(tk); } catch (e) { d.stock = []; d.stockError = String(e.message || e).slice(0, 160); }
  d.leido = new Date().toISOString();
  cache = { at: Date.now(), data: d };
  return d;
}

async function notaPipedrive({ email, dealId, quien, estado, nota }) {
  let id = Number(dealId) || 0;
  if (!id && email) { try { const d = await tratoPorEmail(email); if (d) id = d.id; } catch (e) { /* sin trato */ } }
  if (!id) return null;
  const contenido = `<b>[CRM · ${String(quien || "equipo")}]</b> ${String(estado || "Nota")}${nota ? ": " + String(nota) : ""}`;
  await pd("POST", "notes", { content: contenido.slice(0, 2000), deal_id: id });
  return id;
}

async function guardarNota({ email, quien, estado, nota, dealId, sinPipedrive }) {
  const tk = await tokenGoogle("https://www.googleapis.com/auth/spreadsheets");
  const fila = [new Date().toISOString(), String(email || "").toLowerCase(),
    String(quien || "").slice(0, 40), String(estado || "").slice(0, 40), String(nota || "").slice(0, 500)];
  const cuerpo = { values: [fila] };
  try {
    await sheets(tk, rango(TAB_NOTAS, "A1") + ":append?valueInputOption=RAW&insertDataOption=INSERT_ROWS", "POST", cuerpo);
  } catch (e) {
    // primera vez: crear la pestaña con cabecera y reintentar
    await sheets(tk, ":batchUpdate", "POST", {
      requests: [{ addSheet: { properties: { title: TAB_NOTAS } } }],
    });
    await sheets(tk, rango(TAB_NOTAS, "A1") + "?valueInputOption=RAW", "PUT",
      { values: [["Fecha", "Email", "Quién", "Estado", "Nota"]] });
    await sheets(tk, rango(TAB_NOTAS, "A1") + ":append?valueInputOption=RAW&insertDataOption=INSERT_ROWS", "POST", cuerpo);
  }
  cache = { at: 0, data: null };
  if (!sinPipedrive) {
    try { fila.push(await notaPipedrive({ email, dealId, quien, estado, nota })); } catch (e) { fila.push(null); }
  }
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
        const s = autenticar(b.usuario, b.password);
        if (!s) return res.status(401).json({ error: "Usuario o contraseña incorrectos" });
        return res.status(200).json({ token: emitirToken(s.usuario), caduca: Date.now() + TTL_SESION, usuario: s.usuario, nombre: s.nombre, rol: s.rol });
      }
      const ses = sesion(b.token || req.headers["x-api-key"] || (req.headers.authorization || "").replace(/^Bearer /, ""));
      if (!ses) return res.status(401).json({ error: "Sesión caducada. Vuelve a entrar." });
      if (ses.usuario !== "equipo") b.quien = ses.nombre;   // firma siempre con el usuario que ha entrado
      if (b.op === "nota") {
        if (!b.email) return res.status(400).json({ error: "Falta el email del lead" });
        const fila = await guardarNota(b);
        return res.status(200).json({ ok: true, fila });
      }
      if (b.op === "mover") return res.status(200).json({ ok: true, ...(await moverTrato(b)) });
      if (b.op === "perder") return res.status(200).json({ ok: true, ...(await perderTrato(b)) });
      return res.status(400).json({ error: "Operación desconocida" });
    }
    const token = req.headers["x-api-key"] || (req.headers.authorization || "").replace(/^Bearer /, "");
    const s = sesion(token);
    if (!s) return res.status(401).json({ error: "Sin sesión" });
    const d = await datos();
    const solo = (req.query && req.query.solo) || "";                // ?solo=stock|leads|notas para integraciones
    if (solo && d[solo] !== undefined) return res.status(200).json({ generado: d.generado, [solo]: d[solo], sesion: s });
    return res.status(200).json({ ...d, sesion: s });
  } catch (e) {
    return res.status(500).json({ error: String(e.message || e).slice(0, 300) });
  }
};

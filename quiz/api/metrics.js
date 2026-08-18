// Métricas de email en vivo para el dashboard interno.
// Dos motores: campañas de Brevo (ABM templado + newsletter) y outbound frío
// de Smartlead. Agrega por envío y por semana ISO y devuelve un JSON compacto.
// Las claves viven solo en BREVO_API_KEY y SMARTLEAD_API_KEY.
//
// Nota de métrica: globalStats de Brevo devuelve ceros (bug conocido), así que
// todo se calcula sumando campaignStats por lista. "Aperturas" usa
// trackableViews (aperturas verificables, sin el inflado de Apple MPP) —
// es la cifra que venimos reportando al equipo. uniqueViews (con MPP) se
// devuelve aparte como aperturasBrutas.

let cache = { at: 0, data: null };
const TTL = 10 * 60 * 1000;

function tipoDe(nombre) {
  const n = (nombre || "").toLowerCase();
  if (n.startsWith("compraventa") || n.startsWith("plataformas elevación") ||
      n.startsWith("plataformas elevacion")) return "compraventa";
  return "newsletter";
}

// lunes de la semana ISO, en formato YYYY-MM-DD
function semanaDe(iso) {
  const d = new Date(iso);
  const dow = (d.getUTCDay() + 6) % 7; // 0 = lunes
  d.setUTCDate(d.getUTCDate() - dow);
  return d.toISOString().slice(0, 10);
}

async function brevo(path) {
  const r = await fetch("https://api.brevo.com/v3/" + path, {
    headers: { "api-key": process.env.BREVO_API_KEY, accept: "application/json" },
  });
  if (!r.ok) throw new Error("brevo " + r.status);
  return r.json();
}

// ── Outbound frío (Smartlead) ────────────────────────────────────────────
// Cada mensaje trae sent_time / open_time / reply_time, así que se agrupa por
// la semana en que SE ENVIÓ (cohorte), que es como se leen las tasas en frío.
async function smartlead() {
  const key = process.env.SMARTLEAD_API_KEY;
  if (!key) return null;
  const base = "https://server.smartlead.ai/api/v1";
  const r = await fetch(`${base}/campaigns?api_key=${key}`);
  if (!r.ok) throw new Error("smartlead " + r.status);
  const lista = await r.json();
  const campanas = Array.isArray(lista) ? lista : (lista.data || []);
  const salida = [], semanas = {};
  for (const c of campanas) {
    const a = await (await fetch(`${base}/campaigns/${c.id}/analytics?api_key=${key}`)).json();
    salida.push({
      id: c.id, nombre: c.name, estado: c.status,
      creada: (c.created_at || "").slice(0, 10),
      enviados: +a.sent_count || 0,
      empresas: +a.unique_sent_count || 0,
      totalLeads: +a.total_count || 0,
      aperturas: +a.unique_open_count || 0,
      clics: +a.unique_click_count || 0,
      respuestas: +a.reply_count || 0,
      rebotes: +a.bounce_count || 0,
      bajas: +a.unsubscribed_count || 0,
    });
    // desglose semanal a partir de los mensajes
    for (let off = 0; off < 2000; off += 100) {
      const st = await (await fetch(
        `${base}/campaigns/${c.id}/statistics?api_key=${key}&limit=100&offset=${off}`)).json();
      const filas = (st && st.data) || [];
      for (const f of filas) {
        if (!f.sent_time) continue;
        const k = semanaDe(f.sent_time);
        const w = semanas[k] || (semanas[k] = { semana: k, enviados: 0, aperturas: 0,
          clics: 0, respuestas: 0, rebotes: 0 });
        w.enviados++;
        if (f.open_time) w.aperturas++;
        if (f.click_time) w.clics++;
        if (f.reply_time) w.respuestas++;
        if (f.is_bounced) w.rebotes++;
      }
      if (filas.length < 100) break;
    }
  }
  return { campanas: salida, semanas: Object.keys(semanas).sort().map(k => semanas[k]) };
}

async function construir() {
  const envios = [];
  for (let offset = 0; offset < 500; offset += 50) {
    const d = await brevo(`emailCampaigns?limit=50&offset=${offset}&status=sent&sort=desc`);
    const lote = (d && d.campaigns) || [];
    for (const c of lote) {
      const st = { enviados: 0, entregados: 0, aperturas: 0, aperturasBrutas: 0,
                   clics: 0, clicadores: 0, bajas: 0, rebotes: 0 };
      for (const cs of ((c.statistics && c.statistics.campaignStats) || [])) {
        st.enviados += cs.sent || 0;
        st.entregados += cs.delivered || 0;
        st.aperturas += cs.trackableViews || 0;
        st.aperturasBrutas += cs.uniqueViews || 0;
        st.clics += cs.uniqueClicks || 0;
        st.clicadores += cs.clickers || 0;
        st.bajas += cs.unsubscriptions || 0;
        st.rebotes += (cs.hardBounces || 0) + (cs.softBounces || 0);
      }
      if (!st.enviados) continue;
      const fecha = (c.sentDate || c.scheduledAt || "").slice(0, 10);
      if (!fecha) continue;
      envios.push({
        id: c.id, nombre: c.name, asunto: c.subject, fecha,
        semana: semanaDe(c.sentDate || c.scheduledAt),
        tipo: tipoDe(c.name), ...st,
      });
    }
    if (lote.length < 50) break;
  }
  envios.sort((a, b) => (a.fecha < b.fecha ? 1 : -1));
  let frio = null;
  try { frio = await smartlead(); } catch (e) { frio = { error: String(e.message || e) }; }
  return { generado: new Date().toISOString(), envios, frio };
}

module.exports = async (req, res) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  if (req.method === "OPTIONS") return res.status(200).end();
  if (!process.env.BREVO_API_KEY) {
    return res.status(500).json({ error: "BREVO_API_KEY no configurada" });
  }
  try {
    if (!cache.data || Date.now() - cache.at > TTL) {
      cache = { at: Date.now(), data: await construir() };
    }
    res.setHeader("cache-control", "public, max-age=300");
    return res.status(200).json(cache.data);
  } catch (e) {
    if (cache.data) return res.status(200).json(cache.data); // servimos lo último bueno
    return res.status(502).json({ error: String((e && e.message) || e) });
  }
};

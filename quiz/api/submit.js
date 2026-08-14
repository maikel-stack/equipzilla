// Función serverless (Vercel): recibe las respuestas del quiz y envía el
// informe por email al equipo comercial vía Brevo.
// La API key de Brevo vive SOLO en la variable de entorno BREVO_API_KEY.

const TEAM = [
  { email: "david@equipzilla.com", name: "David" },
  { email: "andres@equipzilla.com", name: "Andrés" },
  { email: "maikel@equipzilla.com", name: "Maikel" },
];

const LABELS = {
  actividad: "Actividad",
  trabajo: "Qué necesita hacer",
  tipo: "Máquina que cree necesitar",
  hoy: "Cómo lo resuelve hoy",
  gasto: "Coste actual",
  uso: "Uso previsto",
  condiciones: "Condiciones",
  presupuesto: "Presupuesto",
  pago: "Pago",
  urgencia: "Urgencia",
  prioridades: "Prioridades",
  nombre: "Nombre",
  empresa: "Empresa",
  telefono: "Teléfono",
  zona: "Zona",
};

function esc(s) {
  return String(s || "").replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

function intentScore(a) {
  let s = 30;
  if ((a.urgencia || "").includes("Ya")) s += 30;
  else if ((a.urgencia || "").includes("menos de un mes")) s += 20;
  else if ((a.urgencia || "").includes("1-3")) s += 10;
  if ((a.hoy || "").includes("rechazamos")) s += 15;
  if ((a.hoy || "").includes("Alquilamos")) s += 10;
  if ((a.gasto || "").includes("3.000") || (a.gasto || "").includes("1.500")) s += 10;
  if (!(a.presupuesto || "").includes("Depende")) s += 5;
  return Math.min(100, s);
}

module.exports = async (req, res) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") return res.status(200).end();
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });

  const key = process.env.BREVO_API_KEY;
  if (!key) return res.status(500).json({ error: "BREVO_API_KEY no configurada" });

  const body = typeof req.body === "string" ? JSON.parse(req.body || "{}") : (req.body || {});
  const a = body.answers || {};
  const matches = Array.isArray(body.matches) ? body.matches : [];
  const score = intentScore(a);

  const rows = Object.keys(LABELS)
    .filter((k) => a[k])
    .map((k) =>
      `<tr><td style="padding:6px 10px;border-bottom:1px solid #EEF1F4;color:#667085;font-size:12px;white-space:nowrap">${LABELS[k]}</td>` +
      `<td style="padding:6px 10px;border-bottom:1px solid #EEF1F4;color:#14181C">${esc(a[k])}</td></tr>`)
    .join("");

  const reco = body.recomendacion
    ? `<div style="background:#17323A;color:#D7E4E4;border-radius:10px;padding:14px 16px;margin:12px 0;font-size:13px">` +
      `<div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#8FD3C0;font-weight:700;margin-bottom:6px">Recomendación mostrada</div>` +
      `${esc(body.recomendacion)}</div>`
    : "";

  const machinesHtml = matches.length
    ? `<p style="margin:14px 0 6px"><strong>Máquinas que le hemos enseñado como encaje:</strong></p><ul>` +
      matches.map((m) => `<li>${esc(m)}</li>`).join("") + `</ul>`
    : `<p style="margin:14px 0 6px;color:#B34A38"><strong>Sin encaje directo en stock</strong> — oportunidad de localizar máquina por encargo.</p>`;

  const html = `<div style="font-family:system-ui,sans-serif;font-size:14px;line-height:1.55;color:#14181C;max-width:620px">
<p style="font-size:16px"><strong>🎯 Nuevo proyecto de compra vía quiz</strong></p>
<p><strong>${esc(a.nombre || "?")}</strong>${a.empresa ? " · " + esc(a.empresa) : ""} · 📞 <strong>${esc(a.telefono || "—")}</strong>
· Buyer Intent: <strong>${score}/100</strong>${score >= 61 ? " 🔥" : ""}</p>
<table style="width:100%;border-collapse:collapse;font-size:13px;background:#fff;border:1px solid #D9DEE4">${rows}</table>
${reco}
${machinesHtml}
<p style="font-size:12px;color:#8A93A0">Enviado automáticamente por el quiz asesor de compra (Vercel).</p></div>`;

  const to = body.test ? [{ email: "maikel@equipzilla.com", name: "Maikel" }] : TEAM;
  const results = [];
  for (const t of to) {
    const r = await fetch("https://api.brevo.com/v3/smtp/email", {
      method: "POST",
      headers: { "api-key": key, "content-type": "application/json" },
      body: JSON.stringify({
        sender: { id: 10 },
        to: [t],
        subject: `🎯 Lead quiz · ${a.nombre || "?"}${a.empresa ? " (" + a.empresa + ")" : ""} · intent ${score}`,
        htmlContent: html,
        tags: ["quiz-asesor"],
      }),
    });
    results.push(r.status);
  }
  return res.status(200).json({ ok: true, sent: results });
};

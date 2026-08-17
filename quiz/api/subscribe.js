// Alta en el sistema de alertas de stock: guarda el contacto en Brevo
// (lista "Alertas Stock" #33) con su categoría de interés y presupuesto,
// y le envía un email de confirmación con lo que va a recibir.
// BREVO_API_KEY vive solo en la variable de entorno.

const LIST_ID = 33;

function esc(s) {
  return String(s || "").replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

module.exports = async (req, res) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") return res.status(200).end();
  if (req.method !== "POST" && req.method !== "GET") {
    return res.status(405).json({ error: "GET o POST" });
  }

  const key = process.env.BREVO_API_KEY;
  if (!key) return res.status(500).json({ error: "BREVO_API_KEY no configurada" });

  // GET = alta con un clic desde un email de campaña:
  // /api/subscribe?email={{contact.EMAIL}}&categoria=todas
  const isOneClick = req.method === "GET";
  const body = isOneClick
    ? (req.query || {})
    : (typeof req.body === "string" ? JSON.parse(req.body || "{}") : (req.body || {}));
  const email = String(body.email || "").trim().toLowerCase();
  if (isOneClick && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    return res.status(400).send("Falta el email. Escríbenos a clientes@equipzilla.com y te damos de alta.");
  }
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    return res.status(400).json({ error: "email inválido" });
  }
  const categoria = String(body.categoria || "todas").slice(0, 60);
  const precioMax = Number(body.precioMax) || 0;

  // alta/actualización del contacto en la lista de alertas
  const up = await fetch("https://api.brevo.com/v3/contacts", {
    method: "POST",
    headers: { "api-key": key, "content-type": "application/json" },
    body: JSON.stringify({
      email,
      updateEnabled: true,
      listIds: [LIST_ID],
      attributes: {
        NOMBRE: body.nombre || "",
        ALERTA_CATEGORIA: categoria,
        ALERTA_PRECIO_MAX: precioMax,
        ALERTA_TELEFONO: body.telefono || "",
      },
    }),
  });
  if (up.status >= 400) {
    return res.status(502).json({ error: "no se pudo guardar", status: up.status });
  }

  // confirmación al suscriptor
  await fetch("https://api.brevo.com/v3/smtp/email", {
    method: "POST",
    headers: { "api-key": key, "content-type": "application/json" },
    body: JSON.stringify({
      sender: { id: 10 },
      to: [{ email }],
      subject: "Alertas activadas — te avisamos de bajadas y novedades",
      htmlContent: `<div style="font-family:system-ui,sans-serif;font-size:14.5px;line-height:1.6;color:#14181C;max-width:520px">
<p>Hola${body.nombre ? " " + esc(body.nombre) : ""},</p>
<p>Ya estás dentro. A partir de ahora te avisaremos por email cuando:</p>
<ul><li>una máquina de tu interés (<strong>${esc(categoria)}</strong>) <strong>baje de precio</strong>;</li>
<li>entre en stock una <strong>máquina nueva similar</strong> a lo que buscas.</li></ul>
<p>Sin spam: solo cuando haya algo que de verdad te pueda interesar. Y si quieres algo ya, escríbenos por WhatsApp al <strong>606 836 581</strong>.</p>
<p>Un saludo,<br><strong>El equipo de Equipzilla</strong><br>
<span style="color:#667085;font-size:12.5px">911 238 750 · equipzilla.com</span></p></div>`,
      tags: ["alerta-alta"],
    }),
  });

  if (isOneClick) {
    res.setHeader("content-type", "text/html; charset=utf-8");
    return res.status(200).send(`<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Alertas activadas · Equipzilla</title></head>
<body style="margin:0;background:#F5F8F8;font-family:system-ui,sans-serif;color:#14181C">
<div style="max-width:460px;margin:60px auto;padding:0 18px;text-align:center">
<div style="font-size:44px">🔔</div>
<h1 style="font-size:24px;margin:10px 0 8px">Alertas activadas</h1>
<p style="font-size:15px;color:#4A5C5E;line-height:1.6">Te avisaremos en <b>${esc(email)}</b> cuando una máquina baje de precio o entre una nueva que encaje. Sin spam.</p>
<a href="https://equipzilla-quiz.vercel.app" style="display:inline-block;margin-top:18px;background:#387E7F;color:#fff;font-weight:700;padding:13px 22px;border-radius:10px;text-decoration:none">Ver el asesor de compra</a>
<p style="font-size:12px;color:#788B8D;margin-top:22px">Equipzilla · 911 238 750 · clientes@equipzilla.com</p>
</div></body></html>`);
  }
  return res.status(200).json({ ok: true });
};

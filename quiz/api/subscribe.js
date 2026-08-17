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
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") return res.status(200).end();
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });

  const key = process.env.BREVO_API_KEY;
  if (!key) return res.status(500).json({ error: "BREVO_API_KEY no configurada" });

  const body = typeof req.body === "string" ? JSON.parse(req.body || "{}") : (req.body || {});
  const email = String(body.email || "").trim().toLowerCase();
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

  return res.status(200).json({ ok: true });
};

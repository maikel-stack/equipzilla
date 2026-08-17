// Captura genérica de leads de los lead magnets (calculadora, guías, etc.).
// Recibe {origen, nombre, telefono, email, calculo?} → email al equipo,
// deal en Pipedrive y, para la calculadora, email al lead con su análisis.
// body.test = true → email solo a Maikel y sin deal (para pruebas).

const { pushToPipedrive } = require("./_lead.js");

const TEAM = [
  { email: "david@equipzilla.com", name: "David" },
  { email: "andres@equipzilla.com", name: "Andrés" },
  { email: "maikel@equipzilla.com", name: "Maikel" },
];

function esc(s) {
  return String(s || "").replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

function eur(n) {
  return Math.round(n).toLocaleString("es-ES") + " €";
}

const NOMBRES = {
  carr: "carretilla elevadora", plat: "plataforma elevadora", mini: "miniexcavadora",
  tele: "manipulador telescópico", exca: "excavadora", pala: "pala cargadora",
};

// Recalcula el análisis en el servidor (no nos fiamos de números del navegador).
function analiza(c) {
  const alq = Math.max(0, Number(c.alquilerMes) || 0);
  const meses = Math.min(12, Math.max(1, Number(c.mesesAno) || 0));
  const precio = Math.max(0, Number(c.precio) || 0);
  const anos = Math.min(8, Math.max(1, Number(c.anos) || 3));
  if (alq < 50 || precio < 1000) return null;
  const totalAlq = alq * meses * anos;
  const mant = precio * 0.06 * anos;
  const residual = precio * 0.5;
  const netoCompra = precio + mant - residual;
  return {
    tipo: NOMBRES[c.tipo] || "máquina", alq, meses, precio, anos,
    totalAlq, netoCompra, ahorro: totalAlq - netoCompra,
    beMeses: Math.ceil(netoCompra / alq),
  };
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
  const origen = String(body.origen || "web").slice(0, 40);
  const email = String(body.email || "").trim().toLowerCase();
  const nombre = String(body.nombre || "").slice(0, 80);
  const telefono = String(body.telefono || "").slice(0, 30);
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email) && telefono.replace(/\D/g, "").length < 9) {
    return res.status(400).json({ error: "hace falta email o teléfono" });
  }

  const a = body.calculo ? analiza(body.calculo) : null;
  const detalle = String(body.detalle || "").slice(0, 600);
  const resumen = a
    ? `Calculadora alquilar vs comprar — ${a.tipo}: paga ${eur(a.alq)}/mes de alquiler, ` +
      `${a.meses} meses/año, horizonte ${a.anos} años. Alquiler total ${eur(a.totalAlq)} vs ` +
      `compra neta ${eur(a.netoCompra)} → ${a.ahorro > 0 ? "AHORRO " + eur(a.ahorro) : "aún compensa alquilar"} ` +
      `(amortización ~${a.beMeses} meses).`
    : (detalle || `Lead de ${origen}.`);

  // aviso al equipo
  const teamHtml = `<div style="font-family:system-ui,sans-serif;font-size:14px;line-height:1.55;color:#14181C;max-width:620px">
<p style="font-size:16px"><strong>🧮 Lead de ${esc(origen)}</strong></p>
<p><strong>${esc(nombre || "?")}</strong> · 📞 <strong>${esc(telefono || "—")}</strong> · ✉️ ${esc(email || "—")}</p>
<div style="background:#17323A;color:#D7E4E4;border-radius:10px;padding:14px 16px;margin:12px 0;font-size:13px">${esc(resumen)}</div>
<p style="font-size:12px;color:#8A93A0">Enviado automáticamente (${esc(origen)} · Vercel).</p></div>`;
  const to = body.test ? [TEAM[2]] : TEAM;
  for (const t of to) {
    await fetch("https://api.brevo.com/v3/smtp/email", {
      method: "POST",
      headers: { "api-key": key, "content-type": "application/json" },
      body: JSON.stringify({
        sender: { id: 10 }, to: [t],
        subject: `🧮 Lead ${origen} · ${nombre || email || telefono}`,
        htmlContent: teamHtml, tags: ["lead-" + origen],
      }),
    });
  }

  // análisis por email al lead (solo calculadora)
  if (a && email) {
    const veredicto = a.ahorro > 0
      ? `<p style="font-size:17px"><strong>Comprando de ocasión ahorrarías ≈ ${eur(a.ahorro)}</strong> en ${a.anos} años, y amortizas la compra en unos <strong>${a.beMeses} meses</strong> de alquiler.</p>`
      : `<p>Con tu uso actual (${a.meses} meses/año) el alquiler aún compensa. Si el uso sube, la balanza cambia rápido — te avisamos si aparece una oportunidad.</p>`;
    await fetch("https://api.brevo.com/v3/smtp/email", {
      method: "POST",
      headers: { "api-key": key, "content-type": "application/json" },
      body: JSON.stringify({
        sender: { id: 10 },
        replyTo: { email: "david@equipzilla.com", name: "David Devis" },
        to: [{ email }],
        subject: `Tu análisis: alquilar vs comprar ${a.tipo}`,
        htmlContent: `<div style="font-family:system-ui,sans-serif;font-size:14.5px;line-height:1.65;color:#14181C;max-width:540px">
<p>Hola${nombre ? " " + esc(nombre) : ""},</p>
<p>Aquí tienes el análisis que has pedido con la calculadora de Equipzilla:</p>
<table style="border-collapse:collapse;width:100%;font-size:14px;margin:10px 0">
<tr><td style="padding:7px 10px;border-bottom:1px solid #EEF1F4;color:#667085">Seguir alquilando (${a.meses} meses/año × ${a.anos} años)</td><td style="padding:7px 10px;border-bottom:1px solid #EEF1F4;text-align:right"><b>${eur(a.totalAlq)}</b></td></tr>
<tr><td style="padding:7px 10px;border-bottom:1px solid #EEF1F4;color:#667085">Comprar de ocasión (precio + mantenimiento − valor de reventa)</td><td style="padding:7px 10px;border-bottom:1px solid #EEF1F4;text-align:right"><b>${eur(a.netoCompra)}</b></td></tr>
</table>
${veredicto}
<p>Tenemos ${a.tipo}s de ocasión revisadas en stock, con opción de garantía, contrato de mantenimiento y financiación. Si quieres, te preparo una selección con precios para tu caso: responde a este email o escríbeme al <b>606 836 581</b> (WhatsApp).</p>
<p>Un saludo,<br><b>David Devis</b><br><span style="color:#667085;font-size:12.5px">Equipzilla · 911 238 750 · equipzilla.com</span></p></div>`,
        tags: ["calculadora-analisis"],
      }),
    });
  }

  // deal en Pipedrive (no en modo test)
  let crm = false;
  if (!body.test) {
    crm = (await pushToPipedrive({
      nombre: nombre || email, telefono, email, resumen, origen,
    })).ok;
  }
  return res.status(200).json({ ok: true, crm });
};

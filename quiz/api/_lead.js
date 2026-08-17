// Registro automático de leads web en Pipedrive (pipeline Transaccional,
// etapa "Lead - Recibido"). Compartido por el quiz (/api/submit) y el
// chatbot (/api/chat). Nunca rompe la respuesta al usuario: si Pipedrive
// falla, el lead sigue llegando por email/WhatsApp.
// PIPEDRIVE_TOKEN vive solo en la variable de entorno.

const PIPELINE_ID = 6; // Transaccional
const STAGE_ID = 45;   // Lead - Recibido

async function pd(token, method, path, body) {
  const r = await fetch(
    `https://api.pipedrive.com/v1/${path}${path.includes("?") ? "&" : "?"}api_token=${token}`,
    {
      method,
      headers: { "content-type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
  return r.json().catch(() => ({}));
}

function esc(s) {
  return String(s || "").replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

// lead: {nombre, empresa, telefono, email, zona, resumen, maquinas, intent, origen}
async function pushToPipedrive(lead) {
  const token = process.env.PIPEDRIVE_TOKEN;
  if (!token || !lead.nombre) return { ok: false, reason: "sin token o nombre" };
  try {
    let phone = String(lead.telefono || "").replace(/[^+\d]/g, "");
    if (phone && !phone.startsWith("+")) phone = "+34" + phone;

    // dedupe: si el teléfono ya existe en Pipedrive, reutilizar la persona
    // (exact_match para no engancharse a coincidencias parciales)
    let personId = null;
    let created = false;
    if (phone.length >= 9) {
      const s = await pd(token, "GET",
        `persons/search?term=${encodeURIComponent(phone.replace("+34", ""))}&fields=phone&exact_match=true`);
      const hit = s && s.data && s.data.items && s.data.items[0];
      if (hit && hit.item) personId = hit.item.id;
    }
    if (!personId) {
      created = true;
      const p = await pd(token, "POST", "persons", {
        name: lead.nombre + (lead.empresa ? ` (${lead.empresa})` : ""),
        phone: phone ? [{ value: phone, primary: true, label: "work" }] : undefined,
        email: lead.email ? [{ value: lead.email, primary: true, label: "work" }] : undefined,
      });
      personId = p && p.data && p.data.id;
    }
    if (!personId) return { ok: false, reason: "no person" };

    const maquinas = Array.isArray(lead.maquinas) ? lead.maquinas : [];
    const d = await pd(token, "POST", "deals", {
      title: `Web ${lead.origen || "lead"} · ${lead.nombre}` +
        (maquinas.length ? ` · ${maquinas[0]}` : ""),
      person_id: personId,
      pipeline_id: PIPELINE_ID,
      stage_id: STAGE_ID,
    });
    const dealId = d && d.data && d.data.id;
    if (dealId) {
      await pd(token, "POST", "notes", {
        deal_id: dealId,
        content:
          `<b>Lead web (${esc(lead.origen || "?")})</b><br>` +
          (lead.intent != null ? `Buyer intent: <b>${lead.intent}/100</b><br>` : "") +
          (lead.zona ? `Zona: ${esc(lead.zona)}<br>` : "") +
          (phone ? `Tel: ${esc(phone)}<br>` : "") +
          (maquinas.length ? `Máquinas recomendadas: ${esc(maquinas.join(" · "))}<br>` : "") +
          (lead.resumen ? `<br>${esc(lead.resumen)}` : ""),
      });
    }
    return { ok: !!dealId, dealId, personId, personCreated: created };
  } catch (e) {
    return { ok: false, reason: String(e && e.message) };
  }
}

module.exports = { pushToPipedrive };

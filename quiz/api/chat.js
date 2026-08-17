// Chatbot asesor de compra (widget web): función serverless que conversa con
// el visitante usando Claude (Anthropic) con el playbook del Agente de Demanda
// y el catálogo real de máquinas como contexto. Cuando el visitante deja
// nombre + teléfono con interés claro, el modelo llama a la herramienta
// avisar_equipo y se envía el aviso por email (Brevo) y la ficha por WhatsApp
// (respond.io), igual que hace el quiz.
// Claves solo en variables de entorno: ANTHROPIC_API_KEY, BREVO_API_KEY,
// RESPONDIO_TOKEN, RESPONDIO_CHANNEL.

const Anthropic = require("@anthropic-ai/sdk");
const FALLBACK_MACHINES = require("./machines.json");

const MODEL = "claude-opus-5";
// data/machines.json en la rama por defecto: al actualizar el catálogo ahí,
// el bot lo recoge solo (sin redeploy). Si falla, usa la copia empaquetada.
const CATALOG_URL =
  "https://raw.githubusercontent.com/maikel-stack/equipzilla/refs/heads/claude/generate-bot-documentation-ELzal/data/machines.json";

const CAT = {
  mini: "miniexcavadora",
  exca: "excavadora",
  plat: "plataforma elevadora",
  carr: "carretilla elevadora",
  tele: "manipulador telescópico",
  pala: "pala cargadora",
};

const TEAM = [
  { email: "david@equipzilla.com", name: "David" },
  { email: "andres@equipzilla.com", name: "Andrés" },
  { email: "maikel@equipzilla.com", name: "Maikel" },
];

const FALLBACK_REPLY =
  "Ahora mismo no puedo atenderte por aquí 🙏 Escríbenos por WhatsApp al " +
  "**606 836 581** o llámanos al **911 238 750** y te ayudamos con tu máquina al momento.";

let catalogCache = { data: null, at: 0 };

async function getCatalog() {
  if (catalogCache.data && Date.now() - catalogCache.at < 15 * 60 * 1000) {
    return catalogCache.data;
  }
  try {
    const r = await fetch(CATALOG_URL, { signal: AbortSignal.timeout(4000) });
    if (r.ok) {
      const data = await r.json();
      if (Array.isArray(data) && data.length) {
        catalogCache = { data, at: Date.now() };
        return data;
      }
    }
  } catch (e) {
    /* sin red o timeout: copia empaquetada */
  }
  catalogCache = { data: FALLBACK_MACHINES, at: Date.now() };
  return FALLBACK_MACHINES;
}

function fmtEur(p) {
  return p.toLocaleString("es-ES") + " €";
}

function catalogText(machines) {
  return machines
    .map((m) =>
      `- ${m.n} · ${CAT[m.c] || m.c} · ${m.y} · ${m.s}` +
      (m.h ? ` · ${m.h.toLocaleString("es-ES")} h` : " · horas a confirmar") +
      ` · ${fmtEur(m.p)} + IVA` + (m.e ? " · eléctrica" : ""))
    .join("\n");
}

function systemPrompt(machines) {
  return `Eres el asesor de compra de maquinaria de ocasión de Equipzilla (equipzilla.com), empresa española de compraventa de maquinaria industrial y de construcción de segunda mano. Atiendes el chat de la web.

TU PAPEL
- Asesor experto en maquinaria + consultor de operaciones. Nunca un vendedor agresivo, un buscador de productos ni un formulario disfrazado de conversación.
- Diagnostica antes de recomendar: primero entiende qué necesita HACER el cliente (trabajos, terreno, alturas/pesos, interior o exterior, frecuencia de uso, cómo lo resuelve hoy y qué le cuesta), y solo después cruza eso con el stock.
- Nunca empieces preguntando "¿qué máquina buscas?". Si el cliente pide una máquina concreta, entiende primero el trabajo: a veces le encaja mejor otra cosa, y se lo explicas.

CÓMO CONVERSAS
- Español de España, tuteo, cercano y profesional. Mensajes CORTOS: 2-4 frases. UNA pregunta cada vez.
- Cuando tengas información suficiente (actividad, trabajo, condiciones, uso, presupuesto aproximado), recomienda 1-3 máquinas concretas del stock explicando por qué encajan. Usa **negrita** para nombres y precios. Sin tablas.
- Si preguntan por algo ajeno a maquinaria o a Equipzilla, redirige con amabilidad al tema.

REGLAS DE ORO
- SOLO recomiendas máquinas del stock listado abajo. Nunca inventes máquinas, precios, horas ni características. Si un dato no aparece en la ficha, di que lo confirmas con el equipo.
- Los precios siempre son "+ IVA".
- Opción de garantía, contrato de mantenimiento y financiación en casi todas nuestras unidades en venta.
- Si no hay encaje en stock, dilo con honestidad y ofrece localizar la máquina por encargo (lo hacemos habitualmente).
- Nunca menciones proveedores, orígenes de las máquinas ni empresas terceras.
- No hagas descuentos ni negocies precios: eso lo ve el cliente con el equipo comercial.

CONTACTO Y CIERRE
- Equipo comercial: WhatsApp 606 836 581 (David) · Teléfono 911 238 750 · clientes@equipzilla.com.
- Cuando detectes interés real, pide de forma natural el nombre y un teléfono ("¿te llamamos y lo vemos?").
- En cuanto tengas nombre + teléfono + un interés claro, llama UNA sola vez a la herramienta avisar_equipo. Después confirma al cliente que le contactamos en breve (mismo día laborable). No repitas el aviso en la misma conversación.

STOCK ACTUAL EQUIPZILLA (ocasión, precios + IVA):
${catalogText(machines)}`;
}

const TOOLS = [
  {
    name: "avisar_equipo",
    description:
      "Avisa al equipo comercial de Equipzilla de un lead del chat con interés real. " +
      "Úsala una sola vez por conversación, cuando ya tengas nombre y teléfono del cliente.",
    input_schema: {
      type: "object",
      properties: {
        nombre: { type: "string", description: "Nombre del cliente" },
        telefono: { type: "string", description: "Teléfono de contacto" },
        empresa: { type: "string", description: "Empresa, si la ha dicho" },
        zona: { type: "string", description: "Zona / provincia, si la ha dicho" },
        resumen: {
          type: "string",
          description:
            "Resumen del proyecto en 2-4 frases: qué necesita hacer, condiciones, uso, presupuesto y urgencia",
        },
        maquinas: {
          type: "array",
          items: { type: "string" },
          description: "Máquinas del stock recomendadas, por nombre",
        },
        urgencia: { type: "string", description: "Cuándo la necesita" },
      },
      required: ["nombre", "telefono", "resumen"],
    },
  },
];

function esc(s) {
  return String(s || "").replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

async function notifyTeam(lead) {
  const key = process.env.BREVO_API_KEY;
  const out = { email: false, wa: "no-phone" };
  const maquinas = Array.isArray(lead.maquinas) ? lead.maquinas : [];
  if (key) {
    const html = `<div style="font-family:system-ui,sans-serif;font-size:14px;line-height:1.55;color:#14181C;max-width:620px">
<p style="font-size:16px"><strong>💬 Lead del chatbot de la web</strong></p>
<p><strong>${esc(lead.nombre)}</strong>${lead.empresa ? " · " + esc(lead.empresa) : ""} · 📞 <strong>${esc(lead.telefono)}</strong>${lead.zona ? " · " + esc(lead.zona) : ""}${lead.urgencia ? " · ⏱ " + esc(lead.urgencia) : ""}</p>
<div style="background:#17323A;color:#D7E4E4;border-radius:10px;padding:14px 16px;margin:12px 0;font-size:13px">
<div style="font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#8FD3C0;font-weight:700;margin-bottom:6px">Resumen del proyecto</div>
${esc(lead.resumen)}</div>
${maquinas.length ? "<p><strong>Máquinas recomendadas en el chat:</strong></p><ul>" + maquinas.map((m) => `<li>${esc(m)}</li>`).join("") + "</ul>" : ""}
<p style="font-size:12px;color:#8A93A0">Enviado automáticamente por el asesor de compra (chatbot web).</p></div>`;
    let ok = false;
    for (const t of TEAM) {
      const r = await fetch("https://api.brevo.com/v3/smtp/email", {
        method: "POST",
        headers: { "api-key": key, "content-type": "application/json" },
        body: JSON.stringify({
          sender: { id: 10 },
          to: [t],
          subject: `💬 Lead chatbot · ${lead.nombre}${lead.empresa ? " (" + lead.empresa + ")" : ""}`,
          htmlContent: html,
          tags: ["chat-asesor"],
        }),
      });
      ok = ok || r.ok;
    }
    out.email = ok;
  }
  // Ficha por WhatsApp vía respond.io (mismo flujo que el quiz).
  const rt = process.env.RESPONDIO_TOKEN;
  const channel = Number(process.env.RESPONDIO_CHANNEL || 0);
  let phone = String(lead.telefono || "").replace(/[^+\d]/g, "");
  if (phone && !phone.startsWith("+")) phone = "+34" + phone;
  if (rt && channel && phone.length >= 9) {
    try {
      const ident = encodeURIComponent(`phone:${phone}`);
      const hdrs = { Authorization: `Bearer ${rt}`, "content-type": "application/json" };
      await fetch(`https://api.respond.io/v2/contact/create_or_update/${ident}`, {
        method: "POST", headers: hdrs,
        body: JSON.stringify({ firstName: lead.nombre || "Lead", lastName: lead.empresa || "", phone }),
      });
      await fetch(`https://api.respond.io/v2/contact/${ident}/tag`, {
        method: "POST", headers: hdrs, body: JSON.stringify(["chat-lead"]),
      });
      const ficha =
        `Hola${lead.nombre ? " " + lead.nombre : ""}, soy David de Equipzilla 👋 Gracias por hablar con nuestro asesor. ` +
        (maquinas.length
          ? `Esta es nuestra recomendación para tu proyecto:\n\n🔧 ${maquinas.join("\n🔧 ")}\n\nTe puedo enviar fotos, vídeo e informe de la unidad. ¿Te viene bien que hablemos?`
          : `He visto tu proyecto y te preparo opciones. ¿Te viene bien que hablemos?`);
      const r = await fetch(`https://api.respond.io/v2/contact/${ident}/message`, {
        method: "POST", headers: hdrs,
        body: JSON.stringify({ channelId: channel, message: { type: "text", text: ficha } }),
      });
      out.wa = r.ok ? "sent" : `error-${r.status}`;
    } catch (e) {
      out.wa = "failed";
    }
  }
  return out;
}

function cleanHistory(raw) {
  if (!Array.isArray(raw)) return null;
  const msgs = raw
    .filter((m) => m && (m.role === "user" || m.role === "assistant") && typeof m.content === "string")
    .slice(-40)
    .map((m) => ({ role: m.role, content: m.content.slice(0, 4000) }));
  if (!msgs.length || msgs[msgs.length - 1].role !== "user") return null;
  return msgs;
}

module.exports = async (req, res) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") return res.status(200).end();
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });

  const body = typeof req.body === "string" ? JSON.parse(req.body || "{}") : (req.body || {});
  const messages = cleanHistory(body.messages);
  if (!messages) return res.status(400).json({ error: "messages inválido" });

  if (!process.env.ANTHROPIC_API_KEY) {
    return res.status(200).json({ reply: FALLBACK_REPLY, contacted: false });
  }

  const client = new Anthropic();
  const system = [
    {
      type: "text",
      text: systemPrompt(await getCatalog()),
      // El prompt + catálogo es estable entre peticiones: cachearlo abarata
      // ~90% el coste de entrada de cada turno.
      cache_control: { type: "ephemeral", ttl: "1h" },
    },
  ];

  try {
    let contacted = false;
    let reply = "";
    // Bucle de tool-use acotado: como mucho un aviso al equipo + respuesta.
    for (let i = 0; i < 3; i++) {
      const response = await client.messages.create({
        model: MODEL,
        max_tokens: 700,
        // Chat comercial: prima la latencia, sin razonamiento extendido.
        thinking: { type: "disabled" },
        system,
        tools: TOOLS,
        messages,
      });

      const text = response.content
        .filter((b) => b.type === "text")
        .map((b) => b.text)
        .join("");
      if (text) reply = text;

      if (response.stop_reason !== "tool_use") break;

      messages.push({ role: "assistant", content: response.content });
      const results = [];
      for (const block of response.content) {
        if (block.type !== "tool_use") continue;
        let result = "Herramienta desconocida.";
        if (block.name === "avisar_equipo") {
          if (contacted) {
            result = "El equipo ya fue avisado en esta conversación. No lo repitas.";
          } else {
            const r = await notifyTeam(block.input || {});
            contacted = true;
            result = r.email
              ? "Aviso enviado al equipo comercial. Confirma al cliente que le contactamos en breve."
              : "No se pudo enviar el aviso automático. Da al cliente el WhatsApp 606 836 581 y el teléfono 911 238 750.";
          }
        }
        results.push({ type: "tool_result", tool_use_id: block.id, content: result });
      }
      messages.push({ role: "user", content: results });
    }

    return res.status(200).json({ reply: reply || FALLBACK_REPLY, contacted });
  } catch (e) {
    console.error("chat error", e && e.message);
    return res.status(200).json({ reply: FALLBACK_REPLY, contacted: false });
  }
};

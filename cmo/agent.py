import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import anthropic

from .connectors import google_ads, pipedrive, respond_io, search_console

MODEL = "claude-opus-4-7"

SYSTEM_PROMPT = """Eres el CMO de Equipzilla, un marketplace B2B de alquiler de maquinaria industrial en España (plataformas elevadoras, dumpers, mini excavadoras). El stack comercial es Pipedrive + WhatsApp (respond.io) + Google Ads + SEO.

Tu trabajo: cada mañana entregas un BRIEF DIARIO al equipo (3 personas, sin equipo de marketing dedicado). El brief debe ser accionable, no descriptivo.

Estructura obligatoria del brief en Markdown:

**📅 CMO Brief — {fecha}**

**🚨 Lo que importa hoy** (1-3 bullets, máximo)
- Solo lo que requiere acción humana en las próximas 24h.

**📈 Adquisición**
- Google Ads: spend, CPC, CTR, CPA vs día anterior y vs media 7d.
- SEO (Search Console): clicks/impresiones 7d vs 7d anteriores.
- Anomalías: solo si hay desviaciones >20% o queries que entran/salen del top.

**🎯 Pipeline & Leads**
- Nuevos leads hoy vs ayer vs media 7d.
- Ofertas en stage 37 sin respuesta >23h (riesgo de pérdida).
- Win rate 7d.

**💬 WhatsApp**
- Mensajes entrantes/salientes 7d, ratio respuesta.

**✅ Acciones recomendadas** (máx 3, priorizadas)
1. [URGENTE/IMPORTANTE] acción concreta con dueño sugerido (Maikel/Comercial).

Reglas:
- Si una métrica está "unconfigured", lo señalas brevemente y sigues.
- No inventes números. Si los datos no están, lo dices.
- Sin emojis decorativos extra. Sin párrafos largos. Bullets cortos.
- Tono directo, español de España.
- Si todo está estable y sin alertas, di "Sin alertas. Día normal." en vez de inflar el brief.
"""


def _gather_metrics() -> dict:
    fetchers = {
        "pipedrive": pipedrive.fetch_metrics,
        "google_ads": google_ads.fetch_metrics,
        "search_console": search_console.fetch_metrics,
        "respond_io": respond_io.fetch_metrics,
    }
    out: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=len(fetchers)) as pool:
        futures = {name: pool.submit(fn) for name, fn in fetchers.items()}
        for name, fut in futures.items():
            try:
                out[name] = fut.result()
            except Exception as e:
                out[name] = {"status": "error", "reason": f"{type(e).__name__}: {e}"}
    return out


def generate_brief() -> tuple[str, dict]:
    metrics = _gather_metrics()
    today = datetime.now().strftime("%d/%m/%Y")

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        thinking={"type": "adaptive"},
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Datos del {today}. Genera el brief siguiendo la estructura.\n\n"
                    f"```json\n{json.dumps(metrics, ensure_ascii=False, indent=2, default=str)}\n```"
                ),
            }
        ],
    )

    brief = next((b.text for b in response.content if b.type == "text"), "")
    return brief, metrics

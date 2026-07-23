# Campaña Google Ads — Maquinaria de construcción 2ª mano

Campaña de captación de leads para la compra de maquinaria de construcción de
segunda mano de Equipzilla (mercado España).

## Contenido

| Archivo | Qué es |
|---|---|
| `plan_campana.html` | Plan estratégico completo (abrir en navegador) |
| `equipzilla_campana_import.csv` | Importar en **Google Ads Editor**: 1 campaña, 7 grupos, 39 keywords, 7 RSA |
| `equipzilla_negativas.csv` | 35 palabras clave negativas |
| `build_campaign.py` | Genera y **valida** los CSV (límites de caracteres) |
| `create_campaign_api.py` | Crea la campaña **directamente por la Google Ads API** |
| `generate_refresh_token.py` | Genera el `refresh_token` de OAuth |
| `.env.example` | Plantilla de credenciales (copiar a `.env`) |

## Opción A — sin API (2 minutos)

1. Instala **Google Ads Editor** y conéctalo a la cuenta.
2. `Cuenta → Importar → Desde archivo` → `equipzilla_campana_import.csv`.
3. Importa también `equipzilla_negativas.csv`.
4. Fija presupuesto, ubicación (España), calendario y seguimiento de conversiones.
5. Añade extensiones y **Publica**.

## Opción B — por API

> ⚠️ Las credenciales van SOLO en `.env` (está en `.gitignore`). Nunca las
> pegues en chats ni las subas al repo. Si alguna se expuso, **regenérala**.

```bash
pip install google-ads google-auth-oauthlib
cp .env.example .env            # y rellena tus credenciales
python generate_refresh_token.py   # genera el refresh_token -> pégalo en .env
python create_campaign_api.py --dry-run   # comprueba sin crear nada
python create_campaign_api.py             # crea la campaña (EN PAUSA)
```

La campaña se crea **en pausa**: revísala en Google Ads, añade extensiones,
verifica el seguimiento de conversiones y actívala cuando esté todo correcto.

### Requisitos de la API
- **Developer token** aprobado (nivel Basic) en tu MCC.
- ID de cliente OAuth tipo *Desktop* (client_id + client_secret).
- Customer ID de la cuenta (10 dígitos sin guiones).

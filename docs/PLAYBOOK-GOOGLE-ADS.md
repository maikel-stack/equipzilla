# Playbook Google Ads — Compraventa Equipzilla

> Runbook para **medir y gestionar las campañas de Google Ads de compraventa** desde
> cualquier sesión (incluida la sesión **Brevo/CMO**). Las campañas ya están creadas y
> **vivas en la cuenta de Google Ads**; este documento es el puente para que otra
> sesión tenga contexto, insights y control sin reconstruir nada.

---

## 0) Cómo se conecta otra sesión a esto (arquitectura)

Dos piezas, nada de copiar secretos por el chat:

1. **Repo compartido = cerebro común.** Los scripts (`marketing/google-ads/`) y este
   playbook viajan por git. Cualquier sesión del repo hace `git pull` y los tiene.
2. **Credenciales = variables de entorno del ENTORNO compartido.** Todas las sesiones
   corren en el mismo entorno de Claude Code (`env_018usMNkWGxXeG7yy3urBEYk`). Si las
   claves de Google Ads se definen como **variables de entorno del entorno** (ajustes
   del entorno en la web de Claude Code), **todas las sesiones las heredan** — sin
   `.env` locales (que además se pierden al reiniciarse el contenedor).

> Regla de oro: **secretos SOLO en variables de entorno**, nunca en el repo, el chat
> ni los logs (misma norma que `PLAYBOOK-OUTBOUND-COMPRAVENTA.md`).

---

## 1) Cuentas e IDs (no son secretos)

| Recurso | ID |
|---|---|
| Cuenta Google Ads (compraventa) | **3057448284** — "Equipzilla - Compraventa" |
| Administrador (MCC) | **9812988446** — "Qualivo" |
| Google Merchant Center | **5828608786** |
| GA4 | propiedad "Equipzilla - GA4" (vinculada a la cuenta de Ads) |

> Nota: existe otra cuenta antigua ("Equipzilla - Corporate LAB", 9726619164) con
> campañas de alquiler y 2 campañas DSA corruptas que bloquean su API. La compraventa
> vive en la cuenta NUEVA (3057448284), creada limpia para esquivar ese bloqueo.

## 2) Variables de entorno requeridas (SOLO nombres)

Definir en los ajustes del entorno (nunca en el repo):

- `GOOGLE_ADS_DEVELOPER_TOKEN`  (nivel Explorer; permite leer y gestionar campañas,
  NO crear cuentas nuevas)
- `GOOGLE_ADS_CLIENT_ID`
- `GOOGLE_ADS_CLIENT_SECRET`
- `GOOGLE_ADS_REFRESH_TOKEN`  (OAuth; scope `https://www.googleapis.com/auth/adwords`)
- `GOOGLE_ADS_CUSTOMER_ID` = `3057448284`
- `GOOGLE_ADS_LOGIN_CUSTOMER_ID` = `9812988446`
- `GOOGLE_ADS_MERCHANT_ID` = `5828608786`

## 3) Estado actual de las campañas (todo EN MARCHA)

| Campaña | Tipo | Puja | Presupuesto |
|---|---|---|---|
| ES \| Compra \| Maquinaria Construccion 2a Mano | Búsqueda | Maximizar conversiones | 20 €/día |
| ES \| Shopping \| Maquinaria Construccion 2a Mano | Shopping | CPC manual | 20 €/día |

- **Búsqueda:** 7 grupos, 39 keywords, 7 RSA (aprobados), 35 negativas, 14 extensiones
  (4 enlaces, 6 destacados, 2 fragmentos, llamada, precios). España + Español.
- **Shopping:** feed de 15 máquinas vía Merchant Center 5828608786; grupo "todos los
  productos". España.
- **Conversiones (principales):** Reserva Completada, Formulario De Contacto Exitoso,
  Petición De Llamada Correcta. `purchase` = secundaria.

## 4) Insights (última lectura)

- **CPC medio ~0,24 €** — muy barato para el sector.
- **Shopping es el motor de volumen** y suele quedar `BUDGET_CONSTRAINED` con 20 €/día
  → si convierte, subirle presupuesto es la palanca #1.
- **Búsqueda** arranca en aprendizaje (`BIDDING_STRATEGY_LEARNING`) con CTR muy alto
  (~15%) pero poco volumen; darle 1–2 semanas antes de juzgar el CPA.
- El `purchase` es de bajo volumen; por eso las reservas/formularios/llamadas son las
  conversiones principales que guían la puja.

## 5) Medir Google Ads (para el panel de la sesión Brevo)

```bash
pip install google-ads
python marketing/google-ads/report_metrics.py --days 30          # tabla + JSON
python marketing/google-ads/report_metrics.py --days 7 --json    # solo JSON (para el panel)
```

Devuelve por campaña: impresiones, clics, coste, conversiones, CPA, CTR + totales.
El bloque JSON se puede volcar directamente en el "Panel de Campañas Compraventa".

## 6) Gestionar (cambios habituales)

Los scripts de creación/ajuste están en `marketing/google-ads/`
(`create_campaign_api.py`, `create_shopping_api.py`, `create_extensions_api.py`,
`feed_generator.py`, `build_campaign.py`). Para cambios puntuales (presupuesto, puja,
negativas) basta una llamada `CampaignService`/`CampaignBudgetService` con las mismas
credenciales. Ejemplos y textos validados: `build_campaign.py`.

## 7) Pendientes / vigilancia

- Regenerar y **resubir el feed** a Merchant Center cuando cambie el stock
  (`feed_generator.py`).
- Vigilar **términos de búsqueda** (Shopping se controla solo con negativas).
- Si Shopping convierte bien → subir su presupuesto; si Búsqueda sale de aprendizaje
  con buen CPA → subirla o pasar Shopping a **ROAS objetivo**.
- Las 2 campañas zombie de la cuenta vieja: pendiente que soporte de Google las borre.

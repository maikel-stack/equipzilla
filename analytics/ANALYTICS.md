# Plan de medición Equipzilla — Guía de implementación

Documento técnico para el dev del front. Acompaña al `equipzilla_events_plan.xlsx` (catálogo de eventos) y los CSV en esta carpeta.

- **Catálogo de eventos**: pestaña `Plan` del xlsx — 28 eventos, snippet por fila, punto de inserción.
- **Glosario**: pestaña `Parametros` — tipos y formato de cada parámetro.
- **Backlog**: pestaña `Backlog` — 10 tickets ANL-1..ANL-10 con criterios de aceptación.

---

## Reglas inviolables

1. **Ningún parámetro contiene PII**. Nada de email, teléfono o nombre crudos. Si se necesita identificador, se hashea (SHA-256 lowercase trim).
2. **Todo evento pasa por el helper `track()`**. Nunca llamar a `gtag` o `window.dataLayer.push` directamente desde un componente.
3. **Los eventos de conversión (`generate_lead`, `sign_up`) se duplican server-side** vía Measurement Protocol y Meta CAPI.
4. **Consent Mode v2** con default `denied` para región `ES`. Los tags publicitarios respetan el consentimiento.
5. **Nomenclatura GA4** (snake_case, eventos recomendados cuando aplica). Country, form_id, etc. son **parámetros**, no parte del nombre.

---

## 1. Setup único (ANL-1)

### 1.1 Helper `analytics.js`

```js
// src/lib/analytics.js
const hasWindow = typeof window !== 'undefined';

export const track = (event, params = {}) => {
  if (!hasWindow) return;
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push({
    event,
    ...params,
    _ts: Date.now(),
    country: params.country ?? window.__EZ_COUNTRY__ ?? 'es',
  });
};

export const sha256 = async (str) => {
  const buf = await crypto.subtle.digest(
    'SHA-256',
    new TextEncoder().encode(String(str).trim().toLowerCase()),
  );
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
};

export const identify = async ({ userId, email, userType }) => {
  if (!hasWindow) return;
  const emailHash = email ? await sha256(email) : undefined;
  window.dataLayer.push({
    event: 'user_identified',
    user_id: userId,
    user_properties: { user_type: userType, email_hash: emailHash },
  });
};

export const toGA4Item = (p) => ({
  item_id: p.sku ?? p.id,
  item_name: p.name ?? p.model,
  item_category: p.category,
  item_category2: p.subcategory,
  item_variant: p.variant,
  quantity: p.quantity ?? 1,
  price: p.price,
});

export const getGaClientId = () => {
  if (!hasWindow) return null;
  return document.cookie.match(/_ga=GA\d\.\d\.(\d+\.\d+)/)?.[1] ?? null;
};
```

### 1.2 Consent Mode v2

En `<head>` del documento, **antes** del snippet de GTM:

```html
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){ dataLayer.push(arguments); }
  gtag('consent', 'default', {
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    analytics_storage: 'denied',
    functionality_storage: 'granted',
    security_storage: 'granted',
    wait_for_update: 500,
    region: ['ES']
  });
  gtag('consent', 'default', {
    ad_storage: 'granted',
    ad_user_data: 'granted',
    ad_personalization: 'granted',
    analytics_storage: 'granted',
    region: ['MX']
  });
</script>
```

Al aceptar el banner de cookies (Cookiebot/Iubenda/propio) en EU:

```js
gtag('consent', 'update', {
  ad_storage: 'granted',
  ad_user_data: 'granted',
  ad_personalization: 'granted',
  analytics_storage: 'granted',
});
```

### 1.3 Carga de GTM

En `<head>`, **después** del bloque de Consent Mode:

```html
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-XXXXXXX');</script>
```

Y el `<noscript>` correspondiente justo tras `<body>`. Pedir al cliente el `GTM-XXXXXXX` real.

### 1.4 Detección de país y user properties

```js
// src/lib/country.js
export const detectCountry = () => {
  if (typeof window === 'undefined') return 'es';
  const fromUrl = window.location.pathname.match(/^\/(es|mx)\b/)?.[1];
  const fromTld = window.location.hostname.endsWith('.mx') ? 'mx' : null;
  const fromCookie = document.cookie.match(/ez_country=(es|mx)/)?.[1];
  return fromUrl ?? fromCookie ?? fromTld ?? 'es';
};

// En _app.jsx / app/layout.jsx, al inicio:
window.__EZ_COUNTRY__ = detectCountry();
```

---

## 2. Implementación por componente

> Las líneas exactas de cada `track()` están en la columna `Snippet JS` del xlsx. Aquí va el contexto adicional por componente.

### 2.1 Buscador home (ANL-2)

Componente: barra de búsqueda principal de la home.

```jsx
const handleSearch = async (query) => {
  const results = await fetchSearch(query);
  track('search', {
    search_term: query,
    results_count: results.length,
    search_location: 'home',
  });
  setResults(results);
};

const handleResultClick = (result, idx) => {
  track('select_search_result', {
    search_term: query,
    item_name: result.name,
    position: idx,
  });
  router.push(result.url);
};

const handleClear = () => {
  track('search_clear', { search_term: query });
  setQuery('');
  setResults([]);
};
```

### 2.2 Catálogo (ANL-3)

Componentes: páginas de listado (`/alquiler/maquinaria/*`, `/ubicaciones/*`), ficha de producto, tarjetas de producto, controles de filtro.

```jsx
// pages/alquiler/maquinaria/[slug].jsx
useEffect(() => {
  if (!products?.length) return;
  track('view_item_list', {
    item_list_id: category.slug,
    item_list_name: category.name,
    items: products.map(toGA4Item),
  });
}, [products]);

// ProductCard.jsx
<a onClick={() => track('select_item', {
  item_list_name: listName,
  items: [{ ...toGA4Item(product), index: idx }],
})} ...>

// pages/producto/[slug].jsx
useEffect(() => {
  track('view_item', { currency: 'EUR', items: [toGA4Item(product)] });
}, [product]);

// FilterControl.jsx — con debounce
const handleFilterChange = useDebouncedCallback((type, value) => {
  track('filter_apply', {
    filter_type: type,
    filter_value: value,
    item_list_name: listName,
  });
}, 300);
```

### 2.3 Calculadora (ANL-4)

```jsx
// CalculatorPage.jsx
useEffect(() => track('view_calculator'), []);

const onAddItem = (item) => {
  track('add_to_cart', {
    currency: 'EUR',
    value: item.price * item.quantity * item.days,
    items: [toGA4Item(item)],
    context: 'calculator',
  });
  addToSummary(item);
};

const onRemoveItem = (item) => {
  track('remove_from_cart', {
    currency: 'EUR',
    value: item.price * item.quantity * item.days,
    items: [toGA4Item(item)],
    context: 'calculator',
  });
  removeFromSummary(item);
};

const onSubmit = async (data) => {
  track('begin_checkout', { currency: 'EUR', value: cartTotal, items: cartItems });
  try {
    const res = await postLead({ ...data, ga_client_id: getGaClientId() });
    track('generate_lead', {
      form_id: 'calculator',
      lead_source: 'calculator',
      currency: 'EUR',
      value: cartTotal,
      items: cartItems,
    });
  } catch (err) {
    track('form_error', {
      form_id: 'calculator',
      error_code: String(err.status || 'unknown'),
    });
  }
};
```

### 2.4 Formularios contacto y onlyPhone (ANL-5)

Patrón aplicable a `ContactForm` (home, about), `LandingContactForm` (por país) y `OnlyPhoneForm`.

```jsx
const startedRef = useRef(false);

const onFirstFocus = () => {
  if (startedRef.current) return;
  startedRef.current = true;
  track('form_start', { form_id: 'contact', form_location: 'home' });
};

const onCancel = () => {
  track('form_cancel', { form_id: 'onlyphone', step: 'phone' });
  closeModal();
};

const onSubmit = async (data) => {
  try {
    await postContact({ ...data, ga_client_id: getGaClientId() });
    track('generate_lead', {
      form_id: 'contact',
      lead_source: 'contact_form',
      form_location: 'home',
    });
  } catch (err) {
    track('form_error', {
      form_id: 'contact',
      error_code: String(err.status),
    });
  }
};

// JSX:
<input onFocus={onFirstFocus} ... />
```

### 2.5 Login y registro (ANL-6)

```jsx
// LoginForm.jsx
const onSubmit = async (data) => {
  try {
    const { user } = await login(data);
    track('login', { method: 'email', user_id: user.id });
    await identify({ userId: user.id, email: data.email, userType: user.type });
  } catch (err) {
    track('login_error', { method: 'email', error_code: err.code });
  }
};

// SignUpModal.jsx
useEffect(() => {
  track('sign_up_view', { user_type: userType, source });
}, []);

const onSubmit = async (data) => {
  try {
    const { user } = await signup({ ...data, type: userType });
    track('sign_up', { method: 'email', user_type: userType, user_id: user.id });
    await identify({ userId: user.id, email: data.email, userType });
  } catch (err) {
    track('sign_up_error', { method: 'email', user_type: userType, error_code: err.code });
  }
};

const onCancel = () => track('sign_up_cancel', { user_type: userType, step: 'form' });
const onCloseSuccess = () => track('sign_up_cancel', { user_type: userType, step: 'success_modal' });
```

### 2.6 Carrito y checkout (ANL-7)

**Crítico**: la utility `addToCart` ya existe en el código pero no se llama desde los componentes. Hay que conectarla en los tres puntos: resumen visible, dropdown del header, vista móvil.

```jsx
// CartUtils.js — la utility existente
export const addToCart = (item) => {
  // ... lógica existente
  track('add_to_cart', {
    currency: 'EUR',
    value: item.price * item.quantity,
    items: [toGA4Item(item)],
    context: 'cart',
  });
};

// CheckoutPage.jsx
useEffect(() => {
  if (cartItems.length > 0) {
    track('begin_checkout', { currency: 'EUR', value: cartTotal, items: cartItems });
  }
}, []);

// ELIMINAR el tracking campo-a-campo. Sustituir por:
const startedRef = useRef(false);
const handleAnyFieldFocus = () => {
  if (startedRef.current) return;
  startedRef.current = true;
  track('form_start', { form_id: 'reservation' });
};

// Validación con Yup/Zod — en el callback de error:
const onValidationError = (field, error) => {
  track('form_field_error', {
    form_id: 'reservation',
    field_name: field,
    error_type: error.type,
  });
};

// TermsCheckbox.jsx
<input
  type="checkbox"
  onChange={(e) => {
    track('terms_toggle', { accepted: e.target.checked, form_id: 'checkout' });
    setAccepted(e.target.checked);
  }}
/>

// Botón final
const onSubmit = async () => {
  track('begin_checkout_submit', { currency: 'EUR', value: cartTotal, items: cartItems });
  try {
    await postReservation({ ...form, ga_client_id: getGaClientId() });
    track('generate_lead', {
      form_id: 'reservation',
      lead_source: 'reservation',
      currency: 'EUR',
      value: cartTotal,
      items: cartItems,
    });
  } catch (err) {
    track('form_error', { form_id: 'reservation', error_code: String(err.status) });
  }
};
```

### 2.7 WhatsApp + outbound + 404 (ANL-8)

```jsx
// WhatsAppWidget.jsx
const handleOpen = () => {
  setOpen(true);
  track('whatsapp_widget_open');
};

const handleCountry = (country) => () => {
  track('whatsapp_country_click', { country });
  // navegación a wa.me se ejecuta a continuación
};

// _app.jsx / layout.jsx — outbound delegation
useEffect(() => {
  const onClick = (e) => {
    const a = e.target.closest('a');
    if (!a?.href) return;
    try {
      const url = new URL(a.href);
      if (url.host !== window.location.host) {
        track('click_outbound', {
          outbound_url: a.href,
          destination_type: a.dataset.destType ?? 'external',
        });
      }
    } catch {}
  };
  document.addEventListener('click', onClick);
  return () => document.removeEventListener('click', onClick);
}, []);

// pages/404.jsx
useEffect(() => {
  track('page_not_found', {
    path: window.location.pathname,
    referrer: document.referrer,
  });
}, []);
```

---

## 3. Server-side (ANL-9)

Duplicar `generate_lead` y `sign_up` desde el backend. Inmuniza contra adblockers y mejora atribución de Meta y Google Ads.

### 3.1 Frontend: pasar `_ga` client_id al backend

```js
import { getGaClientId } from '@/lib/analytics';

await fetch('/api/leads', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ ...formData, ga_client_id: getGaClientId() }),
});
```

### 3.2 Backend: Measurement Protocol GA4

```js
// server/analytics/ga4.js
import crypto from 'node:crypto';

const sha = (s) => crypto.createHash('sha256')
  .update(String(s).trim().toLowerCase())
  .digest('hex');

export const sendGenerateLead = async ({ lead, gaClientId, userId }) => {
  const body = {
    client_id: gaClientId || crypto.randomUUID(),
    user_id: userId,
    events: [{
      name: 'generate_lead',
      params: {
        form_id: lead.formId,
        lead_source: lead.source,
        value: lead.estimatedValue,
        currency: lead.currency,
        country: lead.country,
        lead_category: lead.category,
        lead_duration_days: lead.durationDays,
      },
    }],
    user_data: {
      sha256_email_address: sha(lead.email),
      sha256_phone_number: sha(lead.phoneE164),
    },
  };

  await fetch(
    `https://www.google-analytics.com/mp/collect?measurement_id=${process.env.GA4_ID}&api_secret=${process.env.GA4_SECRET}`,
    { method: 'POST', body: JSON.stringify(body) },
  );
};
```

Validar en GA4: `Admin → Data Streams → Web stream → Measurement Protocol API secrets → DebugView`. En modo debug: añadir `?measurement_id=...&api_secret=...&debug_mode=1` y ver eventos en tiempo real.

### 3.3 Backend: Meta Conversions API

```js
// server/analytics/meta.js
export const sendMetaLead = async ({ lead, fbp, fbc, eventId }) => {
  const body = {
    data: [{
      event_name: 'Lead',
      event_time: Math.floor(Date.now() / 1000),
      event_id: eventId, // mismo id que el evento Pixel del front (deduplicación)
      action_source: 'website',
      event_source_url: lead.pageUrl,
      user_data: {
        em: [sha(lead.email)],
        ph: [sha(lead.phoneE164)],
        country: [sha(lead.country)],
        fbp,
        fbc,
        client_user_agent: lead.userAgent,
        client_ip_address: lead.ip,
      },
      custom_data: {
        currency: lead.currency,
        value: lead.estimatedValue,
        content_category: lead.category,
      },
    }],
  };

  await fetch(
    `https://graph.facebook.com/v19.0/${process.env.META_PIXEL_ID}/events?access_token=${process.env.META_CAPI_TOKEN}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    },
  );
};
```

Para deduplicar con el Pixel del front, generar un `event_id` único en el front, mandarlo en `fbq('track', 'Lead', {...}, { eventID: id })` y reutilizarlo en CAPI.

---

## 4. Configuración GTM y GA4 (ANL-10)

### 4.1 GTM — variables, triggers, tags

**Data Layer Variables** (una por parámetro):
`search_term`, `results_count`, `search_location`, `position`, `item_name`, `item_id`, `items`, `value`, `currency`, `form_id`, `form_location`, `lead_source`, `country`, `user_id`, `user_properties`, `method`, `user_type`, `error_code`, `error_message`, `accepted`, `field_name`, `error_type`, `item_list_id`, `item_list_name`, `filter_type`, `filter_value`, `outbound_url`, `destination_type`, `path`, `referrer`, `step`, `context`, `source`.

**Triggers** (Custom Event, uno por evento de la pestaña Plan):
28 triggers, nombre del trigger = nombre del evento.

**Tags**:

| Tag | Tipo | Disparo |
|---|---|---|
| GA4 — Configuration | GA4 Configuration (G-XXXX) | All Pages |
| GA4 — Event genérico | GA4 Event con `event_name = {{Event}}` y todos los params como variables | TODOS los triggers de eventos |
| Meta Pixel — base | Custom HTML con fbq('init') | All Pages |
| Meta Pixel — Lead | Custom HTML con fbq('track','Lead', {...}, { eventID: ... }) | `generate_lead` |
| Meta Pixel — CompleteRegistration | fbq('track','CompleteRegistration', ...) | `sign_up` |
| Meta Pixel — AddToCart | fbq('track','AddToCart', ...) | `add_to_cart` |
| Meta Pixel — InitiateCheckout | fbq('track','InitiateCheckout', ...) | `begin_checkout` |
| Google Ads — Conversion Lead | Google Ads Conversion Tracking | `generate_lead` |
| Google Ads — Conversion Signup | Google Ads Conversion Tracking | `sign_up` (solo si `user_type=partner`) |

### 4.2 GA4 — Key events y custom dimensions

**Key events (conversiones)**:
- `generate_lead`
- `sign_up` con condición `user_type = partner`
- (Opcional micro-conversión) `whatsapp_country_click`

**Custom dimensions** (Admin → Custom definitions):
| Dimension | Scope | Parámetro |
|---|---|---|
| Form ID | Event | form_id |
| Form Location | Event | form_location |
| Lead Source | Event | lead_source |
| Country | Event | country |
| Lead Category | Event | lead_category |
| User Type | User | user_type |
| Filter Type | Event | filter_type |
| Item List Name | Event | item_list_name |

**Custom metric**:
- Lead value: parámetro `value` (currency).

### 4.3 GA4 — Audiencias

| Audiencia | Definición |
|---|---|
| Carrito abandonado | Usuarios con `begin_checkout` AND NOT `generate_lead` en 24h |
| Alta intención no convertida | `view_calculator` AND `add_to_cart` AND NOT `generate_lead` en 7d |
| Partners en proceso | `sign_up_view` con `user_type=partner` AND NOT `sign_up` en 7d |
| Repetidores | Más de 1 `generate_lead` en 30d |

---

## 5. Validación y QA

### 5.1 GTM Preview Mode

1. En GTM: `Preview` → conectar al dominio.
2. En el navegador: ejecutar el flujo (búsqueda, calculadora, formulario…).
3. Comprobar en el panel de GTM Preview que **cada interacción dispara el evento esperado** y que las variables (`search_term`, `value`, `items`…) tienen los valores correctos.

### 5.2 GA4 DebugView

1. Instalar la extensión **Google Analytics Debugger** o añadir `?gtm_debug=x` a la URL.
2. En GA4: `Configure → DebugView`.
3. Cada evento debe aparecer en menos de 5s con todos sus parámetros.
4. Para server-side: misma DebugView muestra los eventos del backend (mandar con `debug_mode: 1`).

### 5.3 Checklist de PR (cada ticket)

- [ ] El evento se dispara exactamente UNA vez por interacción.
- [ ] Los parámetros obligatorios siempre están presentes.
- [ ] Ningún parámetro contiene email, teléfono o nombre crudo.
- [ ] Validado en GTM Preview.
- [ ] Validado en GA4 DebugView.
- [ ] Estado en el Sheet movido a `QA`.

---

## Anexo: contacto

Cualquier duda de **criterio de medición** (qué medir, cómo nombrar, qué params): contestarla con esta guía o preguntar al PO de marketing/data.
Cualquier duda de **implementación técnica** (dónde poner el `useEffect`, cómo evitar que dispare doble): decisión del dev del front.

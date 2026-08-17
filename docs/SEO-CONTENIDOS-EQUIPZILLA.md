# Sistema de SEO + Contenidos + Lead Magnets · Equipzilla Ocasión

> Adaptación del Playbook Qualivo de captación al negocio de compraventa de
> maquinaria de ocasión. Objetivo: tráfico orgánico cualificado → lead magnet →
> lead en Pipedrive → nurture → llamada de David.

---

## 0. Decisión previa: DÓNDE se publica (bloqueante)

El contenido SEO solo posiciona en un dominio con autoridad. `*.vercel.app` no sirve
para rankear. Opciones por orden de preferencia:

| Opción | Qué hace falta | SEO |
|---|---|---|
| **A. equipzilla.com/ocasion/guias/** (dentro del CMS actual) | Acceso al CMS de equipzilla.com | ★★★ hereda toda la autoridad |
| **B. Subdominio `ocasion.equipzilla.com`** → Vercel | 1 CNAME en el DNS (`cname.vercel-dns.com`) | ★★ autoridad parcial, control total |
| C. Seguir en vercel.app | nada | ✗ solo sirve para tráfico de pago/campañas |

**Pedido al equipo:** acceso al CMS de equipzilla.com **o** el CNAME. Con el CNAME
lo dejo todo montado sin depender de nadie (los lead magnets ya viven en ese proyecto).
También: alta en **Google Search Console** (verificación por DNS) para medir.

---

## 1. Pilares (hub-and-spoke)

**Pilar 1 · Comprar maquinaria de ocasión sin pillarse los dedos** (BOFU/MOFU)
La página madre: qué revisar, garantías, financiación, proceso Equipzilla.
→ Lead magnet: checklist de inspección + asesor de compra.

**Pilar 2 · ¿Alquilar o comprar?** (MOFU — nuestro ángulo diferencial)
El argumento comercial de Equipzilla convertido en contenido: cuándo compensa
comprar, con números. → Lead magnet: **calculadora alquilar vs comprar** (prototipo
ya construido: `quiz/alquilar-o-comprar-maquinaria.html`).

**Pilar 3 · Precios de maquinaria usada** (TOFU/MOFU — el imán de tráfico)
Guías de precios por categoría con datos reales de stock. Nadie publica precios
en este sector: ventaja brutal. → Lead magnet: alertas de precio.

**Pilar 4 · Vende tu máquina** (captación de OFERTA)
Guía de tasación + qué documentación preparar. → Lead magnet: **tasación express**.

## 2. Keyword map (1 keyword = 1 URL)

| Cluster | Keyword principal | Etapa | URL | Lead magnet en página |
|---|---|---|---|---|
| Pilar 2 | alquilar o comprar maquinaria | MOFU | /guias/alquilar-o-comprar-maquinaria | Calculadora |
| Precios | miniexcavadora segunda mano precio | TOFU | /guias/precio-miniexcavadora-segunda-mano | Alertas |
| Precios | carretilla elevadora segunda mano | TOFU | /guias/precio-carretilla-elevadora-segunda-mano | Alertas |
| Precios | plataforma elevadora usada precio | TOFU | /guias/precio-plataforma-elevadora-usada | Alertas |
| Precios | manipulador telescópico usado | TOFU | /guias/precio-manipulador-telescopico-usado | Alertas |
| Precios | excavadora usada precio | TOFU | /guias/precio-excavadora-usada | Alertas |
| Pilar 1 | comprar maquinaria segunda mano | BOFU | /guias/comprar-maquinaria-segunda-mano | Checklist + Asesor |
| Pilar 1 | qué revisar antes de comprar una miniexcavadora usada | MOFU | /guias/que-revisar-miniexcavadora-usada | Checklist |
| Pilar 1 | horas de una excavadora: cuántas son muchas | TOFU | /guias/horas-maquinaria-usada | Asesor |
| Pilar 1 | garantía maquinaria segunda mano | BOFU | /guias/garantia-maquinaria-ocasion | Asesor |
| Pilar 1 | financiar maquinaria segunda mano | BOFU | /guias/financiacion-maquinaria-ocasion | Simulador financiación |
| Marcas | kubota kx080 opiniones / ficha | MOFU | /guias/kubota-kx080-4-opiniones | Asesor + stock |
| Marcas | manitou plataforma articulada opiniones | MOFU | /guias/manitou-170-aetjl | Ficha + WhatsApp |
| Pilar 4 | vender maquinaria usada | oferta | /guias/vender-maquinaria-usada | Tasación express |
| Pilar 4 | cuánto vale mi excavadora | oferta | /guias/cuanto-vale-mi-maquina | Tasación express |
| Comparativas | carretilla eléctrica o diésel | TOFU | /guias/carretilla-electrica-o-diesel | Asesor |
| Comparativas | plataforma tijera o articulada | TOFU | /guias/plataforma-tijera-o-articulada | Asesor |

Validar volúmenes con Keyword Planner + Search Console en cuanto haya accesos;
el mapa está ordenado por (intención de compra × facilidad de rankear).

## 3. Capa GEO/AEO (aparecer en ChatGPT/Perplexity/AI Overviews)

- Cada artículo abre con **respuesta directa de 2-3 frases** a la keyword (formato snippet).
- `FAQPage` + `Product`/`Offer` schema en las guías de precio (precios reales = oro para los LLM).
- Tablas de precios con datos concretos y fecha ("actualizado agosto 2026") — los
  motores de respuesta citan fuentes con números frescos.
- Página "Quiénes somos / datos de Equipzilla" con señales de entidad (NAP, años, volumen).

## 4. Pipeline de producción (sistema, no artículos sueltos)

```
Cola de keywords (este doc, tabla §2)
   → borrador IA con plantilla fija (intro-respuesta, tabla de precios del stock
     real vía data/machines.json, secciones H2, FAQ, lead magnet incrustado, schema)
   → revisión humana (Maikel/David: 10 min por pieza, verificar datos técnicos)
   → publicar (CMS o subdominio) + interlinking al pilar
   → medir en Search Console → iterar títulos/CTR
```

- Ritmo: **2 piezas/semana** (1 de precios + 1 de pilar). 8 semanas = mapa completo.
- Los precios de las guías se generan del stock real (`data/machines.json`) →
  cuando cambia el stock, las guías se regeneran (script, mismo patrón que las alertas).
- Regla editorial: nunca inventar datos técnicos; specs solo de fichas reales;
  jamás mencionar proveedores/orígenes de las máquinas.

## 5. Menú de lead magnets (propuestas)

| # | Lead magnet | Capta | Estado | Impacto |
|---|---|---|---|---|
| 1 | **Tasación express "¿Cuánto vale tu máquina?"** (marca/modelo/año/horas → rango + oferta en 24h) | **Vendedores** (¡stock!) | propuesta | ★★★ alimenta el negocio entero |
| 2 | **Calculadora ¿Alquilar o comprar?** | Compradores MOFU | prototipo construido | ★★★ |
| 3 | Asesor de compra (quiz + chat) | Compradores | ✅ en producción | ★★★ |
| 4 | Alertas de bajada de precio | Compradores fríos→templados | ✅ en producción | ★★ |
| 5 | Checklist PDF "21 puntos antes de comprar de ocasión" | Compradores TOFU | propuesta | ★★ |
| 6 | Simulador de financiación (cuota/mes por máquina) | Compradores BOFU | propuesta | ★★ |
| 7 | Guía de precios 2026 por categoría (PDF con tabla real) | TOFU + prensa/citas | propuesta | ★ |

Los 7 comparten el mismo backend ya construido: `/api/lead` → email equipo +
WhatsApp + deal en Pipedrive con `origen` + nurture por tag.

## 6. Nurture (secuencia tipo, 5 emails · trigger = tag del lead magnet)

1. **Inmediato** — entrega del recurso (análisis/checklist/tasación) + qué hace Equipzilla.
2. **Día 2** — caso práctico: "cómo X ahorró Y comprando en vez de alquilar" (o el proceso de inspección).
3. **Día 5** — objeción principal: "¿y si sale rana?" → garantía, inspección presencial, financiación.
4. **Día 8** — prueba social + stock actual de su categoría (dinámico).
5. **Día 12** — CTA directa: llamada de 10 min con David (link a calendario) o WhatsApp.
   Sale de la secuencia si responde, agenda o compra. Se monta en Brevo Automation
   (UI) con los tags ya existentes: `quiz-asesor`, `chat-asesor`, `alerta-alta`, `calculadora`.

## 7. Medición

- Search Console (impresiones/clics por URL) + Brevo (leads por tag/origen) +
  Pipedrive (deals por `origen`) → fila diaria en el sheet de métricas existente.
- KPI del sistema: **leads/semana por origen** y **deals creados** (no tráfico bruto).

---
*Siguiente acción bloqueante: CNAME o acceso CMS + Search Console. Todo lo demás es ejecutable ya.*

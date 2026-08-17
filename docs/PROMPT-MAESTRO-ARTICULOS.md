# Prompt Maestro · Sistema de artículos SEO → Lead Magnet → Lead (Equipzilla)

> Estándar editorial obligatorio para TODO artículo del sistema de contenidos.
> Origen: playbook Qualivo. Este archivo = prompt maestro + contexto Equipzilla relleno.
> Uso: al producir un artículo nuevo, seguir el proceso completo (estrategia → lead
> magnet → SEO → artículo → CTA → diseño → interlinking → CRO → nurturing).

## 1. Contexto del negocio (relleno para Equipzilla)

- **Empresa:** Equipzilla (equipzilla.com) · Barcelona · 911 238 750
- **Qué vende:** maquinaria industrial y de construcción de ocasión, revisada, con
  inspección y prueba presencial, opción de garantía, contrato de mantenimiento y
  financiación en casi todas las unidades. También localización por encargo y compra
  de máquinas usadas (tasación).
- **Cliente ideal (ICP):** pymes españolas que usan maquinaria a diario — construcción,
  obra civil, demolición, movimiento de tierras, logística/almacén, industria,
  mantenimiento, agrícola. Decide el dueño o el jefe de obra/operaciones. Hoy alquilan,
  tienen máquina vieja o rechazan trabajos.
- **Problemas del cliente:** (1) el alquiler recurrente se come el margen; (2) miedo a
  comprar usado "y que salga rana" — horas falseadas, averías caras, sin garantía;
  (3) no sabe qué máquina/configuración encaja con su trabajo.
- **Deseos:** (1) dejar de tirar dinero en alquiler; (2) comprar con seguridad
  (garantía, historial, factura); (3) acertar de tamaño/tipo a la primera; (4) pagar
  cómodo (financiación).
- **Diferenciadores:** (1) publicamos precios reales — nadie más lo hace; (2) inspección
  y prueba presencial + horas certificadas; (3) garantía + contrato de mantenimiento +
  financiación; (4) asesoramos por el trabajo, no por el catálogo (asesor IA + David).
- **Tono:** experto cercano, español de España, tuteo, directo, cero humo. Nunca
  mencionar proveedores/orígenes de las máquinas. Nunca inventar datos técnicos.
- **Objetivo comercial:** leads de compra (y tasaciones = stock) → deal en Pipedrive →
  llamada/WhatsApp de David.

## 2. Reglas del sistema (resumen operativo)

1. **Nada de artículos por keyword suelta**: antes de escribir → search intent, perfil
   del lector, fase TOFU/MOFU/BOFU, siguiente paso lógico y lead magnet asociado.
2. **Respuesta rápida** de 40-80 palabras arriba (para Google + IA/AEO).
3. Estructura editorial: H2/H3, tablas con datos reales del stock, pasos numerados,
   bloques de **Error común** y **Consejo del asesor**, caso práctico con números.
4. **Lead magnet como continuación natural** con la fórmula: "Ahora ya sabes X. Si
   quieres Y sin empezar de cero, hemos preparado Z." CTA que vende el resultado.
   Lead magnets disponibles: alertas de precio (por categoría), calculadora
   alquilar-vs-comprar, asesor de compra (quiz/chat), checklist de inspección,
   tasación express.
5. Diseño editorial premium: Archivo + IBM Plex Sans, mucho blanco, ancho ~70ch,
   jerarquía clara, componentes del design system de `scripts/gen_guias.py`.
6. Claridad > longitud. Sin "hoy en día", sin relleno, sin keyword stuffing.
7. FAQ con schema FAQPage; datos de precios siempre del stock real
   (`data/machines.json`) con fecha de actualización.
8. Interlinking: cada satélite enlaza a su pilar y al lead magnet; los pilares
   enlazan a los satélites.
9. CRO: el CTA aparece después de haber dado valor (tras la tabla o el framework),
   nunca antes; segundo CTA al final.
10. Nurturing: definido en docs/SEO-CONTENIDOS-EQUIPZILLA.md §6 (5 emails por tag).

## 3. Prompt maestro completo (verbatim)

<details><summary>Desplegar el prompt maestro original</summary>

Actúa como un estratega senior de Growth Marketing, SEO, CRO, copywriting y diseño
editorial. Tu trabajo no es simplemente escribir artículos. Tu objetivo es crear
artículos que atraigan tráfico cualificado, generen confianza y conviertan lectores
en leads, haciendo que cada artículo tenga asociado un lead magnet específico.

[El prompt completo con las 18 secciones — contexto, principio fundamental, análisis
previo, investigación, estructura, contenido, autoridad, SEO on-page, AEO/GEO, lead
magnet, diseño del lead magnet, transición, CTA final, diseño del artículo, imágenes,
interlinking, conversión, output final — tal y como lo entregó Maikel el 17/08/2026.
Ante cualquier duda de interpretación, prevalece la regla: intención → problema →
solución → lead magnet → siguiente paso comercial. Si un tema no tiene oportunidad
de captación, decirlo y proponer alternativa antes de escribir.]

</details>

# Google Ads · estructura actual, diagnóstico y plan al subir presupuesto

Fecha: 11/09/2026 · Cuenta 3057448284 · Datos: últimos 30 días (12/08-10/09)

## 1. Cómo está hoy

| | Search «ES · Compra» | Shopping |
|---|---|---|
| Presupuesto | 20 €/día · Maximizar conversiones | 20 €/día · CPC manual |
| Gasto 30 d | 540 € | 542 € |
| Clics · CPC | 638 · 0,85 € | 2.625 · 0,21 € |
| Conversiones medidas | 3 (importadas de GA4) | 1 |
| Cuota de impresiones | 13,6 % | 35,2 % |
| Perdida por presupuesto | 21,6 % | **54,7 %** |
| Perdida por ranking | **64,8 %** | 10,1 % |
| Geo | España, «presencia o interés» | España, «presencia o interés» |
| Dispositivo | 87 % de los clics en móvil | — |

Search tiene 1 campaña con 12 grupos: 7 activos con anuncio (genérico, mini, excavadoras, minicargadoras, dumpers, rodillos, marcas), 2 activos **sin anuncio** (retro, plataformas: 0 impresiones desde el 09/09), 2 pausados sin página (carretillas, telescópicos). Todos los anuncios son «AVERAGE» salvo marcas («GOOD»), y 4 apuntan a una URL que redirige (308).

## 2. Diagnóstico: por qué no es la mejor estructura

1. **Sin medición no hay estructura que valga.** La etiqueta AW-18345032067 lleva 0 conversiones en 30 días: los formularios de equipzilla.com no la disparan (solo cargan GTM). La puja «Maximizar conversiones» está aprendiendo de 3 conversiones importadas de GA4 en un mes: es puja a ciegas. Es la causa de la pérdida del 65 % de impresiones por ranking.
2. **El grupo genérico se come el 41 % del gasto de Search** (223 €) con la keyword «maquinaria construccion segunda mano» en nivel de calidad 1 y «maquinaria obra publica segunda mano» con 141 clics y 0 conversiones. Es tráfico de curiosos que compite con los grupos de categoría, que sí tienen CTR del 13-21 %.
3. **Una sola campaña de Search = un solo presupuesto.** No se puede dar más dinero a minis y excavadoras (lo que se vende) sin dárselo también al genérico.
4. **Los anuncios no coinciden con la búsqueda.** Dumpers, rodillos, minicargadoras y genérico aterrizan en la misma página general. Google penaliza la relevancia (ranking) y el usuario no ve su máquina.
5. **Shopping está estrangulado**: pierde el 55 % de impresiones por presupuesto con clics a 0,21 €. Es el tráfico más barato de la cuenta, pero solo con una parte del stock en el feed y sin saber si convierte.
6. **Geo «presencia o interés»** deja entrar búsquedas desde fuera de España sobre maquinaria en España. Con presupuesto pequeño, sobra.

## 3. Estructura propuesta (para 60-120 €/día)

```
SEARCH · Movimiento de tierras      30 €/d   mini · excavadoras · retro · minicargadoras · dumpers · rodillos
SEARCH · Elevación y manipulación   20 €/d   plataformas (ya) · carretillas y telescópicos (cuando exista la página)
SEARCH · Marcas                     10 €/d   kubota · doosan · develon · bobcat · manitou · jlg · genie · haulotte · hyster
SEARCH · Genéricas (control)         5 €/d   «maquinaria construcción segunda mano» solo exacta, CPC máx. 0,40 €
SHOPPING · Stock completo           30 €/d   grupos de producto por categoría, puja por categoría
REMARKETING (fase 2)                 5 €/d   visitantes de /compra/ y del stock, 30 días
```

Reglas de cada grupo: 1 anuncio adaptable con 15 títulos y 4 descripciones que nombren la categoría, «desde X €», garantía e inspección; URL final a la página de su categoría (comprobada con 200 y título correcto); extensiones de llamada (David), enlaces de sitio (stock, guías, WhatsApp) y texto destacado; geo solo presencia; horario con puja +20 % de 8 a 19 h laborables; móvil como prioridad de diseño de landing.

Puja: mientras no haya 30 conversiones/mes medidas, **Maximizar clics con CPC máximo 0,60 €** en Search. Cuando entren las conversiones offline (oferta enviada, operación ganada) y la etiqueta web funcione, pasar a **Maximizar conversiones con CPA objetivo 50 €** y, con ventas, a valor de conversión.

## 4. Plan por fases

| Fase | Cuándo | Presupuesto | Qué se hace | Salida |
|---|---|---|---|---|
| 0 · Medir | Semana 14/09 | 40 €/d (20+20) | Etiqueta en GTM (Lorenzo), Data Manager API (Maikel), conversiones offline subiendo, anuncios en retro y plataformas, URLs, geo, negativas | Conversiones reales en la cuenta |
| 1 · Reestructurar | Semana 21/09 | 70 €/d | 3 campañas de Search por categoría + Shopping 30 €/d con el feed completo; pausar genérico salvo exacta | CPL por categoría |
| 2 · Escalar | Octubre | 100-120 €/d | Subir lo que tenga CPL < 60 €, activar carretillas/telescópicos con sus páginas, remarketing, CPA objetivo | 1-2 leads/día medidos |

Estimación con los datos actuales (no promesa): Search a 40 €/d son ~50 clics/día; con un 2-3 % de conversión en landing salen 1-1,5 leads/día, 25-40 leads/mes a 35-50 € cada uno. Shopping a 30 €/d son ~140 clics/día de los que hoy no sabemos la conversión: se mide en fase 0.

## 5. Ejecución

`scripts/ads_ajustes.py` aplica la fase 0 (anuncios retro y plataformas, URLs, geo, 20 negativas). Su ejecución desde las sesiones de Claude está bloqueada por el clasificador de seguridad («Modify Shared Resources»); se necesita una regla de permisos para `python3 scripts/*` o que lo ejecute Andrés en local con las credenciales. La reestructura (fase 1) se escribirá como `scripts/ads_reestructura.py` con modo `--prueba` para revisarla antes de aplicarla.

# Riesgo: que Google deje de rastrear o indexar equipzilla.com entero (SEO · 23/09/2026)

Pedido por el Director el 23/09 tras ver que /guias/ de ocasion pasó de «descubierta» a
«desconocida para Google». Tres preguntas: qué pasaría, qué señales lo anticipan y qué haría
falta para revertirlo. Todo con datos de Search Console de hoy (propiedad sc-domain:equipzilla.com).

## 1. Dónde estamos hoy (evidencia, no hipótesis)

**Rastreo del sitio principal: funciona.** La home se rastreó el 20/09, /maquinaria/plataformas-
elevadoras/madrid el 10/09, la página de carretillas usadas el 02/09; todas «Enviada e indexada».
Googlebot recibe el mismo HTML que un navegador (200, byte a byte), sin X-Robots-Tag, con
`meta robots index,follow`, robots.txt correcto. Sitemap-0 y sitemap-1 leídos el 17/09 sin errores.

**Visibilidad: cayendo desde el 17/09, sin perder clics.**

| día | impresiones | posición media | consultas distintas | clics |
|---|---|---|---|---|
| 15/09 | 5.265 | 21,2 | 1.700 | 74 |
| 16/09 | 4.946 | 19,5 | 1.500 | 72 |
| 17/09 | 3.796 | 14,8 | 1.136 | 78 |
| 18/09 | 3.636 | 16,4 | 1.211 | 83 |
| 19/09 | 2.915 | 17,6 | 1.168 | 33 |
| 20/09 | 2.986 | 16,7 | 1.131 | 49 |

Semana 15-21/09: 26.864 impresiones frente a 40.163 la anterior (−33 %), con las mismas
~1.400 páginas recibiendo impresiones y los clics estables. La posición media *mejora* de 25 a
15 porque desaparecen las impresiones profundas (posición 40-80): las páginas de alquiler por
ciudad (/ubicaciones/ pasa de 28.225 a 18.664 impresiones semanales; /maquinaria/ de 9.231 a
5.833). Es decir: Google ha dejado de mostrar el sitio para la cola larga en la que ya
aparecía mal, no ha dejado de rastrearlo. De momento el negocio no lo nota (clics iguales),
pero es la primera vez que el dominio entero se mueve a la vez, y coincide con el día 14 del
hackeo del blog.

**Dos subdominios en mal estado dentro de la misma propiedad:**
- blog.equipzilla.com sirve spam de casino a Googlebot en **cualquier URL** (probado: una
  URL inventada devuelve 200 con el título «DEWI138 Portal Game Arcade»). La home spam enlaza a
  46 URL de spam en el propio blog y a 10 dominios externos. Google ya ha desindexado la home
  del blog («Rastreada, no indexada» desde el 03/09). Es la definición exacta de «sitio
  hackeado» en las políticas de spam de Google.
- ocasion.equipzilla.com: 41 URL en sitemap, 1 indexada, y /guias/ descartada tras 13 días sin
  rastreo. Sin enlaces desde el dominio principal.

## 2. Qué pasaría si Google dejara de rastrear o indexar el dominio

Tres escenarios, de menos a más grave:

1. **Reducción de presupuesto de rastreo** (ya en marcha en ocasion). Las páginas nuevas o
   cambiadas tardan semanas en reflejarse; las secciones sin enlaces no entran nunca. Síntoma:
   fechas de último rastreo que se alejan; sitemaps «leídos» pero con 0 indexadas.
2. **Acción manual por «sitio hackeado» o «spam».** Google puede aplicarla a la URL, al
   subdominio o a *toda la propiedad*. Si es a la propiedad: equipzilla.com desaparece de los
   resultados o pierde la mayor parte de posiciones en cuestión de días. Con 1.584 clics en
   28 d y 103 en /compra/, es todo el canal orgánico y parte de los leads de Ads (las páginas de
   destino siguen existiendo, pero el Quality Score y la confianza del dominio caen). Google
   avisa por correo al propietario de la propiedad y lo muestra en Search Console → Seguridad y
   acciones manuales. **La API no expone esa pantalla: hay que mirarla a mano.**
3. **Desindexación algorítmica del dominio** (sin aviso). Ocurre cuando el sistema de spam
   clasifica el sitio como comprometido. Se parece a lo del 17/09 pero llegando a las
   posiciones 1-20 y a los clics. Se revierte solo cuando la causa desaparece y Google vuelve a
   rastrear, y tarda semanas o meses.

Lo que **no** pasaría: que el sitio deje de funcionar para los usuarios directos, Ads o email.
Solo se pierde el descubrimiento orgánico.

## 3. Señales de alerta (las miro cada día; las tres primeras están en la API)

| señal | umbral | hoy |
|---|---|---|
| Clics del dominio, media 7 d | −30 % frente a la semana anterior | 394 vs 373: estable |
| Impresiones del dominio, media 7 d | −30 % | −33 % (17/09): **activada** |
| Último rastreo de la home | > 7 días | 20/09: bien |
| Consultas de marca («equipzilla») | pierden la posición 1 | por comprobar mañana con filtro de marca |
| Search Console → Seguridad y acciones manuales | cualquier aviso | **solo se ve en la interfaz: Maikel** |
| Correo de Google a la cuenta propietaria | «Se ha detectado…» | Maikel |

## 4. Qué haría falta para revertirlo (por orden, y quién)

1. **Limpiar el blog o apagarlo hoy** (Lorenzo). Mientras sirva spam, cualquier arreglo es
   temporal. Opciones en 15 minutos: 503 en todo blog.equipzilla.com, o quitar el CNAME. En
   1-2 h: restaurar WordPress desde copia previa al 03/09, actualizar core y plugins, cambiar
   contraseñas, borrar usuarios admin desconocidos, revisar wp-config y .htaccess.
2. **Comprobar en Search Console → Seguridad y acciones manuales** (Maikel, 2 minutos). Si hay
   aviso: tras limpiar, «Solicitar revisión». Google contesta en días o semanas.
3. **Sitemaps y canonicals de equipzilla.com** (Lorenzo, 1 h): sitemaps con las URL /usada/
   (hoy 442 antiguas y 0 nuevas), canonical sin www, 301 de la errata de telescópicos. Sin esto,
   Google gasta rastreo en redirecciones.
4. **Enlaces desde equipzilla.com a ocasion** (Lorenzo, 15 min, docs/SEO-ENLACES-INTERNOS-OCASION.md).
5. **Reenviar sitemaps y solicitar indexación** de las 10 URL de más valor (yo + Maikel).
6. **Si hubo acción manual sobre la propiedad**: además de lo anterior, documento de
   reconsideración con lo hecho (fechas, capturas), enviado desde Search Console. Yo lo redacto.

Coste de no hacer nada: el escenario 2 o 3 puede saltar cualquier día; la señal del 17/09 ya
es el dominio entero moviéndose a la vez.

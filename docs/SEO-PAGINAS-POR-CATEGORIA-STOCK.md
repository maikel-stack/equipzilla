# Páginas de compra que pediría para las categorías con stock (SEO · 22/09/2026)

Cruce de tres fuentes: stock real (`data/machines.json`, 41 máquinas), páginas /compra/ que
existen en equipzilla.com (sitemaps sitemap-0/1.xml, 850 URL de /compra/) y Search Console
28 d (24/08–20/09). Sin inventar cifras: donde no hay datos, se dice.

## 0. Antes de pedir páginas nuevas: tres defectos en las que ya existen (Lorenzo)

1. **Migración /compra/maquinaria/ocasion/ → /compra/maquinaria/usada/ a medias.**
   Desde el 28/08 las URL de ocasión redirigen con 308 a /usada/. El cambio se completó
   hacia el 06/09. Los sitemaps siguen listando 442 URL /ocasion/ y ninguna /usada/.
   Impresiones diarias de la sección: 500-700 con /ocasion/ (julio-agosto) frente a
   250-370 con /usada/ (septiembre). Es la explicación más probable de la caída de /compra/
   (−21 % impresiones, −18 % clics en 28 d) y de «carretilla elevadora segunda mano»
   (posición 8,6 → 12,5). Arreglo: regenerar los sitemaps con las URL /usada/ y reenviarlos.
2. **Canonical a www en las páginas /usada/.** Ejemplo: la página de carretillas usadas
   declara `canonical = https://www.equipzilla.com/...` y www.equipzilla.com redirige 301 a
   equipzilla.com. Google recibe una señal contradictoria (canonical a una URL que redirige).
   La home sí tiene canonical correcto sin www. Arreglo: canonical sin www en todas las /usada/.
3. **Errata en la URL de manipuladores telescópicos usados:**
   `/manipulacion-elevacion-cargas-segunda-mano/manipulador-teñescopico-segunda-mano`
   (con ñ) está en el sitemap y responde 200; la versión correcta con «telescopico» también
   responde 200. Duplicado y URL ilegible. Arreglo: 301 de la errata a la correcta y sitemap.

## 1. Stock por categoría y página que lo debería vender

| Categoría (stock) | Uds | Precio | Página /compra/…/usada/ existente | Impr 28 d · pos | Qué pediría |
|---|---|---|---|---|---|
| Miniexcavadoras | 12 | 13.900–71.900 € | maquinaria-construccion-segunda-mano/miniexcavadoras-segunda-mano | 10 · 10,3 | Es la categoría con más stock y la página apenas aparece. Título y H1 con «miniexcavadora segunda mano» (hoy la consulta principal no está entre las 2.000 del dominio), texto de 300-500 palabras con rangos de precio reales por tonelaje (0,8-8 t), enlaces a las 3 guías de miniexcavadoras y a las 12 fichas. |
| Plataformas articuladas | 8 | 6.500–20.500 € | plataforma-elevadora-segunda-mano/plataformas-articuladas-segunda-mano | 1.005 · 29,2 | Tiene demanda y rankea en 29: pasar a top 10 con texto propio (eléctrica/diésel, 11-20 m), tabla de precios reales y enlace a la guía de articuladas. Es el mejor quick win de categoría. |
| Carretillas elevadoras | 6 | 6.200–16.000 € | manipulacion-elevacion-cargas-segunda-mano/carretilla-elevadora-segunda-mano | 2.149 · 17,8 | La más buscada (383 impr «carretilla elevadora segunda mano»). Arreglar canonical y sitemap (punto 0), añadir texto de diésel/eléctrica/GLP con precios reales, enlazar a las 5 guías de carretillas. |
| Manipuladores telescópicos | 4 | 26.450–70.000 € | manipulacion-elevacion-cargas-segunda-mano/manipulador-telescopico-segunda-mano (+ errata) | 0 · — | Sin impresiones: la URL con errata y el duplicado se lo comen. Corregir URL, título «manipulador telescópico usado» y enlace a la guía de precios de telescópicos. |
| Excavadoras 14-23 t | 4 | 87.500–139.900 € | maquinaria-construccion-segunda-mano/excavadoras-segunda-mano | 23 · 12,7 | Ticket alto: página con tabla real por tonelaje y horas, y enlace a las 3 guías de excavadoras. |
| Plataformas de tijera | 3 | 3.000–5.500 € | plataforma-elevadora-segunda-mano/plataformas-tijera-segunda-mano | 51 · 25,2 | Texto corto de alturas (8-10 m) y enlace a la guía de tijera pequeña. |
| Palas / minicargadoras | 2 | 23.500–197.900 € | maquinaria-construccion-segunda-mano/minicargadoras-segunda-mano | 140 · 28,0 | «minicargadora articulada» (25 impr) aterriza aquí en posición 28. Texto y ficha del Bobcat S70 destacada (Ads: 11.622 búsquedas/mes de minicargadora). |
| Dumper | 1 | 18.500 € | maquinaria-construccion-segunda-mano/dumpers-segunda-mano | 5 · 12,6 | Enlace a las 2 guías de dumper; no pediría más con una sola unidad. |
| Plataforma sobre camión | 1 | 27.000 € | plataforma-elevadora-segunda-mano/plataformas-elevadoras-sobre-camion-segunda-mano | 21 · 8,4 | Nada: ya rankea bien para su volumen. |

Sin stock pero con demanda que ya rankea (mantener y enlazar a guías): transpaletas
(1.697 impr, pos 10,1, guía lista) y apiladores (363 impr, pos 12,7, guía lista).

## 2. Páginas nuevas que pediría (solo si el stock las respalda)

- **/compra/maquinaria/usada/miniexcavadoras-segunda-mano/kubota**: 7 de las 12 minis son
  Kubota; «kubota kx080» y similares están en el keyword map. Solo si tecnología puede filtrar
  por marca sin crear contenido duplicado.
- Ninguna otra. Con 41 máquinas, cada página nueva sin unidades detrás es una página vacía.

## 3. Orden que propongo
1. Sitemaps con /usada/ + canonical sin www + errata de telescópicos (Lorenzo, técnico, 1 h).
2. Enlaces a las guías de ocasion (docs/SEO-ENLACES-INTERNOS-OCASION.md, 15 min).
3. Textos de categoría: articuladas, carretillas, miniexcavadoras (yo los redacto con precios
   reales; tecnología los cuelga).

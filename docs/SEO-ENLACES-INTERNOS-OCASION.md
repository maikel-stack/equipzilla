# Enlaces internos desde equipzilla.com a ocasion.equipzilla.com (para Lorenzo)

**Por qué:** las 38 guías de ocasion.equipzilla.com llevan desde el 08/09 «Descubiertas, no
indexadas» en Search Console. No es un problema de servidor (Googlebot recibe 200 y el mismo
HTML que un navegador; Vercel sin firewall). Es que ninguna página de equipzilla.com enlaza a
ocasion, y Google no rastrea lo que no tiene enlaces. Este documento contiene los bloques
exactos a pegar. Sin diseño impuesto: son enlaces `<a>` normales; el estilo lo pone el sitio.

## 1. Menú o pie de página (todo el sitio)

```html
<a href="https://ocasion.equipzilla.com/guias/">Guías de compra de maquinaria de ocasión</a>
```

## 2. Página /compra/maquinaria/ocasion/manipulacion-elevacion-cargas-segunda-mano/carretilla-elevadora-segunda-mano

```html
<section class="guias-relacionadas">
  <h2>Guías para comprar una carretilla elevadora de segunda mano</h2>
  <ul>
    <li><a href="https://ocasion.equipzilla.com/guias/precio-carretilla-elevadora-segunda-mano.html">Precio de una carretilla elevadora de segunda mano (tabla real)</a></li>
    <li><a href="https://ocasion.equipzilla.com/guias/carretilla-elevadora-diesel-segunda-mano.html">Carretilla diésel de segunda mano: precios y qué revisar</a></li>
    <li><a href="https://ocasion.equipzilla.com/guias/carretilla-elevadora-electrica-segunda-mano.html">Carretilla eléctrica de segunda mano: precios y batería</a></li>
    <li><a href="https://ocasion.equipzilla.com/guias/carretilla-electrica-o-diesel.html">¿Carretilla eléctrica o diésel? Cuál comprar</a></li>
    <li><a href="https://ocasion.equipzilla.com/guias/carretilla-elevadora-segunda-mano-particulares.html">Comprar una carretilla a un particular: qué exigir</a></li>
  </ul>
</section>
```

## 3. Página /compra/maquinaria/ocasion/manipulacion-elevacion-cargas-segunda-mano/transpaleta-segunda-mano

```html
<section class="guias-relacionadas">
  <h2>Guías para comprar transpaletas y apiladores usados</h2>
  <ul>
    <li><a href="https://ocasion.equipzilla.com/guias/transpaleta-segunda-mano.html">Transpaleta de segunda mano: qué comprar y qué revisar</a></li>
    <li><a href="https://ocasion.equipzilla.com/guias/apilador-segunda-mano.html">Apilador de segunda mano: manual o eléctrico</a></li>
  </ul>
</section>
```

## 4. Página /compra/maquinaria/ocasion/plataforma-elevadora-segunda-mano

```html
<section class="guias-relacionadas">
  <h2>Guías para comprar una plataforma elevadora de segunda mano</h2>
  <ul>
    <li><a href="https://ocasion.equipzilla.com/guias/precio-plataforma-elevadora-usada.html">Precio de una plataforma elevadora usada (tabla real)</a></li>
    <li><a href="https://ocasion.equipzilla.com/guias/plataforma-elevadora-electrica-segunda-mano.html">Plataforma eléctrica de segunda mano: precios</a></li>
    <li><a href="https://ocasion.equipzilla.com/guias/plataforma-elevadora-articulada-segunda-mano.html">Plataforma articulada de segunda mano: precios</a></li>
    <li><a href="https://ocasion.equipzilla.com/guias/plataforma-tijera-o-articulada.html">¿Plataforma de tijera o articulada? Cuál comprar</a></li>
  </ul>
</section>
```

## 5. Página /compra/maquinaria/ocasion/maquinaria-construccion-segunda-mano

```html
<section class="guias-relacionadas">
  <h2>Guías para comprar maquinaria de construcción de segunda mano</h2>
  <ul>
    <li><a href="https://ocasion.equipzilla.com/guias/precio-miniexcavadora-segunda-mano.html">Precio de una miniexcavadora de segunda mano (tabla real)</a></li>
    <li><a href="https://ocasion.equipzilla.com/guias/mini-excavadora-segunda-mano.html">Mini excavadora de segunda mano: guía y precios</a></li>
    <li><a href="https://ocasion.equipzilla.com/guias/que-revisar-miniexcavadora-usada.html">Qué revisar en una miniexcavadora usada: 25 puntos</a></li>
    <li><a href="https://ocasion.equipzilla.com/guias/excavadora-segunda-mano.html">Excavadora de segunda mano: precios por tonelaje</a></li>
    <li><a href="https://ocasion.equipzilla.com/guias/comprar-maquinaria-segunda-mano.html">Comprar maquinaria de segunda mano: checklist</a></li>
  </ul>
</section>
```

## Notas
- Las guías `transpaleta`, `apilador`, `plataforma-elevadora-articulada`, `carretilla-…-particulares`
  y `que-revisar-miniexcavadora-usada` existen en el repo pero no estarán en vivo hasta el deploy
  del quiz (pendiente de OK). Si el deploy se retrasa, pega los bloques igualmente: cuando se
  despliegue, los enlaces empezarán a funcionar; mientras tanto devuelven 404 sin más efecto.
- Sin `rel="nofollow"`: es el mismo dominio y queremos que Google los siga.
- Cuando estén puestos, avisa al Agente SEO (reporte diario) y solicita en Search Console la
  indexación de `https://ocasion.equipzilla.com/guias/`.

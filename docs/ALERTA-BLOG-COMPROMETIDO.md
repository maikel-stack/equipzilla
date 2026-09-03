# 🚨 ALERTA · blog.equipzilla.com sirve spam a Google (cloaking activo)

**Detectado:** 03/09/2026 · por el ciclo diario del Demand Engine, al conectar
Search Console.

## Qué pasa (verificado, no es una hipótesis)

`blog.equipzilla.com` es un WordPress (Apache, `wp-json` activo) que
**muestra contenido distinto a Google que a las personas**:

| Quién visita | Qué recibe |
|---|---|
| Navegador normal | `<title>EQUIPZILLA - Equipzilla Blog</title>` — página legítima |
| **Googlebot** | `<title>DEWI138 Portal Game Arcade Resmi Equipzilla Blog Server Spanyol</title>` + enlaces de slots |

Reproducible con:

```bash
curl -s -L -A "Mozilla/5.0 (compatible; Googlebot/2.1)" https://blog.equipzilla.com/ | grep -i "<title>"
```

Eso es **cloaking**: la técnica que Google castiga con acción manual.

## Impacto medido en Search Console (28 días)

- La consulta basura `slot88kuy.site` generó **6.293 impresiones en posición 4**
  apuntando a `blog.equipzilla.com/`.
- El blog sólo tiene **8 consultas propias**: no aporta tráfico de negocio.
- En los últimos 7 días esas impresiones han caído a 0 → Google probablemente
  ya está desindexando el subdominio.

## Por qué importa para el objetivo de 25 operaciones

1. **Riesgo de arrastre**: la propiedad de Search Console es `sc-domain:equipzilla.com`,
   así que una acción manual sobre el subdominio puede afectar al dominio raíz,
   que hoy trae **289 clics y 27.168 impresiones** al mes y donde viven las
   páginas de compraventa que sí funcionan.
2. **Bloquea la máquina SEO**: los 8 artículos de compraventa iban a publicarse
   justo ahí. Publicar sobre un WordPress comprometido es tirar el trabajo.
3. **Es una brecha de seguridad**: alguien tiene acceso de escritura al servidor.

## Qué hay que hacer (por orden)

1. **Hoy — contener**: sacar el subdominio de la vista de Google mientras se
   limpia (quitar el DNS o devolver 503 a Googlebot). No basta con "no verlo"
   desde el navegador: el spam sólo aparece con user-agent de Googlebot.
2. **Limpiar el WordPress**: actualizar núcleo/plugins/temas, cambiar TODAS las
   contraseñas (WP, FTP/SSH, base de datos, hosting), revisar usuarios
   administradores no reconocidos y buscar ficheros inyectados
   (`wp-content/uploads/*.php` es el escondite habitual).
3. **Search Console**: revisar "Acciones manuales" y "Problemas de seguridad" en
   la propiedad. Si hay acción, pedir revisión sólo después de limpiar.
4. **Después** — y sólo después — publicar los artículos de `seo/articulos/`.

## Decisión pendiente de Maikel
¿Quién tiene el hosting del blog? Sin ese acceso no se puede limpiar desde aquí.

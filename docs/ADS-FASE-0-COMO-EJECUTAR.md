# Cómo ejecutar la fase 0 de Google Ads

Lleva desde el 11/09 preparada y sin aplicar. Las sesiones de Claude no pueden
escribir en la cuenta porque el clasificador de seguridad bloquea las escrituras
externas. Cualquiera del equipo con las credenciales puede lanzarlo en dos minutos.

## En un ordenador con el repo

```bash
git pull origin claude/brevo-equipzilla-template-t47ip0
python3 scripts/bootstrap_credenciales.py     # crea ~/.outbound/ desde las variables
python3 scripts/ads_ajustes.py --informe      # qué va a cambiar, en castellano llano
python3 scripts/ads_ajustes.py --prueba       # el detalle, sin escribir nada
python3 scripts/ads_ajustes.py                # aplica los cambios
```

Necesita dos credenciales: `~/.outbound/google_sa.json` y
`~/.outbound/googleads_dev_token`. El script avisa por su nombre si falta alguna
antes de tocar nada.

## Qué cambia

| # | Cambio | Por qué |
|---|---|---|
| 1 | Dos anuncios nuevos: Retroexcavadoras y Plataformas | Ambos grupos llevan desde el 09/09 activos y sin anuncio, así que no salen nunca. Retroexcavadoras es la categoría más buscada de la cuenta: 42.000 impresiones al mes |
| 2 | Cuatro anuncios apuntan a la página de su categoría | Hoy van al listado general y por una ruta que devuelve una redirección |
| 3 | Cuatro enlaces de sitio apuntan a su página | Los cuatro llevaban al mismo listado general. Por ellos pasa el 71 % del gasto de Búsqueda |
| 4 | Segmentación «personas en España» | Hoy es «en España o interesadas en España» y entra tráfico de Francia, Rumanía y Marruecos |
| 5 | Negativas hasta 57 por campaña | Incluye las variantes con acento: «agricola» no bloquea «agrícola» |

## Qué NO cambia

Presupuesto (sigue en 20 €/día por campaña) y estrategia de puja. Esos dos
necesitan OK expreso de Maikel y van en la fase 1, en `scripts/ads_reestructura.py`.

## Si algo sale mal

Todo queda en el historial de cambios de Google Ads (Herramientas → Historial de
cambios) y se revierte desde ahí. El script no borra nada: crea, actualiza URLs y
añade negativas.

## Después de ejecutarlo

Avisar en esta rama. Al día siguiente el ciclo diario del agente comprueba que los
dos anuncios estén aprobados y que empiecen a salir impresiones en esos grupos.

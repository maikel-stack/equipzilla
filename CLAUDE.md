# CLAUDE.md — Sistema de Agentes ABM · Equipzilla

Contexto y convenciones para los agentes de **Account-Based Marketing (ABM)** de Equipzilla.
Este proyecto es **independiente** de cualquier otro flujo (p. ej. SEO) del repositorio.

---

## Negocio

**Equipzilla** es un marketplace B2B de **alquiler de maquinaria industrial** en España.
Conectamos a empresas que necesitan maquinaria (constructoras, industria, eventos,
agricultura, logística) con empresas de alquiler que disponen de ella.

El objetivo de este sistema ABM es **trabajar la lista de cuentas objetivo** —el directorio
de empresas de alquiler que ya tenemos— para priorizarlas, construir fichas de venta y
generar secuencias de contacto personalizadas. Los contactos están enriquecidos vía
**Apollo.io** (nombre, cargo, email, teléfono, LinkedIn).

---

## Convenciones de trabajo (OBLIGATORIAS)

1. **Idioma: español.** Todo el contenido generado (fichas, emails, mensajes, resúmenes,
   razones de score) se redacta en español de España, tono profesional B2B.

2. **Fuente de verdad única: `data/cuentas.csv`.** Todos los agentes leen las cuentas desde
   ese fichero. No se trabaja sobre listas inventadas ni copiadas de memoria.

3. **NUNCA inventar datos.** Prohibido fabricar empresas, contactos, cargos, teléfonos,
   emails, noticias o señales de compra. Solo se admite:
   - Datos presentes en `data/cuentas.csv`.
   - Datos obtenidos del **servidor MCP de Apollo.io** (si está disponible).
   - Datos obtenidos mediante **búsqueda web sobre fuentes verificables** (web oficial de
     la empresa, prensa, portales de empleo, registros públicos).
   Si un dato no se puede verificar, se marca explícitamente como **"sin verificar"** o
   **"no disponible"** — nunca se rellena con una suposición.

4. **Citar la fuente** de toda noticia o señal de compra (URL + fecha). Si no hay fuente,
   no se incluye.

5. **Salidas en `output/`** (se crea si no existe):
   - `output/cuentas_priorizadas.csv`
   - `output/dossiers/{empresa-slug}.md`
   - `output/secuencias/{empresa-slug}.md`

6. **`{empresa-slug}`**: nombre de la empresa en minúsculas, sin acentos, espacios y
   símbolos sustituidos por guiones (p. ej. `Alquileres García e Hijos, S.L.` →
   `alquileres-garcia-e-hijos`).

---

## Perfil de Cliente Ideal (ICP) — EDITABLE

> Esta sección define el ICP que usa el agente `scoring-cuentas`. **Está pensada para
> afinarse**: ajusta pesos, rangos y palabras clave según vaya madurando el proyecto.
> Los pesos deben sumar 100.

### Dimensiones y pesos

| Dimensión | Peso | Qué medimos |
|-----------|------|-------------|
| Tamaño de empresa | 30 | Volumen y capacidad para ser un partner relevante |
| Especialidad de maquinaria | 25 | Encaje del catálogo con la demanda de Equipzilla |
| Cobertura regional | 20 | Presencia en zonas prioritarias de demanda |
| Madurez digital | 25 | Capacidad/disposición a operar en un marketplace online |

### Rúbricas por dimensión (0–100 cada una)

**1. Tamaño de empresa (peso 30)**
- `empleados` y `facturacion` del CSV.
- 90–100: > 200 empleados o > 20 M€ facturación.
- 70–89: 50–200 empleados o 5–20 M€.
- 40–69: 10–49 empleados o 1–5 M€.
- 10–39: < 10 empleados o < 1 M€.
- Sin dato → 50 (neutro) y marcar "tamaño sin verificar".

**2. Especialidad de maquinaria (peso 25)**
- Campo `especialidad` del CSV.
- Prioritarias (90–100): elevación (plataformas/grúas), movimiento de tierras
  (excavadoras, retros, dúmpers), maquinaria de obra civil.
- Secundarias (60–89): manutención (carretillas/manipuladores telescópicos),
  compactación, generadores/energía, climatización industrial.
- Largo/nicho (30–59): eventos, andamios, herramienta ligera.
- Fuera de foco (0–29): especialidades sin relación con construcción/industria.

**3. Cobertura regional (peso 20)**
- Campos `pais`, `region`, `ciudad`.
- Regiones prioritarias (90–100): Madrid, Cataluña, Comunidad Valenciana, Andalucía,
  País Vasco.
- Resto de España peninsular (60–89).
- Insular / zonas de baja demanda (30–59).
- Fuera de España (0–29) salvo que se decida internacionalizar.

**4. Madurez digital (peso 25)**
- Señales: tiene `web` propia y activa; presencia del contacto en LinkedIn (`contacto` con
  perfil); web con catálogo/reservas online; uso de canales digitales.
- 90–100: web moderna con catálogo/reserva online y presencia digital fuerte.
- 60–89: web informativa + presencia en LinkedIn.
- 30–59: web básica o solo redes sociales.
- 0–29: sin web ni presencia digital localizable.
- Para evaluar esta dimensión se puede usar búsqueda web; si no se verifica, marcar
  "madurez digital sin verificar" y asignar 50.

### Cálculo del score

```
score_total = Σ ( puntuación_dimensión × peso_dimensión / 100 )
```

Resultado de 0 a 100. Tiers:
- **A — Encaje alto:** ≥ 75
- **B — Encaje medio:** 50–74
- **C — Encaje bajo:** < 50

### Señales de compra (bonus, no altera el peso base)

Se registran aparte como contexto comercial (las usa `dossier-cuenta`), no para inflar el
score: expansión/nuevas delegaciones, nuevas obras o adjudicaciones, ofertas de empleo de
operarios/maquinistas, ampliación de flota, rondas de inversión.

---

## Agentes del sistema

- **`scoring-cuentas`** — puntúa todas las cuentas del CSV según este ICP →
  `output/cuentas_priorizadas.csv`.
- **`dossier-cuenta`** — ficha de venta de una empresa (decisores, noticias, señales,
  ángulo) → `output/dossiers/{empresa-slug}.md`.
- **`secuencia-personalizada`** — secuencia multicanal (3 emails + 2 LinkedIn) a partir de
  un dossier → `output/secuencias/{empresa-slug}.md`.

Comando orquestador: **`/abm-run [N]`** (por defecto N=10).

---

## Apollo.io (MCP)

Si el servidor MCP de Apollo.io está conectado (ver `.mcp.json.example` y `README_ABM.md`),
los agentes lo usan para enriquecer/confirmar decisores. Si no está disponible, se usan los
contactos del CSV. **Nunca** se inventan contactos para suplir su ausencia.

# Equipzilla · Pipeline de fotos de maquinaria

Pipeline en Python que recibe fotos de máquinas enviadas por los alquiladores y
genera automáticamente **3 versiones editadas** de cada foto usando una API de
edición de imagen por IA:

1. **`operador`** → la máquina con un operador realista usándola/conduciéndola.
2. **`ficha_tecnica`** → la máquina sobre fondo neutro uniforme (catálogo).
3. **`en_faena`** → la misma máquina en un contexto de obra/terreno realista.

El proveedor de imagen está abstraído tras una interfaz (`ImageProvider`), de
modo que se puede cambiar sin tocar el resto del código. Por defecto usa
**Google Gemini** (*Nano Banana* / Gemini Flash Image) para edición
image-to-image + inpainting, y deja un **stub listo para FLUX.1 Kontext**.

---

## ⚠️ Regla crítica de precisión

El modelo **debe preservar la identidad real de la máquina**: marca, modelo,
color exacto, forma, adhesivos y estado real (desgaste, suciedad, golpes). Está
**prohibido** inventar partes que no se ven en el original, cambiar el modelo o
"embellecer" la máquina. Esta regla se antepone automáticamente a todos los
prompts (ver `global_constraint` en `config.yaml`).

### Sobre el "360 real"

Un **360 real no se puede generar a partir de una sola foto** sin *fabricar*
geometría inexistente (caras de la máquina que la cámara nunca capturó). Eso
violaría la regla de precisión. Para obtener un 360 fiable hay que **capturar
varias fotos por ángulo** (p. ej. cada 15–30°) y montarlas. Por eso el pipeline
**no implementa** generación de 360 por invención: queda documentado como flujo
de captura multiángulo, no de alucinación de imagen.

---

## Estructura

```
equipzilla-fotos/
  input/                 # fotos originales que entran
  output/<id_maquina>/   # versiones generadas + manifest.json
  processed/             # originales ya procesados
  config.yaml            # prompts de cada versión (editable)
  .env.example           # plantilla de configuración / API key
  requirements.txt
  README.md
  src/
    run.py               # CLI: python -m src.run
    config.py            # carga .env + config.yaml
    pipeline.py          # orquestación, reintentos, idempotencia
    manifest.py          # manifest.json por máquina
    logging_setup.py     # logging a consola + archivo
    providers/
      base.py            # interfaz ImageProvider
      gemini.py          # Google Gemini (por defecto)
      flux.py            # FLUX.1 Kontext (stub)
```

---

## 1. Instalación

Requiere **Python 3.11+**.

```bash
cd equipzilla-fotos

# (recomendado) entorno virtual
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

---

## 2. Dónde poner la API key

1. Copia la plantilla de entorno:

   ```bash
   cp .env.example .env
   ```

2. Edita `.env` y pega tu **API key de Google Gemini**
   (consíguela en <https://aistudio.google.com/apikey>):

   ```dotenv
   IMAGE_PROVIDER=gemini
   GEMINI_API_KEY=tu_api_key_real
   GEMINI_MODEL=gemini-2.5-flash-image-preview
   COST_PER_IMAGE_USD=0.039
   ```

> El archivo `.env` está en `.gitignore`: **nunca** se sube al repositorio.

---

## 3. Cómo ejecutar

Pon las fotos originales en `input/` (formatos: jpg, png, webp, bmp, tif) y
ejecuta:

```bash
python -m src.run
```

Por cada foto el pipeline:

- asigna un **id** (el nombre del archivo, p. ej. `EXC-001.jpg` → `EXC-001`),
- genera las 3 versiones vía API,
- guarda en `output/<id>/<id>_<version>.jpg`,
- escribe `output/<id>/manifest.json`,
- mueve el original a `processed/`.

### Opciones del CLI

| Comando | Qué hace |
|---|---|
| `python -m src.run` | Procesa todas las fotos de `input/`. |
| `python -m src.run --force` | Reprocesa aunque ya existan las versiones en `output/`. |
| `python -m src.run --input ruta/foto.jpg` | Procesa una foto concreta. |
| `python -m src.run --id EXC-001` | Fuerza el id (solo con 1 foto de entrada). |
| `python -m src.run --dry-run` | Muestra qué haría, **sin llamar a la API**. |
| `python -m src.run --verbose` | Logging en nivel DEBUG. |

**Características del proceso:**

- **Barra de progreso** por lotes (tqdm).
- **Reintentos con backoff exponencial** ante errores de API (hasta 4 intentos).
- **Idempotente**: no reprocesa versiones ya presentes en `output/`; usa
  `--force` para forzar.
- **Logging** a consola y a `logs/equipzilla.log`.
- **`manifest.json`** por máquina con: original, versiones creadas, proveedor,
  modelo, timestamp y coste estimado.

---

## 4. Cómo editar los prompts de cada versión

Todos los prompts viven en **`config.yaml`** (no hace falta tocar el código):

```yaml
versions:
  operador:
    description: "..."
    prompt: >-
      Añade un operador humano realista usando esta máquina...
  ficha_tecnica:
    prompt: >-
      Coloca la máquina sobre un fondo de estudio neutro y uniforme...
  en_faena:
    prompt: >-
      Coloca esta MISMA máquina en un contexto de trabajo realista...
```

- `global_constraint`: la **regla crítica** que se antepone a todos los prompts.
  No la quites.
- `negative_prompt`: lo que **no** debe aparecer.
- `output.quality`: calidad JPG (1–100).
- Puedes **añadir o quitar versiones**: cada clave bajo `versions:` produce un
  archivo `output/<id>/<id>_<clave>.jpg`.
- Variable disponible en los prompts: `{machine_id}`.

---

## 5. Cambiar de proveedor de imagen

El pipeline funciona con cualquier implementación de `ImageProvider`
(`src/providers/base.py`).

- **Gemini** (por defecto): `IMAGE_PROVIDER=gemini` en `.env`.
- **FLUX.1 Kontext** (alternativa): `IMAGE_PROVIDER=flux` + `FLUX_API_KEY=...`.
  La clase `FluxProvider` (`src/providers/flux.py`) está como **stub**: solo hay
  que rellenar el método `edit()` con la llamada HTTP real al endpoint de FLUX
  (la lógica de reintentos, guardado y manifest ya es común a todos los
  proveedores).

Para añadir un proveedor nuevo: implementa `ImageProvider` y regístralo en
`src/providers/__init__.py::get_provider`.

---

## Comando para ejecutar

```bash
python -m src.run
```

(desde dentro de la carpeta `equipzilla-fotos/`, con el `.venv` activado y la
`GEMINI_API_KEY` puesta en `.env`).

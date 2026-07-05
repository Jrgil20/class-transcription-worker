# Hardware y elección de modelo

El proyecto se diseñó y probó sobre un **Intel i5 9th Gen sin GPU dedicada, 16 GB RAM** (ver [plan.md](plan.md#2-contexto-y-restricciones-de-hardware)), y el default (`ModelConfig.model_size = "small"`, `compute_type = "int8"`) está calibrado para ese piso. Si vas a instalarlo en otra máquina, esta guía te ayuda a elegir un modelo mejor sin tener que adivinar. Todo se ajusta en [`poc/config.py`](../poc/config.py) → `ModelConfig` (ver [configuración](configuracion.md#modelconfig)).

Regla general: **más grande el modelo → mejor calidad de transcripción, pero más CPU/RAM y más calor**. En un mismo hardware, el salto de `small` a `medium` puede ser la diferencia entre transcribir en tiempo real o ir acumulando atraso.

## Solo CPU (sin GPU dedicada)

| Tu CPU | Modelo recomendado | `compute_type` | Notas |
|---|---|---|---|
| Dual/quad-core viejo, laptop de gama baja | `tiny` o `base` | `int8` | Prioriza no perder segmentos por atraso sobre la calidad. |
| Intel i5 9th Gen o equivalente (el hardware de referencia de este proyecto) | `small` | `int8` | Default actual. Buen balance calidad/latencia para clases de 60-90 min. |
| i7/Ryzen 7 recientes (8+ cores), 32 GB RAM | `medium` | `int8` | Notablemente mejor con acentos, tecnicismos y ruido de aula. Vigilar temperatura igual (ver `ThermalConfig`). |
| Apple Silicon (M1/M2/M3/M4) | `small` o `medium` vía `int8` | `int8` | `faster-whisper`/CTranslate2 no usa el Neural Engine ni Metal todavía; corre en CPU igual que un x86. Si querés aprovechar el Neural Engine, mirá `whisper.cpp` (Metal) o `mlx-whisper` como alternativa al motor actual — implica cambiar el módulo `transcriber.py`, no es drop-in. |

## Con GPU NVIDIA (CUDA)

Si tenés una GPU NVIDIA, aunque sea de gama media (GTX 1660, RTX 3050 en adelante), el salto de calidad es grande porque deja de ser el cuello de botella térmico/de CPU:

| GPU | Modelo recomendado | `device` / `compute_type` | Notas |
|---|---|---|---|
| GTX 1650/1660, RTX 3050 (4-6 GB VRAM) | `medium` | `device="cuda"`, `compute_type="float16"` | Instalar `faster-whisper` con soporte CUDA (requiere CUDA/cuDNN de NVIDIA instalados). |
| RTX 3060 en adelante (8+ GB VRAM) | `large-v3` o `distil-large-v3` | `device="cuda"`, `compute_type="float16"` | `distil-large-v3` (Hugging Face `distil-whisper/distil-large-v3`) da calidad cercana a `large-v3` con ~6x menos latencia; buena opción si vas a transcribir en vivo durante toda una clase. |

Con GPU, el riesgo de *thermal throttling* de CPU que motivó `ThermalConfig` deja de ser el cuello de botella principal; igual dejá el monitor activo, ahora vigilando la GPU en vez de la CPU (`nvidia-smi` en paralelo mientras corre `main.py`).

## Cómo cambiar el modelo

Editar en `poc/config.py`:

```python
MODEL = ModelConfig(
    model_size="medium",
    fallback_model_size="small",   # el que se usa si hay throttling
    device="cpu",                  # o "cuda"
    compute_type="int8",           # "float16" si device="cuda"
    language="es",
)
```

La primera corrida con un `model_size` nuevo descarga los pesos de Hugging Face (una sola vez, requiere internet); después la inferencia queda 100% local.

## No sabés qué elegir

Si es tu primera instalación y no conocés bien las capacidades térmicas de la máquina: arrancá con el default (`small`/`int8`/`cpu`), corré una sesión de 30-45 min real, y mirá los logs `[monitor] ... temp=..`. Si nunca se acerca a `ThermalConfig.threshold_c` (80°C) y la latencia por segmento queda muy por debajo de la duración del segmento, subí un escalón (`base`→`small`→`medium`). Es más barato probar y bajar que sobre-invertir en un modelo que termine degradándose todo el tiempo por calor.

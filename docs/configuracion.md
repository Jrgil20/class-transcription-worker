# Configuración

Todos los parámetros ajustables de la PoC viven en [`poc/config.py`](../poc/config.py), en `dataclasses` inmutables agrupadas por área. No hay archivo `.yaml`/`.env` todavía: para cambiar un valor, se edita `config.py` directamente.

## `AudioConfig`

| Campo | Default | Descripción |
|---|---|---|
| `sample_rate` | `16_000` | Requerido por Whisper y por `webrtcvad`. No cambiar. |
| `channels` | `1` | Mono. |
| `frame_duration_ms` | `30` | `webrtcvad` solo acepta 10/20/30 ms. |
| `input_device` | `None` | `None` usa el dispositivo por defecto del sistema. Poner el índice numérico del dispositivo (ver `python3 -m sounddevice`) para forzar otro. |

## `VadConfig`

| Campo | Default | Descripción |
|---|---|---|
| `aggressiveness` | `2` | 0 (permisivo) a 3 (estricto). Más alto filtra más ruido de fondo pero puede cortar voz baja. |
| `silence_timeout_s` | `0.8` | Silencio continuo necesario para cerrar un segmento. |
| `min_segment_duration_s` | `0.3` | Descarta segmentos más cortos que esto (ruido puntual). |
| `padding_ms` | `200` | Margen de silencio incluido antes/después de la voz detectada. |
| `max_segment_duration_s` | `20.0` | Corta un segmento igual si hay voz continua sin pausas, para no mandarle audios larguísimos a Whisper. |

## `ModelConfig`

| Campo | Default | Descripción |
|---|---|---|
| `model_size` | `"small"` | Tamaño de modelo Whisper. Ver [hardware y modelos](hardware-y-modelos.md) para qué conviene según tu máquina. |
| `fallback_model_size` | `"base"` | Modelo al que se degrada si hay *thermal throttling*. |
| `device` | `"cpu"` | `"cpu"` o `"cuda"` si tenés GPU NVIDIA compatible. |
| `compute_type` | `"int8"` | Cuantización vía CTranslate2. `int8` en CPU; `float16` si `device="cuda"`. |
| `language` | `"es"` | Forzar idioma (evita el costo de autodetección). `None` autodetecta por segmento. |

## `ThermalConfig`

| Campo | Default | Descripción |
|---|---|---|
| `threshold_c` | `80.0` | Temperatura de CPU a partir de la cual se degrada el modelo. |
| `check_interval_s` | `30.0` | Frecuencia del chequeo térmico. |

## `OutputConfig`

| Campo | Default | Descripción |
|---|---|---|
| `output_dir` | `poc/sesiones/` | Carpeta de salida de las notas. |
| `filename_prefix` | `"clase"` | Prefijo del nombre de archivo. |
| `session_split_minutes` | `15.0` | Cada cuántos minutos se cierra y arranca una nota nueva (`_parte2`, ...). `0` o `None` desactiva el split. |

## `QueueConfig`

| Campo | Default | Descripción |
|---|---|---|
| `maxsize` | `50` | Tamaño de la cola productor→consumidor. Si se llena, el productor bloquea (*back-pressure*) en vez de descartar audio. |

## Notas sobre `psutil.sensors_temperatures()`

En algunos sistemas (WSL, ciertas VMs, algunos laptops) esta API no está disponible o no expone sensores de CPU reconocibles. `main.py` lo maneja de forma defensiva: si falla, el monitor sigue mostrando CPU/RAM pero sin temperatura, y el fallback térmico automático queda inactivo (no hay forma de saber la temperatura real). En ese caso, prestá atención manualmente al rendimiento en sesiones largas.

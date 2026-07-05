# Sistema de Transcripción Desatendido para Aulas

> Servicio en segundo plano (*background worker*) en Python que captura, segmenta por VAD y transcribe el dictado continuo de un profesor en un aula con ruido y eco, produciendo apuntes estructurados en Markdown. Optimizado para CPU Intel i5 9th Gen sin GPU dedicada, ejecutando inferencia íntegramente local.

---

## ¿Qué hace?

Un proceso desatendido toma notas mientras el estudiante se concentra en **comprender**, no en transcribir. Captura audio del micrófono, detecta voz (VAD), transcribe con Whisper local y guarda el resultado en un archivo Markdown compatible con Obsidian.

## Stack

| Capa | Herramienta |
|---|---|
| Lenguaje | Python 3.11+ |
| Inferencia | `faster-whisper` (CTranslate2 int8) |
| Modelo | `whisper-small` int8 |
| Captura de audio | `sounddevice` |
| VAD | `silero-vad` |
| Salida | Markdown (compatible Obsidian) |
| Observabilidad | `structlog` + `psutil` |

## Arquitectura

Patrón Productor–Consumidor con Clean Architecture:

```
src/
├── domain/          # AudioChunk, TranscriptionResult
├── application/     # transcribe_session (caso de uso)
├── adapters/        # audio/, inference/, vad/, output/
└── infrastructure/  # main.py, config, logging
```

## Restricciones de hardware

- **CPU:** Intel i5 9th Gen (sin GPU dedicada)
- **RAM:** 16 GB
- **SO:** Pop!_OS con PipeWire

> **Riesgo principal:** thermal throttling bajo carga sostenida.  
> **Mitigación:** inferencia int8 + procesamiento asíncrono por lotes.

## Estado

`poc` — PoC funcional en [`poc/`](poc/). Sin Clean Architecture todavía (scripts planos pero con responsabilidades bien separadas); valida el pipeline completo captura → VAD → transcripción → nota antes de invertir en arquitectura. Ver [`docs/plan.md`](docs/plan.md) para el diseño completo.

### Cómo correr la PoC

```bash
cd poc
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python3 main.py
```

Graba desde el micrófono por defecto, transcribe segmentos de voz en vivo y al cortar con `Ctrl+C` guarda la nota en `poc/sesiones/`.

### Inicio rápido en clase

Hay un alias `clase` en `.bashrc` que corre `poc/start_clase.sh` (activa el venv y lanza `main.py`). Abrí una terminal y escribí:

```bash
clase --asignatura "Desarrollo de Software II" --profesor "Calonzo"
```

Ambos flags son opcionales; van al frontmatter de la nota y al nombre del archivo. La fecha/hora se toman automáticamente. `Ctrl+C` para cortar y guardar la nota.

### Robustez (más allá de la PoC mínima)

- **Cap de duración de segmento** (`VadConfig.max_segment_duration_s`, 20s por defecto): si hay voz continua sin pausas, igual corta para no mandar audios larguísimos a Whisper.
- **Manejo de excepciones en los hilos**: si el micrófono se desconecta o falla la inferencia, el error se loguea y el proceso corta prolijamente (guarda lo que tenga) en vez de quedar colgado en silencio.
- **Split de sesión** (`OutputConfig.session_split_minutes`, 15 min por defecto): en clases largas, cierra y arranca un archivo nuevo (`_parte2`, `_parte3`, ...) periódicamente para no perder todo si algo falla cerca del final.
- **Monitor térmico** (`ThermalConfig`, umbral 80°C): si la CPU se calienta, degrada automáticamente de `small` a `base` (`ModelConfig.fallback_model_size`).
- **Recuperación de sesiones huérfanas**: si el proceso muere sin pasar por `Ctrl+C` (corte de luz, cierre forzado), al arrancar `main.py` de nuevo detecta cualquier `.tmp.md` suelto en `poc/sesiones/` y lo convierte en una nota `_recuperada.md` (marcada como tal, sin la metadata que solo vivía en memoria).
- **Cierre prolijo también con `SIGTERM`**: no solo `Ctrl+C` (`SIGINT`) guarda la nota; si el proceso recibe `SIGTERM` (p. ej. se cierra la terminal o lo mata systemd), también finaliza y guarda antes de salir.

> Nota: esta PoC usa `webrtcvad` en vez de `silero-vad` (más liviano, sin dependencia de `torch`). Los parámetros de audio, VAD y modelo están centralizados en `poc/config.py`.

## Documentación

- [Plan de diseño completo](docs/plan.md)

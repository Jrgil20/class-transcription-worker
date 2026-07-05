# Arquitectura

## Estado actual: PoC

El código en [`poc/`](../poc/) es intencionalmente **scripts planos**, no la Clean Architecture descrita en el [plan de diseño](plan.md). Esto fue una decisión, no un descuido: antes de invertir en capas/puertos/DI había que validar que el pipeline completo (captura → VAD → transcripción → nota) funcionara con audio real y no se cayera por calor en una sesión larga. Ver [plan.md §7](plan.md#7-siguiente-paso--decisión) para el razonamiento completo.

Aun así, la PoC ya separa responsabilidades por archivo:

```
poc/
├── main.py            # orquestador: hilo productor + hilo consumidor + monitor térmico
├── config.py           # todos los parámetros ajustables, centralizados
├── models.py            # AudioChunk, TranscriptionResult (dataclasses, sin lógica)
├── audio_capture.py    # captura del micrófono → frames PCM16
├── vad.py               # VAD + segmentación en AudioChunk
├── transcriber.py       # wrapper de faster-whisper
├── note_writer.py       # escritura de la nota Markdown + recuperación de sesiones huérfanas
└── start_clase.sh       # script de arranque para el alias `clase`
```

## Flujo en tiempo de ejecución

Patrón productor-consumidor con tres hilos (`threading`), coordinados por `main.py`:

1. **Productor** (`audio_capture.frame_stream` + `vad.SpeechSegmenter`): captura frames de 30ms, aplica VAD, agrupa voz en `AudioChunk` y los encola.
2. **Consumidor**: saca `AudioChunk` de la cola, transcribe con `Transcriber` (faster-whisper), y escribe el segmento con `MarkdownWriter`.
3. **Monitor**: cada 30s reporta CPU/RAM/temperatura y dispara la degradación de modelo si hace falta.

La cola (`queue.Queue(maxsize=QUEUE.maxsize)`) aplica *back-pressure*: si el consumidor se atrasa, el productor bloquea en vez de descartar audio o crecer sin límite.

Manejo de errores: cualquier excepción en productor o consumidor se captura, se guarda en `error_box`, y dispara `stop_event` para que el proceso cierre prolijamente (guardando lo que tenga) en vez de quedar colgado.

## Hacia dónde evoluciona

El [plan de diseño](plan.md#4-arquitectura) define una Clean Architecture con puertos (`IAudioProvider`, `IVoiceActivityDetector`, `ITranscriptionEngine`, `INoteWriter`) para poder cambiar de implementación (por ejemplo, `faster-whisper` → `whisper.cpp`, o `sounddevice` → otra librería) sin tocar el núcleo. Migrar a esa estructura tiene sentido cuando:

- Se necesite soportar más de una implementación real de algún puerto (no solo como ejercicio teórico).
- Se quiera cubrir el pipeline con tests unitarios que hoy son difíciles de aislar por estar todo en scripts con efectos secundarios directos.

Hasta entonces, la prioridad es mantener la PoC simple y confiable antes que "bien diseñada" en abstracto — ver [contribución](contribucion.md) sobre por qué no se persiguen features o refactors especulativos.

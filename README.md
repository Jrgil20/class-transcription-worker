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

`design` — en fase de PoC. Ver [`docs/plan.md`](docs/plan.md) para el diseño detallado.

## Documentación

- [Plan de diseño completo](docs/plan.md)

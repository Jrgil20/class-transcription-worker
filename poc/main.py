"""Orquestador de la PoC: hilo productor (captura+VAD) + hilo consumidor (transcripción+escritura).

Uso:
    python main.py

Ctrl+C detiene la captura y cierra la nota Markdown de forma prolija.
"""
import queue
import threading
import time

import psutil

from audio_capture import frame_stream
from config import AUDIO, MODEL, OUTPUT, QUEUE, VAD
from models import AudioChunk
from note_writer import MarkdownWriter
from transcriber import Transcriber
from vad import SpeechSegmenter


def _producer(chunk_queue: "queue.Queue[AudioChunk]", stop_event: threading.Event) -> None:
    segmenter = SpeechSegmenter(AUDIO, VAD)
    frames = frame_stream(AUDIO, stop_event)
    for chunk in segmenter.segments(frames):
        if stop_event.is_set():
            break
        chunk_queue.put(chunk)  # back-pressure: bloquea si la cola está llena


def _consumer(
    chunk_queue: "queue.Queue[AudioChunk]",
    stop_event: threading.Event,
    writer: MarkdownWriter,
) -> None:
    transcriber = Transcriber(MODEL)
    print("[main] modelo cargado, listo para transcribir")

    while not (stop_event.is_set() and chunk_queue.empty()):
        try:
            chunk = chunk_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        t0 = time.monotonic()
        result = transcriber.transcribe(chunk)
        latency = time.monotonic() - t0

        if result.text:
            writer.add_segment(result)
            print(f"[{latency:5.2f}s] {result.text}")
        else:
            print(f"[{latency:5.2f}s] (segmento sin texto reconocible)")


def _log_system_health(stop_event: threading.Event) -> None:
    while not stop_event.wait(30):
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        print(f"[monitor] cpu={cpu:.0f}% mem={mem:.0f}%")


def main() -> None:
    writer = MarkdownWriter(OUTPUT, model_name=f"faster-whisper-{MODEL.model_size}-{MODEL.compute_type}")
    writer.start()

    chunk_queue: "queue.Queue[AudioChunk]" = queue.Queue(maxsize=QUEUE.maxsize)
    stop_event = threading.Event()

    producer_thread = threading.Thread(target=_producer, args=(chunk_queue, stop_event), daemon=True)
    consumer_thread = threading.Thread(
        target=_consumer, args=(chunk_queue, stop_event, writer), daemon=True
    )
    monitor_thread = threading.Thread(target=_log_system_health, args=(stop_event,), daemon=True)

    producer_thread.start()
    consumer_thread.start()
    monitor_thread.start()

    print("[main] grabando... Ctrl+C para detener")
    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n[main] deteniendo...")

    stop_event.set()
    consumer_thread.join(timeout=30)

    final_path = writer.finalize()
    print(f"[main] nota guardada en: {final_path}")


if __name__ == "__main__":
    main()

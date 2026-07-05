"""Orquestador de la PoC: hilo productor (captura+VAD) + hilo consumidor (transcripción+escritura).

Uso:
    python main.py [--asignatura "Desarrollo"] [--profesor "Calonzo"]

Ctrl+C detiene la captura y cierra la nota Markdown de forma prolija.
"""
import argparse
import queue
import signal
import threading
import time
import traceback

import psutil

from audio_capture import frame_stream
from config import AUDIO, MODEL, OUTPUT, QUEUE, THERMAL, VAD
from models import AudioChunk
from note_writer import MarkdownWriter, recover_orphaned_sessions
from transcriber import Transcriber
from vad import SpeechSegmenter


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcripción desatendida de clases")
    parser.add_argument("--asignatura", default="", help="Nombre de la asignatura (va al frontmatter y al nombre de archivo)")
    parser.add_argument("--profesor", default="", help="Nombre del profesor (va al frontmatter)")
    return parser.parse_args()


def _producer(
    chunk_queue: "queue.Queue[AudioChunk]", stop_event: threading.Event, error_box: list
) -> None:
    try:
        segmenter = SpeechSegmenter(AUDIO, VAD)
        frames = frame_stream(AUDIO, stop_event)
        for chunk in segmenter.segments(frames):
            if stop_event.is_set():
                break
            chunk_queue.put(chunk)  # back-pressure: bloquea si la cola está llena
    except Exception:  # noqa: BLE001 - queremos capturar cualquier falla de audio/VAD
        error_box.append(("productor", traceback.format_exc()))
        stop_event.set()


def _consumer(
    chunk_queue: "queue.Queue[AudioChunk]",
    stop_event: threading.Event,
    writer: MarkdownWriter,
    thermal_event: threading.Event,
    error_box: list,
) -> None:
    try:
        transcriber = Transcriber(MODEL)
        print("[main] modelo cargado, listo para transcribir")

        split_seconds = (OUTPUT.session_split_minutes or 0) * 60
        part = 1
        session_started_at = time.monotonic()

        while not (stop_event.is_set() and chunk_queue.empty()):
            if thermal_event.is_set() and not transcriber.degraded:
                print("[main] temperatura elevada: degradando a modelo más liviano")
                transcriber.degrade()

            if split_seconds and (time.monotonic() - session_started_at) >= split_seconds:
                final_path = writer.finalize()
                print(f"[main] split de sesión, nota guardada en: {final_path}")
                part += 1
                writer.start(part=part)
                session_started_at = time.monotonic()

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
    except Exception:  # noqa: BLE001 - falla de inferencia o de escritura de notas
        error_box.append(("consumidor", traceback.format_exc()))
        stop_event.set()


def _monitor(stop_event: threading.Event, thermal_event: threading.Event) -> None:
    temps_available = True
    while not stop_event.wait(THERMAL.check_interval_s):
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        temp_str = ""

        if temps_available:
            try:
                sensors = psutil.sensors_temperatures()
            except (AttributeError, NotImplementedError):
                temps_available = False
                sensors = {}

            cpu_keywords = ("core", "cpu", "acpi", "k10temp", "zenpower")
            cpu_sensors = {
                name: readings
                for name, readings in sensors.items()
                if any(kw in name.lower() for kw in cpu_keywords)
            } or sensors  # si no reconocemos ninguno, usamos todos como fallback

            if cpu_sensors:
                max_temp = max(
                    reading.current for readings in cpu_sensors.values() for reading in readings
                )
                temp_str = f" temp={max_temp:.0f}C"
                if max_temp >= THERMAL.threshold_c:
                    thermal_event.set()

        print(f"[monitor] cpu={cpu:.0f}% mem={mem:.0f}%{temp_str}")


def main() -> None:
    args = _parse_args()

    recovered = recover_orphaned_sessions(OUTPUT)
    for path in recovered:
        print(f"[main] sesión huérfana recuperada: {path}")

    writer = MarkdownWriter(
        OUTPUT,
        model_name=f"faster-whisper-{MODEL.model_size}-{MODEL.compute_type}",
        asignatura=args.asignatura,
        profesor=args.profesor,
    )
    writer.start()

    chunk_queue: "queue.Queue[AudioChunk]" = queue.Queue(maxsize=QUEUE.maxsize)
    stop_event = threading.Event()
    thermal_event = threading.Event()
    error_box: list = []

    def _handle_sigterm(signum, frame) -> None:
        stop_event.set()

    signal.signal(signal.SIGTERM, _handle_sigterm)

    producer_thread = threading.Thread(
        target=_producer, args=(chunk_queue, stop_event, error_box), daemon=True
    )
    consumer_thread = threading.Thread(
        target=_consumer,
        args=(chunk_queue, stop_event, writer, thermal_event, error_box),
        daemon=True,
    )
    monitor_thread = threading.Thread(
        target=_monitor, args=(stop_event, thermal_event), daemon=True
    )

    producer_thread.start()
    consumer_thread.start()
    monitor_thread.start()

    print("[main] grabando... Ctrl+C para detener")
    try:
        while not stop_event.is_set():
            time.sleep(0.2)
        if error_box:
            source, tb = error_box[0]
            print(f"[main] error irrecuperable en {source}:\n{tb}")
    except KeyboardInterrupt:
        print("\n[main] deteniendo...")

    stop_event.set()
    consumer_thread.join(timeout=30)

    final_path = writer.finalize()
    print(f"[main] nota guardada en: {final_path}")


if __name__ == "__main__":
    main()

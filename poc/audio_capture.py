"""Captura de audio del micrófono en frames PCM16 de duración fija.

Expone un generador que produce bytes crudos (PCM16 mono) listos para
pasar al VAD (webrtcvad exige exactamente 10/20/30 ms por frame).
"""
import queue
import threading
from collections.abc import Iterator

import sounddevice as sd

from config import AudioConfig


def frame_stream(cfg: AudioConfig, stop_event: threading.Event) -> Iterator[bytes]:
    """Yield frames PCM16 de `cfg.frame_duration_ms` hasta que se active `stop_event`."""
    frame_samples = int(cfg.sample_rate * cfg.frame_duration_ms / 1000)
    frame_bytes_len = frame_samples * 2  # int16 = 2 bytes

    raw_queue: queue.Queue[bytes] = queue.Queue()

    def _callback(indata, frames, time_info, status) -> None:
        if status:
            print(f"[audio_capture] status: {status}")
        raw_queue.put(bytes(indata))

    stream = sd.RawInputStream(
        samplerate=cfg.sample_rate,
        blocksize=frame_samples,
        device=cfg.input_device,
        dtype="int16",
        channels=cfg.channels,
        callback=_callback,
    )

    with stream:
        while not stop_event.is_set():
            try:
                frame = raw_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            if len(frame) != frame_bytes_len:
                continue  # descarta frames parciales (p.ej. al cerrar el stream)
            yield frame

"""Detección de voz (VAD) y segmentación de frames en AudioChunk.

Usa webrtcvad para clasificar cada frame como voz/silencio, y agrupa
frames de voz consecutivos en segmentos, con:
- padding: unos ms de contexto antes de que arranque la voz.
- silence_timeout_s: silencio sostenido que cierra el segmento actual.
- min_segment_duration_s: descarta segmentos demasiado cortos (ruido puntual).
- max_segment_duration_s: corta un segmento aunque siga habiendo voz, para no
  mandarle a Whisper audios larguísimos (peor latencia y precisión al final).
"""
import collections
from collections.abc import Iterator
from datetime import datetime, timezone

import numpy as np
import webrtcvad

from config import AudioConfig, VadConfig
from models import AudioChunk


def _pcm16_bytes_to_float32(raw: bytes) -> np.ndarray:
    ints = np.frombuffer(raw, dtype=np.int16)
    return (ints.astype(np.float32) / 32768.0).copy()


class SpeechSegmenter:
    def __init__(self, audio_cfg: AudioConfig, vad_cfg: VadConfig):
        self._audio_cfg = audio_cfg
        self._vad_cfg = vad_cfg
        self._vad = webrtcvad.Vad(vad_cfg.aggressiveness)
        self._frame_duration_s = audio_cfg.frame_duration_ms / 1000

        padding_frames = max(1, vad_cfg.padding_ms // audio_cfg.frame_duration_ms)
        self._ring_buffer: collections.deque[tuple[bytes, bool]] = collections.deque(
            maxlen=padding_frames
        )
        silence_frames = max(1, int(vad_cfg.silence_timeout_s / self._frame_duration_s))
        self._silence_frames_limit = silence_frames
        self._max_segment_frames = max(
            1, int(vad_cfg.max_segment_duration_s / self._frame_duration_s)
        )

    def segments(self, frames: Iterator[bytes]) -> Iterator[AudioChunk]:
        """Consume el stream de frames crudos y produce AudioChunks de voz."""
        triggered = False
        voiced_frames: list[bytes] = []
        num_silence = 0
        segment_started_at: datetime | None = None

        for frame in frames:
            is_speech = self._vad.is_speech(frame, self._audio_cfg.sample_rate)

            if not triggered:
                self._ring_buffer.append((frame, is_speech))
                num_voiced = sum(1 for _, speech in self._ring_buffer if speech)
                if num_voiced > 0.9 * self._ring_buffer.maxlen:
                    triggered = True
                    segment_started_at = datetime.now(timezone.utc)
                    voiced_frames.extend(f for f, _ in self._ring_buffer)
                    self._ring_buffer.clear()
                continue

            voiced_frames.append(frame)
            if is_speech:
                num_silence = 0
            else:
                num_silence += 1

            if num_silence >= self._silence_frames_limit:
                chunk = self._build_chunk(voiced_frames, segment_started_at)
                if chunk is not None:
                    yield chunk
                triggered = False
                voiced_frames = []
                num_silence = 0
                segment_started_at = None
                self._ring_buffer.clear()
            elif len(voiced_frames) >= self._max_segment_frames:
                # Voz continua sin pausas: cortamos igual para no acumular
                # audios larguísimos, pero seguimos "triggered" sin pasar por el ring buffer.
                chunk = self._build_chunk(voiced_frames, segment_started_at)
                if chunk is not None:
                    yield chunk
                voiced_frames = []
                num_silence = 0
                segment_started_at = datetime.now(timezone.utc)

        # stream cerrado con un segmento todavía abierto
        if triggered and voiced_frames:
            chunk = self._build_chunk(voiced_frames, segment_started_at)
            if chunk is not None:
                yield chunk

    def _build_chunk(
        self, voiced_frames: list[bytes], started_at: datetime | None
    ) -> AudioChunk | None:
        duration_s = len(voiced_frames) * self._frame_duration_s
        if duration_s < self._vad_cfg.min_segment_duration_s:
            return None
        samples = _pcm16_bytes_to_float32(b"".join(voiced_frames))
        return AudioChunk(
            samples=samples,
            sample_rate=self._audio_cfg.sample_rate,
            started_at=started_at or datetime.now(timezone.utc),
            duration_s=duration_s,
        )

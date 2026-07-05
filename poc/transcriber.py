"""Motor de transcripción: envuelve faster-whisper (CTranslate2 int8)."""
from faster_whisper import WhisperModel

from config import ModelConfig
from models import AudioChunk, TranscriptionResult


class Transcriber:
    def __init__(self, cfg: ModelConfig):
        self._cfg = cfg
        self._model = WhisperModel(
            cfg.model_size, device=cfg.device, compute_type=cfg.compute_type
        )

    def transcribe(self, chunk: AudioChunk) -> TranscriptionResult:
        segments, info = self._model.transcribe(
            chunk.samples,
            language=self._cfg.language,
            beam_size=5,
        )
        texts: list[str] = []
        avg_logprobs: list[float] = []
        for seg in segments:  # `segments` es un generador: se recorre una sola vez
            stripped = seg.text.strip()
            if stripped:
                texts.append(stripped)
            avg_logprobs.append(seg.avg_logprob)

        text = " ".join(texts)
        avg_logprob = sum(avg_logprobs) / len(avg_logprobs) if avg_logprobs else 0.0

        return TranscriptionResult(
            text=text,
            language=info.language,
            avg_logprob=avg_logprob,
            source_chunk_started_at=chunk.started_at,
            source_chunk_duration_s=chunk.duration_s,
        )

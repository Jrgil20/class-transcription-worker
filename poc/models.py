"""Entidades de dominio: sin dependencias externas, solo dataclasses."""
from dataclasses import dataclass
from datetime import datetime

import numpy as np


@dataclass(frozen=True)
class AudioChunk:
    samples: np.ndarray  # float32 mono, normalizado [-1, 1]
    sample_rate: int
    started_at: datetime
    duration_s: float


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str
    avg_logprob: float
    source_chunk_started_at: datetime
    source_chunk_duration_s: float

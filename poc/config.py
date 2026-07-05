"""Configuración centralizada de la PoC. Todos los parámetros ajustables viven aquí."""
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AudioConfig:
    sample_rate: int = 16_000       # requerido por Whisper y webrtcvad
    channels: int = 1
    frame_duration_ms: int = 30     # webrtcvad solo acepta 10/20/30 ms
    input_device: int | None = None  # None = dispositivo por defecto del sistema


@dataclass(frozen=True)
class VadConfig:
    aggressiveness: int = 2          # 0 (permisivo) .. 3 (estricto)
    silence_timeout_s: float = 0.8   # silencio continuo para cerrar un segmento
    min_segment_duration_s: float = 0.3  # descarta segmentos más cortos (ruido)
    padding_ms: int = 200            # margen de silencio incluido antes/después de la voz
    max_segment_duration_s: float = 20.0  # corta un segmento aunque siga habiendo voz


@dataclass(frozen=True)
class ModelConfig:
    model_size: str = "small"
    fallback_model_size: str = "base"  # modelo más liviano si hay thermal throttling
    device: str = "cpu"
    compute_type: str = "int8"       # cuantización int8 vía CTranslate2
    language: str = "es"             # forzar idioma; None = autodetección


@dataclass(frozen=True)
class ThermalConfig:
    threshold_c: float = 80.0    # temperatura a partir de la cual se degrada el modelo
    check_interval_s: float = 30.0


@dataclass(frozen=True)
class OutputConfig:
    output_dir: Path = Path(__file__).parent / "sesiones"
    filename_prefix: str = "clase"
    session_split_minutes: float = 15.0  # 0 o None desactiva el split


@dataclass(frozen=True)
class QueueConfig:
    maxsize: int = 50  # back-pressure: si se llena, el productor espera


AUDIO = AudioConfig()
VAD = VadConfig()
MODEL = ModelConfig()
THERMAL = ThermalConfig()
OUTPUT = OutputConfig()
QUEUE = QueueConfig()

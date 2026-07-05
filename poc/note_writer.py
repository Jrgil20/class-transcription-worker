"""Escritor de notas Markdown compatible con Obsidian.

Escribe cada segmento a un archivo temporal (.tmp.md) apenas se transcribe,
para no perder trabajo si el proceso se cae a mitad de la clase (WAL ligero).
Al finalizar la sesión, compone el archivo final con front-matter y metadata.
"""
from datetime import datetime, timezone
from pathlib import Path

from config import OutputConfig
from models import TranscriptionResult


def _format_offset(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


class MarkdownWriter:
    def __init__(self, cfg: OutputConfig, model_name: str):
        self._cfg = cfg
        self._model_name = model_name
        self._session_start: datetime | None = None
        self._tmp_path: Path | None = None
        self._segment_count = 0
        self._logprob_sum = 0.0

    def start(self) -> None:
        self._cfg.output_dir.mkdir(parents=True, exist_ok=True)
        self._session_start = datetime.now(timezone.utc)
        stamp = self._session_start.strftime("%Y%m%d_%H%M")
        self._tmp_path = self._cfg.output_dir / f"{self._cfg.filename_prefix}_{stamp}.tmp.md"
        self._tmp_path.write_text("", encoding="utf-8")

    def add_segment(self, result: TranscriptionResult) -> None:
        assert self._session_start is not None, "llamar start() antes de add_segment()"
        offset_start = (result.source_chunk_started_at - self._session_start).total_seconds()
        offset_end = offset_start + result.source_chunk_duration_s

        block = (
            f"## {_format_offset(offset_start)} — {_format_offset(offset_end)}\n"
            f"{result.text}\n\n"
        )
        with self._tmp_path.open("a", encoding="utf-8") as f:
            f.write(block)

        self._segment_count += 1
        self._logprob_sum += result.avg_logprob

    def finalize(self) -> Path:
        assert self._session_start is not None, "llamar start() antes de finalize()"
        end = datetime.now(timezone.utc)
        duration = end - self._session_start
        avg_logprob = (
            self._logprob_sum / self._segment_count if self._segment_count else 0.0
        )

        header = (
            "---\n"
            f"fecha: {self._session_start.date()}\n"
            "asignatura: \n"
            "profesor: \n"
            f"duracion: {_format_offset(duration.total_seconds())}\n"
            f"modelo: {self._model_name}\n"
            "---\n\n"
            f"# Clase — {self._session_start.strftime('%Y-%m-%d %H:%M')}\n\n"
            "> [!meta]\n"
            f"> - Segmentos: {self._segment_count}\n"
            f"> - Confianza media (avg_logprob): {avg_logprob:.2f}\n\n"
        )
        body = self._tmp_path.read_text(encoding="utf-8")

        stamp = self._session_start.strftime("%Y%m%d_%H%M")
        final_path = self._cfg.output_dir / f"{self._cfg.filename_prefix}_{stamp}.md"
        final_path.write_text(header + body, encoding="utf-8")
        self._tmp_path.unlink(missing_ok=True)
        return final_path

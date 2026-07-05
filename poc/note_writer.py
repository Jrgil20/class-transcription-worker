"""Escritor de notas Markdown compatible con Obsidian.

Escribe cada segmento a un archivo temporal (.tmp.md) apenas se transcribe,
para no perder trabajo si el proceso se cae a mitad de la clase (WAL ligero).
Al finalizar la sesión, compone el archivo final con front-matter y metadata.
"""
import re
from datetime import datetime, timezone
from pathlib import Path

from config import OutputConfig
from models import TranscriptionResult

_STAMP_RE = re.compile(r"(\d{8}_\d{4})")


def _format_offset(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _slugify(text: str) -> str:
    keep = [c.lower() if c.isalnum() else "-" for c in text.strip()]
    slug = "".join(keep)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


class MarkdownWriter:
    def __init__(
        self,
        cfg: OutputConfig,
        model_name: str,
        asignatura: str = "",
        profesor: str = "",
    ):
        self._cfg = cfg
        self._model_name = model_name
        self._asignatura = asignatura
        self._profesor = profesor
        self._session_start: datetime | None = None
        self._tmp_path: Path | None = None
        self._final_stem: str | None = None
        self._segment_count = 0
        self._logprob_sum = 0.0

    def start(self, part: int | None = None) -> None:
        self._cfg.output_dir.mkdir(parents=True, exist_ok=True)
        self._session_start = datetime.now(timezone.utc)
        stamp = self._session_start.strftime("%Y%m%d_%H%M")

        stem_parts = [self._cfg.filename_prefix]
        if self._asignatura:
            stem_parts.append(_slugify(self._asignatura))
        stem_parts.append(stamp)
        if part is not None:
            stem_parts.append(f"parte{part}")
        self._final_stem = "_".join(stem_parts)

        self._tmp_path = self._cfg.output_dir / f"{self._final_stem}.tmp.md"
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
            f"asignatura: {self._asignatura}\n"
            f"profesor: {self._profesor}\n"
            f"duracion: {_format_offset(duration.total_seconds())}\n"
            f"modelo: {self._model_name}\n"
            "---\n\n"
            f"# Clase — {self._session_start.strftime('%Y-%m-%d %H:%M')}\n\n"
            "> [!meta]\n"
            f"> - Segmentos: {self._segment_count}\n"
            f"> - Confianza media (avg_logprob): {avg_logprob:.2f}\n\n"
        )
        body = self._tmp_path.read_text(encoding="utf-8")

        final_path = self._cfg.output_dir / f"{self._final_stem}.md"
        final_path.write_text(header + body, encoding="utf-8")
        self._tmp_path.unlink(missing_ok=True)
        return final_path


def recover_orphaned_sessions(cfg: OutputConfig) -> list[Path]:
    """Convierte en .md cualquier .tmp.md dejado por un corte inesperado del proceso.

    No conocemos asignatura/profesor/duración/modelo de una sesión huérfana (esa
    metadata vivía solo en memoria), así que el resultado queda marcado como
    recuperado y con esos campos vacíos.
    """
    if not cfg.output_dir.exists():
        return []

    recovered: list[Path] = []
    for tmp_path in sorted(cfg.output_dir.glob("*.tmp.md")):
        body = tmp_path.read_text(encoding="utf-8")
        segment_count = sum(1 for line in body.splitlines() if line.startswith("## "))

        match = _STAMP_RE.search(tmp_path.name)
        started_at = (
            datetime.strptime(match.group(1), "%Y%m%d_%H%M")
            if match
            else datetime.fromtimestamp(tmp_path.stat().st_mtime)
        )

        header = (
            "---\n"
            f"fecha: {started_at.date()}\n"
            "asignatura: \n"
            "profesor: \n"
            "duracion: desconocida (sesión recuperada tras corte inesperado)\n"
            "modelo: desconocido\n"
            "---\n\n"
            f"# Clase — {started_at.strftime('%Y-%m-%d %H:%M')} (recuperada)\n\n"
            "> [!warning] Sesión recuperada\n"
            "> El proceso se interrumpió sin cerrar la nota correctamente; "
            "esto se reconstruyó a partir del progreso guardado.\n"
            f"> - Segmentos recuperados: {segment_count}\n\n"
        )

        base_name = tmp_path.name.removesuffix(".tmp.md")
        final_path = cfg.output_dir / f"{base_name}_recuperada.md"
        final_path.write_text(header + body, encoding="utf-8")
        tmp_path.unlink()
        recovered.append(final_path)

    return recovered

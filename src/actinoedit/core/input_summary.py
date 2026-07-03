"""Input file summaries for reproducible design runs."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def _file_digest(path: Path, *, chunk_size: int = 65536) -> str:
    """Return SHA-256 hex digest of a file."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def summarize_input_file(path: str | Path) -> dict[str, Any]:
    """Build a reproducibility summary for one input file."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Input file not found: {path}")
    stat = p.stat()
    return {
        "path": str(p.resolve()),
        "name": p.name,
        "size_bytes": stat.st_size,
        "sha256": _file_digest(p),
    }


def summarize_design_inputs(
    genome_path: str,
    annotation_path: str,
    *,
    bgc_path: str | None = None,
) -> dict[str, Any]:
    """Summarize all design input files for audit trails."""
    summary: dict[str, Any] = {
        "genome": summarize_input_file(genome_path),
        "annotation": summarize_input_file(annotation_path),
    }
    if bgc_path:
        summary["bgc"] = summarize_input_file(bgc_path)
    return summary

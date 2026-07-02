"""Resolve bundled example data and profiles for dev, pip install, and PyInstaller."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path


def _package_root() -> Path:
    return Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def get_examples_dir() -> Path:
    """Return the examples directory containing demo genome and profiles.

    Resolution order:
    1. PyInstaller ``_MEIPASS/examples``
    2. Wheel-bundled ``actinoedit/_examples``
    3. Repository ``examples/`` (editable install / dev checkout)
    """
    candidates: list[Path] = []

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "examples")

    candidates.extend(
        [
            _package_root() / "_examples",
            _package_root().parent.parent / "examples",
            _package_root().parent.parent.parent / "examples",
        ]
    )

    for path in candidates:
        if (path / "demo_genome.fasta").is_file():
            return path

    searched = ", ".join(str(p) for p in candidates)
    raise FileNotFoundError(
        f"ActinoEdit examples not found. Searched: {searched}. "
        "Reinstall with: pip install -e ."
    )


def get_profiles_dir() -> Path:
    """Directory containing organism profile YAML files."""
    return get_examples_dir() / "profiles"


def get_demo_genome_path() -> Path:
    """Path to bundled Streptomyces demo FASTA."""
    return get_examples_dir() / "demo_genome.fasta"


def get_demo_annotation_path(fmt: str = "gff") -> Path:
    """Path to bundled demo annotation (GFF or GenBank)."""
    if fmt.lower() == "gbk":
        return get_examples_dir() / "demo_annotation.gbk"
    return get_examples_dir() / "demo_annotation.gff"

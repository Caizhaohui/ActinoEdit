"""Configuration management for ActinoEdit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG: dict[str, Any] = {
    "default_pam": "NGG",
    "default_spacer_length": 20,
    "default_max_mismatches": 3,
    "output_format": "csv",
}


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load configuration from a YAML file.

    Args:
        config_path: Path to configuration file. If None, returns default config.

    Returns:
        Configuration dictionary.
    """
    if config_path is None:
        return DEFAULT_CONFIG.copy()

    config_path = Path(config_path)
    if not config_path.exists():
        return DEFAULT_CONFIG.copy()

    with open(config_path) as f:
        user_config = yaml.safe_load(f) or {}

    # Merge with defaults
    config = DEFAULT_CONFIG.copy()
    config.update(user_config)
    return config

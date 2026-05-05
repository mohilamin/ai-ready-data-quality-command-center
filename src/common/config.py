from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from src.common.paths import PROJECT_ROOT, resolve_path

DEFAULT_SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.yaml"
DEFAULT_RULES_PATH = PROJECT_ROOT / "config" / "data_quality_rules.yaml"


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        loaded = yaml.safe_load(file) or {}
    if not isinstance(loaded, dict):
        msg = f"YAML file must contain a mapping: {path}"
        raise ValueError(msg)
    return loaded


@lru_cache(maxsize=1)
def load_settings() -> dict[str, Any]:
    """Load project settings from YAML."""
    configured = os.getenv("COMMAND_CENTER_SETTINGS")
    path = resolve_path(configured) if configured else DEFAULT_SETTINGS_PATH
    return _read_yaml(path)


@lru_cache(maxsize=1)
def load_quality_rules() -> dict[str, Any]:
    """Load table-level data quality rules from YAML."""
    return _read_yaml(DEFAULT_RULES_PATH)


def get_path(name: str) -> Path:
    """Return a configured data path by name."""
    settings = load_settings()
    try:
        return resolve_path(settings["paths"][name])
    except KeyError as exc:
        msg = f"Missing configured path: {name}"
        raise KeyError(msg) from exc

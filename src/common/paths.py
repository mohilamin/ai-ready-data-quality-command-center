from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_path(path_value: str | Path) -> Path:
    """Resolve a project-relative path to an absolute path."""
    path = Path(path_value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def ensure_directory(path_value: str | Path) -> Path:
    """Create a directory when needed and return its absolute path."""
    path = resolve_path(path_value)
    path.mkdir(parents=True, exist_ok=True)
    return path

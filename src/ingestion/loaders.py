from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common.config import get_path, load_quality_rules
from src.common.logging import get_logger

LOGGER = get_logger(__name__)


class RawDataLoadError(FileNotFoundError):
    """Raised when an expected raw dataset is missing."""


def expected_raw_files() -> dict[str, Path]:
    """Return table names and expected raw CSV paths."""
    raw_path = get_path("raw")
    return {table_name: raw_path / f"{table_name}.csv" for table_name in load_quality_rules()}


def validate_expected_files() -> None:
    """Validate all expected raw CSV files exist."""
    missing = [str(path) for path in expected_raw_files().values() if not path.exists()]
    if missing:
        msg = "Missing raw CSV files: " + ", ".join(missing)
        raise RawDataLoadError(msg)


def load_raw_data() -> dict[str, pd.DataFrame]:
    """Load all expected raw CSV files into DataFrames."""
    validate_expected_files()
    datasets: dict[str, pd.DataFrame] = {}
    for table_name, path in expected_raw_files().items():
        LOGGER.info("loading raw dataset", extra={"table": table_name, "path": str(path)})
        datasets[table_name] = pd.read_csv(path)
    return datasets

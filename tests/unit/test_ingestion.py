from pathlib import Path

import pytest

from src.data_generation.generate_synthetic_data import generate_all, write_raw_data
from src.ingestion.loaders import RawDataLoadError, load_raw_data, validate_expected_files


def test_load_raw_data_after_generation() -> None:
    write_raw_data(generate_all())
    loaded = load_raw_data()
    assert "customers" in loaded
    assert not loaded["transactions"].empty


def test_validate_expected_files_raises_when_missing() -> None:
    missing_path = Path("data/raw/customers.csv")
    backup_path = Path("data/raw/customers.csv.bak")
    write_raw_data(generate_all())
    missing_path.rename(backup_path)
    try:
        with pytest.raises(RawDataLoadError):
            validate_expected_files()
    finally:
        backup_path.rename(missing_path)

from __future__ import annotations

import pandas as pd

from src.common.config import get_path
from src.common.logging import get_logger
from src.common.paths import ensure_directory
from src.quality.rules import get_table_rules

LOGGER = get_logger(__name__)


def write_quality_issues(issues: pd.DataFrame) -> None:
    """Write the issue-level exceptions table."""
    quarantine_path = ensure_directory(get_path("quarantine"))
    output_path = quarantine_path / "quality_issues.csv"
    issues.to_csv(output_path, index=False)
    LOGGER.info("wrote quality issues", extra={"path": str(output_path), "rows": len(issues)})


def issue_record_ids(issues: pd.DataFrame, table_name: str) -> set[str]:
    """Return record IDs with issues for a table."""
    if issues.empty:
        return set()
    return set(issues.loc[issues["table_name"] == table_name, "record_id"].astype(str))


def write_quarantine_files(datasets: dict[str, pd.DataFrame], issues: pd.DataFrame) -> None:
    """Write table-specific quarantine files for rows with detected issues."""
    quarantine_path = ensure_directory(get_path("quarantine"))
    rules = get_table_rules()
    for table_name, frame in datasets.items():
        rule = rules[table_name]
        ids = issue_record_ids(issues, table_name)
        if not ids or rule.business_key not in frame.columns:
            continue
        quarantined = frame.loc[frame[rule.business_key].astype(str).isin(ids)]
        if quarantined.empty:
            continue
        output_path = quarantine_path / f"{table_name}_quarantine.csv"
        quarantined.to_csv(output_path, index=False)
        LOGGER.info(
            "wrote quarantine table",
            extra={"table": table_name, "path": str(output_path), "rows": len(quarantined)},
        )


def quarantine_bad_records(datasets: dict[str, pd.DataFrame], issues: pd.DataFrame) -> None:
    """Write all quarantine outputs."""
    write_quality_issues(issues)
    write_quarantine_files(datasets, issues)

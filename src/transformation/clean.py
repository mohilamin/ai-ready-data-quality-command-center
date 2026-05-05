from __future__ import annotations

import pandas as pd

from src.common.config import get_path
from src.common.logging import get_logger
from src.common.paths import ensure_directory
from src.quality.quarantine import issue_record_ids
from src.quality.rules import get_table_rules

LOGGER = get_logger(__name__)


def build_clean_datasets(
    datasets: dict[str, pd.DataFrame], issues: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    """Create clean datasets by excluding rows with critical or high quality issues."""
    clean: dict[str, pd.DataFrame] = {}
    rules = get_table_rules()
    blocking = (
        issues.loc[issues["severity"].isin(["critical", "high"])] if not issues.empty else issues
    )
    for table_name, frame in datasets.items():
        rule = rules[table_name]
        ids = issue_record_ids(blocking, table_name)
        if ids and rule.business_key in frame.columns:
            cleaned = frame.loc[~frame[rule.business_key].astype(str).isin(ids)].copy()
        else:
            cleaned = frame.copy()
        clean[table_name] = cleaned
    return clean


def write_clean_datasets(clean_datasets: dict[str, pd.DataFrame]) -> None:
    """Write clean CSV outputs."""
    clean_path = ensure_directory(get_path("clean"))
    for table_name, frame in clean_datasets.items():
        output_path = clean_path / f"{table_name}.csv"
        frame.to_csv(output_path, index=False)
        LOGGER.info("wrote clean dataset", extra={"table": table_name, "rows": len(frame)})

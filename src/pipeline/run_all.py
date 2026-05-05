from __future__ import annotations

import logging

from src.common.logging import configure_logging, get_logger
from src.data_generation.generate_synthetic_data import generate_all, write_raw_data
from src.ingestion.loaders import load_raw_data
from src.quality.quarantine import quarantine_bad_records
from src.quality.validators import validate_all
from src.scoring.accuracy import (
    calculate_accuracy_report,
    load_injected_issue_manifest,
    summarize_accuracy,
    write_accuracy_outputs,
)
from src.scoring.ai_readiness import calculate_ai_readiness_summary
from src.scoring.trust_score import (
    calculate_table_scorecards,
    write_ai_readiness_summary,
    write_scorecards,
)
from src.transformation.clean import build_clean_datasets, write_clean_datasets
from src.transformation.models import build_curated_models

LOGGER = get_logger(__name__)


def run_pipeline(generate_data: bool = False) -> None:
    """Run the full local data quality command center pipeline."""
    if generate_data:
        LOGGER.info("generating raw data before pipeline")
        write_raw_data(generate_all())
    raw_datasets = load_raw_data()
    issues = validate_all(raw_datasets)
    quarantine_bad_records(raw_datasets, issues)
    clean_datasets = build_clean_datasets(raw_datasets, issues)
    write_clean_datasets(clean_datasets)
    build_curated_models(clean_datasets, issues)
    scorecards = calculate_table_scorecards(raw_datasets, issues)
    write_scorecards(scorecards)
    summary = calculate_ai_readiness_summary(scorecards, issues)
    write_ai_readiness_summary(summary)
    manifest = load_injected_issue_manifest()
    accuracy_report = calculate_accuracy_report(issues, manifest)
    write_accuracy_outputs(accuracy_report, summarize_accuracy(accuracy_report))
    LOGGER.info("pipeline complete", extra={"tables": len(raw_datasets), "issues": len(issues)})


def main() -> None:
    configure_logging(logging.INFO)
    run_pipeline(generate_data=False)


if __name__ == "__main__":
    main()

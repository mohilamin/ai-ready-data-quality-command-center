from pathlib import Path

from src.data_generation.generate_synthetic_data import generate_all, write_raw_data
from src.pipeline.run_all import run_pipeline


def test_full_pipeline_execution() -> None:
    write_raw_data(generate_all())
    run_pipeline()
    assert Path("data/quarantine/quality_issues.csv").exists()
    assert Path("data/scorecards/table_scorecards.csv").exists()
    assert Path("data/scorecards/ai_readiness_summary.json").exists()
    assert Path("data/processed/command_center.duckdb").exists()

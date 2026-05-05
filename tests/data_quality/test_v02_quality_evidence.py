import json
from pathlib import Path

import duckdb
import pandas as pd
from fastapi.testclient import TestClient

from src.api.main import app
from src.data_generation.generate_synthetic_data import (
    build_injected_issue_manifest,
    generate_all,
    write_raw_data,
)
from src.pipeline.run_all import run_pipeline
from src.quality.quarantine import quarantine_bad_records
from src.quality.validators import validate_all
from src.scoring.accuracy import calculate_accuracy_report, summarize_accuracy
from src.scoring.trust_score import calculate_table_scorecards


def _issues() -> pd.DataFrame:
    return validate_all(generate_all())


def _issue_types() -> set[str]:
    return set(_issues()["issue_type"])


def test_injected_issue_manifest_creation() -> None:
    datasets = generate_all()
    write_raw_data(datasets)
    path = Path("data/raw/injected_issue_manifest.json")
    assert path.exists()
    manifest = json.loads(path.read_text())
    assert manifest["expected_issue_counts"]["duplicate_customers"] == 2


def test_duplicate_customer_detection() -> None:
    assert "duplicate_customers" in _issue_types()


def test_missing_customer_email_detection() -> None:
    assert "missing_customer_emails" in _issue_types()


def test_invalid_account_foreign_key_detection() -> None:
    assert "invalid_account_foreign_keys" in _issue_types()


def test_stale_source_load_detection() -> None:
    assert "stale_source_loads" in _issue_types()


def test_invalid_product_code_detection() -> None:
    assert "invalid_product_codes" in _issue_types()


def test_outlier_transaction_detection() -> None:
    assert "outlier_transaction_amounts" in _issue_types()


def test_negative_balance_detection() -> None:
    assert "negative_balances" in _issue_types()


def test_unauthorized_access_detection() -> None:
    assert "unauthorized_employee_access" in _issue_types()


def test_closed_account_transaction_detection() -> None:
    assert "transactions_linked_to_closed_accounts" in _issue_types()


def test_schema_drift_detection() -> None:
    assert "schema_drift_detected" in _issue_types()


def test_invalid_date_detection() -> None:
    assert "invalid_dates" in _issue_types()


def test_pii_risk_detection() -> None:
    assert "pii_risk_indicators" in _issue_types()


def test_quality_issues_have_audit_fields() -> None:
    issues = _issues()
    expected = {
        "issue_id",
        "table_name",
        "column_name",
        "record_id",
        "issue_type",
        "severity",
        "description",
        "detected_at",
        "recommended_action",
    }
    assert expected.issubset(issues.columns)
    assert issues["issue_id"].notna().all()


def test_quarantine_file_creation() -> None:
    datasets = generate_all()
    issues = validate_all(datasets)
    quarantine_bad_records(datasets, issues)
    assert Path("data/quarantine/customers_quarantine.csv").exists()
    assert Path("data/quarantine/transactions_quarantine.csv").exists()


def test_quality_issues_csv_creation() -> None:
    datasets = generate_all()
    issues = validate_all(datasets)
    quarantine_bad_records(datasets, issues)
    assert Path("data/quarantine/quality_issues.csv").exists()


def test_scorecards_are_between_0_and_100() -> None:
    datasets = generate_all()
    scorecards = calculate_table_scorecards(datasets, validate_all(datasets))
    score_columns = [column for column in scorecards.columns if column.endswith("_score")]
    assert scorecards[score_columns].apply(lambda series: series.between(0, 100).all()).all()


def test_accuracy_report_matches_manifest() -> None:
    datasets = generate_all()
    manifest = build_injected_issue_manifest(datasets)
    report = calculate_accuracy_report(validate_all(datasets), manifest)
    summary = summarize_accuracy(report)
    assert summary["overall_detection_accuracy"] == 1.0
    assert summary["missed_issue_count"] == 0


def test_ai_readiness_summary_exists_and_has_expected_keys() -> None:
    write_raw_data(generate_all())
    run_pipeline()
    path = Path("data/scorecards/ai_readiness_summary.json")
    assert path.exists()
    summary = json.loads(path.read_text())
    assert {"overall_ai_readiness_score", "readiness_band", "critical_issue_count"}.issubset(
        summary
    )


def test_accuracy_report_outputs_exist() -> None:
    write_raw_data(generate_all())
    run_pipeline()
    assert Path("data/scorecards/accuracy_report.json").exists()
    assert Path("data/scorecards/accuracy_report.csv").exists()


def test_duckdb_database_exists() -> None:
    write_raw_data(generate_all())
    run_pipeline()
    assert Path("data/processed/command_center.duckdb").exists()


def test_curated_duckdb_tables_exist() -> None:
    write_raw_data(generate_all())
    run_pipeline()
    con = duckdb.connect("data/processed/command_center.duckdb")
    try:
        tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    finally:
        con.close()
    assert {
        "customer_account_summary",
        "transaction_risk_summary",
        "source_freshness_summary",
        "data_quality_issue_summary",
    }.issubset(tables)


def test_api_tables_returns_list() -> None:
    write_raw_data(generate_all())
    client = TestClient(app)
    response = client.get("/tables")
    assert response.status_code == 200
    assert "customers" in response.json()["tables"]


def test_api_issues_returns_list() -> None:
    write_raw_data(generate_all())
    run_pipeline()
    client = TestClient(app)
    response = client.get("/issues")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_full_pipeline_can_run_end_to_end() -> None:
    write_raw_data(generate_all())
    run_pipeline()
    assert Path("data/scorecards/table_scorecards.csv").exists()

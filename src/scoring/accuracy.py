from __future__ import annotations

import json
from typing import Any

import pandas as pd

from src.common.config import get_path
from src.common.paths import ensure_directory

TRACKED_ISSUE_TYPES = [
    "duplicate_customers",
    "missing_customer_emails",
    "invalid_account_foreign_keys",
    "stale_source_loads",
    "invalid_product_codes",
    "outlier_transaction_amounts",
    "negative_balances",
    "unauthorized_employee_access",
    "transactions_linked_to_closed_accounts",
    "schema_drift_detected",
]


def load_injected_issue_manifest() -> dict[str, Any]:
    """Load the deterministic injected issue manifest."""
    path = get_path("raw") / "injected_issue_manifest.json"
    if not path.exists():
        msg = "Missing injected issue manifest. Run synthetic data generation first."
        raise FileNotFoundError(msg)
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def calculate_accuracy_report(issues: pd.DataFrame, manifest: dict[str, Any]) -> pd.DataFrame:
    """Compare expected injected issues with detected data quality issues."""
    expected_counts = {issue_type: 0 for issue_type in TRACKED_ISSUE_TYPES}
    for entry in manifest["issues"]:
        issue_type = entry["issue_type"]
        if issue_type in expected_counts:
            expected_counts[issue_type] += 1

    detected_counts = {issue_type: 0 for issue_type in TRACKED_ISSUE_TYPES}
    if not issues.empty:
        counts = issues["issue_type"].value_counts().to_dict()
        detected_counts.update(
            {issue_type: int(counts.get(issue_type, 0)) for issue_type in TRACKED_ISSUE_TYPES}
        )

    rows = []
    for issue_type in TRACKED_ISSUE_TYPES:
        expected = expected_counts[issue_type]
        detected = detected_counts[issue_type]
        matched = min(expected, detected)
        missed = max(expected - detected, 0)
        false_positive = max(detected - expected, 0)
        accuracy = round(matched / expected, 4) if expected else 1.0 if detected == 0 else 0.0
        rows.append(
            {
                "issue_type": issue_type,
                "expected_count": expected,
                "detected_count": detected,
                "matched_count": matched,
                "missed_count": missed,
                "false_positive_count": false_positive,
                "detection_accuracy": accuracy,
            }
        )
    return pd.DataFrame(rows)


def summarize_accuracy(report: pd.DataFrame) -> dict[str, Any]:
    """Summarize issue detection accuracy across tracked issue types."""
    expected_total = int(report["expected_count"].sum())
    detected_total = int(report["detected_count"].sum())
    matched_total = int(report["matched_count"].sum())
    missed_total = int(report["missed_count"].sum())
    false_positive_total = int(report["false_positive_count"].sum())
    overall = round(matched_total / expected_total, 4) if expected_total else 1.0
    return {
        "overall_detection_accuracy": overall,
        "expected_issue_count": expected_total,
        "detected_issue_count": detected_total,
        "matched_issue_count": matched_total,
        "missed_issue_count": missed_total,
        "false_positive_count": false_positive_total,
        "issue_type_count": len(report),
        "issue_type_results": report.to_dict("records"),
    }


def write_accuracy_outputs(report: pd.DataFrame, summary: dict[str, Any]) -> None:
    """Write accuracy CSV and JSON outputs."""
    scorecard_path = ensure_directory(get_path("scorecards"))
    report.to_csv(scorecard_path / "accuracy_report.csv", index=False)
    with (scorecard_path / "accuracy_report.json").open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)

from __future__ import annotations

import json

import pandas as pd

from src.common.config import get_path, load_settings
from src.common.paths import ensure_directory
from src.quality.rules import get_table_rules


def _score(issue_count: int, row_count: int, penalty: float = 100.0) -> float:
    if row_count <= 0:
        return 100.0
    return round(max(0.0, 100.0 - ((issue_count / row_count) * penalty)), 2)


def _count_issues(issues: pd.DataFrame, table_name: str, issue_types: set[str]) -> int:
    if issues.empty:
        return 0
    table_issues = issues.loc[issues["table_name"] == table_name]
    return int(table_issues["issue_type"].isin(issue_types).sum())


def calculate_table_scorecards(
    raw_datasets: dict[str, pd.DataFrame], issues: pd.DataFrame
) -> pd.DataFrame:
    """Calculate table-level Data Trust scorecards from issue evidence."""
    weights = load_settings()["scoring_weights"]
    rows = []
    for table_name, frame in raw_datasets.items():
        row_count = len(frame)
        scores = {
            "completeness_score": _score(
                _count_issues(
                    issues,
                    table_name,
                    {"missing_customer_emails", "missing_required_values"},
                ),
                row_count,
            ),
            "uniqueness_score": _score(
                _count_issues(
                    issues,
                    table_name,
                    {"duplicate_customers", "duplicate_primary_keys"},
                ),
                row_count,
            ),
            "freshness_score": _score(
                _count_issues(issues, table_name, {"stale_source_loads"}), row_count
            ),
            "schema_stability_score": _score(
                _count_issues(issues, table_name, {"schema_drift_detected", "invalid_dates"}),
                row_count,
            ),
            "referential_integrity_score": _score(
                _count_issues(
                    issues,
                    table_name,
                    {
                        "invalid_account_foreign_keys",
                        "invalid_foreign_keys",
                        "transactions_linked_to_closed_accounts",
                        "invalid_product_codes",
                    },
                ),
                row_count,
            ),
            "anomaly_score": _score(
                _count_issues(
                    issues,
                    table_name,
                    {"outlier_transaction_amounts", "negative_balances"},
                ),
                row_count,
            ),
            "pii_risk_score": _score(
                _count_issues(
                    issues,
                    table_name,
                    {"pii_risk_indicators", "unauthorized_employee_access"},
                ),
                row_count,
            ),
        }
        weighted = sum(scores[name] * float(weights.get(name, 0)) for name in scores)
        weight_total = sum(float(weights.get(name, 0)) for name in scores)
        scores["ai_readiness_score"] = round(weighted / weight_total, 2) if weight_total else 0.0
        rows.append({"table_name": table_name, "row_count": row_count, **scores})
    return pd.DataFrame(rows)


def write_scorecards(scorecards: pd.DataFrame) -> None:
    """Write table scorecard CSV output."""
    scorecard_path = ensure_directory(get_path("scorecards"))
    scorecards.to_csv(scorecard_path / "table_scorecards.csv", index=False)


def summarize_scorecards(scorecards: pd.DataFrame, issues: pd.DataFrame) -> dict[str, object]:
    """Build an executive AI-readiness summary."""
    average_score = round(float(scorecards["ai_readiness_score"].mean()), 2)
    lowest = scorecards.sort_values("ai_readiness_score").head(3)
    critical_count = 0 if issues.empty else int((issues["severity"] == "critical").sum())
    return {
        "overall_ai_readiness_score": average_score,
        "readiness_band": "ready" if average_score >= 85 else "needs_remediation",
        "critical_issue_count": critical_count,
        "lowest_scoring_tables": lowest[["table_name", "ai_readiness_score"]].to_dict("records"),
    }


def write_ai_readiness_summary(summary: dict[str, object]) -> None:
    """Write executive AI-readiness JSON output."""
    scorecard_path = ensure_directory(get_path("scorecards"))
    with (scorecard_path / "ai_readiness_summary.json").open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)


def expected_score_columns() -> list[str]:
    """Return the required score columns."""
    return [
        "completeness_score",
        "uniqueness_score",
        "freshness_score",
        "schema_stability_score",
        "referential_integrity_score",
        "anomaly_score",
        "pii_risk_score",
        "ai_readiness_score",
    ]


def configured_tables() -> list[str]:
    """Return configured scoring table names."""
    return list(get_table_rules())

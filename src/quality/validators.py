from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from src.common.config import load_settings
from src.common.logging import get_logger
from src.quality.rules import TableRule, get_table_rules

LOGGER = get_logger(__name__)
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


@dataclass(frozen=True)
class QualityIssue:
    """One data quality exception found in a table."""

    table_name: str
    issue_type: str
    severity: str
    record_id: str
    column_name: str
    description: str
    issue_id: str
    detected_at: str
    recommended_action: str


def _issue(
    table_name: str,
    issue_type: str,
    record_id: object,
    column_name: str,
    description: str,
    severity: str = "high",
) -> QualityIssue:
    issue_id = _issue_id(table_name, issue_type, record_id, column_name, description)
    return QualityIssue(
        table_name=table_name,
        issue_type=issue_type,
        severity=severity,
        record_id=str(record_id),
        column_name=column_name,
        description=description,
        issue_id=issue_id,
        detected_at=_detected_at(),
        recommended_action=_recommended_action(issue_type),
    )


def _detected_at() -> str:
    base_datetime = load_settings()["project"]["generation_base_datetime"]
    return datetime.fromisoformat(base_datetime).isoformat()


def _issue_id(
    table_name: str,
    issue_type: str,
    record_id: object,
    column_name: str,
    description: str,
) -> str:
    raw = f"{table_name}|{issue_type}|{record_id}|{column_name}|{description}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return f"DQ-{digest}"


def _recommended_action(issue_type: str) -> str:
    actions = {
        "duplicate_customers": "Merge or survivorship-match duplicate customer records.",
        "duplicate_primary_keys": "Resolve duplicate business keys before publishing clean data.",
        "missing_customer_emails": "Source or remediate customer email before AI activation.",
        "missing_required_values": "Populate required fields or quarantine the affected records.",
        "invalid_account_foreign_keys": "Repair account customer_id references against customers.",
        "invalid_foreign_keys": "Repair the foreign key reference or quarantine the child record.",
        "stale_source_loads": "Refresh the source load and verify ingestion scheduling.",
        "invalid_product_codes": "Map product_code to an approved reference value.",
        "outlier_transaction_amounts": (
            "Review amount with transaction monitoring or source owners."
        ),
        "negative_balances": "Confirm business rule exception or correct the account balance.",
        "unauthorized_employee_access": "Escalate to governance and access-control owners.",
        "transactions_linked_to_closed_accounts": (
            "Investigate transaction posting after account closure."
        ),
        "schema_drift_detected": "Review schema contract and update or reject unexpected fields.",
        "invalid_dates": "Standardize date parsing and source date formats.",
        "pii_risk_indicators": "Mask or remove sensitive values before downstream use.",
        "invalid_email_formats": "Correct malformed email values or mark contactability unknown.",
    }
    return actions.get(issue_type, "Review with the data owner and remediate before certification.")


def _record_id(row: pd.Series, rule: TableRule) -> object:
    return row.get(rule.business_key, row.name)


def _parse_datetime(value: object) -> pd.Timestamp | None:
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        return None
    return parsed


def validate_required_fields(
    table_name: str, frame: pd.DataFrame, rule: TableRule
) -> list[QualityIssue]:
    """Detect missing required columns and values."""
    issues: list[QualityIssue] = []
    for column in rule.required_fields:
        if column not in frame.columns:
            issues.append(
                _issue(
                    table_name,
                    "schema_drift_detected",
                    "TABLE",
                    column,
                    f"Required column {column} is missing.",
                    "critical",
                )
            )
            continue
        missing = frame[column].isna() | (frame[column].astype(str).str.strip() == "")
        for _, row in frame.loc[missing].iterrows():
            issue_type = (
                "missing_customer_emails"
                if table_name == "customers" and column == "email"
                else "missing_required_values"
            )
            issues.append(
                _issue(
                    table_name,
                    issue_type,
                    _record_id(row, rule),
                    column,
                    f"Required field {column} is missing.",
                )
            )
    return issues


def validate_duplicates(
    table_name: str,
    frame: pd.DataFrame,
    rule: TableRule,
) -> list[QualityIssue]:
    """Detect duplicate business keys."""
    if rule.business_key not in frame.columns:
        return []
    duplicate_mask = frame.duplicated(subset=[rule.business_key], keep=False)
    issue_type = "duplicate_customers" if table_name == "customers" else "duplicate_primary_keys"
    return [
        _issue(
            table_name,
            issue_type,
            row[rule.business_key],
            rule.business_key,
            f"Duplicate business key {row[rule.business_key]} detected at row {row.name}.",
        )
        for _, row in frame.loc[duplicate_mask].iterrows()
    ]


def validate_foreign_keys(
    table_name: str,
    frame: pd.DataFrame,
    datasets: dict[str, pd.DataFrame],
    rule: TableRule,
) -> list[QualityIssue]:
    """Detect invalid foreign key references."""
    issues: list[QualityIssue] = []
    for column, reference in rule.foreign_keys.items():
        reference_table, reference_column = reference.split(".")
        if column not in frame.columns or reference_table not in datasets:
            continue
        valid_values = set(datasets[reference_table][reference_column].dropna().astype(str))
        invalid_mask = ~frame[column].astype(str).isin(valid_values)
        for _, row in frame.loc[invalid_mask].iterrows():
            issue_type = "invalid_foreign_keys"
            if table_name == "accounts" and column == "customer_id":
                issue_type = "invalid_account_foreign_keys"
            if table_name == "transactions" and column == "product_code":
                issue_type = "invalid_product_codes"
            issues.append(
                _issue(
                    table_name,
                    issue_type,
                    _record_id(row, rule),
                    column,
                    f"{column} value {row[column]} is not present in {reference}.",
                )
            )
    return issues


def validate_non_negative(
    table_name: str,
    frame: pd.DataFrame,
    rule: TableRule,
) -> list[QualityIssue]:
    """Detect negative values where they are disallowed."""
    issues: list[QualityIssue] = []
    for column in rule.non_negative_fields:
        if column not in frame.columns:
            continue
        invalid = pd.to_numeric(frame[column], errors="coerce") < 0
        for _, row in frame.loc[invalid].iterrows():
            issues.append(
                _issue(
                    table_name,
                    "negative_balances",
                    _record_id(row, rule),
                    column,
                    f"{column} cannot be negative.",
                )
            )
    return issues


def validate_outliers(table_name: str, frame: pd.DataFrame, rule: TableRule) -> list[QualityIssue]:
    """Detect configured numeric outliers."""
    issues: list[QualityIssue] = []
    for column, limits in rule.outlier_fields.items():
        if column not in frame.columns:
            continue
        absolute_max = float(limits["absolute_max"])
        invalid = pd.to_numeric(frame[column], errors="coerce").abs() > absolute_max
        for _, row in frame.loc[invalid].iterrows():
            issues.append(
                _issue(
                    table_name,
                    "outlier_transaction_amounts",
                    _record_id(row, rule),
                    column,
                    f"{column} exceeds absolute threshold {absolute_max}.",
                    "medium",
                )
            )
    return issues


def validate_email_formats(
    table_name: str,
    frame: pd.DataFrame,
    rule: TableRule,
) -> list[QualityIssue]:
    """Detect malformed email values."""
    if "email" not in frame.columns:
        return []
    valid = frame["email"].fillna("").astype(str).str.match(EMAIL_PATTERN)
    invalid = (~valid) & frame["email"].notna()
    return [
        _issue(
            table_name,
            "invalid_email_formats",
            _record_id(row, rule),
            "email",
            f"Email value {row['email']} is not valid.",
            "medium",
        )
        for _, row in frame.loc[invalid].iterrows()
    ]


def validate_pii_risk(table_name: str, frame: pd.DataFrame, rule: TableRule) -> list[QualityIssue]:
    """Detect obvious PII exposure indicators in configured PII columns."""
    issues: list[QualityIssue] = []
    for column in rule.pii_fields:
        if column not in frame.columns:
            continue
        risky = frame[column].fillna("").astype(str).str.contains(SSN_PATTERN)
        for _, row in frame.loc[risky].iterrows():
            issues.append(
                _issue(
                    table_name,
                    "pii_risk_indicators",
                    _record_id(row, rule),
                    column,
                    f"{column} contains a sensitive-data pattern.",
                    "critical",
                )
            )
    return issues


def validate_stale_loads(
    table_name: str,
    frame: pd.DataFrame,
    rule: TableRule,
) -> list[QualityIssue]:
    """Detect stale source loads from configured freshness threshold."""
    if table_name != "source_system_loads" or "loaded_at" not in frame.columns:
        return []
    settings = load_settings()
    max_age_hours = int(settings["freshness_thresholds"]["source_system_loads_max_age_hours"])
    now = datetime.fromisoformat(settings["project"]["generation_base_datetime"])
    issues: list[QualityIssue] = []
    for _, row in frame.iterrows():
        parsed = _parse_datetime(row["loaded_at"])
        if parsed is None:
            issues.append(
                _issue(
                    table_name,
                    "invalid_dates",
                    _record_id(row, rule),
                    "loaded_at",
                    "Invalid date.",
                )
            )
            continue
        age_hours = (now - parsed.to_pydatetime()).total_seconds() / 3600
        if age_hours > max_age_hours:
            issues.append(
                _issue(
                    table_name,
                    "stale_source_loads",
                    _record_id(row, rule),
                    "loaded_at",
                    f"Source load is {age_hours:.1f} hours old.",
                    "medium",
                )
            )
    return issues


def validate_dates(table_name: str, frame: pd.DataFrame, rule: TableRule) -> list[QualityIssue]:
    """Detect invalid date-like values in known date columns."""
    date_columns = [
        column for column in frame.columns if column.endswith("_at") or column.endswith("_date")
    ]
    issues: list[QualityIssue] = []
    for column in date_columns:
        parsed = pd.to_datetime(frame[column], errors="coerce", utc=True)
        invalid = parsed.isna() & frame[column].notna()
        for _, row in frame.loc[invalid].iterrows():
            issues.append(
                _issue(
                    table_name,
                    "invalid_dates",
                    _record_id(row, rule),
                    column,
                    f"{column} cannot be parsed as a date.",
                    "medium",
                )
            )
    return issues


def validate_closed_account_transactions(
    datasets: dict[str, pd.DataFrame], rules: dict[str, TableRule]
) -> list[QualityIssue]:
    """Detect transactions linked to closed accounts."""
    if "transactions" not in datasets or "accounts" not in datasets:
        return []
    transactions = datasets["transactions"]
    accounts = datasets["accounts"]
    closed_accounts = set(
        accounts.loc[
            accounts["account_status"].astype(str).str.lower() == "closed",
            "account_id",
        ].astype(str)
    )
    linked = transactions["account_id"].astype(str).isin(closed_accounts)
    rule = rules["transactions"]
    return [
        _issue(
            "transactions",
            "transactions_linked_to_closed_accounts",
            _record_id(row, rule),
            "account_id",
            f"Transaction is linked to closed account {row['account_id']}.",
            "high",
        )
        for _, row in transactions.loc[linked].iterrows()
    ]


def validate_unauthorized_access(
    table_name: str, frame: pd.DataFrame, rule: TableRule
) -> list[QualityIssue]:
    """Detect unauthorized employee access events."""
    if table_name != "employee_access" or "authorized_flag" not in frame.columns:
        return []
    unauthorized = ~frame["authorized_flag"].astype(str).str.lower().isin(["true", "1", "yes"])
    return [
        _issue(
            table_name,
            "unauthorized_employee_access",
            _record_id(row, rule),
            "authorized_flag",
            "Employee access event was not authorized.",
            "critical",
        )
        for _, row in frame.loc[unauthorized].iterrows()
    ]


def validate_unexpected_columns(
    table_name: str,
    frame: pd.DataFrame,
    rule: TableRule,
) -> list[QualityIssue]:
    """Detect unexpected columns against the table schema contract."""
    if not rule.expected_columns:
        return []
    expected = set(rule.expected_columns)
    unexpected = [column for column in frame.columns if column not in expected]
    return [
        _issue(
            table_name,
            "schema_drift_detected",
            "TABLE",
            column,
            f"Unexpected column {column} is not in the schema contract.",
            "medium",
        )
        for column in unexpected
    ]


def validate_all(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Run all data quality checks and return an issue-level exceptions table."""
    rules = get_table_rules()
    issues: list[QualityIssue] = []
    for table_name, frame in datasets.items():
        rule = rules[table_name]
        LOGGER.info("validating dataset", extra={"table": table_name, "rows": len(frame)})
        issues.extend(validate_unexpected_columns(table_name, frame, rule))
        issues.extend(validate_required_fields(table_name, frame, rule))
        issues.extend(validate_duplicates(table_name, frame, rule))
        issues.extend(validate_foreign_keys(table_name, frame, datasets, rule))
        issues.extend(validate_non_negative(table_name, frame, rule))
        issues.extend(validate_outliers(table_name, frame, rule))
        issues.extend(validate_email_formats(table_name, frame, rule))
        issues.extend(validate_pii_risk(table_name, frame, rule))
        issues.extend(validate_stale_loads(table_name, frame, rule))
        issues.extend(validate_dates(table_name, frame, rule))
        issues.extend(validate_unauthorized_access(table_name, frame, rule))
    issues.extend(validate_closed_account_transactions(datasets, rules))
    return pd.DataFrame([issue.__dict__ for issue in issues])

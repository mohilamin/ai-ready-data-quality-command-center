from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.common.config import load_quality_rules


@dataclass(frozen=True)
class TableRule:
    """Normalized table-level quality rule."""

    table_name: str
    business_key: str
    required_fields: list[str]
    expected_columns: list[str]
    pii_fields: list[str]
    foreign_keys: dict[str, str]
    non_negative_fields: list[str]
    outlier_fields: dict[str, dict[str, float]]


def get_table_rules() -> dict[str, TableRule]:
    """Load quality rules as typed TableRule objects."""
    raw_rules: dict[str, Any] = load_quality_rules()
    return {
        table_name: TableRule(
            table_name=table_name,
            business_key=str(rule["business_key"]),
            required_fields=list(rule.get("required_fields", [])),
            expected_columns=list(rule.get("expected_columns", [])),
            pii_fields=list(rule.get("pii_fields", [])),
            foreign_keys=dict(rule.get("foreign_keys", {})),
            non_negative_fields=list(rule.get("non_negative_fields", [])),
            outlier_fields=dict(rule.get("outlier_fields", {})),
        )
        for table_name, rule in raw_rules.items()
    }

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

from src.common.config import get_path, load_settings
from src.common.logging import configure_logging, get_logger
from src.common.paths import ensure_directory

LOGGER = get_logger(__name__)


def _base_datetime() -> datetime:
    settings = load_settings()
    return datetime.fromisoformat(settings["project"]["generation_base_datetime"])


def _date_series(base: datetime, count: int, rng: np.random.Generator, max_days: int) -> list[str]:
    return [
        (base - timedelta(days=int(rng.integers(0, max_days)))).date().isoformat()
        for _ in range(count)
    ]


def _manifest_entry(
    issue_id: str,
    issue_type: str,
    table_name: str,
    record_id: str,
    column_name: str,
    description: str,
) -> dict[str, str]:
    return {
        "issue_id": issue_id,
        "issue_type": issue_type,
        "table_name": table_name,
        "record_id": record_id,
        "column_name": column_name,
        "description": description,
    }


def build_customers(rng: np.random.Generator, count: int = 100) -> pd.DataFrame:
    """Build synthetic customer records with deliberate duplicates, missing emails, and PII risk."""
    now = _base_datetime()
    statuses = np.array(["active", "inactive", "prospect"])
    customers = pd.DataFrame(
        {
            "customer_id": [f"CUST{i:04d}" for i in range(1, count + 1)],
            "full_name": [f"Customer {i:04d}" for i in range(1, count + 1)],
            "email": [f"customer{i:04d}@example.com" for i in range(1, count + 1)],
            "phone": [f"555-01{i:03d}" for i in range(1, count + 1)],
            "customer_status": rng.choice(statuses, size=count, p=[0.7, 0.2, 0.1]),
            "created_at": _date_series(now, count, rng, 900),
            "region": rng.choice(["Northeast", "South", "Midwest", "West"], size=count),
        }
    )
    customers.loc[[4, 19, 44], "email"] = np.nan
    customers.loc[7, "email"] = "not-an-email"
    customers.loc[11, "phone"] = "555-12-1234; SSN: 111-22-3333"
    customers = pd.concat([customers, customers.iloc[[2]].copy()], ignore_index=True)
    return customers


def build_product_reference() -> pd.DataFrame:
    """Build product reference data with one deliberate schema drift column."""
    return pd.DataFrame(
        [
            {
                "product_code": "CHK",
                "product_name": "Checking Account",
                "product_family": "deposit",
                "active_flag": True,
                "risk_tier": "low",
            },
            {
                "product_code": "SAV",
                "product_name": "Savings Account",
                "product_family": "deposit",
                "active_flag": True,
                "risk_tier": "low",
            },
            {
                "product_code": "CRD",
                "product_name": "Credit Card",
                "product_family": "credit",
                "active_flag": True,
                "risk_tier": "medium",
            },
            {
                "product_code": "MTG",
                "product_name": "Mortgage",
                "product_family": "lending",
                "active_flag": True,
                "risk_tier": "high",
            },
            {
                "product_code": "LEGACY",
                "product_name": "Legacy Product",
                "product_family": "legacy",
                "active_flag": False,
                "risk_tier": "high",
            },
        ]
    )


def build_accounts(
    rng: np.random.Generator,
    customers: pd.DataFrame,
    count: int = 130,
) -> pd.DataFrame:
    """Build account records with deliberate invalid foreign keys and negative balances."""
    now = _base_datetime()
    customer_ids = customers["customer_id"].dropna().unique()
    account_types = np.array(["checking", "savings", "credit_card", "mortgage"])
    accounts = pd.DataFrame(
        {
            "account_id": [f"ACCT{i:05d}" for i in range(1, count + 1)],
            "customer_id": rng.choice(customer_ids, size=count),
            "account_type": rng.choice(account_types, size=count),
            "account_status": "open",
            "opened_at": _date_series(now, count, rng, 1500),
            "balance": np.abs(rng.normal(8500, 12000, size=count)).round(2) + 100,
        }
    )
    accounts.loc[[5, 36], "customer_id"] = ["CUST9999", "CUST8888"]
    accounts.loc[[8, 28], "balance"] = [-250.0, -1200.0]
    accounts.loc[15, "opened_at"] = "2024/31/01"
    accounts.loc[20, "account_status"] = "closed"
    return accounts


def build_transactions(
    rng: np.random.Generator,
    accounts: pd.DataFrame,
    products: pd.DataFrame,
    count: int = 500,
) -> pd.DataFrame:
    """Build transactions with deliberate invalid products, outliers, dates, and links."""
    now = _base_datetime()
    open_account_ids = accounts.loc[accounts["account_status"] == "open", "account_id"].to_numpy()
    product_codes = products["product_code"].to_numpy()
    transactions = pd.DataFrame(
        {
            "transaction_id": [f"TXN{i:06d}" for i in range(1, count + 1)],
            "account_id": rng.choice(open_account_ids, size=count),
            "product_code": rng.choice(product_codes, size=count),
            "transaction_date": _date_series(now, count, rng, 45),
            "amount": rng.normal(175, 950, size=count).round(2),
            "currency": "USD",
            "channel": rng.choice(["branch", "mobile", "web", "atm"], size=count),
        }
    )
    transactions.loc[[12, 47], "product_code"] = ["BADCODE", "UNKNOWN"]
    transactions.loc[[21, 88], "amount"] = [125000.0, -80000.0]
    transactions.loc[33, "transaction_date"] = "2024/31/01"
    closed_account = accounts.loc[accounts["account_status"] == "closed", "account_id"].iloc[0]
    transactions.loc[0, "account_id"] = closed_account
    transactions.loc[1, "account_id"] = "ACCT99999"
    return transactions


def build_employee_access(rng: np.random.Generator, count: int = 80) -> pd.DataFrame:
    """Build employee access events with deliberate unauthorized access examples."""
    now = _base_datetime()
    access = pd.DataFrame(
        {
            "access_event_id": [f"ACCESS{i:05d}" for i in range(1, count + 1)],
            "employee_id": [f"EMP{int(i):04d}" for i in rng.integers(1, 35, size=count)],
            "table_name": rng.choice(["customers", "accounts", "transactions"], size=count),
            "access_level": rng.choice(["read", "write", "export"], size=count),
            "access_timestamp": [
                (now - timedelta(hours=int(rng.integers(1, 240)))).isoformat() for _ in range(count)
            ],
            "authorized_flag": True,
        }
    )
    access.loc[[3, 16], "authorized_flag"] = False
    return access


def build_source_system_loads(rng: np.random.Generator) -> pd.DataFrame:
    """Build source load metadata with deliberate stale load examples."""
    now = _base_datetime()
    tables = [
        "customers",
        "accounts",
        "transactions",
        "product_reference",
        "employee_access",
        "data_lineage_events",
    ]
    rows = []
    for index, table in enumerate(tables, start=1):
        age_hours = int(rng.integers(1, 14))
        if table in {"product_reference", "employee_access"}:
            age_hours = 96
        rows.append(
            {
                "load_id": f"LOAD{index:04d}",
                "source_system": f"{table}_system",
                "table_name": table,
                "loaded_at": (now - timedelta(hours=age_hours)).isoformat(),
                "record_count": int(rng.integers(50, 600)),
                "status": "success",
            }
        )
    return pd.DataFrame(rows)


def build_lineage_events(rng: np.random.Generator, count: int = 30) -> pd.DataFrame:
    """Build simple lineage events for raw-to-clean-to-curated movement."""
    now = _base_datetime()
    sources = np.array(["customers", "accounts", "transactions", "source_system_loads"])
    targets = np.array(
        [
            "clean_customers",
            "clean_accounts",
            "clean_transactions",
            "customer_account_summary",
            "transaction_risk_summary",
        ]
    )
    return pd.DataFrame(
        {
            "lineage_event_id": [f"LIN{i:05d}" for i in range(1, count + 1)],
            "source_table": rng.choice(sources, size=count),
            "target_table": rng.choice(targets, size=count),
            "transformation_name": rng.choice(
                ["required_field_validation", "quarantine_split", "scorecard_build"],
                size=count,
            ),
            "event_timestamp": [
                (now - timedelta(hours=int(rng.integers(1, 120)))).isoformat()
                for _ in range(count)
            ],
        }
    )


def generate_all() -> dict[str, pd.DataFrame]:
    """Generate all synthetic datasets and return them as DataFrames."""
    settings = load_settings()
    rng = np.random.default_rng(int(settings["project"]["random_seed"]))
    customers = build_customers(rng)
    products = build_product_reference()
    accounts = build_accounts(rng, customers)
    transactions = build_transactions(rng, accounts, products)
    return {
        "customers": customers,
        "accounts": accounts,
        "transactions": transactions,
        "product_reference": products,
        "employee_access": build_employee_access(rng),
        "source_system_loads": build_source_system_loads(rng),
        "data_lineage_events": build_lineage_events(rng),
    }


def build_injected_issue_manifest(datasets: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """Return the deterministic manifest of deliberately injected quality issues."""
    entries = [
        _manifest_entry(
            "INJ-DUP-CUSTOMERS-001A",
            "duplicate_customers",
            "customers",
            "CUST0003",
            "customer_id",
            "Original customer key participates in a deliberate duplicate.",
        ),
        _manifest_entry(
            "INJ-DUP-CUSTOMERS-001B",
            "duplicate_customers",
            "customers",
            "CUST0003",
            "customer_id",
            "Copied customer key participates in a deliberate duplicate.",
        ),
        *[
            _manifest_entry(
                f"INJ-MISSING-EMAIL-{record_id}",
                "missing_customer_emails",
                "customers",
                record_id,
                "email",
                "Customer email was intentionally removed.",
            )
            for record_id in ["CUST0005", "CUST0020", "CUST0045"]
        ],
        *[
            _manifest_entry(
                f"INJ-ACCOUNT-FK-{record_id}",
                "invalid_account_foreign_keys",
                "accounts",
                record_id,
                "customer_id",
                "Account references a customer_id that does not exist.",
            )
            for record_id in ["ACCT00006", "ACCT00037"]
        ],
        *[
            _manifest_entry(
                f"INJ-STALE-LOAD-{record_id}",
                "stale_source_loads",
                "source_system_loads",
                record_id,
                "loaded_at",
                "Source load timestamp exceeds the freshness SLA.",
            )
            for record_id in ["LOAD0004", "LOAD0005"]
        ],
        *[
            _manifest_entry(
                f"INJ-BAD-PRODUCT-{record_id}",
                "invalid_product_codes",
                "transactions",
                record_id,
                "product_code",
                "Transaction product_code is not in product_reference.",
            )
            for record_id in ["TXN000013", "TXN000048"]
        ],
        *[
            _manifest_entry(
                f"INJ-TXN-OUTLIER-{record_id}",
                "outlier_transaction_amounts",
                "transactions",
                record_id,
                "amount",
                "Transaction amount exceeds the configured outlier threshold.",
            )
            for record_id in ["TXN000022", "TXN000089"]
        ],
        *[
            _manifest_entry(
                f"INJ-NEG-BALANCE-{record_id}",
                "negative_balances",
                "accounts",
                record_id,
                "balance",
                "Account balance is negative where non-negative balance is required.",
            )
            for record_id in ["ACCT00009", "ACCT00029"]
        ],
        *[
            _manifest_entry(
                f"INJ-UNAUTH-ACCESS-{record_id}",
                "unauthorized_employee_access",
                "employee_access",
                record_id,
                "authorized_flag",
                "Employee access event is deliberately unauthorized.",
            )
            for record_id in ["ACCESS00004", "ACCESS00017"]
        ],
        _manifest_entry(
            "INJ-CLOSED-ACCOUNT-TXN-001",
            "transactions_linked_to_closed_accounts",
            "transactions",
            "TXN000001",
            "account_id",
            "Transaction is linked to a deliberately closed account.",
        ),
        _manifest_entry(
            "INJ-SCHEMA-DRIFT-PRODUCT-001",
            "schema_drift_detected",
            "product_reference",
            "TABLE",
            "risk_tier",
            "Unexpected risk_tier column simulates schema drift.",
        ),
    ]
    expected_counts = pd.DataFrame(entries)["issue_type"].value_counts().sort_index().to_dict()
    return {
        "generated_at": _base_datetime().isoformat(),
        "random_seed": int(load_settings()["project"]["random_seed"]),
        "datasets": {table_name: len(frame) for table_name, frame in datasets.items()},
        "issues": entries,
        "expected_issue_counts": expected_counts,
    }


def write_injected_issue_manifest(datasets: dict[str, pd.DataFrame]) -> None:
    """Write the injected issue manifest to the raw data directory."""
    raw_path = ensure_directory(get_path("raw"))
    manifest = build_injected_issue_manifest(datasets)
    output_path = raw_path / "injected_issue_manifest.json"
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2)
    LOGGER.info("wrote injected issue manifest", extra={"path": str(output_path)})


def write_raw_data(datasets: dict[str, pd.DataFrame]) -> None:
    """Write generated datasets and issue manifest to the configured raw data directory."""
    raw_path = ensure_directory(get_path("raw"))
    for table_name, frame in datasets.items():
        output_path = raw_path / f"{table_name}.csv"
        frame.to_csv(output_path, index=False)
        LOGGER.info("wrote raw dataset", extra={"table": table_name, "path": str(output_path)})
    write_injected_issue_manifest(datasets)


def main() -> None:
    configure_logging(logging.INFO)
    datasets = generate_all()
    write_raw_data(datasets)
    LOGGER.info("synthetic data generation complete", extra={"tables": list(datasets)})


if __name__ == "__main__":
    main()

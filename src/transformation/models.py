from __future__ import annotations

import duckdb
import pandas as pd

from src.common.config import get_path
from src.common.logging import get_logger
from src.common.paths import ensure_directory

LOGGER = get_logger(__name__)


def build_curated_models(clean_datasets: dict[str, pd.DataFrame], issues: pd.DataFrame) -> None:
    """Build curated business-ready DuckDB tables."""
    processed_path = ensure_directory(get_path("processed"))
    database_path = get_path("duckdb")
    if database_path.exists():
        database_path.unlink()
    con = duckdb.connect(str(database_path))
    try:
        for table_name, frame in clean_datasets.items():
            con.register(table_name, frame)
            con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM {table_name}")
        con.register("quality_issues_df", issues)
        con.execute("CREATE OR REPLACE TABLE quality_issues AS SELECT * FROM quality_issues_df")
        con.execute(
            """
            CREATE OR REPLACE TABLE customer_account_summary AS
            SELECT
                c.customer_id,
                c.region,
                c.customer_status,
                COUNT(a.account_id) AS account_count,
                COALESCE(SUM(a.balance), 0) AS total_balance
            FROM customers c
            LEFT JOIN accounts a ON c.customer_id = a.customer_id
            GROUP BY c.customer_id, c.region, c.customer_status
            """
        )
        con.execute(
            """
            CREATE OR REPLACE TABLE transaction_risk_summary AS
            SELECT
                account_id,
                COUNT(*) AS transaction_count,
                SUM(ABS(amount)) AS absolute_transaction_volume,
                MAX(ABS(amount)) AS largest_transaction
            FROM transactions
            GROUP BY account_id
            """
        )
        con.execute(
            """
            CREATE OR REPLACE TABLE source_freshness_summary AS
            SELECT
                table_name,
                source_system,
                loaded_at,
                status,
                record_count
            FROM source_system_loads
            """
        )
        con.execute(
            """
            CREATE OR REPLACE TABLE data_quality_issue_summary AS
            SELECT
                table_name,
                issue_type,
                severity,
                COUNT(*) AS issue_count
            FROM quality_issues
            GROUP BY table_name, issue_type, severity
            """
        )
    finally:
        con.close()
    LOGGER.info("built curated DuckDB models", extra={"path": str(processed_path)})

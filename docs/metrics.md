# Metrics

All table-level scores range from 0 to 100. A score of 100 means no issues of that score category were detected for the table. Lower scores mean the table has more evidence of risk relative to its row count.

## Shared Penalty Formula

For most component scores:

```text
score = max(0, 100 - ((issue_count / row_count) * 100))
```

Inputs:

- `issue_count`: detected issue count for the relevant issue types.
- `row_count`: number of records in the raw table.
- `100`: proportional penalty scale.

Example: if a table has 2 duplicate-key issues across 100 rows, uniqueness is `100 - (2 / 100 * 100) = 98`.

## completeness_score

Business meaning: how reliably required fields are populated.

Formula: `100 - missing-required-value rate`.

Input fields:

- Required fields in `config/data_quality_rules.yaml`
- Detected issue types: `missing_customer_emails`, `missing_required_values`

Penalty logic: each missing required value reduces the score proportionally to table size.

Example interpretation: a completeness score of 97 means roughly 3% of rows had required-field failures.

## uniqueness_score

Business meaning: whether business keys identify one real-world entity or event.

Formula: `100 - duplicate-key issue rate`.

Input fields:

- Table business keys in `config/data_quality_rules.yaml`
- Detected issue types: `duplicate_customers`, `duplicate_primary_keys`

Penalty logic: each record participating in a duplicate key reduces the score.

Example interpretation: a uniqueness score below 100 signals entity resolution or source deduplication work is needed.

## freshness_score

Business meaning: whether source loads are recent enough for AI, analytics, and operational use.

Formula: `100 - stale-load issue rate`.

Input fields:

- `source_system_loads.loaded_at`
- `freshness_thresholds.source_system_loads_max_age_hours`
- Detected issue type: `stale_source_loads`

Penalty logic: each source load older than the SLA reduces the score for `source_system_loads`.

Example interpretation: a low freshness score means downstream users may be looking at outdated data.

## schema_stability_score

Business meaning: whether table schemas and date formats are stable enough for automated consumers.

Formula: `100 - schema/date issue rate`.

Input fields:

- Expected columns in `config/data_quality_rules.yaml`
- Date-like fields ending in `_at` or `_date`
- Detected issue types: `schema_drift_detected`, `invalid_dates`

Penalty logic: unexpected columns, missing expected columns, and unparseable date values reduce the score.

Example interpretation: a schema stability score below 100 means APIs, dashboards, or ML feature jobs may break.

## referential_integrity_score

Business meaning: whether relationships across datasets are valid.

Formula: `100 - relationship issue rate`.

Input fields:

- Foreign keys in `config/data_quality_rules.yaml`
- Account status for closed-account transaction checks
- Detected issue types: `invalid_account_foreign_keys`, `invalid_foreign_keys`, `invalid_product_codes`, `transactions_linked_to_closed_accounts`

Penalty logic: invalid child-to-parent references and transactions posted to closed accounts reduce the score.

Example interpretation: weak referential integrity means downstream joins and customer/account analytics cannot be trusted.

## anomaly_score

Business meaning: whether numeric values are plausible under configured business rules.

Formula: `100 - anomaly issue rate`.

Input fields:

- `accounts.balance`
- `transactions.amount`
- Outlier thresholds in `config/data_quality_rules.yaml`
- Detected issue types: `negative_balances`, `outlier_transaction_amounts`

Penalty logic: each numeric anomaly reduces the score.

Example interpretation: a low anomaly score may indicate source posting errors, fraud-monitoring candidates, or rule exceptions.

## pii_risk_score

Business meaning: whether the table appears safe for AI and analytics consumption from a privacy perspective.

Formula: `100 - PII/governance issue rate`.

Input fields:

- Configured PII fields
- `employee_access.authorized_flag`
- Detected issue types: `pii_risk_indicators`, `unauthorized_employee_access`

Penalty logic: sensitive-data patterns and unauthorized access events reduce the score.

Example interpretation: a low PII risk score means data should not be sent to broad analytics or GenAI tools without remediation.

## ai_readiness_score

Business meaning: an overall table-level readiness signal for analytics, ML, GenAI agents, and executive reporting.

Formula:

```text
ai_readiness_score =
  weighted_average(
    completeness_score,
    uniqueness_score,
    freshness_score,
    schema_stability_score,
    referential_integrity_score,
    anomaly_score,
    pii_risk_score
  )
```

Input fields:

- Component scores listed above
- Weights in `config/settings.yaml`

Penalty logic: each component contributes according to the configured score weight.

Example interpretation: a table with an AI-readiness score under 85 is treated as needing remediation before high-trust AI or executive usage.

## Accuracy Evidence

The synthetic generator writes `data/raw/injected_issue_manifest.json`, which records known injected issues. The pipeline compares that manifest with detected issues and writes:

- `data/scorecards/accuracy_report.csv`
- `data/scorecards/accuracy_report.json`

Accuracy formula by issue type:

```text
detection_accuracy = matched_count / expected_count
```

Overall accuracy:

```text
overall_detection_accuracy = total_matched_count / total_expected_count
```

This makes the project auditable: the portfolio can show not only that issues were found, but that the detector found the issues it was designed to find.

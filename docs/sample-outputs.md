# Sample Outputs

These examples show the shape of generated artifacts after running:

```bash
python -m src.data_generation.generate_synthetic_data
python -m src.pipeline.run_all
```

## Sample `table_scorecards.csv` Rows

```csv
table_name,row_count,completeness_score,uniqueness_score,freshness_score,schema_stability_score,referential_integrity_score,anomaly_score,pii_risk_score,ai_readiness_score
customers,101,97.03,98.02,100.0,100.0,100.0,100.0,99.01,99.23
accounts,130,100.0,100.0,100.0,99.23,98.46,98.46,100.0,99.32
transactions,500,100.0,100.0,100.0,99.8,99.4,99.6,100.0,99.81
```

## Sample Quality Issue Record

```json
{
  "issue_id": "DQ-765201039aa9",
  "table_name": "accounts",
  "column_name": "customer_id",
  "record_id": "ACCT00006",
  "issue_type": "invalid_account_foreign_keys",
  "severity": "high",
  "description": "customer_id value CUST9999 is not present in customers.customer_id.",
  "detected_at": "2026-05-05T12:00:00+00:00",
  "recommended_action": "Repair account customer_id references against customers."
}
```

## Sample Accuracy Report

```json
{
  "overall_detection_accuracy": 1.0,
  "expected_issue_count": 19,
  "detected_issue_count": 19,
  "matched_issue_count": 19,
  "missed_issue_count": 0,
  "false_positive_count": 0
}
```

## Sample API Response

`GET /ai-readiness-summary`

```json
{
  "overall_ai_readiness_score": 99.03,
  "readiness_band": "ready",
  "critical_issue_count": 3,
  "lowest_scoring_tables": [
    {
      "table_name": "source_system_loads",
      "ai_readiness_score": 95.56
    }
  ]
}
```

## Sample Executive Dashboard Interpretation

The executive view should be read as a certification summary:

- Overall AI-readiness is high because the synthetic dataset is mostly clean.
- Critical issues still exist: PII exposure and unauthorized access require governance review.
- Quarantine files provide audit-ready examples of records that should not flow into trusted products.
- The accuracy report proves that the validation layer catches the known injected defects.
